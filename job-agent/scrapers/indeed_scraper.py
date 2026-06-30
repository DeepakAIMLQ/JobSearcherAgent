"""
Indeed India Scraper -- Adzuna /in/ endpoint
Only activates when ADZUNA keys are set and valid.
"""
import requests, logging
from datetime import datetime
from typing import List, Dict, Any
logger = logging.getLogger(__name__)

class IndeedScraper:

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        from config.settings import SETTINGS
        self.app_id  = SETTINGS.get("adzuna_app_id", "").strip()
        self.app_key = SETTINGS.get("adzuna_app_key", "").strip()
        self._valid  = None

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not self.app_id or not self.app_key:
            logger.info(
                "  [Indeed India] Skipped -- add ADZUNA_APP_ID + ADZUNA_APP_KEY to .env\n"
                "    Free signup (2 min): https://developer.adzuna.com/"
            )
            return []

        if self._valid is None:
            self._valid = self._test()

        if not self._valid:
            logger.warning(
                "  [Indeed India] Skipped -- invalid credentials.\n"
                "    Check ADZUNA_APP_ID and ADZUNA_APP_KEY in .env\n"
                "    Get free keys: https://developer.adzuna.com/"
            )
            return []

        all_jobs = []
        for query in self.profile.get("search_queries", [])[:5]:
            jobs = self._search(query)
            all_jobs.extend(jobs)

        seen, unique = set(), []
        for job in all_jobs:
            if job["job_id"] not in seen:
                seen.add(job["job_id"])
                unique.append(job)
        logger.info("  [Indeed India] Got %d jobs", len(unique))
        return unique

    def _test(self) -> bool:
        try:
            r = requests.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={"app_id": self.app_id, "app_key": self.app_key,
                        "results_per_page": 1, "what": "manager"},
                timeout=10
            )
            return r.status_code == 200
        except Exception:
            return False

    def _search(self, query: str) -> List[Dict[str, Any]]:
        try:
            r = requests.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={"app_id": self.app_id, "app_key": self.app_key,
                        "results_per_page": 20, "what": query, "sort_by": "date"},
                timeout=15
            )
            if r.status_code == 200:
                return [self._norm(j) for j in r.json().get("results", [])]
        except Exception as e:
            logger.debug("  Adzuna error: %s", e)
        return []

    def _norm(self, raw: Dict) -> Dict:
        loc = raw.get("location", {})
        loc_str = ", ".join((loc.get("display_name", "") or "").split(",")[:2])
        if "india" not in loc_str.lower():
            loc_str = (loc_str + ", India").strip(", ")
        return {
            "job_id":   f"adzuna2_{raw.get('id', '')}",
            "title":    raw.get("title", ""),
            "company":  (raw.get("company") or {}).get("display_name", ""),
            "location": loc_str,
            "is_remote": "remote" in raw.get("title", "").lower(),
            "description": raw.get("description", "")[:2000],
            "apply_url": raw.get("redirect_url", ""),
            "source":   "Indeed",
            "posted_at": raw.get("created", datetime.utcnow().isoformat()),
            "experience_required": "",
            "skills":   [(raw.get("category") or {}).get("label", "")],
            "salary":   "",
            "employment_type": raw.get("contract_type", "Full-time") or "Full-time",
        }

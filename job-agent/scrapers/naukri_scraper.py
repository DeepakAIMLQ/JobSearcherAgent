"""
India Jobs Scraper
==================
Tier 1 (with API keys - real India jobs):
  - JSearch RapidAPI  -> Naukri + LinkedIn + Indeed India
  - Adzuna /in/       -> Indeed India

Tier 2 (free, no keys - filtered for relevance):
  - Remotive          -> filtered by profile keywords
  - The Muse          -> senior roles only
  - Arbeitnow         -> remote roles

Tier 2 runs ALWAYS as baseline. Tier 1 adds real India jobs on top.
"""

import requests, re, logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class NaukriScraper:

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        from config.settings import SETTINGS
        self.rapidapi_key   = SETTINGS.get("rapidapi_key", "").strip()
        self.adzuna_app_id  = SETTINGS.get("adzuna_app_id", "").strip()
        self.adzuna_app_key = SETTINGS.get("adzuna_app_key", "").strip()
        # Build keyword set from profile for relevance pre-filtering
        self._keywords = set(
            w.lower() for skill in profile.get("skills", [])
            for w in skill.split()
        ) | set(
            w.lower() for title in profile.get("target_titles", [])
            for w in title.split()
        )

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        all_jobs = []

        # --- TIER 1: Real India jobs (needs API keys) ---

        if self.rapidapi_key:
            logger.info("  [JSearch] Fetching Naukri+LinkedIn+Indeed India...")
            jobs = self._fetch_jsearch()
            logger.info("    Got %d India jobs from JSearch", len(jobs))
            all_jobs.extend(jobs)
        else:
            logger.info(
                "  [JSearch] NOT configured -- to get real Naukri/LinkedIn/Indeed India jobs:\n"
                "    Step 1: Go to https://rapidapi.com/letscrape-6bfxmjk09/api/jsearch\n"
                "    Step 2: Click 'Subscribe to Test' -> FREE plan (200 req/month, no card)\n"
                "    Step 3: Copy key from dashboard -> add to .env: RAPIDAPI_KEY=your_key"
            )

        if self.adzuna_app_id and self.adzuna_app_key:
            logger.info("  [Adzuna] Fetching Indeed India...")
            jobs = self._fetch_adzuna()
            logger.info("    Got %d Indeed India jobs from Adzuna", len(jobs))
            all_jobs.extend(jobs)
        else:
            logger.info(
                "  [Adzuna/Indeed] NOT configured:\n"
                "    Step 1: Go to https://developer.adzuna.com/ -> Register free\n"
                "    Step 2: Add to .env: ADZUNA_APP_ID=xxx  ADZUNA_APP_KEY=xxx"
            )

        # --- TIER 2: Free global sources, keyword-filtered ---

        logger.info("  [Remotive] Fetching keyword-matched remote jobs...")
        jobs = self._fetch_remotive_filtered()
        logger.info("    Got %d keyword-matched jobs from Remotive", len(jobs))
        all_jobs.extend(jobs)

        logger.info("  [TheMuse] Fetching senior tech roles...")
        jobs = self._fetch_muse()
        logger.info("    Got %d jobs from The Muse", len(jobs))
        all_jobs.extend(jobs)

        logger.info("  [Arbeitnow] Fetching remote roles...")
        jobs = self._fetch_arbeitnow()
        logger.info("    Got %d jobs from Arbeitnow", len(jobs))
        all_jobs.extend(jobs)

        # Deduplicate
        seen, unique = set(), []
        for job in all_jobs:
            if job["job_id"] not in seen:
                seen.add(job["job_id"])
                unique.append(job)
        return unique

    # ─── JSearch ──────────────────────────────────────────────────
    def _fetch_jsearch(self) -> List[Dict[str, Any]]:
        all_jobs = []
        for query in self.profile.get("search_queries", [])[:5]:
            try:
                r = requests.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers={"X-RapidAPI-Key": self.rapidapi_key,
                             "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                    params={"query": query, "page": "1",
                            "num_pages": "2", "date_posted": "month"},
                    timeout=15,
                )
                if r.status_code == 200:
                    for j in r.json().get("data", []):
                        cc = (j.get("job_country_code") or "").lower()
                        co = (j.get("job_country") or "").lower()
                        if "india" in co or cc == "in":
                            all_jobs.append(self._norm_jsearch(j))
                elif r.status_code == 429:
                    logger.warning("    JSearch quota reached (200/month). Resets monthly.")
                    break
                elif r.status_code == 403:
                    logger.warning("    JSearch 403 -- key may be invalid or quota exceeded.")
                    break
            except Exception as e:
                logger.debug("    JSearch error: %s", e)
        return all_jobs

    def _norm_jsearch(self, raw: Dict) -> Dict:
        url = raw.get("job_apply_link", "")
        src = "Naukri" if "naukri" in url.lower() else \
              "Indeed" if "indeed" in url.lower() else \
              "Glassdoor" if "glassdoor" in url.lower() else "LinkedIn"
        city = raw.get("job_city", "")
        return {
            "job_id":   f"jsearch_{raw.get('job_id','')}",
            "title":    raw.get("job_title", ""),
            "company":  raw.get("employer_name", ""),
            "location": f"{city}, India".strip(", ") if city else "India",
            "is_remote": raw.get("job_is_remote", False),
            "description": raw.get("job_description", "")[:2000],
            "apply_url": url,
            "source":   src,
            "posted_at": raw.get("job_posted_at_datetime_utc", datetime.utcnow().isoformat()),
            "experience_required": str(
                (raw.get("job_required_experience") or {})
                .get("required_experience_in_months", 0) // 12) + " yrs",
            "skills":   raw.get("job_required_skills") or [],
            "salary":   str(raw.get("job_min_salary") or ""),
            "employment_type": raw.get("job_employment_type", "Full-time"),
        }

    # ─── Adzuna India ─────────────────────────────────────────────
    def _fetch_adzuna(self) -> List[Dict[str, Any]]:
        all_jobs = []
        for query in self.profile.get("search_queries", [])[:5]:
            try:
                r = requests.get(
                    "https://api.adzuna.com/v1/api/jobs/in/search/1",
                    params={"app_id": self.adzuna_app_id, "app_key": self.adzuna_app_key,
                            "results_per_page": 20, "what": query, "sort_by": "date"},
                    timeout=15,
                )
                if r.status_code == 200:
                    all_jobs.extend([self._norm_adzuna(j) for j in r.json().get("results", [])])
                elif r.status_code == 401:
                    logger.error("    Adzuna 401 -- invalid credentials")
                    break
            except Exception as e:
                logger.debug("    Adzuna error: %s", e)
        return all_jobs

    def _norm_adzuna(self, raw: Dict) -> Dict:
        loc = raw.get("location", {})
        loc_str = ", ".join((loc.get("display_name", "") or "").split(",")[:2])
        if "india" not in loc_str.lower():
            loc_str = (loc_str + ", India").strip(", ")
        return {
            "job_id":   f"adzuna_{raw.get('id','')}",
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

    # ─── Remotive (keyword pre-filtered) ─────────────────────────
    def _fetch_remotive_filtered(self) -> List[Dict[str, Any]]:
        """
        Fetch from Remotive but ONLY keep jobs where title/tags
        contain keywords from the user's profile.
        This prevents irrelevant jobs like 'Video Editor' or 'Sales Head'.
        """
        all_jobs = []
        categories = ["software-dev", "data", "product", "management-finance"]
        # Build a tight keyword set from target titles
        title_keywords = set()
        for title in self.profile.get("target_titles", []):
            for word in title.lower().split():
                if len(word) > 3:  # skip short words like 'of', 'the'
                    title_keywords.add(word)

        for cat in categories:
            try:
                r = requests.get(
                    "https://remotive.com/api/remote-jobs",
                    params={"category": cat, "limit": 100},
                    timeout=15,
                )
                if r.status_code == 200:
                    for job in r.json().get("jobs", []):
                        # Pre-filter: title or tags must contain a profile keyword
                        job_title = job.get("title", "").lower()
                        job_tags  = " ".join(job.get("tags", [])).lower()
                        combined  = job_title + " " + job_tags
                        # Must match at least one title keyword
                        if any(kw in combined for kw in title_keywords):
                            # Drop US/Europe-only jobs
                            loc = (job.get("candidate_required_location") or "").lower()
                            if any(x in loc for x in [
                                "united states only","us only","usa only",
                                "uk only","europe only","eu only","canada only"
                            ]):
                                continue
                            all_jobs.append(self._norm_remotive(job))
            except Exception as e:
                logger.debug("    Remotive %s error: %s", cat, e)
        return all_jobs

    def _norm_remotive(self, raw: Dict) -> Dict:
        desc = re.sub(r"<[^>]+>", " ", raw.get("description", "")).strip()[:2000]
        loc  = raw.get("candidate_required_location", "") or "Remote (India eligible)"
        return {
            "job_id":   f"remotive_{raw.get('id','')}",
            "title":    raw.get("title", ""),
            "company":  raw.get("company_name", ""),
            "location": loc,
            "is_remote": True,
            "description": desc,
            "apply_url": raw.get("url", ""),
            "source":   "Remotive",
            "posted_at": raw.get("publication_date", datetime.utcnow().isoformat()),
            "experience_required": "",
            "skills":   raw.get("tags", []),
            "salary":   raw.get("salary", ""),
            "employment_type": raw.get("job_type", "Full-time"),
        }

    # ─── The Muse ─────────────────────────────────────────────────
    def _fetch_muse(self) -> List[Dict[str, Any]]:
        all_jobs = []
        for cat in ["IT", "Product Management", "Data Science", "Project Management"]:
            try:
                r = requests.get(
                    "https://www.themuse.com/api/public/jobs",
                    params={"category": cat, "level": "Senior Level", "page": 0},
                    timeout=15,
                )
                if r.status_code == 200:
                    all_jobs.extend([self._norm_muse(j) for j in r.json().get("results", [])])
            except Exception as e:
                logger.debug("    Muse error: %s", e)
        return all_jobs

    def _norm_muse(self, raw: Dict) -> Dict:
        desc = re.sub(r"<[^>]+>", " ", raw.get("contents", "")).strip()[:2000]
        locs = raw.get("locations", [{}])
        loc  = locs[0].get("name", "Remote") if locs else "Remote"
        return {
            "job_id":   f"muse_{raw.get('id','')}",
            "title":    raw.get("name", ""),
            "company":  (raw.get("company") or {}).get("name", ""),
            "location": loc,
            "is_remote": "remote" in loc.lower(),
            "description": desc,
            "apply_url": (raw.get("refs") or {}).get("landing_page", ""),
            "source":   "TheMuse",
            "posted_at": raw.get("publication_date", datetime.utcnow().isoformat()),
            "experience_required": ", ".join(l.get("name", "") for l in raw.get("levels", [])),
            "skills":   [c.get("name", "") for c in raw.get("categories", [])],
            "salary":   "",
            "employment_type": "Full-time",
        }

    # ─── Arbeitnow ────────────────────────────────────────────────
    def _fetch_arbeitnow(self) -> List[Dict[str, Any]]:
        try:
            r = requests.get("https://arbeitnow.com/api/job-board-api", timeout=15)
            if r.status_code == 200:
                return [self._norm_arbeitnow(j) for j in r.json().get("data", [])[:50]]
        except Exception as e:
            logger.debug("    Arbeitnow error: %s", e)
        return []

    def _norm_arbeitnow(self, raw: Dict) -> Dict:
        desc = re.sub(r"<[^>]+>", " ", raw.get("description", "")).strip()[:2000]
        ts   = raw.get("created_at", 0)
        return {
            "job_id":   f"arbeitnow_{raw.get('slug','')}",
            "title":    raw.get("title", ""),
            "company":  raw.get("company_name", ""),
            "location": raw.get("location", "Remote"),
            "is_remote": raw.get("remote", False),
            "description": desc,
            "apply_url": raw.get("url", ""),
            "source":   "Arbeitnow",
            "posted_at": datetime.utcfromtimestamp(ts).isoformat() if ts else datetime.utcnow().isoformat(),
            "experience_required": "",
            "skills":   raw.get("tags", []),
            "salary":   "",
            "employment_type": "Full-time",
        }

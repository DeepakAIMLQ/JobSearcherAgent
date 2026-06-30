"""
LinkedIn + Naukri India Scraper -- JSearch RapidAPI
====================================================
Fetches ONLY India-based jobs from LinkedIn, Naukri, Indeed, Glassdoor.

FREE setup (5 minutes):
  1. Go to https://rapidapi.com/letscrape-6bfxmjk09/api/jsearch
  2. Click 'Subscribe to Test' -> select FREE plan (200 req/month)
  3. Copy your key from the dashboard
  4. Add to .env: RAPIDAPI_KEY=your_key_here
"""
import requests, logging
from datetime import datetime
from typing import List, Dict, Any
logger = logging.getLogger(__name__)

class LinkedInScraper:

    JSEARCH = "https://jsearch.p.rapidapi.com/search"

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        from config.settings import SETTINGS
        self.key    = SETTINGS.get("rapidapi_key", "").strip()
        self._valid = None

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        if not self.key:
            logger.info(
                "  [LinkedIn/Naukri India] NOT configured.\n"
                "    Get FREE key (5 min): https://rapidapi.com/letscrape-6bfxmjk09/api/jsearch\n"
                "    Add to .env: RAPIDAPI_KEY=your_key\n"
                "    This gives LinkedIn + Naukri + Indeed + Glassdoor India jobs"
            )
            return []

        if self._valid is None:
            self._valid = self._test()

        if not self._valid:
            logger.warning(
                "  [LinkedIn/Naukri] SKIPPED -- key invalid or not subscribed to JSearch.\n"
                "    Fix: subscribe at rapidapi.com/letscrape-6bfxmjk09/api/jsearch (FREE plan)"
            )
            return []

        all_jobs = []
        queries = self.profile.get("search_queries", [])
        logger.info("  [LinkedIn/Naukri India] Fetching with %d queries...", len(queries[:5]))

        for query in queries[:5]:
            jobs = self._search(query)
            all_jobs.extend(jobs)

        # Deduplicate
        seen, unique = set(), []
        for job in all_jobs:
            if job["job_id"] not in seen:
                seen.add(job["job_id"])
                unique.append(job)

        logger.info("  [LinkedIn/Naukri India] Got %d unique India jobs", len(unique))
        return unique

    def _test(self) -> bool:
        try:
            r = requests.get(
                self.JSEARCH,
                headers={"X-RapidAPI-Key": self.key,
                         "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                params={"query": "manager India", "page": "1", "num_pages": "1"},
                timeout=10,
            )
            return r.status_code == 200
        except Exception:
            return False

    def _search(self, query: str) -> List[Dict[str, Any]]:
        try:
            r = requests.get(
                self.JSEARCH,
                headers={"X-RapidAPI-Key": self.key,
                         "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                params={
                    "query":       f"{query} India",
                    "page":        "1",
                    "num_pages":   "2",
                    "date_posted": "month",
                },
                timeout=15,
            )
            if r.status_code == 200:
                jobs = []
                for j in r.json().get("data", []):
                    # Hard filter: only India jobs
                    country_code = (j.get("job_country_code") or "").lower()
                    country      = (j.get("job_country") or "").lower()
                    city         = (j.get("job_city") or "").lower()
                    if "india" in country or "in" == country_code or self._is_india_city(city):
                        jobs.append(self._norm(j))
                logger.debug("    Query '%s': %d India jobs", query, len(jobs))
                return jobs
            elif r.status_code == 429:
                logger.warning("    JSearch quota reached (200 req/month free plan).")
        except Exception as e:
            logger.debug("    JSearch error: %s", e)
        return []

    def _is_india_city(self, city: str) -> bool:
        india_cities = {
            "delhi","mumbai","bangalore","bengaluru","hyderabad","pune","chennai",
            "kolkata","noida","gurgaon","gurugram","ahmedabad","jaipur","chandigarh",
            "kochi","coimbatore","indore","lucknow","surat","vadodara","nagpur",
            "thane","faridabad","ghaziabad","greater noida","mysore","vizag",
        }
        return any(c in city for c in india_cities)

    def _norm(self, raw: Dict) -> Dict:
        url = raw.get("job_apply_link", "")
        if "naukri"     in url.lower(): src = "Naukri"
        elif "indeed"   in url.lower(): src = "Indeed"
        elif "linkedin" in url.lower(): src = "LinkedIn"
        elif "glassdoor" in url.lower(): src = "Glassdoor"
        else: src = "LinkedIn"

        city    = raw.get("job_city", "")
        country = raw.get("job_country", "India")
        loc     = f"{city}, {country}".strip(", ") if city else country

        return {
            "job_id":   f"li_{raw.get('job_id', '')}",
            "title":    raw.get("job_title", ""),
            "company":  raw.get("employer_name", ""),
            "location": loc,
            "is_remote": raw.get("job_is_remote", False),
            "description": raw.get("job_description", "")[:2000],
            "apply_url": url,
            "source":   src,
            "posted_at": raw.get("job_posted_at_datetime_utc", datetime.utcnow().isoformat()),
            "experience_required": str(
                (raw.get("job_required_experience") or {})
                .get("required_experience_in_months", 0) // 12
            ) + " yrs",
            "skills":   raw.get("job_required_skills") or [],
            "salary":   str(raw.get("job_min_salary") or ""),
            "employment_type": raw.get("job_employment_type", "Full-time"),
        }

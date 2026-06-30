"""
Job Agent -- Orchestrator
Scrape -> Filter -> Deduplicate -> Rank -> Email
"""

import json, logging
from datetime import datetime
from typing import List, Dict, Any

from scrapers.naukri_scraper   import NaukriScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper   import IndeedScraper
from utils.job_filter          import JobFilter
from utils.email_sender        import EmailSender
from utils.deduplicator        import JobDeduplicator
from config.profile            import PROFILE
from config.settings           import SETTINGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class JobAgent:

    def __init__(self):
        self.profile      = PROFILE
        self.settings     = SETTINGS
        self.filter       = JobFilter(self.profile)
        self.deduplicator = JobDeduplicator()
        self.email_sender = EmailSender(self.settings)
        self.scrapers     = [
            IndeedScraper(self.profile),
            NaukriScraper(self.profile),
            LinkedInScraper(self.profile),
        ]

    def run(self, force_fresh: bool = False) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("Job Agent Started: %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
        if force_fresh:
            logger.info("Mode: FRESH RUN (dedup cache cleared)")
        logger.info("=" * 60)

        # Clear dedup cache if force_fresh
        if force_fresh:
            self.deduplicator.clear()

        all_jobs = []
        for scraper in self.scrapers:
            source = scraper.__class__.__name__
            logger.info("Scraping from %s...", source)
            try:
                jobs = scraper.fetch_jobs()
                logger.info("  Found %d raw jobs from %s", len(jobs), source)
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error("  Error scraping %s: %s", source, str(e))

        logger.info("Total raw jobs collected: %d", len(all_jobs))

        filtered = self.filter.apply(all_jobs)
        logger.info("After profile filtering: %d jobs", len(filtered))

        new_jobs = self.deduplicator.filter_new(filtered)
        logger.info("After deduplication: %d new jobs", len(new_jobs))

        ranked = self.filter.rank(new_jobs)

        if ranked:
            sent = self.email_sender.send_digest(ranked, self.profile)
            if sent:
                self.deduplicator.mark_sent(ranked)
                logger.info("[OK] Email digest sent with %d jobs.", len(ranked))
            else:
                logger.error(
                    "[FAIL] Email failed -- jobs NOT marked as sent (will retry next run).\n"
                    "  Fix: add GMAIL_USER and GMAIL_APP_PASSWORD to your .env\n"
                    "  Guide: https://myaccount.google.com/apppasswords"
                )
        else:
            logger.info("No new relevant jobs found. No email sent.")

        result = {
            "date":          datetime.now().isoformat(),
            "total_scraped": len(all_jobs),
            "after_filter":  len(filtered),
            "new_jobs_sent": len(ranked),
        }
        logger.info("Run summary: %s", json.dumps(result, indent=2))
        return result

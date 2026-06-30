"""
Job Deduplicator — tracks sent jobs, prevents duplicate emails.
"""

import json, os, logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
DEFAULT_FILE   = "data/seen_jobs.json"
RETENTION_DAYS = 30


class JobDeduplicator:

    def __init__(self, filepath: str = DEFAULT_FILE):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self._seen: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        with open(self.filepath, "w") as f:
            json.dump(self._seen, f, indent=2)

    def filter_new(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(days=RETENTION_DAYS)).isoformat()
        self._seen = {k: v for k, v in self._seen.items() if v >= cutoff}
        new_jobs = [j for j in jobs if j["job_id"] not in self._seen]
        logger.info("Deduplication: %d/%d jobs are new", len(new_jobs), len(jobs))
        return new_jobs

    def mark_sent(self, jobs: List[Dict[str, Any]]):
        now = datetime.utcnow().isoformat()
        for job in jobs:
            self._seen[job["job_id"]] = now
        self._save()
        logger.info("Marked %d jobs as sent", len(jobs))

    def clear(self):
        """Reset the dedup cache — next run delivers all matching jobs fresh."""
        count = len(self._seen)
        self._seen = {}
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
        logger.info("Dedup cache cleared (%d entries removed)", count)

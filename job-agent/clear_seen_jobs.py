"""
clear_seen_jobs.py
==================
Resets the deduplication cache so the next run re-sends all jobs.

Use when:
  - Gmail was not configured and jobs were marked sent incorrectly
  - You want a fresh digest today

Usage:
    python clear_seen_jobs.py
"""
import os, json

path = "data/seen_jobs.json"

if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
    count = len(data)
    os.remove(path)
    print(f"Cleared {count} entries from {path}")
    print("Next run will deliver a fresh digest.")
else:
    print(f"Nothing to clear — {path} does not exist.")
    print("Next run will work normally.")

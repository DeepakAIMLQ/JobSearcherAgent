"""
SETTINGS — loads all credentials from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

SETTINGS = {
    # ── Email ─────────────────────────────────────────────────────
    "smtp_host":     "smtp.gmail.com",
    "smtp_port":     587,
    "smtp_user":     os.getenv("GMAIL_USER", ""),
    "smtp_password": os.getenv("GMAIL_APP_PASSWORD", ""),

    # ── LinkedIn / JSearch (RapidAPI) ─────────────────────────────
    # Free: 200 req/month — https://rapidapi.com/letscrape-6bfxmjk09/api/jsearch
    "enable_linkedin": True,
    "rapidapi_key":    os.getenv("RAPIDAPI_KEY", ""),

    # ── Adzuna (FREE fallback for LinkedIn) ───────────────────────
    # Free: 250 req/month — register at https://developer.adzuna.com
    # Used automatically when RAPIDAPI_KEY is not set
    "adzuna_app_id":  os.getenv("ADZUNA_APP_ID", ""),
    "adzuna_app_key": os.getenv("ADZUNA_APP_KEY", ""),

    # ── Naukri (web scraping — no key needed) ────────────────────
    "enable_naukri": True,

    # ── Scheduling ────────────────────────────────────────────────
    "schedule_time": "08:00",

    # ── Storage ───────────────────────────────────────────────────
    "seen_jobs_file": "data/seen_jobs.json",

    # ── Logging ───────────────────────────────────────────────────
    "log_file":  "logs/agent.log",
    "log_level": "INFO",
}

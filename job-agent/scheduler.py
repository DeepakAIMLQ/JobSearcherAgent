"""
scheduler.py -- Job Agent Entry Point

Usage:
  python scheduler.py             # Run daily at scheduled time (08:00 AM)
  python scheduler.py --now       # Run once immediately
  python scheduler.py --now --fresh  # Run now + clear dedup cache first
"""

import sys, os, time, logging, schedule
from datetime import datetime

import sys as _sys
# UTF-8 encoding for Windows console (fixes cp1252 UnicodeEncodeError)
_stdout_handler = logging.StreamHandler(
    _sys.stdout if hasattr(_sys.stdout, "reconfigure") and
    _sys.stdout.reconfigure(encoding="utf-8") is None else _sys.stdout
)
_stdout_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_file_handler = logging.FileHandler("logs/agent.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[_stdout_handler, _file_handler],
)
logger = logging.getLogger(__name__)

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

PROFILE_PATH        = "config/profile.py"
PLACEHOLDER_EMAIL   = "your.email@gmail.com"


def profile_is_configured() -> bool:
    if not os.path.exists(PROFILE_PATH):
        return False
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("profile", PROFILE_PATH)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        p = mod.PROFILE
        return (
            p.get("email_to", "") != PLACEHOLDER_EMAIL and
            bool(p.get("target_titles")) and
            bool(p.get("skills"))
        )
    except Exception:
        return False


def prompt_setup():
    print("\n" + "=" * 55)
    print("  Job Agent -- First-Time Setup Required")
    print("=" * 55)
    print("\n  No profile found. Run setup first:\n")
    print("    python setup_profile.py path/to/your_resume.pdf\n")
    print("=" * 55 + "\n")
    sys.exit(0)


def run_agent(force_fresh: bool = False):
    logger.info("Triggered at %s%s", datetime.now().isoformat(),
                " (fresh run)" if force_fresh else "")
    try:
        from agents.job_agent import JobAgent
        agent = JobAgent()
        agent.run(force_fresh=force_fresh)
    except Exception as e:
        logger.exception("Agent run failed: %s", str(e))


def main():
    if not profile_is_configured():
        prompt_setup()

    force_fresh = "--fresh" in sys.argv

    if "--now" in sys.argv:
        if force_fresh:
            logger.info("Running immediately with fresh dedup cache...")
        else:
            logger.info("Running immediately (--now flag)...")
        run_agent(force_fresh=force_fresh)
        return

    from config.settings import SETTINGS
    run_time = SETTINGS.get("schedule_time", "08:00")
    schedule.every().day.at(run_time).do(run_agent)
    logger.info("Scheduler started -- daily digest at %s.", run_time)
    logger.info("Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()

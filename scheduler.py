"""
scheduler.py
============
Main entry point for the Job Agent.

Usage:
    python scheduler.py            # Run daily digest at scheduled time
    python scheduler.py --now      # Run once immediately (for testing)
    python scheduler.py --setup    # Shortcut: run profile setup wizard
"""

import sys
import os
import time
import logging
import schedule
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

file_handler = logging.FileHandler("logs/agent.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)


PROFILE_PATH = "config/profile.py"
PROFILE_PLACEHOLDER_EMAIL = "your.email@gmail.com"


def profile_is_configured() -> bool:
    """Return True only if profile.py exists and has been personalised."""
    if not os.path.exists(PROFILE_PATH):
        return False
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("profile", PROFILE_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        p = mod.PROFILE
        # Treat as unconfigured if still using the placeholder email
        if p.get("email_to", "") == PROFILE_PLACEHOLDER_EMAIL:
            return False
        # Must have at least one title and one skill
        if not p.get("target_titles") or not p.get("skills"):
            return False
        return True
    except Exception:
        return False


def prompt_setup():
    """Print a clear setup prompt and exit."""
    print("\n" + "=" * 55)
    print("  Job Agent — First-Time Setup Required")
    print("=" * 55)
    print("\n  No personalised profile found.")
    print("\n  Run the setup wizard first:")
    print("\n    python setup_profile.py path/to/your_resume.pdf")
    print("\n  This reads your resume and auto-creates config/profile.py")
    print("  using Claude AI. Takes about 10-15 seconds.\n")
    print("=" * 55 + "\n")
    sys.exit(0)


def run_agent():
    logger.info("Scheduled run triggered at %s", datetime.now().isoformat())
    try:
        from agents.job_agent import JobAgent
        agent = JobAgent()
        result = agent.run()
        logger.info("Run complete: %s", result)
    except Exception as e:
        logger.exception("Agent run failed: %s", str(e))


def main():
    # --setup flag: hand off directly to setup_profile.py
    if "--setup" in sys.argv:
        print("\nTip: pass your resume path like this:")
        print("  python setup_profile.py path/to/your_resume.pdf\n")
        sys.exit(0)

    # Guard: block execution until profile is configured
    if not profile_is_configured():
        prompt_setup()

    # --now: single immediate run (for testing)
    if "--now" in sys.argv:
        logger.info("Running immediately (--now flag)...")
        run_agent()
        return

    # Default: schedule daily runs
    from config.settings import SETTINGS
    run_time = SETTINGS.get("schedule_time", "08:00")
    schedule.every().day.at(run_time).do(run_agent)

    logger.info("Job Agent started. Daily digest scheduled at %s.", run_time)
    logger.info("Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()

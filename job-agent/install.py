"""
install.py — Run this after downloading the zip to apply all updates.
Usage: python install.py
"""
import os, sys, json, shutil
from datetime import datetime

print("\n" + "="*55)
print("  Job Agent — Install / Verify")
print("="*55)

errors = []

# 1. Check all required files exist
required = [
    "scheduler.py",
    "agents/job_agent.py",
    "scrapers/indeed_scraper.py",
    "scrapers/linkedin_scraper.py",
    "scrapers/naukri_scraper.py",
    "utils/job_filter.py",
    "utils/email_sender.py",
    "utils/deduplicator.py",
    "config/profile.py",
    "config/settings.py",
]
print("\n[1] Checking files...")
for f in required:
    if os.path.exists(f):
        print(f"    ✓ {f}")
    else:
        print(f"    ✗ MISSING: {f}")
        errors.append(f"Missing: {f}")

# 2. Check .env
print("\n[2] Checking .env credentials...")
env_path = ".env"
if not os.path.exists(env_path):
    print("    ✗ .env not found — creating from .env.example")
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("    ✓ Created .env — please fill in your credentials")
    else:
        errors.append(".env file missing")
else:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    keys = {
        "GMAIL_USER":         ("Required", "Email digest won't send"),
        "GMAIL_APP_PASSWORD": ("Required", "Email digest won't send"),
        "RAPIDAPI_KEY":       ("Optional", "LinkedIn/Indeed via JSearch"),
        "ADZUNA_APP_ID":      ("Optional", "Indeed India via Adzuna"),
        "ADZUNA_APP_KEY":     ("Optional", "Indeed India via Adzuna"),
        "ANTHROPIC_API_KEY":  ("Optional", "Resume parsing via setup_profile.py"),
    }
    for key, (req, purpose) in keys.items():
        val = os.getenv(key, "").strip()
        if val:
            masked = val[:4] + "*" * (len(val)-4)
            print(f"    ✓ {key} = {masked}  [{req}]")
        else:
            sym = "✗" if req == "Required" else "·"
            print(f"    {sym} {key} = NOT SET  [{req}] — {purpose}")
            if req == "Required":
                errors.append(f"{key} not set in .env")

# 3. Check seen_jobs.json — auto-clear if stale
print("\n[3] Checking deduplication cache...")
seen_path = "data/seen_jobs.json"
if os.path.exists(seen_path):
    try:
        with open(seen_path) as f:
            data = json.load(f)
        count = len(data)
        if count > 0:
            # Check if all entries are from today
            today = datetime.utcnow().strftime("%Y-%m-%d")
            old = [k for k, v in data.items() if not v.startswith(today)]
            if old:
                os.remove(seen_path)
                print(f"    ✓ Cleared {count} stale entries (from previous runs)")
                print("      Next run will deliver a fresh digest.")
            else:
                print(f"    · {count} entries from today — will only send new jobs")
        else:
            print("    ✓ Cache empty — fresh run")
    except Exception as e:
        os.remove(seen_path)
        print(f"    ✓ Cleared corrupt cache: {e}")
else:
    print("    ✓ No cache — fresh run")

# 4. Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 5. Summary
print("\n" + "="*55)
if errors:
    print("\n  ✗ Issues to fix:")
    for e in errors:
        print(f"    - {e}")
    print()
    if any("GMAIL" in e for e in errors):
        print("  Gmail App Password setup:")
        print("  1. Go to: https://myaccount.google.com/security")
        print("     → Enable 2-Step Verification")
        print("  2. Go to: https://myaccount.google.com/apppasswords")
        print("     → Type 'Job Agent' → Create → copy 16-char code")
        print("  3. Add to .env:")
        print("     GMAIL_USER=your@gmail.com")
        print("     GMAIL_APP_PASSWORD=abcdefghijklmnop")
else:
    print("\n  ✓ Everything looks good!")
    print("\n  Run now:")
    print("    python scheduler.py --now")
    print()

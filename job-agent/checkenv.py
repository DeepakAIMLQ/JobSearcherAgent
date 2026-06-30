"""
check_env.py — Run this to diagnose .env loading issues
Usage: python check_env.py
"""
import os
import sys

print("\n" + "="*55)
print("  Job Agent — Environment Diagnostics")
print("="*55)

# 1. Show current working directory
cwd = os.getcwd()
print(f"\n[1] Working directory:\n    {cwd}")

# 2. Find .env file
env_path = os.path.join(cwd, ".env")
print(f"\n[2] Looking for .env at:\n    {env_path}")

if os.path.exists(env_path):
    print("    ✓ File EXISTS")
    with open(env_path) as f:
        lines = f.readlines()
    print(f"    ✓ File has {len(lines)} lines")
    print("\n    Contents (values masked):")
    for line in lines:
        line = line.rstrip()
        if not line or line.startswith("#"):
            print(f"    {line}")
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if val:
                masked = val[:3] + "*"*(len(val)-3) if len(val) > 3 else "***"
                print(f"    {key} = {masked}  ← ({len(val)} chars)")
            else:
                print(f"    {key} =   ← EMPTY — this is the problem!")
        else:
            print(f"    {line}")
else:
    print("    ✗ File NOT FOUND — this is the problem!")
    print(f"\n    Fix: create the file at exactly:\n    {env_path}")

# 3. Try loading with dotenv
print("\n[3] Testing python-dotenv load...")
try:
    from dotenv import load_dotenv
    loaded = load_dotenv(env_path, override=True)
    print(f"    load_dotenv returned: {loaded}")
except ImportError:
    print("    ✗ python-dotenv not installed! Run: pip install python-dotenv")
    sys.exit(1)

# 4. Check specific keys after load
print("\n[4] Key values after dotenv load:")
keys = ["GMAIL_USER", "GMAIL_APP_PASSWORD", "ANTHROPIC_API_KEY",
        "RAPIDAPI_KEY", "ADZUNA_APP_ID", "ADZUNA_APP_KEY"]
missing = []
for key in keys:
    val = os.getenv(key, "")
    if val:
        masked = val[:3] + "*"*(len(val)-3) if len(val) > 3 else "***"
        print(f"    ✓ {key} = {masked}  ({len(val)} chars)")
    else:
        print(f"    ✗ {key} = NOT SET")
        missing.append(key)

# 5. Summary
print("\n" + "="*55)
if "GMAIL_USER" in missing or "GMAIL_APP_PASSWORD" in missing:
    print("\n  PROBLEM: Gmail credentials missing or empty.")
    print("\n  Your .env file must contain these two lines:")
    print("  ─────────────────────────────────────────────")
    print("  GMAIL_USER=your.email@gmail.com")
    print("  GMAIL_APP_PASSWORD=your16charapppassword")
    print("  ─────────────────────────────────────────────")
    print("\n  No quotes, no spaces around =, no spaces in password.")
    print(f"\n  File location: {env_path}")
else:
    print("\n  ✓ Gmail credentials are loaded correctly!")
    print("  Run: python scheduler.py --now")
print()
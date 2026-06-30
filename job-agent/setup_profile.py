"""
setup_profile.py
================
Run this FIRST before starting the job agent.

Usage:
    python setup_profile.py path/to/your_resume.pdf

This will:
  1. Read your resume PDF
  2. Call Claude API to extract your profile
  3. Write config/profile.py automatically
  4. You can then run: python scheduler.py
"""

import sys
import os
import base64
import json
import re

def check_dependencies():
    missing = []
    try:
        import anthropic
    except ImportError:
        missing.append("anthropic")
    try:
        import dotenv
    except ImportError:
        missing.append("python-dotenv")
    if missing:
        print(f"\n[ERROR] Missing packages: {', '.join(missing)}")
        print(f"  Run: pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert Python developer and job search assistant.
The user will provide a resume PDF. Extract all relevant information and generate a complete, ready-to-use profile.py file for a job agent.

The output MUST be only valid Python code — no markdown, no backticks, no explanations, no preamble.
Start directly with the triple-quoted docstring and end with the closing brace of the PROFILE dict.

Generate a PROFILE dict with these exact keys:
- name (str): Full name from resume
- email_to (str): Email from resume
- target_titles (list of str): 12-16 realistic senior-level job titles matching their seniority and domain
- skills (list of str): All technical and domain skills from resume, grouped by category using inline comments
- min_experience_years (int): Conservative estimate based on total years of experience
- max_experience_years (int): Set to 35
- locations (list of str): Extract city/country from resume, add nearby cities, "Remote", and "India" if applicable
- remote_ok (bool): True
- preferred_companies (list of str): 20-25 relevant companies — MAANG, domain-specific leaders, top companies in their industry vertical, and major Indian IT/consulting companies if the person is India-based
- excluded_companies (list of str): empty list []
- search_queries (list of str): 6-8 targeted search query strings combining their top titles + key skills
- score_weights (dict): title_match 0.35, skills_match 0.30, location_match 0.15, company_preference 0.10, recency 0.10
- min_relevance_score (float): 0.45
- max_jobs_in_email (int): 25

Use inline # comments to label groups within the skills and preferred_companies lists.
Make it production-ready and specific to this exact person's resume."""


def read_pdf_as_base64(pdf_path: str) -> str:
    with open(pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def generate_profile(pdf_path: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n[ERROR] ANTHROPIC_API_KEY not set in your .env file.")
        print("  Add this line to your .env:  ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"  Reading: {pdf_path}")
    pdf_data = read_pdf_as_base64(pdf_path)

    print("  Sending to Claude for analysis...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Generate the profile.py file for this resume. Output only valid Python code, no markdown fences.",
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text
    # Strip any accidental markdown fences
    code = re.sub(r"^```python\s*", "", raw.strip())
    code = re.sub(r"^```\s*", "", code)
    code = re.sub(r"```$", "", code).strip()
    return code


def write_profile(code: str, output_path: str = "config/profile.py"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Backup existing profile if present
    if os.path.exists(output_path):
        backup = output_path.replace(".py", "_backup.py")
        os.rename(output_path, backup)
        print(f"  Backed up existing profile to: {backup}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"  Written: {output_path}")


def validate_profile(output_path: str) -> bool:
    """Quick sanity check — make sure PROFILE dict loaded correctly."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("profile", output_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        profile = mod.PROFILE
        required = ["name", "email_to", "target_titles", "skills", "search_queries"]
        for key in required:
            assert key in profile and profile[key], f"Missing or empty key: {key}"
        return True
    except Exception as e:
        print(f"\n[WARNING] Profile validation issue: {e}")
        print("  The file was written but may need manual review.")
        return False


def print_summary(output_path: str):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("profile", output_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        p = mod.PROFILE
        print("\n  ── Profile Summary ─────────────────────────────")
        print(f"  Name          : {p.get('name', '')}")
        print(f"  Email         : {p.get('email_to', '')}")
        print(f"  Target titles : {len(p.get('target_titles', []))} roles")
        print(f"  Skills        : {len(p.get('skills', []))} skills")
        print(f"  Locations     : {', '.join(p.get('locations', [])[:4])} ...")
        print(f"  Search queries: {len(p.get('search_queries', []))} queries")
        print(f"  Companies     : {len(p.get('preferred_companies', []))} preferred")
        print("  ────────────────────────────────────────────────")
    except Exception:
        pass


def main():
    print("\n" + "=" * 55)
    print("  Job Agent — Profile Setup")
    print("=" * 55)

    if len(sys.argv) < 2:
        print("\nUsage:  python setup_profile.py <path_to_resume.pdf>")
        print("\nExample:")
        print("  python setup_profile.py resume.pdf")
        print("  python setup_profile.py ~/Downloads/Deepak_Resume.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"\n[ERROR] File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.lower().endswith(".pdf"):
        print(f"\n[ERROR] File must be a PDF: {pdf_path}")
        sys.exit(1)

    output_path = "config/profile.py"

    print(f"\nStep 1/3  Reading resume...")
    print(f"Step 2/3  Generating profile with Claude AI...")
    code = generate_profile(pdf_path)

    print(f"Step 3/3  Writing {output_path}...")
    write_profile(code, output_path)

    valid = validate_profile(output_path)
    print_summary(output_path)

    if valid:
        print("\n[OK] profile.py created successfully!")
        print("\nNext steps:")
        print("  1. Review config/profile.py and tweak if needed")
        print("  2. Make sure your .env has GMAIL_USER, GMAIL_APP_PASSWORD, RAPIDAPI_KEY")
        print("  3. Run:  python scheduler.py --now   (to test)")
        print("  4. Run:  python scheduler.py         (to start daily digest)")
    else:
        print("\n[OK] profile.py written. Please review it before running the agent.")

    print()


if __name__ == "__main__":
    main()

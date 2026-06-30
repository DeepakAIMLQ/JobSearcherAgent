"""
Email Sender -- Anti-Spam + India-only digest
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

SOURCE_COLORS = {
    "LinkedIn":      ("#0a66c2", "LinkedIn"),
    "Indeed":        ("#e6322d", "Indeed"),
    "Naukri":        ("#ff7555", "Naukri"),
    "Adzuna/Indeed": ("#e6322d", "Indeed"),
    "Remotive":      ("#00a550", "Remotive"),
    "TheMuse":       ("#5c6bc0", "The Muse"),
    "Arbeitnow":     ("#1976d2", "Arbeitnow"),
}


class EmailSender:

    def __init__(self, settings: Dict[str, Any]):
        self.host     = settings.get("smtp_host", "smtp.gmail.com")
        self.port     = settings.get("smtp_port", 587)
        self.user     = settings.get("smtp_user", "")
        self.password = settings.get("smtp_password", "")

    def send_digest(self, jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> bool:
        if not self.user or not self.password:
            logger.error(
                "Gmail credentials not configured.\n"
                "  Add to .env:\n"
                "    GMAIL_USER=your@gmail.com\n"
                "    GMAIL_APP_PASSWORD=your16charapppassword\n"
                "  Get App Password at: https://myaccount.google.com/apppasswords"
            )
            return False

        to_email = profile.get("email_to", self.user)
        name     = profile.get("name", "")
        date_str = datetime.now().strftime("%B %d, %Y")
        subject  = f"AI Job Digest ({len(jobs)} Roles, 50%+ Match) -- {date_str}"

        html = self._build_html(jobs, profile, date_str)
        text = self._build_text(jobs, date_str)

        msg = MIMEMultipart("alternative")
        msg["Subject"]               = subject
        msg["From"]                  = f"{name} Job Agent <{self.user}>"
        msg["To"]                    = to_email
        msg["Reply-To"]              = self.user
        msg["Date"]                  = formatdate(localtime=True)
        msg["Message-ID"]            = make_msgid(domain=self.user.split("@")[-1])
        msg["X-Mailer"]              = "JobAgent/2.0"
        msg["X-Priority"]            = "3"
        msg["Precedence"]            = "bulk"
        msg["List-Unsubscribe"]      = f"<mailto:{self.user}?subject=Unsubscribe>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html",  "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.user, self.password)
                server.sendmail(self.user, to_email, msg.as_string())
            logger.info("[OK] Email digest sent to %s (%d jobs)", to_email, len(jobs))
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Gmail authentication failed.\n"
                "  Use an App Password (16 chars), not your Gmail password.\n"
                "  Create one at: https://myaccount.google.com/apppasswords"
            )
            return False
        except Exception as e:
            logger.error("Email send failed: %s", str(e))
            return False

    # -- HTML Builder ----------------------------------------------
    def _build_html(self, jobs: List[Dict], profile: Dict, date_str: str) -> str:
        name       = profile.get("name", "")
        high_match = sum(1 for j in jobs if int(j.get("relevance_score", 0) * 100) >= 75)
        sources    = {}
        for j in jobs:
            src = j.get("source", "Other")
            sources[src] = sources.get(src, 0) + 1

        source_pills = "".join(
            f'<span style="background:{SOURCE_COLORS.get(s, ("#555",""))[0]};color:#fff;'
            f'padding:3px 10px;border-radius:12px;font-size:11px;margin:2px">'
            f'{SOURCE_COLORS.get(s,(s,s))[1]}: {c}</span>'
            for s, c in sources.items()
        )

        cards = ""
        for i, job in enumerate(jobs, 1):
            pct         = int(job.get("relevance_score", 0) * 100)
            bar_color   = "#16a34a" if pct >= 75 else "#d97706" if pct >= 60 else "#2563eb"
            src_color, src_label = SOURCE_COLORS.get(job["source"], ("#555", job["source"]))
            remote_tag  = (
                '<span style="background:#dcfce7;color:#166534;padding:2px 8px;'
                'border-radius:4px;font-size:11px;margin-left:6px"> Remote</span>'
            ) if job.get("is_remote") else ""
            salary_row  = (
                f'<p style="margin:3px 0;font-size:12px;color:#555"> {job["salary"]}</p>'
            ) if job.get("salary") else ""
            exp_row     = (
                f'<p style="margin:3px 0;font-size:12px;color:#555"> {job["experience_required"]}</p>'
            ) if job.get("experience_required") else ""
            desc        = job.get("description", "")[:260]
            if len(job.get("description", "")) > 260:
                desc += "..."
            desc = desc.replace("<","&lt;").replace(">","&gt;")

            breakdown  = job.get("score_breakdown", {})
            score_rows = "".join(
                f'<span style="font-size:10px;color:#6b7280;margin-right:8px">'
                f'{k.title()}: {int(v*100)}%</span>'
                for k, v in breakdown.items()
            )

            cards += f"""
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
            padding:16px;margin-bottom:12px;border-left:4px solid {bar_color}">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td style="vertical-align:top">
        <p style="margin:0 0 2px;font-size:15px;font-weight:600;color:#111">
          {i}. {job['title']}
        </p>
        <p style="margin:0;font-size:13px;font-weight:500;color:#374151">{job['company']}</p>
        <p style="margin:3px 0;font-size:12px;color:#6b7280"> {job['location']}</p>
      </td>
      <td style="text-align:right;vertical-align:top;white-space:nowrap;padding-left:12px">
        <div style="font-size:26px;font-weight:700;color:{bar_color};line-height:1">{pct}%</div>
        <div style="font-size:9px;color:#9ca3af;text-align:center">MATCH</div>
      </td>
    </tr>
  </table>

  <!-- Match bar -->
  <div style="background:#f3f4f6;border-radius:4px;height:5px;margin:8px 0 4px">
    <div style="background:{bar_color};width:{pct}%;height:5px;border-radius:4px"></div>
  </div>
  <div style="margin-bottom:8px">{score_rows}</div>

  <div style="margin:6px 0">
    <span style="background:{src_color};color:#fff;padding:2px 8px;
                 border-radius:4px;font-size:11px">{src_label}</span>
    <span style="background:#fef3c7;color:#92400e;padding:2px 8px;
                 border-radius:4px;font-size:11px;margin-left:4px"> India</span>
    {remote_tag}
  </div>

  {salary_row}{exp_row}
  <p style="color:#4b5563;font-size:12px;line-height:1.6;margin:8px 0 10px">{desc}</p>
  <a href="{job['apply_url']}"
     style="display:inline-block;background:#4f46e5;color:#fff;padding:7px 18px;
            border-radius:6px;text-decoration:none;font-size:12px;font-weight:600">
    Apply Now ->
  </a>
</div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Job Digest -- {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif">
<div style="max-width:620px;margin:0 auto;padding:20px 14px">

  <!-- Header -->
  <div style="background:#1e3a5f;border-radius:12px;padding:24px 28px;margin-bottom:16px">
    <h1 style="color:#fff;margin:0 0 4px;font-size:20px"> Your Daily AI Job Digest</h1>
    <p style="color:#93c5fd;margin:0;font-size:13px">
      {date_str} &nbsp;*&nbsp; Top {len(jobs)} roles &nbsp;*&nbsp; 50%+ match &nbsp;*&nbsp;  India only
    </p>
  </div>

  <!-- Stats bar -->
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;
                margin-bottom:14px">
    <tr>
      <td style="padding:12px;text-align:center;border-right:1px solid #f3f4f6">
        <div style="font-size:24px;font-weight:700;color:#4f46e5">{len(jobs)}</div>
        <div style="font-size:11px;color:#6b7280">Jobs Today</div>
      </td>
      <td style="padding:12px;text-align:center;border-right:1px solid #f3f4f6">
        <div style="font-size:24px;font-weight:700;color:#16a34a">{high_match}</div>
        <div style="font-size:11px;color:#6b7280">High Match 75%+</div>
      </td>
      <td style="padding:12px;text-align:center">
        <div style="font-size:13px;font-weight:600;color:#374151;line-height:1.6">{source_pills}</div>
        <div style="font-size:11px;color:#6b7280;margin-top:2px">Sources</div>
      </td>
    </tr>
  </table>

  <!-- Job cards -->
  {cards}

  <!-- Footer -->
  <div style="text-align:center;padding:14px;color:#9ca3af;font-size:11px;line-height:1.8">
    <p style="margin:0">AI Job Agent * Daily digest at 8:00 AM * India only * 50%+ match</p>
    <p style="margin:0">Hi {name} -- digest personalised from your resume profile</p>
  </div>

</div>
</body>
</html>"""

    def _build_text(self, jobs: List[Dict], date_str: str) -> str:
        lines = [
            f"AI Job Digest -- {date_str}",
            f"Top {len(jobs)} roles | India only | 50%+ match",
            "=" * 55, ""
        ]
        for i, job in enumerate(jobs, 1):
            pct = int(job.get("relevance_score", 0) * 100)
            lines += [
                f"{i}. [{pct}% match] {job['title']}",
                f"   Company  : {job['company']}",
                f"   Location : {job['location']}",
                f"   Source   : {job['source']}",
                f"   Apply    : {job['apply_url']}",
                ""
            ]
        return "\n".join(lines)

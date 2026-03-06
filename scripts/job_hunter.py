"""
Job Hunter Agent for Nikhil Sadaphule
Scrapes SOC Engineer jobs from multiple sources and sends alerts via Gmail + Telegram
"""

import os
import json
import hashlib
import smtplib
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIG — all values loaded from GitHub Secrets
# ─────────────────────────────────────────────
GMAIL_USER       = os.environ["GMAIL_USER"]         # your Gmail address
GMAIL_APP_PASS   = os.environ["GMAIL_APP_PASS"]     # Gmail App Password
GMAIL_TO         = os.environ["GMAIL_TO"]           # recipient email (can be same)
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]     # Telegram bot token
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # your Telegram chat ID

SEEN_JOBS_FILE = "seen_jobs.json"

JOB_SEARCHES = [
    {
        "source": "Indeed India",
        "url": "https://in.indeed.com/jobs?q=SOC+Analyst+entry+level&l=Pune%2C+Maharashtra",
        "label": "Indeed — Pune"
    },
    {
        "source": "Indeed India",
        "url": "https://in.indeed.com/jobs?q=SOC+Engineer+fresher&l=Mumbai%2C+Maharashtra",
        "label": "Indeed — Mumbai"
    },
    {
        "source": "Indeed India",
        "url": "https://in.indeed.com/jobs?q=SOC+Analyst+remote&l=India",
        "label": "Indeed — Remote India"
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

KEYWORDS = [
    "soc", "security analyst", "siem", "splunk", "qradar",
    "sentinel", "incident response", "threat hunting",
    "cloud security", "cybersecurity", "information security"
]


# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────
def scrape_indeed(url, label):
    jobs = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", class_="job_seen_beacon")
        for card in cards:
            title_el = card.find("h2", class_="jobTitle")
            company_el = card.find("span", attrs={"data-testid": "company-name"})
            location_el = card.find("div", attrs={"data-testid": "text-location"})
            link_el = card.find("a", href=True)

            title    = title_el.get_text(strip=True) if title_el else "N/A"
            company  = company_el.get_text(strip=True) if company_el else "N/A"
            location = location_el.get_text(strip=True) if location_el else "N/A"
            link     = ("https://in.indeed.com" + link_el["href"]) if link_el else url

            if any(kw in title.lower() for kw in KEYWORDS):
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "source": label,
                    "date": datetime.now().strftime("%d %b %Y")
                })
    except Exception as e:
        print(f"[WARN] Scraping failed for {label}: {e}")
    return jobs


def deduplicate(jobs):
    """Return only jobs not seen before, update seen list."""
    try:
        with open(SEEN_JOBS_FILE, "r") as f:
            seen = set(json.load(f))
    except FileNotFoundError:
        seen = set()

    new_jobs = []
    for job in jobs:
        job_id = hashlib.md5(f"{job['title']}{job['company']}".encode()).hexdigest()
        if job_id not in seen:
            seen.add(job_id)
            new_jobs.append(job)

    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

    return new_jobs


def score_job(job):
    """Score job relevance 1–10 based on title keywords."""
    score = 5
    title = job["title"].lower()
    high  = ["soc", "security analyst", "siem", "incident response"]
    bonus = ["splunk", "qradar", "sentinel", "threat", "cloud security"]
    for kw in high:
        if kw in title:
            score += 1
    for kw in bonus:
        if kw in title:
            score += 0.5
    return min(round(score, 1), 10)


# ─────────────────────────────────────────────
# GMAIL
# ─────────────────────────────────────────────
def build_html_email(jobs, date_str):
    rows = ""
    for i, j in enumerate(jobs, 1):
        score = score_job(j)
        bar_color = "#22c55e" if score >= 8 else "#f59e0b" if score >= 6 else "#ef4444"
        rows += f"""
        <tr style="background:{'#f9fafb' if i%2==0 else '#ffffff'}">
          <td style="padding:12px;font-weight:600;color:#1e293b">{j['title']}</td>
          <td style="padding:12px;color:#334155">{j['company']}</td>
          <td style="padding:12px;color:#64748b">{j['location']}</td>
          <td style="padding:12px;color:#64748b">{j['source']}</td>
          <td style="padding:12px;text-align:center">
            <span style="background:{bar_color};color:white;padding:3px 10px;
                         border-radius:12px;font-size:13px;font-weight:bold">
              {score}/10
            </span>
          </td>
          <td style="padding:12px">
            <a href="{j['link']}" style="background:#3b82f6;color:white;padding:6px 14px;
               border-radius:6px;text-decoration:none;font-size:13px">Apply →</a>
          </td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px">
      <div style="max-width:900px;margin:auto;background:white;border-radius:12px;
                  box-shadow:0 2px 12px rgba(0,0,0,0.1);overflow:hidden">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1e3a5f,#3b82f6);padding:28px 32px">
          <h1 style="color:white;margin:0;font-size:24px">🛡️ Daily SOC Job Digest</h1>
          <p style="color:#bfdbfe;margin:6px 0 0">
            {date_str} &nbsp;|&nbsp; {len(jobs)} new opportunities found for Nikhil Sadaphule
          </p>
        </div>

        <!-- Summary bar -->
        <div style="display:flex;gap:0;border-bottom:1px solid #e2e8f0">
          <div style="flex:1;padding:16px 24px;text-align:center;border-right:1px solid #e2e8f0">
            <div style="font-size:28px;font-weight:bold;color:#3b82f6">{len(jobs)}</div>
            <div style="font-size:12px;color:#94a3b8;margin-top:2px">NEW JOBS TODAY</div>
          </div>
          <div style="flex:1;padding:16px 24px;text-align:center;border-right:1px solid #e2e8f0">
            <div style="font-size:28px;font-weight:bold;color:#22c55e">
              {len([j for j in jobs if score_job(j) >= 8])}
            </div>
            <div style="font-size:12px;color:#94a3b8;margin-top:2px">HIGH FIT (8+)</div>
          </div>
          <div style="flex:1;padding:16px 24px;text-align:center">
            <div style="font-size:28px;font-weight:bold;color:#f59e0b">
              {len(set(j['company'] for j in jobs))}
            </div>
            <div style="font-size:12px;color:#94a3b8;margin-top:2px">COMPANIES</div>
          </div>
        </div>

        <!-- Table -->
        <div style="overflow-x:auto;padding:24px">
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <thead>
              <tr style="background:#f8fafc">
                <th style="padding:12px;text-align:left;color:#475569;border-bottom:2px solid #e2e8f0">Job Title</th>
                <th style="padding:12px;text-align:left;color:#475569;border-bottom:2px solid #e2e8f0">Company</th>
                <th style="padding:12px;text-align:left;color:#475569;border-bottom:2px solid #e2e8f0">Location</th>
                <th style="padding:12px;text-align:left;color:#475569;border-bottom:2px solid #e2e8f0">Source</th>
                <th style="padding:12px;text-align:center;color:#475569;border-bottom:2px solid #e2e8f0">Fit Score</th>
                <th style="padding:12px;text-align:left;color:#475569;border-bottom:2px solid #e2e8f0">Link</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>

        <!-- Footer -->
        <div style="background:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;
                    font-size:12px;color:#94a3b8;text-align:center">
          🤖 Automated by your Job Hunter Agent &nbsp;|&nbsp;
          Searching: Indeed India (Pune, Mumbai, Remote) &nbsp;|&nbsp;
          Profile: SOC Engineer · Entry Level · SIEM · Incident Response
        </div>
      </div>
    </body></html>"""
    return html


def send_gmail(jobs, date_str):
    if not jobs:
        print("[INFO] No new jobs — skipping Gmail.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🛡️ {len(jobs)} New SOC Jobs Found — {date_str}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = GMAIL_TO

    html = build_html_email(jobs, date_str)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_USER, GMAIL_TO, msg.as_string())
    print(f"[OK] Gmail sent — {len(jobs)} jobs")


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(jobs, date_str):
    if not jobs:
        print("[INFO] No new jobs — skipping Telegram.")
        return

    high_fit = [j for j in jobs if score_job(j) >= 8]
    top      = sorted(jobs, key=score_job, reverse=True)[:5]

    # Summary message
    summary = (
        f"🛡️ *SOC Job Digest — {date_str}*\n\n"
        f"📊 *{len(jobs)}* new jobs found\n"
        f"🟢 *{len(high_fit)}* high-fit roles (8+/10)\n"
        f"🏢 *{len(set(j['company'] for j in jobs))}* companies\n\n"
        f"─────────────────────\n"
        f"🔝 *Top {len(top)} Picks Today:*\n\n"
    )

    for i, j in enumerate(top, 1):
        score = score_job(j)
        emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
        summary += (
            f"{emoji} *{i}. {j['title']}*\n"
            f"   🏢 {j['company']}\n"
            f"   📍 {j['location']}\n"
            f"   ⭐ Fit: {score}/10\n"
            f"   🔗 [Apply Here]({j['link']})\n\n"
        )

    summary += "─────────────────────\n🤖 _Your Job Hunter Agent_"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": summary,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }, timeout=15)

    if resp.status_code == 200:
        print(f"[OK] Telegram sent — top {len(top)} jobs")
    else:
        print(f"[ERROR] Telegram failed: {resp.text}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    date_str = datetime.now().strftime("%d %B %Y")
    print(f"\n🔍 Job Hunter started — {date_str}\n")

    all_jobs = []
    for search in JOB_SEARCHES:
        print(f"  Scraping {search['label']}...")
        found = scrape_indeed(search["url"], search["label"])
        print(f"  → {len(found)} jobs found")
        all_jobs.extend(found)

    # Sort by fit score
    all_jobs.sort(key=score_job, reverse=True)

    # Remove duplicates from previous runs
    new_jobs = deduplicate(all_jobs)
    print(f"\n✅ {len(new_jobs)} NEW jobs after deduplication\n")

    # Send alerts
    send_gmail(new_jobs, date_str)
    send_telegram(new_jobs, date_str)

    print("\n🎯 Job Hunter finished.\n")


if __name__ == "__main__":
    main()

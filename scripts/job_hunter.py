"""
Final Full Coverage SOC Job Hunter — Nikhil Sadaphule
Uses JSearch API (RapidAPI) — searches LinkedIn, Indeed, 
Glassdoor, Google Jobs, Naukri, company websites all at once
Notifications: Gmail + Telegram
"""

import os
import json
import hashlib
import smtplib
import requests
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────────
# CONFIG — loaded from GitHub Secrets
# ─────────────────────────────────────────────
GMAIL_USER       = os.environ["GMAIL_USER"]
GMAIL_APP_PASS   = os.environ["GMAIL_APP_PASS"]
GMAIL_TO         = os.environ["GMAIL_TO"]
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
RAPIDAPI_KEY     = os.environ["RAPIDAPI_KEY"]

SEEN_JOBS_FILE = "seen_jobs.json"

# ─────────────────────────────────────────────
# SEARCH QUERIES
# Covers: LinkedIn, Indeed, Glassdoor, Naukri,
#         Google Jobs, and company websites
# ─────────────────────────────────────────────
SEARCH_QUERIES = [
    # Location specific
    "SOC Analyst entry level Pune India",
    "SOC Analyst fresher Mumbai India",
    "SOC Engineer entry level India remote",
    # Tool specific
    "SIEM analyst entry level India Splunk",
    "QRadar SOC analyst India",
    "Microsoft Sentinel SOC analyst India",
    # Role specific
    "Security Operations Center L1 analyst India",
    "Incident Response analyst fresher India",
    "Threat detection analyst entry level India",
    "Cybersecurity analyst fresher Pune Mumbai",
    # Company specific
    "SOC analyst Wipro entry level",
    "SOC analyst Deloitte India fresher",
]

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
def score_job(job):
    score = 5
    title    = job.get("title", "").lower()
    company  = job.get("company", "").lower()
    location = job.get("location", "").lower()

    # Title keywords
    high  = ["soc", "security analyst", "siem", "incident response", "security operations"]
    bonus = ["splunk", "qradar", "sentinel", "threat", "cloud security", "l1", "tier 1"]
    fresh = ["entry", "fresher", "junior", "graduate", "trainee", "0-2", "0-1"]

    for kw in high:
        if kw in title: score += 1
    for kw in bonus:
        if kw in title: score += 0.5
    for kw in fresh:
        if kw in title or kw in company: score += 0.5

    # Location bonus
    if any(loc in location.lower() for loc in ["pune", "mumbai", "india", "remote"]):
        score += 0.5

    return min(round(score, 1), 10)


# ─────────────────────────────────────────────
# JSEARCH API — searches ALL job platforms
# ─────────────────────────────────────────────
def search_jsearch():
    all_jobs = []
    print("\n[JSearch] Searching across LinkedIn, Indeed, Glassdoor, Naukri + more...")
    print("=" * 55)

    seen_in_session = set()

    for query in SEARCH_QUERIES:
        try:
            resp = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                headers={
                    "x-rapidapi-host": "jsearch.p.rapidapi.com",
                    "x-rapidapi-key": RAPIDAPI_KEY
                },
                params={
                    "query": query,
                    "page": "1",
                    "num_pages": "1",
                    "country": "in",
                    "date_posted": "month",
                },
                timeout=20
            )

            if resp.status_code != 200:
                print(f"  [{resp.status_code}] Failed: {query}")
                continue

            data = resp.json()
            results = data.get("data", [])
            new_count = 0

            for job in results:
                title    = job.get("job_title", "N/A")
                company  = job.get("employer_name", "N/A")
                location = f"{job.get('job_city', '')}, {job.get('job_country', 'India')}".strip(", ")
                link     = job.get("job_apply_link") or job.get("job_google_link", "#")
                source   = job.get("job_publisher", "JSearch")
                remote   = "🌐 Remote" if job.get("job_is_remote") else location

                # Session dedup
                job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()
                if job_id in seen_in_session:
                    continue
                seen_in_session.add(job_id)

                all_jobs.append({
                    "title":   title,
                    "company": company,
                    "location": remote,
                    "link":    link,
                    "source":  source,
                    "date":    datetime.now().strftime("%d %b %Y")
                })
                new_count += 1

            print(f"  ✓ '{query[:45]}' → {new_count} jobs")
            time.sleep(0.8)  # respect rate limits

        except Exception as e:
            print(f"  [WARN] Query failed '{query}': {e}")

    print(f"\n  Total raw jobs: {len(all_jobs)}")
    return all_jobs


# ─────────────────────────────────────────────
# DEDUPLICATION (across days)
# ─────────────────────────────────────────────
def deduplicate(jobs):
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


# ─────────────────────────────────────────────
# GMAIL — Beautiful HTML digest
# ─────────────────────────────────────────────
def build_html_email(jobs, date_str):
    rows = ""
    for i, j in enumerate(jobs, 1):
        score = score_job(j)
        color = "#22c55e" if score >= 8 else "#f59e0b" if score >= 6 else "#ef4444"
        rows += f"""
        <tr style="background:{'#f9fafb' if i%2==0 else '#ffffff'}">
          <td style="padding:12px;font-weight:600;color:#1e293b;max-width:220px">{j['title']}</td>
          <td style="padding:12px;color:#334155">{j['company']}</td>
          <td style="padding:12px;color:#64748b">{j['location']}</td>
          <td style="padding:12px;color:#94a3b8;font-size:12px">{j['source']}</td>
          <td style="padding:12px;text-align:center">
            <span style="background:{color};color:white;padding:3px 10px;
                         border-radius:12px;font-size:13px;font-weight:bold">
              {score}/10
            </span>
          </td>
          <td style="padding:12px">
            <a href="{j['link']}" style="background:#3b82f6;color:white;padding:6px 14px;
               border-radius:6px;text-decoration:none;font-size:13px">Apply →</a>
          </td>
        </tr>"""

    high_fit = len([j for j in jobs if score_job(j) >= 8])
    companies = len(set(j['company'] for j in jobs))

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px">
      <div style="max-width:960px;margin:auto;background:white;border-radius:12px;
                  box-shadow:0 2px 12px rgba(0,0,0,0.1);overflow:hidden">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1e3a5f,#3b82f6);padding:28px 32px">
          <h1 style="color:white;margin:0;font-size:24px">🛡️ Daily SOC Job Digest</h1>
          <p style="color:#bfdbfe;margin:8px 0 0;font-size:14px">
            {date_str} &nbsp;|&nbsp; Powered by JSearch — LinkedIn · Indeed · Glassdoor · Naukri · Google Jobs
          </p>
        </div>

        <!-- Stats -->
        <div style="display:flex;border-bottom:1px solid #e2e8f0">
          <div style="flex:1;padding:20px;text-align:center;border-right:1px solid #e2e8f0">
            <div style="font-size:32px;font-weight:bold;color:#3b82f6">{len(jobs)}</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px">NEW JOBS TODAY</div>
          </div>
          <div style="flex:1;padding:20px;text-align:center;border-right:1px solid #e2e8f0">
            <div style="font-size:32px;font-weight:bold;color:#22c55e">{high_fit}</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px">HIGH FIT (8+/10)</div>
          </div>
          <div style="flex:1;padding:20px;text-align:center">
            <div style="font-size:32px;font-weight:bold;color:#f59e0b">{companies}</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px">COMPANIES</div>
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
                <th style="padding:12px;text-align:left;color:#475569;border-bottom:2px solid #e2e8f0">Apply</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>

        <!-- Footer -->
        <div style="background:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;
                    font-size:12px;color:#94a3b8;text-align:center">
          🤖 Automated Job Hunter for Nikhil Sadaphule &nbsp;|&nbsp;
          Sources: LinkedIn · Indeed · Glassdoor · Naukri · Google Jobs &nbsp;|&nbsp;
          Profile: SOC Engineer · Entry Level · Pune/Mumbai/Remote
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
    msg.attach(MIMEText(build_html_email(jobs, date_str), "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_USER, GMAIL_TO, msg.as_string())
    print(f"[OK] Gmail sent — {len(jobs)} jobs to {GMAIL_TO}")


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(jobs, date_str):
    if not jobs:
        print("[INFO] No new jobs — skipping Telegram.")
        return

    high_fit = [j for j in jobs if score_job(j) >= 8]
    top5     = sorted(jobs, key=score_job, reverse=True)[:5]

    msg = (
        f"🛡️ *SOC Job Digest — {date_str}*\n\n"
        f"📊 *{len(jobs)}* new jobs found today\n"
        f"🟢 *{len(high_fit)}* high\\-fit roles \\(8\\+/10\\)\n"
        f"🏢 *{len(set(j['company'] for j in jobs))}* companies hiring\n\n"
        f"📡 *Sources:* LinkedIn · Indeed · Glassdoor · Naukri\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔝 *Top 5 Picks For You:*\n\n"
    )

    for i, j in enumerate(top5, 1):
        score = score_job(j)
        emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
        # Escape special chars for Telegram MarkdownV2
        title   = j['title'].replace('-','\\-').replace('.','\\.')
        company = j['company'].replace('-','\\-').replace('.','\\.')
        loc     = j['location'].replace('-','\\-').replace('.','\\.')
        msg += (
            f"{emoji} *{i}\\. {title}*\n"
            f"   🏢 {company}\n"
            f"   📍 {loc}\n"
            f"   ⭐ Fit Score: {score}/10\n"
            f"   🔗 [Apply Here]({j['link']})\n\n"
        )

    msg += "━━━━━━━━━━━━━━━━━━━━━\n🤖 _Your Automated Job Hunter_"

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True
        },
        timeout=15
    )
    if resp.status_code == 200:
        print(f"[OK] Telegram sent — top {len(top5)} jobs")
    else:
        print(f"[ERROR] Telegram: {resp.status_code} — {resp.text}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    date_str = datetime.now().strftime("%d %B %Y")
    print(f"\n{'='*55}")
    print(f"  SOC Job Hunter — {date_str}")
    print(f"  Searching: LinkedIn, Indeed, Glassdoor, Naukri")
    print(f"{'='*55}")

    # Search all platforms via JSearch
    all_jobs = search_jsearch()

    # Sort by fit score
    all_jobs.sort(key=score_job, reverse=True)

    # Remove jobs seen in previous runs
    new_jobs = deduplicate(all_jobs)

    print(f"\n{'='*55}")
    print(f"  New jobs (not seen before): {len(new_jobs)}")
    print(f"{'='*55}\n")

    # Send notifications
    send_gmail(new_jobs, date_str)
    send_telegram(new_jobs, date_str)

    print("\n✅ Job Hunter finished successfully!\n")


if __name__ == "__main__":
    main()

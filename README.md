# 🛡️ SOC Job Hunter — Nikhil Sadaphule
### Automated Daily Job Alerts via Gmail + Telegram using GitHub Actions

---

## 📁 Project Structure

```
job-hunter/
├── .github/
│   └── workflows/
│       └── job_hunter.yml      ← GitHub Actions schedule
├── scripts/
│   └── job_hunter.py           ← Main scraping + notification script
├── requirements.txt
└── README.md
```

---

## ⚙️ COMPLETE SETUP GUIDE (Step by Step)

---

### STEP 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) → click **"New"**
2. Name it: `soc-job-hunter`
3. Set it to **Private** (recommended)
4. Click **"Create repository"**
5. Upload all files from this folder into the repo (maintain the folder structure)

---

### STEP 2 — Set Up Gmail App Password

> Gmail blocks direct password login — you need an "App Password"

1. Go to your Google Account → [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** → **2-Step Verification** → Enable it if not already
3. Go back to Security → scroll down → **App Passwords**
4. Select app: **Mail** | Select device: **Other** → type `Job Hunter`
5. Click **Generate** → Copy the 16-character password shown (e.g. `abcd efgh ijkl mnop`)
6. Save it — you'll need it in Step 4

---

### STEP 3 — Set Up Telegram Bot

> You'll create a personal Telegram bot that sends you job alerts

#### 3a. Create the Bot
1. Open Telegram → Search for **@BotFather**
2. Send: `/newbot`
3. Give it a name: `Nikhil Job Hunter`
4. Give it a username: `nikhil_job_hunter_bot` (must end in `bot`)
5. BotFather will reply with your **Bot Token** — looks like:
   ```
   7412345678:AAFabcdefghijklmnopqrstuvwxyz123456
   ```
6. Copy and save this token

#### 3b. Get Your Chat ID
1. Search for your new bot in Telegram and click **Start**
2. Send any message like: `hello`
3. Open this URL in your browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
4. Look for `"chat":{"id":` — the number after it is your **Chat ID**
   ```json
   "chat": { "id": 987654321 }
   ```
5. Save this number

---

### STEP 4 — Add GitHub Secrets

> Secrets keep your passwords safe — never hardcode them in code

1. In your GitHub repo → click **Settings** tab
2. Left sidebar → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** for each of the 5 secrets below:

| Secret Name       | Value                              | Example                          |
|-------------------|------------------------------------|----------------------------------|
| `GMAIL_USER`      | Your Gmail address                 | `nikhil@gmail.com`               |
| `GMAIL_APP_PASS`  | 16-char App Password from Step 2   | `abcdefghijklmnop`               |
| `GMAIL_TO`        | Where to send emails               | `nikhil@gmail.com`               |
| `TELEGRAM_TOKEN`  | Bot token from Step 3a             | `7412345678:AAFabc...`           |
| `TELEGRAM_CHAT_ID`| Your chat ID from Step 3b          | `987654321`                      |

---

### STEP 5 — Enable GitHub Actions

1. In your repo → click **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You'll see **"🛡️ Daily SOC Job Hunter"** listed

---

### STEP 6 — Test It Manually

1. Go to **Actions** tab → click **"🛡️ Daily SOC Job Hunter"**
2. Click **"Run workflow"** → **"Run workflow"** (green button)
3. Watch the logs in real time
4. Within ~60 seconds, check:
   - 📧 Your Gmail inbox for the job digest email
   - 📱 Your Telegram for the job summary message

---

## 🕘 When Does It Run Automatically?

Every day at **9:00 AM IST** (3:30 AM UTC) automatically.

No action needed — GitHub Actions runs it for free in the cloud.

---

## 📊 What You'll Receive

### Gmail Email (Daily Digest)
- Beautiful HTML email with job table
- Fit score (1–10) per job
- Direct Apply buttons
- Summary stats (new jobs, high-fit count, companies)

### Telegram Message (Daily Alert)
- Clean text message with top 5 picks
- Fit score with colour indicators (🟢🟡🔴)
- Direct apply links
- Sent to your personal Telegram

---

## 🔧 Customisation

### Change Search Keywords
Edit `JOB_SEARCHES` in `scripts/job_hunter.py` to add more URLs:
```python
{
    "source": "Naukri",
    "url": "https://www.naukri.com/soc-analyst-jobs-in-pune",
    "label": "Naukri — Pune"
},
```

### Change Alert Time
Edit `.github/workflows/job_hunter.yml`:
```yaml
- cron: "30 3 * * *"   # 3:30 UTC = 9:00 AM IST
- cron: "0 12 * * *"   # 12:00 UTC = 5:30 PM IST (evening digest)
```

### Change Score Threshold for High-Fit
In `job_hunter.py`, find `score_job()` and adjust weights.

---

## 🆓 Cost

| Service        | Cost      |
|----------------|-----------|
| GitHub Actions | **Free**  |
| Gmail SMTP     | **Free**  |
| Telegram Bot   | **Free**  |
| **Total**      | **₹0/month** |

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| Gmail not sending | Check App Password is correct, 2FA must be ON |
| Telegram not working | Re-verify Chat ID using getUpdates URL |
| No jobs found | Indeed may have changed HTML — try manual run and check logs |
| Workflow not triggering | Check Actions tab is enabled in repo settings |

---

*Built for Nikhil Sadaphule | SOC Engineer Job Search Automation*

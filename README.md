# classroom-notifier
```
 ██████╗██╗      █████╗ ███████╗███████╗██████╗  ██████╗  ██████╗ ███╗   ███╗
██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║
██║     ██║     ███████║███████╗███████╗██████╔╝██║   ██║██║   ██║██╔████╔██║
██║     ██║     ██╔══██║╚════██║╚════██║██╔══██╗██║   ██║██║   ██║██║╚██╔╝██║
╚██████╗███████╗██║  ██║███████║███████║██║  ██║╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
 ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝
     N O T I F I E R
```

> i got tired of opening google classroom every 10 minutes like a maniac. so i automated it.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Discord](https://img.shields.io/badge/Discord-Webhook-5865F2?style=flat-square&logo=discord)
![Railway](https://img.shields.io/badge/Hosted-Railway-black?style=flat-square&logo=railway)
![Google Classroom](https://img.shields.io/badge/Google-Classroom%20API-green?style=flat-square&logo=google)
![Gemini](https://img.shields.io/badge/Gemini-AI-orange?style=flat-square&logo=google)
![Status](https://img.shields.io/badge/status-running%2024%2F7-brightgreen?style=flat-square)

---

## what is this

a python bot that watches all your google classroom courses 24/7 and fires a discord notification the moment a professor posts anything. assignments, quizzes, lab tasks — all sorted into their own channels automatically. gemini AI summarizes every assignment in one line. tracks your grades. reminds you when deadlines are close. and roasts your professor when they forget to write a description.

runs on railway for free. never touches your laptop. just works.

---

## how it actually works
```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Google Classroom API                              │
│          │                                          │
│          ▼                                          │
│   ┌─────────────┐                                   │
│   │ poll every  │  ◄── runs forever on Railway      │
│   │  15 minutes │                                   │
│   └──────┬──────┘                                   │
│          │                                          │
│          ├──────────────────────────────────┐       │
│          │                                  │       │
│          ▼                                  ▼       │
│   new assignment?                    grade posted?  │
│          │                                  │       │
│         yes                                yes      │
│          │                                  │       │
│          ▼                                  ▼       │
│   ┌─────────────┐                   instant ping   │
│   │   Gemini AI │  ◄── summarizes   with score     │
│   └──────┬──────┘                                  │
│          │                                          │
│          ▼                                          │
│   ┌─────────────────────────┐                       │
│   │     Discord Webhook     │                       │
│   │  📝 assignments channel │                       │
│   │  🔬 lab-tasks channel   │                       │
│   │  ❓ quizzes channel     │                       │
│   │  📌 general channel     │                       │
│   └─────────────────────────┘                       │
│                                                     │
│   urgency system runs in parallel:                  │
│   24h left → ping once                              │
│   12h left → ping again                             │
│   3h left  → ping every 30 minutes                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## features
```
✓  detects new assignments across ALL active courses
✓  gemini AI writes a 1-line summary so you know what it is
✓  routes to the right discord channel automatically
✓  filters out past-deadline stuff — no noise
✓  roasts your professor when they forget to write a description

✓  grade notifications — instant ping when professor grades your work
✓  shows grade out of max points with color indicator
✓  🟢 above 80%  🟡 above 60%  🔴 below 60%

✓  urgency alerts — 24h before deadline → first warning
✓  urgency alerts — 12h before deadline → second warning  
✓  urgency alerts — 3h before deadline → every 30 minutes until it passes

✓  9AM daily digest — full list of everything due with urgency tags
✓  🚨 DUE TODAY  ⚠️ DUE SOON  📌 upcoming
✓  digest also shows recently graded assignments
✓  sends WOHOOO when nothing is due (rare but appreciated)

✓  hosted free on railway — runs 24/7 without your laptop
```

---

## the discord setup
```
📚 CLASSROOM NOTIFIER SERVER
│
├── 📋 assignments     ← regular coursework
├── 🔬 lab-tasks       ← anything with "lab" in the title
├── ❓ quizzes         ← MCQs and short answer questions
└── 📌 general-updates ← daily digest + grades + urgency alerts
```

new assignment notification:
```
┌──────────────────────────────────────────────┐
│ 📝 Assignment: Data Structures Report        │
│──────────────────────────────────────────────│
│ 📚 Course          │ ⏰ Deadline             │
│ CS-301             │ Apr 15 at 11:59 PM      │
│──────────────────────────────────────────────│
│ 💡 Summary                                   │
│ Analyze sorting algorithms and submit a      │
│ comparative performance report.              │
└──────────────────────────────────────────────┘
```

grade notification:
```
┌──────────────────────────────────────────────┐
│ 🎓 Grade Posted — Machine Learning BSAI     │
│──────────────────────────────────────────────│
│ 📋 Assignment: Lab Task 03                   │
│ 🟢 Grade: 18 / 20                           │
│ 📊 Status: Returned by Professor            │
└──────────────────────────────────────────────┘
```

urgency alert:
```
┌──────────────────────────────────────────────┐
│ ⚠️ 11 HOURS LEFT — Lab Task 08              │
│──────────────────────────────────────────────│
│ 📚 Course          │ ⏰ Deadline             │
│ ML BSAI Spring26   │ Apr 15 at 11:59 PM      │
│──────────────────────────────────────────────│
│ 💬 you still have time but don't push it 👀 │
└──────────────────────────────────────────────┘
```

and when the professor leaves the description empty:
```
💡 "Teacher was too lazy to write a description. Classic. 😂"
```

---

## tech stack
```
language      →  Python
classroom     →  Google Classroom API
auth          →  Google OAuth 2.0
summarization →  Google Gemini AI (gemini-pro)
notifications →  Discord Webhooks
hosting       →  Railway (free tier)
persistence   →  JSON files (seen IDs, alerts, grades)
scheduler     →  schedule library (every 15 min)
```

---

## project structure
```
classroom-notifier/
│
├── main.py              ← everything lives here
├── requirements.txt     ← clean, no pinned versions
├── Procfile             ← tells railway to run main.py
├── seen_ids.json        ← tracks notified assignments
├── alerts.json          ← tracks urgency alert state
├── grades.json          ← tracks known grades
├── .env                 ← your secrets (never committed)
├── credentials.json     ← google oauth app (never committed)
└── token.json           ← google auth token (never committed)
```

---

## setup

**clone it**
```bash
git clone https://github.com/muhammadabdullah018/classroom-notifier.git
cd classroom-notifier
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**environment variables** — create `.env`:
```
DISCORD_WEBHOOK_ASSIGNMENTS=
DISCORD_WEBHOOK_LABS=
DISCORD_WEBHOOK_QUIZZES=
DISCORD_WEBHOOK_GENERAL=
GEMINI_API_KEY=
```

**google oauth**
- go to console.cloud.google.com
- create a project → enable Google Classroom API
- create OAuth credentials → download as `credentials.json`
- run `python main.py` → browser opens → authenticate with student email
- `token.json` gets created automatically

**deploy to railway**
- push to a private github repo
- connect on railway.app → deploy from github
- add all env variables + paste contents of `credentials.json` and `token.json`
- set worker command: `python main.py`
- done. it runs forever.

---

## notes

- polls every 15 minutes — not instant but close enough
- google oauth tokens expire eventually — if it breaks, re-auth locally and update `GOOGLE_TOKEN` in railway variables
- railway free tier gives $5/month credit — this script uses under $1
- json files reset on railway restart — you'll get one duplicate burst of old notifications, then it's fine
- urgency alerts stop automatically once the deadline passes

---

*built by muhammad abdullah — ai student, air university islamabad*
*one day. zero dollars. runs forever — hosted on railway*
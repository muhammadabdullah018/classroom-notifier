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
![Status](https://img.shields.io/badge/status-running%2024%2F7-brightgreen?style=flat-square)

---

## what is this

a python bot that watches all your google classroom courses 24/7 and fires a discord notification the moment a professor posts anything. assignments, quizzes, lab tasks — all sorted into their own channels automatically. also uses gemini AI to summarize what the assignment actually is so you don't have to read the whole thing at 2am.

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
│          ▼                                          │
│   new assignment? ──── no ──── wait 15 min          │
│          │                                          │
│         yes                                         │
│          │                                          │
│          ▼                                          │
│   ┌─────────────┐                                   │
│   │   Gemini AI │  ◄── summarizes in 1 line         │
│   └──────┬──────┘                                   │
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
✓  sends a 9AM daily digest of everything due
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
└── 📌 general-updates ← daily digest + anything else
```

each notification looks like this:
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
persistence   →  JSON file for seen assignment IDs
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
├── seen_ids.json        ← tracks what's been notified
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

- polls every 15 minutes — not instant but good enough
- google oauth tokens expire eventually — if it breaks, re-auth locally and update `GOOGLE_TOKEN` in railway variables
- railway free tier gives $5/month credit — this script uses under $1
- `seen_ids.json` resets on railway restart — you'll get one duplicate burst, then it's fine

---

*built by muhammad abdullah — student, air university*
*one weekend. zero dollars. runs forever -hosted on Railway*
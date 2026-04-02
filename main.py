import os
import json
import time
import random
import schedule
import requests
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

# ── Config ──────────────────────────────────────────────────────
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly'
]

WEBHOOKS = {
    "ASSIGNMENT": os.getenv("DISCORD_WEBHOOK_ASSIGNMENTS"),
    "SHORT_ANSWER_QUESTION": os.getenv("DISCORD_WEBHOOK_QUIZZES"),
    "MULTIPLE_CHOICE_QUESTION": os.getenv("DISCORD_WEBHOOK_QUIZZES"),
    "LAB": os.getenv("DISCORD_WEBHOOK_LABS"),
    "DEFAULT": os.getenv("DISCORD_WEBHOOK_GENERAL")
}

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SEEN_IDS_FILE = "seen_ids.json"

# ── Auth ─────────────────────────────────────────────────────────
def get_classroom_service():
    token_data = os.getenv("GOOGLE_TOKEN")

    creds = Credentials.from_authorized_user_info(
        json.loads(token_data), SCOPES
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("classroom", "v1", credentials=creds)


# ── Seen IDs ──────────────────────────────────────────────────────
def load_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r") as f:
        return set(json.load(f))

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)

# ── Gemini Summary ────────────────────────────────────────────────
def summarize(title, description):
    if not description or description.strip() == "":
        funny_excuses = [
            "Teacher was too lazy to write a description. Classic. 😂",
            "Description? Never heard of her. — Your Professor 🤷",
            "The teacher typed... nothing. Respect the mystery. 🕵️",
            "No description. The professor is an enigma wrapped in silence. 🧩",
            "Teacher left the description blank. Probably on a tea break. ☕",
            "Your prof said: figure it out yourself. Motivational. 💪",
            "Description missing. The teacher has ascended beyond words. 🚀",
        ]
        return random.choice(funny_excuses)
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Summarize this assignment in one sentence, max 15 words. Title: {title}. Description: {description}"
                }]
            }]
        }
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Could not summarize — go check Classroom manually. 👀"

# ── Format Deadline ───────────────────────────────────────────────
def format_deadline(due_date, due_time):
    if not due_date:
        return "No deadline set"
    try:
        year = due_date.get("year", 2025)
        month = due_date.get("month", 1)
        day = due_date.get("day", 1)
        hour = due_time.get("hours", 23) if due_time else 23
        minute = due_time.get("minutes", 59) if due_time else 59
        dt = datetime(year, month, day, hour, minute)
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except:
        return "Unknown deadline"

# ── Detect if Lab Task ────────────────────────────────────────────
def detect_type(title, description):
    text = (title + " " + (description or "")).lower()
    if any(word in text for word in ["lab", "laboratory", "practical"]):
        return "LAB"
    return None

# ── Discord Post ──────────────────────────────────────────────────
def send_discord(webhook_url, title, course_name, work_type_label, deadline_str, summary, assignment_id):
    color_map = {
        "📝 Assignment": 5763719,
        "🔬 Lab Task": 15105570,
        "❓ Quiz": 15548997,
        "📌 Task": 3447003
    }
    color = color_map.get(work_type_label, 3447003)

    embed = {
        "title": f"{work_type_label}: {title}",
        "color": color,
        "fields": [
            {"name": "📚 Course", "value": course_name, "inline": True},
            {"name": "⏰ Deadline", "value": deadline_str, "inline": True},
            {"name": "💡 Summary", "value": summary, "inline": False},
        ],
        "footer": {"text": f"Assignment ID: {assignment_id}"},
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"  Discord response: {response.status_code}")
    except Exception as e:
        print(f"Discord error: {e}")

# ── Daily Status ──────────────────────────────────────────────────
def send_daily_status():
    now = datetime.now()
    if now.hour != 9 or now.minute > 14:
        return

    try:
        service = get_classroom_service()
        courses = service.courses().list(courseStates=["ACTIVE"]).execute()
        course_list = courses.get("courses", [])

        upcoming = []

        for course in course_list:
            course_id = course["id"]
            course_name = course["name"]

            try:
                coursework = service.courses().courseWork().list(
                    courseId=course_id,
                    orderBy="updateTime desc",
                    pageSize=20
                ).execute()
            except:
                continue

            items = coursework.get("courseWork", [])

            for item in items:
                due_date = item.get("dueDate")
                due_time = item.get("dueTime")
                if not due_date:
                    continue
                try:
                    year = due_date.get("year", 2025)
                    month = due_date.get("month", 1)
                    day = due_date.get("day", 1)
                    hour = due_time.get("hours", 23) if due_time else 23
                    minute = due_time.get("minutes", 59) if due_time else 59
                    deadline_dt = datetime(year, month, day, hour, minute)
                    if deadline_dt > datetime.utcnow():
                        upcoming.append({
                            "title": item.get("title", "Untitled"),
                            "course": course_name,
                            "deadline": deadline_dt.strftime("%b %d at %I:%M %p")
                        })
                except:
                    continue

        webhook_url = WEBHOOKS["DEFAULT"]

        if not upcoming:
            embed = {
                "title": "🎉 Daily Check-In",
                "description": "**WOHOOO! Nothing is due!** 🥳\nYou're completely clear. Go ride your motorcycle or something. 🏍️",
                "color": 5763719,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            upcoming.sort(key=lambda x: x["deadline"])
            lines = "\n".join([
                f"📌 **{item['title']}** — {item['course']}\n   ⏰ Due: {item['deadline']}"
                for item in upcoming
            ])
            embed = {
                "title": "☀️ Good Morning! Here's what's due",
                "description": lines,
                "color": 15105570,
                "footer": {"text": "Stay on top of it. You got this."},
                "timestamp": datetime.utcnow().isoformat()
            }

        requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
        print(f"  Daily status sent — {len(upcoming)} upcoming assignments")

    except Exception as e:
        print(f"Daily status error: {e}")

# ── Core Check ────────────────────────────────────────────────────
def check_classroom():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking Classroom...")
    seen_ids = load_seen_ids()

    try:
        service = get_classroom_service()
        courses = service.courses().list(courseStates=["ACTIVE"]).execute()
        course_list = courses.get("courses", [])

        if not course_list:
            print("  No active courses found.")
            return

        for course in course_list:
            course_id = course["id"]
            course_name = course["name"]
            print(f"  Checking course: {course_name}")

            try:
                coursework = service.courses().courseWork().list(
                    courseId=course_id,
                    orderBy="updateTime desc",
                    pageSize=10
                ).execute()
            except Exception as e:
                print(f"  Could not fetch coursework for {course_name}: {e}")
                continue

            items = coursework.get("courseWork", [])

            for item in items:
                item_id = item["id"]
                if item_id in seen_ids:
                    continue

                seen_ids.add(item_id)

                title = item.get("title", "Untitled")
                description = item.get("description", "")
                due_date = item.get("dueDate")
                due_time = item.get("dueTime")
                work_type = item.get("workType", "ASSIGNMENT")

                # Skip assignments with past deadlines
                if due_date:
                    try:
                        year = due_date.get("year", 2025)
                        month = due_date.get("month", 1)
                        day = due_date.get("day", 1)
                        hour = due_time.get("hours", 23) if due_time else 23
                        minute = due_time.get("minutes", 59) if due_time else 59
                        deadline_dt = datetime(year, month, day, hour, minute)
                        if deadline_dt < datetime.utcnow():
                            continue
                    except:
                        pass

                detected = detect_type(title, description)
                if detected:
                    work_type = detected

                deadline_str = format_deadline(due_date, due_time)
                summary = summarize(title, description)

                type_map = {
                    "ASSIGNMENT": ("📝 Assignment", WEBHOOKS["ASSIGNMENT"]),
                    "SHORT_ANSWER_QUESTION": ("❓ Quiz", WEBHOOKS["SHORT_ANSWER_QUESTION"]),
                    "MULTIPLE_CHOICE_QUESTION": ("❓ Quiz", WEBHOOKS["MULTIPLE_CHOICE_QUESTION"]),
                    "LAB": ("🔬 Lab Task", WEBHOOKS["LAB"]),
                }

                work_type_label, webhook_url = type_map.get(
                    work_type,
                    ("📌 Task", WEBHOOKS["DEFAULT"])
                )

                send_discord(webhook_url, title, course_name, work_type_label, deadline_str, summary, item_id)
                print(f"  Posted: {title} → {work_type_label} ({course_name})")

        save_seen_ids(seen_ids)

    except Exception as e:
        print(f"Error during check: {e}")

# ── Entry Point ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("Classroom Notifier started.")
    check_classroom()
    send_daily_status()

    schedule.every(15).minutes.do(check_classroom)
    schedule.every(15).minutes.do(send_daily_status)

    while True:
        schedule.run_pending()
        time.sleep(60)
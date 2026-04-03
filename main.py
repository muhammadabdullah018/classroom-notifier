import os
import json
import time
import random
import schedule
import requests
from datetime import datetime, timedelta
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
ALERTS_FILE = "alerts.json"
GRADES_FILE = "grades.json"

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
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE, "r") as f:
            return set(json.load(f))
    seen_env = os.getenv("SEEN_IDS", "[]")
    return set(json.loads(seen_env))

def save_seen_ids(seen_ids):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(seen_ids), f)

# ── Alerts Tracking ───────────────────────────────────────────────
def load_alerts():
    if not os.path.exists(ALERTS_FILE):
        return {}
    with open(ALERTS_FILE, "r") as f:
        return json.load(f)

def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f)

# ── Grades Tracking ───────────────────────────────────────────────
def load_grades():
    if not os.path.exists(GRADES_FILE):
        return {}
    with open(GRADES_FILE, "r") as f:
        return json.load(f)

def save_grades(grades):
    with open(GRADES_FILE, "w") as f:
        json.dump(grades, f)

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

# ── Get Deadline DateTime ─────────────────────────────────────────
def get_deadline_dt(due_date, due_time):
    if not due_date:
        return None
    try:
        year = due_date.get("year", 2025)
        month = due_date.get("month", 1)
        day = due_date.get("day", 1)
        hour = due_time.get("hours", 23) if due_time else 23
        minute = due_time.get("minutes", 59) if due_time else 59
        return datetime(year, month, day, hour, minute)
    except:
        return None

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

    try:
        response = requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
        print(f"  Discord response: {response.status_code}")
    except Exception as e:
        print(f"Discord error: {e}")

# ── Send Urgency Alert ────────────────────────────────────────────
def send_urgency_alert(title, course_name, deadline_str, hours_left, assignment_id):
    webhook_url = WEBHOOKS["DEFAULT"]

    if hours_left <= 3:
        color = 15548997  # red
        urgency = f"🚨 ONLY {int(hours_left * 60)} MINUTES LEFT"
        message = "bro get off your motorcycle and do this RIGHT NOW 🏍️💀"
    else:
        color = 15105570  # orange
        urgency = f"⚠️ {int(hours_left)} HOURS LEFT"
        message = "you still have time but don't push it 👀"

    embed = {
        "title": f"{urgency} — {title}",
        "color": color,
        "fields": [
            {"name": "📚 Course", "value": course_name, "inline": True},
            {"name": "⏰ Deadline", "value": deadline_str, "inline": True},
            {"name": "💬 Note", "value": message, "inline": False},
        ],
        "footer": {"text": f"Assignment ID: {assignment_id}"},
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
        print(f"  Urgency alert sent: {title} ({int(hours_left)}h left)")
    except Exception as e:
        print(f"Urgency alert error: {e}")

# ── Check Urgency Alerts ──────────────────────────────────────────
def check_urgency_alerts():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking urgency alerts...")
    alerts = load_alerts()
    now = datetime.utcnow()

    try:
        service = get_classroom_service()
        courses = service.courses().list(courseStates=["ACTIVE"]).execute()
        course_list = courses.get("courses", [])

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

            for item in coursework.get("courseWork", []):
                item_id = item["id"]
                title = item.get("title", "Untitled")
                due_date = item.get("dueDate")
                due_time = item.get("dueTime")

                deadline_dt = get_deadline_dt(due_date, due_time)
                if not deadline_dt:
                    continue

                # Skip if already passed
                if deadline_dt < now:
                    continue

                hours_left = (deadline_dt - now).total_seconds() / 3600
                deadline_str = format_deadline(due_date, due_time)

                if item_id not in alerts:
                    alerts[item_id] = {
                        "24h_sent": False,
                        "12h_sent": False,
                        "last_3h_ping": None
                    }

                alert = alerts[item_id]

                # 24h alert — send once
                if hours_left <= 24 and not alert["24h_sent"]:
                    send_urgency_alert(title, course_name, deadline_str, hours_left, item_id)
                    alerts[item_id]["24h_sent"] = True

                # 12h alert — send once
                elif hours_left <= 12 and not alert["12h_sent"]:
                    send_urgency_alert(title, course_name, deadline_str, hours_left, item_id)
                    alerts[item_id]["12h_sent"] = True

                # 3h alert — every 30 minutes
                elif hours_left <= 3:
                    last_ping = alert.get("last_3h_ping")
                    should_ping = False

                    if last_ping is None:
                        should_ping = True
                    else:
                        last_ping_dt = datetime.fromisoformat(last_ping)
                        if (now - last_ping_dt).total_seconds() >= 1800:  # 30 minutes
                            should_ping = True

                    if should_ping:
                        send_urgency_alert(title, course_name, deadline_str, hours_left, item_id)
                        alerts[item_id]["last_3h_ping"] = now.isoformat()

        save_alerts(alerts)

    except Exception as e:
        print(f"Urgency check error: {e}")

# ── Check Grades ──────────────────────────────────────────────────
def check_grades():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking grades...")
    known_grades = load_grades()

    try:
        service = get_classroom_service()
        courses = service.courses().list(courseStates=["ACTIVE"]).execute()
        course_list = courses.get("courses", [])

        for course in course_list:
            course_id = course["id"]
            course_name = course["name"]

            try:
                submissions = service.courses().courseWork().studentSubmissions().list(
                    courseId=course_id,
                    courseWorkId="-",
                    states=["RETURNED"]
                ).execute()
            except Exception as e:
                print(f"  Could not fetch submissions for {course_name}: {e}")
                continue

            for sub in submissions.get("studentSubmissions", []):
                sub_id = sub.get("id")
                assignment_grade = sub.get("assignedGrade")
                draft_grade = sub.get("draftGrade")
                coursework_id = sub.get("courseWorkId")
                state = sub.get("state")

                if state != "RETURNED":
                    continue

                grade = assignment_grade or draft_grade
                if grade is None:
                    continue

                grade_key = f"{sub_id}"
                if grade_key in known_grades and known_grades[grade_key] == grade:
                    continue

                # New grade posted
                known_grades[grade_key] = grade

                # Get assignment title
                try:
                    coursework = service.courses().courseWork().get(
                        courseId=course_id,
                        id=coursework_id
                    ).execute()
                    assignment_title = coursework.get("title", "Unknown Assignment")
                    max_points = coursework.get("maxPoints", "?")
                except:
                    assignment_title = "Unknown Assignment"
                    max_points = "?"

                # Grade emoji
                if max_points != "?" and grade is not None:
                    percentage = (grade / max_points) * 100
                    if percentage >= 80:
                        grade_emoji = "🟢"
                    elif percentage >= 60:
                        grade_emoji = "🟡"
                    else:
                        grade_emoji = "🔴"
                else:
                    grade_emoji = "⭐"

                embed = {
                    "title": f"🎓 Grade Posted — {course_name}",
                    "color": 5763719,
                    "fields": [
                        {"name": "📋 Assignment", "value": assignment_title, "inline": False},
                        {"name": f"{grade_emoji} Grade", "value": f"{grade} / {max_points}", "inline": True},
                        {"name": "📊 Status", "value": "Returned by Professor", "inline": True},
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }

                try:
                    requests.post(WEBHOOKS["DEFAULT"], json={"embeds": [embed]}, timeout=10)
                    print(f"  Grade posted: {assignment_title} — {grade}/{max_points}")
                except Exception as e:
                    print(f"Grade Discord error: {e}")

        save_grades(known_grades)

    except Exception as e:
        print(f"Grade check error: {e}")

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
        graded_today = []

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
                due_time_val = item.get("dueTime")
                if not due_date:
                    continue

                deadline_dt = get_deadline_dt(due_date, due_time_val)
                if not deadline_dt:
                    continue

                if deadline_dt > datetime.utcnow():
                    hours_left = (deadline_dt - datetime.utcnow()).total_seconds() / 3600

                    if hours_left <= 24:
                        urgency_tag = "🚨 DUE TODAY"
                    elif hours_left <= 72:
                        urgency_tag = "⚠️ DUE SOON"
                    else:
                        urgency_tag = "📌"

                    upcoming.append({
                        "title": item.get("title", "Untitled"),
                        "course": course_name,
                        "deadline": deadline_dt.strftime("%b %d at %I:%M %p"),
                        "deadline_dt": deadline_dt,
                        "tag": urgency_tag
                    })

            # Check submissions for graded work
            try:
                submissions = service.courses().courseWork().studentSubmissions().list(
                    courseId=course_id,
                    courseWorkId="-",
                    states=["RETURNED"]
                ).execute()

                for sub in submissions.get("studentSubmissions", []):
                    grade = sub.get("assignedGrade") or sub.get("draftGrade")
                    if grade is not None:
                        try:
                            cw = service.courses().courseWork().get(
                                courseId=course_id,
                                id=sub.get("courseWorkId")
                            ).execute()
                            graded_today.append({
                                "title": cw.get("title", "Unknown"),
                                "grade": grade,
                                "max": cw.get("maxPoints", "?"),
                                "course": course_name
                            })
                        except:
                            pass
            except:
                pass

        webhook_url = WEBHOOKS["DEFAULT"]
        upcoming.sort(key=lambda x: x["deadline_dt"])

        if not upcoming:
            embed = {
                "title": "🎉 Good Morning! Daily Check-In",
                "description": "**WOHOOO! Nothing is due!** 🥳\nYou're completely clear. Go ride your motorcycle or something. 🏍️",
                "color": 5763719,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            lines = "\n".join([
                f"{item['tag']} **{item['title']}** — {item['course']}\n   ⏰ Due: {item['deadline']}"
                for item in upcoming
            ])

            grade_lines = ""
            if graded_today:
                grade_lines = "\n\n**📊 Recently Graded:**\n" + "\n".join([
                    f"⭐ **{g['title']}** — {g['grade']}/{g['max']} ({g['course']})"
                    for g in graded_today[:5]
                ])

            embed = {
                "title": "☀️ Good Morning! Here's your daily briefing",
                "description": lines + grade_lines,
                "color": 15105570,
                "footer": {"text": f"{len(upcoming)} assignments pending. Stay on top of it."},
                "timestamp": datetime.utcnow().isoformat()
            }

        requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)
        print(f"  Daily status sent — {len(upcoming)} upcoming")

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

                # Skip past deadlines
                if due_date:
                    deadline_dt = get_deadline_dt(due_date, due_time)
                    if deadline_dt and deadline_dt < datetime.utcnow():
                        continue

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
    check_grades()
    check_urgency_alerts()
    send_daily_status()

    schedule.every(15).minutes.do(check_classroom)
    schedule.every(15).minutes.do(check_grades)
    schedule.every(15).minutes.do(check_urgency_alerts)
    schedule.every(15).minutes.do(send_daily_status)

    while True:
        schedule.run_pending()
        time.sleep(60)
from __future__ import annotations

from typing import Any

from app.core.alumni import list_alumni_posts
from app.core.ats.database.analyses import get_user_history
from app.core.roles import ADMIN, ALUMNI, STUDENT, TEACHER


def chatbot_bootstrap(role: str) -> dict:
    return {
        "intro": _intro(role),
        "quick_prompts": _quick_prompts(role),
    }


def chatbot_reply(*, user: dict, message: str) -> dict:
    prompt = message.strip()
    role = user.get("role", "")
    context = _context_for_user(user)

    if not prompt:
        return _payload(
            "Ask me about attendance, timetable, ATS resume scoring, jobs, internships, notes, alumni connect, events, or profile help.",
            role,
            context,
        )

    lowered = prompt.lower()
    if role == STUDENT and _has_any(lowered, ["job", "jobs", "internship", "internships", "role", "career", "placement"]):
        return _payload(_student_career_reply(context), role, context, topic="career")
    if _has_any(lowered, ["attendance", "face", "present", "absent"]):
        return _payload(_role_reply(role, "attendance"), role, context, topic="attendance")
    if _has_any(lowered, ["timetable", "schedule", "class"]):
        return _payload(_role_reply(role, "timetable"), role, context, topic="timetable")
    if _has_any(lowered, ["resume", "ats", "job description", "jd", "score"]):
        return _payload(_ats_reply(role, context), role, context, topic="ats")
    if _has_any(lowered, ["notes", "quiz", "test", "question"]):
        return _payload(_role_reply(role, "notes"), role, context, topic="notes")
    if _has_any(lowered, ["alumni", "mentor", "guidance", "chat"]):
        return _payload(_role_reply(role, "alumni"), role, context, topic="alumni")
    if _has_any(lowered, ["event", "seminar", "meetup"]):
        return _payload(_role_reply(role, "events"), role, context, topic="events")
    if _has_any(lowered, ["profile", "photo", "password", "account"]):
        return _payload(_role_reply(role, "profile"), role, context, topic="profile")

    return _payload(
        "I can guide you around Smart Campus based on your role. Try asking about ATS score, internship suggestions, attendance, timetable, alumni chat, notes-to-test, events, or profile settings.",
        role,
        context,
    )


def _context_for_user(user: dict) -> dict:
    context: dict[str, Any] = {"ats": None, "opportunities": []}
    if user.get("role") != STUDENT:
        return context
    try:
        history = get_user_history(user["id"])
    except Exception:
        history = []
    latest = history[0] if history else None
    context["ats"] = _summarize_ats(latest) if latest else None
    posts = []
    for post_type in ("internship", "job"):
        posts.extend(list_alumni_posts(post_type)[:4])
    context["opportunities"] = posts[:6]
    return context


def _summarize_ats(row: dict | None) -> dict | None:
    if not row:
        return None
    result = row.get("analysis_result") or {}
    parsed = result.get("parsed_resume") or {}
    skills = _as_list(parsed.get("skills") or result.get("skills") or result.get("resume_skills"))
    keywords = _as_list(parsed.get("keywords") or result.get("resume_keywords") or result.get("keywords"))
    missing = _as_list(result.get("missing_keywords") or row.get("missing_keywords"))
    component_scores = result.get("component_scores") or {}
    score = result.get("ats_score") or result.get("ATS_score") or row.get("ats_score") or 0
    return {
        "score": int(float(score or 0)),
        "filename": row.get("filename") or "resume",
        "skills": [str(item) for item in skills[:12]],
        "keywords": [str(item) for item in keywords[:12]],
        "missing": [str(item) for item in missing[:10]],
        "component_scores": component_scores,
        "interpretation": result.get("interpretation") or "",
    }


def _student_career_reply(context: dict) -> str:
    ats = context.get("ats")
    posts = context.get("opportunities") or []
    if not ats:
        base = (
            "Upload your resume in ATS Resume Scorer first. After that I can use your ATS score, skills, and missing keywords to suggest job and internship roles."
        )
        if posts:
            base += "\n\nCurrent alumni-posted opportunities:\n" + _format_posts(posts[:4])
        return base

    roles = _suggest_roles(ats)
    lines = [
        f"Based on your latest ATS score ({ats['score']}%) from {ats['filename']}, these roles fit best:",
        *[f"- {role}" for role in roles],
    ]
    if ats["score"] < 60:
        lines.append("\nBefore applying, improve your resume formatting, project evidence, and missing keywords.")
    elif ats["score"] < 75:
        lines.append("\nYou can apply to internships now, but tailor keywords for every job description.")
    else:
        lines.append("\nYour score is strong enough to target selective internships and entry-level roles.")
    if ats.get("missing"):
        lines.append("\nAdd or strengthen these keywords if they are truthful:")
        lines.extend(f"- {item}" for item in ats["missing"][:6])
    if posts:
        lines.append("\nMatching alumni opportunities:")
        lines.append(_format_posts(_rank_posts(posts, roles, ats)[:4]))
    return "\n".join(lines)


def _ats_reply(role: str, context: dict) -> str:
    if role != STUDENT:
        return _role_reply(role, "ats")
    ats = context.get("ats")
    if not ats:
        return "Open ATS Resume Scorer, upload your resume, then ask me again for score-based role and internship suggestions."
    lines = [
        f"Your latest ATS score is {ats['score']}% for {ats['filename']}.",
        ats.get("interpretation") or "Use this score to decide where to apply and what to improve.",
    ]
    if ats.get("skills"):
        lines.append("Detected skills: " + ", ".join(ats["skills"][:8]))
    if ats.get("missing"):
        lines.append("Missing keywords to review: " + ", ".join(ats["missing"][:8]))
    lines.append("Ask: suggest internships based on my ATS score.")
    return "\n".join(line for line in lines if line)


def _suggest_roles(ats: dict) -> list[str]:
    text = " ".join(ats.get("skills", []) + ats.get("keywords", [])).lower()
    roles = []
    if _has_any(text, ["python", "django", "fastapi", "flask", "sql"]):
        roles.extend(["Python Backend Intern", "FastAPI/Django Developer Intern"])
    if _has_any(text, ["react", "javascript", "typescript", "html", "css"]):
        roles.extend(["Frontend Developer Intern", "Full Stack Web Intern"])
    if _has_any(text, ["machine learning", "ml", "data", "pandas", "numpy", "tensorflow", "pytorch"]):
        roles.extend(["Data Science Intern", "Machine Learning Intern"])
    if _has_any(text, ["aws", "docker", "linux", "devops", "ci/cd"]):
        roles.extend(["Cloud/DevOps Intern", "Platform Engineering Intern"])
    if _has_any(text, ["cyber", "security", "network", "soc"]):
        roles.extend(["Cybersecurity Intern", "SOC Analyst Intern"])
    if not roles:
        roles = ["Software Developer Intern", "Web Developer Intern", "Technical Support Intern"]
    if ats.get("score", 0) >= 75:
        roles.append("Associate Software Engineer")
    return list(dict.fromkeys(roles))[:5]


def _rank_posts(posts: list[dict], roles: list[str], ats: dict) -> list[dict]:
    terms = set(" ".join(roles + ats.get("skills", []) + ats.get("keywords", [])).lower().replace("/", " ").split())

    def score(post: dict) -> int:
        text = " ".join(str(post.get(key) or "") for key in ("title", "description", "company", "post_type")).lower()
        return sum(1 for term in terms if len(term) > 2 and term in text)

    return sorted(posts, key=score, reverse=True)


def _format_posts(posts: list[dict]) -> str:
    if not posts:
        return "- No matching alumni opportunities are available right now."
    lines = []
    for post in posts:
        post_type = str(post.get("post_type") or "opportunity").title()
        company = f" at {post.get('company')}" if post.get("company") else ""
        lines.append(f"- {post_type}: {post.get('title', 'Opportunity')}{company}")
    return "\n".join(lines)


def _role_reply(role: str, topic: str) -> str:
    replies = {
        STUDENT: {
            "attendance": "Open Attendance from the sidebar to view attendance details. Use Face Login when you need attendance login.",
            "timetable": "Open Timetable to see your latest branch, semester, and section schedule.",
            "ats": "Open ATS Resume Scorer to upload your resume. I can then suggest jobs and internships from your ATS score.",
            "notes": "Open AI Notes-to-Test to generate quizzes from study material.",
            "alumni": "Open Alumni Connect for mentorship chat, or Alumni Opportunities for jobs and internships.",
            "events": "Open Events to browse seminars, meetups, and campus activities.",
            "profile": "Use the top-bar profile photo control for your picture and profile pages for account details.",
        },
        TEACHER: {
            "attendance": "Open Attendance to create sessions, upload class photos, review AI matches, and save final attendance.",
            "timetable": "Use Teacher Setup to map subjects to branch/section, then view the latest timetable.",
            "ats": "ATS is mainly for students. Guide them to upload resumes and compare job descriptions.",
            "notes": "Open AI Notes-to-Test to generate quizzes from teaching notes.",
            "alumni": "Alumni Connect is restricted to student and alumni users.",
            "events": "Open Events to view campus activities and seminars.",
            "profile": "Use the top bar profile photo control to update your account picture.",
        },
        ADMIN: {
            "attendance": "Use Attendance analytics and admin pages to review sessions, AI review status, and student records.",
            "timetable": "Generate AI Timetable after teacher subjects and branch mappings are saved.",
            "ats": "Open ATS analytics/history to review resume analysis activity.",
            "notes": "Use Notes-to-Test module health and activity pages.",
            "alumni": "Use Admin Mentorship to approve alumni mentors and monitor mentorship activity.",
            "events": "Open Events to manage seminars, meetups, and campus activities.",
            "profile": "Use Admin User Management for account changes and the top bar for your own photo.",
        },
        ALUMNI: {
            "attendance": "Attendance is restricted to student, teacher, and admin workflows.",
            "timetable": "Timetable is restricted to campus academic roles.",
            "ats": "You can guide students to improve their ATS score and choose better job descriptions.",
            "notes": "Notes-to-Test is focused on student and teacher study workflows.",
            "alumni": "Open Student Connect or Chat/Guidance to handle mentorship requests and live chats. Use Opportunities to post jobs or internships.",
            "events": "Open Events to browse campus activities and alumni meetups.",
            "profile": "Use the top-bar profile photo control to update your picture.",
        },
    }
    return replies.get(role, replies[STUDENT]).get(topic, "I can help with that from your dashboard.")


def _payload(reply: str, role: str, context: dict, topic: str = "") -> dict:
    return {
        "reply": reply,
        "actions": _actions_for(role, topic),
        "quick_prompts": _quick_prompts(role),
        "voice_reply": _voice_summary(reply),
        "context": {"has_ats": bool(context.get("ats"))},
    }


def _actions_for(role: str, topic: str = "") -> list[dict]:
    if role == STUDENT:
        actions = [
            {"label": "ATS Resume", "href": "/ats"},
            {"label": "Jobs", "href": "/alumni/opportunities?post_type=job"},
            {"label": "Internships", "href": "/alumni/opportunities?post_type=internship"},
            {"label": "Alumni Connect", "href": "/alumni/connect"},
        ]
        if topic == "attendance":
            actions.insert(0, {"label": "Attendance", "href": "/attendance"})
        return actions[:5]
    if role == TEACHER:
        return [
            {"label": "Attendance", "href": "/attendance"},
            {"label": "Teacher Setup", "href": "/teacher/setup"},
            {"label": "Timetable", "href": "/timetable/latest"},
        ]
    if role == ADMIN:
        return [
            {"label": "Users", "href": "/admin/users"},
            {"label": "Mentorship", "href": "/admin/mentorship"},
            {"label": "Analytics", "href": "/admin/analytics"},
        ]
    if role == ALUMNI:
        return [
            {"label": "Student Connect", "href": "/alumni/connect"},
            {"label": "Opportunities", "href": "/alumni/opportunities"},
            {"label": "Events", "href": "/events"},
        ]
    return [{"label": "Dashboard", "href": f"/{role}/dashboard"}]


def _quick_prompts(role: str) -> list[str]:
    if role == STUDENT:
        return [
            "Suggest internships based on my ATS score",
            "What job roles fit my resume?",
            "How can I improve my ATS score?",
            "Show alumni job opportunities",
        ]
    if role == TEACHER:
        return ["How do I take attendance?", "Open timetable help", "How do I generate quizzes?"]
    if role == ALUMNI:
        return ["How do I chat with students?", "How do I post an internship?", "How do I review mentorship requests?"]
    return ["Show admin analytics help", "How do I manage users?", "How do I manage alumni approvals?"]


def _intro(role: str) -> str:
    if role == STUDENT:
        return "Ask me about attendance, timetable, ATS score, internships, jobs, alumni mentors, notes, or profile help."
    if role == TEACHER:
        return "Ask me about attendance sessions, class photo review, teacher setup, timetable, notes-to-test, events, or profile help."
    if role == ALUMNI:
        return "Ask me about student mentorship, chat guidance, requests, opportunities, events, or profile help."
    if role == ADMIN:
        return "Ask me about users, analytics, alumni approvals, timetable generation, events, modules, or platform management."
    return "Ask me about your Smart Campus dashboard."


def _voice_summary(text: str) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:420]


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)

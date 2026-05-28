import os
import json 
import logging
import re
from typing import Dict

from groq import Groq

logger=logging.getLogger('ats_resume_scorer')


GROQ_MODEL='llama-3.3-70b-versatile'
MAX_GROQ_INPUT_CHARS = 12000

_client=None

def _get_client()->Groq:
    global _client
    if _client is None:
        api_key=os.getenv('GROQ_API_KEY')

        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        _client=Groq(api_key=api_key, timeout=45.0)
    return _client

RESUME_SYSTEM_PROMPT = (
    "You are a resume parser. Extract information from the resume "
    "and return ONLY a valid JSON object. No explanation, no markdown."
)

RESUME_USER_PROMPT = """Extract the following from this resume and return as JSON:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "linkedin": "LinkedIn URL if present, otherwise null",
  "github": "GitHub URL if present, otherwise null",
  "professional_summary": "the full text of the Summary, Profile, About Me, Objective, or Professional Summary section at the top of the resume. Copy the ENTIRE paragraph exactly as written. If no such section exists, return an empty string.",
  "skills": ["list", "of", "skills"],
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "duration_months": 0,
      "description": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "year": ""
    }}
  ],
  "certifications": ["list of certifications"],
  "projects": [
    {{
      "title": "project name",
      "description": "what the project does and how it was built",
      "technologies": ["tech", "used"]
    }}
  ],
  "action_verbs": ["strong action verbs used in bullet points, e.g. developed, implemented, designed"],
  "keywords": ["important keywords and phrases from the resume for ATS matching"]
}}

Important instructions:
- For duration_months, calculate the number of months between start_date and end_date. If end_date is "Present" or "Current", calculate from start_date to now.
- For skills, extract ALL technical and soft skills mentioned anywhere in the resume.
- For action_verbs, find verbs that start bullet points or describe achievements.
- For keywords, extract noun phrases and technical terms relevant to ATS matching.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Resume Text:
{raw_text}"""

def _call_groq(client:Groq, system_prompt:str, user_prompt:str)->str:

    response=client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature=0.0,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()

def _try_parse_json(text: str) -> dict | None:

    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):

        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None
    
def parse_resume(raw_text: str)->Dict:

    client=_get_client()
    prompt=RESUME_USER_PROMPT.format(raw_text=raw_text[:MAX_GROQ_INPUT_CHARS])
    logger.info("Calling Groq to parse resume...")
    raw_response=_call_groq(client, RESUME_SYSTEM_PROMPT, prompt)
    result=_try_parse_json(raw_response)

    if result is not None:
        return _validate_resume_result(result)
    

    logger.warning("Groq resume parse: first attempt returned invalid JSON, retrying...")
    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )
    raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, strict_prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_resume_result(result)

    logger.warning("Groq resume parse returned non-JSON after retry; using local fallback parser.")
    return _fallback_parse_resume(raw_text)
    
JD_SYSTEM_PROMPT = (
    "You are a job description parser. Extract information and "
    "return ONLY a valid JSON object. No explanation, no markdown."
)

JD_USER_PROMPT = """Extract the following from this job description and return as JSON:
{{
  "job_title": "",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "experience_required": "",
  "education_required": "",
  "key_responsibilities": ["list of responsibilities"],
  "keywords": ["important keywords and phrases for ATS matching"]
}}

Important instructions:
- required_skills: skills explicitly stated as required or must-have.
- preferred_skills: skills stated as preferred, nice-to-have, or bonus.
- keywords: extract ALL important terms an ATS system would match against,
  including skills, technologies, certifications, and domain terms.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Job Description Text:
{raw_text}"""

def parse_job_description(raw_text: str) -> Dict:
    client = _get_client()
    prompt = JD_USER_PROMPT.format(raw_text=raw_text[:MAX_GROQ_INPUT_CHARS])

    logger.info("Calling Groq to parse job description...")
    raw_response = _call_groq(client, JD_SYSTEM_PROMPT, prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_jd_result(result)

    logger.warning("Groq JD parse: first attempt returned invalid JSON, retrying...")
    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )
    raw_response = _call_groq(client, JD_SYSTEM_PROMPT, strict_prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_jd_result(result)

    logger.warning("Groq JD parse returned non-JSON after retry; using local fallback parser.")
    return _fallback_parse_jd(raw_text)


def _fallback_parse_resume(raw_text: str) -> dict:
    text = raw_text or ""
    lines = [line.strip(" \t-*•") for line in text.splitlines() if line.strip()]
    collapsed = " ".join(lines)
    skills = _extract_section_items(text, ("skills", "technical skills", "core skills"))
    certifications = _extract_section_items(text, ("certifications", "certification"))
    projects = _extract_projects(lines)
    action_verbs = _extract_action_verbs(collapsed)
    keywords = _unique(skills + certifications + action_verbs + _extract_keyword_phrases(collapsed))
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)

    return _validate_resume_result(
        {
            "name": lines[0] if lines else "",
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "linkedin": _first_url(text, "linkedin.com"),
            "github": _first_url(text, "github.com"),
            "professional_summary": _extract_summary(lines),
            "skills": skills,
            "experience": _extract_experience(lines),
            "education": _extract_section_items(text, ("education",)),
            "certifications": certifications,
            "projects": projects,
            "action_verbs": action_verbs,
            "keywords": keywords,
        }
    )


def _fallback_parse_jd(raw_text: str) -> dict:
    text = raw_text or ""
    keywords = _extract_keyword_phrases(" ".join(text.splitlines()))
    return _validate_jd_result(
        {
            "job_title": "",
            "required_skills": _extract_section_items(text, ("required skills", "requirements", "skills")),
            "preferred_skills": _extract_section_items(text, ("preferred skills", "nice to have")),
            "experience_required": "",
            "education_required": "",
            "key_responsibilities": _extract_section_items(text, ("responsibilities", "what you will do")),
            "keywords": keywords,
        }
    )


def _extract_section_items(text: str, headings: tuple[str, ...]) -> list[str]:
    lines = [line.strip(" \t-*•:") for line in text.splitlines()]
    items: list[str] = []
    collecting = False
    section_headings = {
        "summary",
        "profile",
        "objective",
        "experience",
        "work experience",
        "education",
        "certifications",
        "projects",
        "skills",
        "technical skills",
        "core skills",
        "achievements",
    }
    for line in lines:
        if not line:
            continue
        normalized = line.lower().strip(":")
        if normalized in headings:
            collecting = True
            continue
        if collecting and normalized in section_headings and normalized not in headings:
            break
        if collecting:
            parts = re.split(r"[,|;/]", line)
            items.extend(part.strip() for part in parts if _looks_like_item(part))
    return _unique(items)


def _extract_projects(lines: list[str]) -> list[dict]:
    projects: list[dict] = []
    in_projects = False
    for index, line in enumerate(lines):
        normalized = line.lower().strip(":")
        if normalized == "projects":
            in_projects = True
            continue
        if in_projects and normalized in {"skills", "experience", "education", "certifications"}:
            break
        if in_projects and line and not line.lower().startswith(("description", "technologies")):
            description = lines[index + 1] if index + 1 < len(lines) else ""
            projects.append({"title": line, "description": description, "technologies": []})
    return projects[:5]


def _extract_experience(lines: list[str]) -> list[dict]:
    for index, line in enumerate(lines):
        if line.lower().strip(":") in {"experience", "work experience"}:
            description = " ".join(lines[index + 1 : index + 6])
            return [
                {
                    "job_title": "",
                    "company": "",
                    "start_date": "",
                    "end_date": "",
                    "duration_months": 0,
                    "description": description,
                }
            ]
    return []


def _extract_summary(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if line.lower().strip(":") in {"summary", "profile", "objective", "professional summary"}:
            return " ".join(lines[index + 1 : index + 4])
    return ""


def _extract_action_verbs(text: str) -> list[str]:
    verbs = re.findall(
        r"\b(achieved|built|created|designed|developed|implemented|improved|led|managed|optimized|reduced|tested)\b",
        text,
        flags=re.IGNORECASE,
    )
    return _unique([verb.title() for verb in verbs])


def _extract_keyword_phrases(text: str) -> list[str]:
    phrases = re.findall(r"\b[A-Z][A-Za-z0-9+#.-]*(?:\s+[A-Z][A-Za-z0-9+#.-]*){0,3}\b", text)
    return _unique([phrase.strip() for phrase in phrases if len(phrase.strip()) > 2])[:30]


def _first_url(text: str, domain: str) -> str | None:
    match = re.search(r"https?://[^\s)]+", text)
    if match and domain in match.group(0).lower():
        return match.group(0)
    return None


def _looks_like_item(value: str) -> bool:
    value = value.strip()
    return bool(value) and len(value) <= 80 and not value.endswith(".")


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = " ".join(str(item).strip().split())
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result

#it will make sure, that the parse json has all the valid fields we expect
def _validate_jd_result(result: dict) -> dict:
    
    defaults = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": "",
        "education_required": "",
        "key_responsibilities": [],
        "keywords": [],
    }

    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    return result


#to make sure the parse json has all the valid json fields
def _validate_resume_result(result: dict) -> dict:

    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": [],
        "keywords": [],
    }
    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
            
        # Ensure list fields are actually lists
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    #Validate experience entries
    for exp in result.get("experience", []):
        if not isinstance(exp, dict):
            continue
        exp.setdefault("job_title", "")
        exp.setdefault("company", "")
        exp.setdefault("start_date", "")
        exp.setdefault("end_date", "")
        exp.setdefault("duration_months", 0)
        exp.setdefault("description", "")
        #Ensure duration_months is an int
        try:
            exp["duration_months"] = int(exp["duration_months"])
        except (ValueError, TypeError):
            exp["duration_months"] = 0

    #Validate project entries
    for proj in result.get("projects", []):
        if not isinstance(proj, dict):
            continue
        proj.setdefault("title", "")
        proj.setdefault("description", "")
        proj.setdefault("technologies", [])

    return result



import json
import logging
import os
import re
from pathlib import Path

import httpx
from openai import OpenAI
from app.core.config import settings
from app.core.quiz.database.quizzes import get_chapter_by_id, save_questions_for_chapter

logger = logging.getLogger(__name__)

MIN_QUIZ_QUESTIONS = 3
# Adjusted to be relative to the platform's app root or workspace
PROMPT_EXAMPLES_PATH = settings.workspace_dir / "Testmodule" / "backend" / "prompts" / "quiz_examples.jsonl"

OOP_CONCEPTS = [
    ("Class", "A blueprint or template that defines attributes and methods for objects"),
    ("Object", "A real instance of a class that is created in memory"),
    ("Encapsulation", "Wrapping data and methods into a class and restricting direct access to internal data"),
    ("Inheritance", "Allowing a child class to reuse properties and behavior from a parent class"),
    ("Polymorphism", "Allowing the same object or method to behave differently depending on context"),
    ("Abstraction", "Hiding unnecessary implementation details and showing only relevant features"),
    ("Access Specifier", "A rule that controls the visibility of class members"),
    ("Friend Class", "A C++ class granted access to private and protected members of another class"),
    ("Constructor", "A special method called automatically when an object is created"),
    ("Destructor", "A C++ member function called when an object is destroyed or goes out of scope"),
    ("Garbage Collector", "A Java memory management feature that frees unused object memory automatically"),
    ("Scope Resolution Operator", "A C++ operator used to access members outside the current scope"),
    ("This Pointer", "A pointer that refers to the current object inside a class method"),
    ("Shallow Copy", "A copy where objects share referenced memory instead of duplicating it"),
    ("Deep Copy", "A copy where referenced data is duplicated into separate memory"),
    ("Multiple Inheritance", "Inheritance where one class inherits from more than one parent class"),
    ("Diamond Problem", "An ambiguity that occurs when multiple inheritance creates duplicate base class paths"),
    ("Compile-time Polymorphism", "Polymorphism resolved during compilation through overloading"),
    ("Run-time Polymorphism", "Polymorphism resolved during execution through overriding or virtual functions"),
    ("Method Overloading", "Using the same method name with different parameter lists"),
    ("Method Overriding", "Redefining a parent class method in a child class with the same signature"),
    ("Virtual Function", "A C++ function that enables runtime method overriding through dynamic dispatch"),
    ("Abstract Class", "A class that cannot be instantiated directly and may contain abstract methods"),
    ("Interface", "A Java type that defines methods a class must implement"),
    ("Static Data Member", "A class-level data member shared by all objects of the class"),
]


class QuizGenerationError(ValueError):
    pass


def _parse_llm_json(text: str) -> list:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)

def _has_usable_api_key() -> bool:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(key and "YOUR_API_KEY" not in key and key.startswith("sk-"))

def _use_ollama() -> bool:
    return os.getenv("LLM_PROVIDER", "ollama").strip().lower() == "ollama"

def _ollama_generate(prompt: str, *, json_format: bool = False, timeout: int = 120) -> str:
    payload = {
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    if json_format:
        payload["format"] = "json"
    response = httpx.post(
        f"{os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')}/api/generate",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("response", "")

def _load_prompt_examples(content: str = "", limit: int = 5) -> str:
    if not PROMPT_EXAMPLES_PATH.exists():
        return ""
    rows = []
    try:
        for line in PROMPT_EXAMPLES_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            rows.append(item)
    except Exception as exc:
        logger.warning("Could not load prompt examples: %s", exc)
        return ""

    oop_keywords = ("oop", "object", "class", "inheritance", "polymorphism", "constructor")
    is_oop_content = any(keyword in content.lower() for keyword in oop_keywords)
    if is_oop_content:
        rows.sort(
            key=lambda item: any(keyword in item.get("input", "").lower() for keyword in oop_keywords),
            reverse=True,
        )

    examples = []
    for item in rows[:limit]:
        examples.append(
                "Input notes:\n"
                f"{item['input']}\n"
                "Good quiz JSON:\n"
                f"{json.dumps(item['output'], ensure_ascii=False)}"
        )
    return "\n\n".join(examples)

def _clean_study_context_with_ollama(content: str) -> str:
    prompt = f"""
Clean this OCR/study text into concise notes for quiz generation.
Rules:
- Remove page numbers, contact details, watermarks, broken OCR fragments, random symbols, and incomplete phrases.
- Keep only meaningful concepts, facts, definitions, rules, examples, and relationships.
- Use short bullet points.
- If the text is mostly unreadable, return the best meaningful points only.

Text:
{content[:4500]}
"""
    cleaned = _ollama_generate(prompt, json_format=False, timeout=180).strip()
    return cleaned if len(cleaned) >= 120 else content

def _clean_question_text(text: str) -> str:
    text = re.sub(r"[|_~`{}^\\]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -•*")
    return text

def _is_useful_sentence(sentence: str) -> bool:
    sentence = _clean_question_text(sentence)
    compact = sentence.replace(" ", "")
    if len(compact) < 35 or len(compact) > 220:
        return False
    alpha_ratio = sum(char.isalpha() for char in compact) / max(len(compact), 1)
    symbol_count = len(re.findall(r"[^A-Za-z0-9\s.,:;?!()/%'-]", sentence))
    words = re.findall(r"[A-Za-z][A-Za-z]{2,}", sentence)
    return alpha_ratio >= 0.6 and symbol_count <= 2 and len(words) >= 6

def _extract_key_terms(content: str) -> list[str]:
    stop_words = {
        "about", "after", "again", "also", "because", "before", "between", "could",
        "each", "from", "have", "into", "more", "most", "only", "other", "should",
        "some", "such", "than", "that", "their", "there", "these", "this", "those",
        "through", "using", "were", "when", "where", "which", "while", "with", "would",
        "first", "second", "third", "include", "includes", "included", "result",
        "results", "section", "chapter", "example", "examples", "natural",
    }
    candidates = re.findall(r"\b[A-Za-z][A-Za-z-]{4,}\b", content)
    seen = set()
    terms = []
    for candidate in candidates:
        term = candidate.strip("-").lower()
        if term in stop_words or term in seen:
            continue
        seen.add(term)
        terms.append(candidate.strip("-"))
    return terms

def _unique_options(answer: str, distractors: list[str]) -> list[str]:
    options = []
    for option in [answer, *distractors]:
        cleaned = _clean_question_text(option)
        if cleaned and cleaned.lower() not in {existing.lower() for existing in options}:
            options.append(cleaned)
    fallback_options = ["Not mentioned", "Both A and B", "None of these", "All of these"]
    for option in fallback_options:
        if len(options) >= 4:
            break
        if option.lower() not in {existing.lower() for existing in options}:
            options.append(option)
    return options[:4]

def _answer_is_substantial(answer: str) -> bool:
    answer = _clean_question_text(answer)
    words = re.findall(r"[A-Za-z0-9]+", answer)
    weak_answers = {
        "a", "an", "the", "and", "or", "number", "numbers", "cannot", "expressed",
        "prime", "composite", "irrational", "true", "false", "first", "includes",
    }
    return (
        len(answer) >= 3
        and answer.lower() not in weak_answers
        and (len(words) >= 2 or len(answer) >= 10)
    )

def _term_is_concept(term: str) -> bool:
    term = _clean_question_text(term)
    words = re.findall(r"[A-Za-z0-9]+", term)
    lowered = term.lower()
    banned_words = {
        "smallest", "largest", "first", "last", "digit", "digits", "sum", "result",
        "results", "example", "examples", "exercise", "question", "answer",
    }
    if not (1 <= len(words) <= 4):
        return False
    if any(word.lower() in banned_words for word in words):
        return False
    if re.search(r"\d", term):
        return False
    if term.count("(") != term.count(")") or term.endswith(("(", "-", "/")):
        return False
    return _answer_is_substantial(term)

def _definition_is_conceptual(definition: str) -> bool:
    definition = _clean_question_text(definition)
    lowered = definition.lower()
    words = re.findall(r"[A-Za-z0-9]+", definition)
    banned_patterns = [
        r"=",
        r"\bsum of\b",
        r"\bfirst \d+\b",
        r"\bsmallest\b",
        r"\blargest\b",
        r"\bdigit irrational\b",
        r"\bis \d+\b",
        r"\b=\s*\d+\b",
    ]
    if len(words) < 5 or len(words) > 28:
        return False
    if any(re.search(pattern, lowered) for pattern in banned_patterns):
        return False
    return _answer_is_substantial(definition)

def _question_is_high_quality(question_text: str) -> bool:
    question_text = _clean_question_text(question_text)
    if not question_text.endswith("?"):
        return False
    if "____" in question_text or "__" in question_text:
        return False
    if re.search(r"\b(blank|fill in|complete the)\b", question_text, re.IGNORECASE):
        return False
    words = re.findall(r"[A-Za-z0-9]+", question_text)
    return 5 <= len(words) <= 34

def _option_set_is_high_quality(options: list[str], answer: str) -> bool:
    cleaned_options = [_clean_question_text(option) for option in options]
    banned_fragments = (
        "not the idea described",
        "not the main concept",
        "source sentence",
        "is discussed as a key concept",
    )
    return (
        len(cleaned_options) == 4
        and len({option.lower() for option in cleaned_options}) == 4
        and answer.lower() in {option.lower() for option in cleaned_options}
        and all(_answer_is_substantial(option) for option in cleaned_options)
        and all(_definition_is_conceptual(option) for option in cleaned_options)
        and not any(fragment in option.lower() for option in cleaned_options for fragment in banned_fragments)
    )

def _make_explanation(question_text: str, answer: str) -> str:
    if answer:
        return f"The correct answer is {answer}."
    return f"Review the source section for: {question_text}"

def _extract_definition_pairs(content: str) -> list[dict]:
    pairs = []
    seen = set()
    cleaned_content = _clean_question_text(content)
    pattern = re.compile(
        r"([A-Z][A-Za-z0-9 /()&+-]{2,45})\s*[:\-]\s*"
        r"(.{18,180}?)(?=(?:\s+[A-Z][A-Za-z0-9 /()&+-]{2,45}\s*[:\-])|[.!?](?:\s|$)|$)"
    )
    for match in pattern.finditer(cleaned_content):
        term = _clean_question_text(match.group(1))
        definition = _clean_question_text(match.group(2)).rstrip(".")
        key = term.lower()
        if key in seen or not _term_is_concept(term) or not _definition_is_conceptual(definition):
            continue
        if term.lower() in {"numbers", "results on numbers"}:
            continue
        seen.add(key)
        pairs.append({"term": term, "definition": definition})
    return pairs

def _extract_oop_concept_pairs(content: str) -> list[dict]:
    lowered = content.lower()
    pairs = []
    for term, definition in OOP_CONCEPTS:
        term_pattern = re.escape(term.lower()).replace("\\ ", r"[\s-]+")
        if re.search(rf"\b{term_pattern}s?\b", lowered):
            pairs.append({"term": term, "definition": definition})
    return pairs

def _merge_definition_pairs(*groups: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for group in groups:
        for pair in group:
            key = pair["term"].lower()
            if key in seen:
                continue
            if _term_is_concept(pair["term"]) and _definition_is_conceptual(pair["definition"]):
                merged.append(pair)
                seen.add(key)
    return merged

def _build_definition_question(pair: dict, all_pairs: list[dict]) -> dict:
    correct_option = pair["definition"]
    distractors = [
        other["definition"]
        for other in all_pairs
        if other["term"].lower() != pair["term"].lower()
    ]
    options = _unique_options(correct_option, distractors[:3])
    return {
        "type": "mcq",
        "question": f"Which statement best describes {pair['term']}?",
        "options": options,
        "answer": correct_option,
        "explanation": f"{pair['term']} means: {correct_option}.",
    }

def _build_supported_statement_question(sentence: str, all_sentences: list[str]) -> dict:
    correct_option = sentence[:180].rstrip(".")
    distractors = [
        other[:180].rstrip(".")
        for other in all_sentences
        if other.lower() != sentence.lower()
    ]
    distractors.extend([
        "The section mainly discusses unrelated administrative details",
        "The section says the topic should be ignored during study",
        "The section gives no meaningful information about this topic",
    ])
    options = _unique_options(correct_option, distractors[:3])
    return {
        "type": "mcq",
        "question": "Which statement is directly supported by this section?",
        "options": options,
        "answer": correct_option,
        "explanation": f"The uploaded section supports this statement: {correct_option}.",
    }

def _normalize_question_types(question_types: list[str] | None) -> list[str]:
    allowed = {"mcq", "short_answer", "true_false"}
    normalized = [
        str(item).strip().lower().replace("-", "_").replace(" ", "_")
        for item in (question_types or ["mcq"])
    ]
    normalized = [item for item in normalized if item in allowed]
    return normalized or ["mcq"]

def _question_key(question_text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", question_text.lower())

def _normalize_mcq_questions(questions: list[dict], content: str, difficulty: str = "medium") -> list[dict]:
    normalized = []
    fallback = _build_local_quiz(content)
    seen_questions = set()
    for question in questions:
        answer = _clean_question_text(str(question.get("answer", "")))
        options = question.get("options") or []
        options = [_clean_question_text(str(option)) for option in options if _clean_question_text(str(option))]
        if answer and answer.lower() not in {option.lower() for option in options}:
            options.insert(0, answer)
        options = _unique_options(answer or (options[0] if options else ""), options)
        question_text = _clean_question_text(str(question.get("question", "")))
        key = _question_key(question_text)
        if (
            not question_text
            or not answer
            or key in seen_questions
            or not _question_is_high_quality(question_text)
            or not _option_set_is_high_quality(options, answer)
        ):
            continue
        seen_questions.add(key)
        normalized.append({
            "type": "mcq",
            "question": question_text[:240],
            "options": options,
            "answer": next((option for option in options if option.lower() == answer.lower()), options[0]),
            "difficulty": difficulty,
            "explanation": _clean_question_text(str(question.get("explanation", ""))) or _make_explanation(question_text, answer),
        })
        if len(normalized) == 5:
            break

    for question in fallback:
        if len(normalized) >= 5:
            break
        key = _question_key(question["question"])
        if key in seen_questions:
            continue
        question = {**question, "difficulty": difficulty, "explanation": _make_explanation(question["question"], question["answer"])}
        seen_questions.add(key)
        normalized.append(question)

    return normalized[:5]

def _normalize_generated_questions(
    questions: list[dict],
    content: str,
    difficulty: str = "medium",
    question_types: list[str] | None = None,
) -> list[dict]:
    requested_types = _normalize_question_types(question_types)
    if requested_types == ["mcq"]:
        return _normalize_mcq_questions(questions, content, difficulty)

    normalized = []
    seen_questions = set()
    for question in questions:
        question_type = str(question.get("type", "mcq")).strip().lower().replace("-", "_").replace(" ", "_")
        if question_type in {"subjective", "written", "short"}:
            question_type = "short_answer"
        if question_type not in requested_types:
            continue

        question_text = _clean_question_text(str(question.get("question", "")))
        answer = _clean_question_text(str(question.get("answer", "")))
        key = _question_key(question_text)
        if not question_text or not answer or key in seen_questions:
            continue

        if question_type == "mcq":
            options = question.get("options") or []
            options = [_clean_question_text(str(option)) for option in options if _clean_question_text(str(option))]
            if answer.lower() not in {option.lower() for option in options}:
                options.insert(0, answer)
            options = _unique_options(answer, options)
            if not _question_is_high_quality(question_text) or not _option_set_is_high_quality(options, answer):
                continue
            normalized_question = {
                "type": "mcq",
                "question": question_text[:240],
                "options": options,
                "answer": next((option for option in options if option.lower() == answer.lower()), options[0]),
            }
        elif question_type == "true_false":
            if not _question_is_high_quality(question_text):
                continue
            answer = "True" if answer.lower() in {"true", "yes", "correct"} else "False"
            normalized_question = {
                "type": "true_false",
                "question": question_text[:240],
                "options": ["True", "False"],
                "answer": answer,
            }
        else:
            if not _question_is_high_quality(question_text) or not _answer_is_substantial(answer):
                continue
            normalized_question = {
                "type": "short_answer",
                "question": question_text[:240],
                "options": [],
                "answer": answer[:240],
            }

        normalized_question["difficulty"] = difficulty
        normalized_question["explanation"] = (
            _clean_question_text(str(question.get("explanation", "")))
            or _make_explanation(question_text, normalized_question["answer"])
        )
        seen_questions.add(key)
        normalized.append(normalized_question)
        if len(normalized) == 5:
            break

    if len(normalized) < 5:
        fallback = _normalize_mcq_questions([], content, difficulty)
        for question in fallback:
            if len(normalized) >= 5:
                break
            key = _question_key(question["question"])
            if key not in seen_questions:
                normalized.append(question)
                seen_questions.add(key)

    return normalized[:5]

def _build_local_quiz(content: str) -> list[dict]:
    sentences = [
        _clean_question_text(s)
        for s in re.split(r"(?<=[.!?])\s+", content)
        if _is_useful_sentence(s)
    ]
    terms = _extract_key_terms(" ".join(sentences) or content)
    oop_pairs = _extract_oop_concept_pairs(content)
    extracted_pairs = _extract_definition_pairs(content)
    definition_pairs = _merge_definition_pairs(
        oop_pairs,
        extracted_pairs if len(oop_pairs) < 5 else [],
    )

    questions = []
    seen_questions = set()
    for pair in definition_pairs:
        if len(questions) >= 5:
            break
        question = _build_definition_question(pair, definition_pairs)
        if _question_is_high_quality(question["question"]) and _option_set_is_high_quality(question["options"], question["answer"]):
            seen_questions.add(_question_key(question["question"]))
            questions.append(question)

    if len(definition_pairs) < 4:
        candidate_sentences = sentences[:8]
    else:
        candidate_sentences = []

    for sentence in candidate_sentences:
        if len(questions) >= 5:
            break
        terms_in_sentence = [
            term for term in terms
            if re.search(rf"\b{re.escape(term)}\b", sentence, re.IGNORECASE)
        ]
        answer = next((term for term in terms_in_sentence if _answer_is_substantial(term)), "")
        if not answer:
            continue
        local_pairs = [
            {"term": answer, "definition": sentence[:180].rstrip(".")},
            *definition_pairs,
        ]
        question = _build_definition_question(local_pairs[0], local_pairs)
        key = _question_key(question["question"])
        if key not in seen_questions and _term_is_concept(answer) and _question_is_high_quality(question["question"]) and _option_set_is_high_quality(question["options"], question["answer"]):
            seen_questions.add(key)
            questions.append(question)

    for sentence in candidate_sentences:
        if len(questions) >= 5:
            break
        question = _build_supported_statement_question(sentence, candidate_sentences)
        key = _question_key(f"{question['question']} {question['answer']}")
        if key not in seen_questions and _question_is_high_quality(question["question"]) and _option_set_is_high_quality(question["options"], question["answer"]):
            seen_questions.add(key)
            questions.append(question)

    for pair in definition_pairs[:5]:
        if len(questions) >= 5:
            break
        question = _build_definition_question(pair, definition_pairs)
        key = _question_key(question["question"])
        if key not in seen_questions and _question_is_high_quality(question["question"]) and _option_set_is_high_quality(question["options"], question["answer"]):
            seen_questions.add(key)
            questions.append(question)

    return questions[:5]

def _ensure_enough_questions(questions: list[dict]) -> list[dict]:
    if len(questions) < MIN_QUIZ_QUESTIONS:
        raise QuizGenerationError(
            "Not enough readable study content to generate a useful quiz. "
            "Upload a clearer photo/PDF or fix the extracted text in Review extracted text, "
            "then try again."
        )
    return questions[:5]

def _merge_questions(primary: list[dict], fallback: list[dict]) -> list[dict]:
    merged = []
    seen = set()
    for question in [*primary, *fallback]:
        key = _question_key(question.get("question", ""))
        if not key or key in seen:
            continue
        merged.append(question)
        seen.add(key)
        if len(merged) >= 5:
            break
    return merged

def _normalize_with_raw_fallback(
    parsed_questions: list[dict],
    model_context: str,
    raw_context: str,
    difficulty: str,
    requested_types: list[str],
) -> list[dict]:
    model_questions = _normalize_generated_questions(parsed_questions, model_context, difficulty, requested_types)
    raw_questions = _normalize_generated_questions([], raw_context, difficulty, requested_types)
    return _merge_questions(model_questions, raw_questions)


def generate_quiz_for_chapter(chapter_id: str, difficulty: str = "medium", question_types: list[str] | None = None):
    chapter = get_chapter_by_id(chapter_id)
    if not chapter:
        return {"error": "Chapter not found"}

    content_snippet = chapter.get("content", "")[:3500]
    quiz_context = content_snippet

    if _use_ollama():
        try:
            quiz_context = _clean_study_context_with_ollama(content_snippet)
        except Exception as e:
            logger.warning("Ollama cleanup failed; using raw context: %s", e)

    requested_types = _normalize_question_types(question_types)
    prompt_examples = _load_prompt_examples(content_snippet)
    prompt = f"""
You're an expert tutor. Generate a JSON list of 5 useful practice questions based on this chapter.
Ignore OCR noise, broken words, page numbers, random symbols, and unreadable fragments.
Allowed question types: {", ".join(requested_types)}.
Difficulty: {difficulty}.
For MCQ questions, include exactly 4 unique options and make the answer exactly match one option.
For true_false questions, use options ["True", "False"] and answer "True" or "False".
For short_answer questions, use an empty options list.
Do not ask questions from contact details, watermarks, publisher notes, or incomplete OCR fragments.
Make each question exam-style and understandable without seeing the original paragraph.
Never create fill-in-the-blank, cloze, or missing-word questions.
Never use "____", "blank", "fill in", or "complete the sentence".
Never use one-word answers like "number", "numbers", "prime", "cannot", or "expressed".
Each MCQ option must be a meaningful phrase or sentence, not a single isolated word.
Prefer concept, definition, application, comparison, and reasoning questions.
Every explanation must briefly explain why the answer is correct.
Return ONLY valid JSON in this format:

[
  {{
    "type": "mcq",
    "question": "Which property makes a number a perfect number?",
    "options": [
      "Its proper divisors add up exactly to the number itself",
      "It can only be divided by 1 and itself",
      "It cannot be written as a fraction of two integers",
      "It has at least one factor other than 1 and itself"
    ],
    "answer": "Its proper divisors add up exactly to the number itself",
    "explanation": "A perfect number equals the sum of its proper divisors, excluding itself."
  }}
]

Follow these examples for question style:
{prompt_examples}

Chapter content:
{quiz_context[:3500]}
"""

    if _use_ollama():
        try:
            generated = _ollama_generate(prompt, json_format=True, timeout=180)
            parsed = _parse_llm_json(generated)
            if isinstance(parsed, dict):
                parsed = parsed.get("questions", [])
            questions = _normalize_with_raw_fallback(parsed, quiz_context, content_snippet, difficulty, requested_types)
            questions = _ensure_enough_questions(questions)
            save_questions_for_chapter(chapter_id, questions)
            return {"chapter_id": chapter_id, "questions": questions}
        except Exception as e:
            logger.warning("Ollama quiz generation failed; using local fallback: %s", e)
            questions = _normalize_generated_questions([], content_snippet, difficulty, requested_types)
            questions = _ensure_enough_questions(questions)
            save_questions_for_chapter(chapter_id, questions)
            return {"chapter_id": chapter_id, "questions": questions}

    if not _has_usable_api_key():
        questions = _normalize_generated_questions([], content_snippet, difficulty, requested_types)
        questions = _ensure_enough_questions(questions)
        save_questions_for_chapter(chapter_id, questions)
        return {"chapter_id": chapter_id, "questions": questions}

    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        questions_text = response.choices[0].message.content
        parsed = _parse_llm_json(questions_text)
        if isinstance(parsed, dict):
            parsed = parsed.get("questions", [])
        questions = _normalize_generated_questions(parsed, content_snippet, difficulty, requested_types)
        questions = _ensure_enough_questions(questions)
        save_questions_for_chapter(chapter_id, questions)
        return {"chapter_id": chapter_id, "questions": questions}
    except Exception as e:
        logger.warning("LLM quiz generation failed; using local fallback: %s", e)
        questions = _normalize_generated_questions([], content_snippet, difficulty, requested_types)
        questions = _ensure_enough_questions(questions)
        save_questions_for_chapter(chapter_id, questions)
        return {"chapter_id": chapter_id, "questions": questions}

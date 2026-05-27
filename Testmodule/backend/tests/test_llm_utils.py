"""Unit tests for app.llm_utils – specifically the JSON parsing helper."""
import json
import pytest

from app.llm_utils import (
    QuizGenerationError,
    _build_local_quiz,
    _ensure_enough_questions,
    _load_prompt_examples,
    _normalize_generated_questions,
    _normalize_with_raw_fallback,
    _parse_llm_json,
)


SAMPLE_QUESTIONS = [
    {
        "type": "mcq",
        "question": "What is 2+2?",
        "options": ["3", "4", "5", "6"],
        "answer": "4",
    },
    {
        "type": "subjective",
        "question": "Explain gravity.",
        "answer": "Gravity is a force of attraction.",
    },
]


def test_parse_plain_json():
    text = json.dumps(SAMPLE_QUESTIONS)
    result = _parse_llm_json(text)
    assert result == SAMPLE_QUESTIONS


def test_parse_json_with_markdown_fence():
    text = f"```json\n{json.dumps(SAMPLE_QUESTIONS)}\n```"
    result = _parse_llm_json(text)
    assert result == SAMPLE_QUESTIONS


def test_parse_json_with_plain_fence():
    text = f"```\n{json.dumps(SAMPLE_QUESTIONS)}\n```"
    result = _parse_llm_json(text)
    assert result == SAMPLE_QUESTIONS


def test_parse_json_with_leading_whitespace():
    text = f"   \n{json.dumps(SAMPLE_QUESTIONS)}\n"
    result = _parse_llm_json(text)
    assert result == SAMPLE_QUESTIONS


def test_parse_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        _parse_llm_json("this is not json")


def test_parse_empty_list():
    assert _parse_llm_json("[]") == []


def test_build_local_quiz_returns_real_questions():
    content = (
        "Python is a programming language used for automation and web development. "
        "FastAPI helps developers create APIs quickly with Python type hints. "
        "React builds interactive user interfaces with reusable components."
    )
    result = _build_local_quiz(content)
    assert len(result) >= 3
    assert result[0]["type"] == "mcq"
    assert "question" in result[0]
    assert "options" in result[0]
    assert "answer" in result[0]


def test_ensure_enough_questions_rejects_low_quality_ocr_fallback():
    with pytest.raises(QuizGenerationError, match="Not enough readable study content"):
        _ensure_enough_questions([])


def test_normalize_generated_questions_drops_malformed_duplicates():
    questions = [
        {"type": "mcq", "question": "", "options": ["A", "B"], "answer": "A"},
        {
            "type": "mcq",
            "question": "Which statement best describes Python in this section?",
            "options": [
                "Python is a programming language used for automation and web development",
                "Python is a database table used only for storing records",
                "Python is a markup language used only for page styling",
                "Python is a browser plugin used for rendering images",
            ],
            "answer": "Python is a programming language used for automation and web development",
        },
        {
            "type": "mcq",
            "question": "Which statement best describes Python in this section?",
            "options": [
                "Python is a programming language used for automation and web development",
                "Python is a database table used only for storing records",
                "Python is a markup language used only for page styling",
                "Python is a browser plugin used for rendering images",
            ],
            "answer": "Python is a programming language used for automation and web development",
        },
    ]
    result = _normalize_generated_questions(
        questions,
        "Python is a programming language used for automation. FastAPI creates APIs.",
    )
    assert len(result) >= 2
    assert result[0]["question"] == "Which statement best describes Python in this section?"
    assert len(result[0]["options"]) == 4
    assert result[0]["answer"] in result[0]["options"]
    assert "explanation" in result[0]


def test_normalize_generated_questions_supports_true_false_and_short_answer():
    questions = [
        {"type": "true_false", "question": "Is Python used for automation according to this section?", "options": ["True", "False"], "answer": "True"},
        {"type": "short_answer", "question": "Which Python web framework is mentioned in this section?", "answer": "FastAPI framework"},
    ]
    result = _normalize_generated_questions(
        questions,
        "Python is used for automation. FastAPI is a Python web framework.",
        question_types=["true_false", "short_answer"],
    )
    assert result[0]["type"] == "true_false"
    assert result[0]["options"] == ["True", "False"]
    assert result[1]["type"] == "short_answer"


def test_normalize_generated_questions_rejects_cloze_and_one_word_options():
    questions = [
        {
            "type": "mcq",
            "question": "Perfect ____: A number equal to the sum of its proper divisors?",
            "options": ["number", "Irrational", "Numbers", "Cannot"],
            "answer": "number",
        },
        {
            "type": "mcq",
            "question": "Which property makes a number a perfect number?",
            "options": [
                "Its proper divisors add up exactly to the number itself",
                "It has exactly two factors, 1 and itself",
                "It has at least one factor other than 1 and itself",
                "It cannot be expressed as a ratio of two integers",
            ],
            "answer": "Its proper divisors add up exactly to the number itself",
        },
    ]
    result = _normalize_generated_questions(
        questions,
        "A perfect number is equal to the sum of its proper divisors, excluding itself.",
    )
    assert result[0]["question"] == "Which property makes a number a perfect number?"
    assert "____" not in result[0]["question"]
    assert all(len(option.split()) > 1 for option in result[0]["options"])


def test_local_quiz_uses_real_definitions_as_distractors():
    content = (
        "Composite Numbers: Non-prime natural numbers that have at least one factor other than 1 and itself. "
        "Co-prime Numbers: Two natural numbers with a greatest common divisor of 1. "
        "Irrational Numbers: Cannot be expressed as a simple fraction. "
        "Real Numbers: Set includes both rational and irrational numbers. "
        "Perfect Numbers: Numbers equal to the sum of their proper divisors."
    )
    result = _build_local_quiz(content)
    combined_options = " ".join(option for question in result for option in question["options"])
    assert "not the idea described" not in combined_options
    assert "source sentence" not in combined_options
    assert any(question["question"] == "Which statement best describes Composite Numbers?" for question in result)


def test_local_quiz_rejects_fact_fragments_as_definitions():
    content = (
        "Composite Numbers: Non-prime natural numbers that have at least one factor other than 1 and itself. "
        "Smallest three: digit irrational number is 101. "
        "Prime Numbers: Sum of first 50 prime numbers = 328. "
        "Irrational Numbers: Cannot be expressed as a simple fraction, examples include square root 2 and square root 3. "
        "Real Numbers: Set includes both rational and irrational numbers, denoted by R. "
        "Perfect Numbers: Numbers equal to the sum of their proper divisors."
    )
    result = _build_local_quiz(content)
    questions = " ".join(question["question"] for question in result)
    options = " ".join(option for question in result for option in question["options"])
    assert "Smallest three" not in questions
    assert "Sum of first 50" not in options
    assert "digit irrational number is 101" not in options
    assert "Which statement best describes Prime Numbers?" not in questions


def test_oops_raw_fallback_handles_empty_model_output():
    content = (
        "Constructor is a special method called automatically when an object is created. "
        "Destructor in C++ is called when an object goes out of scope. "
        "Inheritance allows a child class to reuse behavior from a parent class. "
        "Polymorphism allows methods to behave differently depending on context."
    )
    result = _normalize_with_raw_fallback([], "", content, "medium", ["mcq"])
    assert len(result) >= 3
    assert any("Constructor" in question["question"] for question in result)
    assert any("Inheritance" in question["question"] for question in result)


def test_oops_prompt_examples_are_prioritized_for_oop_content():
    examples = _load_prompt_examples("constructor inheritance polymorphism class object", limit=2)
    assert "Object-oriented programming" in examples or "OOP" in examples

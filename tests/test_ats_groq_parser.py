from app.core.ats.services import groq_parser


def test_try_parse_json_extracts_object_from_extra_text():
    result = groq_parser._try_parse_json('Here is the JSON:\n{"skills": ["Python"]}\nDone')

    assert result == {"skills": ["Python"]}


def test_resume_fallback_handles_plain_text_groq_response():
    raw_text = """
    Arti Sharma
    Experience
    Software Engineer ABC Company Jan 2020 Present
    Developed and implemented a new feature
    Certifications
    Google Cloud Certified
    Microsoft Certified
    Projects
    Project1
    Description This is a project
    Technologies Python Java
    Skills
    Communication
    Team Management
    Time Management
    Problem Solving
    Leadership
    Action Verbs
    Developed
    Implemented
    Designed
    Tested
    Keywords
    Cloud Computing
    Machine Learning
    Data Science
    """

    result = groq_parser._fallback_parse_resume(raw_text)

    assert result["name"] == "Arti Sharma"
    assert "Communication" in result["skills"]
    assert "Google Cloud Certified" in result["certifications"]
    assert "Developed" in result["action_verbs"]
    assert result["keywords"]

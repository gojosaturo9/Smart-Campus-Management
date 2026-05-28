from app.core.face_bridge import FACE_MATCH_GAP, FACE_MATCH_THRESHOLD, find_embedding_match


def _embedding(value):
    return [float(value)] * 128


def test_find_embedding_match_returns_nearest_under_threshold():
    students = [
        {"profile_id": "far", "face_embedding": _embedding(1.0)},
        {"profile_id": "near", "face_embedding": _embedding(0.01)},
    ]

    match = find_embedding_match(_embedding(0.0), students, threshold=0.2, match_gap=0.0)

    assert match is not None
    student, best_distance, second_distance = match
    assert student["profile_id"] == "near"
    assert best_distance < 0.2
    assert second_distance is not None


def test_find_embedding_match_rejects_distance_above_threshold():
    students = [{"profile_id": "far", "face_embedding": _embedding(1.0)}]

    assert find_embedding_match(_embedding(0.0), students, threshold=0.2, match_gap=0.0) is None


def test_default_face_login_threshold_rejects_loose_dlib_match():
    per_dimension_delta = 0.06
    distance = per_dimension_delta * (128**0.5)
    assert distance > FACE_MATCH_THRESHOLD
    students = [{"profile_id": "too_far", "face_embedding": _embedding(per_dimension_delta)}]

    assert find_embedding_match(_embedding(0.0), students) is None


def test_find_embedding_match_rejects_ambiguous_second_best_gap():
    students = [
        {"profile_id": "first", "face_embedding": _embedding(0.01)},
        {"profile_id": "second", "face_embedding": _embedding(0.011)},
    ]

    assert find_embedding_match(_embedding(0.0), students, threshold=0.2, match_gap=0.05) is None


def test_default_face_login_gap_rejects_ambiguous_close_users():
    best_delta = 0.01
    second_delta = best_delta + (FACE_MATCH_GAP / (128**0.5) / 2)
    students = [
        {"profile_id": "first", "face_embedding": _embedding(best_delta)},
        {"profile_id": "second", "face_embedding": _embedding(second_delta)},
    ]

    assert find_embedding_match(_embedding(0.0), students) is None


def test_find_embedding_match_ignores_invalid_stored_embeddings():
    students = [
        {"profile_id": "bad", "face_embedding": [0.0, 1.0]},
        {"profile_id": "good", "face_embedding": _embedding(0.01)},
    ]

    match = find_embedding_match(_embedding(0.0), students, threshold=0.2, match_gap=0.0)

    assert match is not None
    assert match[0]["profile_id"] == "good"

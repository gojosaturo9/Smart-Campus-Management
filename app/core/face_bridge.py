from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import os


FACE_MATCH_THRESHOLD = 0.55
FACE_MATCH_GAP = 0.04


@dataclass(frozen=True)
class FaceResult:
    ok: bool
    embedding: list[float] | None = None
    message: str = ""


def create_face_embedding(image_bytes: bytes) -> FaceResult:
    try:
        import numpy as np
        from PIL import Image

        from app.core.face_ai import create_face_embedding as create_platform_embedding

        image_np = np.array(Image.open(BytesIO(image_bytes)).convert("RGB"))
        embedding = create_platform_embedding(image_np)
    except Exception as exc:
        return FaceResult(False, None, _friendly_face_error(exc))
    return FaceResult(True, embedding, "Face profile created.")


def match_face(image_bytes: bytes, students: list[dict]) -> tuple[dict | None, str, list[float] | None]:
    result = create_face_embedding(image_bytes)
    if not result.ok or not result.embedding:
        return None, result.message, None
    match = find_embedding_match(result.embedding, students)
    if match:
        student, best_distance, second_distance = match
        detail = f"Face matched with distance {best_distance:.4f}."
        if second_distance is not None:
            detail = f"{detail} Second-best distance {second_distance:.4f}."
        return student, detail, result.embedding
    return None, "Face was captured, but no matching student profile was found.", result.embedding


def match_class_faces(image_bytes: bytes, roster: list[dict]) -> tuple[dict[str, dict], str, int]:
    try:
        import numpy as np
        from PIL import Image

        from app.core.face_ai import create_face_embeddings

        image_np = np.array(Image.open(BytesIO(image_bytes)).convert("RGB"))
        embeddings, total_faces = create_face_embeddings(image_np)
    except Exception as exc:
        return {}, _friendly_face_error(exc), 0

    matches: dict[str, dict] = {}
    for embedding in embeddings:
        match = find_embedding_match(embedding, roster)
        if not match:
            continue
        student, distance, second_distance = match
        student_id = str(student.get("id") or student.get("profile_id") or "")
        if not student_id:
            continue
        existing = matches.get(student_id)
        if existing and existing["distance"] <= distance:
            continue
        matches[student_id] = {
            "student": student,
            "distance": distance,
            "second_distance": second_distance,
        }
    return matches, "Face analysis completed.", total_faces


def find_embedding_match(
    embedding: list[float],
    students: list[dict],
    *,
    threshold: float | None = None,
    match_gap: float | None = None,
) -> tuple[dict, float, float | None] | None:
    import numpy as np

    probe = _embedding_array(embedding)
    if probe is None:
        return None

    threshold = _get_float_env("FACE_RECOGNITION_THRESHOLD", FACE_MATCH_THRESHOLD) if threshold is None else threshold
    match_gap = _get_float_env("FACE_RECOGNITION_MATCH_GAP", FACE_MATCH_GAP) if match_gap is None else match_gap

    distances: list[tuple[float, dict]] = []
    for student in students:
        stored = _embedding_array(student.get("face_embedding"))
        if stored is None:
            continue
        distances.append((float(np.linalg.norm(stored - probe)), student))

    if not distances:
        return None

    distances.sort(key=lambda item: item[0])
    best_distance, best_student = distances[0]
    second_distance = distances[1][0] if len(distances) > 1 else None
    if not _is_confident_embedding_match(best_distance, second_distance, threshold, match_gap):
        return None
    return best_student, best_distance, second_distance


def _embedding_array(value):
    import numpy as np

    if not value:
        return None
    try:
        array = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if array.ndim != 1 or array.size != 128:
        return None
    if not np.isfinite(array).all():
        return None
    return array


def _is_confident_embedding_match(best_distance: float, second_best_distance: float | None, threshold: float, gap: float) -> bool:
    if best_distance > threshold:
        return False
    if gap <= 0:
        return True
    if second_best_distance is None:
        return True
    return (second_best_distance - best_distance) >= gap


def _get_float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _friendly_face_error(exc: Exception) -> str:
    text = str(exc)
    missing = []
    for name in ("numpy", "PIL", "pillow", "dlib", "face_recognition_models"):
        if name.lower() in text.lower():
            missing.append(name)
    if missing:
        return "Face AI dependencies are not installed in the platform environment: " + ", ".join(sorted(set(missing)))
    return text or "Face AI could not process this image."

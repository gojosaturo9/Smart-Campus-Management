from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO


FACE_MATCH_THRESHOLD = 0.82


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
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        return None, _friendly_face_error(exc), None

    probe = np.asarray(result.embedding, dtype=np.float32)
    best_student = None
    best_distance = None
    for student in students:
        stored = _embedding_array(student.get("face_embedding"))
        if stored is None:
            continue
        distance = float(np.linalg.norm(stored - probe))
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_student = student
    if best_student and best_distance is not None and best_distance <= FACE_MATCH_THRESHOLD:
        return best_student, f"Face matched with distance {best_distance:.4f}.", result.embedding
    return None, "Face was captured, but no matching student profile was found.", result.embedding


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
    return array


def _friendly_face_error(exc: Exception) -> str:
    text = str(exc)
    missing = []
    for name in ("numpy", "PIL", "pillow", "dlib", "face_recognition_models"):
        if name.lower() in text.lower():
            missing.append(name)
    if missing:
        return "Face AI dependencies are not installed in the platform environment: " + ", ".join(sorted(set(missing)))
    return text or "Face AI could not process this image."

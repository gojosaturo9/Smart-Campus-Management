from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


class FaceAISetupError(RuntimeError):
    pass


@contextmanager
def _suppress_native_output():
    devnull = open(os.devnull, "w")
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = devnull
        sys.stderr = devnull
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        devnull.close()


def create_face_embedding(image_np) -> list[float]:
    _validate_single_face_quality(image_np)
    encodings, total_faces = _encode_faces(image_np)
    if total_faces == 0:
        raise FaceAISetupError("No face was detected. Use a clear front-facing photo.")
    if total_faces > 1:
        raise FaceAISetupError("Multiple faces were detected. Capture only one student.")
    if not encodings:
        raise FaceAISetupError("Could not create a clear face profile from this image.")
    return encodings[0].astype(float).tolist()


def create_face_embeddings(image_np) -> tuple[list[list[float]], int]:
    encodings, total_faces = _encode_faces(image_np, max_size=1280)
    return [encoding.astype(float).tolist() for encoding in encodings], total_faces


def _encode_faces(image_np, max_size=960) -> tuple[list[np.ndarray], int]:
    _, sp, facerec = _load_dlib_models()
    image_np = _as_dlib_rgb_image(image_np)
    image_np = _resize_for_detection(image_np, max_size=max_size)
    image_np = _as_dlib_rgb_image(image_np)
    faces = _filter_duplicate_faces(_detect_faces(image_np, upsample_times=2))
    encodings = []
    for face in faces:
        with _suppress_native_output():
            shape = sp(image_np, face)
            descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.asarray(descriptor, dtype=np.float32))
    return encodings, len(faces)


def _validate_single_face_quality(image_np, min_face_area_ratio=0.015):
    image_np = _as_dlib_rgb_image(image_np)
    image_np = _resize_for_detection(image_np, max_size=960)
    image_np = _as_dlib_rgb_image(image_np)
    faces = _filter_duplicate_faces(_detect_faces(image_np, upsample_times=2))
    if len(faces) != 1:
        return
    image_area = max(1, image_np.shape[0] * image_np.shape[1])
    face_ratio = _face_area(faces[0]) / image_area
    if face_ratio < min_face_area_ratio:
        raise FaceAISetupError("Face is too small. Move closer and capture a clearer front-facing photo.")


@lru_cache(maxsize=1)
def _load_dlib_models():
    try:
        import dlib
        import face_recognition_models
    except ModuleNotFoundError as exc:
        raise FaceAISetupError(
            "Face AI dependencies are missing in platform environment. Run: "
            "python -m pip install -r platform/requirements.txt"
        ) from exc
    with _suppress_native_output():
        detector = dlib.get_frontal_face_detector()
        shape_predictor = dlib.shape_predictor(face_recognition_models.pose_predictor_model_location())
        face_rec = dlib.face_recognition_model_v1(face_recognition_models.face_recognition_model_location())
    return detector, shape_predictor, face_rec


def _detect_faces(image_np, upsample_times=2):
    image_np = _as_dlib_rgb_image(image_np)
    detector, _, _ = _load_dlib_models()
    with _suppress_native_output():
        faces = detector(image_np, upsample_times)
    if faces:
        return faces
    enhanced = Image.fromarray(image_np.astype(np.uint8)).convert("RGB")
    enhanced = ImageOps.autocontrast(enhanced, cutoff=1)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(1.2)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.15)
    enhanced_np = np.asarray(enhanced)
    with _suppress_native_output():
        faces = detector(enhanced_np, upsample_times)
    if faces:
        return faces
    with _suppress_native_output():
        faces = detector(enhanced_np, upsample_times + 1)
    if faces:
        return faces
    with _suppress_native_output():
        faces = detector(enhanced_np, upsample_times + 2)
    if faces:
        return faces
    with _suppress_native_output():
        return detector(enhanced_np, upsample_times + 3)


def _filter_duplicate_faces(faces, min_center_distance=18):
    filtered = []
    for face in sorted(faces, key=_face_area, reverse=True):
        center = np.array([(face.left() + face.right()) / 2, (face.top() + face.bottom()) / 2])
        if all(
            np.linalg.norm(center - np.array([(seen.left() + seen.right()) / 2, (seen.top() + seen.bottom()) / 2]))
            > min_center_distance
            for seen in filtered
        ):
            filtered.append(face)
    return filtered


def _face_area(face):
    return max(0, face.right() - face.left()) * max(0, face.bottom() - face.top())


def _resize_for_detection(image_np, max_size=960):
    height, width = image_np.shape[:2]
    if max(height, width) <= max_size:
        return image_np
    scale = max_size / max(height, width)
    new_size = (int(width * scale), int(height * scale))
    return np.asarray(Image.fromarray(image_np).resize(new_size, Image.LANCZOS))


def _as_dlib_rgb_image(image_np):
    image = np.asarray(image_np)

    if image.ndim == 4 and image.shape[0] == 1:
        image = image[0]

    if image.ndim == 3 and image.shape[0] in (1, 3, 4) and image.shape[2] not in (1, 3, 4):
        image = np.transpose(image, (1, 2, 0))

    image = np.squeeze(image)

    if image.dtype != np.uint8:
        if np.issubdtype(image.dtype, np.floating):
            finite_image = np.nan_to_num(image, nan=0.0, posinf=255.0, neginf=0.0)
            if finite_image.size and float(np.nanmax(finite_image)) <= 1.0:
                finite_image = finite_image * 255.0
            image = np.clip(finite_image, 0, 255).astype(np.uint8)
        else:
            image = np.clip(image, 0, 255).astype(np.uint8)

    if image.ndim == 2:
        pil_image = Image.fromarray(image)
    elif image.ndim == 3:
        if image.shape[2] == 1:
            pil_image = Image.fromarray(image[:, :, 0])
        elif image.shape[2] in (3, 4):
            pil_image = Image.fromarray(image)
        else:
            raise FaceAISetupError(
                f"Unsupported image channel count: {image.shape[2]}. Expected gray, RGB, or RGBA."
            )
    else:
        raise FaceAISetupError(
            f"Unsupported image dimensions: {image.ndim}. Expected gray, RGB, or RGBA image."
        )

    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    rgb_image = np.array(pil_image, dtype=np.uint8, copy=True)
    rgb_image = np.require(rgb_image, dtype=np.uint8, requirements=["C", "A", "W"])

    if rgb_image.ndim != 3 or rgb_image.shape[2] != 3:
        raise FaceAISetupError(
            f"Unsupported normalized image shape: {rgb_image.shape}. Expected RGB image."
        )

    return rgb_image


def _as_rgb_image(image_np):
    return _as_dlib_rgb_image(image_np)

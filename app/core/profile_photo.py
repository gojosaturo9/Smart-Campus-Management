from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.core.supabase_client import SupabaseError, eq, rest_update


MAX_PROFILE_PHOTO_BYTES = 3 * 1024 * 1024
PROFILE_PHOTO_SIZE = (360, 360)


def profile_photo_path(user_id: str) -> Path:
    safe_user_id = "".join(char for char in str(user_id) if char.isalnum() or char in {"-", "_"})
    return settings.data_dir / "profile_photos" / f"{safe_user_id}.jpg"


def save_profile_photo(user_id: str, image_bytes: bytes | None) -> tuple[bool, str]:
    if not image_bytes:
        return False, "Profile image is required."
    if len(image_bytes) > MAX_PROFILE_PHOTO_BYTES:
        return False, "Profile image must be 3 MB or smaller."

    try:
        image = Image.open(BytesIO(image_bytes))
        image.verify()
        image = Image.open(BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return False, "Upload a valid image file."

    image.thumbnail(PROFILE_PHOTO_SIZE)
    target = profile_photo_path(user_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="JPEG", quality=88, optimize=True)

    try:
        rest_update("profiles", {"id": eq(user_id)}, {"avatar_url": "/profile/photo"})
    except SupabaseError as exc:
        return False, str(exc)
    return True, "Profile picture updated."


save_student_profile_photo = save_profile_photo

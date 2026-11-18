from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from config import THUMB_DIR, THUMB_JPEG_QUALITY, THUMB_MAX_SIZE


def make_thumbnail(source_path: Path, thumb_name: str) -> str:
    """Write a JPEG thumbnail. Raises UnidentifiedImageError if not an image."""
    dest = THUMB_DIR / thumb_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((THUMB_MAX_SIZE, THUMB_MAX_SIZE))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        image.save(dest, format="JPEG", quality=THUMB_JPEG_QUALITY, optimize=True)

    return thumb_name

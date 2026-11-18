from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "votes.db"
UPLOAD_DIR = BASE_DIR / "uploads"
THUMB_DIR = BASE_DIR / "thumbnails"

# Longest edge of a thumbnail in pixels. Grid views never send originals.
THUMB_MAX_SIZE = 400
THUMB_JPEG_QUALITY = 80

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64 MB per request

# Local-only. Replace before any public deploy.
SECRET_KEY = "dev-not-for-production"

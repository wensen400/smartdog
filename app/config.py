import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

DATABASE_URL = os.getenv("SMARTDOG_DATABASE_URL", f"sqlite:///{BASE_DIR / 'smartdog.db'}")
SECRET_KEY = os.getenv("SMARTDOG_SECRET_KEY", "dev-secret-change-me-in-production")
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

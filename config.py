"""
Application configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHARACTER_DIR = DATA_DIR / "characters"
SCENE_DIR = DATA_DIR / "scenes"
VIDEO_DIR = DATA_DIR / "videos"

# Ensure directories exist
for directory in (DATA_DIR, CHARACTER_DIR, SCENE_DIR, VIDEO_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# SQLite database
SQLITE_PATH = DATA_DIR / "workflow.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_PATH}")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

# Video generation API
VIDEO_API_URL = os.getenv("VIDEO_API_URL", "http://35.229.117.169:8000/api/generate-video")
VIDEO_API_EMAIL = os.getenv("VIDEO_API_EMAIL", "rehmanhassan@gmail.com")
VIDEO_API_SECRET = os.getenv("VIDEO_API_SECRET", "hakuna_matata")
VIDEO_API_NAME = os.getenv("VIDEO_API_NAME", "anonymous")

# Flask settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB


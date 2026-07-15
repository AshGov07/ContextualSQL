from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/ or the root directory .env
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

UPLOAD_DIR = BASE_DIR / "uploads"
SESSION_DIR = BASE_DIR / "sessions"
CONFIG_PATH = BASE_DIR / "config.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)
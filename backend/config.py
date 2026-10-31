import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "database" / "subscription.db"))
SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-key-change-me")


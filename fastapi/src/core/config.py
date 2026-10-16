"""Environment-backed configuration."""
import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/personal_finance")
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
FASTAPI_INTERNAL_API_KEY = os.getenv("FASTAPI_INTERNAL_API_KEY", "").strip()
APP_TITLE = os.getenv("APP_TITLE", "Spending Analysis API")
APP_VERSION = os.getenv("APP_VERSION", "0.5.0")

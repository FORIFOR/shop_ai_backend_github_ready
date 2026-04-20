import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Shop AI Staff Backend API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql+asyncpg://shopai:shopai@localhost:5432/shopai",
)

LOCAL_FAST_LLM_BASE_URL = os.getenv("LOCAL_FAST_LLM_BASE_URL", "http://gpu-node:8000/v1")
LOCAL_FAST_LLM_MODEL = os.getenv("LOCAL_FAST_LLM_MODEL", "fast-local-model")
LOCAL_DEEP_LLM_BASE_URL = os.getenv("LOCAL_DEEP_LLM_BASE_URL", "http://mac-mini:11434/v1")
LOCAL_DEEP_LLM_MODEL = os.getenv("LOCAL_DEEP_LLM_MODEL", "deep-local-model")

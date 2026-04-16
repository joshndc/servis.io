import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

SUPABASE_URL = _require("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = _require("SUPABASE_SERVICE_ROLE_KEY")
META_APP_SECRET = _require("META_APP_SECRET")
META_WEBHOOK_VERIFY_TOKEN = _require("META_WEBHOOK_VERIFY_TOKEN")
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

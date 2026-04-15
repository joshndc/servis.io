import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
META_APP_SECRET = os.environ["META_APP_SECRET"]
META_WEBHOOK_VERIFY_TOKEN = os.environ["META_WEBHOOK_VERIFY_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

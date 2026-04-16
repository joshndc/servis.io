import os
os.environ["SUPABASE_URL"] = "https://fake.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "fake-key"
os.environ["META_APP_SECRET"] = "fake-secret"
os.environ["META_WEBHOOK_VERIFY_TOKEN"] = "fake-token"
os.environ["ANTHROPIC_API_KEY"] = "fake-anthropic-key"
os.environ["TELEGRAM_BOT_TOKEN"] = "fake-telegram-token"

import importlib
import config as _config_module
importlib.reload(_config_module)
import config

def test_telegram_bot_token_loaded():
    assert config.TELEGRAM_BOT_TOKEN == "fake-telegram-token"

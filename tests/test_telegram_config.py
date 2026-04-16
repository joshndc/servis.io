import os

_defaults = {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "ANTHROPIC_API_KEY": "fake-anthropic-key",
    "TELEGRAM_BOT_TOKEN": "fake-telegram-token",
}
for _k, _v in _defaults.items():
    if not os.environ.get(_k):
        os.environ[_k] = _v

import importlib
import config as _config_module
importlib.reload(_config_module)
import config

def test_telegram_bot_token_loaded():
    assert config.TELEGRAM_BOT_TOKEN == "fake-telegram-token"

import sys, os
# Stub env vars before any import
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "GEMINI_API_KEY": "fake-gemini",
    "ANTHROPIC_API_KEY": "fake-anthropic",
    "TELEGRAM_BOT_TOKEN": "fake-telegram",
}.items():
    os.environ[k] = os.environ.get(k) or v

from unittest.mock import patch, MagicMock
from services.tenant import get_tenant_by_page_id, get_catalog, get_reply_rules, get_or_create_conversation, get_settings

def _result(data):
    m = MagicMock()
    m.data = data
    return m

def test_get_tenant_by_page_id_not_found():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.limit.return_value
         .execute.return_value) = _result([])
        assert get_tenant_by_page_id("missing_page") is None

def test_get_catalog_returns_list():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.eq.return_value
         .execute.return_value) = _result([{"name": "Milk Tea", "price": 80}])
        result = get_catalog("tenant-1")
        assert len(result) == 1
        assert result[0]["name"] == "Milk Tea"

def test_get_reply_rules_returns_list():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value
         .execute.return_value) = _result([{"keyword": "price", "reply_template": "₱80"}])
        result = get_reply_rules("tenant-1")
        assert len(result) == 1

def test_get_or_create_conversation_existing():
    existing = {"page_id": "p1", "sender_id": "s1", "status": "open"}
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .upsert.return_value.execute.return_value) = _result([existing])
        result = get_or_create_conversation("p1", "s1")
        assert result["status"] == "open"

def test_get_settings_found():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.limit.return_value
         .execute.return_value) = _result([{"tenant_id": "t1", "welcome_message": "Hi!"}])
        result = get_settings("t1")
        assert result["welcome_message"] == "Hi!"

def test_get_settings_not_found():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.limit.return_value
         .execute.return_value) = _result([])
        result = get_settings("missing")
        assert result is None

def test_update_conversation():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .update.return_value.eq.return_value.eq.return_value
         .execute.return_value) = _result([{"status": "escalated"}])
        from services.tenant import update_conversation
        result = update_conversation("p1", "s1", {"status": "escalated"})
        assert result["status"] == "escalated"

def test_get_settings_by_chat_id_returns_row():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.limit.return_value
         .execute.return_value) = _result([{"tenant_id": "t1", "telegram_chat_id": "chat-999"}])
        from services.tenant import get_settings_by_chat_id
        result = get_settings_by_chat_id("chat-999")
        assert result["tenant_id"] == "t1"

def test_update_settings_calls_supabase():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .update.return_value.eq.return_value
         .execute.return_value) = _result([{"tenant_id": "t1", "is_on_break": True}])
        from services.tenant import update_settings
        result = update_settings("t1", {"is_on_break": True})
        assert result["is_on_break"] is True

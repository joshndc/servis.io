import sys, os
# Stub env vars before any import
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "GEMINI_API_KEY": "fake-gemini",
}.items():
    os.environ.setdefault(k, v)

from unittest.mock import patch, MagicMock
from services.tenant import get_tenant_by_page_id, get_catalog, get_reply_rules, get_or_create_conversation

def _result(data):
    m = MagicMock()
    m.data = data
    return m

def test_get_tenant_by_page_id_not_found():
    with patch("services.tenant.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.single.return_value
         .execute.return_value) = _result(None)
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
         .select.return_value.eq.return_value.eq.return_value
         .execute.return_value) = _result([existing])
        result = get_or_create_conversation("p1", "s1")
        assert result["status"] == "open"

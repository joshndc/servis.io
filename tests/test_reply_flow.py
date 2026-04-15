import os
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "GEMINI_API_KEY": "fake-gemini-key",
}.items():
    os.environ.setdefault(k, v)

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

PAGE = {"tenant_id": "t1", "access_token": "tok", "page_id": "page_111"}
CATALOG = [{"name": "Milk Tea", "price": 80, "description": "Classic", "discounted_price": None, "is_available": True}]
CONV_NEW = {"page_id": "page_111", "sender_id": "user_123", "status": "open", "detected_language": None}

DM_PAYLOAD = {
    "object": "page",
    "entry": [{"id": "page_111", "messaging": [{"sender": {"id": "user_123"}, "recipient": {"id": "page_111"}, "message": {"text": "What's your menu?"}}]}]
}

COMMENT_PAYLOAD = {
    "object": "page",
    "entry": [{"id": "page_111", "changes": [{"field": "feed", "value": {"item": "comment", "comment_id": "cmt_1", "message": "How much?", "from": {"id": "user_456"}}}]}]
}

def _mocks(monkeypatch=None, welcome=None, rule_reply=None, gemini_reply="Test reply"):
    return {
        "main.get_tenant_by_page_id": PAGE,
        "main.get_catalog": CATALOG,
        "main.get_reply_rules": [],
        "main.get_settings": {"welcome_message": welcome, "handoff_keyword": "human", "comment_reply_mode": "comment"},
        "main.get_or_create_conversation": CONV_NEW,
        "main.match_rule": rule_reply,
        "main.generate_reply": gemini_reply,
    }

def test_dm_triggers_gemini_reply():
    with patch("main.get_tenant_by_page_id", return_value=PAGE), \
         patch("main.get_catalog", return_value=CATALOG), \
         patch("main.get_reply_rules", return_value=[]), \
         patch("main.get_settings", return_value={"welcome_message": None, "handoff_keyword": "human", "comment_reply_mode": "comment"}), \
         patch("main.get_or_create_conversation", return_value=CONV_NEW), \
         patch("main.update_conversation"), \
         patch("main.generate_reply", return_value="Meron kaming Milk Tea!") as mock_gemini, \
         patch("main.send_dm") as mock_send:
        response = client.post("/webhook", json=DM_PAYLOAD)
        assert response.status_code == 200
        mock_gemini.assert_called_once()
        mock_send.assert_called_once_with("tok", "user_123", "Meron kaming Milk Tea!")

def test_dm_triggers_keyword_rule():
    with patch("main.get_tenant_by_page_id", return_value=PAGE), \
         patch("main.get_catalog", return_value=CATALOG), \
         patch("main.get_reply_rules", return_value=[{"keyword": "menu", "reply_template": "Here is our menu!"}]), \
         patch("main.get_settings", return_value={"welcome_message": None, "handoff_keyword": "human", "comment_reply_mode": "comment"}), \
         patch("main.get_or_create_conversation", return_value=CONV_NEW), \
         patch("main.update_conversation"), \
         patch("main.generate_reply") as mock_gemini, \
         patch("main.send_dm") as mock_send:
        response = client.post("/webhook", json=DM_PAYLOAD)
        assert response.status_code == 200
        mock_gemini.assert_not_called()
        mock_send.assert_called_once_with("tok", "user_123", "Here is our menu!")

def test_dm_handoff_escalates():
    payload = {"object": "page", "entry": [{"id": "page_111", "messaging": [{"sender": {"id": "user_123"}, "recipient": {"id": "page_111"}, "message": {"text": "human"}}]}]}
    with patch("main.get_tenant_by_page_id", return_value=PAGE), \
         patch("main.get_catalog", return_value=CATALOG), \
         patch("main.get_reply_rules", return_value=[]), \
         patch("main.get_settings", return_value={"welcome_message": None, "handoff_keyword": "human", "comment_reply_mode": "comment"}), \
         patch("main.get_or_create_conversation", return_value=CONV_NEW), \
         patch("main.update_conversation") as mock_update, \
         patch("main.send_dm") as mock_send:
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        mock_send.assert_called_once()
        mock_update.assert_called_once_with("page_111", "user_123", {"status": "escalated"})

def test_comment_reply_sent():
    with patch("main.get_tenant_by_page_id", return_value=PAGE), \
         patch("main.get_catalog", return_value=CATALOG), \
         patch("main.get_reply_rules", return_value=[]), \
         patch("main.get_settings", return_value={"welcome_message": None, "handoff_keyword": "human", "comment_reply_mode": "comment"}), \
         patch("main.generate_reply", return_value="Great question!"), \
         patch("main.send_comment_reply") as mock_comment:
        response = client.post("/webhook", json=COMMENT_PAYLOAD)
        assert response.status_code == 200
        mock_comment.assert_called_once_with("tok", "cmt_1", "Great question!")

def test_non_page_object_ignored():
    payload = {"object": "instagram", "entry": []}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}

def test_unknown_page_skipped():
    with patch("main.get_tenant_by_page_id", return_value=None), \
         patch("main.send_dm") as mock_send:
        response = client.post("/webhook", json=DM_PAYLOAD)
        assert response.status_code == 200
        mock_send.assert_not_called()

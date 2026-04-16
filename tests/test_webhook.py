import os
import hmac
import hashlib
import json

os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "test_verify_token")
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key")
# Force-set these in case the shell has them set to empty strings
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY") or "fake-anthropic-key"
os.environ["TELEGRAM_BOT_TOKEN"] = os.environ.get("TELEGRAM_BOT_TOKEN") or "fake-telegram-token"

from fastapi.testclient import TestClient
import main
from main import app
import config

client = TestClient(app)


def _signed_post(payload: dict) -> object:
    """Post a webhook payload with a valid X-Hub-Signature-256 header."""
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = "sha256=" + hmac.new(
        config.META_APP_SECRET.encode(), raw, hashlib.sha256
    ).hexdigest()
    return client.post(
        "/webhook",
        content=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
    )


def test_webhook_verify_success():
    token = config.META_WEBHOOK_VERIFY_TOKEN
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": token,
        "hub.challenge": "abc123"
    })
    assert response.status_code == 200
    assert response.text == "abc123"

def test_webhook_verify_wrong_token():
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "abc123"
    })
    assert response.status_code == 403

def test_webhook_post_returns_200():
    payload = {"object": "page", "entry": []}
    response = _signed_post(payload)
    assert response.status_code == 200

def test_webhook_post_invalid_signature_returns_403():
    payload = {"object": "page", "entry": []}
    raw = json.dumps(payload).encode()
    response = client.post(
        "/webhook",
        content=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=badsig"},
    )
    assert response.status_code == 403


def test_dm_on_break_sends_break_message(mocker):
    mocker.patch("main.get_tenant_by_page_id", return_value={
        "tenant_id": "t1", "access_token": "tok"
    })
    mocker.patch("main.get_catalog", return_value=[])
    mocker.patch("main.get_reply_rules", return_value=[])
    mocker.patch("main.get_promos", return_value=[])
    mocker.patch("main.get_settings", return_value={
        "is_on_break": True,
        "welcome_message": None,
        "handoff_keyword": "human",
    })
    mocker.patch("main.get_or_create_conversation", return_value={"last_message": "prev"})
    mock_send = mocker.patch("main.send_dm")
    mocker.patch("main.append_message")

    payload = {"object": "page", "entry": [{"id": "page1", "messaging": [{
        "sender": {"id": "user1"},
        "message": {"text": "hello"}
    }]}]}
    _signed_post(payload)
    mock_send.assert_called_once_with("tok", "user1", "We're on a break right now. We'll be back soon! 😊")


def test_dm_order_confirmed_creates_order_and_notifies(mocker):
    ai_reply_with_order = """Confirmed! See you at 3pm 😊
[ORDER_CONFIRMED]
name: Juan
contact: 09171234567
items: 2x Milk Tea (₱120)
total: 240
pickup_time: 3pm
notes:
[/ORDER_CONFIRMED]"""

    mocker.patch("main.get_tenant_by_page_id", return_value={
        "tenant_id": "t1", "access_token": "tok"
    })
    mocker.patch("main.get_catalog", return_value=[])
    mocker.patch("main.get_reply_rules", return_value=[])
    mocker.patch("main.get_promos", return_value=[])
    mocker.patch("main.get_settings", return_value={
        "is_on_break": False,
        "welcome_message": None,
        "handoff_keyword": "human",
        "telegram_chat_id": "chat-999",
    })
    mocker.patch("main.get_or_create_conversation", return_value={"last_message": "prev"})
    mocker.patch("main.generate_reply", return_value=ai_reply_with_order)
    mock_send_dm = mocker.patch("main.send_dm")
    mocker.patch("main.append_message")
    mocker.patch("main.update_conversation")
    mock_create_order = mocker.patch("main.create_order", return_value={"id": "order-1", "sender_name": "Juan"})
    mock_notify = mocker.patch("main.send_order_notification")

    payload = {"object": "page", "entry": [{"id": "page1", "messaging": [{
        "sender": {"id": "user1"},
        "message": {"text": "sige order na ko"}
    }]}]}
    _signed_post(payload)

    # Customer gets clean reply (no ORDER_CONFIRMED block)
    sent_text = mock_send_dm.call_args[0][2]
    assert "[ORDER_CONFIRMED]" not in sent_text
    assert "Confirmed!" in sent_text

    # Order was saved
    mock_create_order.assert_called_once()

    # Telegram was notified
    mock_notify.assert_called_once_with("chat-999", {"id": "order-1", "sender_name": "Juan"})

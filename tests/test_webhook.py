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

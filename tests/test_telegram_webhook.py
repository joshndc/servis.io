import os
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY") or "fake-anthropic-key"
os.environ["TELEGRAM_BOT_TOKEN"] = os.environ.get("TELEGRAM_BOT_TOKEN") or "fake-telegram-token"
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "fake-token")

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import main
from main import app

client = TestClient(app)


def _tg_update(text: str, chat_id: str = "chat-123") -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "chat": {"id": chat_id},
            "text": text,
            "from": {"id": chat_id}
        }
    }


def _tg_callback(data: str, chat_id: str = "chat-123") -> dict:
    return {
        "update_id": 2,
        "callback_query": {
            "id": "cq-1",
            "from": {"id": chat_id},
            "message": {"message_id": 10, "chat": {"id": chat_id}},
            "data": data
        }
    }


def test_telegram_connect_success(mocker):
    mocker.patch("main.find_settings_by_connect_code", return_value={
        "tenant_id": "t1",
        "telegram_connect_code": "servis-abc123",
    })
    mock_update = mocker.patch("main.update_settings", return_value={})
    mock_send = mocker.patch("main.send_message")

    response = client.post("/telegram", json=_tg_update("/connect servis-abc123"))
    assert response.status_code == 200
    mock_update.assert_called_once_with("t1", {"telegram_chat_id": "chat-123"})
    mock_send.assert_called_with("chat-123", "✅ Connected! You'll receive order notifications here.")


def test_telegram_connect_wrong_code(mocker):
    mocker.patch("main.find_settings_by_connect_code", return_value=None)
    mock_send = mocker.patch("main.send_message")

    response = client.post("/telegram", json=_tg_update("/connect wrong-code"))
    assert response.status_code == 200
    mock_send.assert_called_with("chat-123", "❌ Invalid code. Check your connect code and try again.")


def test_telegram_approve_callback(mocker):
    mocker.patch("main.get_settings_by_chat_id", return_value={
        "tenant_id": "t1", "telegram_chat_id": "chat-123"
    })
    mocker.patch("main.get_order", return_value={
        "id": "order-1", "customer_psid": "user-fb", "page_id": "page-1",
        "sender_name": "Juan"
    })
    mock_update_order = mocker.patch("main.update_order_status", return_value={"status": "approved"})
    mocker.patch("main.get_tenant_by_page_id", return_value={
        "access_token": "tok", "tenant_id": "t1"
    })
    mock_send_dm = mocker.patch("main.send_dm")
    mock_answer = mocker.patch("main.answer_callback_query")
    mock_edit = mocker.patch("main.edit_message_text")

    response = client.post("/telegram", json=_tg_callback("approve:order-1"))
    assert response.status_code == 200
    mock_update_order.assert_called_once_with("order-1", "approved")
    mock_send_dm.assert_called_once()
    mock_answer.assert_called_once()

import os
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "ANTHROPIC_API_KEY": "fake-key",
    "TELEGRAM_BOT_TOKEN": "fake-token",
}.items():
    os.environ[k] = os.environ.get(k) or v

from unittest.mock import patch, MagicMock

def test_send_message_calls_telegram_api():
    with patch("services.telegram.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(is_success=True)
        from services.telegram import send_message
        send_message("chat-123", "Hello!")
        mock_post.assert_called_once()
        call_json = mock_post.call_args.kwargs["json"]
        assert call_json["chat_id"] == "chat-123"
        assert call_json["text"] == "Hello!"

def test_send_order_notification_includes_order_details():
    with patch("services.telegram.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(is_success=True, json=lambda: {"result": {"message_id": 1}})
        from services.telegram import send_order_notification
        order = {
            "id": "abc-123",
            "sender_name": "Juan",
            "contact_number": "09171234567",
            "items": [{"name": "Milk Tea", "qty": 2, "price": 120}],
            "total_amount": 240,
            "pickup_time": "3pm",
            "notes": "less sugar",
        }
        send_order_notification("chat-456", order)
        call_json = mock_post.call_args.kwargs["json"]
        assert "Juan" in call_json["text"]
        assert "09171234567" in call_json["text"]
        assert "240" in call_json["text"]
        assert call_json["reply_markup"]["inline_keyboard"] is not None

def test_answer_callback_query_calls_api():
    with patch("services.telegram.httpx.post") as mock_post:
        mock_post.return_value = MagicMock(is_success=True)
        from services.telegram import answer_callback_query
        answer_callback_query("cq-id-1", "Order approved!")
        call_url = mock_post.call_args.args[0]
        assert "answerCallbackQuery" in call_url

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
from services.messenger import send_dm, send_comment_reply

def _mock_response(status_code=200):
    m = MagicMock()
    m.status_code = status_code
    m.raise_for_status = MagicMock()
    m.json.return_value = {"message_id": "mid.123"}
    return m

def test_send_dm_calls_graph_api():
    with patch("services.messenger.httpx.post") as mock_post:
        mock_post.return_value = _mock_response()
        send_dm("tok123", "user456", "Hello!")
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "graph.facebook.com" in url
        assert "/me/messages" in url

def test_send_dm_passes_correct_payload():
    with patch("services.messenger.httpx.post") as mock_post:
        mock_post.return_value = _mock_response()
        send_dm("tok123", "user456", "Hello!")
        kwargs = mock_post.call_args[1]
        assert kwargs["json"]["recipient"]["id"] == "user456"
        assert kwargs["json"]["message"]["text"] == "Hello!"
        assert kwargs["json"]["messaging_type"] == "RESPONSE"
        assert kwargs["params"]["access_token"] == "tok123"

def test_send_comment_reply_calls_graph_api():
    with patch("services.messenger.httpx.post") as mock_post:
        mock_post.return_value = _mock_response()
        send_comment_reply("tok123", "comment789", "Thank you!")
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "comment789" in url

def test_send_comment_reply_passes_correct_payload():
    with patch("services.messenger.httpx.post") as mock_post:
        mock_post.return_value = _mock_response()
        send_comment_reply("tok123", "comment789", "Thank you!")
        kwargs = mock_post.call_args[1]
        assert kwargs["json"]["message"] == "Thank you!"
        assert kwargs["params"]["access_token"] == "tok123"

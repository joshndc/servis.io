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
from services.gemini import generate_reply, build_catalog_text

def test_build_catalog_text_with_items():
    catalog = [
        {"name": "Milk Tea", "description": "Classic", "price": 80, "discounted_price": None},
        {"name": "Ube Pandesal", "description": None, "price": 25, "discounted_price": 20},
    ]
    text = build_catalog_text(catalog)
    assert "Milk Tea" in text
    assert "₱80" in text
    assert "Ube Pandesal" in text
    assert "₱20" in text  # discounted price used when available

def test_build_catalog_text_empty():
    assert build_catalog_text([]) == "No catalog available."

def test_generate_reply_returns_string():
    catalog = [{"name": "Milk Tea", "price": 80, "description": "Classic", "discounted_price": None}]
    with patch("services.gemini.model") as mock_model:
        mock_response = MagicMock()
        mock_response.text = "Meron kaming Milk Tea sa ₱80!"
        mock_model.generate_content.return_value = mock_response
        result = generate_reply("Magkano ang milk tea?", catalog)
        assert isinstance(result, str)
        assert len(result) > 0

def test_generate_reply_includes_catalog_in_prompt():
    catalog = [{"name": "Ube Pandesal", "price": 25, "description": "Fresh", "discounted_price": None}]
    with patch("services.gemini.model") as mock_model:
        mock_response = MagicMock()
        mock_response.text = "We have Ube Pandesal!"
        mock_model.generate_content.return_value = mock_response
        generate_reply("What do you sell?", catalog)
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Ube Pandesal" in call_args

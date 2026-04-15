import os
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "GEMINI_API_KEY": "fake-gemini-key",
}.items():
    os.environ.setdefault(k, v)

from services.sheets import parse_sheet_rows

def test_parse_valid_rows():
    rows = [
        ["name", "description", "price", "discounted_price", "category", "is_available"],
        ["Milk Tea", "Classic milk tea", "80", "", "drinks", "TRUE"],
        ["Ube Pandesal", "Fresh ube bread", "25", "20", "bread", "TRUE"],
    ]
    result = parse_sheet_rows(rows)
    assert len(result) == 2
    assert result[0]["name"] == "Milk Tea"
    assert result[0]["price"] == 80.0
    assert result[0]["discounted_price"] is None
    assert result[1]["discounted_price"] == 20.0

def test_parse_marks_unavailable():
    rows = [
        ["name", "description", "price", "discounted_price", "category", "is_available"],
        ["Sold Out", "", "50", "", "food", "FALSE"],
    ]
    result = parse_sheet_rows(rows)
    assert len(result) == 1
    assert result[0]["is_available"] is False

def test_parse_empty_sheet_returns_empty():
    assert parse_sheet_rows([]) == []
    assert parse_sheet_rows([["name", "price"]]) == []  # header only

def test_parse_skips_blank_rows():
    rows = [
        ["name", "description", "price", "discounted_price", "category", "is_available"],
        ["", "", "", "", "", ""],
        ["Milk Tea", "Classic", "80", "", "drinks", "TRUE"],
    ]
    result = parse_sheet_rows(rows)
    assert len(result) == 1
    assert result[0]["name"] == "Milk Tea"

import os
os.environ["SUPABASE_URL"] = os.environ.get("SUPABASE_URL") or "https://fake.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "fake-key"
os.environ["META_APP_SECRET"] = os.environ.get("META_APP_SECRET") or "fake-secret"
os.environ["META_WEBHOOK_VERIFY_TOKEN"] = os.environ.get("META_WEBHOOK_VERIFY_TOKEN") or "fake-token"
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY") or "fake-key"
os.environ["TELEGRAM_BOT_TOKEN"] = os.environ.get("TELEGRAM_BOT_TOKEN") or "fake-token"

from services.gemini import parse_order_from_reply

def test_parse_order_detects_block():
    reply = """Confirmed! See you at 3pm 😊
[ORDER_CONFIRMED]
name: Juan dela Cruz
contact: 09171234567
items: 2x Brown Sugar Milk Tea (₱120), 1x Taro Milk Tea (₱110)
total: 350
pickup_time: 3pm
notes: less sugar for taro
[/ORDER_CONFIRMED]"""
    order = parse_order_from_reply(reply)
    assert order is not None
    assert order["name"] == "Juan dela Cruz"
    assert order["contact"] == "09171234567"
    assert order["total"] == 350.0
    assert order["pickup_time"] == "3pm"
    assert order["notes"] == "less sugar for taro"
    assert len(order["items"]) == 2

def test_parse_order_returns_none_when_no_block():
    reply = "Sure! What size would you like? 😊"
    assert parse_order_from_reply(reply) is None

def test_strip_order_block_from_reply():
    from services.gemini import strip_order_block
    reply = "Confirmed! See you soon.\n[ORDER_CONFIRMED]\nname: Juan\n[/ORDER_CONFIRMED]"
    clean = strip_order_block(reply)
    assert "[ORDER_CONFIRMED]" not in clean
    assert "Confirmed! See you soon." in clean

def test_parse_items_from_string():
    from services.gemini import parse_order_items
    items_str = "2x Brown Sugar Milk Tea (₱120), 1x Taro Milk Tea (₱110)"
    items = parse_order_items(items_str)
    assert items[0] == {"name": "Brown Sugar Milk Tea", "qty": 2, "price": 120.0}
    assert items[1] == {"name": "Taro Milk Tea", "qty": 1, "price": 110.0}

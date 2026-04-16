# Telegram Bot + Order Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Telegram bot so business owners can receive order notifications and manage their store from their phone.

**Architecture:** Telegram webhook at `POST /telegram` added to the existing FastAPI service on Railway. AI detects confirmed orders via a structured `[ORDER_CONFIRMED]` tag in replies, saves to Supabase `orders` table, and sends a Telegram notification with inline Approve/Deny buttons.

**Tech Stack:** python-telegram-bot (bot API via httpx), FastAPI, Supabase, existing messenger.py for Facebook DMs.

---

## Context

- Backend: `backend/` — FastAPI app on Railway
- Key files: `main.py`, `services/gemini.py`, `services/tenant.py`, `services/messenger.py`, `config.py`
- Supabase tables: `tenants`, `facebook_pages`, `settings`, `catalog_cache`, `conversations`, `orders`, `reply_rules`, `promos`
- `orders` table has columns: `id`, `business_id`, `conversation_id`, `customer_psid`, `items` (jsonb), `delivery_type`, `delivery_address`, `total_amount`, `status`, `created_at`, `page_id`, `sender_name`, `contact_number`, `pickup_time`, `notes`
- `settings` table has new columns: `telegram_chat_id`, `telegram_connect_code`, `is_on_break`
- Tenant for "Sensei of Sheets": `id = 6811d326-6082-4716-8590-69643c7bc966`
- `business_id` in orders = `tenant_id` everywhere else
- Tests live in `tests/`, follow patterns in `test_webhook.py`
- All env vars go in Railway (never hardcoded). Local `.env` is gitignored.

---

## Task 1: Add TELEGRAM_BOT_TOKEN to config

**Files:**
- Modify: `backend/config.py`

**Step 1: Write the failing test**

In `tests/test_telegram_config.py`:
```python
import os
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "fake-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake-anthropic-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "fake-telegram-token")

import config

def test_telegram_bot_token_loaded():
    assert config.TELEGRAM_BOT_TOKEN == "fake-telegram-token"
```

**Step 2: Run test to verify it fails**
```bash
cd backend && pytest tests/test_telegram_config.py -v
```
Expected: FAIL with `AttributeError: module 'config' has no attribute 'TELEGRAM_BOT_TOKEN'`

**Step 3: Add to config.py**

Add this line after line 17 (`ANTHROPIC_API_KEY = _require(...)`):
```python
TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
```

**Step 4: Run test to verify it passes**
```bash
cd backend && pytest tests/test_telegram_config.py -v
```
Expected: PASS

**Step 5: Commit**
```bash
git add backend/config.py tests/test_telegram_config.py
git commit -m "feat: add TELEGRAM_BOT_TOKEN to config"
```

---

## Task 2: Orders service

**Files:**
- Create: `backend/services/orders.py`
- Create: `tests/test_orders.py`

**Step 1: Write the failing tests**

Create `tests/test_orders.py`:
```python
import os
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "fake-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "fake-token")

from unittest.mock import MagicMock, patch

def test_create_order_calls_supabase():
    mock_sb = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{"id": "order-123"}]
    with patch("services.orders.get_supabase", return_value=mock_sb):
        from services.orders import create_order
        result = create_order(
            tenant_id="tenant-1",
            page_id="page-1",
            sender_id="sender-1",
            sender_name="Juan",
            contact_number="09171234567",
            items=[{"name": "Milk Tea", "qty": 2, "price": 120}],
            total_price=240,
            pickup_time="3pm",
            notes="less sugar"
        )
        assert result["id"] == "order-123"

def test_update_order_status_calls_supabase():
    mock_sb = MagicMock()
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "order-123", "status": "approved"}]
    with patch("services.orders.get_supabase", return_value=mock_sb):
        from services.orders import update_order_status
        result = update_order_status("order-123", "approved")
        assert result["status"] == "approved"

def test_get_pending_orders_returns_list():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": "order-1", "status": "pending"}
    ]
    with patch("services.orders.get_supabase", return_value=mock_sb):
        from services.orders import get_pending_orders
        result = get_pending_orders("tenant-1")
        assert len(result) == 1
        assert result[0]["id"] == "order-1"
```

**Step 2: Run tests to verify they fail**
```bash
cd backend && pytest tests/test_orders.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'services.orders'`

**Step 3: Create backend/services/orders.py**
```python
from services.tenant import get_supabase


def create_order(
    tenant_id: str,
    page_id: str,
    sender_id: str,
    sender_name: str,
    contact_number: str,
    items: list,
    total_price: float,
    pickup_time: str = None,
    notes: str = None,
) -> dict:
    """Insert a new order with status=pending. Returns the created row."""
    payload = {
        "business_id": tenant_id,
        "page_id": page_id,
        "customer_psid": sender_id,
        "sender_name": sender_name,
        "contact_number": contact_number,
        "items": items,
        "total_amount": total_price,
        "pickup_time": pickup_time,
        "notes": notes,
        "status": "pending",
        "delivery_type": "pickup",
    }
    result = get_supabase().table("orders").insert(payload).execute()
    return result.data[0] if result.data else {}


def update_order_status(order_id: str, status: str) -> dict:
    """Update order status. status: pending | approved | denied | cancelled"""
    result = (
        get_supabase()
        .table("orders")
        .update({"status": status})
        .eq("id", order_id)
        .execute()
    )
    return result.data[0] if result.data else {}


def get_pending_orders(tenant_id: str) -> list:
    """Return all pending orders for a tenant."""
    result = (
        get_supabase()
        .table("orders")
        .select("*")
        .eq("business_id", tenant_id)
        .eq("status", "pending")
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


def get_order(order_id: str) -> dict:
    """Return a single order by id."""
    result = (
        get_supabase()
        .table("orders")
        .select("*")
        .eq("id", order_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else {}
```

**Step 4: Run tests to verify they pass**
```bash
cd backend && pytest tests/test_orders.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**
```bash
git add backend/services/orders.py tests/test_orders.py
git commit -m "feat: add orders service (create, update, get)"
```

---

## Task 3: Tenant service — settings helpers

**Files:**
- Modify: `backend/services/tenant.py`
- Modify: `tests/test_tenant.py`

**Step 1: Write the failing tests**

Add to the bottom of `tests/test_tenant.py`:
```python
def test_get_settings_by_chat_id_returns_row(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"tenant_id": "t1", "telegram_chat_id": "chat-999"}
    ]
    from services.tenant import get_settings_by_chat_id
    result = get_settings_by_chat_id("chat-999")
    assert result["tenant_id"] == "t1"

def test_update_settings_calls_supabase(mock_supabase):
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        {"tenant_id": "t1", "is_on_break": True}
    ]
    from services.tenant import update_settings
    result = update_settings("t1", {"is_on_break": True})
    assert result["is_on_break"] is True
```

**Step 2: Run tests to verify they fail**
```bash
cd backend && pytest tests/test_tenant.py -v -k "chat_id or update_settings"
```
Expected: FAIL with `ImportError`

**Step 3: Add functions to backend/services/tenant.py**

Append to the end of `backend/services/tenant.py`:
```python
def get_settings_by_chat_id(chat_id: str):
    """Look up settings row by telegram_chat_id."""
    result = (get_supabase().table("settings")
              .select("*")
              .eq("telegram_chat_id", chat_id)
              .limit(1)
              .execute())
    return result.data[0] if result.data else None


def update_settings(tenant_id: str, updates: dict) -> dict:
    """Partial update of a settings row."""
    result = (get_supabase().table("settings")
              .update(updates)
              .eq("tenant_id", tenant_id)
              .execute())
    return result.data[0] if result.data else {}
```

**Step 4: Run tests to verify they pass**
```bash
cd backend && pytest tests/test_tenant.py -v
```
Expected: PASS

**Step 5: Commit**
```bash
git add backend/services/tenant.py tests/test_tenant.py
git commit -m "feat: add get_settings_by_chat_id and update_settings to tenant service"
```

---

## Task 4: Telegram service

**Files:**
- Create: `backend/services/telegram.py`
- Create: `tests/test_telegram_service.py`

**Step 1: Write the failing tests**

Create `tests/test_telegram_service.py`:
```python
import os
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "fake-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "fake-token")

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
```

**Step 2: Run tests to verify they fail**
```bash
cd backend && pytest tests/test_telegram_service.py -v
```
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create backend/services/telegram.py**
```python
import logging
import httpx
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: str, text: str) -> dict:
    """Send a plain text message to a Telegram chat."""
    response = httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )
    if not response.is_success:
        logger.error(f"Telegram sendMessage failed: {response.text}")
    return response.json()


def send_order_notification(chat_id: str, order: dict) -> dict:
    """Send new order notification with Approve/Deny inline buttons."""
    order_id = order.get("id", "")
    short_id = str(order_id)[:8]  # first 8 chars for display

    items_text = "\n".join(
        f"   {i.get('qty', 1)}x {i.get('name', '')} (₱{i.get('price', 0)})"
        for i in (order.get("items") or [])
    )

    text = (
        f"🛒 New Order #{short_id}\n\n"
        f"👤 {order.get('sender_name', 'Unknown')}\n"
        f"📞 {order.get('contact_number', '-')}\n"
        f"📦 Items:\n{items_text}\n"
        f"💰 Total: ₱{order.get('total_amount', 0)}\n"
    )
    if order.get("pickup_time"):
        text += f"🕒 Pickup: {order['pickup_time']}\n"
    if order.get("notes"):
        text += f"📝 {order['notes']}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve:{order_id}"},
            {"text": "❌ Deny", "callback_data": f"deny:{order_id}"},
        ]]
    }

    response = httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text, "reply_markup": keyboard},
        timeout=10,
    )
    if not response.is_success:
        logger.error(f"Telegram order notification failed: {response.text}")
    return response.json()


def edit_message_text(chat_id: str, message_id: int, text: str) -> dict:
    """Edit an existing message (used after approve/deny to update notification)."""
    response = httpx.post(
        f"{TELEGRAM_API}/editMessageText",
        json={"chat_id": chat_id, "message_id": message_id, "text": text},
        timeout=10,
    )
    return response.json()


def answer_callback_query(callback_query_id: str, text: str) -> dict:
    """Acknowledge a button tap (shows popup on phone)."""
    response = httpx.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": text},
        timeout=10,
    )
    return response.json()
```

**Step 4: Run tests to verify they pass**
```bash
cd backend && pytest tests/test_telegram_service.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**
```bash
git add backend/services/telegram.py tests/test_telegram_service.py
git commit -m "feat: add telegram service (send_message, send_order_notification, answer_callback)"
```

---

## Task 5: AI order detection — prompt + parser

**Files:**
- Modify: `backend/services/gemini.py`
- Create: `tests/test_order_detection.py`

**Step 1: Write the failing tests**

Create `tests/test_order_detection.py`:
```python
import os
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "fake-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "fake-token")

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
```

**Step 2: Run tests to verify they fail**
```bash
cd backend && pytest tests/test_order_detection.py -v
```
Expected: FAIL with `ImportError`

**Step 3: Add parser functions and update system prompt in backend/services/gemini.py**

Add these imports at the top of `backend/services/gemini.py` (after existing imports):
```python
import re
```

Add these functions before `generate_reply()`:
```python
def parse_order_items(items_str: str) -> list:
    """Parse items string like '2x Brown Sugar Milk Tea (₱120), 1x Taro (₱110)'"""
    items = []
    # Match: NUMx NAME (₱PRICE) or NUMx NAME
    pattern = r'(\d+)x\s+([^(,₱]+?)(?:\s*\(₱?([\d.]+)\))?\s*(?:,|$)'
    for m in re.finditer(pattern, items_str):
        qty = int(m.group(1))
        name = m.group(2).strip()
        price = float(m.group(3)) if m.group(3) else 0.0
        items.append({"name": name, "qty": qty, "price": price})
    return items


def parse_order_from_reply(reply: str) -> dict | None:
    """Extract structured order data from [ORDER_CONFIRMED]...[/ORDER_CONFIRMED] block."""
    match = re.search(r'\[ORDER_CONFIRMED\](.*?)\[/ORDER_CONFIRMED\]', reply, re.DOTALL)
    if not match:
        return None
    block = match.group(1).strip()
    data = {}
    for line in block.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            data[key.strip()] = val.strip()
    items_str = data.get("items", "")
    return {
        "name": data.get("name", ""),
        "contact": data.get("contact", ""),
        "items": parse_order_items(items_str),
        "total": float(data.get("total", 0) or 0),
        "pickup_time": data.get("pickup_time") or None,
        "notes": data.get("notes") or None,
    }


def strip_order_block(reply: str) -> str:
    """Remove [ORDER_CONFIRMED]...[/ORDER_CONFIRMED] block from reply text."""
    return re.sub(r'\s*\[ORDER_CONFIRMED\].*?\[/ORDER_CONFIRMED\]', '', reply, flags=re.DOTALL).strip()
```

Now update the system prompt inside `generate_reply()`. Find the `IMPORTANT RULES:` section near the end of the system prompt and add this block just before `BUSINESS DATA:`:

```python
    system = f"""...(existing prompt)...

---

ORDER DETECTION:
When you have collected ALL of the following from the customer:
- Their name
- Their contact number
- The items they want (with quantities)

Then confirm the order with the customer. Once they confirm, append this block at the END of your reply (after your message to the customer):

[ORDER_CONFIRMED]
name: <customer full name>
contact: <contact number>
items: <qty>x <product name> (₱<price>), <qty>x <product name> (₱<price>)
total: <total amount as number>
pickup_time: <time if mentioned, else leave blank>
notes: <special instructions if any, else leave blank>
[/ORDER_CONFIRMED]

IMPORTANT: Only append this block ONCE when the customer explicitly confirms. Never append it for inquiries or tentative interest.

---

BUSINESS DATA:
Products:
{catalog_text}{promo_section}"""
```

**Step 4: Run tests to verify they pass**
```bash
cd backend && pytest tests/test_order_detection.py -v
```
Expected: PASS (4 tests)

**Step 5: Commit**
```bash
git add backend/services/gemini.py tests/test_order_detection.py
git commit -m "feat: add order detection parser and ORDER_CONFIRMED prompt block"
```

---

## Task 6: Break mode in webhook handler

**Files:**
- Modify: `backend/main.py`
- Modify: `tests/test_webhook.py`

**Step 1: Write the failing test**

Add to `tests/test_webhook.py`:
```python
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
```

Note: this test requires `pytest-mock`. Check `requirements.txt` — if `pytest-mock` is missing, add it.

**Step 2: Run test to verify it fails**
```bash
cd backend && pytest tests/test_webhook.py::test_dm_on_break_sends_break_message -v
```
Expected: FAIL

**Step 3: Add break mode check to main.py DM handler**

In `backend/main.py`, inside the `for event in entry.get("messaging", []):` block, add the break check AFTER the handoff check and BEFORE the keyword rule match (around line 85):

```python
                # Break mode check
                if settings.get("is_on_break"):
                    send_dm(access_token, sender_id, "We're on a break right now. We'll be back soon! 😊")
                    continue
```

**Step 4: Run test to verify it passes**
```bash
cd backend && pytest tests/test_webhook.py -v
```
Expected: all PASS

**Step 5: Commit**
```bash
git add backend/main.py tests/test_webhook.py
git commit -m "feat: add break mode — AI pauses when is_on_break is true"
```

---

## Task 7: Order detection in DM flow + Telegram notification

**Files:**
- Modify: `backend/main.py`

**Step 1: Write the failing test**

Add to `tests/test_webhook.py`:
```python
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
```

**Step 2: Run test to verify it fails**
```bash
cd backend && pytest tests/test_webhook.py::test_dm_order_confirmed_creates_order_and_notifies -v
```
Expected: FAIL

**Step 3: Update main.py**

At the top of `main.py`, add these imports:
```python
from services.gemini import parse_order_from_reply, strip_order_block
from services.orders import create_order
from services.telegram import send_order_notification
```

In the DM handler, replace the AI reply block (currently around lines 94-99):
```python
                # AI reply with conversation history
                append_message(page_id, sender_id, "user", message_text)
                raw_reply = generate_reply(message_text, catalog, promos, history)

                # Detect and handle confirmed order
                order_data = parse_order_from_reply(raw_reply)
                clean_reply = strip_order_block(raw_reply)

                if order_data:
                    order = create_order(
                        tenant_id=tenant_id,
                        page_id=page_id,
                        sender_id=sender_id,
                        sender_name=order_data["name"],
                        contact_number=order_data["contact"],
                        items=order_data["items"],
                        total_price=order_data["total"],
                        pickup_time=order_data.get("pickup_time"),
                        notes=order_data.get("notes"),
                    )
                    tg_chat_id = settings.get("telegram_chat_id")
                    if tg_chat_id and order:
                        send_order_notification(tg_chat_id, order)

                send_dm(access_token, sender_id, clean_reply)
                append_message(page_id, sender_id, "assistant", clean_reply)
                update_conversation(page_id, sender_id, {"last_message": message_text, "status": "open"})
```

**Step 4: Run tests to verify they pass**
```bash
cd backend && pytest tests/test_webhook.py -v
```
Expected: all PASS

**Step 5: Commit**
```bash
git add backend/main.py tests/test_webhook.py
git commit -m "feat: detect ORDER_CONFIRMED in AI reply, save order, notify Telegram"
```

---

## Task 8: POST /telegram endpoint (commands + callbacks)

**Files:**
- Modify: `backend/main.py`
- Create: `tests/test_telegram_webhook.py`

**Step 1: Write the failing tests**

Create `tests/test_telegram_webhook.py`:
```python
import os
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "fake-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "fake-token")

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
    mocker.patch("main.get_settings", return_value={
        "tenant_id": "t1",
        "telegram_connect_code": "servis-abc123",
        "telegram_chat_id": None,
    })
    # get_settings_by_connect_code lookup
    mocker.patch("main.get_supabase_client").return_value = MagicMock()
    mock_find = mocker.patch("main.find_settings_by_connect_code", return_value={
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
    mock_get_page = mocker.patch("main.get_tenant_by_page_id", return_value={
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
```

**Step 2: Run tests to verify they fail**
```bash
cd backend && pytest tests/test_telegram_webhook.py -v
```
Expected: FAIL with `404` (endpoint doesn't exist yet)

**Step 3: Add POST /telegram to main.py**

Add these imports at the top of `main.py`:
```python
from services.telegram import send_message, answer_callback_query, edit_message_text
from services.tenant import get_settings_by_chat_id, update_settings
from services.orders import get_order, update_order_status
```

Add a helper function before the routes:
```python
def find_settings_by_connect_code(code: str):
    """Find settings row by telegram_connect_code."""
    from services.tenant import get_supabase
    result = (get_supabase().table("settings")
              .select("*")
              .eq("telegram_connect_code", code)
              .limit(1)
              .execute())
    return result.data[0] if result.data else None
```

Add the endpoint after the `/sync-catalog` route:
```python
@app.post("/telegram")
async def telegram_webhook(request: Request):
    body = await request.json()

    # --- Handle inline button callbacks (approve/deny) ---
    if "callback_query" in body:
        cq = body["callback_query"]
        cq_id = cq["id"]
        chat_id = str(cq["message"]["chat"]["id"])
        message_id = cq["message"]["message_id"]
        data = cq.get("data", "")

        settings = get_settings_by_chat_id(chat_id)
        if not settings:
            answer_callback_query(cq_id, "❌ Account not connected.")
            return {"ok": True}

        if ":" not in data:
            return {"ok": True}

        action, order_id = data.split(":", 1)

        if action in ("approve", "deny"):
            status = "approved" if action == "approve" else "denied"
            update_order_status(order_id, status)

            order = get_order(order_id)
            if order:
                page = get_tenant_by_page_id(order.get("page_id", ""))
                if page:
                    if status == "approved":
                        msg = "Great news! Your order has been approved. 🎉 We'll see you soon!"
                    else:
                        msg = "We're sorry, your order could not be processed at this time."
                    send_dm(page["access_token"], order["customer_psid"], msg)

            emoji = "✅" if status == "approved" else "❌"
            edit_message_text(chat_id, message_id, f"{emoji} Order {status.capitalize()}: #{order_id[:8]}")
            answer_callback_query(cq_id, f"Order {status}!")

        return {"ok": True}

    # --- Handle text commands ---
    message = body.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return {"ok": True}

    # /connect <code>
    if text.startswith("/connect"):
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ""
        row = find_settings_by_connect_code(code)
        if row:
            update_settings(row["tenant_id"], {"telegram_chat_id": chat_id})
            send_message(chat_id, "✅ Connected! You'll receive order notifications here.")
        else:
            send_message(chat_id, "❌ Invalid code. Check your connect code and try again.")
        return {"ok": True}

    # All other commands require a connected account
    settings = get_settings_by_chat_id(chat_id)
    if not settings:
        send_message(chat_id, "👋 To connect your account, send: /connect <your-code>")
        return {"ok": True}

    tenant_id = settings["tenant_id"]

    # /sync
    if text == "/sync":
        sheet_url = settings.get("google_sheet_id")
        if not sheet_url:
            send_message(chat_id, "❌ No Google Sheet configured yet.")
        else:
            try:
                import json
                from pathlib import Path
                sa_path = Path(__file__).parent / "service_account.json"
                if sa_path.exists():
                    service_account = json.loads(sa_path.read_text())
                else:
                    import os as _os
                    raw = _os.environ.get("GOOGLE_SERVICE_ACCOUNT")
                    service_account = json.loads(raw) if raw else None
                if not service_account:
                    send_message(chat_id, "❌ No service account configured.")
                else:
                    from services.sheets import sync_catalog_from_sheet
                    counts = sync_catalog_from_sheet(tenant_id, sheet_url, service_account)
                    send_message(chat_id, f"✅ Synced! Products: {counts.get('products',0)}, Rules: {counts.get('rules',0)}, Promos: {counts.get('promos',0)}")
            except Exception as e:
                send_message(chat_id, f"❌ Sync failed: {str(e)}")

    # /break
    elif text == "/break":
        update_settings(tenant_id, {"is_on_break": True})
        send_message(chat_id, "⏸ Break mode ON. AI will reply with a break message.")

    # /back
    elif text == "/back":
        update_settings(tenant_id, {"is_on_break": False})
        send_message(chat_id, "▶️ Back online! AI is responding normally.")

    # /cancel <order_id>
    elif text.startswith("/cancel"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Usage: /cancel <order_id>")
        else:
            order_id = parts[1].strip()
            order = get_order(order_id)
            if not order:
                send_message(chat_id, "❌ Order not found.")
            else:
                update_order_status(order_id, "cancelled")
                page = get_tenant_by_page_id(order.get("page_id", ""))
                if page:
                    send_dm(page["access_token"], order["customer_psid"],
                            "We're sorry, your order has been cancelled. Feel free to order again! 😊")
                send_message(chat_id, f"✅ Order #{order_id[:8]} cancelled.")

    # /status
    elif text == "/status":
        from services.orders import get_pending_orders
        from services.tenant import get_supabase as _gsb
        pending = get_pending_orders(tenant_id)
        open_convs = (_gsb().table("conversations")
                      .select("id", count="exact")
                      .eq("page_id", settings.get("page_id", ""))
                      .eq("status", "open")
                      .execute())
        open_count = open_convs.count or 0
        send_message(chat_id, f"📊 Status\n🛒 Pending orders: {len(pending)}\n💬 Open conversations: {open_count}")

    else:
        send_message(chat_id, "Commands: /sync /break /back /cancel <id> /status")

    return {"ok": True}
```

**Step 4: Run tests to verify they pass**
```bash
cd backend && pytest tests/test_telegram_webhook.py -v
```
Expected: PASS

**Step 5: Run full test suite**
```bash
cd backend && pytest -v
```
Expected: all PASS

**Step 6: Commit**
```bash
git add backend/main.py tests/test_telegram_webhook.py
git commit -m "feat: add POST /telegram endpoint with commands and order callbacks"
```

---

## Task 9: Register Telegram webhook + smoke test

**Step 1: Push to Railway**
```bash
git push
```
Wait for Railway to redeploy (check Railway dashboard).

**Step 2: Register Telegram webhook**

Replace `<RAILWAY_URL>` with your actual Railway URL and `<TOKEN>` with your bot token:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<RAILWAY_URL>/telegram"
```
Expected response: `{"ok":true,"result":true,"description":"Webhook was set"}`

**Step 3: Verify webhook is registered**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
Expected: `"url": "https://<RAILWAY_URL>/telegram"` and `"pending_update_count": 0`

**Step 4: Connect your Telegram account**
1. Open Telegram, find your bot (search by bot username from BotFather)
2. Send: `/connect servis-3292ce71`
3. Expected reply: `✅ Connected! You'll receive order notifications here.`

**Step 5: Test break mode**
1. Send `/break` to bot → expected: `⏸ Break mode ON`
2. Send a DM to Sensei of Sheets Facebook page → expected: break message
3. Send `/back` to bot → expected: `▶️ Back online!`

**Step 6: Test sync**
1. Send `/sync` to bot
2. Expected: `✅ Synced! Products: 5, Rules: X, Promos: X`

**Step 7: Test order flow (end-to-end)**
1. DM the Facebook page and place a complete order (name, items, contact)
2. Confirm the order
3. Telegram bot should send notification with ✅ Approve / ❌ Deny buttons
4. Tap Approve → Facebook page sends confirmation DM to customer

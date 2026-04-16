# Telegram Bot + Order Management Design

**Goal:** Let business owners manage orders and control their AI assistant via Telegram on mobile.

**Date:** 2026-04-16

---

## Architecture

```
Customer DMs Facebook Page
        ↓
FastAPI (Railway) — AI replies, detects confirmed order
        ↓
Supabase — order saved (status: pending)
        ↓
Telegram Bot (same FastAPI service, POST /telegram)
        ↓
Owner taps [✅ Approve #12] or [❌ Deny #12]
        ↓
Supabase updated — AI sends confirmation DM to customer
```

Single service on Railway. Telegram webhook registered at `POST /telegram`.

---

## Supabase Changes

**orders table** (already exists, added columns):
- `page_id` text
- `sender_name` text
- `contact_number` text
- `pickup_time` text
- `notes` text

**settings table** (columns added):
- `telegram_chat_id` text — saved when owner runs /connect
- `telegram_connect_code` text — pre-generated auth code
- `is_on_break` boolean default false — toggled by /break and /back

---

## AI Order Detection

When the AI has collected all required order info (name, items, quantity, contact), it appends a structured marker to its reply:

```
[ORDER_CONFIRMED]
name: Juan dela Cruz
contact: 09171234567
items: 2x Brown Sugar Milk Tea (₱120), 1x Taro Milk Tea (₱110)
total: 350
pickup_time: 3pm
notes: less sugar for taro
[/ORDER_CONFIRMED]
```

Backend behavior:
1. Detect `[ORDER_CONFIRMED]...[/ORDER_CONFIRMED]` block in AI reply
2. Parse fields into structured dict
3. Strip block from reply before sending to customer
4. Save order to Supabase (status: pending)
5. Send Telegram notification to owner

---

## Telegram Bot

**Token:** stored as `TELEGRAM_BOT_TOKEN` in Railway env vars (never in code).

**Webhook:** registered at `https://<railway-url>/telegram` via:
```
POST https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://<railway-url>/telegram
```

### Commands

| Command | Action |
|---|---|
| `/connect servis-XXXXXXXX` | Links owner's Telegram chat_id to their tenant |
| `/sync` | Triggers Google Sheet sync for the linked tenant |
| `/break` | Sets is_on_break=true, AI replies with break message |
| `/back` | Sets is_on_break=false, AI resumes normal replies |
| `/cancel [order_id]` | Sets order status to cancelled, notifies customer via DM |
| `/status` | Shows count of open conversations + pending orders |

### New Order Notification

Sent automatically when order is detected:

```
🛒 New Order #12

👤 Juan dela Cruz
📞 09171234567
📦 2x Brown Sugar Milk Tea
   1x Taro Milk Tea
💰 Total: ₱350
🕒 Pickup: 3pm
📝 less sugar for taro

[✅ Approve] [❌ Deny]
```

Tapping a button:
- Updates order status in Supabase
- Sends confirmation or rejection DM to customer via Facebook
- Edits the Telegram message to show final status

### /connect Flow

1. Owner messages bot: `/connect servis-3292ce71`
2. Bot checks code against `settings.telegram_connect_code`
3. If match: saves `telegram_chat_id` to settings, replies "✅ Connected!"
4. All future notifications go to this chat_id

### Break Mode

When `is_on_break = true`:
- AI skips normal reply logic
- Sends hardcoded message: "We're on a break right now. We'll be back soon! 😊"
- Orders are NOT accepted during break

---

## New Files

- `backend/services/telegram.py` — bot logic (send message, send order notification, handle callback)
- `backend/services/orders.py` — create_order(), update_order_status(), get_pending_orders()

## Modified Files

- `backend/main.py` — add `POST /telegram` endpoint, integrate order detection in webhook handler
- `backend/services/gemini.py` — add ORDER_CONFIRMED block to system prompt, add break mode check
- `backend/services/tenant.py` — add get_settings_by_chat_id(), update_settings()

---

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |


import config  # validates all env vars at startup
import json
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, Response, HTTPException, Query
from typing import Optional
from config import META_WEBHOOK_VERIFY_TOKEN, META_APP_SECRET, ADMIN_TOKEN
from services.tenant import (
    get_tenant_by_page_id, get_catalog, get_reply_rules,
    get_settings, get_promos, get_or_create_conversation, update_conversation, append_message
)
from services.rules import match_rule
from services.gemini import generate_reply, parse_order_from_reply, strip_order_block
from services.messenger import send_dm, send_comment_reply
from services.orders import create_order, get_order, update_order_status
from services.telegram import send_order_notification, send_message, answer_callback_query, edit_message_text
from services.tenant import get_settings_by_chat_id, update_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="servis.io backend")

def find_settings_by_connect_code(code: str):
    """Find settings row by telegram_connect_code."""
    from services.tenant import get_supabase
    result = (get_supabase().table("settings")
              .select("*")
              .eq("telegram_connect_code", code)
              .limit(1)
              .execute())
    return result.data[0] if result.data else None


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == META_WEBHOOK_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    expected_sig = "sha256=" + hmac.new(
        META_APP_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig_header, expected_sig):
        raise HTTPException(status_code=403, detail="Invalid signature")
    body = json.loads(raw_body)
    if body.get("object") != "page":
        return {"status": "ignored"}

    for entry in body.get("entry", []):
        try:
            page_id = entry.get("id")
            page = get_tenant_by_page_id(page_id)
            if not page:
                continue

            tenant_id = page["tenant_id"]
            access_token = page["access_token"]
            catalog = get_catalog(tenant_id)
            rules = get_reply_rules(tenant_id)
            promos = get_promos(tenant_id)
            settings = get_settings(tenant_id) or {}

            # Handle DMs
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                message_text = event.get("message", {}).get("text", "")
                if not message_text:
                    continue

                conv = get_or_create_conversation(page_id, sender_id)
                history = conv.get("message_history") or []
                is_new = not conv.get("last_message")

                # Welcome message — only on very first message
                if is_new and settings.get("welcome_message"):
                    send_dm(access_token, sender_id, settings["welcome_message"])

                # Handoff check
                handoff_kw = settings.get("handoff_keyword", "human")
                if handoff_kw and handoff_kw.lower() in message_text.lower():
                    send_dm(access_token, sender_id, "Connecting you to our team. Please wait!")
                    update_conversation(page_id, sender_id, {"status": "escalated"})
                    continue

                # Break mode check
                if settings.get("is_on_break"):
                    send_dm(access_token, sender_id, "We're on a break right now. We'll be back soon! 😊")
                    continue

                # Keyword rule match
                rule_reply = match_rule(message_text, rules)
                if rule_reply:
                    send_dm(access_token, sender_id, rule_reply)
                    update_conversation(page_id, sender_id, {"last_message": message_text})
                    append_message(page_id, sender_id, "user", message_text)
                    append_message(page_id, sender_id, "assistant", rule_reply)
                    continue

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
                    if tg_chat_id and order.get("id"):
                        send_order_notification(tg_chat_id, order)

                send_dm(access_token, sender_id, clean_reply)
                append_message(page_id, sender_id, "assistant", clean_reply)
                update_conversation(page_id, sender_id, {"last_message": message_text, "status": "open"})

            # Handle comments
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if change.get("field") != "feed" or value.get("item") != "comment":
                    continue
                comment_id = value.get("comment_id")
                comment_text = value.get("message", "")
                commenter_id = value.get("from", {}).get("id")
                if not comment_id or not comment_text:
                    continue

                mode = settings.get("comment_reply_mode", "comment")
                reply = match_rule(comment_text, rules) or generate_reply(comment_text, catalog, promos)

                if mode == "dm" and commenter_id:
                    send_dm(access_token, commenter_id, reply)
                else:
                    send_comment_reply(access_token, comment_id, reply)

        except Exception as exc:
            logger.error(f"Error processing entry {entry.get('id')}: {exc}", exc_info=True)
            continue

    return {"status": "ok"}

@app.post("/sync-catalog")
async def sync_catalog(request: Request):
    import json, gspread.exceptions
    from pathlib import Path
    # Auth check
    token = request.headers.get("X-Admin-Token", "")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    tenant_id = body.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing required field: tenant_id")
    # Load sheet URL from settings
    settings = get_settings(tenant_id)
    sheet_url = (settings or {}).get("google_sheet_id")
    if not sheet_url:
        raise HTTPException(status_code=400, detail="No Google Sheet URL configured for this tenant. Set google_sheet_id in settings.")
    # Load service account from file or env
    sa_path = Path(__file__).parent / "service_account.json"
    if sa_path.exists():
        service_account = json.loads(sa_path.read_text())
    else:
        import os
        raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
        if not raw:
            raise HTTPException(status_code=500, detail="No service account credentials configured")
        service_account = json.loads(raw)
    try:
        from services.sheets import sync_catalog_from_sheet
        counts = sync_catalog_from_sheet(tenant_id, sheet_url, service_account)
        return {"synced": counts}
    except gspread.exceptions.SpreadsheetNotFound:
        raise HTTPException(status_code=400, detail="Sheet not found or not accessible. Check the URL and sharing settings.")
    except Exception as e:
        logger.error(f"Sync failed for tenant {tenant_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {type(e).__name__}: {str(e)}")


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
                import json as _json
                from pathlib import Path
                sa_path = Path(__file__).parent / "service_account.json"
                if sa_path.exists():
                    service_account = _json.loads(sa_path.read_text())
                else:
                    import os as _os
                    raw = _os.environ.get("GOOGLE_SERVICE_ACCOUNT")
                    service_account = _json.loads(raw) if raw else None
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
        pending = get_pending_orders(tenant_id)
        send_message(chat_id, f"📊 Status\n🛒 Pending orders: {len(pending)}")

    else:
        send_message(chat_id, "Commands: /sync /break /back /cancel <id> /status")

    return {"ok": True}

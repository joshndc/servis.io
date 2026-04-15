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
    get_settings, get_promos, get_or_create_conversation, update_conversation
)
from services.rules import match_rule
from services.gemini import generate_reply
from services.messenger import send_dm, send_comment_reply

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="servis.io backend")

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

                # Welcome message for new conversations
                if not conv.get("detected_language") and settings.get("welcome_message"):
                    send_dm(access_token, sender_id, settings["welcome_message"])

                # Handoff check
                handoff_kw = settings.get("handoff_keyword", "human")
                if handoff_kw and handoff_kw.lower() in message_text.lower():
                    send_dm(access_token, sender_id, "Connecting you to our team. Please wait!")
                    update_conversation(page_id, sender_id, {"status": "escalated"})
                    continue

                # Keyword rule match
                rule_reply = match_rule(message_text, rules)
                if rule_reply:
                    send_dm(access_token, sender_id, rule_reply)
                    update_conversation(page_id, sender_id, {"last_message": message_text})
                    continue

                # AI reply
                reply = generate_reply(message_text, catalog, promos)
                send_dm(access_token, sender_id, reply)
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
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

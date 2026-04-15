# Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the servis.io FastAPI backend — a multi-tenant Facebook auto-reply engine that receives webhook events, matches keyword rules, calls Gemini Flash, and sends replies via the Meta Graph API.

**Architecture:** FastAPI app hosted on Railway. Each webhook event is identified by `page_id` → tenant lookup in Supabase → keyword rules checked → Gemini Flash called with catalog context → reply sent via Meta Graph API. Google Sheets synced to `catalog_cache` table in Supabase.

**Tech Stack:** Python 3.11+, FastAPI, Supabase (supabase-py), google-generativeai, httpx, python-dotenv, pytest

---

### Task 1: Project scaffold

**Files:**
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env` (symlink or copy from root)
- Create: `tests/__init__.py`
- Create: `tests/test_health.py`

**Step 1: Create folder structure**

```
backend/
  main.py
  config.py
  requirements.txt
  services/
    __init__.py
  tests/
    __init__.py
    test_health.py
```

Run in terminal:
```bash
cd C:/Users/jcndc/github/servis.io
mkdir -p backend/services tests
```

**Step 2: Write `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn==0.30.6
supabase==2.7.4
google-generativeai==0.7.2
httpx==0.27.2
python-dotenv==1.0.1
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

**Step 3: Create and activate virtual environment**

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

**Step 4: Write `backend/config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
META_APP_SECRET = os.environ["META_APP_SECRET"]
META_WEBHOOK_VERIFY_TOKEN = os.environ["META_WEBHOOK_VERIFY_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
```

**Step 5: Write `backend/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="servis.io backend")

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 6: Write `tests/test_health.py`**

```python
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 7: Run test**

```bash
cd C:/Users/jcndc/github/servis.io
pytest tests/test_health.py -v
```
Expected: PASS

**Step 8: Start dev server to verify manually**

```bash
cd backend
uvicorn main:app --reload
```
Open `http://localhost:8000/health` — should return `{"status": "ok"}`

**Step 9: Commit**

```bash
cd C:/Users/jcndc/github/servis.io
git add backend/ tests/
git commit -m "feat: scaffold FastAPI backend with health check"
```

---

### Task 2: Supabase schema

**Files:**
- No code files — SQL run directly in Supabase SQL editor

**Step 1: Open Supabase SQL editor**

Go to `https://supabase.com/dashboard/project/nfgverphajkqharxpwpi` → **SQL Editor** → **New query**

**Step 2: Run this SQL**

```sql
-- Tenants
create table tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null unique,
  plan text not null default 'starter',
  created_at timestamptz default now()
);

-- Facebook Pages
create table facebook_pages (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  page_id text not null unique,
  page_name text,
  access_token text not null,
  webhook_subscribed boolean default false,
  created_at timestamptz default now()
);

-- Catalog cache
create table catalog_cache (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  name text not null,
  description text,
  price numeric,
  discounted_price numeric,
  category text,
  is_available boolean default true,
  synced_at timestamptz default now()
);

-- Conversations
create table conversations (
  id uuid primary key default gen_random_uuid(),
  page_id text not null,
  sender_id text not null,
  last_message text,
  detected_language text,
  status text default 'open',
  updated_at timestamptz default now(),
  unique(page_id, sender_id)
);

-- Reply rules
create table reply_rules (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  keyword text not null,
  reply_template text not null
);

-- Settings
create table settings (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  google_sheet_id text,
  welcome_message text,
  handoff_keyword text default 'human',
  notification_email text,
  comment_reply_mode text default 'comment'
);
```

**Step 3: Verify tables exist**

In the Supabase dashboard → **Table Editor** — confirm all 6 tables are listed:
`tenants`, `facebook_pages`, `catalog_cache`, `conversations`, `reply_rules`, `settings`

**Step 4: Insert a test tenant**

```sql
insert into tenants (name, email, plan)
values ('Test Business', 'test@example.com', 'starter')
returning id;
```

Copy the returned UUID — you'll use it in later tasks.

**Step 5: Commit**

```bash
git add -A
git commit -m "docs: note Supabase schema created"
```

---

### Task 3: Webhook endpoint

**Files:**
- Modify: `backend/main.py`
- Create: `tests/test_webhook.py`

**Step 1: Write failing tests**

```python
# tests/test_webhook.py
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from main import app

client = TestClient(app)

VERIFY_TOKEN = "test_verify_token"

def test_webhook_verify_success(monkeypatch):
    monkeypatch.setenv("META_WEBHOOK_VERIFY_TOKEN", VERIFY_TOKEN)
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "abc123"
    })
    assert response.status_code == 200
    assert response.text == "abc123"

def test_webhook_verify_wrong_token(monkeypatch):
    monkeypatch.setenv("META_WEBHOOK_VERIFY_TOKEN", VERIFY_TOKEN)
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "abc123"
    })
    assert response.status_code == 403

def test_webhook_post_returns_200():
    payload = {"object": "page", "entry": []}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_webhook.py -v
```
Expected: FAIL — `/webhook` route not found

**Step 3: Add webhook routes to `backend/main.py`**

```python
from fastapi import FastAPI, Request, Response, HTTPException
from config import META_WEBHOOK_VERIFY_TOKEN

app = FastAPI(title="servis.io backend")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == META_WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    # Events processed here in later tasks
    return {"status": "received"}
```

**Step 4: Run tests**

```bash
pytest tests/test_webhook.py -v
```
Expected: all 3 PASS

**Step 5: Commit**

```bash
git add backend/main.py tests/test_webhook.py
git commit -m "feat: add Facebook webhook verify and receive endpoints"
```

---

### Task 4: Tenant resolution service

**Files:**
- Create: `backend/services/tenant.py`
- Create: `tests/test_tenant.py`

**Step 1: Write `backend/services/tenant.py`**

```python
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

_client = None

def get_supabase():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client

def get_tenant_by_page_id(page_id: str) -> dict | None:
    """Returns facebook_pages row joined with tenant_id, or None if not found."""
    sb = get_supabase()
    result = sb.table("facebook_pages").select("*, tenants(*)").eq("page_id", page_id).single().execute()
    return result.data if result.data else None

def get_catalog(tenant_id: str) -> list[dict]:
    """Returns all available catalog items for a tenant."""
    sb = get_supabase()
    result = sb.table("catalog_cache").select("*").eq("tenant_id", tenant_id).eq("is_available", True).execute()
    return result.data or []

def get_reply_rules(tenant_id: str) -> list[dict]:
    """Returns all keyword reply rules for a tenant."""
    sb = get_supabase()
    result = sb.table("reply_rules").select("*").eq("tenant_id", tenant_id).execute()
    return result.data or []

def get_settings(tenant_id: str) -> dict | None:
    """Returns settings row for a tenant."""
    sb = get_supabase()
    result = sb.table("settings").select("*").eq("tenant_id", tenant_id).single().execute()
    return result.data if result.data else None

def get_or_create_conversation(page_id: str, sender_id: str) -> dict:
    """Returns existing conversation or creates a new one."""
    sb = get_supabase()
    result = sb.table("conversations").select("*").eq("page_id", page_id).eq("sender_id", sender_id).execute()
    if result.data:
        return result.data[0]
    new_conv = sb.table("conversations").insert({
        "page_id": page_id,
        "sender_id": sender_id,
        "status": "open"
    }).execute()
    return new_conv.data[0]

def update_conversation(page_id: str, sender_id: str, updates: dict):
    """Updates conversation fields."""
    sb = get_supabase()
    sb.table("conversations").update(updates).eq("page_id", page_id).eq("sender_id", sender_id).execute()
```

**Step 2: Write `tests/test_tenant.py`**

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from unittest.mock import patch, MagicMock
from services.tenant import get_tenant_by_page_id, get_catalog, get_reply_rules

def make_mock_result(data):
    mock = MagicMock()
    mock.data = data
    return mock

def test_get_tenant_by_page_id_not_found():
    with patch("services.tenant.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.single.return_value \
            .execute.return_value = make_mock_result(None)
        result = get_tenant_by_page_id("nonexistent_page")
        assert result is None

def test_get_catalog_returns_list():
    with patch("services.tenant.get_supabase") as mock_sb:
        mock_sb.return_value.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.execute.return_value = make_mock_result([
                {"name": "Milk Tea", "price": 80, "is_available": True}
            ])
        result = get_catalog("some-tenant-id")
        assert len(result) == 1
        assert result[0]["name"] == "Milk Tea"
```

**Step 3: Run tests**

```bash
pytest tests/test_tenant.py -v
```
Expected: PASS (mocked — no real Supabase calls)

**Step 4: Commit**

```bash
git add backend/services/tenant.py tests/test_tenant.py
git commit -m "feat: add tenant resolution and catalog services"
```

---

### Task 5: Keyword rules matcher

**Files:**
- Create: `backend/services/rules.py`
- Create: `tests/test_rules.py`

**Step 1: Write failing test**

```python
# tests/test_rules.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from services.rules import match_rule

def test_exact_keyword_match():
    rules = [{"keyword": "price", "reply_template": "Our prices start at ₱80."}]
    assert match_rule("what is your price", rules) == "Our prices start at ₱80."

def test_case_insensitive_match():
    rules = [{"keyword": "MENU", "reply_template": "Here is our menu!"}]
    assert match_rule("Can I see the menu?", rules) == "Here is our menu!"

def test_no_match_returns_none():
    rules = [{"keyword": "price", "reply_template": "₱80"}]
    assert match_rule("hello", rules) is None

def test_empty_rules_returns_none():
    assert match_rule("hello", []) is None
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_rules.py -v
```
Expected: FAIL — `services.rules` not found

**Step 3: Write `backend/services/rules.py`**

```python
def match_rule(message: str, rules: list[dict]) -> str | None:
    """Returns reply template if any keyword matches the message, else None."""
    message_lower = message.lower()
    for rule in rules:
        if rule["keyword"].lower() in message_lower:
            return rule["reply_template"]
    return None
```

**Step 4: Run tests**

```bash
pytest tests/test_rules.py -v
```
Expected: all 4 PASS

**Step 5: Commit**

```bash
git add backend/services/rules.py tests/test_rules.py
git commit -m "feat: add keyword rule matcher"
```

---

### Task 6: Gemini reply service

**Files:**
- Create: `backend/services/gemini.py`
- Create: `tests/test_gemini.py`

**Step 1: Write failing test**

```python
# tests/test_gemini.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from unittest.mock import patch, MagicMock
from services.gemini import generate_reply

def test_generate_reply_returns_string():
    catalog = [{"name": "Milk Tea", "price": 80, "description": "Classic milk tea"}]
    with patch("services.gemini.model") as mock_model:
        mock_response = MagicMock()
        mock_response.text = "Kami ay may Milk Tea sa halagang ₱80!"
        mock_model.generate_content.return_value = mock_response
        result = generate_reply("Magkano ang milk tea?", catalog)
        assert isinstance(result, str)
        assert len(result) > 0

def test_generate_reply_includes_catalog_context():
    catalog = [{"name": "Ube Pandesal", "price": 25, "description": "Fresh ube pandesal"}]
    with patch("services.gemini.model") as mock_model:
        mock_response = MagicMock()
        mock_response.text = "We have Ube Pandesal for ₱25!"
        mock_model.generate_content.return_value = mock_response
        result = generate_reply("What do you sell?", catalog)
        mock_model.generate_content.assert_called_once()
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Ube Pandesal" in call_args
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_gemini.py -v
```
Expected: FAIL

**Step 3: Write `backend/services/gemini.py`**

```python
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def build_catalog_text(catalog: list[dict]) -> str:
    if not catalog:
        return "No catalog available."
    lines = []
    for item in catalog:
        price = item.get("discounted_price") or item.get("price", "")
        line = f"- {item['name']}"
        if item.get("description"):
            line += f": {item['description']}"
        if price:
            line += f" (₱{price})"
        lines.append(line)
    return "\n".join(lines)

def generate_reply(message: str, catalog: list[dict]) -> str:
    catalog_text = build_catalog_text(catalog)
    prompt = f"""You are a friendly customer service assistant for a small Filipino business.

Customer message: {message}

Our catalog:
{catalog_text}

Instructions:
- Detect the language of the customer's message (English, Tagalog, Taglish, Bisaya, or other Philippine language)
- Reply in the same language. Default to Taglish if unsure.
- Mention relevant products and prices from the catalog if applicable
- Keep the reply short, friendly, and helpful
- Do not make up products not in the catalog

Reply:"""
    response = model.generate_content(prompt)
    return response.text.strip()
```

**Step 4: Run tests**

```bash
pytest tests/test_gemini.py -v
```
Expected: all 2 PASS

**Step 5: Commit**

```bash
git add backend/services/gemini.py tests/test_gemini.py
git commit -m "feat: add Gemini Flash reply service"
```

---

### Task 7: Meta Graph API sender

**Files:**
- Create: `backend/services/messenger.py`
- Create: `tests/test_messenger.py`

**Step 1: Write failing test**

```python
# tests/test_messenger.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from unittest.mock import patch, MagicMock
from services.messenger import send_dm, send_comment_reply

def test_send_dm_calls_graph_api():
    with patch("services.messenger.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_dm(page_access_token="token123", recipient_id="user456", message="Hello!")
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "graph.facebook.com" in url

def test_send_comment_reply_calls_graph_api():
    with patch("services.messenger.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_comment_reply(page_access_token="token123", comment_id="comment789", message="Thank you!")
        mock_post.assert_called_once()
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_messenger.py -v
```
Expected: FAIL

**Step 3: Write `backend/services/messenger.py`**

```python
import httpx

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

def send_dm(page_access_token: str, recipient_id: str, message: str):
    """Send a direct message to a user via Messenger."""
    url = f"{GRAPH_API_BASE}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "messaging_type": "RESPONSE"
    }
    response = httpx.post(url, json=payload, params={"access_token": page_access_token})
    response.raise_for_status()
    return response.json()

def send_comment_reply(page_access_token: str, comment_id: str, message: str):
    """Reply to a comment on a Facebook post."""
    url = f"{GRAPH_API_BASE}/{comment_id}/comments"
    payload = {"message": message}
    response = httpx.post(url, json=payload, params={"access_token": page_access_token})
    response.raise_for_status()
    return response.json()
```

**Step 4: Run tests**

```bash
pytest tests/test_messenger.py -v
```
Expected: all 2 PASS

**Step 5: Commit**

```bash
git add backend/services/messenger.py tests/test_messenger.py
git commit -m "feat: add Meta Graph API DM and comment reply senders"
```

---

### Task 8: Wire up the reply engine in the webhook

**Files:**
- Modify: `backend/main.py`
- Create: `tests/test_reply_flow.py`

**Step 1: Write failing test**

```python
# tests/test_reply_flow.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

DM_PAYLOAD = {
    "object": "page",
    "entry": [{
        "id": "111",
        "messaging": [{
            "sender": {"id": "user_123"},
            "recipient": {"id": "page_111"},
            "message": {"text": "What's your menu?"}
        }]
    }]
}

def test_dm_event_triggers_reply():
    with patch("main.get_tenant_by_page_id") as mock_tenant, \
         patch("main.get_catalog") as mock_catalog, \
         patch("main.get_reply_rules") as mock_rules, \
         patch("main.get_settings") as mock_settings, \
         patch("main.get_or_create_conversation") as mock_conv, \
         patch("main.update_conversation"), \
         patch("main.generate_reply") as mock_gemini, \
         patch("main.send_dm") as mock_send:

        mock_tenant.return_value = {"tenant_id": "t1", "access_token": "tok", "page_id": "page_111"}
        mock_catalog.return_value = [{"name": "Milk Tea", "price": 80}]
        mock_rules.return_value = []
        mock_settings.return_value = {"welcome_message": None, "handoff_keyword": "human"}
        mock_conv.return_value = {"status": "open", "detected_language": None}
        mock_gemini.return_value = "Meron kaming Milk Tea sa ₱80!"

        response = client.post("/webhook", json=DM_PAYLOAD)
        assert response.status_code == 200
        mock_send.assert_called_once()
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_reply_flow.py -v
```
Expected: FAIL

**Step 3: Rewrite `backend/main.py` with full reply flow**

```python
from fastapi import FastAPI, Request, Response, HTTPException
from config import META_WEBHOOK_VERIFY_TOKEN
from services.tenant import (
    get_tenant_by_page_id, get_catalog, get_reply_rules,
    get_settings, get_or_create_conversation, update_conversation
)
from services.rules import match_rule
from services.gemini import generate_reply
from services.messenger import send_dm, send_comment_reply

app = FastAPI(title="servis.io backend")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == META_WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    if body.get("object") != "page":
        return {"status": "ignored"}

    for entry in body.get("entry", []):
        page_id = entry.get("id")
        page = get_tenant_by_page_id(page_id)
        if not page:
            continue

        tenant_id = page["tenant_id"]
        access_token = page["access_token"]
        catalog = get_catalog(tenant_id)
        rules = get_reply_rules(tenant_id)
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

            # Gemini reply
            reply = generate_reply(message_text, catalog)
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
            reply = match_rule(comment_text, rules) or generate_reply(comment_text, catalog)

            if mode == "dm" and commenter_id:
                send_dm(access_token, commenter_id, reply)
            else:
                send_comment_reply(access_token, comment_id, reply)

    return {"status": "ok"}
```

**Step 4: Run all tests**

```bash
pytest tests/ -v
```
Expected: all tests PASS

**Step 5: Commit**

```bash
git add backend/main.py tests/test_reply_flow.py
git commit -m "feat: wire up full reply engine in webhook handler"
```

---

### Task 9: Google Sheets catalog sync

**Files:**
- Create: `backend/services/sheets.py`
- Create: `tests/test_sheets.py`

**Step 1: Install gspread**

Add to `backend/requirements.txt`:
```
gspread==6.1.2
```

Run:
```bash
pip install gspread==6.1.2
```

**Step 2: Write failing test**

```python
# tests/test_sheets.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
from unittest.mock import patch, MagicMock
from services.sheets import parse_sheet_rows

def test_parse_sheet_rows_valid():
    rows = [
        ["name", "description", "price", "discounted_price", "category", "is_available"],
        ["Milk Tea", "Classic milk tea", "80", "", "drinks", "TRUE"],
        ["Ube Pandesal", "Fresh ube pandesal", "25", "20", "bread", "TRUE"],
    ]
    result = parse_sheet_rows(rows)
    assert len(result) == 2
    assert result[0]["name"] == "Milk Tea"
    assert result[0]["price"] == 80.0
    assert result[0]["discounted_price"] is None
    assert result[1]["discounted_price"] == 20.0

def test_parse_sheet_rows_skips_unavailable():
    rows = [
        ["name", "description", "price", "discounted_price", "category", "is_available"],
        ["Sold Out Item", "", "50", "", "food", "FALSE"],
    ]
    result = parse_sheet_rows(rows)
    assert len(result) == 1
    assert result[0]["is_available"] == False
```

**Step 3: Run to verify they fail**

```bash
pytest tests/test_sheets.py -v
```
Expected: FAIL

**Step 4: Write `backend/services/sheets.py`**

```python
import gspread
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def parse_sheet_rows(rows: list[list]) -> list[dict]:
    """Parse raw Google Sheets rows into catalog dicts. First row is header."""
    if len(rows) < 2:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if not any(row):
            continue
        item = dict(zip(headers, row))
        result.append({
            "name": item.get("name", "").strip(),
            "description": item.get("description", "").strip() or None,
            "price": float(item["price"]) if item.get("price") else None,
            "discounted_price": float(item["discounted_price"]) if item.get("discounted_price") else None,
            "category": item.get("category", "").strip() or None,
            "is_available": item.get("is_available", "TRUE").upper() != "FALSE",
        })
    return result

def sync_catalog_from_sheet(tenant_id: str, sheet_url: str, service_account_json: dict):
    """Fetch Google Sheet and upsert into catalog_cache."""
    gc = gspread.service_account_from_dict(service_account_json)
    sheet = gc.open_by_url(sheet_url).sheet1
    rows = sheet.get_all_values()
    items = parse_sheet_rows(rows)

    sb = get_supabase()
    # Clear existing catalog for tenant
    sb.table("catalog_cache").delete().eq("tenant_id", tenant_id).execute()
    # Insert fresh items
    for item in items:
        item["tenant_id"] = tenant_id
    if items:
        sb.table("catalog_cache").insert(items).execute()
    return len(items)
```

**Step 5: Run tests**

```bash
pytest tests/test_sheets.py -v
```
Expected: all 2 PASS

**Step 6: Add sync endpoint to `backend/main.py`**

```python
@app.post("/sync-catalog")
async def sync_catalog(request: Request):
    body = await request.json()
    tenant_id = body.get("tenant_id")
    sheet_url = body.get("sheet_url")
    service_account = body.get("service_account")
    if not all([tenant_id, sheet_url, service_account]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    from services.sheets import sync_catalog_from_sheet
    count = sync_catalog_from_sheet(tenant_id, sheet_url, service_account)
    return {"synced": count}
```

**Step 7: Run all tests**

```bash
pytest tests/ -v
```
Expected: all PASS

**Step 8: Commit**

```bash
git add backend/services/sheets.py tests/test_sheets.py backend/main.py
git commit -m "feat: add Google Sheets catalog sync"
```

---

### Task 10: Local end-to-end test with ngrok

**Files:** No code changes — this is a manual integration test.

**Step 1: Install ngrok**

Download from ngrok.com (free account). Sign up with `joshnietodc@gmail.com`. Follow the setup instructions to authenticate the CLI.

**Step 2: Start the FastAPI server**

```bash
cd C:/Users/jcndc/github/servis.io/backend
source .venv/Scripts/activate
uvicorn main:app --reload --port 8000
```

**Step 3: In a new terminal, start ngrok**

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL.

**Step 4: Register webhook with Meta**

Go to `developers.facebook.com` → your **servis.io** app → **Messenger** → **Webhooks** → **Add Callback URL**:
- Callback URL: `https://xxxx.ngrok-free.app/webhook`
- Verify token: value of `META_WEBHOOK_VERIFY_TOKEN` from `.env`

Click **Verify and Save**.

**Step 5: Add a test Facebook Page**

In the Meta Developer dashboard → **Messenger** → **Access Tokens** → add your test Facebook Page. Copy the Page Access Token.

**Step 6: Insert test data into Supabase**

Run in Supabase SQL editor (replace values with your actual tenant ID and page ID):

```sql
-- Use the tenant ID from Task 2
insert into facebook_pages (tenant_id, page_id, page_name, access_token, webhook_subscribed)
values ('<your-tenant-id>', '<your-page-id>', 'Test Page', '<your-page-access-token>', true);

insert into settings (tenant_id, welcome_message, handoff_keyword, comment_reply_mode)
values ('<your-tenant-id>', 'Hello! Welcome to our shop. How can we help you? 😊', 'human', 'comment');

insert into catalog_cache (tenant_id, name, description, price, is_available)
values ('<your-tenant-id>', 'Milk Tea', 'Classic milk tea', 80, true);

insert into reply_rules (tenant_id, keyword, reply_template)
values ('<your-tenant-id>', 'location', 'We deliver anywhere in Metro Manila! DM us to order. 🛵');
```

**Step 7: Send a test DM**

Open Facebook and send a DM to your test Page. Verify:
- Welcome message is sent on first contact
- Keyword "location" triggers the template reply
- Other messages get a Gemini-generated reply

**Step 8: Commit any fixes found during testing**

```bash
git add -A
git commit -m "fix: e2e test adjustments"
```

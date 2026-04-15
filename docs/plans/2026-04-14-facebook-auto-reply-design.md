# servis.io — Facebook Auto-Reply Service Design

**Date:** 2026-04-14  
**Status:** Approved, not yet in production  
**Scope:** MVP — Facebook Auto-Reply only (Instagram expansion planned later)

---

## Overview

servis.io is a multi-tenant SaaS that provides automated Facebook Page reply services for small to medium businesses — starting with food businesses, local service providers, and SMEs in the Philippines.

The first service is an **Instant Auto-Reply System** that responds to customer DMs and comments on Facebook Pages using the business's own product/service catalog as a knowledge base.

---

## Architecture

```
[ Facebook ]
     |
     | Webhook Events (DMs, Comments)
     ↓
[ FastAPI Backend ]  ←→  [ Supabase DB ]
     |                        |
     | Identify tenant         |— tenants
     | Load catalog cache      |— facebook_pages
     | Call Claude Haiku       |— catalog_cache
     |                         |— conversations
     ↓                         |— reply_rules
[ Meta Graph API ]             |— settings
     |
     ↓
  Reply sent to customer
     
[ Next.js Dashboard ]  ←→  [ Supabase Auth + DB ]
       (Vercel)
```

---

## Tech Stack

| Component | Tool | Hosting | Cost |
|---|---|---|---|
| Backend API | Python + FastAPI | Railway (free tier) | ~₱0 |
| Frontend Dashboard | Next.js | Vercel (free tier) | ₱0 |
| Database + Auth | Supabase | Supabase (free tier) | ₱0 |
| Catalog source | Google Sheets | Client-managed | ₱0 |
| AI replies | Gemini Flash | Google AI Studio (free tier) | ₱0 |
| Facebook integration | Meta Graph API + Webhooks | Meta (free) | ₱0 |

**Target monthly cost:** ₱0 at MVP scale (Gemini free tier: 1,500 requests/day).

---

## Data Model

```sql
tenants
  id, name, email, plan (starter), created_at

facebook_pages
  id, tenant_id, page_id, page_name, access_token, webhook_subscribed

catalog_cache
  id, tenant_id, name, description, price, discounted_price, category, is_available, synced_at

conversations
  id, page_id, sender_id, last_message, detected_language, status (open/handled/escalated), updated_at

reply_rules
  id, tenant_id, keyword, reply_template

settings
  tenant_id, google_sheet_id, welcome_message, handoff_keyword, notification_email, comment_reply_mode (comment/dm)
```

**Multi-tenancy:** every webhook event is tied to a `page_id` → lookup `facebook_pages` → get `tenant_id` → load that tenant's catalog, rules, and settings.

---

## Catalog via Google Sheets

- Each tenant manages their own Google Sheet (servis.io provides a template)
- Tenant shares the sheet (read-only) with the servis.io service account email
- Tenant pastes the Sheet URL into their dashboard
- Backend syncs the sheet to `catalog_cache` in Supabase on demand ("Sync Now") or hourly
- Replies are generated from the cached data — fast, no Sheets API call per message

**Google Sheet columns:**
`name | description | price | discounted_price | category | is_available`

- `discounted_price` is optional. If filled, AI uses it as the current price in replies.

---

## Reply Flow

```
1. Facebook sends webhook event → FastAPI

2. Identify tenant
   page_id → facebook_pages → tenant_id

3. Check reply_rules (exact keyword match)
   → if match: send template reply immediately (no AI)

4. If no match:
   → load catalog_cache for tenant
   → call Gemini Flash (free tier):
       "Customer said: [message]
        Catalog: [catalog rows]
        Detect the language. Reply in the same language.
        Supported: English, Tagalog, Taglish, Bisaya/Cebuano, other PH languages.
        Default to Taglish if unsure.
        Mention relevant products and prices. Be friendly and helpful."
   → send reply via Meta Graph API

5. If handoff keyword detected (e.g. "human", "agent", "tao"):
   → flag conversation as escalated
   → send handoff message to customer
   → send email notification to business owner

6. Log conversation to Supabase (store detected_language for thread consistency)
```

**First message from new sender:** send `welcome_message` before processing.

**Comment events:** reply as a comment on the post OR send a DM to the commenter — configurable per tenant via `comment_reply_mode`.

---

## Language Detection

Handled entirely by Claude Haiku in the same API call — no extra cost.

Supported languages:
- English
- Tagalog
- Taglish (Tagalog + English mix)
- Bisaya / Cebuano
- Other Philippine languages

Detected language is stored on the `conversations` record so subsequent messages in the same thread use the same language without re-detecting.

---

## Client Onboarding Flow

1. Business owner signs up on servis.io → Supabase Auth
2. Clicks "Connect Facebook Page" → Facebook OAuth flow → Page Access Token + Page ID stored automatically
3. Pastes Google Sheet URL → synced to catalog cache
4. Configures welcome message, keyword rules, handoff settings
5. Goes live — webhook is active

---

## Dashboard (Next.js)

```
Pages
  ├── Connect Facebook Page (OAuth)
  └── View / disconnect connected pages

Catalog
  ├── Paste Google Sheet URL
  ├── Sync Now
  └── Preview cached catalog

Reply Settings
  ├── Welcome message
  ├── Keyword rules (add / edit / delete)
  ├── Handoff keyword + notification email
  └── Comment reply mode (comment reply vs DM)

Conversations
  ├── View recent conversations
  ├── View escalated conversations
  └── Mark as handled
```

---

## Features NOT in MVP

- Instagram integration
- Analytics / reporting
- Post scheduling
- Bulk messaging
- Promo codes or time-based discounts
- Multi-language catalog (catalog is in one language, AI translates replies)
- Mobile app

---

## Meta App Notes

- A Meta Developer App is required (created once by servis.io, not per client)
- Clients authorize the app via OAuth — no manual Page ID entry needed
- Permissions required: `pages_messaging`, `pages_read_engagement`, `pages_manage_metadata`
- **Meta App Review** required for production access — can take 1–3 weeks
- During development, test users can be added manually

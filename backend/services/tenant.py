import functools
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

@functools.lru_cache(maxsize=1)
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def get_tenant_by_page_id(page_id: str):
    result = (get_supabase().table("facebook_pages")
              .select("*, tenants(*)")
              .eq("page_id", page_id)
              .limit(1)
              .execute())
    return result.data[0] if result.data else None

def get_catalog(tenant_id: str) -> list:
    result = (get_supabase().table("catalog_cache")
              .select("*")
              .eq("tenant_id", tenant_id)
              .eq("is_available", True)
              .execute())
    return result.data or []

def get_reply_rules(tenant_id: str) -> list:
    result = (get_supabase().table("reply_rules")
              .select("*")
              .eq("tenant_id", tenant_id)
              .execute())
    return result.data or []

def get_promos(tenant_id: str) -> list:
    result = (get_supabase().table("promos")
              .select("*")
              .eq("tenant_id", tenant_id)
              .eq("is_active", True)
              .execute())
    return result.data or []

def get_settings(tenant_id: str):
    result = (get_supabase().table("settings")
              .select("*")
              .eq("tenant_id", tenant_id)
              .limit(1)
              .execute())
    return result.data[0] if result.data else None

def get_or_create_conversation(page_id: str, sender_id: str) -> dict:
    result = (get_supabase().table("conversations")
              .upsert(
                  {"page_id": page_id, "sender_id": sender_id, "status": "open"},
                  on_conflict="page_id,sender_id",
                  ignore_duplicates=True
              )
              .execute())
    if result.data:
        return result.data[0]
    # Row already existed — fetch it
    existing = (get_supabase().table("conversations")
                .select("*")
                .eq("page_id", page_id)
                .eq("sender_id", sender_id)
                .limit(1)
                .execute())
    return existing.data[0] if existing.data else {}

def update_conversation(page_id: str, sender_id: str, updates: dict) -> dict:
    result = (get_supabase().table("conversations")
              .update(updates)
              .eq("page_id", page_id)
              .eq("sender_id", sender_id)
              .execute())
    if not result.data:
        raise ValueError(f"No conversation found for page_id={page_id}, sender_id={sender_id}")
    return result.data[0]

def append_message(page_id: str, sender_id: str, role: str, text: str):
    """Append a message to the conversation's message_history (keep last 10)."""
    conv = (get_supabase().table("conversations")
            .select("message_history")
            .eq("page_id", page_id)
            .eq("sender_id", sender_id)
            .limit(1)
            .execute())
    history = conv.data[0].get("message_history") or [] if conv.data else []
    history.append({"role": role, "text": text})
    history = history[-10:]  # keep last 10 messages
    get_supabase().table("conversations").update({"message_history": history}).eq("page_id", page_id).eq("sender_id", sender_id).execute()

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

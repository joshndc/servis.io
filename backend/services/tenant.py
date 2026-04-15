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

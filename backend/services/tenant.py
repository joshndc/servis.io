from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

_client = None

def get_supabase():
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client

def get_tenant_by_page_id(page_id: str):
    result = (get_supabase().table("facebook_pages")
              .select("*, tenants(*)")
              .eq("page_id", page_id)
              .single()
              .execute())
    return result.data if result.data else None

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
              .single()
              .execute())
    return result.data if result.data else None

def get_or_create_conversation(page_id: str, sender_id: str) -> dict:
    result = (get_supabase().table("conversations")
              .select("*")
              .eq("page_id", page_id)
              .eq("sender_id", sender_id)
              .execute())
    if result.data:
        return result.data[0]
    new = (get_supabase().table("conversations")
           .insert({"page_id": page_id, "sender_id": sender_id, "status": "open"})
           .execute())
    return new.data[0]

def update_conversation(page_id: str, sender_id: str, updates: dict):
    (get_supabase().table("conversations")
     .update(updates)
     .eq("page_id", page_id)
     .eq("sender_id", sender_id)
     .execute())

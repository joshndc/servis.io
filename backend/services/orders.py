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

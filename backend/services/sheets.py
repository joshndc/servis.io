import gspread
from services.tenant import get_supabase

def parse_sheet_rows(rows: list[list]) -> list[dict]:
    """Parse raw Google Sheets rows into catalog dicts. First row is header."""
    if len(rows) < 2:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if not any(str(cell).strip() for cell in row):
            continue
        item = dict(zip(headers, row))
        disc = item.get("discounted_price", "").strip()
        result.append({
            "name": item.get("name", "").strip(),
            "description": item.get("description", "").strip() or None,
            "price": float(item["price"]) if item.get("price", "").strip() else None,
            "discounted_price": float(disc) if disc else None,
            "category": item.get("category", "").strip() or None,
            "is_available": item.get("is_available", "TRUE").strip().upper() != "FALSE",
        })
    return result

def sync_catalog_from_sheet(tenant_id: str, sheet_url: str, service_account_json: dict) -> int:
    """Fetch Google Sheet and upsert into catalog_cache. Returns count of synced items."""
    gc = gspread.service_account_from_dict(service_account_json)
    sheet = gc.open_by_url(sheet_url).sheet1
    rows = sheet.get_all_values()
    items = parse_sheet_rows(rows)

    sb = get_supabase()
    sb.table("catalog_cache").delete().eq("tenant_id", tenant_id).execute()
    if items:
        for item in items:
            item["tenant_id"] = tenant_id
        sb.table("catalog_cache").insert(items).execute()
    return len(items)

import gspread
from datetime import date
from services.tenant import get_supabase

def _open_spreadsheet(sheet_url: str, service_account_json: dict):
    gc = gspread.service_account_from_dict(service_account_json)
    return gc.open_by_url(sheet_url)

def _parse_products(rows: list[list]) -> list[dict]:
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

def _parse_rules(rows: list[list]) -> list[dict]:
    if len(rows) < 2:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if not any(str(cell).strip() for cell in row):
            continue
        item = dict(zip(headers, row))
        keyword = item.get("keyword", "").strip()
        reply = item.get("reply_template", "").strip()
        if keyword and reply:
            result.append({"keyword": keyword, "reply_template": reply})
    return result

def _parse_promos(rows: list[list]) -> list[dict]:
    if len(rows) < 2:
        return []
    headers = [h.strip().lower() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if not any(str(cell).strip() for cell in row):
            continue
        item = dict(zip(headers, row))
        name = item.get("name", "").strip()
        if not name:
            continue
        promo_price_raw = item.get("promo_price", "").strip()
        valid_until_raw = item.get("valid_until", "").strip()
        result.append({
            "name": name,
            "promo_price": float(promo_price_raw) if promo_price_raw else None,
            "valid_until": valid_until_raw or None,
            "is_active": item.get("is_active", "TRUE").strip().upper() != "FALSE",
        })
    return result

def sync_catalog_from_sheet(tenant_id: str, sheet_url: str, service_account_json: dict) -> dict:
    """Sync Products, Rules, and Promos tabs from Google Sheet. Returns counts per tab."""
    spreadsheet = _open_spreadsheet(sheet_url, service_account_json)
    sb = get_supabase()
    counts = {}

    # --- Products tab ---
    try:
        products_ws = spreadsheet.worksheet("Products")
        products = _parse_products(products_ws.get_all_values())
        if products:
            sb.table("catalog_cache").delete().eq("tenant_id", tenant_id).execute()
            for p in products:
                p["tenant_id"] = tenant_id
            sb.table("catalog_cache").insert(products).execute()
        counts["products"] = len(products)
    except gspread.exceptions.WorksheetNotFound:
        counts["products"] = 0

    # --- Rules tab ---
    try:
        rules_ws = spreadsheet.worksheet("Rules")
        rules = _parse_rules(rules_ws.get_all_values())
        if rules:
            sb.table("reply_rules").delete().eq("tenant_id", tenant_id).execute()
            for r in rules:
                r["tenant_id"] = tenant_id
            sb.table("reply_rules").insert(rules).execute()
        counts["rules"] = len(rules)
    except gspread.exceptions.WorksheetNotFound:
        counts["rules"] = 0

    # --- Promos tab ---
    try:
        promos_ws = spreadsheet.worksheet("Promos")
        promos = _parse_promos(promos_ws.get_all_values())
        if promos:
            sb.table("promos").delete().eq("tenant_id", tenant_id).execute()
            for p in promos:
                p["tenant_id"] = tenant_id
            sb.table("promos").insert(promos).execute()
        counts["promos"] = len(promos)
    except gspread.exceptions.WorksheetNotFound:
        counts["promos"] = 0

    return counts

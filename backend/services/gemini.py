import httpx
import logging
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-3-haiku-20240307"

def build_catalog_text(catalog: list[dict]) -> str:
    if not catalog:
        return "No catalog available."
    lines = []
    for item in catalog:
        price = item["discounted_price"] if item.get("discounted_price") is not None else item.get("price")
        line = f"- {item['name']}"
        if item.get("description"):
            line += f": {item['description']}"
        if price is not None:
            line += f" (₱{price})"
        lines.append(line)
    return "\n".join(lines)

def build_promos_text(promos: list[dict]) -> str:
    if not promos:
        return ""
    lines = []
    for p in promos:
        line = f"- {p['name']}: ₱{p['promo_price']}"
        if p.get("valid_until"):
            line += f" (valid until {p['valid_until']})"
        lines.append(line)
    return "\n".join(lines)

def build_history_text(history: list[dict]) -> str:
    if not history:
        return ""
    lines = []
    for msg in history:
        role = "Customer" if msg.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {msg.get('text', '')}")
    return "\n".join(lines)

def generate_reply(message: str, catalog: list[dict], promos: list[dict] = None, history: list[dict] = None) -> str:
    catalog_text = build_catalog_text(catalog)
    promos_text = build_promos_text(promos or [])
    promo_section = f"\nActive promos:\n{promos_text}" if promos_text else ""
    history_text = build_history_text(history or [])
    history_section = f"\nConversation so far:\n{history_text}\n" if history_text else ""
    system = f"""You are a friendly customer service assistant for a small Filipino business.

Catalog:
{catalog_text}{promo_section}

Rules:
- Reply in the same language as the customer (English, Tagalog, Taglish, Bisaya, or other PH language). Default to Taglish if unsure.
- Use conversation history for context and consistency.
- Mention relevant products and prices. Highlight active promos when relevant.
- Keep replies short, friendly, and helpful.
- Never make up products not in the catalog.
- Output ONLY the reply to the customer. No labels, no explanations."""

    history_messages = []
    for msg in (history or []):
        role = "user" if msg.get("role") == "user" else "assistant"
        history_messages.append({"role": role, "content": msg.get("text", "")})

    messages = history_messages + [{"role": "user", "content": message}]

    response = httpx.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 512,
            "system": system,
            "messages": messages,
        },
        timeout=30,
    )
    if not response.is_success:
        logger.error(f"Anthropic API error {response.status_code}: {response.text}")
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"].strip()

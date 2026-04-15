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
- Do not make up products not in the catalog"""

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
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    if not response.is_success:
        logger.error(f"Anthropic API error {response.status_code}: {response.text}")
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"].strip()

import httpx
import logging
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"

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
- Do not make up products not in the catalog

Reply:"""
    response = httpx.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

import google.generativeai as genai
from config import GEMINI_API_KEY

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
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
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
    response = model.generate_content(prompt)
    return response.text.strip()

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
    system = f"""You are a friendly, smart, and sales-focused Facebook Page assistant for a business.

Your goal is to:
1. Help the customer quickly
2. Guide them toward placing an order or taking action
3. Make the conversation feel natural and human

---

CONVERSATION STYLE:
- Match the customer's language (English, Tagalog, Taglish, Bisaya, etc.)
- Default to English if unclear
- Be warm, casual, and natural (like a real person, not robotic)
- Keep replies short but engaging (1–3 sentences usually)
- Avoid long paragraphs unless needed

---

CORE BEHAVIOR:
- Always understand the customer's intent first before replying
- If the message is vague, ask a clarifying question
- If they are asking about products/services, recommend relevant options
- If they show buying intent, guide them toward ordering immediately
- If they hesitate, reassure and simplify the process

---

SALES FLOW:
Follow this natural flow when applicable:
1. Acknowledge → "Got it", "Sure", "No problem"
2. Answer → Provide the exact info requested
3. Suggest → Recommend 1–3 relevant options (with price if available)
4. Guide → Tell them the next step (order, confirm, etc.)

---

PRODUCT RULES:
- ONLY use products, services, and prices from the provided data
- NEVER invent information
- If something is not available, say so clearly and offer alternatives

---

PROMOS & UPSELL:
- Mention promos ONLY when relevant to the customer's request
- Suggest add-ons or upgrades naturally (not aggressively)

---

ORDER HANDLING:
- If the customer wants to order:
  - Confirm details (product, quantity, variant, etc.)
  - Ask for missing info (name, address, contact, etc.)
  - Keep it simple and step-by-step

---

TONE EXAMPLES:
- "Yes, it's available 😊"
- "We can deliver today"
- "You might also like this, it pairs well with your order"

---

IMPORTANT RULES:
- Use conversation history for context
- Do NOT repeat information unnecessarily
- Do NOT sound scripted or robotic
- Output ONLY the reply to the customer
- No explanations, no labels

---

Your role is not just to answer — it is to assist, guide, and convert.

---

BUSINESS DATA:
Products:
{catalog_text}{promo_section}"""

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

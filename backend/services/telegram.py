import logging
import httpx
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: str, text: str) -> dict:
    """Send a plain text message to a Telegram chat."""
    response = httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    )
    if not response.is_success:
        logger.error(f"Telegram sendMessage failed: {response.text}")
    try:
        return response.json()
    except Exception:
        return {}


def send_order_notification(chat_id: str, order: dict) -> dict:
    """Send new order notification with Approve/Deny inline buttons."""
    order_id = order.get("id", "")
    short_id = str(order_id)[:8]  # first 8 chars for display

    items_text = "\n".join(
        f"   {i.get('qty', 1)}x {i.get('name', '')} (₱{i.get('price', 0)})"
        for i in (order.get("items") or [])
    )

    text = (
        f"🛒 New Order #{short_id}\n\n"
        f"👤 {order.get('sender_name', 'Unknown')}\n"
        f"📞 {order.get('contact_number', '-')}\n"
        f"📦 Items:\n{items_text}\n"
        f"💰 Total: ₱{order.get('total_amount', 0)}\n"
    )
    if order.get("pickup_time"):
        text += f"🕒 Pickup: {order['pickup_time']}\n"
    if order.get("notes"):
        text += f"📝 {order['notes']}\n"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve:{order_id}"},
            {"text": "❌ Deny", "callback_data": f"deny:{order_id}"},
        ]]
    }

    response = httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text, "reply_markup": keyboard},
        timeout=10,
    )
    if not response.is_success:
        logger.error(f"Telegram order notification failed: {response.text}")
    try:
        return response.json()
    except Exception:
        return {}


def edit_message_text(chat_id: str, message_id: int, text: str) -> dict:
    """Edit an existing message (used after approve/deny to update notification)."""
    response = httpx.post(
        f"{TELEGRAM_API}/editMessageText",
        json={"chat_id": chat_id, "message_id": message_id, "text": text},
        timeout=10,
    )
    if not response.is_success:
        logger.error(f"Telegram editMessageText failed: {response.text}")
    try:
        return response.json()
    except Exception:
        return {}


def answer_callback_query(callback_query_id: str, text: str) -> dict:
    """Acknowledge a button tap (shows popup on phone)."""
    response = httpx.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": text},
        timeout=10,
    )
    if not response.is_success:
        logger.error(f"Telegram answerCallbackQuery failed: {response.text}")
    try:
        return response.json()
    except Exception:
        return {}

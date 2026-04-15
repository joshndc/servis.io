import httpx

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

def send_dm(page_access_token: str, recipient_id: str, message: str) -> dict:
    """Send a direct message to a user via Messenger."""
    url = f"{GRAPH_API_BASE}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message},
        "messaging_type": "RESPONSE",
    }
    response = httpx.post(
        url,
        json=payload,
        params={"access_token": page_access_token},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def send_comment_reply(page_access_token: str, comment_id: str, message: str) -> dict:
    """Reply to a comment on a Facebook post."""
    url = f"{GRAPH_API_BASE}/{comment_id}/comments"
    response = httpx.post(
        url,
        json={"message": message},
        params={"access_token": page_access_token},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

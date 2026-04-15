from fastapi.testclient import TestClient
import os
os.environ.setdefault("META_WEBHOOK_VERIFY_TOKEN", "test_verify_token")
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("META_APP_SECRET", "fake-secret")
os.environ.setdefault("GEMINI_API_KEY", "fake-gemini-key")

import main
from main import app
import config

client = TestClient(app)


def test_webhook_verify_success():
    token = config.META_WEBHOOK_VERIFY_TOKEN
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": token,
        "hub.challenge": "abc123"
    })
    assert response.status_code == 200
    assert response.text == "abc123"

def test_webhook_verify_wrong_token():
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "abc123"
    })
    assert response.status_code == 403

def test_webhook_post_returns_200():
    payload = {"object": "page", "entry": []}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200

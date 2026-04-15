import config  # validates all env vars at startup
from fastapi import FastAPI, Request, Response, HTTPException, Query
from typing import Optional
from config import META_WEBHOOK_VERIFY_TOKEN

app = FastAPI(title="servis.io backend")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/webhook")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == META_WEBHOOK_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    # Reply logic wired in Task 8
    return {"status": "received"}

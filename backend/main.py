import config  # validates all env vars at startup
from fastapi import FastAPI, Request, Response, HTTPException
from config import META_WEBHOOK_VERIFY_TOKEN

app = FastAPI(title="servis.io backend")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == META_WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    # Full reply logic wired in Task 8
    return {"status": "received"}

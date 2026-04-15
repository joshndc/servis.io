from fastapi import FastAPI

app = FastAPI(title="servis.io backend")

@app.get("/health")
def health():
    return {"status": "ok"}

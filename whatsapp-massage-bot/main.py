from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
import os
from app.adapters.database import init_db
from app.application.booking_service import handle_incoming_message

app = FastAPI(title="WhatsApp Holistic Clinic Bot", version="1.0.0")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "clinic_secure_token_123")

@app.on_event("startup")
def startup_event():
    init_db()
    print("[INFO] SQLite database initialized for WhatsApp Massage Bot.")

@app.get("/")
def health_check():
    return {"status": "online", "service": "WhatsApp Massage Bot API"}

@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """WhatsApp Webhook verification endpoint required by Meta."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("[INFO] Webhook verified successfully by Meta.")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receives incoming messages from WhatsApp Cloud API."""
    body = await request.json()

    try:
        entry = body.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for c in changes:
                value = c.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    phone_number = msg.get("from")  # Sender phone
                    msg_type = msg.get("type")

                    if msg_type == "text":
                        incoming_text = msg.get("text", {}).get("body", "")
                        print(f"[INCOMING WHATSAPP] From: {phone_number} | Text: {incoming_text}")
                        handle_incoming_message(phone_number, incoming_text)

        return JSONResponse(content={"status": "received"}, status_code=200)
    except Exception as ex:
        print(f"[ERROR] Error processing webhook: {ex}")
        return JSONResponse(content={"status": "error", "detail": str(ex)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

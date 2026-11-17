from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
import os
from app.adapters.database import init_db, get_connection
from app.application.booking_service import handle_incoming_message
from app.application.reminder_service import dispatch_pending_reminders

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

# =============================================================================
# Admin & Dashboard API Endpoints
# =============================================================================

@app.get("/api/appointments")
def get_appointments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.phone_number, a.client_name, a.service_id, s.name as service_name,
               s.price_mxn, s.duration_mins, a.appointment_time, a.status, a.created_at, a.reminder_sent
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        ORDER BY a.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.patch("/api/appointments/{app_id}/status")
async def update_appointment_status(app_id: int, request: Request):
    body = await request.json()
    new_status = body.get("status")
    if new_status not in ["CONFIRMED", "COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, app_id))
    conn.commit()
    conn.close()
    return {"status": "success", "updated_id": app_id, "new_status": new_status}

@app.get("/api/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM appointments")
    total_appts = cursor.fetchone()["total"]

    cursor.execute("SELECT SUM(s.price_mxn) as revenue FROM appointments a JOIN services s ON a.service_id = s.id WHERE a.status != 'CANCELLED'")
    revenue = cursor.fetchone()["revenue"] or 0.0

    cursor.execute("SELECT status, COUNT(*) as count FROM appointments GROUP BY status")
    by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

    conn.close()
    return {
        "total_appointments": total_appts,
        "estimated_revenue_mxn": revenue,
        "by_status": by_status
    }

@app.post("/api/reminders/dispatch")
def trigger_reminders():
    """Triggers the automated WhatsApp reminder dispatch for confirmed appointments."""
    result = dispatch_pending_reminders()
    return {"status": "success", **result}

@app.get("/admin", response_class=HTMLResponse)
def serve_admin_panel():
    html_path = os.path.join(os.path.dirname(__file__), "admin", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h3>Admin panel HTML not found. Please check whatsapp-massage-bot/admin/index.html</h3>", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

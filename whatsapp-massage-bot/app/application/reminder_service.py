from app.adapters.database import get_connection, get_service
from app.adapters.whatsapp_client import send_whatsapp_message

def dispatch_pending_reminders():
    """Finds confirmed appointments without a reminder sent and dispatches WhatsApp reminders."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.phone_number, a.client_name, a.service_id, a.appointment_time, a.status
        FROM appointments a
        WHERE a.status = 'CONFIRMED' AND a.reminder_sent = 0
    """)
    rows = cursor.fetchall()

    dispatched_count = 0
    reminders_log = []

    for row in rows:
        app_dict = dict(row)
        svc = get_service(app_dict["service_id"])
        svc_name = svc.name if svc else "Masaje Holístico"

        msg = f"🌿 *Recordatorio de Cita — Sintonía Zen* 🌿\n\n"
        msg += f"¡Hola *{app_dict['client_name']}*! Te recordamos tu cita próxima:\n\n"
        msg += f"💆 *Servicio:* {svc_name}\n"
        msg += f"📅 *Fecha/Hora:* {app_dict['appointment_time']}\n\n"
        msg += "📍 Te esperamos en nuestra clínica. Si necesitas reagendar o cancelar, por favor respóndenos a este mensaje. ¡Nos vemos pronto! ✨"

        # Send WhatsApp message
        result = send_whatsapp_message(app_dict["phone_number"], msg)

        # Mark reminder as sent
        cursor.execute("UPDATE appointments SET reminder_sent = 1 WHERE id = ?", (app_dict["id"],))
        conn.commit()

        dispatched_count += 1
        reminders_log.append({
            "appointment_id": app_dict["id"],
            "client_name": app_dict["client_name"],
            "phone": app_dict["phone_number"],
            "status": "sent"
        })

    conn.close()
    return {
        "dispatched_count": dispatched_count,
        "reminders": reminders_log
    }

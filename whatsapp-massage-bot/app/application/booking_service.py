from app.adapters.database import (
    get_session, save_session, get_all_services, get_service, save_appointment
)
from app.domain.models import Appointment
from app.adapters.whatsapp_client import send_whatsapp_message

def handle_incoming_message(phone_number: str, incoming_text: str):
    text = incoming_text.strip().lower()
    session = get_session(phone_number)

    # Global commands
    if text in ["menu", "hola", "inicio", "hi", "start"]:
        session.current_state = "MENU"
        session.selected_service = None
        session.selected_datetime = None
        session.client_name = None
        save_session(session)
        send_menu(phone_number)
        return

    if text in ["cancelar", "salir"]:
        session.current_state = "MENU"
        session.selected_service = None
        session.selected_datetime = None
        session.client_name = None
        save_session(session)
        send_whatsapp_message(phone_number, "❌ Operación cancelada. Escribe *MENU* para volver al inicio.")
        return

    # State Machine
    if session.current_state == "MENU" or session.current_state == "AWAITING_SERVICE":
        handle_service_selection(phone_number, text, session)
    elif session.current_state == "AWAITING_DATE":
        handle_date_selection(phone_number, incoming_text.strip(), session)
    elif session.current_state == "AWAITING_NAME":
        handle_name_entry(phone_number, incoming_text.strip(), session)
    else:
        # Default fallback
        session.current_state = "MENU"
        save_session(session)
        send_menu(phone_number)

def send_menu(phone_number: str):
    services = get_all_services()
    msg = "🌿 *Clinica de Masajes Holisticos 'Sintonia Zen'* 🌿\n\n"
    msg += "¡Hola! Bienvenido/a. ¿En qué podemos ayudarte hoy?\n\n"
    msg += "Por favor, *responde con el número* de la opción deseada:\n\n"

    for idx, svc in enumerate(services, 1):
        msg += f"*{idx}*. {svc.name}\n"
        msg += f"   ⏱️ {svc.duration_mins} mins | 💲 ${svc.price_mxn:.0f} MXN\n"
        msg += f"   _{svc.description}_\n\n"

    msg += "ℹ️ Responde con el número (ej. *1*, *2*, etc.) para agendar tu cita."
    send_whatsapp_message(phone_number, msg)

def handle_service_selection(phone_number: str, text: str, session):
    services = get_all_services()
    try:
        choice = int(text)
        if 1 <= choice <= len(services):
            selected = services[choice - 1]
            session.selected_service = selected.id
            session.current_state = "AWAITING_DATE"
            save_session(session)

            msg = f"✅ Has elegido: *{selected.name}* (${selected.price_mxn:.0f} MXN).\n\n"
            msg += "📅 Por favor, indícanos la *fecha y hora* deseada para tu cita\n"
            msg += "(Ejemplo: _Mañana a las 5pm_ o _25 de Noviembre 10:00 AM_):"
            send_whatsapp_message(phone_number, msg)
        else:
            send_whatsapp_message(phone_number, "⚠️ Opción inválida. Por favor responde con un número del 1 al 4 del menú.")
    except ValueError:
        send_whatsapp_message(phone_number, "⚠️ Por favor ingresa el número correspondiente al servicio deseado (ej. 1, 2, 3...).")

def handle_date_selection(phone_number: str, text: str, session):
    session.selected_datetime = text
    session.current_state = "AWAITING_NAME"
    save_session(session)

    msg = f"📅 Fecha seleccionada: _{text}_\n\n"
    msg += "👤 Para finalizar, ¿cuál es tu *nombre completo*?"
    send_whatsapp_message(phone_number, msg)

def handle_name_entry(phone_number: str, text: str, session):
    session.client_name = text_capitalize(text)
    session.current_state = "CONFIRMED"

    # Save appointment in DB
    svc = get_service(session.selected_service)
    appointment = Appointment(
        id=None,
        phone_number=phone_number,
        client_name=session.client_name,
        service_id=session.selected_service,
        appointment_time=session.selected_datetime,
        status="CONFIRMED"
    )
    app_id = save_appointment(appointment)
    save_session(session)

    msg = f"🎉 *¡Cita Confirmada con Éxito!* (Folio #{app_id})\n\n"
    msg += f"👤 *Cliente:* {session.client_name}\n"
    msg += f"💆 *Servicio:* {svc.name}\n"
    msg += f"⏱️ *Duración:* {svc.duration_mins} mins\n"
    msg += f"💲 *Inversión:* ${svc.price_mxn:.0f} MXN\n"
    msg += f"📅 *Fecha/Hora:* {session.selected_datetime}\n\n"
    msg += "📍 Te esperamos en nuestra clínica. Te enviaremos un recordatorio 2 horas antes.\n\n"
    msg += "Escribe *MENU* si deseas agendar otra cita."

    send_whatsapp_message(phone_number, msg)

def text_capitalize(text: str) -> str:
    return " ".join([word.capitalize() for word in text.split()])

import os
import pytest
from app.adapters.database import init_db, get_session, get_all_services
from app.application.booking_service import handle_incoming_message, text_capitalize

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

def test_text_capitalize():
    assert text_capitalize("juan perez") == "Juan Perez"

def test_services_seeded():
    services = get_all_services()
    assert len(services) >= 4
    assert services[0].name == "Masaje Relajante / Sueco"

def test_bot_state_machine_flow():
    phone = "525512345678"

    # 1. Send 'hola' -> should trigger menu
    handle_incoming_message(phone, "hola")
    session = get_session(phone)
    assert session.current_state in ["MENU", "AWAITING_SERVICE"]

    # 2. Select service '1'
    handle_incoming_message(phone, "1")
    session = get_session(phone)
    assert session.selected_service == "s1"
    assert session.current_state == "AWAITING_DATE"

    # 3. Select date 'Mañana a las 4pm'
    handle_incoming_message(phone, "Mañana a las 4pm")
    session = get_session(phone)
    assert session.selected_datetime == "Mañana a las 4pm"
    assert session.current_state == "AWAITING_NAME"

    # 4. Enter name 'Carlos Gomez'
    handle_incoming_message(phone, "carlos gomez")
    session = get_session(phone)
    assert session.client_name == "Carlos Gomez"
    assert session.current_state == "CONFIRMED"

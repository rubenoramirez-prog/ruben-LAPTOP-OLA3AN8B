import pytest
from fastapi.testclient import TestClient
from main import app
from app.adapters.database import init_db, save_appointment
from app.domain.models import Appointment
from app.application.reminder_service import dispatch_pending_reminders

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_reminder_service_dispatch():
    # Insert a test confirmed appointment
    app_obj = Appointment(
        id=None,
        phone_number="525500112233",
        client_name="Test Reminders",
        service_id="s1",
        appointment_time="Mañana a las 10am",
        status="CONFIRMED"
    )
    save_appointment(app_obj)

    # Dispatch reminders
    result = dispatch_pending_reminders()
    assert result["dispatched_count"] >= 1

    # Dispatch again -> should be 0 because reminder_sent is now 1
    result_second = dispatch_pending_reminders()
    assert result_second["dispatched_count"] == 0

def test_reminder_api_endpoint():
    response = client.post("/api/reminders/dispatch")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "dispatched_count" in data

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "service": "WhatsApp Massage Bot API"}

def test_webhook_verification():
    # Meta webhook verification GET request
    response = client.get("/webhook?hub.mode=subscribe&hub.verify_token=clinic_secure_token_123&hub.challenge=1158201443")
    assert response.status_code == 200
    assert response.text == "1158201443"

def test_admin_endpoints():
    # Test GET stats
    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert "total_appointments" in data
    assert "estimated_revenue_mxn" in data

    # Test GET appointments
    appts_res = client.get("/api/appointments")
    assert appts_res.status_code == 200
    assert isinstance(appts_res.json(), list)

    # Test serve admin HTML panel
    admin_res = client.get("/admin")
    assert admin_res.status_code == 200
    assert "Sintonía Zen" in admin_res.text

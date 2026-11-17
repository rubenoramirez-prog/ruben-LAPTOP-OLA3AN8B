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

def test_webhook_incoming_message():
    # Simulate incoming WhatsApp message JSON payload
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15555555555",
                                "phone_number_id": "100000000000000"
                            },
                            "contacts": [{"profile": {"name": "Cliente Test"}, "wa_id": "525599887766"}],
                            "messages": [
                                {
                                    "from": "525599887766",
                                    "id": "wamid.HBgL...",
                                    "timestamp": "1600000000",
                                    "text": {"body": "menu"},
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "received"}

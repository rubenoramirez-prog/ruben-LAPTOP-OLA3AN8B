import requests
import json

BASE_URL = "http://localhost:8000"

def simulate_message(phone_number: str, text: str):
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
                            "contacts": [{"profile": {"name": "Cliente Prueba"}, "wa_id": phone_number}],
                            "messages": [
                                {
                                    "from": phone_number,
                                    "id": "wamid.SIMULATED...",
                                    "timestamp": "1600000000",
                                    "text": {"body": text},
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

    print(f"\n[SIMULATION] Sending message from {phone_number}: '{text}'")
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.json()}")

if __name__ == "__main__":
    phone = "525599887766"

    print("=== Simulando Flujo Completo del Bot de WhatsApp ===")

    # 1. Enviar 'hola' (Menú)
    simulate_message(phone, "hola")

    # 2. Seleccionar servicio '2' (Masaje Descontracturante)
    simulate_message(phone, "2")

    # 3. Seleccionar fecha 'Viernes a las 6pm'
    simulate_message(phone, "Viernes a las 6pm")

    # 4. Enviar nombre 'Sofía Ramírez'
    simulate_message(phone, "Sofía Ramírez")

    print("\n✅ ¡Simulación completa! Revisa el panel de administración en http://localhost:8000/admin para ver la cita registrada.")

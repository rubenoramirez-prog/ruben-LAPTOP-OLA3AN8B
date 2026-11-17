import os
import requests

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "EAA_DUMMY_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "100000000000000")
VERSION = "v18.0"

def send_whatsapp_message(to_phone: str, message: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message},
    }

    # In development or testing without token, log instead of failing
    if WHATSAPP_TOKEN == "EAA_DUMMY_TOKEN":
        print(f"[MOCK WHATSAPP SEND] To: {to_phone} | Message:\n{message}")
        return {"status": "mocked", "to": to_phone}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Failed to send WhatsApp message: {e}")
        return {"status": "error", "message": str(e)}

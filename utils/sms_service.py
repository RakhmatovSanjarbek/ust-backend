import os

import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv('SMS_BASE_URL')
TOKEN = os.getenv('SMS_TOKEN')

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def send_sms(phone, message):
    print("SMS yuborilmoqda:", phone, message)

    response = requests.post(
        f"{BASE_URL}/send_sms.php",
        headers=headers,
        json={
            "phone": phone,
            "message": message
        }
    )

    return response.json()

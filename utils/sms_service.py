import requests

BASE_URL = "https://devsms.uz/api"
TOKEN = "6d4dd4d9cf0e17428bce7fce0f5fca71786e42865baf6e38e67e846d61c25f7a"

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

    print("SMS javobi:", response.text)

    return response.json()
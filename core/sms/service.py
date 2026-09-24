import requests
import os
from dotenv import load_dotenv

load_dotenv()

class SMSClient:
    def __init__(self):
        self.base_url = "https://smsvas.com/bulk/public/index.php/api/v1"
        self.user = os.getenv('SMS_USER')
        self.password = os.getenv('SMS_PASSWORD')
        self.sender_id = os.getenv('SMS_SENDER_ID')

    def make_request(self, endpoint, data):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            print(f"✅ {url} → OK")
            return response.text
        except requests.RequestException as e:
            print(f"❌ {url} → {e}")
            if e.response is not None:
                print("↪️ Détails :", e.response.text)
            return None

    def send_sms(self, message, mobile_number):
        endpoint = "/sendsms"
        payload = {
            "user": self.user,
            "password": self.password,
            "senderid": self.sender_id,
            "sms": message,
            "mobiles": mobile_number
        }
        return self.make_request(endpoint, payload)

    def send_sms_to_single_recipient(self, message, receiver_phone):
        return self.send_sms(message, receiver_phone)

# Example usage:
# sms_client = SMSClient()
# response = sms_client.send_sms_to_single_recipient("Bonjour, ceci est un test depuis mon script Python.", "237672269508")
# print("Réponse:", response)=
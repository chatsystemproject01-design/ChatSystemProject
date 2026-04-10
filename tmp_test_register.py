import requests
import json

URL = "http://localhost:5000/api/v1/auth/register"
payload = {
    "email": "finaltest@example.com",
    "password": "Password123!",
    "fullName": "Real Test",
    "phone": "0999888777"
}

headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(URL, data=json.dumps(payload), headers=headers)
    print("STATUS:", response.status_code)
    print("RESPONSE:", json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)

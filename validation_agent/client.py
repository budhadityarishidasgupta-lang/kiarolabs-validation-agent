import requests
from validation_agent.config import BASE_URL

class APIClient:
    def __init__(self):
        self.token = None

    def login(self, email, password):
        res = requests.post(
            f"{BASE_URL}/login",
            data={
                "username": email,
                "password": password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        res.raise_for_status()
        self.token = res.json()["access_token"]

    def get(self, path):
        res = requests.get(
            f"{BASE_URL}{path}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
        return res

    def post(self, path, data=None):
        res = requests.post(
            f"{BASE_URL}{path}",
            json=data or {},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
        return res

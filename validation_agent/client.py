import requests
from validation_agent.config import BASE_URL


class APIClient:
    def __init__(self):
        self.token = None

    def login_response(self, email, password):
        return requests.post(
            f"{BASE_URL}/login",
            data={
                "username": email,
                "password": password,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    def login(self, email, password):
        res = self.login_response(email, password)
        res.raise_for_status()
        self.token = res.json()["access_token"]

    def _auth_headers(self, token=True):
        if token is None:
            return {}

        bearer = self.token if token is True else token
        return {"Authorization": f"Bearer {bearer}"}

    def get(self, path, token=True):
        res = requests.get(
            f"{BASE_URL}{path}",
            headers=self._auth_headers(token),
        )
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
        return res

    def post(self, path, data=None, token=True):
        res = requests.post(
            f"{BASE_URL}{path}",
            json=data or {},
            headers=self._auth_headers(token),
        )
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
        return res

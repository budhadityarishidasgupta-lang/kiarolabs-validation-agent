import requests
from requests.exceptions import ReadTimeout

from validation_agent.config import BASE_URL, REQUEST_TIMEOUT_SECONDS


def _safe_print(label, value):
    text = str(value).encode("ascii", errors="backslashreplace").decode("ascii")
    print(label, text)


class APIClient:
    def __init__(self):
        self.token = None

    def warm_up(self):
        for path in ("/docs", "/health"):
            try:
                res = requests.get(
                    f"{BASE_URL}{path}",
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                print("WARMUP STATUS:", res.status_code, path)
                return res
            except ReadTimeout:
                print("WARMUP TIMEOUT:", path)
            except Exception as exc:
                print("WARMUP SKIP:", path, type(exc).__name__)
        return None

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
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def login(self, email, password):
        last_exc = None
        for attempt in range(2):
            try:
                res = self.login_response(email, password)
                res.raise_for_status()
                self.token = res.json()["access_token"]
                return
            except ReadTimeout as exc:
                last_exc = exc
                if attempt == 0:
                    print("LOGIN TIMEOUT: retrying once after timeout")
                    continue
                raise AssertionError("Backend timeout after warm-up/retry") from exc

        if last_exc is not None:
            raise AssertionError("Backend timeout after warm-up/retry") from last_exc

        res.raise_for_status()

    def _auth_headers(self, token=True):
        if token is None:
            return {}

        bearer = self.token if token is True else token
        return {"Authorization": f"Bearer {bearer}"}

    def get(self, path, token=True):
        res = requests.get(
            f"{BASE_URL}{path}",
            headers=self._auth_headers(token),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        print("STATUS:", res.status_code)
        _safe_print("TEXT:", res.text)
        return res

    def post(self, path, data=None, token=True):
        res = requests.post(
            f"{BASE_URL}{path}",
            json=data or {},
            headers=self._auth_headers(token),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        print("STATUS:", res.status_code)
        _safe_print("TEXT:", res.text)
        return res

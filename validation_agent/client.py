from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class ValidationHttpError(RuntimeError):
    pass


@dataclass(frozen=True)
class LoginContext:
    token: str
    email: str
    role: str


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def close(self) -> None:
        self.session.close()

    def _request(self, method: str, path: str, *, token: str | None = None, **kwargs: Any) -> requests.Response:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", "application/json")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=headers,
            timeout=self.timeout_seconds,
            **kwargs,
        )
        return response

    def request_json(self, method: str, path: str, *, token: str | None = None, expected_status: int = 200, **kwargs: Any) -> Any:
        response = self._request(method, path, token=token, **kwargs)
        if response.status_code != expected_status:
            raise ValidationHttpError(
                f"{method} {path} returned {response.status_code}: {response.text[:500]}"
            )
        try:
            return response.json()
        except Exception as exc:
            raise ValidationHttpError(f"{method} {path} did not return JSON: {response.text[:500]}") from exc

    def login(self, email: str, password: str) -> LoginContext:
        payload = self.request_json(
            "POST",
            "/login",
            json={"email": email, "password": password},
        )
        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise ValidationHttpError("Login succeeded without access_token")
        return LoginContext(
            token=token,
            email=str(payload.get("email") or email),
            role=str(payload.get("role") or ""),
        )


# Backward compatibility for legacy imports that used APIClient.
APIClient = ApiClient

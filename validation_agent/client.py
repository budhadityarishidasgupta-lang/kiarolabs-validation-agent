from __future__ import annotations

import time
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


@dataclass
class RequestOutcome:
    method: str
    path: str
    retries: int
    final_outcome: str
    duration_seconds: float
    status_code: int | None = None
    error: str = ""


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        *,
        max_retries: int = 4,
        initial_backoff_seconds: float = 2.0,
        backoff_multiplier: float = 2.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, int(max_retries))
        self.initial_backoff_seconds = max(0.0, float(initial_backoff_seconds))
        self.backoff_multiplier = max(1.0, float(backoff_multiplier))
        self.session = requests.Session()
        self.request_outcomes: list[RequestOutcome] = []

    def close(self) -> None:
        self.session.close()

    def _sleep_backoff(self, retry_index: int) -> None:
        delay = self.initial_backoff_seconds * (self.backoff_multiplier ** max(0, retry_index - 1))
        if delay > 0:
            time.sleep(delay)

    def _record(self, *, method: str, path: str, retries: int, outcome: str, started_at: float, status_code: int | None = None, error: str = "") -> None:
        self.request_outcomes.append(
            RequestOutcome(
                method=method,
                path=path,
                retries=retries,
                final_outcome=outcome,
                duration_seconds=round(time.perf_counter() - started_at, 4),
                status_code=status_code,
                error=error[:500],
            )
        )

    def _request(self, method: str, path: str, *, token: str | None = None, **kwargs: Any) -> requests.Response:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", "application/json")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        started = time.perf_counter()
        last_error = ""
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=f"{self.base_url}{path}",
                    headers=headers,
                    timeout=self.timeout_seconds,
                    **kwargs,
                )
                if response.status_code >= 500 and attempt < self.max_retries:
                    last_error = f"HTTP {response.status_code}"
                    print(f"[RETRY] {method} {path} got {response.status_code}, retry {attempt + 1}/{self.max_retries}")
                    self._sleep_backoff(attempt + 1)
                    continue
                outcome = "success" if response.status_code < 500 else "http_5xx_exhausted"
                self._record(
                    method=method,
                    path=path,
                    retries=attempt,
                    outcome=outcome,
                    started_at=started,
                    status_code=response.status_code,
                    error=last_error,
                )
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                last_error = str(exc)
                if attempt < self.max_retries:
                    print(f"[RETRY] {method} {path} transient error, retry {attempt + 1}/{self.max_retries}: {exc}")
                    self._sleep_backoff(attempt + 1)
                    continue
                self._record(
                    method=method,
                    path=path,
                    retries=attempt,
                    outcome="timeout_or_connection_exhausted",
                    started_at=started,
                    error=last_error,
                )
                raise ValidationHttpError(f"{method} {path} failed after retries: {exc}") from exc
            except requests.exceptions.RequestException as exc:
                self._record(
                    method=method,
                    path=path,
                    retries=attempt,
                    outcome="request_exception",
                    started_at=started,
                    error=str(exc),
                )
                raise ValidationHttpError(f"{method} {path} request error: {exc}") from exc

        # Defensive fallback.
        self._record(method=method, path=path, retries=self.max_retries, outcome="unknown_error", started_at=started, error=last_error)
        raise ValidationHttpError(f"{method} {path} failed with unknown retry error")

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

    def warmup(self) -> None:
        warmup_paths = ["/health", "/", "/docs", "/me"]
        for path in warmup_paths:
            try:
                # /me may be unauthorized without token, which is acceptable for warmup.
                self._request("GET", path)
                return
            except Exception:
                continue

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


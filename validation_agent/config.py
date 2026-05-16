from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_URL = os.getenv("VALIDATION_BASE_URL", "https://kiarolabs-membership-service.onrender.com").strip().rstrip("/")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("VALIDATION_REQUEST_TIMEOUT_SECONDS", "20"))
REQUEST_MAX_RETRIES = int(os.getenv("VALIDATION_REQUEST_MAX_RETRIES", "4"))
REQUEST_INITIAL_BACKOFF_SECONDS = float(os.getenv("VALIDATION_REQUEST_INITIAL_BACKOFF_SECONDS", "2"))
REQUEST_BACKOFF_MULTIPLIER = float(os.getenv("VALIDATION_REQUEST_BACKOFF_MULTIPLIER", "2"))


@dataclass(frozen=True)
class Settings:
    base_url: str
    admin_email: str | None
    admin_password: str | None
    student_email: str | None
    student_password: str | None
    reports_dir: Path
    vr_keys_dir: Path
    request_timeout_seconds: float
    request_max_retries: int
    request_initial_backoff_seconds: float
    request_backoff_multiplier: float
    fail_on_failure: bool


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def load_settings() -> Settings:
    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = Path(os.getenv("VALIDATION_REPORTS_DIR", repo_root / "reports"))
    vr_keys_dir = Path(os.getenv("VALIDATION_VR_KEYS_DIR", repo_root / "fixtures" / "vr-answer-keys"))

    base_url = BASE_URL
    admin_email = os.getenv("VALIDATION_ADMIN_EMAIL", "").strip() or None
    admin_password = os.getenv("VALIDATION_ADMIN_PASSWORD", "").strip() or None

    student_email = os.getenv("VALIDATION_STUDENT_EMAIL", "").strip() or None
    student_password = os.getenv("VALIDATION_STUDENT_PASSWORD", "").strip() or None

    return Settings(
        base_url=base_url,
        admin_email=admin_email,
        admin_password=admin_password,
        student_email=student_email,
        student_password=student_password,
        reports_dir=reports_dir,
        vr_keys_dir=vr_keys_dir,
        request_timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        request_max_retries=REQUEST_MAX_RETRIES,
        request_initial_backoff_seconds=REQUEST_INITIAL_BACKOFF_SECONDS,
        request_backoff_multiplier=REQUEST_BACKOFF_MULTIPLIER,
        fail_on_failure=_env_bool("VALIDATION_FAIL_ON_FAILURE", True),
    )

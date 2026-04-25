import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _user(prefix: str, default_email: str, default_password: str) -> dict[str, str]:
    key_prefix = prefix.upper()
    return {
        "email": _env(f"{key_prefix}_EMAIL", default_email),
        "password": _env(f"{key_prefix}_PASSWORD", default_password),
    }


BASE_URL = _env("VALIDATION_BASE_URL", "https://kiarolabs-membership-service.onrender.com")
REPORTS_DIR = Path(_env("VALIDATION_REPORTS_DIR", "reports"))
FAIL_ON_FAILURE = _env("VALIDATION_FAIL_ON_FAILURE", "true").lower() in {"1", "true", "yes", "on"}
REQUEST_TIMEOUT_SECONDS = int(_env("VALIDATION_REQUEST_TIMEOUT_SECONDS", "20"))

TEST_USERS = {
    "admin": _user("VALIDATION_ADMIN", "rishi@test.com", "Learn123!"),
    "test_admin": _user("VALIDATION_TEST_ADMIN", "testagent3@test.com", "Learn123!"),
    "student": _user("VALIDATION_STUDENT", "testuser1@example.com", "Learn123!"),
}

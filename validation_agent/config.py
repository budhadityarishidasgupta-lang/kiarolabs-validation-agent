import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _explicit_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _user(prefix: str, default_email: str, default_password: str) -> dict[str, str]:
    key_prefix = prefix.upper()
    return {
        "email": _env(f"{key_prefix}_EMAIL", default_email),
        "password": _env(f"{key_prefix}_PASSWORD", default_password),
    }


def _resolve_user_with_fallback(
    primary_prefix: str,
    fallback_prefixes: list[str],
    default_email: str,
    default_password: str,
) -> dict[str, str]:
    email_var = f"{primary_prefix.upper()}_EMAIL"
    password_var = f"{primary_prefix.upper()}_PASSWORD"

    explicit_email = _explicit_env(email_var)
    explicit_password = _explicit_env(password_var)
    if explicit_email and explicit_password:
        return {"email": explicit_email, "password": explicit_password}

    for fallback_prefix in fallback_prefixes:
        fallback_email = _explicit_env(f"{fallback_prefix.upper()}_EMAIL")
        fallback_password = _explicit_env(f"{fallback_prefix.upper()}_PASSWORD")
        if fallback_email and fallback_password:
            print(
                f"VALIDATION CONFIG WARNING: {primary_prefix.lower()} credentials missing; "
                f"falling back to {fallback_prefix.lower()} credentials."
            )
            return {"email": fallback_email, "password": fallback_password}

    if explicit_email or explicit_password:
        print(
            f"VALIDATION CONFIG WARNING: {primary_prefix.lower()} credentials are incomplete; "
            "using configured defaults."
        )

    return {"email": default_email, "password": default_password}


BASE_URL = _env("VALIDATION_BASE_URL", "https://kiarolabs-membership-service.onrender.com")
REPORTS_DIR = Path(_env("VALIDATION_REPORTS_DIR", "reports"))
FAIL_ON_FAILURE = _env("VALIDATION_FAIL_ON_FAILURE", "true").lower() in {"1", "true", "yes", "on"}
REQUEST_TIMEOUT_SECONDS = int(_env("VALIDATION_REQUEST_TIMEOUT_SECONDS", "20"))

TEST_USERS = {
    "admin": _user("VALIDATION_ADMIN", "rishi@test.com", "Learn123!"),
    "test_admin": _resolve_user_with_fallback(
        "VALIDATION_TEST_ADMIN",
        ["VALIDATION_ADMIN"],
        "testagent3@test.com",
        "Learn123!",
    ),
    "student": _resolve_user_with_fallback(
        "VALIDATION_STUDENT",
        ["VALIDATION_TEST_ADMIN", "VALIDATION_ADMIN"],
        "testuser1@example.com",
        "Learn123!",
    ),
}

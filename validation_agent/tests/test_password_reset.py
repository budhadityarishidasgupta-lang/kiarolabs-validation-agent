from validation_agent.client import APIClient


def test_request_reset_does_not_expose_user_existence():
    client = APIClient()
    res = client.post(
        "/auth/request-reset",
        {"email": "unknown-reset-user@example.com"},
        token=None,
    )

    assert res.status_code == 200, res.text
    assert res.json()["message"] == "If account exists, reset link sent"


def test_reset_password_rejects_invalid_token():
    client = APIClient()
    res = client.post(
        "/auth/reset-password",
        {
            "token": "invalid-token",
            "new_password": "NewLearn123!",
        },
        token=None,
    )

    assert res.status_code == 400, res.text


def test_direct_reset_does_not_expose_user_existence():
    client = APIClient()
    res = client.post(
        "/auth/reset-password-direct",
        {
            "email": "unknown-direct-reset-user@example.com",
            "new_password": "NewLearn123!",
        },
        token=None,
    )

    assert res.status_code == 200, res.text
    assert res.json()["message"] == "If account exists, password updated"


def test_admin_reset_password_requires_token():
    client = APIClient()
    res = client.post(
        "/admin/reset-password",
        {
            "user_id": 999999,
            "new_password": "NewLearn123!",
        },
        token=None,
    )

    assert res.status_code in [401, 403], res.text

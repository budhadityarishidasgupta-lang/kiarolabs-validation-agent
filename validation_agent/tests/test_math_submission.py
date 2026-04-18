import requests

from validation_agent.config import BASE_URL, TEST_USERS


def test_math_submission():
    print("\nRunning test_math_submission...")

    login_res = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": TEST_USERS["admin"]["email"],
            "password": TEST_USERS["admin"]["password"],
        },
        timeout=20,
    )

    assert login_res.status_code == 200, "Login failed"

    token = login_res.json().get("access_token")
    assert token, "Token missing"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "paper_code": "MATH_PAPER_A",
        "answers": ["1/1", "240", "A", "72", "8"],
    }

    res = requests.post(
        f"{BASE_URL}/practice/math/submit",
        json=payload,
        headers=headers,
        timeout=20,
    )

    print("STATUS:", res.status_code)
    print("TEXT:", res.text)

    assert res.status_code == 200, "Submission failed"

    data = res.json()

    assert "score" in data, "Score missing"
    assert "total" in data, "Total missing"
    assert data["total"] > 0, "Invalid total"

    print("test_math_submission PASSED")

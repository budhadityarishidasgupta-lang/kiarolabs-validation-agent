from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def test_login():
    client = APIClient()
    client.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])

    res = client.get("/me")
    assert res.status_code == 200

    data = res.json()
    assert "email" in data


def test_repeat_login_stress():
    for _ in range(5):
        test_login()


def test_login_invalid():
    client = APIClient()
    res = client.login_response("wrong@test.com", "Wrong123")

    print("STATUS:", res.status_code)
    print("TEXT:", res.text)
    assert res.status_code in [400, 401]

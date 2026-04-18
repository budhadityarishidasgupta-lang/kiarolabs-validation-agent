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


def test_admin_role_consistency():
    client = APIClient()
    login_res = client.login_response(
        TEST_USERS["admin"]["email"],
        TEST_USERS["admin"]["password"],
    )
    print("STATUS:", login_res.status_code)
    print("TEXT:", login_res.text)
    assert login_res.status_code == 200

    login_data = login_res.json()
    client.token = login_data["access_token"]

    me_res = client.get("/me")
    dashboard_res = client.get("/dashboard")

    assert me_res.status_code == 200, me_res.text
    assert dashboard_res.status_code == 200, dashboard_res.text

    me_data = me_res.json()
    dashboard_data = dashboard_res.json()

    assert login_data["role"] == "admin"
    assert me_data["role"] == login_data["role"]
    assert dashboard_data["role"] == login_data["role"]
    assert login_data["email"] == me_data["email"]
    assert login_data["user_id"] == me_data["user_id"]
    assert login_data["account_type"] == me_data["account_type"]

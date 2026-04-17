from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS

def test_login():
    client = APIClient()
    client.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])

    res = client.get("/me")
    assert res.status_code == 200

    data = res.json()
    assert "email" in data

from client import APIClient
from config import TEST_USERS

def test_dashboard_loads():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    res = client.get("/dashboard")
    assert res.status_code == 200

    data = res.json()
    assert "spelling" in data
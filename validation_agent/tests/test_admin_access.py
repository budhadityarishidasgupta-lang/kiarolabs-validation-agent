from client import APIClient
from config import TEST_USERS

def test_admin_unlocks_all():
    client = APIClient()
    client.login(TEST_USERS["test_admin"]["email"], TEST_USERS["test_admin"]["password"])

    res = client.get("/practice/math/tests")
    data = res.json()

    for test in data:
        assert test["access"] == "full", "Admin access failed"
from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS

def test_admin_unlocks_all():
    client = APIClient()
    client.login(TEST_USERS["test_admin"]["email"], TEST_USERS["test_admin"]["password"])

    res = client.get("/dashboard")
    data = res.json()

    assert data["modules"]["spelling"]["unlocked"] == True
    assert data["modules"]["words"]["unlocked"] == True

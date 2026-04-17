from client import APIClient
from validation_agent.config import TEST_USERS


def test_dashboard_loads():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    res = client.get("/dashboard")
    assert res.status_code == 200

    data = res.json()
    assert "modules" in data
    assert "spelling" in data["modules"]


def test_dashboard_admin_unlocks_all_modules():
    client = APIClient()
    client.login(TEST_USERS["test_admin"]["email"], TEST_USERS["test_admin"]["password"])

    res = client.get("/dashboard")
    assert res.status_code == 200

    modules = res.json()
    for module_name, module_data in modules.items():
        assert module_data.get("unlocked") is True, (
            f"Expected admin to have '{module_name}' unlocked, got: {module_data}"
        )

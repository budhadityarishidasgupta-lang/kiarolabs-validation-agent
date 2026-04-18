from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def test_admin_can_start_mock_test_without_purchase_check():
    client = APIClient()
    client.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])

    tests_res = client.get("/practice/math/tests")
    assert tests_res.status_code == 200, tests_res.text

    tests = tests_res.json()
    assert isinstance(tests, list) and tests, f"Expected mock tests list: {tests}"

    test_id = tests[0]["test_id"]
    start_res = client.get(f"/practice/math/test/start?test_id={test_id}")

    assert start_res.status_code == 200, start_res.text
    payload = start_res.json()
    assert payload["test_id"] == test_id
    assert isinstance(payload["questions"], list)

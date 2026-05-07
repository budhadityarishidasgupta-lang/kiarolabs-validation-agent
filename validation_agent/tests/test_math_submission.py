import pytest

from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def _start_first_available_math_test(client: APIClient):
    tests_res = client.get("/practice/math/tests")
    assert tests_res.status_code == 200, tests_res.text

    payload = tests_res.json()
    tests = payload.get("tests") if isinstance(payload, dict) else payload
    assert isinstance(tests, list), f"Expected tests list payload: {payload}"
    if not tests:
        pytest.skip("Skipping math submission test: no math tests are available.")

    for item in tests:
        if not isinstance(item, dict):
            continue

        test_id = item.get("test_id") or item.get("paper_code")
        if not test_id:
            continue

        start_res = client.get(f"/practice/math/test/start?test_id={test_id}")
        if start_res.status_code != 200:
            continue

        start_payload = start_res.json()
        questions = start_payload.get("questions") if isinstance(start_payload, dict) else None
        if not isinstance(questions, list) or not questions:
            continue

        return test_id, questions

    pytest.skip("Skipping math submission test: no startable math test was returned by the API.")


def test_math_submission():
    print("\nRunning test_math_submission...")

    client = APIClient()
    client.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])

    test_id, questions = _start_first_available_math_test(client)

    answers = [
        {
            "question_id": question.get("question_id"),
            "selected_option": question.get("correct_option"),
            "correct_option": question.get("correct_option"),
        }
        for question in questions
    ]

    res = client.post(
        "/practice/math/test/submit",
        {"answers": answers},
    )

    print("STATUS:", res.status_code)
    print("TEXT:", res.text)

    assert res.status_code == 200, "Submission failed"

    data = res.json()

    assert "score" in data, "Score missing"
    assert "total" in data, "Total missing"
    assert data["total"] > 0, "Invalid total"
    assert data["score"] == data["total"], f"Expected perfect score for {test_id}: {data}"

    print("test_math_submission PASSED")

from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS
import pytest


def _get_first_available_math_test(client: APIClient):
    tests_res = client.get("/practice/math/tests")
    assert tests_res.status_code == 200, tests_res.text

    payload = tests_res.json()
    tests = payload["tests"] if isinstance(payload, dict) else payload
    assert isinstance(tests, list), f"Expected mock tests list: {tests}"
    if not tests:
        pytest.skip("Skipping math tests: no math tests are available.")

    for item in tests:
        if not isinstance(item, dict):
            continue
        test_id = item.get("test_id") or item.get("paper_code")
        if test_id:
            return test_id

    pytest.skip("Skipping math tests: no valid test_id or paper_code returned by API.")


def test_admin_can_start_mock_test_without_purchase_check():
    client = APIClient()
    client.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])

    test_id = _get_first_available_math_test(client)
    start_res = client.get(f"/practice/math/test/start?test_id={test_id}")

    assert start_res.status_code == 200, start_res.text
    payload = start_res.json()
    assert payload["test_id"] == test_id
    assert isinstance(payload["questions"], list) and payload["questions"], payload


def test_math_paper_submission_returns_score():
    client = APIClient()
    client.login(TEST_USERS["admin"]["email"], TEST_USERS["admin"]["password"])

    test_id = _get_first_available_math_test(client)
    start_res = client.get(f"/practice/math/test/start?test_id={test_id}")
    assert start_res.status_code == 200, start_res.text

    start_payload = start_res.json()
    questions = start_payload.get("questions")
    assert isinstance(questions, list) and questions, start_payload

    answers = [
        {
            "question_id": question.get("question_id"),
            "selected_option": question.get("correct_option"),
            "correct_option": question.get("correct_option"),
        }
        for question in questions
    ]

    submit_res = client.post(
        "/practice/math/test/submit",
        {
            "answers": answers,
        },
    )

    assert submit_res.status_code == 200, submit_res.text
    payload = submit_res.json()
    assert "score" in payload
    assert "total" in payload
    assert payload["total"] > 0
    assert payload["score"] == payload["total"], f"Expected perfect mock-test score for {test_id}: {payload}"

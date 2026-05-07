import pytest

from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def _json_or_raise(response, endpoint):
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(
            f"Expected JSON from {endpoint} but got status={response.status_code}, body={response.text}"
        ) from exc


def _extract_passage_ids(courses_payload):
    courses = courses_payload.get("courses") if isinstance(courses_payload, dict) else courses_payload
    assert isinstance(courses, list) and courses, f"Courses list missing or empty: {courses_payload}"

    passage_ids = []
    for course in courses:
        lessons = course.get("lessons") if isinstance(course, dict) else None
        if not isinstance(lessons, list):
            continue
        for lesson in lessons:
            if isinstance(lesson, dict) and lesson.get("lesson_id") is not None:
                passage_ids.append(lesson["lesson_id"])

    assert passage_ids, f"No passage ids found in comprehension courses payload: {courses_payload}"
    return passage_ids


def _assert_optional_encouragement(item):
    if "encouragement_message" in item:
        assert isinstance(item["encouragement_message"], str), item
        assert item["encouragement_message"].strip(), item


def test_comprehension_no_immediate_repeat():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    courses_res = client.get("/practice/comprehension/courses")
    assert courses_res.status_code == 200, courses_res.text
    courses_payload = _json_or_raise(courses_res, "/practice/comprehension/courses")
    passage_ids = _extract_passage_ids(courses_payload)

    for passage_id in passage_ids[:10]:
        start_res = client.get(f"/practice/comprehension/start?passage_id={passage_id}")
        if start_res.status_code != 200:
            continue

        start_payload = _json_or_raise(start_res, f"/practice/comprehension/start?passage_id={passage_id}")
        questions = start_payload.get("questions")
        if not isinstance(questions, list):
            continue

        question_ids = [q.get("question_id") for q in questions if isinstance(q, dict) and q.get("question_id") is not None]
        if len(set(question_ids)) < 2:
            continue

        first_question_id = start_payload.get("start_question_id") or question_ids[0]
        first_res = client.get(
            f"/practice/comprehension/question?passage_id={passage_id}&question_id={first_question_id}"
        )
        assert first_res.status_code == 200, first_res.text
        first_question = _json_or_raise(
            first_res,
            f"/practice/comprehension/question?passage_id={passage_id}&question_id={first_question_id}",
        )
        assert first_question.get("question_id") is not None, first_question
        _assert_optional_encouragement(first_question)

        submit_res = client.post(
            "/practice/comprehension/answer",
            {
                "passage_id": passage_id,
                "question_id": first_question["question_id"],
                "selected_answer": "__validation_wrong__",
            },
        )
        assert submit_res.status_code == 200, submit_res.text

        second_res = client.get(f"/practice/comprehension/question?passage_id={passage_id}")
        assert second_res.status_code == 200, second_res.text
        second_question = _json_or_raise(
            second_res,
            f"/practice/comprehension/question?passage_id={passage_id}",
        )
        assert second_question.get("question_id") is not None, second_question
        _assert_optional_encouragement(second_question)

        assert second_question["question_id"] != first_question["question_id"], (
            f"Immediate comprehension repeat violation for passage_id={passage_id}: "
            f"question_id {first_question['question_id']} repeated despite multiple "
            f"questions being available in the passage."
        )
        return

    pytest.skip("Skipping comprehension anti-repeat test: no suitable multi-question passage found.")

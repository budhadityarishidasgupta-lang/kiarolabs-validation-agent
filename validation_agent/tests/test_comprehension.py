import pytest

from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS
from validation_agent.learning_integrity import (
    assert_no_answer_leakage,
    assert_options_integrity,
    assert_progression_advances,
    warn_if_review_distribution_excessive,
)


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


def _get_comprehension_question(client: APIClient, passage_id, question_id=None):
    path = (
        f"/practice/comprehension/question?passage_id={passage_id}&question_id={question_id}"
        if question_id is not None
        else f"/practice/comprehension/question?passage_id={passage_id}"
    )
    response = client.get(path)
    assert response.status_code == 200, response.text
    question = _json_or_raise(response, path)
    assert question.get("question_id") is not None, question
    assert_no_answer_leakage(question, context=f"comprehension passage_id={passage_id}")
    assert_options_integrity(
        item_id=question["question_id"],
        headword="",
        options=question.get("options"),
        context="comprehension",
    )
    return question


def test_comprehension_learning_integrity():
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
        first_question = _get_comprehension_question(client, passage_id, question_id=first_question_id)

        submit_res = client.post(
            "/practice/comprehension/answer",
            {
                "passage_id": passage_id,
                "question_id": first_question["question_id"],
                "selected_answer": "__validation_wrong__",
            },
        )
        assert submit_res.status_code == 200, submit_res.text

        second_question = _get_comprehension_question(client, passage_id)
        assert_progression_advances(
            first_question,
            second_question,
            context=f"comprehension passage_id={passage_id}",
        )
        return

    pytest.skip("Skipping comprehension integrity test: no suitable multi-question passage found.")


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
        first_question = _get_comprehension_question(client, passage_id, question_id=first_question_id)
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

        second_question = _get_comprehension_question(client, passage_id)
        _assert_optional_encouragement(second_question)
        assert_progression_advances(
            first_question,
            second_question,
            context=f"comprehension passage_id={passage_id}",
        )

        assert second_question["question_id"] != first_question["question_id"], (
            f"Immediate comprehension repeat violation for passage_id={passage_id}: "
            f"question_id {first_question['question_id']} repeated despite multiple "
            f"questions being available in the passage."
        )
        return

    pytest.skip("Skipping comprehension anti-repeat test: no suitable multi-question passage found.")


def test_comprehension_review_distribution_warn():
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

        observed_questions = []
        current_question = _get_comprehension_question(client, passage_id, question_id=start_payload.get("start_question_id") or question_ids[0])
        observed_questions.append(current_question)

        for _ in range(5):
            submit_res = client.post(
                "/practice/comprehension/answer",
                {
                    "passage_id": passage_id,
                    "question_id": current_question["question_id"],
                    "selected_answer": "__validation_wrong__",
                },
            )
            assert submit_res.status_code == 200, submit_res.text
            current_question = _get_comprehension_question(client, passage_id)
            observed_questions.append(current_question)

        warn_if_review_distribution_excessive(
            observed_questions,
            context=f"comprehension passage_id={passage_id}",
        )
        return

    pytest.skip("Skipping comprehension review distribution test: no suitable multi-question passage found.")

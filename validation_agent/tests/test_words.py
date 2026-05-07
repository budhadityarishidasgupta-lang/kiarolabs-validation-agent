import base64
import json

import pytest

from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def _extract_first_lesson_id(courses_payload):
    """Extract the first lesson_id from the courses payload returned by API."""
    courses = courses_payload.get("courses") if isinstance(courses_payload, dict) else courses_payload
    assert isinstance(courses, list) and courses, f"Courses list missing or empty: {courses_payload}"

    first_course = courses[0]
    assert isinstance(first_course, dict), f"First course must be dict, got: {type(first_course).__name__}"

    lessons = first_course.get("lessons")
    assert isinstance(lessons, list) and lessons, f"Lessons missing for first course: {first_course}"

    first_lesson = lessons[0]
    assert isinstance(first_lesson, dict), f"First lesson must be dict, got: {type(first_lesson).__name__}"
    assert "lesson_id" in first_lesson, f"lesson_id missing in lesson payload: {first_lesson}"

    return first_lesson["lesson_id"]


def _json_or_raise(response, endpoint):
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(
            f"Expected JSON from {endpoint} but got status={response.status_code}, body={response.text}"
        ) from exc


def _decode_jwt_payload(token):
    parts = token.split('.')
    if len(parts) != 3:
        return {}
    payload_b64 = parts[1] + '=' * ((4 - len(parts[1]) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))


def _extract_lesson_ids(courses_payload):
    courses = courses_payload.get("courses") if isinstance(courses_payload, dict) else courses_payload
    assert isinstance(courses, list) and courses, f"Courses list missing or empty: {courses_payload}"

    lesson_ids = []
    for course in courses:
        lessons = course.get("lessons") if isinstance(course, dict) else None
        if not isinstance(lessons, list):
            continue
        for lesson in lessons:
            if isinstance(lesson, dict) and lesson.get("lesson_id") is not None:
                lesson_ids.append(lesson["lesson_id"])

    assert lesson_ids, f"No lesson_ids found in words courses payload: {courses_payload}"
    return lesson_ids


def _assert_optional_encouragement(item):
    if "encouragement_message" in item:
        assert isinstance(item["encouragement_message"], str), item
        assert item["encouragement_message"].strip(), item


def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    jwt_payload = _decode_jwt_payload(client.token)
    if jwt_payload.get("user_id") is None:
        pytest.skip("Skipping words test: student JWT missing user_id claim")

    courses_res = client.get("/practice/courses")
    courses_payload = _json_or_raise(courses_res, "/practice/courses")
    lesson_id = _extract_first_lesson_id(courses_payload)

    start_res = client.get(f"/practice/session/start?lesson_id={lesson_id}")
    start_payload = _json_or_raise(start_res, f"/practice/session/start?lesson_id={lesson_id}")

    assert isinstance(start_payload, dict) and start_payload, f"Invalid session start payload: {start_payload}"
    assert "question" in start_payload, f"question missing in session start payload: {start_payload}"

    question = start_payload["question"]
    assert isinstance(question, dict) and question, f"Invalid question payload in session start response: {question}"
    assert "word_id" in question, f"word_id missing in question payload: {question}"
    assert "options" in question, f"options missing in question payload: {question}"
    assert isinstance(question["options"], list) and question["options"], f"options must be a non-empty list: {question}"

    word_id = question["word_id"]
    options = question["options"]
    submit_payload = {
        "word_id": word_id,
        "chosen": options[0],
        "response_ms": 1000,
    }
    submit_res = client.post("/practice/synonym/answer", submit_payload)

    assert submit_res.status_code == 200, submit_res.text


def test_invalid_word_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    submit_res = client.post(
        "/practice/synonym/answer",
        {
            "word_id": 999999,
            "chosen": "test",
            "response_ms": 1000,
        },
    )

    assert submit_res.status_code in [400, 404], submit_res.text


def test_words_no_immediate_repeat():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    jwt_payload = _decode_jwt_payload(client.token)
    if jwt_payload.get("user_id") is None:
        pytest.skip("Skipping words anti-repeat test: student JWT missing user_id claim")

    courses_res = client.get("/practice/courses")
    courses_payload = _json_or_raise(courses_res, "/practice/courses")
    lesson_ids = _extract_lesson_ids(courses_payload)

    for lesson_id in lesson_ids[:10]:
        first_res = client.get(f"/practice/session/start?lesson_id={lesson_id}")
        if first_res.status_code != 200:
            continue

        first_payload = _json_or_raise(first_res, f"/practice/session/start?lesson_id={lesson_id}")
        first_question = first_payload.get("question")
        if not isinstance(first_question, dict) or first_question.get("word_id") is None:
            continue

        _assert_optional_encouragement(first_question)

        submit_res = client.post(
            "/practice/synonym/answer",
            {
                "word_id": first_question["word_id"],
                "chosen": "__validation_wrong__",
                "response_ms": 1000,
            },
        )
        assert submit_res.status_code == 200, submit_res.text

        second_res = client.get(f"/practice/session/start?lesson_id={lesson_id}")
        assert second_res.status_code == 200, second_res.text
        second_payload = _json_or_raise(second_res, f"/practice/session/start?lesson_id={lesson_id}")
        second_question = second_payload.get("question")
        assert isinstance(second_question, dict) and second_question.get("word_id") is not None, second_payload
        _assert_optional_encouragement(second_question)

        if second_question["word_id"] != first_question["word_id"]:
            return

        second_submit_res = client.post(
            "/practice/synonym/answer",
            {
                "word_id": second_question["word_id"],
                "chosen": "__validation_wrong__",
                "response_ms": 1000,
            },
        )
        assert second_submit_res.status_code == 200, second_submit_res.text

        third_res = client.get(f"/practice/session/start?lesson_id={lesson_id}")
        assert third_res.status_code == 200, third_res.text
        third_payload = _json_or_raise(third_res, f"/practice/session/start?lesson_id={lesson_id}")
        third_question = third_payload.get("question")
        assert isinstance(third_question, dict) and third_question.get("word_id") is not None, third_payload
        _assert_optional_encouragement(third_question)

        if third_question["word_id"] != second_question["word_id"]:
            raise AssertionError(
                f"Immediate WordSprint repeat violation for lesson_id={lesson_id}: "
                f"word_id {first_question['word_id']} repeated immediately even though "
                f"another word {third_question['word_id']} was available."
            )

    pytest.skip("Skipping words anti-repeat test: no suitable multi-item lesson found.")

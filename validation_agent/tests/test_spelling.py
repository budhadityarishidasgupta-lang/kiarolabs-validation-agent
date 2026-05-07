from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS
import pytest


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

    assert lesson_ids, f"No lesson_ids found in spelling courses payload: {courses_payload}"
    return lesson_ids


def _assert_optional_encouragement(item):
    if "encouragement_message" in item:
        assert isinstance(item["encouragement_message"], str), item
        assert item["encouragement_message"].strip(), item


def test_spelling_question_retrieval():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    courses_res = client.get("/practice/spelling/courses")
    courses_payload = courses_res.json()
    lesson_id = _extract_first_lesson_id(courses_payload)

    question_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
    question = question_res.json()
    if question_res.status_code == 400 and "User not provisioned" in question_res.text:
        pytest.skip("Skipping spelling test: user is not provisioned for spelling.")

    assert question_res.status_code == 200, question_res.text
    assert isinstance(question, dict) and question, f"Invalid spelling question payload: {question}"
    assert "word_id" in question, f"word_id missing in spelling question payload: {question}"
    assert "masked_word" in question, f"masked_word missing in spelling question payload: {question}"


def test_spelling_no_immediate_repeat():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    courses_res = client.get("/practice/spelling/courses")
    courses_payload = courses_res.json()
    lesson_ids = _extract_lesson_ids(courses_payload)

    if not lesson_ids:
        pytest.skip("Skipping spelling anti-repeat test: no spelling lessons available.")

    for lesson_id in lesson_ids[:10]:
        first_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
        if first_res.status_code == 400 and "User not provisioned" in first_res.text:
            pytest.skip("Skipping spelling anti-repeat test: user is not provisioned for spelling.")
        if first_res.status_code != 200:
            continue

        first_question = first_res.json()
        if not isinstance(first_question, dict) or first_question.get("word_id") is None:
            continue

        _assert_optional_encouragement(first_question)

        submit_payload = {
            "lesson_id": lesson_id,
            "word_id": first_question["word_id"],
            "answer": "__validation_wrong__",
            "response_ms": 1000,
        }
        if first_question.get("question_id") is not None:
            submit_payload["question_id"] = first_question["question_id"]
        if first_question.get("session_id") is not None:
            submit_payload["session_id"] = first_question["session_id"]

        submit_res = client.post("/practice/spelling/answer", submit_payload)
        assert submit_res.status_code == 200, submit_res.text

        second_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
        assert second_res.status_code == 200, second_res.text
        second_question = second_res.json()
        assert isinstance(second_question, dict) and second_question.get("word_id") is not None, second_question
        _assert_optional_encouragement(second_question)

        if second_question["word_id"] != first_question["word_id"]:
            return

        second_submit_payload = {
            "lesson_id": lesson_id,
            "word_id": second_question["word_id"],
            "answer": "__validation_wrong__",
            "response_ms": 1000,
        }
        if second_question.get("question_id") is not None:
            second_submit_payload["question_id"] = second_question["question_id"]
        if second_question.get("session_id") is not None:
            second_submit_payload["session_id"] = second_question["session_id"]

        second_submit_res = client.post("/practice/spelling/answer", second_submit_payload)
        assert second_submit_res.status_code == 200, second_submit_res.text

        third_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
        assert third_res.status_code == 200, third_res.text
        third_question = third_res.json()
        assert isinstance(third_question, dict) and third_question.get("word_id") is not None, third_question
        _assert_optional_encouragement(third_question)

        if third_question["word_id"] != second_question["word_id"]:
            raise AssertionError(
                f"Immediate spelling repeat violation for lesson_id={lesson_id}: "
                f"word_id {first_question['word_id']} repeated immediately even though "
                f"another word {third_question['word_id']} was available."
            )

    pytest.skip("Skipping spelling anti-repeat test: no suitable multi-item lesson found.")

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
        value = item["encouragement_message"]
        assert value is None or (isinstance(value, str) and value.strip()), item


def _assert_spelling_review_contract(question):
    is_review = bool(question.get("is_review"))
    session_state = question.get("session_state")
    assert isinstance(session_state, dict), f"session_state missing or invalid: {question}"
    assert session_state.get("is_review") is is_review, f"session_state.is_review mismatch: {question}"

    encouragement = question.get("encouragement_message")
    review_reason = question.get("review_reason")
    session_review_reason = session_state.get("review_reason")

    if is_review:
        assert isinstance(encouragement, str) and encouragement.strip(), (
            f"Review spelling question missing encouragement_message: {question}"
        )
        assert isinstance(review_reason, str) and review_reason.strip(), (
            f"Review spelling question missing review_reason: {question}"
        )
        assert session_review_reason == review_reason, (
            f"session_state.review_reason mismatch: {question}"
        )
    else:
        assert encouragement is None, (
            f"Ordinary spelling question leaked encouragement_message: {question}"
        )
        assert review_reason is None, (
            f"Ordinary spelling question leaked review_reason: {question}"
        )
        assert session_review_reason is None, (
            f"Ordinary spelling question leaked session_state.review_reason: {question}"
        )


def _submit_wrong_spelling_answer(client: APIClient, lesson_id, question):
    payload = {
        "lesson_id": lesson_id,
        "word_id": question["word_id"],
        "answer": "__validation_wrong__",
        "response_ms": 1000,
    }
    if question.get("question_id") is not None:
        payload["question_id"] = question["question_id"]
    if question.get("session_id") is not None:
        payload["session_id"] = question["session_id"]

    submit_res = client.post("/practice/spelling/answer", payload)
    assert submit_res.status_code == 200, submit_res.text


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
    assert question.get("example_sentence") is None, (
        f"Spelling question leaked example_sentence before submit: {question}"
    )
    _assert_spelling_review_contract(question)


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

        assert first_question.get("example_sentence") is None, (
            f"Spelling question leaked example_sentence before submit: {first_question}"
        )
        _assert_optional_encouragement(first_question)
        _assert_spelling_review_contract(first_question)

        first_word_id = first_question["word_id"]
        _submit_wrong_spelling_answer(client, lesson_id, first_question)

        second_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
        assert second_res.status_code == 200, second_res.text
        second_question = second_res.json()
        assert isinstance(second_question, dict) and second_question.get("word_id") is not None, second_question
        assert second_question.get("example_sentence") is None, (
            f"Spelling question leaked example_sentence before submit: {second_question}"
        )
        _assert_optional_encouragement(second_question)
        _assert_spelling_review_contract(second_question)

        if second_question["word_id"] == first_word_id:
            raise AssertionError(
                f"Immediate spelling repeat violation for lesson_id={lesson_id}: "
                f"word_id {first_word_id} repeated immediately after a wrong answer."
            )

        seen_word_ids = {first_word_id, second_question["word_id"]}
        first_word_returned = False
        return_question = None
        current_question = second_question

        for _ in range(4):
            _submit_wrong_spelling_answer(client, lesson_id, current_question)
            next_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
            assert next_res.status_code == 200, next_res.text
            next_question = next_res.json()
            assert isinstance(next_question, dict) and next_question.get("word_id") is not None, next_question
            assert next_question.get("example_sentence") is None, (
                f"Spelling question leaked example_sentence before submit: {next_question}"
            )
            _assert_optional_encouragement(next_question)
            _assert_spelling_review_contract(next_question)

            next_word_id = next_question["word_id"]
            if next_word_id == first_word_id:
                first_word_returned = True
                return_question = next_question
                break

            seen_word_ids.add(next_word_id)
            current_question = next_question

        if len(seen_word_ids) >= 5:
            assert not first_word_returned, (
                f"Cooldown violation for lesson_id={lesson_id}: word_id {first_word_id} "
                "returned within the next 4 questions even though at least 5 lesson words were available."
            )

            _submit_wrong_spelling_answer(client, lesson_id, current_question)
            return_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
            assert return_res.status_code == 200, return_res.text
            return_question = return_res.json()
            assert isinstance(return_question, dict) and return_question.get("word_id") is not None, return_question
            assert return_question.get("example_sentence") is None, (
                f"Spelling question leaked example_sentence before submit: {return_question}"
            )
            _assert_optional_encouragement(return_question)
            _assert_spelling_review_contract(return_question)

            if return_question["word_id"] == first_word_id and "encouragement_message" in return_question:
                assert return_question["encouragement_message"].strip(), return_question
            return

        if first_word_returned and "encouragement_message" in return_question:
            assert return_question["encouragement_message"].strip(), return_question
            return

    pytest.skip("Skipping spelling anti-repeat test: no suitable multi-item lesson found.")

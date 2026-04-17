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


def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

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

    submit_payload = {
        "word_id": question["word_id"],
        "answer": question["options"][0],
    }
    submit_res = client.post("/practice/synonym/answer", submit_payload)

    assert submit_res.status_code == 200, submit_res.text

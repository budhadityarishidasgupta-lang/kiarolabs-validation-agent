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


def test_spelling_question_retrieval():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    courses_res = client.get("/practice/spelling/courses")
    courses_payload = courses_res.json()
    lesson_id = _extract_first_lesson_id(courses_payload)

    question_res = client.get(f"/practice/spelling/question?lesson_id={lesson_id}")
    question = question_res.json()

    assert question_res.status_code == 200, question_res.text
    assert isinstance(question, dict) and question, f"Invalid spelling question payload: {question}"
    assert "word_id" in question, f"word_id missing in spelling question payload: {question}"
    assert "masked_word" in question, f"masked_word missing in spelling question payload: {question}"

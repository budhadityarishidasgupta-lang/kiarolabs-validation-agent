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


def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    # 1) Follow UI flow: fetch courses and resolve lesson_id from API response
    courses_res = client.get("/practice/courses")
    courses_payload = courses_res.json()
    lesson_id = _extract_first_lesson_id(courses_payload)

    # 2) Fetch synonym question using lesson_id from API
    question_res = client.get(f"/practice/synonym/question?lesson_id={lesson_id}")
    question = question_res.json()

    assert isinstance(question, dict) and question, f"Invalid synonym question payload: {question}"
    assert "word_id" in question, f"word_id missing in synonym question payload: {question}"
    assert "correct_answer" in question, f"correct_answer missing in synonym question payload: {question}"

    # 3) Submit using UI payload structure with only API-returned fields
    submit_payload = {
        "word_id": question["word_id"],
        "answer": question["correct_answer"],
    }
    submit_res = client.post("/practice/synonym/answer", submit_payload)

    assert submit_res.status_code == 200, submit_res.text

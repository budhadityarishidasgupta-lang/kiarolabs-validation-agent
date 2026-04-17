from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    # 1) Fetch courses
    courses_res = client.get("/practice/courses")
    courses_payload = courses_res.json()

    # 2) Extract first course -> first lesson -> lesson_id
    courses = courses_payload.get("courses") if isinstance(courses_payload, dict) else courses_payload
    assert isinstance(courses, list) and courses, f"Courses list missing or empty: {courses_payload}"

    first_course = courses[0]
    lessons = first_course.get("lessons") if isinstance(first_course, dict) else None
    assert isinstance(lessons, list) and lessons, f"Lessons missing for first course: {first_course}"

    first_lesson = lessons[0]
    lesson_id = first_lesson.get("lesson_id") or first_lesson.get("id")
    assert lesson_id is not None, f"Lesson id missing in first lesson: {first_lesson}"

    # 3) Fetch question (GET with lesson_id)
    q_res = client.get(f"/practice/synonym/question?lesson_id={lesson_id}")
    q = q_res.json()

    # 4) Validate response
    assert q is not None, "Synonym question response is None"
    assert isinstance(q, dict), f"Synonym question response must be dict, got {type(q).__name__}"
    assert "word_id" in q or "id" in q, "Synonym question missing both 'word_id' and 'id'"

    word_id = q.get("word_id") or q.get("id")
    assert word_id is not None, f"word_id resolved to None from payload: {q}"

    options = q.get("options")
    correct_answer = q.get("correct_answer")
    if correct_answer is None and isinstance(options, list) and options:
        correct_answer = options[0]
    assert correct_answer is not None, f"No answer available in question payload: {q}"

    # 5) Submit answer
    res = client.post(
        "/practice/synonym/answer",
        {
            "word_id": word_id,
            "answer": correct_answer,
        },
    )

    assert res.status_code == 200

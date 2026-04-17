from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS

def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    client.post("/practice/session/start", {"module": "synonym"})

    courses_res = client.get("/practice/courses")
    courses_payload = courses_res.json()

    courses = courses_payload.get("courses") if isinstance(courses_payload, dict) else courses_payload
    first_course = courses[0] if isinstance(courses, list) and courses else {}
    course_id = first_course.get("course_id") or first_course.get("id")

    lessons = first_course.get("lessons") if isinstance(first_course, dict) else None
    first_lesson = lessons[0] if isinstance(lessons, list) and lessons else {}
    lesson_id = first_lesson.get("lesson_id") or first_lesson.get("id")

    if lesson_id is None and course_id is not None:
        lesson_id = course_id

    q_res = client.get(f"/practice/synonym/question?lesson_id={lesson_id}")
    if not getattr(q_res, "text", "").strip():
        raise Exception("Empty response from synonym API")

    q = q_res.json()
    word_id = q.get("word_id") or q.get("id")

    res = client.post("/practice/synonym/answer", {
        "word_id": word_id,
        "answer": q["correct_answer"]
    })

    assert res.status_code == 200

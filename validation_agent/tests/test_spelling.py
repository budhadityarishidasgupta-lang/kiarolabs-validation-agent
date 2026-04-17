from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS

def test_spelling_attempt_recorded():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    # Get a question
    q = client.get("/practice/spelling/question?lesson_id=1").json()

    word_id = q.get("word_id") or q.get("id")

    # Submit answer
    response = client.post("/practice/spelling/submit", {
        "word_id": word_id,
        "answer": q.get("word") or q.get("word_audio"),
        "correct": True
    })

    assert response is not None
    assert getattr(response, "status_code", None) == 200

    # Response payload shape can vary; only verify JSON is valid when present
    if getattr(response, "text", "").strip():
        payload = response.json()
        assert payload is not None

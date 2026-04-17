from client import APIClient
from config import TEST_USERS

def test_spelling_attempt_recorded():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    # Get a question
    q = client.get("/practice/spelling/question?lesson_id=1").json()

    # Submit answer
    res = client.post("/practice/spelling/submit", {
        "word_id": q["word_id"],
        "answer": q["word"],
        "correct": True
    })

    assert res.status_code == 200
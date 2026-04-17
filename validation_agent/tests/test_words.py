from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS

def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    q = client.get("/practice/synonym/question").json()
    word_id = q.get("word_id") or q.get("id")

    res = client.post("/practice/synonym/answer", {
        "word_id": word_id,
        "answer": q["correct_answer"]
    })

    assert res.status_code == 200

from client import APIClient
from config import TEST_USERS

def test_words_submission():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    q = client.get("/practice/words/question").json()

    res = client.post("/practice/words/submit", {
        "word_id": q["word_id"],
        "answer": q["correct_answer"]
    })

    assert res.status_code == 200
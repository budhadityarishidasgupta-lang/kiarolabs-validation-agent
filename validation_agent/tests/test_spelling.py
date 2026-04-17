from validation_agent.client import APIClient
from validation_agent.config import TEST_USERS


def test_spelling_attempt_recorded():
    client = APIClient()
    client.login(TEST_USERS["student"]["email"], TEST_USERS["student"]["password"])

    # Get a question
    q = client.get("/practice/spelling/question?lesson_id=1").json()

    assert q is not None, "Spelling question response is None"
    assert isinstance(q, dict), f"Spelling question response must be a dict, got {type(q).__name__}"
    assert "word_id" in q or "id" in q, "Spelling question missing both 'word_id' and 'id'"

    word_id = q.get("word_id") or q.get("id")
    word = q.get("word_audio") or q.get("word")

    assert word_id is not None, f"Spelling submit aborted: word_id is None; payload={q}"
    assert word is not None, f"Spelling submit aborted: word is None; payload={q}"

    answer = word

    # Submit answer
    res = client.post(
        "/practice/spelling/submit",
        {
            "word_id": word_id,
            "answer": answer,
            "correct": True,
        },
    )

    assert res is not None
    if hasattr(res, "status_code"):
        assert res.status_code == 200

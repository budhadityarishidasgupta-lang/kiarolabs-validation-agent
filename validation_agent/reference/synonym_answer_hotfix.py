from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel


router = APIRouter()


class SynonymAnswerPayload(BaseModel):
    word_id: int
    chosen: str
    response_ms: int


@router.post("/practice/synonym/answer")
def submit_synonym_answer(
    payload: SynonymAnswerPayload,
    current_user=Depends(...),
    connection=Depends(...),
):
    """
    Reference hotfix handler for production endpoint crashes.

    Notes:
    - This preserves schema/table names.
    - It validates required input values.
    - It safely handles missing rows and DB exceptions.
    """
    print("SUBMIT DEBUG:", payload.model_dump())

    if payload.word_id is None:
        raise HTTPException(status_code=400, detail="word_id is required")
    if payload.chosen is None:
        raise HTTPException(status_code=400, detail="chosen is required")

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, synonym
                FROM words
                WHERE id = %s
                """,
                (payload.word_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Word not found")

            # Supports cursor returning tuple or dict-like row.
            if isinstance(row, dict):
                correct_answer = row.get("synonym")
            else:
                # Query selects [id, synonym] in that order.
                correct_answer = row[1]

            is_correct = str(payload.chosen).strip().lower() == str(correct_answer).strip().lower()

            cursor.execute(
                """
                INSERT INTO words_attempts (user_id, word_id, correct, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (current_user.id, payload.word_id, is_correct, datetime.now(timezone.utc)),
            )

        connection.commit()
        return {"ok": True, "correct": is_correct}

    except HTTPException:
        raise
    except Exception as exc:
        print("SUBMIT ERROR:", repr(exc))
        raise HTTPException(status_code=500, detail="Failed to submit synonym answer")

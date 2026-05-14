from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from validation_agent.client import ApiClient, LoginContext
from validation_agent.reporting import TestResult


def _normalize_paper_code(value: str) -> str:
    cleaned = str(value or "").strip().upper().replace("_", "-")
    if cleaned.startswith("VR-P"):
        suffix = cleaned[4:]
    elif cleaned.startswith("VR-"):
        suffix = cleaned[3:]
    elif cleaned.startswith("VRP"):
        suffix = cleaned[3:]
    elif cleaned.startswith("VR"):
        suffix = cleaned[2:]
    else:
        suffix = cleaned
    suffix = suffix.lstrip("P")
    if not suffix.isdigit():
        raise ValueError(f"Unsupported paper code: {value!r}")
    return f"VR-P{int(suffix)}"


@dataclass(frozen=True)
class VrAnswerRow:
    paper_code: str
    question_number: int
    correct_answer: str


def load_vr_answer_keys(keys_dir: Path) -> dict[str, list[VrAnswerRow]]:
    if not keys_dir.exists():
        return {}

    grouped: dict[str, list[VrAnswerRow]] = defaultdict(list)
    for csv_path in sorted(keys_dir.glob("*.csv")):
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=2):
                paper_code = _normalize_paper_code(row.get("paper_code", ""))
                question_number = int(str(row.get("question_number", "")).strip())
                correct_answer = str(row.get("correct_answer", "")).strip().upper()
                if not correct_answer:
                    raise ValueError(f"{csv_path.name}:{index} missing correct_answer")
                grouped[paper_code].append(
                    VrAnswerRow(
                        paper_code=paper_code,
                        question_number=question_number,
                        correct_answer=correct_answer,
                    )
                )

    deduped: dict[str, list[VrAnswerRow]] = {}
    for paper_code, rows in grouped.items():
        unique_by_question = {row.question_number: row for row in rows}
        deduped[paper_code] = [unique_by_question[q] for q in sorted(unique_by_question)]
    return deduped


def _pick_submit_user(client: ApiClient, student_email: str | None, student_password: str | None, admin: LoginContext) -> LoginContext:
    if student_email and student_password:
        try:
            return client.login(student_email, student_password)
        except Exception:
            return admin
    return admin


def _first_wrong_answer(correct_answer: str) -> str:
    for option in ("A", "B", "C", "D", "E"):
        if option != correct_answer:
            return option
    return "A"


def run_vr_printable_validation(
    *,
    client: ApiClient,
    admin_email: str,
    admin_password: str,
    student_email: str | None,
    student_password: str | None,
    keys_dir: Path,
) -> list[TestResult]:
    answer_keys = load_vr_answer_keys(keys_dir)
    if not answer_keys:
        return [
            TestResult(
                test_id="test_vr_answer_keys_present",
                status="skip",
                message=f"No VR answer-key CSV files were found in {keys_dir}",
            )
        ]

    admin = client.login(admin_email, admin_password)
    submit_user = _pick_submit_user(client, student_email, student_password, admin)
    results: list[TestResult] = []

    for paper_code, expected_rows in answer_keys.items():
        expected_count = len(expected_rows)

        try:
            stored_payload = client.request_json(
                "GET",
                f"/admin/verbal-reasoning/printable/answers?paper_code={paper_code}",
                token=admin.token,
            )
            stored_answers = stored_payload.get("answers") or []
            stored_map = {
                int(row["question_number"]): str(row["correct_answer"]).strip().upper()
                for row in stored_answers
            }
            expected_map = {row.question_number: row.correct_answer for row in expected_rows}

            if stored_map != expected_map:
                missing = sorted(set(expected_map) - set(stored_map))
                extra = sorted(set(stored_map) - set(expected_map))
                mismatched = sorted(
                    q for q in set(expected_map) & set(stored_map) if expected_map[q] != stored_map[q]
                )
                results.append(
                    TestResult(
                        test_id=f"test_vr_db_answer_key_{paper_code}",
                        status="fail",
                        message=f"{paper_code}: stored answer key does not match the validation CSV",
                        details={
                            "expected_count": expected_count,
                            "stored_count": len(stored_map),
                            "missing_questions": missing[:10],
                            "extra_questions": extra[:10],
                            "mismatched_questions": mismatched[:10],
                        },
                    )
                )
                continue

            results.append(
                TestResult(
                    test_id=f"test_vr_db_answer_key_{paper_code}",
                    status="pass",
                    message=f"{paper_code}: stored answer key matches the validation CSV ({expected_count} questions)",
                )
            )

            question_payload = client.request_json(
                "GET",
                f"/practice/vr/questions?paper_code={paper_code}",
                token=submit_user.token,
            )
            question_numbers = [int(item) for item in (question_payload.get("questions") or [])]
            if question_numbers != [row.question_number for row in expected_rows]:
                results.append(
                    TestResult(
                        test_id=f"test_vr_question_count_{paper_code}",
                        status="fail",
                        message=f"{paper_code}: student-visible VR question list does not match the answer key count/order",
                        details={
                            "expected_questions": [row.question_number for row in expected_rows[:15]],
                            "actual_questions": question_numbers[:15],
                            "expected_count": expected_count,
                            "actual_count": len(question_numbers),
                        },
                    )
                )
                continue

            results.append(
                TestResult(
                    test_id=f"test_vr_question_count_{paper_code}",
                    status="pass",
                    message=f"{paper_code}: student-visible answer slots match the stored answer key ({expected_count})",
                )
            )

            perfect_payload = client.request_json(
                "POST",
                "/practice/vr/submit",
                token=submit_user.token,
                json={
                    "paper_code": paper_code,
                    "answers": [
                        {
                            "question_number": row.question_number,
                            "student_answer": row.correct_answer,
                        }
                        for row in expected_rows
                    ],
                },
            )
            score = int(perfect_payload.get("score") or -1)
            total = int(perfect_payload.get("total") or -1)
            if score != expected_count or total != expected_count:
                results.append(
                    TestResult(
                        test_id=f"test_vr_scoring_perfect_{paper_code}",
                        status="fail",
                        message=f"{paper_code}: perfect-answer submission did not produce a full score",
                        details={
                            "expected_score": expected_count,
                            "actual_score": score,
                            "actual_total": total,
                            "response": perfect_payload,
                        },
                    )
                )
                continue

            results.append(
                TestResult(
                    test_id=f"test_vr_scoring_perfect_{paper_code}",
                    status="pass",
                    message=f"{paper_code}: perfect-answer submission scored {expected_count}/{expected_count}",
                )
            )

            if expected_rows:
                wrong_rows = list(expected_rows)
                first = wrong_rows[0]
                wrong_payload = client.request_json(
                    "POST",
                    "/practice/vr/submit",
                    token=submit_user.token,
                    json={
                        "paper_code": paper_code,
                        "answers": [
                            {
                                "question_number": row.question_number,
                                "student_answer": _first_wrong_answer(row.correct_answer) if row.question_number == first.question_number else row.correct_answer,
                            }
                            for row in wrong_rows
                        ],
                    },
                )
                wrong_score = int(wrong_payload.get("score") or -1)
                expected_wrong_score = max(expected_count - 1, 0)
                if wrong_score != expected_wrong_score:
                    results.append(
                        TestResult(
                            test_id=f"test_vr_scoring_single_wrong_{paper_code}",
                            status="fail",
                            message=f"{paper_code}: one wrong answer did not reduce the score by exactly one",
                            details={
                                "expected_score": expected_wrong_score,
                                "actual_score": wrong_score,
                                "response": wrong_payload,
                            },
                        )
                    )
                    continue

                results.append(
                    TestResult(
                        test_id=f"test_vr_scoring_single_wrong_{paper_code}",
                        status="pass",
                        message=f"{paper_code}: one wrong answer reduced the score to {expected_wrong_score}/{expected_count}",
                    )
                )

        except Exception as exc:
            results.append(
                TestResult(
                    test_id=f"test_vr_validation_{paper_code}",
                    status="fail",
                    message=f"{paper_code}: VR validation raised an error",
                    details={"error": str(exc)},
                )
            )

    return results


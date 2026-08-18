from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ContentAnomaly:
    app: str
    item_id: str
    severity: str
    code: str
    message: str
    field: str | None = None
    expected: str | None = None
    actual: str | None = None


@dataclass
class ContentAuditReport:
    app: str
    source: str
    records_checked: int = 0
    passed_records: int = 0
    anomalies: list[ContentAnomaly] = field(default_factory=list)
    answer_distribution: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "app": self.app,
            "source": self.source,
            "records_checked": self.records_checked,
            "passed_records": self.passed_records,
            "failed_records": self.records_checked - self.passed_records,
            "answer_distribution": self.answer_distribution,
            "anomalies": [asdict(item) for item in self.anomalies],
        }


QUESTION_FIELDS = ("question_text", "question", "prompt", "headword")
ANSWER_FIELDS = ("correct_answer", "answer", "correct_word")
EXPLANATION_FIELDS = ("explanation", "answer_explanation", "feedback")
ID_FIELDS = ("question_id", "item_id", "id", "question_number")
OPTION_GROUPS = (
    ("option_a", "option_b", "option_c", "option_d", "option_e"),
    ("option_1", "option_2", "option_3", "option_4", "option_5"),
)


def _text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _first(record: dict[str, Any], names: Iterable[str]) -> tuple[str | None, str]:
    for name in names:
        if name in record and _text(record.get(name)):
            return name, _text(record.get(name))
    return None, ""


def _item_id(record: dict[str, Any], index: int) -> str:
    _, value = _first(record, ID_FIELDS)
    return value or str(index + 1)


def _options(record: dict[str, Any]) -> list[str]:
    raw = record.get("options")
    if isinstance(raw, list):
        return [_text(value) for value in raw]
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [_text(value) for value in parsed]
        except json.JSONDecodeError:
            pass
    for group in OPTION_GROUPS:
        if any(name in record for name in group):
            return [_text(record.get(name)) for name in group if name in record]
    return []


def _fingerprint(question: str, answer: str) -> str:
    normalized = re.sub(r"\s+", " ", f"{question}|{answer}".lower()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _answer_matches_options(answer: str, options: list[str]) -> bool:
    if not options:
        return True
    normalized = {value.lower() for value in options if value}
    if answer.lower() in normalized:
        return True
    if len(answer) == 1 and answer.upper() in "ABCDE":
        index = ord(answer.upper()) - ord("A")
        return 0 <= index < len(options) and bool(options[index])
    return False


def audit_records(records: list[dict[str, Any]], *, app: str, source: str = "memory") -> ContentAuditReport:
    report = ContentAuditReport(app=app, source=source, records_checked=len(records))
    fingerprints: dict[str, str] = {}
    answer_counts: Counter[str] = Counter()
    failed_ids: set[str] = set()

    def add(item_id: str, severity: str, code: str, message: str, **kwargs: Any) -> None:
        report.anomalies.append(ContentAnomaly(app, item_id, severity, code, message, **kwargs))
        if severity in {"CRITICAL", "HIGH"}:
            failed_ids.add(item_id)

    for index, record in enumerate(records):
        item_id = _item_id(record, index)
        question_field, question = _first(record, QUESTION_FIELDS)
        answer_field, answer = _first(record, ANSWER_FIELDS)
        explanation_field, explanation = _first(record, EXPLANATION_FIELDS)
        options = _options(record)

        if not question:
            add(item_id, "CRITICAL", "MISSING_QUESTION", "Question text is missing.", field=question_field)
        if not answer:
            add(item_id, "CRITICAL", "MISSING_ANSWER", "Correct answer is missing.", field=answer_field)
        else:
            answer_counts[answer.upper()] += 1

        if options:
            blanks = [str(i + 1) for i, value in enumerate(options) if not value]
            if blanks:
                add(item_id, "HIGH", "BLANK_OPTIONS", f"Blank option positions: {', '.join(blanks)}.")
            normalized = [value.lower() for value in options if value]
            if len(normalized) != len(set(normalized)):
                add(item_id, "HIGH", "DUPLICATE_OPTIONS", "Two or more displayed options are identical after normalization.")
            if answer and not _answer_matches_options(answer, options):
                add(item_id, "CRITICAL", "ANSWER_NOT_IN_OPTIONS", "Stored correct answer does not resolve to a displayed option.", actual=answer)

        if question and answer:
            fingerprint = _fingerprint(question, answer)
            previous = fingerprints.get(fingerprint)
            if previous is not None:
                add(item_id, "HIGH", "EXACT_DUPLICATE", f"Exact normalized question+answer duplicate of item {previous}.")
            else:
                fingerprints[fingerprint] = item_id

        if explanation_field is not None and not explanation:
            add(item_id, "MEDIUM", "EMPTY_EXPLANATION", "Explanation field exists but is empty.", field=explanation_field)
        elif explanation and answer and len(explanation) < 12:
            add(item_id, "MEDIUM", "WEAK_EXPLANATION", "Explanation is unusually short and should be reviewed.", actual=explanation)

        malformed = [value for value in options if re.search(r"[A-Za-z]+\d+|\d+[A-Za-z]+", value)]
        if malformed:
            add(item_id, "MEDIUM", "SUSPICIOUS_OPTION_TEXT", "Option text contains joined letters/numbers and may be malformed.", actual=" | ".join(malformed))

    report.answer_distribution = dict(answer_counts)
    report.passed_records = report.records_checked - len(failed_ids)

    total_answers = sum(answer_counts.values())
    if total_answers >= 20:
        answer, count = answer_counts.most_common(1)[0]
        ratio = count / total_answers
        if ratio >= 0.55:
            report.anomalies.append(ContentAnomaly(
                app, "BANK", "MEDIUM", "SUSPICIOUS_ANSWER_DISTRIBUTION",
                f"Answer {answer!r} occurs {count}/{total_answers} times ({ratio:.0%}); review bank randomisation/key integrity."
            ))

    return report


def _load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("questions", "items", "records"):
                if isinstance(payload.get(key), list):
                    return payload[key]
    raise ValueError(f"Unsupported content audit source: {path}")


def audit_content_file(path: str | Path, *, app: str) -> ContentAuditReport:
    source_path = Path(path)
    return audit_records(_load_records(source_path), app=app, source=str(source_path))

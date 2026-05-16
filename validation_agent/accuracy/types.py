from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

FindingStatus = Literal["PASS", "FAIL", "RISK", "NEEDS_REVIEW"]
FindingSeverity = Literal["low", "medium", "high", "critical"]
Owner = Literal["Codex", "Admin", "Content Review"]


@dataclass(frozen=True)
class AccuracyFinding:
    product: str
    lesson_or_paper_id: str
    question_id: str
    status: FindingStatus
    reason: str
    evidence: str
    suggested_human_review_note: str
    severity: FindingSeverity = "medium"
    recommended_owner: Owner = "Content Review"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ManusReviewTask:
    url: str
    login_role_needed: Literal["student", "admin"]
    product: str
    lesson_or_paper: str
    what_manus_should_inspect: str
    expected_behaviour: str
    screenshot_requirement: str
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AccuracyAuditReport:
    findings: list[AccuracyFinding] = field(default_factory=list)
    manus_tasks: list[ManusReviewTask] = field(default_factory=list)


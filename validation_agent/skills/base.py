from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SkillStatus = Literal["PASS", "FAIL", "RISK", "NEEDS_MANUAL_CHECK"]
VALID_SKILL_STATUSES: set[str] = {"PASS", "FAIL", "RISK", "NEEDS_MANUAL_CHECK"}


@dataclass
class SkillResult:
    status: SkillStatus
    skill_name: str
    summary: str
    details: list[str] = field(default_factory=list)
    files_checked: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in VALID_SKILL_STATUSES:
            raise ValueError(f"Invalid skill status: {self.status}")


class BaseSkill:
    skill_name: str = "Unnamed Skill"

    def run(self) -> SkillResult:
        raise NotImplementedError

    def result(
        self,
        *,
        status: SkillStatus,
        summary: str,
        details: list[str] | None = None,
        files_checked: list[str] | None = None,
        recommendations: list[str] | None = None,
    ) -> SkillResult:
        return SkillResult(
            status=status,
            skill_name=self.skill_name,
            summary=summary,
            details=details or [],
            files_checked=sorted(set(files_checked or [])),
            recommendations=recommendations or [],
        )

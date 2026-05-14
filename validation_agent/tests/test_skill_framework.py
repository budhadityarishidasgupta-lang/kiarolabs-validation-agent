import pytest

from validation_agent.skills.base import SkillResult


def test_skill_result_format_fields():
    result = SkillResult(
        status="PASS",
        skill_name="Example Skill",
        summary="All checks passed.",
        details=["check A"],
        files_checked=["/tmp/file.py"],
        recommendations=["No changes needed."],
    )
    assert result.status == "PASS"
    assert result.skill_name == "Example Skill"
    assert result.details == ["check A"]


def test_skill_result_rejects_invalid_status():
    with pytest.raises(ValueError):
        SkillResult(
            status="UNKNOWN",  # type: ignore[arg-type]
            skill_name="Broken Skill",
            summary="invalid",
        )

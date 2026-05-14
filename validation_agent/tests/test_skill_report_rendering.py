from validation_agent.reporting import write_skill_report
from validation_agent.skills.base import SkillResult


def test_report_renders_named_sections(tmp_path):
    report_path = write_skill_report(
        [
            SkillResult(status="PASS", skill_name="Architecture Guardrails", summary="ok"),
            SkillResult(status="FAIL", skill_name="Learning Integrity", summary="bad"),
        ],
        tmp_path,
    )
    text = report_path.read_text(encoding="utf-8")
    assert "## Architecture Guardrails" in text
    assert "## Learning Integrity" in text
    assert "## Purchase Flow" in text

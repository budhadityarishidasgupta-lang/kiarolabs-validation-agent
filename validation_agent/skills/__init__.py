from validation_agent.skills.architecture_guardrail_skill import ArchitectureGuardrailSkill
from validation_agent.skills.base import BaseSkill, SkillResult
from validation_agent.skills.brand_language_skill import BrandLanguageSkill
from validation_agent.skills.learning_integrity_skill import LearningIntegritySkill
from validation_agent.skills.manual_qa_skill import ManualQASkill
from validation_agent.skills.mock_security_skill import MockSecuritySkill
from validation_agent.skills.preview_access_skill import PreviewAccessSkill
from validation_agent.skills.printable_preview_skill import PrintablePreviewSkill
from validation_agent.skills.purchase_flow_skill import PurchaseFlowSkill


def build_skills() -> list[BaseSkill]:
    return [
        ArchitectureGuardrailSkill(),
        LearningIntegritySkill(),
        PreviewAccessSkill(),
        MockSecuritySkill(),
        PurchaseFlowSkill(),
        PrintablePreviewSkill(),
        BrandLanguageSkill(),
        ManualQASkill(),
    ]


def run_skill_suite() -> list[SkillResult]:
    return [skill.run() for skill in build_skills()]

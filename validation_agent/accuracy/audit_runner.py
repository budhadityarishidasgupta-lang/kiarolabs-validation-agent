from __future__ import annotations

from validation_agent.accuracy.admin_flow_skill import run_admin_flow_skill
from validation_agent.accuracy.antonym_accuracy_skill import run_antonym_accuracy_skill
from validation_agent.accuracy.compound_word_accuracy_skill import run_compound_word_accuracy_skill
from validation_agent.accuracy.context import AuditContext
from validation_agent.accuracy.entitlement_access_skill import run_entitlement_access_skill
from validation_agent.accuracy.math_accuracy_skill import run_math_accuracy_skill
from validation_agent.accuracy.printable_answer_key_skill import run_printable_answer_key_skill
from validation_agent.accuracy.spelling_accuracy_skill import run_spelling_accuracy_skill
from validation_agent.accuracy.synonym_accuracy_skill import run_synonym_accuracy_skill
from validation_agent.accuracy.types import AccuracyAuditReport, ManusReviewTask
from validation_agent.accuracy.verbal_reasoning_accuracy_skill import run_verbal_reasoning_accuracy_skill
from validation_agent.client import ApiClient
from validation_agent.config import Settings


def _build_manus_tasks(base_url: str) -> list[ManusReviewTask]:
    return [
        ManusReviewTask(
            url=f"{base_url}/online-practice",
            login_role_needed="student",
            product="MathSprint",
            lesson_or_paper="sample_lesson",
            what_manus_should_inspect="Math question rendering, options quality, and submit flow.",
            expected_behaviour="One deterministic correct answer after submit; no pre-submit answer leakage.",
            screenshot_requirement="Capture question card and post-submit feedback on anomalies.",
        ),
        ManusReviewTask(
            url=f"{base_url}/practice/session/wordsprint",
            login_role_needed="student",
            product="WordSprint",
            lesson_or_paper="synonym/antonym/compound",
            what_manus_should_inspect="Semantic correctness of options vs approved lesson intent.",
            expected_behaviour="Synonym lessons should not show antonyms as correct and vice versa.",
            screenshot_requirement="Capture failures with headword, options, and feedback panel visible.",
        ),
        ManusReviewTask(
            url=f"{base_url}/printable-papers",
            login_role_needed="student",
            product="Printable papers",
            lesson_or_paper="VR + Comprehension",
            what_manus_should_inspect="Purchased/Open/Upload workflow mapping per paper.",
            expected_behaviour="Only purchased active paper allows upload; Coming soon stays disabled.",
            screenshot_requirement="Capture card CTA states and upload screen entry behavior.",
        ),
        ManusReviewTask(
            url=f"{base_url}/admin",
            login_role_needed="admin",
            product="Admin flow",
            lesson_or_paper="purchase_tracking + curriculum",
            what_manus_should_inspect="Admin-only access, purchase trace visibility, and filter behavior.",
            expected_behaviour="Non-admin denied; admin can filter and export purchase events.",
            screenshot_requirement="Capture filters + table results + access-denied attempt for non-admin.",
        ),
    ]


def run_accuracy_audit(settings: Settings) -> AccuracyAuditReport:
    client: ApiClient | None = None
    admin_login = None
    student_login = None
    try:
        if settings.admin_email and settings.admin_password:
            client = ApiClient(settings.base_url, settings.request_timeout_seconds)
            admin_login = client.login(settings.admin_email, settings.admin_password)
            if settings.student_email and settings.student_password:
                student_login = client.login(settings.student_email, settings.student_password)
        ctx = AuditContext(
            base_url=settings.base_url,
            client=client,
            admin_login=admin_login,
            student_login=student_login,
        )
        findings = []
        findings.extend(run_math_accuracy_skill(ctx))
        findings.extend(run_spelling_accuracy_skill(ctx))
        findings.extend(run_synonym_accuracy_skill(ctx))
        findings.extend(run_antonym_accuracy_skill(ctx))
        findings.extend(run_compound_word_accuracy_skill(ctx))
        findings.extend(run_verbal_reasoning_accuracy_skill(ctx))
        findings.extend(run_printable_answer_key_skill(ctx, settings.vr_keys_dir))
        findings.extend(run_entitlement_access_skill(ctx))
        findings.extend(run_admin_flow_skill(ctx))
        manus_tasks = _build_manus_tasks(settings.base_url)
        return AccuracyAuditReport(findings=findings, manus_tasks=manus_tasks)
    finally:
        if client:
            client.close()


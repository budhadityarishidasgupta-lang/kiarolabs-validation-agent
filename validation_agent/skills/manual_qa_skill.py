from __future__ import annotations

from validation_agent.skills.base import BaseSkill


class ManualQASkill(BaseSkill):
    skill_name = "Manual QA"

    def run(self):
        checklist = [
            "Visitor reaches Q6 lock in Online Practice.",
            "Visitor reaches Q6 lock in Maths Mock.",
            "Paid user completes full practice lesson with no preview lock.",
            "Paid user completes full mock with scoring/timer intact.",
            "Printable 'View sample' modal opens correctly on desktop.",
            "Printable 'View sample' modal opens correctly on mobile.",
            "Gumroad purchase CTA opens the expected URL.",
            "Post-login purchase intent resumes to checkout correctly.",
            "No full paid PDF is accessible from sample modal links.",
        ]
        return self.result(
            status="NEEDS_MANUAL_CHECK",
            summary="Manual browser/environment QA is required for dynamic behaviors.",
            details=checklist,
            files_checked=[],
            recommendations=[
                "Run Playwright where credentials and stable preview fixtures are available.",
                "Capture screenshots/traces for lock-state and sample modal flows.",
            ],
        )

---
name: learning-loop
description: Use when validating the learner practice loop across dashboard, resume, engagement, and progress endpoints, especially for regressions that break continuity between sessions.
---

# Learning Loop

Use this skill when the validation target is the learner journey rather than a single endpoint.

## Focus

- Dashboard module readiness
- Resume continuity
- Engagement metrics
- Weekly improvement reporting

## Workflow

1. Log in as a student test user.
2. Check dashboard shape first.
3. Verify linked continuity endpoints:
   - `/practice/resume`
   - `/practice/engagement`
   - `/practice/progress/weekly-improvement`
4. Report whether the loop is:
   - healthy
   - partially degraded
   - broken

## Guardrails

- Keep checks lightweight and repeatable.
- Avoid assumptions about non-zero activity.
- Fail on contract breakage, invalid JSON, or auth regressions.

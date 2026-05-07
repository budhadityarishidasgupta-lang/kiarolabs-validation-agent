---
name: reporting-and-prompts
description: Use when summarizing validation findings into concise operator-ready reports or when drafting follow-up prompts for targeted runtime, backend, or UI investigation.
---

# Reporting And Prompts

Use this skill when validation output needs to be turned into a clear next-step artifact.

## Focus

- JSON and Markdown validation summaries
- Operator-readable failure framing
- Follow-up prompts for backend, frontend, or QA work

## Workflow

1. Preserve raw pass/fail outcomes from the runner.
2. Summarize failures by endpoint and contract area.
3. Distinguish:
   - auth failure
   - non-200 response
   - invalid JSON
   - missing required field
4. When drafting prompts, keep them scoped to one system and one objective.

## Guardrails

- Do not overstate certainty when a check is inconclusive.
- Keep prompts implementation-ready and minimal.
- Preserve compatibility with the existing report pipeline.

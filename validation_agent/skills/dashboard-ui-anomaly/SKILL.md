---
name: dashboard-ui-anomaly
description: Use when investigating dashboard UI regressions, mismatches between frontend rendering and backend dashboard payloads, or suspicious module/insight anomalies that need validation evidence.
---

# Dashboard UI Anomaly

Use this skill when dashboard behavior looks wrong in the UI and you need to confirm whether the backend contract or rendered state is the source.

## Focus

- Compare dashboard API payloads with expected UI behavior
- Look for missing module fields, malformed insight objects, or null handling issues
- Capture concrete evidence for follow-up fixes in product repos

## Workflow

1. Reproduce with a known test account.
2. Check `/dashboard` and related dashboard endpoints first.
3. Confirm whether the payload is valid before attributing the issue to the frontend.
4. Record:
   - endpoint
   - status code
   - missing or malformed fields
   - whether the issue is backend, frontend, or inconclusive

## Guardrails

- Keep the work read-only unless the user explicitly asks for code changes in this repo.
- Do not rewrite payload expectations to fit one-off UI bugs.
- Prefer actionable findings over vague anomaly descriptions.

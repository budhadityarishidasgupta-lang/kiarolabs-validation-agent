---
name: dashboard-contract
description: Use when validating the Kiarolabs backend dashboard API contract, including module payload shape and supporting read-only endpoints such as dashboard insights, engagement, weekly improvement, and resume.
---

# Dashboard Contract

Use this skill when the task is to verify backend dashboard responses without changing product code or writing data.

## Scope

- Read-only API validation against deployed environments
- Contract checks for `/dashboard`
- Supporting checks for:
  - `/dashboard/insights`
  - `/practice/engagement`
  - `/practice/progress/weekly-improvement`
  - `/practice/resume`

## Workflow

1. Authenticate with `TEST_USERS["student"]` unless the task explicitly needs another role.
2. `GET /dashboard` and assert valid JSON plus a `modules` object.
3. For each returned module under `modules`, validate the contract safely:
   - learning modules (`spelling`, `words`, `math`, `maths`, `comprehension`) require:
     - `unlocked`
     - `attempts`
     - `accuracy`
   - entitlement/access modules (`practice_papers`, `vr_printables`, `mock_exams`, `nvr`) require:
     - `unlocked`
   - unknown module keys should not fail immediately if `unlocked` is present
   - optional keys may exist without being required
4. Check supporting endpoints and fail only for:
   - non-200 responses where 200 is required
   - invalid JSON
   - missing required fields
5. Do not fail on legitimate zero values or empty-but-valid objects.

## Guardrails

- Do not write to production data.
- Do not mutate product repos.
- Keep checks tolerant of additive backend fields.
- Prefer shape validation over brittle exact-payload matching.

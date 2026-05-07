---
name: entitlement-ui
description: Use when validating whether unlocked, purchased, admin, or student entitlement states are represented correctly in Kiarolabs runtime responses and dashboard-facing UI behavior.
---

# Entitlement UI

Use this skill for access and unlock validation that affects what learners or admins can see and use.

## Focus

- Dashboard `unlocked` state
- Role-based access differences
- Purchased versus non-purchased behavior
- Admin override visibility

## Workflow

1. Choose the correct account role from `TEST_USERS`.
2. Validate the backend response first.
3. Confirm that entitlement-sensitive fields are present and JSON-safe.
4. Treat zero counts, empty progress, and fresh accounts as valid when the contract still holds.

## Guardrails

- Do not create or alter entitlements in production data.
- Prefer GET-only checks unless a separate task explicitly requires mutation tests.
- Separate access failures from content-shape failures in reporting.

---
name: wordsprint-runtime-validator
description: Use when validating deployed Kiarolabs runtime behavior after a deploy or before launch. Best for login checks, dashboard checks, entitlement verification, module smoke tests, and browser E2E confirmation. This skill maps to the live watchdog role and should focus on observable production behavior.
---

# WordSprint Runtime Validator

Use this skill for production or staging validation of the live system.

## Core stance

- Validate what users actually experience.
- Prefer repeatable checks over anecdotal browsing.
- Keep read-only checks as the default; use mutation lanes intentionally.
- Treat failures as either product bugs, environment bugs, or test bugs and separate those carefully.

## Validation areas

- login and session continuity
- dashboard load and key stats
- entitlement / access gating
- spelling question retrieval
- words submission flow
- maths practice / printable submission flow
- admin access and guarded admin mutations
- browser E2E health

## How to work

1. Read [references/architecture-rules.md](references/architecture-rules.md).
2. Start with the smallest runtime signal that answers the user’s question.
3. Use the existing validation-agent runners and test ordering when possible.
4. Read [references/safe-change-checklist.md](references/safe-change-checklist.md) before changing tests or validation wiring.
5. Distinguish:
   - failing product behavior
   - failing environment/deploy behavior
   - brittle or inaccurate tests

## Guardrails

- Do not mask a product bug by weakening assertions without saying so.
- Do not convert mutation tests into scheduled destructive checks.
- Do not assume test failures are user-visible regressions until confirmed.
- Keep validation evidence concrete: response codes, screenshots, traceable flows.

## Output shape

- what was checked
- what passed
- what failed
- whether the issue is product, deploy, or test harness
- next smallest fix

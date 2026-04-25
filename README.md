# Kiarolabs Validation Agent

`kiarolabs-validation-agent` is the right home for automated end-to-end and API smoke validation of the Kiarolabs stack.

It already knows how to exercise the deployed `kiarolabs-membership-service`, and this version makes it usable as a proactive watchdog:

- env-driven configuration
- structured JSON + Markdown reports
- CI-friendly exit codes
- suitable for scheduled GitHub Actions runs

## Why This Repo Should Own The Agent

This repo should live separately from `kiarolabs-membership-service` and `growth-leap-studio`.

Why:

- it tests the system from the outside like a real operator
- it can hit deployed environments without being bundled into app runtime
- it is the cleanest place to schedule autonomous validation
- it keeps audit/reporting logic decoupled from product code

`kiarolabs-question-audit-agent` should remain focused on schema/readiness audits.

`kiarolabs-validation-agent` should own:

- login smoke checks
- dashboard validation
- words/spelling/maths flow validation
- admin access validation
- printable maths submission validation
- future frontend-browser E2E expansion

## Project Layout

- `main.py`
- `validation_agent/config.py`
- `validation_agent/client.py`
- `validation_agent/runner.py`
- `validation_agent/reporting.py`
- `validation_agent/tests/`
- `reports/`

## Requirements

- Python 3.11+
- dependencies from `requirements.txt`

Install:

```bash
pip install -r requirements.txt
```

## Configuration

The agent reads configuration from environment variables.

### Required / recommended

```bash
VALIDATION_BASE_URL=https://kiarolabs-membership-service.onrender.com
VALIDATION_ADMIN_EMAIL=admin@example.com
VALIDATION_ADMIN_PASSWORD=secret
VALIDATION_TEST_ADMIN_EMAIL=testadmin@example.com
VALIDATION_TEST_ADMIN_PASSWORD=secret
VALIDATION_STUDENT_EMAIL=student@example.com
VALIDATION_STUDENT_PASSWORD=secret
```

### Optional

```bash
VALIDATION_REPORTS_DIR=reports
VALIDATION_FAIL_ON_FAILURE=true
VALIDATION_REQUEST_TIMEOUT_SECONDS=20
```

## How To Run

From the repo root:

```bash
python main.py
```

This will:

- run the smoke tests
- print pass/fail/skip output
- write:
  - `reports/validation-latest.json`
  - `reports/validation-latest.md`
- return non-zero if failures are found and `VALIDATION_FAIL_ON_FAILURE=true`

## Recommended Autonomous Mode

Use GitHub Actions on a schedule and on-demand.

Recommended cadence:

- every 4 hours for production smoke validation
- manual `workflow_dispatch` after deploys

The agent should:

1. run smoke tests
2. generate reports
3. fail the workflow on regressions
4. later notify Slack/email/GitHub issues if desired

## What It Covers Today

- auth
- password reset safety
- dashboard
- admin access
- maths practice submission
- maths mock tests
- spelling question retrieval
- words submission

## What To Add Next

To make this truly Chronos-like, next additions should be:

1. browser E2E via Playwright
2. endpoint inventory checks
3. printable admin management checks
4. comprehension upload checks
5. proactive alert routing

## Recommended Future Operating Model

Keep this repo as the autonomous validation watchdog.

- `question-audit-agent` = DB/schema/readiness
- `validation-agent` = runtime/API/E2E validation

That split is clean and scalable.

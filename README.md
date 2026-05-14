# Kiarolabs Validation Agent

`kiarolabs-validation-agent` is the right home for automated end-to-end and API smoke validation of the Kiarolabs stack.

It already knows how to exercise the deployed `kiarolabs-membership-service`, and this version makes it usable as a proactive watchdog:

- env-driven configuration
- structured JSON + Markdown reports
- CI-friendly exit codes
- suitable for scheduled GitHub Actions runs
- Playwright browser E2E against the live frontend

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
- frontend-browser E2E expansion

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

## Browser E2E

The repo now also includes a Playwright-based browser agent for the live frontend.

Install browser dependencies:

```bash
npm install
npx playwright install chromium
```

Set:

```bash
E2E_BASE_URL=https://kiarolabs.com
E2E_ADMIN_EMAIL=rishi@test.com
E2E_ADMIN_PASSWORD=your_password
```

Run:

```bash
npm run e2e
```

Current browser coverage:

- admin login
- `/admin` shell load
- curriculum tab render
- comprehension admin tab render

Artifacts:

- `playwright-report/`
- `test-results/`
- `reports/e2e-latest.json`

## Recommended Autonomous Mode

Use GitHub Actions on a schedule and on-demand.

Recommended cadence:

- every 4 hours for production smoke validation
- manual `workflow_dispatch` after deploys
- browser E2E twice daily or after deploys

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
- VR printable answer-key validation from CSV fixtures

## VR Printable Validation

The Python agent can now validate verbal reasoning printable papers end to end.

It works like this:

1. put the same CSV you upload through admin into:
   - `fixtures/vr-answer-keys/`
   - or a custom folder via `VALIDATION_VR_KEYS_DIR`
2. run `python main.py`
3. the agent will:
   - log in as admin
   - fetch the stored VR answer key from the backend
   - compare it with your CSV row by row
   - fetch the student-visible question count from `/practice/vr/questions`
   - submit a perfect attempt and expect a full score
   - submit a one-answer-wrong attempt and expect the score to drop by exactly one

Expected CSV format:

```csv
paper_code,question_number,correct_answer
VR-P3,1,B
VR-P3,2,B
VR-P3,3,C
```

This is the scalable path for more printable subjects too: each subject can get its own fixture folder plus a matching API validation module.

## What To Add Next

To make this truly Chronos-like, next additions should be:

1. printable admin management browser checks
2. comprehension upload browser checks
3. endpoint inventory checks
4. proactive alert routing
5. Slack or issue creation on repeated failures

## Recommended Future Operating Model

Keep this repo as the autonomous validation watchdog.

- `question-audit-agent` = DB/schema/readiness
- `validation-agent` = runtime/API/E2E validation

That split is clean and scalable.

## Skill-Based Validation Architecture

The validation agent now includes modular skill checks under:

- `validation_agent/skills/`
- `validation_agent/skill_config/`
- `reports/latest_report.md`

Each skill returns a shared result contract:

- `status`: `PASS | FAIL | RISK | NEEDS_MANUAL_CHECK`
- `skill_name`
- `summary`
- `details`
- `files_checked`
- `recommendations`

### Skill Responsibility Map

- Architecture Guardrails: detects SQL in frontend, cross-app access patterns, and authority-location risks.
- Learning Integrity: detects answer leaks and attempt-history overwrite signals.
- Preview Access: validates preview contract settings and static preview/full/locked handling signals.
- Mock Security: detects query-param spoof risks like `unlocked=true` trust.
- Purchase Flow: checks purchase baseline drift and purchase intent/redirect continuity signals.
- Printable Preview: scans sample asset metadata and potential full-PDF exposure risks.
- Brand Language: scans frontend copy for banned terms from config.
- Manual QA: emits required browser/runtime checklist items.

### Status Interpretation

- `PASS`: no violation detected by static checks.
- `FAIL`: clear regression/violation found.
- `RISK`: suspicious signal found that needs targeted review.
- `NEEDS_MANUAL_CHECK`: dynamic verification required or baseline not yet approved.

### Running The Agent

Run all checks and generate reports:

```bash
python main.py
```

Run only unit tests:

```bash
pytest -q validation_agent/tests
```

Generate purchase baseline candidate:

```bash
python -m validation_agent.skills.purchase_baseline
```

The validation agent reports issues; it does not auto-fix production code.

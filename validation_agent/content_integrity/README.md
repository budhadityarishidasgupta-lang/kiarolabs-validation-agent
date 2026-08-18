# Content Integrity Audit

Read-only learning-content auditing for Kiarolabs products.

## Safety boundary

- Audit one learning app at a time.
- Input is an app-specific CSV or JSON export.
- This package performs no database writes and no content repairs.
- It must not join, merge, or infer content across learning apps.
- Findings are reports only. Corrections must go through the owning app's approved CSV/admin ingestion process.

## Current checks

- missing question or correct answer
- blank or duplicate options
- correct answer not present in displayed options
- exact normalized question+answer duplicates
- empty/unusually weak explanations when an explanation field exists
- suspicious malformed option text
- suspiciously concentrated answer-key distribution

## Run

```bash
python -m validation_agent.content_integrity.cli --app spelling --source /path/to/spelling_export.csv --reports-dir reports
```

Use `--fail-on-high` in CI to return a non-zero exit code when CRITICAL/HIGH findings exist.

## Next adapters

App-specific read-only extractors must be implemented only after the owning repository/schema is inspected. Do not create generic cross-app learning tables or cross-app queries.

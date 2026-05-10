from pathlib import Path

from validation_agent.learning_integrity import describe_result


DEFAULT_CONSTRAINTS = [
    "no schema change unless explicitly required",
    "no auth/payment changes unless directly relevant",
    "no unrelated refactor",
    "preserve app isolation",
]


def _failure_profile(name: str, detail: str) -> dict:
    lowered = f"{name} {detail}".lower()

    if "dashboard deployment smoke" in lowered:
        return {
            "title": "Dashboard deployment smoke failure",
            "repo": "growth-leap-studio",
            "files": [
                "src/pages/Dashboard.tsx",
                "src/hooks/useDashboardData.ts",
            ],
            "expected_behavior": (
                "Dashboard should load without crashing, render key sections and status stats, "
                "and avoid console or failed-network errors during initial load."
            ),
            "prompt_focus": (
                "Inspect the dashboard page load path, data hook state handling, and render guards "
                "for missing/null data that could blank or crash the dashboard."
            ),
        }

    if "dashboard" in lowered or "insights" in lowered or "engagement" in lowered:
        return {
            "title": "Dashboard API contract validation failure",
            "repo": "kiarolabs-membership-service",
            "files": [
                "app/practice/router.py",
                "app/main.py",
            ],
            "expected_behavior": (
                "Dashboard endpoints should return HTTP 200 with JSON-safe payloads and the required "
                "module, insight, engagement, progress, or resume fields."
            ),
            "prompt_focus": (
                "Inspect only the dashboard and practice read endpoints involved in the failed contract "
                "check, and fix the missing field, invalid JSON, or non-200 response without broad refactors."
            ),
        }

    if "spelling_no_immediate_repeat" in lowered or "spelling anti-repeat" in lowered:
        return {
            "title": "Spelling anti-repeat validation failure",
            "repo": "kiarolabs-membership-service",
            "files": [
                "app/practice/spelling_engine.py",
                "app/practice/router.py",
            ],
            "expected_behavior": (
                "After a wrong spelling answer, the next spelling item in the same lesson should not "
                "repeat immediately when another lesson word is available."
            ),
            "prompt_focus": (
                "Inspect only the lesson-scoped spelling question selection and submission flow for "
                "immediate-repeat handling after incorrect attempts."
            ),
        }

    if "words_no_immediate_repeat" in lowered or "wordsprint repeat" in lowered or "synonym" in lowered:
        return {
            "title": "WordSprint anti-repeat validation failure",
            "repo": "kiarolabs-membership-service",
            "files": [
                "app/practice/synonym_engine.py",
                "app/practice/router.py",
            ],
            "expected_behavior": (
                "After a wrong WordSprint answer, the next lesson-scoped synonym item should not "
                "repeat immediately when another lesson word is available."
            ),
            "prompt_focus": (
                "Inspect only the lesson-based synonym session start and question selection path for "
                "immediate-repeat behavior after incorrect attempts."
            ),
        }

    if "comprehension_no_immediate_repeat" in lowered or "comprehension" in lowered:
        return {
            "title": "Comprehension anti-repeat validation failure",
            "repo": "kiarolabs-membership-service",
            "files": [
                "app/practice/router.py",
            ],
            "expected_behavior": (
                "After a wrong comprehension answer, the next question for the same passage should not "
                "repeat immediately when another passage question is available."
            ),
            "prompt_focus": (
                "Inspect only the passage-scoped comprehension question selection and answer flow "
                "for immediate-repeat handling."
            ),
        }

    return {
        "title": f"Validation failure: {name}",
        "repo": "kiarolabs-membership-service",
        "files": [
            "app/practice/router.py",
            "app/main.py",
        ],
        "expected_behavior": (
            "The validated endpoint or flow should satisfy the existing contract and return the expected "
            "response without runtime errors."
        ),
        "prompt_focus": (
            "Inspect only the code path directly related to the failing validation test and implement "
            "the minimal fix needed to satisfy the observed contract."
        ),
    }


def _build_prompt_block(result: dict) -> str:
    name = result.get("name", "unknown_failure")
    detail = result.get("detail", "") or ""
    profile = _failure_profile(name, detail)
    metadata = describe_result(name, result.get("status", "failed"), detail)
    severity = metadata["severity"]
    module = metadata["module"]

    files = profile["files"]
    files_text = ", ".join(f"`{path}`" for path in files) if files else "Unknown"
    constraints_text = "\n".join(f"- {item}" for item in DEFAULT_CONSTRAINTS)

    prompt = (
        f"Enhancement/fix assessment and implementation prompt.\n\n"
        f"Repo:\n{profile['repo']}\n\n"
        f"Observed failure:\n{name}: {detail}\n\n"
        f"Goal:\nRestore the expected behavior for this failing validation check only.\n\n"
        f"Expected behavior:\n{profile['expected_behavior']}\n\n"
        f"Likely files:\n{files_text}\n\n"
        f"Instructions:\n{profile['prompt_focus']}\n\n"
        f"Safety constraints:\n{constraints_text}"
    )

    lines = [
        f"## {profile['title']}",
        "",
        f"- Title: `{profile['title']}`",
        f"- Severity: `{severity}`",
        f"- Module: `{module}`",
        f"- Likely repo: `{profile['repo']}`",
        f"- Likely files: {files_text}",
        f"- Observed failure: `{name}: {detail}`",
        f"- Expected behavior: {profile['expected_behavior']}",
        "",
        "### Narrow Codex Prompt",
        "",
        "```text",
        prompt,
        "```",
        "",
        "### Safety Constraints",
        "",
        constraints_text,
        "",
    ]
    return "\n".join(lines)


def write_fix_prompts_report(report: dict, reports_dir: Path) -> Path | None:
    findings = [
        result for result in report.get("results", [])
        if result.get("status") in {"failed", "warned"}
    ]
    if not findings:
        return None

    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "fix-prompts-latest.md"

    lines = [
        "# Validation Fix Prompts",
        "",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Finding count: `{len(findings)}`",
        "",
        "Use these prompts to create focused follow-up work in the likely repo without broad refactors.",
        "",
    ]

    for failure in findings:
        lines.append(_build_prompt_block(failure))

    path.write_text("\n".join(lines), encoding="utf-8")
    return path

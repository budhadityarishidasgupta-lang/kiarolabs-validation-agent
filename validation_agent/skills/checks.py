from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".tmp-pydeps",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    "playwright-report",
    "test-results",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def workspace_root() -> Path:
    return repo_root().parent


def get_scan_roots() -> list[Path]:
    root = workspace_root()
    candidates = [
        root / "app",
        root / "growth-leap-studio",
        root / "kiarolabs-membership-service",
        repo_root() / "e2e",
    ]
    return [path for path in candidates if path.exists()]


def iter_source_files(
    roots: list[Path],
    *,
    extensions: tuple[str, ...] = (
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".md",
        ".yaml",
        ".yml",
    ),
    excluded_dirs: set[str] | None = None,
) -> list[Path]:
    excluded = DEFAULT_EXCLUDED_DIRS | (excluded_dirs or set())
    files: list[Path] = []
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in excluded for part in path.parts):
                continue
            if path.suffix.lower() in extensions:
                files.append(path)
    return files


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def find_regex_occurrences(
    files: list[Path],
    patterns: list[re.Pattern[str]],
) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for file_path in files:
        text = safe_read_text(file_path)
        for index, line in enumerate(text.splitlines(), start=1):
            for pattern in patterns:
                if pattern.search(line):
                    hits.append((file_path, index, line.strip()))
                    break
    return hits


def format_hit(path: Path, line: int, content: str) -> str:
    return f"{path}:{line} -> {content}"


def load_simple_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data: dict = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith("  ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = _normalize_scalar(value)
                current_key = None
            else:
                data[key] = []
                current_key = key
            continue
        if current_key and line.lstrip().startswith("- "):
            item = line.lstrip()[2:].strip()
            cast = _normalize_scalar(item)
            if isinstance(data[current_key], list):
                data[current_key].append(cast)
    return data


def _normalize_scalar(value: str) -> str | int:
    value = value.strip().strip("'").strip('"')
    if value.isdigit():
        return int(value)
    return value


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def detect_unlocked_query_param_trust(text: str) -> bool:
    unlocked_reads = re.search(r"get\(['\"]unlocked['\"]\)", text, re.IGNORECASE)
    if not unlocked_reads:
        return False
    risky_assignments = re.search(
        r"(isFull|fullAccess|hasAccess|isUnlocked)\s*=\s*.*unlocked",
        text,
        re.IGNORECASE,
    )
    return bool(risky_assignments)


def looks_like_full_paid_pdf(url_or_path: str) -> bool:
    lower = url_or_path.lower()
    if ".pdf" not in lower:
        return False
    if any(token in lower for token in ("sample", "preview", "excerpt", "demo")):
        return False
    return True


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s\"'`)>]+", text)

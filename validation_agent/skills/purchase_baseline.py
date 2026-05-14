from __future__ import annotations

import json

from validation_agent.skills.checks import extract_urls, get_scan_roots, iter_source_files, safe_read_text


def generate_purchase_baseline() -> dict:
    files = iter_source_files(
        get_scan_roots(),
        extensions=(".ts", ".tsx", ".js", ".jsx", ".py", ".json"),
    )
    urls: set[str] = set()
    for path in files:
        text = safe_read_text(path)
        if "gumroad" not in text.lower() and "purchase" not in text.lower():
            continue
        for url in extract_urls(text):
            if "gumroad.com" in url.lower() or "purchase" in url.lower():
                urls.add(url)
    return {
        "status": "NEEDS_MANUAL_CHECK",
        "note": "Review and approve initial purchase URL baseline before treating drift checks as PASS.",
        "purchase_urls": sorted(urls),
    }


if __name__ == "__main__":
    print(json.dumps(generate_purchase_baseline(), indent=2))

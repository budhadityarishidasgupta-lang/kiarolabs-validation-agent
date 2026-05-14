from validation_agent.skills.brand_language_skill import find_banned_term_hits


def test_banned_language_detection(tmp_path):
    ui_file = tmp_path / "Banner.tsx"
    ui_file.write_text('const cta = "Limited offer available now";', encoding="utf-8")

    hits = find_banned_term_hits(
        [ui_file],
        banned_terms=["limited offer", "sale"],
        allowlist=set(),
    )
    assert hits
    assert "Limited offer" in hits[0][2]


def test_comment_lines_are_ignored(tmp_path):
    ui_file = tmp_path / "Banner.tsx"
    ui_file.write_text("// subscription info appears in developer comment only", encoding="utf-8")
    hits = find_banned_term_hits(
        [ui_file],
        banned_terms=["subscription"],
        allowlist=set(),
    )
    assert hits == []

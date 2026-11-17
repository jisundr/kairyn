"""The human-readable budget report is generated from budgets.yml and current file sizes."""
from datetime import datetime, timezone
from pathlib import Path

from budgets import Budget
from budgets_html import render_html, write_html
from helpers import ROOT

BUDGETS = [
    Budget("CLAUDE.md", 100, "always"),
    Budget("plugin/stages/*.md", 50, "runtime"),
    Budget("*.md", 200, "on-demand"),
]
NOW = datetime(2026, 11, 17, 6, 0, 0, tzinfo=timezone.utc)


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def html_for(tmp_path, files):
    for rel, size in files.items():
        write(tmp_path, rel, "x" * size)
    return render_html(tmp_path, BUDGETS, generated=NOW)


def test_is_a_complete_self_contained_document(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 200})
    assert html.startswith("<!doctype html>")
    assert "<title>" in html
    assert "http://" not in html and "https://" not in html   # no external resources
    assert "<script src" not in html


def test_lists_each_file_with_usage_and_class(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 200, "a.md": 360})
    assert "CLAUDE.md" in html and "50 / 100" in html and "always" in html
    assert "a.md" in html and "90 / 200" in html and "on-demand" in html


def test_most_used_file_comes_first(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 200, "a.md": 360})   # 50% vs 45%
    assert html.index("CLAUDE.md</") < html.index("a.md</")


def test_over_budget_file_is_flagged(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 404})   # 101 / 100
    assert 'class="over"' in html and "over by 1" in html


def test_within_budget_file_is_not_flagged(tmp_path):
    assert 'class="over"' not in html_for(tmp_path, {"CLAUDE.md": 400})


def test_unbudgeted_file_is_flagged(tmp_path):
    html = render_html(_tree(tmp_path, {"docs/new.md": 8}), [Budget("CLAUDE.md", 100, "always")], generated=NOW)
    assert "docs/new.md" in html and "no budget" in html


def _tree(root, files):
    for rel, size in files.items():
        write(root, rel, "x" * size)
    return root


def test_file_names_are_escaped(tmp_path):
    html = html_for(tmp_path, {"x&y.md": 40})
    assert "x&amp;y.md" in html and "x&y.md" not in html


def test_totals_per_load_class(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 200, "a.md": 360, "b.md": 40})
    assert "Always loaded" in html and "50" in html          # CLAUDE.md
    assert "On demand" in html and "100" in html            # 90 + 10


def test_budget_rules_are_listed_in_order(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 4})
    assert html.index("plugin/stages/*.md") < html.index("*.md</code>")
    assert "first match wins" in html.lower()


def test_states_its_source_and_generation_time(tmp_path):
    html = html_for(tmp_path, {"CLAUDE.md": 4})
    assert ".harness/budgets.yml" in html and "2026-11-17 06:00 UTC" in html


def test_supports_light_and_dark(tmp_path):
    assert "prefers-color-scheme: dark" in html_for(tmp_path, {"CLAUDE.md": 4})


def test_write_html_creates_the_file(tmp_path):
    write(tmp_path, "CLAUDE.md", "x" * 4)
    out = tmp_path / "out" / "budgets.html"
    write_html(tmp_path, BUDGETS, out, generated=NOW)
    assert out.read_text().startswith("<!doctype html>")


def test_real_repo_renders_without_errors():
    from budgets import load_budgets
    html = render_html(ROOT, load_budgets(ROOT / ".harness" / "budgets.yml"), generated=NOW)
    assert "CLAUDE.md" in html and "plugin/stages/REQUIREMENTS.md" in html

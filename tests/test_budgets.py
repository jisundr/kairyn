"""Size budgets keep the files an AI reads lean."""
from pathlib import Path

import pytest

from budgets import budget_for, check, estimate_tokens, find_docs, load_budgets, report
from helpers import ROOT

BUDGETS = [("CLAUDE.md", 100), ("plugin/stages/*.md", 50), ("*.md", 200)]


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# --- estimate_tokens ---------------------------------------------------------

def test_estimate_is_chars_divided_by_four_rounded_up():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2


# --- load_budgets ------------------------------------------------------------

def test_load_budgets_reads_pattern_and_limit(tmp_path):
    cfg = tmp_path / "budgets.yml"
    cfg.write_text("budgets:\n  - {pattern: CLAUDE.md, max_tokens: 700}\n  - {pattern: '*.md', max_tokens: 900}\n")
    assert load_budgets(cfg) == [("CLAUDE.md", 700), ("*.md", 900)]


def test_load_budgets_rejects_bad_entries(tmp_path):
    cfg = tmp_path / "budgets.yml"
    cfg.write_text("budgets:\n  - {pattern: CLAUDE.md}\n")
    with pytest.raises(ValueError):
        load_budgets(cfg)


# --- budget_for --------------------------------------------------------------

def test_first_matching_pattern_wins():
    assert budget_for("CLAUDE.md", BUDGETS) == 100
    assert budget_for("plugin/stages/X.md", BUDGETS) == 50
    assert budget_for("other.md", BUDGETS) == 200


def test_no_match_returns_none():
    assert budget_for("notes.txt", BUDGETS) is None


# --- find_docs ---------------------------------------------------------------

def test_find_docs_lists_markdown_and_skips_generated_dirs(tmp_path):
    for rel in ("CLAUDE.md", "plugin/stages/A.md", ".venv/lib/x.md", "evals/results/r/x.md", ".git/y.md", "notes.txt"):
        write(tmp_path, rel, "x")
    assert find_docs(tmp_path) == ["CLAUDE.md", "plugin/stages/A.md"]


# --- check -------------------------------------------------------------------

def test_files_within_budget_pass(tmp_path):
    write(tmp_path, "CLAUDE.md", "x" * 400)  # exactly 100 tokens
    assert check(tmp_path, BUDGETS) == []


def test_file_over_budget_is_reported_with_numbers(tmp_path):
    write(tmp_path, "CLAUDE.md", "x" * 404)  # 101 tokens
    [problem] = check(tmp_path, BUDGETS)
    assert "CLAUDE.md" in problem and "101" in problem and "100" in problem


def test_unbudgeted_file_is_a_problem(tmp_path):
    write(tmp_path, "docs/new.md", "hello")
    [problem] = check(tmp_path, [("CLAUDE.md", 100)])
    assert "docs/new.md" in problem and "no budget" in problem


def test_report_shows_usage_most_used_first(tmp_path):
    write(tmp_path, "CLAUDE.md", "x" * 200)   # 50 / 100
    write(tmp_path, "a.md", "x" * 360)        # 90 / 200 -> 45%
    lines = report(tmp_path, BUDGETS)
    assert "CLAUDE.md" in lines[0] and "50/100" in lines[0]
    assert "a.md" in lines[1] and "90/200" in lines[1]


# --- the real repo -----------------------------------------------------------

def test_repo_files_are_within_budget():
    budgets = load_budgets(ROOT / ".harness" / "budgets.yml")
    assert check(ROOT, budgets) == [], "run: uv run python tools/budgets.py"

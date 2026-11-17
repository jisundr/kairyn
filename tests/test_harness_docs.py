"""Harness docs: every doc has a header an agent can read without opening the body,
and the index tables built from those headers never drift."""
from pathlib import Path

import pytest

from harness_docs import (
    check,
    collect,
    doc_problems,
    read_meta,
    render_claude_table,
    render_readme_table,
    replace_block,
    sync,
)
from budgets import budget_for, load_budgets
from helpers import ROOT

GOOD = """---
title: Testing and evals
summary: How to run tests and evals.
read_when: running or writing tests or evals
load: on-demand
---

# Testing and evals
"""


def make_doc(path: Path, text: str = GOOD) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


# --- header parsing and validation -------------------------------------------

def test_read_meta_parses_front_matter(tmp_path):
    meta = read_meta(make_doc(tmp_path / "a.md"))
    assert meta == {"title": "Testing and evals", "summary": "How to run tests and evals.",
                    "read_when": "running or writing tests or evals", "load": "on-demand"}


def test_read_meta_without_front_matter_is_none(tmp_path):
    assert read_meta(make_doc(tmp_path / "a.md", "# just a heading\n")) is None


def test_valid_doc_has_no_problems(tmp_path):
    path = make_doc(tmp_path / "a.md")
    assert doc_problems(path, read_meta(path)) == []


def test_missing_header_is_a_problem(tmp_path):
    path = make_doc(tmp_path / "a.md", "# no header\n")
    assert any("front matter" in p for p in doc_problems(path, read_meta(path)))


@pytest.mark.parametrize("key", ["title", "summary", "read_when", "load"])
def test_missing_key_is_a_problem(tmp_path, key):
    text = "\n".join(line for line in GOOD.splitlines() if not line.startswith(f"{key}:")) + "\n"
    path = make_doc(tmp_path / "a.md", text)
    assert any(key in p for p in doc_problems(path, read_meta(path)))


def test_empty_value_is_a_problem(tmp_path):
    path = make_doc(tmp_path / "a.md", GOOD.replace("summary: How to run tests and evals.", "summary: "))
    assert any("summary" in p for p in doc_problems(path, read_meta(path)))


def test_unknown_load_class_is_a_problem(tmp_path):
    path = make_doc(tmp_path / "a.md", GOOD.replace("load: on-demand", "load: sometimes"))
    assert any("load" in p for p in doc_problems(path, read_meta(path)))


def test_long_summary_is_a_problem(tmp_path):
    path = make_doc(tmp_path / "a.md", GOOD.replace("How to run tests and evals.", "x" * 161))
    assert any("160" in p for p in doc_problems(path, read_meta(path)))


# --- rendering ---------------------------------------------------------------

def entries(tmp_path):
    root = tmp_path
    make_doc(root / ".harness" / "README.md", GOOD.replace("Testing and evals", "Harness").replace("running or writing tests or evals", "needing the repo layout"))
    make_doc(root / ".harness" / "workflows" / "b.md", GOOD.replace("running or writing tests or evals", "editing a stage"))
    make_doc(root / ".harness" / "workflows" / "a.md")
    return root, collect(root)


def test_collect_puts_readme_first_then_workflows_sorted(tmp_path):
    root, found = entries(tmp_path)
    assert [p.relative_to(root).as_posix() for p, _ in found] == [
        ".harness/README.md", ".harness/workflows/a.md", ".harness/workflows/b.md"]


def test_tables_list_only_on_demand_docs(tmp_path):
    root, _ = entries(tmp_path)
    make_doc(root / ".harness" / "workflows" / "z.md", GOOD.replace("load: on-demand", "load: runtime").replace("running or writing tests or evals", "never listed"))
    found = collect(root)
    assert "never listed" not in render_claude_table(found, root)
    assert "never listed" not in render_readme_table(found, root)


def test_claude_table_lists_read_when_and_path(tmp_path):
    root, found = entries(tmp_path)
    table = render_claude_table(found, root)
    assert "| When you are... | Read |" in table
    assert "| needing the repo layout | `.harness/README.md` |" in table
    assert "| editing a stage | `.harness/workflows/b.md` |" in table


def test_readme_table_links_workflows_only(tmp_path):
    root, found = entries(tmp_path)
    table = render_readme_table(found, root)
    assert "[Testing and evals](workflows/a.md) | running or writing tests or evals |" in table
    assert "README.md" not in table


# --- replace_block -----------------------------------------------------------

BLOCK = "intro\n<!-- harness-docs:start -->\nold\n<!-- harness-docs:end -->\noutro\n"


def test_replace_block_swaps_only_the_marked_region():
    out = replace_block(BLOCK, "new")
    assert out == "intro\n<!-- harness-docs:start -->\nnew\n<!-- harness-docs:end -->\noutro\n"


def test_replace_block_is_idempotent():
    once = replace_block(BLOCK, "new")
    assert replace_block(once, "new") == once


def test_replace_block_requires_markers():
    with pytest.raises(ValueError):
        replace_block("no markers here\n", "new")


# --- sync / check ------------------------------------------------------------

def repo_with_indexes(tmp_path):
    root, _ = entries(tmp_path)
    (root / "CLAUDE.md").write_text(BLOCK)
    (root / ".harness" / "README.md").write_text(
        GOOD.replace("Testing and evals", "Harness").replace("running or writing tests or evals", "needing the repo layout")
        + "\n" + BLOCK)
    return root


def test_check_reports_out_of_sync_indexes(tmp_path):
    root = repo_with_indexes(tmp_path)
    problems = check(root)
    assert any("CLAUDE.md" in p for p in problems)
    assert any("README.md" in p for p in problems)


def test_sync_makes_check_pass(tmp_path):
    root = repo_with_indexes(tmp_path)
    sync(root)
    assert check(root) == []


def test_check_reports_doc_with_bad_header(tmp_path):
    root = repo_with_indexes(tmp_path)
    sync(root)
    make_doc(root / ".harness" / "workflows" / "c.md", "# no header\n")
    assert any("c.md" in p for p in check(root))


# --- the real repo -----------------------------------------------------------

def test_repo_docs_are_valid_and_indexes_in_sync():
    assert check(ROOT) == [], "run: uv run python plugin/scripts/harness_docs.py --write"


def test_header_load_class_matches_budgets_yml():
    """One fact, two places: the header an AI reads and the budget config must agree."""
    budgets = load_budgets(ROOT / ".harness" / "budgets.yml")
    for path, meta in collect(ROOT):
        rel = path.relative_to(ROOT).as_posix()
        assert budget_for(rel, budgets).load == meta["load"], f"{rel}: header and budgets.yml disagree on load class"


def test_cli_checks_the_given_root(tmp_path):
    import subprocess, sys
    from helpers import PLUGIN
    root = repo_with_indexes(tmp_path)
    cmd = [sys.executable, str(PLUGIN / "scripts" / "harness_docs.py"), "--root", str(root)]
    assert subprocess.run(cmd, capture_output=True, text=True).returncode == 1          # stale indexes
    assert subprocess.run(cmd + ["--write"], capture_output=True, text=True).returncode == 0
    assert subprocess.run(cmd, capture_output=True, text=True).returncode == 0

"""Size budgets keep the files an AI reads lean."""
from pathlib import Path

import pytest

from budgets import LOAD_CLASSES, Budget, budget_for, check, estimate_tokens, find_docs, load_budgets, report
from helpers import ROOT

BUDGETS = [
    Budget("CLAUDE.md", 100, "always"),
    Budget("plugin/stages/*.md", 50, "runtime"),
    Budget("*.md", 200, "on-demand"),
]


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
    cfg.write_text("budgets:\n  - {pattern: CLAUDE.md, max_tokens: 700, load: always}\n  - {pattern: '*.md', max_tokens: 900, load: on-demand}\n")
    assert load_budgets(cfg) == [Budget("CLAUDE.md", 700, "always"), Budget("*.md", 900, "on-demand")]


def test_load_budgets_rejects_bad_entries(tmp_path):
    cfg = tmp_path / "budgets.yml"
    cfg.write_text("budgets:\n  - {pattern: CLAUDE.md, load: always}\n")
    with pytest.raises(ValueError):
        load_budgets(cfg)


def test_load_budgets_rejects_unknown_load_class(tmp_path):
    cfg = tmp_path / "budgets.yml"
    cfg.write_text("budgets:\n  - {pattern: CLAUDE.md, max_tokens: 700, load: sometimes}\n")
    with pytest.raises(ValueError, match="load"):
        load_budgets(cfg)


def test_load_classes_are_the_documented_set():
    assert LOAD_CLASSES == ("always", "on-demand", "runtime")


# --- budget_for --------------------------------------------------------------

def test_first_matching_pattern_wins():
    assert budget_for("CLAUDE.md", BUDGETS) == Budget("CLAUDE.md", 100, "always")
    assert budget_for("plugin/stages/X.md", BUDGETS).max_tokens == 50
    assert budget_for("other.md", BUDGETS).load == "on-demand"


def test_no_match_returns_none():
    assert budget_for("notes.txt", BUDGETS) is None


# --- find_docs ---------------------------------------------------------------

def test_find_docs_lists_markdown_and_skips_generated_dirs(tmp_path):
    for rel in ("CLAUDE.md", "plugin/stages/A.md", ".venv/lib/x.md", "evals/results/r/x.md", ".git/y.md", "notes.txt"):
        write(tmp_path, rel, "x")
    assert find_docs(tmp_path) == ["CLAUDE.md", "plugin/stages/A.md"]


def test_find_docs_skips_claude_code_worktrees(tmp_path):
    for rel in ("CLAUDE.md", ".claude/worktrees/w1/CLAUDE.md", ".claude/worktrees/w1/plugin/stages/A.md",
                ".claude/commands/c.md"):
        write(tmp_path, rel, "x")
    assert find_docs(tmp_path) == [".claude/commands/c.md", "CLAUDE.md"]


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
    [problem] = check(tmp_path, [Budget("CLAUDE.md", 100, "always")])
    assert "docs/new.md" in problem and "no budget" in problem


def test_report_shows_usage_most_used_first(tmp_path):
    write(tmp_path, "CLAUDE.md", "x" * 200)   # 50 / 100
    write(tmp_path, "a.md", "x" * 360)        # 90 / 200 -> 45%
    lines = report(tmp_path, BUDGETS)
    assert "CLAUDE.md" in lines[0] and "50/100" in lines[0] and "always" in lines[0]
    assert "a.md" in lines[1] and "90/200" in lines[1] and "on-demand" in lines[1]


# --- the real repo -----------------------------------------------------------

def test_repo_files_are_within_budget():
    budgets = load_budgets(ROOT / ".harness" / "budgets.yml")
    assert check(ROOT, budgets) == [], "run: uv run python plugin/scripts/budgets.py"


# --- strict mode and CLI (consumer repos) ------------------------------------

import subprocess
import sys

from budgets import load_config
from helpers import PLUGIN


def test_config_defaults_to_strict(tmp_path):
    cfg = tmp_path / "budgets.yml"
    cfg.write_text("budgets:\n  - {pattern: CLAUDE.md, max_tokens: 700, load: always}\n")
    budgets, strict = load_config(cfg)
    assert strict is True and budgets == [Budget("CLAUDE.md", 700, "always")]


def test_config_can_turn_strict_off(tmp_path):
    cfg = tmp_path / "budgets.yml"
    cfg.write_text("strict: false\nbudgets:\n  - {pattern: CLAUDE.md, max_tokens: 700, load: always}\n")
    assert load_config(cfg)[1] is False


def test_non_strict_ignores_unbudgeted_files_but_still_enforces_budgeted_ones(tmp_path):
    write(tmp_path, "docs/anything.md", "x" * 4000)     # unbudgeted: ignored
    write(tmp_path, "CLAUDE.md", "x" * 404)             # budgeted and over: reported
    problems = check(tmp_path, [Budget("CLAUDE.md", 100, "always")], strict=False)
    assert len(problems) == 1 and "CLAUDE.md" in problems[0]


def run_cli(*args):
    return subprocess.run([sys.executable, str(PLUGIN / "scripts" / "budgets.py"), *args], capture_output=True, text=True)


def test_cli_checks_the_given_root(tmp_path):
    (tmp_path / ".harness").mkdir()
    (tmp_path / ".harness" / "budgets.yml").write_text("budgets:\n  - {pattern: CLAUDE.md, max_tokens: 1, load: always}\n")
    write(tmp_path, "CLAUDE.md", "x" * 40)
    result = run_cli("--root", str(tmp_path))
    assert result.returncode == 1 and "over by" in result.stdout


def test_cli_passes_on_a_clean_root(tmp_path):
    (tmp_path / ".harness").mkdir()
    (tmp_path / ".harness" / "budgets.yml").write_text("budgets:\n  - {pattern: CLAUDE.md, max_tokens: 100, load: always}\n")
    write(tmp_path, "CLAUDE.md", "x" * 40)
    result = run_cli("--root", str(tmp_path))
    assert result.returncode == 0 and "OK" in result.stdout


# --- fallback budgets for files kairyn installs (consumer repos with a strict budgets.yml) ---

from budgets import FALLBACK_BUDGETS, with_fallbacks

STRICT_CLAUDE_ONLY = "budgets:\n  - {pattern: CLAUDE.md, max_tokens: 2000, load: always}\n"


def test_fallbacks_come_after_the_users_patterns():
    user = [Budget(".kairyn/learnings.md", 10, "runtime")]
    merged = with_fallbacks(user)
    assert merged[0] == user[0] and merged[1:] == FALLBACK_BUDGETS
    assert budget_for(".kairyn/learnings.md", merged).max_tokens == 10   # the user's limit wins


def test_fallbacks_cover_every_markdown_file_init_installs(tmp_path):
    from helpers import make_good_repo
    repo = make_good_repo(tmp_path / "repo")
    write(repo, "docs/tasks/2026-01-01-x/STATE.md", "x")
    unbudgeted = [rel for rel in find_docs(repo) if rel != "CLAUDE.md" and budget_for(rel, FALLBACK_BUDGETS) is None]
    assert unbudgeted == []


def test_find_docs_skips_the_upgrade_base_copies(tmp_path):
    write(tmp_path, ".kairyn/.base/.kairyn/stages/A.md", "x")
    write(tmp_path, ".kairyn/stages/A.md", "x")
    assert find_docs(tmp_path) == [".kairyn/stages/A.md"]


def test_cli_passes_after_init_in_a_repo_with_a_strict_budgets_yml(tmp_path):
    from helpers import make_good_repo
    repo = tmp_path / "repo"
    write(repo, ".harness/budgets.yml", STRICT_CLAUDE_ONLY)
    make_good_repo(repo)
    write(repo, "docs/tasks/2026-01-01-x/STATE.md", "x")
    result = run_cli("--root", str(repo))
    assert result.returncode == 0, result.stdout


def test_cli_still_enforces_fallback_limits(tmp_path):
    write(tmp_path, ".harness/budgets.yml", STRICT_CLAUDE_ONLY)
    write(tmp_path, ".kairyn/stages/BIG.md", "x" * 4000)
    result = run_cli("--root", str(tmp_path))
    assert result.returncode == 1 and ".kairyn/stages/BIG.md" in result.stdout and "over by" in result.stdout

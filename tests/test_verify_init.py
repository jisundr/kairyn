"""verify-init.sh accepts a correct layout and rejects broken ones."""
import shutil

import pytest

from helpers import make_good_repo, run_verify


@pytest.mark.parametrize("fresh", [False, True], ids=["in-use", "fresh"])
def test_good_layout_passes(good_repo, fresh):
    result = run_verify(good_repo, fresh=fresh)
    assert result.returncode == 0, result.stdout
    assert "OK" in result.stdout


def _rmdir_tasks(r): (r / "docs" / "tasks").rmdir()
def _rm_stage(r): (r / ".kairyn" / "stages" / "REQUIREMENTS.md").unlink()
def _rm_template(r): (r / ".kairyn" / "templates" / "STATE.md").unlink()
def _drift(r):
    with open(r / ".kairyn" / "stages" / "REQUIREMENTS.md", "a") as f: f.write("x\n")
def _template_drift(r):
    with open(r / ".kairyn" / "templates" / "STATE.md", "a") as f: f.write("x\n")
def _rm_learnings(r): (r / ".kairyn" / "learnings.md").unlink()
def _bad_heading(r): (r / ".kairyn" / "learnings.md").write_text("hello\n")
def _stray_task(r): (r / "docs" / "tasks" / "2026-01-01-x").mkdir()
def _no_kairyn(r): shutil.rmtree(r / ".kairyn")
def _no_manifest(r): (r / ".kairyn" / "manifest.json").unlink()


# Broken in both modes.
BROKEN = {
    "missing docs/tasks": (_rmdir_tasks, "docs/tasks/ missing"),
    "missing stage file": (_rm_stage, "REQUIREMENTS.md missing"),
    "missing STATE template": (_rm_template, "STATE.md missing"),
    "modified STATE template (plugin-owned)": (_template_drift, "differs from plugin copy"),
    "missing learnings.md": (_rm_learnings, "learnings.md missing"),
    "wrong learnings heading": (_bad_heading, "# Learnings"),
    "missing .kairyn": (_no_kairyn, ".kairyn/ missing"),
    "missing manifest": (_no_manifest, "manifest.json missing"),
}

# Normal in a repo in use; wrong right after init.
FRESH_ONLY = {
    "modified stage copy": (_drift, "differs from plugin copy"),
    "non-empty docs/tasks": (_stray_task, "should be empty"),
}


@pytest.mark.parametrize("fresh", [False, True], ids=["in-use", "fresh"])
@pytest.mark.parametrize("breakage", BROKEN, ids=list(BROKEN))
def test_broken_layout_fails(tmp_path, breakage, fresh):
    mutate, expected = BROKEN[breakage]
    repo = make_good_repo(tmp_path / "repo")
    mutate(repo)
    result = run_verify(repo, fresh=fresh)
    assert result.returncode == 1
    assert expected in result.stdout


@pytest.mark.parametrize("breakage", FRESH_ONLY, ids=list(FRESH_ONLY))
def test_fresh_mode_rejects_a_repo_in_use(tmp_path, breakage):
    mutate, expected = FRESH_ONLY[breakage]
    repo = make_good_repo(tmp_path / "repo")
    mutate(repo)
    result = run_verify(repo, fresh=True)
    assert result.returncode == 1
    assert expected in result.stdout


def test_default_mode_passes_a_repo_in_use(tmp_path):
    """Tasks exist and the user edited a stage: both are normal once kairyn is in use."""
    repo = make_good_repo(tmp_path / "repo")
    _stray_task(repo)
    (repo / "docs" / "tasks" / "2026-01-01-x" / "STATE.md").write_text("x\n")
    _drift(repo)
    result = run_verify(repo)
    assert result.returncode == 0, result.stdout


def test_unknown_option_fails(tmp_path):
    import subprocess
    from helpers import VERIFY
    result = subprocess.run(["bash", str(VERIFY), "--frsh", str(make_good_repo(tmp_path / "repo"))],
                            capture_output=True, text=True)
    assert result.returncode == 2 and "usage" in (result.stdout + result.stderr).lower()


def test_empty_repo_fails(tmp_path):
    assert run_verify(tmp_path).returncode == 1


# --- init.sh: the deterministic core of /kairyn:init -------------------------

import subprocess

from helpers import PLUGIN

INIT = PLUGIN / "scripts" / "init.sh"


def run_init(repo):
    return subprocess.run(["bash", str(INIT), str(repo)], capture_output=True, text=True)


def test_init_creates_verified_layout(tmp_path):
    result = run_init(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "CREATED" in result.stdout
    assert run_verify(tmp_path, fresh=True).returncode == 0


def test_init_never_overwrites(tmp_path):
    run_init(tmp_path)
    notes = tmp_path / ".kairyn" / "learnings.md"
    notes.write_text("# Learnings\n\nuser note: keep me\n")
    stage = tmp_path / ".kairyn" / "stages" / "REQUIREMENTS.md"
    stage.write_text("user edited\n")
    result = run_init(tmp_path)
    assert result.returncode == 0
    assert "ALREADY INITIALIZED" in result.stdout
    assert "keep me" in notes.read_text()
    assert stage.read_text() == "user edited\n"


# --- the consumer harness: .harness/ and the CLAUDE.md block ------------------

HARNESS = PLUGIN / "harness"
HARNESS_FILES = sorted(p.relative_to(HARNESS / ".harness").as_posix() for p in (HARNESS / ".harness").rglob("*") if p.is_file())


def test_init_installs_harness_files(tmp_path):
    run_init(tmp_path)
    for rel in HARNESS_FILES:
        assert (tmp_path / ".harness" / rel).is_file(), rel


def test_init_creates_claude_md_with_the_kairyn_block(tmp_path):
    run_init(tmp_path)
    text = (tmp_path / "CLAUDE.md").read_text()
    assert "<!-- kairyn:start -->" in text and "<!-- kairyn:end -->" in text


def test_init_appends_to_an_existing_claude_md_without_touching_it(tmp_path):
    original = "# My project\n\nMy own rules.\n"
    (tmp_path / "CLAUDE.md").write_text(original)
    run_init(tmp_path)
    text = (tmp_path / "CLAUDE.md").read_text()
    assert text.startswith(original)
    assert text.count("<!-- kairyn:start -->") == 1


def test_init_does_not_duplicate_an_existing_kairyn_block(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("mine\n<!-- kairyn:start -->\nold block\n<!-- kairyn:end -->\n")
    run_init(tmp_path)
    text = (tmp_path / "CLAUDE.md").read_text()
    assert text.count("<!-- kairyn:start -->") == 1 and "old block" in text


def test_init_keeps_existing_harness_files_and_adds_missing_ones(tmp_path):
    (tmp_path / ".harness").mkdir()
    (tmp_path / ".harness" / "README.md").write_text("my own harness readme\n")
    run_init(tmp_path)
    assert (tmp_path / ".harness" / "README.md").read_text() == "my own harness readme\n"
    assert (tmp_path / ".harness" / "workflows" / "task-lifecycle.md").is_file()


def test_init_on_an_initialized_repo_does_not_add_the_harness(tmp_path):
    (tmp_path / ".kairyn").mkdir()
    result = run_init(tmp_path)
    assert "ALREADY INITIALIZED" in result.stdout
    assert not (tmp_path / ".harness").exists() and not (tmp_path / "CLAUDE.md").exists()


def test_verify_fails_when_a_harness_file_is_missing(good_repo):
    (good_repo / ".harness" / "workflows" / "running-stages.md").unlink()
    result = run_verify(good_repo)
    assert result.returncode == 1 and "running-stages.md" in result.stdout


def test_verify_fails_when_claude_md_block_is_missing(good_repo):
    (good_repo / "CLAUDE.md").write_text("# nothing here\n")
    result = run_verify(good_repo)
    assert result.returncode == 1 and "kairyn" in result.stdout


def test_verify_fails_when_claude_md_is_missing(good_repo):
    (good_repo / "CLAUDE.md").unlink()
    assert run_verify(good_repo).returncode == 1


# --- the shipped harness template is itself consistent ------------------------

def test_installed_harness_passes_the_doc_and_budget_checkers(tmp_path):
    from budgets import budget_for, check as check_budgets, load_config
    from harness_docs import check as check_docs, collect

    run_init(tmp_path)
    assert check_docs(tmp_path) == [], "stale index tables: run bash scripts/refresh-harness-templates.sh"
    budgets, strict = load_config(tmp_path / ".harness" / "budgets.yml")
    assert check_budgets(tmp_path, budgets, strict) == []
    for path, meta in collect(tmp_path):
        rel = path.relative_to(tmp_path).as_posix()
        assert budget_for(rel, budgets).load == meta["load"], rel

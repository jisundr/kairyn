"""Deterministic: verify-init.sh accepts a correct layout and rejects broken ones."""
import shutil

import pytest

from conftest import make_good_repo, run_verify


def test_good_layout_passes(good_repo):
    result = run_verify(good_repo)
    assert result.returncode == 0, result.stdout
    assert "OK" in result.stdout


def _rmdir_tasks(r): (r / "docs" / "tasks").rmdir()
def _rm_stage(r): (r / ".kairyn" / "stages" / "requirements.md").unlink()
def _rm_template(r): (r / ".kairyn" / "templates" / "STATE.md").unlink()
def _drift(r):
    with open(r / ".kairyn" / "stages" / "requirements.md", "a") as f: f.write("x\n")
def _rm_learnings(r): (r / ".kairyn" / "learnings.md").unlink()
def _bad_heading(r): (r / ".kairyn" / "learnings.md").write_text("hello\n")
def _stray_task(r): (r / "docs" / "tasks" / "2026-01-01-x").mkdir()
def _no_kairyn(r): shutil.rmtree(r / ".kairyn")


BROKEN = {
    "missing docs/tasks": (_rmdir_tasks, "docs/tasks/ missing"),
    "missing stage file": (_rm_stage, "requirements.md missing"),
    "missing STATE template": (_rm_template, "STATE.md missing"),
    "modified stage copy": (_drift, "differs from plugin copy"),
    "missing learnings.md": (_rm_learnings, "learnings.md missing"),
    "wrong learnings heading": (_bad_heading, "# Learnings"),
    "non-empty docs/tasks": (_stray_task, "should be empty"),
    "missing .kairyn": (_no_kairyn, ".kairyn/ missing"),
}


@pytest.mark.parametrize("breakage", BROKEN, ids=list(BROKEN))
def test_broken_layout_fails(tmp_path, breakage):
    mutate, expected = BROKEN[breakage]
    repo = make_good_repo(tmp_path / "repo")
    mutate(repo)
    result = run_verify(repo)
    assert result.returncode == 1
    assert expected in result.stdout


def test_empty_repo_fails(tmp_path):
    assert run_verify(tmp_path).returncode == 1

"""afk.py for a home-repo task whose code is in a child repo (task 2026-11-24-multi-repo).

Test names carry the design slice (`t1` ... `t5`) so each slice's done command is `pytest -k t<n>`.
"""
import importlib
import subprocess
import sys

import pytest

import test_afk as base
from helpers import PLUGIN
from test_afk import GOOD_GATE, TASK, front, git, run, task_file

sys.path.insert(0, str(PLUGIN / "scripts"))
afk = importlib.import_module("afk")
repo = base.repo   # the home repo fixture of test_afk.py

REPOS = """gates:
  testing: {gate}
repos:
  ui:
    path: {path}
    gates:
      testing: pytest -q
      security:
"""


def child_repo(path):
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    for k, v in (("user.name", "Eval User"), ("user.email", "eval@example.com")):
        git(path, "config", k, v)
    (path / "README.md").write_text("child\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "child base")
    return path


def point_at(repo, name, path):
    """Give the task `repo: <name>` and afk.yml a repos map whose `ui` entry has `path`."""
    state = repo / "docs" / "tasks" / TASK / "STATE.md"
    state.write_text(state.read_text().replace("status: in-progress\n", f"status: in-progress\nrepo: {name}\n"))
    (repo / ".kairyn" / "afk.yml").write_text(REPOS.format(gate=GOOD_GATE, path=path))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "child task")


# --- T1: parse the repos map, read repo:, set code_root, block on a bad entry ---------------


def test_t1_parse_repos():
    data = afk.parse_afk(REPOS.format(gate="make test", path="../ui") + "approval:\n  - '**/migrations/**'\n")
    assert data == {
        "gates": {"testing": "make test"},
        "repos": {"ui": {"path": "../ui", "gates": {"testing": "pytest -q", "security": ""}}},
        "approval": ["**/migrations/**"],
    }
    assert list(data["repos"]["ui"]["gates"]) == ["testing", "security"]


def test_t1_parse_template():
    data = afk.parse_afk((PLUGIN / "templates" / "afk.yml").read_text())
    assert data["limits"] == {"build_usd": 10, "gates_usd": 5, "review_usd": 3, "run_usd": 20, "stage_minutes": 60}
    assert data["gates"] == {k: "" for k in
                             ("testing", "contract", "accessibility", "performance", "observability", "security")}
    assert data["checks"] == {} and data["approval"] == {}
    assert data["escape_hatches"] == afk.DEFAULT_ESCAPES


def test_t1_no_repo_line_keeps_the_home_repo(repo):
    r = afk.Run(repo, TASK)
    r.ensure_worktree()
    r.resolve_repo()
    assert (r.code_root, r.code) == (repo, r.wt)


def test_t1_repo_line_sets_code_root(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")   # A1: relative to the home repo root
    r = afk.Run(repo, TASK)
    r.ensure_worktree()
    r.resolve_repo()
    assert r.code_root == child.resolve()
    assert r.repo_entry["gates"] == {"testing": "pytest -q", "security": ""}


@pytest.mark.parametrize("name, make, cause", [
    ("web", lambda p: child_repo(p), "no entry in the repos: map"),
    ("ui", lambda p: None, "does not exist"),
    ("ui", lambda p: p.mkdir(), "is not a git repo"),
], ids=["unknown-name", "missing-path", "not-git"])
def test_t1_bad_repo_blocks(repo, tmp_path, name, make, cause):
    make(tmp_path / "ui")
    point_at(repo, name, "../ui")
    result = run(repo, "run", TASK)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"repo {name}" in result.stdout and cause in result.stdout
    state = task_file(repo, "STATE.md")
    assert front(state, "status") == "blocked"
    blocked = [line for line in state.splitlines() if "Blocked:" in line]
    assert blocked and f"repo {name}" in blocked[-1] and cause in blocked[-1]
    assert not (repo.parent / "stub.log").exists()   # no session ran

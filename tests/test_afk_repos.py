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


# --- T2: the child kairyn/<task> branch and worktree are `code`; task files commit only in `wt` --


def child_worktree(child):
    return child / ".git" / "kairyn" / "worktrees" / TASK


def test_t2_branches_split(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    child_head = git(child, "rev-parse", "HEAD").strip()
    point_at(repo, "ui", "../ui")
    r = afk.Run(repo, TASK)
    r.ensure_worktree()
    r.resolve_repo()
    assert r.code == child_worktree(child).resolve() and r.code != r.wt
    assert git(r.code, "rev-parse", "--abbrev-ref", "HEAD").strip() == f"kairyn/{TASK}"
    assert git(r.code, "rev-parse", "HEAD").strip() == child_head   # A2: starts at the child HEAD
    assert git(r.wt, "rev-parse", "--abbrev-ref", "HEAD").strip() == f"kairyn/{TASK}"
    home_head = git(r.wt, "rev-parse", "HEAD").strip()
    r.update("build", "a log line")
    (r.code / "app.py").write_text("x = 1\n")   # code the session left uncommitted
    r.commit(f"kairyn({TASK}): build")
    assert git(r.wt, "rev-parse", "HEAD").strip() != home_head   # the task files went to the home branch
    assert git(r.wt, "diff", "--name-only", "HEAD~1", "HEAD").split() == [f"docs/tasks/{TASK}/STATE.md"]
    assert git(child, "rev-parse", f"kairyn/{TASK}").strip() == child_head   # nothing on the child branch
    assert "docs" not in git(child, "ls-tree", "-r", "--name-only", f"kairyn/{TASK}")
    assert (r.code / "app.py").is_file()


def test_t2_run_creates_the_child_worktree(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")
    run(repo, "run", TASK)
    assert child_worktree(child).is_dir()
    assert git(child, "rev-parse", "--verify", f"kairyn/{TASK}")
    assert "docs" not in git(child, "ls-tree", "-r", "--name-only", f"kairyn/{TASK}")


def test_t2_reuse_worktree(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")
    first = afk.Run(repo, TASK)
    first.ensure_worktree()
    first.resolve_repo()
    (first.code / "keep.txt").write_text("left by the first run\n")
    second = afk.Run(repo, TASK)
    second.ensure_worktree()
    second.resolve_repo()   # a second run reuses the worktree, no error
    assert second.code == first.code and (second.code / "keep.txt").is_file()
    # The branch exists but its worktree is gone: the worktree comes back on the same branch.
    git(child, "commit", "-q", "--allow-empty", "-m", "on main")   # main moves on; the task branch does not
    branch_head = git(child, "rev-parse", f"kairyn/{TASK}").strip()
    git(child, "worktree", "remove", "--force", str(first.code))
    third = afk.Run(repo, TASK)
    third.ensure_worktree()
    third.resolve_repo()
    assert third.code.is_dir() and git(third.code, "rev-parse", "HEAD").strip() == branch_head

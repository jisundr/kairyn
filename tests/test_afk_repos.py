"""afk.py for a home-repo task whose code is in a child repo (task 2026-11-24-multi-repo).

Test names carry the design slice (`t1` ... `t5`) so each slice's done command is `pytest -k t<n>`.
"""
import importlib
import re
import subprocess
import sys
from pathlib import Path

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


# --- T3: sessions run in `code`; red, green, flags, diff and backstop use the child commits ------


def lines(repo, suffix):
    log = repo.parent / f"stub.log{suffix}"
    return log.read_text().splitlines() if log.exists() else []


def test_t3_session_cwd(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")
    result = run(repo, "run", TASK)
    assert result.returncode == 0, result.stdout + result.stderr
    wt, code = base.worktree(repo).resolve(), child_worktree(child).resolve()
    cwds = lines(repo, ".cwd")
    assert cwds and all(Path(c).resolve() == code for c in cwds)   # every session, read-only ones too
    assert all(f"--add-dir {wt}" in a for a in lines(repo, ".args"))
    prompts = base.calls(repo)
    builds = [p for p in prompts if re.search(r"\bT\d\b", p) and "BUILD.md" in p and "reviewer" not in p]
    assert len(builds) == 2
    for p in builds + [p for p in prompts if "REVIEW.md" in p and "reviewer" not in p]:
        assert f"{wt}/.kairyn/stages/" in p and f"{wt}/docs/tasks/{TASK}" in p


def test_t3_home_task_session_cwd_is_unchanged(repo):
    assert run(repo, "run", TASK).returncode == 0
    wt = base.worktree(repo).resolve()
    assert all(Path(c).resolve() == wt for c in lines(repo, ".cwd"))
    assert not any("--add-dir" in a for a in lines(repo, ".args"))


def test_t3_red_green_child(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")
    result = run(repo, "run", TASK)
    assert result.returncode == 0, result.stdout + result.stderr
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked"), state
    build = task_file(repo, "BUILD.md")
    child_log = git(child, "log", "--format=%h %s", f"kairyn/{TASK}")
    for tid in ("T1", "T2"):
        row = next(line for line in build.splitlines() if line.startswith(f"| {tid} |"))
        test_sha, red, feat_sha, green = [c.strip() for c in row.strip("|").split("|")][1:5]
        assert f"{test_sha} test({tid})" in child_log and f"{feat_sha} feat({tid})" in child_log
        assert red != "0" and green == "0"
    home_files = git(repo, "ls-tree", "-r", "--name-only", f"kairyn/{TASK}").split()
    assert not any(f.startswith(("check_", "feature_")) for f in home_files)   # code only in the child
    assert (base.worktree(repo) / "docs" / "tasks" / TASK / "REVIEW.md").is_file()
    reviewer = next(p for p in base.calls(repo) if "reviewer" in p)
    assert "feature_t1.py" in reviewer and "check_t2.py" in reviewer   # the reviewer diff is the child diff


def test_t3_flags_child(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")
    assert run(repo, "run", TASK, mode="noqa").returncode == 0
    assert "feature_t1.py" in git(child, "ls-tree", "-r", "--name-only", f"kairyn/{TASK}").split()
    build = task_file(repo, "BUILD.md")
    assert "escape hatch: `feature_t1.py:1` `# noqa` in feat(T1)" in build


def test_t3_backstop_child(repo, tmp_path):
    child = child_repo(tmp_path / "ui")
    point_at(repo, "ui", "../ui")
    afk_yml = repo / ".kairyn" / "afk.yml"
    afk_yml.write_text("approval:\n  - '**/feature_t2.py'\n" + afk_yml.read_text())
    git(repo, "commit", "-q", "-am", "approval glob")
    assert run(repo, "run", TASK).returncode == 0
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("gates", "blocked")
    assert re.search(r"\[gates\] Blocked: approval: `feature_t2.py` matches `\*\*/feature_t2.py` in feat\(T2\)", state)
    assert "feature_t2.py" in git(child, "ls-tree", "-r", "--name-only", f"kairyn/{TASK}").split()

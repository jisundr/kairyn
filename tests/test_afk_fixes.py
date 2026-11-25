"""afk.py fixes from the backlog Next batch of 2026-11-25: where the task folder is, resume, retries.

Each test names its backlog idea. All run afk.py against tests/stubs/claude and tests/stubs/gh.
"""
import importlib
import re
import subprocess
import sys

import pytest

import test_afk as base
from helpers import PLUGIN
from test_afk import TASK, front, git, run, task_file

sys.path.insert(0, str(PLUGIN / "scripts"))
afk = importlib.import_module("afk")
repo = base.repo   # the repo fixture of test_afk.py


def no_traceback(result):
    assert "Traceback" not in result.stderr, result.stderr


# --- afk-uncommitted-task-folder --------------------------------------------------------------


def test_uncommitted_task_folder_goes_on_the_task_branch(repo):
    git(repo, "rm", "-rq", "--cached", "docs/tasks")
    git(repo, "commit", "-qm", "task folder not committed")
    result = run(repo, "run", TASK)
    no_traceback(result)
    assert result.returncode == 0, result.stdout + result.stderr
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked")
    assert f"kairyn({TASK}): task folder" in git(base.worktree(repo), "log", "--format=%s")


def test_task_folder_missing_everywhere_fails_with_no_branch(repo):
    result = run(repo, "run", "2026-01-06-nothing")
    no_traceback(result)
    assert result.returncode == 1 and result.stdout.startswith("FAIL: no task folder")
    assert "kairyn/2026-01-06-nothing" not in git(repo, "branch", "--list")


def test_task_folder_with_no_state_md_blocks(repo):
    (repo / "docs" / "tasks" / TASK / "STATE.md").unlink()
    git(repo, "commit", "-qam", "no STATE.md")
    result = run(repo, "run", TASK)
    no_traceback(result)
    assert result.returncode == 1 and "BLOCKED:" in result.stdout and "STATE.md" in result.stdout


# --- afk-task-folder-check -------------------------------------------------------------------


def test_task_folder_only_on_the_task_branch(repo):
    git(repo, "branch", f"kairyn/{TASK}")
    git(repo, "rm", "-rq", "docs/tasks")
    git(repo, "commit", "-qm", "the task lives on its branch")
    result = run(repo, "run", TASK)
    no_traceback(result)
    assert result.returncode == 0, result.stdout + result.stderr
    assert front(task_file(repo, "STATE.md"), "stage") == "review"
    approve = run(repo, "approve", TASK, "--words", "Ship it")
    assert approve.returncode == 0, approve.stdout + approve.stderr
    assert front(task_file(repo, "STATE.md"), "status") == "done"


# --- afk-resume-blocked ----------------------------------------------------------------------


def test_run_resumes_a_blocked_task(repo):
    (repo / ".kairyn" / "afk.yml").write_text("gates:\n  testing:\n")
    git(repo, "commit", "-qam", "no testing command")
    first = run(repo, "run", TASK)
    assert "BLOCKED:" in first.stdout
    assert front(task_file(repo, "STATE.md"), "status") == "blocked"
    wt = base.worktree(repo)   # the person fixes the cause on the task branch
    (wt / ".kairyn" / "afk.yml").write_text(f"gates:\n  testing: {base.GOOD_GATE}\n")
    git(wt, "commit", "-qam", "set the testing gate")
    second = run(repo, "run", TASK)
    assert second.returncode == 0, second.stdout + second.stderr
    assert "blocked at build" not in second.stdout
    state = task_file(repo, "STATE.md")
    assert (front(state, "stage"), front(state, "status")) == ("review", "blocked")
    assert re.search(r"\[build\] Resumed after a block\.", state), state


def test_run_does_not_resume_a_pending_merge_decision(repo):
    run(repo, "run", TASK)
    (repo.parent / "stub.log").unlink()
    again = run(repo, "run", TASK)
    assert again.returncode == 0 and "STOP:" in again.stdout and base.calls(repo) == []


# --- build-needs-branch-free -----------------------------------------------------------------


def test_task_branch_checked_out_in_the_main_checkout_blocks(repo):
    git(repo, "checkout", "-qb", f"kairyn/{TASK}")
    result = run(repo, "run", TASK)
    no_traceback(result)
    assert result.returncode == 1
    line = result.stdout.strip().splitlines()[-1]
    assert line.startswith("BLOCKED:") and f"kairyn/{TASK} is checked out in {repo.resolve()}" in line, line


# --- afk-drops-task-lines --------------------------------------------------------------------


def test_task_graph_rejects_a_malformed_task_line():
    text = "- T1: a. Done: `x` exits 0.\n- T2 (approval): b. after: T1. Done: `y` exits 0.\n"
    with pytest.raises(ValueError, match=r"T2.*- T<n>:"):
        afk.task_graph(text)


def test_a_malformed_task_line_blocks_the_build(repo):
    design = repo / "docs" / "tasks" / TASK / "DESIGN.md"
    design.write_text(design.read_text().replace("- T2:", "- T2 (approval):"))
    git(repo, "commit", "-qam", "malformed task line")
    result = run(repo, "run", TASK)
    assert "BLOCKED: build: DESIGN.md:" in result.stdout
    assert base.calls(repo) == [], "no slice runs"


# --- approve-retry (with afk-merge-log-unpushed) ---------------------------------------------


def test_approve_retries_a_blocked_merge_with_no_hand_edit(repo):
    remote = base.with_remote(repo)
    base.run_gh(repo, "run", TASK)
    first = base.run_gh(repo, "approve", TASK, "--words", "Ship it", gh_mode="merge_fail")
    assert first.returncode == 1
    second = base.run_gh(repo, "approve", TASK, "--words", "Ship it")
    assert second.returncode == 0, second.stdout + second.stderr
    assert base.gh_calls(repo)[-1] == f"pr merge kairyn/{TASK} --merge"
    state = task_file(repo, "STATE.md")
    assert front(state, "status") == "done"
    assert len(re.findall(r"^Decision: ", task_file(repo, "REVIEW.md"), re.M)) == 1
    tip = git(remote, "rev-parse", f"kairyn/{TASK}").strip()
    assert tip == git(base.worktree(repo), "rev-parse", "HEAD").strip(), "the merge log line is pushed"


def test_approve_does_not_retry_a_rejected_task(repo):
    run(repo, "run", TASK)
    assert run(repo, "reject", TASK, "--words", "Not yet").returncode == 0
    again = run(repo, "approve", TASK, "--words", "Ship it")
    assert again.returncode == 1 and again.stdout.startswith("FAIL:")

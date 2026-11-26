"""close.py record-merge: a hand-merged task gets STATE.md done and a REVIEW.md Decision line from the merged PR."""
import json
import os
import re
import subprocess
import sys

import pytest

from helpers import PLUGIN

CLOSE = PLUGIN / "scripts" / "close.py"
STUB = PLUGIN.parent / "tests" / "stubs" / "gh_prs"
TASK = "2026-01-05-dry-run"
STATE = """---
task: {task}
title: Dry run
stage: build
status: in-progress
stages:
  requirements: done
  design: done
  build: pending
  gates: pending
  review: pending
created: 2026-01-05T09:00:00Z
updated: 2026-01-05T09:20:00Z
---

# Log

2026-01-05T09:00:00Z [requirements] Task created.
{log}"""
MERGER = {"login": "octo", "name": "Octo Cat"}


def pr(number, head="feature", state="MERGED", merged_by=MERGER):
    return {"number": number, "state": state, "headRefName": head,
            "mergedAt": "2026-01-06T10:11:12Z" if state == "MERGED" else None,
            "mergedBy": merged_by if state == "MERGED" else None}


def make(tmp_path, prs, log="", task=TASK, review=None):
    folder = tmp_path / "docs" / "tasks" / task
    folder.mkdir(parents=True)
    (folder / "STATE.md").write_text(STATE.format(task=task, log=log))
    if review is not None:
        (folder / "REVIEW.md").write_text(review)
    (tmp_path / "prs.json").write_text(json.dumps(prs))
    return folder


def run(tmp_path, *args, gh=STUB, **env):
    full = {**os.environ, "KAIRYN_GH": str(gh), "GH_PRS": str(tmp_path / "prs.json"),
            "GH_LOG": str(tmp_path / "gh.log"), **env}
    return subprocess.run([sys.executable, str(CLOSE), *args, "--root", str(tmp_path)],
                          capture_output=True, text=True, env=full)


def front(folder, key):
    for line in (folder / "STATE.md").read_text().splitlines():
        if line.startswith(f"{key}:") or line.startswith(f"  {key}:"):
            return line.split(":", 1)[1].strip()
    return None


def test_record_merge_with_a_pr_argument_marks_the_task_done_and_check_passes(tmp_path):
    folder = make(tmp_path, [pr(7)])
    r = run(tmp_path, "record-merge", TASK, "--pr", "7")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "RECORDED: PR #7 merged by Octo Cat at 2026-01-06T10:11:12Z" in r.stdout
    assert (front(folder, "status"), front(folder, "stage"), front(folder, "review")) == ("done", "review", "done")
    assert front(folder, "build") == "pending", "other stages stay as they are (A2)"
    assert front(folder, "updated") != "2026-01-05T09:20:00Z"
    last = (folder / "STATE.md").read_text().rstrip().splitlines()[-1]
    assert "[review]" in last and "PR #7" in last and "Octo Cat" in last and "2026-01-06T10:11:12Z" in last
    review = (folder / "REVIEW.md").read_text()
    assert f"task: {TASK}\nstage: review\n" in review
    assert 'Decision: Octo Cat, 2026-01-06T10:11:12Z, "merged PR #7"' in review
    assert run(tmp_path, "check", TASK).stdout.strip() == "OK"


def test_record_merge_uses_the_last_pr_named_in_state(tmp_path):
    log = "2026-01-05T10:00:00Z [design] Rebased after PR #3 merged.\n2026-01-06T09:00:00Z [build] Waiting for PR #12.\n"
    folder = make(tmp_path, [pr(3), pr(12)], log=log)
    r = run(tmp_path, "record-merge", TASK)
    assert r.returncode == 0 and "RECORDED: PR #12" in r.stdout, r.stdout
    assert '"merged PR #12"' in (folder / "REVIEW.md").read_text()


def test_record_merge_pr_argument_wins(tmp_path):
    folder = make(tmp_path, [pr(7), pr(12)], log="2026-01-06T09:00:00Z [build] Waiting for PR #12.\n")
    assert run(tmp_path, "record-merge", TASK, "--pr", "7").returncode == 0
    assert '"merged PR #7"' in (folder / "REVIEW.md").read_text()
    assert "pr list" not in (tmp_path / "gh.log").read_text()


@pytest.mark.parametrize("head", [f"kairyn/{TASK}", "jisundr/dry-run", f"feat/{TASK}"])
def test_record_merge_finds_the_pr_by_branch(tmp_path, head):
    folder = make(tmp_path, [pr(4, head=head), pr(5, head="jisundr/dry-run-idea"), pr(6, head="other", state="OPEN")])
    r = run(tmp_path, "record-merge", TASK)
    assert r.returncode == 0 and "RECORDED: PR #4" in r.stdout, r.stdout
    assert '"merged PR #4"' in (folder / "REVIEW.md").read_text()


def test_record_merge_replaces_a_pending_decision(tmp_path):
    review = f"---\ntask: {TASK}\nstage: review\nsummary: \"x\"\n---\n\n# Review\n\n## Findings\n- F1: none\n\nDecision: pending\n"
    folder = make(tmp_path, [pr(7)], review=review)
    assert run(tmp_path, "record-merge", TASK, "--pr", "7").returncode == 0
    text = (folder / "REVIEW.md").read_text()
    assert "Decision: pending" not in text and "- F1: none" in text
    assert text.rstrip().endswith('Decision: Octo Cat, 2026-01-06T10:11:12Z, "merged PR #7"')


def test_record_merge_uses_the_login_when_the_name_is_empty(tmp_path):
    folder = make(tmp_path, [pr(7, merged_by={"login": "octo", "name": ""})])
    assert run(tmp_path, "record-merge", TASK, "--pr", "7").returncode == 0
    assert 'Decision: octo, 2026-01-06T10:11:12Z, "merged PR #7"' in (folder / "REVIEW.md").read_text()


def test_record_merge_leaves_a_done_task(tmp_path):
    folder = make(tmp_path, [pr(7)])
    state = (folder / "STATE.md").read_text().replace("status: in-progress", "status: done")
    (folder / "STATE.md").write_text(state)
    r = run(tmp_path, "record-merge", TASK)
    assert r.returncode == 0 and r.stdout.strip() == f"OK: {TASK} is done", r.stdout
    assert (folder / "STATE.md").read_text() == state and not (folder / "REVIEW.md").exists()
    assert not (tmp_path / "gh.log").exists(), "a done task needs no gh call"


@pytest.mark.parametrize("prs, args, gh, env, cause", [
    ([pr(7)], ["--pr", "7"], "missing", {}, "no gh command"),
    ([pr(7)], ["--pr", "7"], None, {"GH_MODE": "fail"}, "gh pr view failed: gh: not logged in"),
    ([pr(7, state="OPEN")], ["--pr", "7"], None, {}, "PR #7 is open, not merged"),
    ([pr(9, head="other")], [], None, {}, "no PR #<n> in STATE.md and no merged PR from branch"),
    ([pr(4, head="a/dry-run"), pr(5, head=f"kairyn/{TASK}")], [], None, {}, "more than one merged PR matches the branch: #4, #5"),
])
def test_record_merge_fails_and_changes_nothing(tmp_path, prs, args, gh, env, cause):
    folder = make(tmp_path, prs)
    before = (folder / "STATE.md").read_text()
    r = run(tmp_path, "record-merge", TASK, *args, gh=tmp_path / gh if gh else STUB, **env)
    assert r.returncode == 1 and r.stdout.startswith("FAIL: ") and cause in r.stdout, r.stdout
    assert (folder / "STATE.md").read_text() == before and not (folder / "REVIEW.md").exists()


def test_record_merge_refuses_an_unknown_task(tmp_path):
    r = run(tmp_path, "record-merge", "2026-01-09-none")
    assert r.returncode == 1 and "no task" in r.stdout, r.stdout


def test_close_stage_records_the_merge_before_check():
    """R8: step 1 of CLOSE.md (shipped and this repo's copy) runs record-merge, then check."""
    for path in (PLUGIN / "stages" / "CLOSE.md", PLUGIN.parent / ".kairyn" / "stages" / "CLOSE.md"):
        step = next(l for l in path.read_text().splitlines() if l.startswith("1. "))
        assert "record-merge <task>" in step and "--pr" in step and "check <task>" in step, path
        assert step.index("record-merge") < step.index("check <task>"), path
    assert "[PR number]" in (PLUGIN / "skills" / "close" / "SKILL.md").read_text()


def test_record_merge_writes_a_bullet_log_entry_and_keeps_old_entries(tmp_path):
    folder = make(tmp_path, [pr(7)], log="2026-01-05T09:10:00Z [design] Old plain entry.\n")
    assert run(tmp_path, "record-merge", TASK, "--pr", "7").returncode == 0
    lines = (folder / "STATE.md").read_text().rstrip("\n").splitlines()
    assert re.fullmatch(r"- \S+Z \[review\] Merged by hand: PR #7 .*", lines[-1]), lines[-1]
    assert lines[-2] == "2026-01-05T09:10:00Z [design] Old plain entry.", "old entries stay as they are (R6)"

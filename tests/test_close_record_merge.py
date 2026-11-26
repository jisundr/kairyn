"""close.py record-merge: a hand-merged task gets STATE.md done and a REVIEW.md Decision line from the merged PR."""
import json
import os
import subprocess
import sys

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

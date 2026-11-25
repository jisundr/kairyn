"""close.py: the scripted half of the close stage (checks, changelog, deletion, release tag)."""
import subprocess
import sys

import pytest

from helpers import PLUGIN

CLOSE = PLUGIN / "scripts" / "close.py"
TASK = "2026-01-05-dry-run"

STATE = """---
task: {task}
title: Dry run
stage: requirements
status: {status}
stages:
  requirements: done
created: 2026-01-05T09:00:00Z
updated: 2026-01-05T09:20:00Z
---

# Log
"""
REQS = "---\ntask: {task}\nstage: requirements\nsummary: \"x\"\n---\n\n# Requirements\n\n{approval}\n"
APPROVED = 'Approval: Eval User, 2026-01-05T09:20:00Z, "Approved"'


def backlog(status, body=""):
    return f"---\ntitle: t\nstatus: {status}\n---\n\n# t\n\n{body}\n\n# Log\n"


def run(root, *args):
    return subprocess.run([sys.executable, str(CLOSE), *args, "--root", str(root)], capture_output=True, text=True)


def make_task(root, task=TASK, status="done", approval=APPROVED):
    d = root / "docs" / "tasks" / task
    d.mkdir(parents=True)
    (d / "STATE.md").write_text(STATE.format(task=task, status=status))
    (d / "REQUIREMENTS.md").write_text(REQS.format(task=task, approval=approval))
    return d


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for k, v in (("user.name", "Eval User"), ("user.email", "eval@example.com")):
        subprocess.run(["git", "-C", str(root), "config", k, v], check=True)
    make_task(root)
    b = root / "docs" / "backlog"
    b.mkdir(parents=True)
    (b / "1-linked.md").write_text(backlog("committed", f"Task [{TASK}](../tasks/{TASK}/REQUIREMENTS.md)."))
    (b / "2-dropped.md").write_text(backlog("dropped", "Shipped elsewhere."))
    (b / "3-parked.md").write_text(backlog("parked"))
    (b / "4-inbox.md").write_text(backlog("inbox"))
    (b / "5-other.md").write_text(backlog("committed", "Task [other](../tasks/2026-01-09-other/REQUIREMENTS.md)."))
    make_task(root, "2026-01-09-other", status="in-progress")
    (b / "README.md").write_text("# Backlog\n\n| Idea |\n|---|\n| [Linked](1-linked.md) |\n| [Dropped](2-dropped.md) |\n"
                                 "| [Parked](3-parked.md) |\n")
    return root


def test_check_accepts_a_done_approved_task(repo):
    r = run(repo, "check", TASK)
    assert r.returncode == 0 and r.stdout.strip() == "OK", r.stdout + r.stderr


@pytest.mark.parametrize("status,approval", [("blocked", APPROVED), ("in-progress", APPROVED), ("done", "Approval: pending"),
                                             ("done", "")])
def test_close_refuses_a_task_that_is_not_done_and_approved(tmp_path, status, approval):
    root = tmp_path / "r"
    make_task(root, status=status, approval=approval)
    before = sorted(p.relative_to(root) for p in root.rglob("*"))
    r = run(root, "close", TASK, "--entry", "Added a dry run.")
    assert r.returncode == 1 and r.stdout.startswith("FAIL:"), r.stdout
    assert sorted(p.relative_to(root) for p in root.rglob("*")) == before


def test_close_refuses_an_unknown_task(repo):
    assert run(repo, "close", "2026-01-01-nope", "--entry", "x").returncode == 1


def test_close_writes_changelog_and_deletes_the_task(repo):
    r = run(repo, "close", TASK, "--entry", "Added a dry-run flag.")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (repo / "docs" / "tasks" / TASK).exists()
    assert (repo / "docs" / "tasks" / "2026-01-09-other").is_dir()
    log = (repo / "CHANGELOG.md").read_text()
    assert log.startswith("# Changelog\n") and "## Unreleased\n" in log
    assert f"- Added a dry-run flag. ({TASK})" in log
    assert f"DELETED docs/tasks/{TASK}/" in r.stdout and "WROTE CHANGELOG.md" in r.stdout


def test_close_appends_under_an_existing_unreleased_section(repo):
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Older. (t0)\n\n## 0.1.0 - 2026-01-01\n\n- First. (t-1)\n")
    run(repo, "close", TASK, "--entry", "Newer.")
    log = (repo / "CHANGELOG.md").read_text()
    assert log.index("- Older.") < log.index("- Newer.") < log.index("## 0.1.0")


def test_close_deletes_linked_and_dropped_backlog_files_only(repo):
    run(repo, "close", TASK, "--entry", "x")
    left = sorted(p.name for p in (repo / "docs" / "backlog").glob("*.md"))
    assert left == ["3-parked.md", "4-inbox.md", "5-other.md", "README.md"]


def test_close_removes_index_rows_of_deleted_files(repo):
    r = run(repo, "close", TASK, "--entry", "x")
    index = (repo / "docs" / "backlog" / "README.md").read_text()
    assert "1-linked.md" not in index and "2-dropped.md" not in index and "3-parked.md" in index
    assert "EDITED docs/backlog/README.md" in r.stdout


def test_close_reports_links_to_the_deleted_task(repo):
    (repo / "docs" / "notes.md").write_text(f"See docs/tasks/{TASK}/REQUIREMENTS.md\n")
    r = run(repo, "close", TASK, "--entry", "x")
    assert f"LINK: docs/notes.md still links tasks/{TASK}/" in r.stdout
    assert (repo / "docs" / "notes.md").exists()


def test_adr_path_numbers_from_existing_records(repo):
    assert run(repo, "adr-path", "use-skills").stdout.strip() == "docs/adr/0001-use-skills.md"
    (repo / "docs" / "adr").mkdir()
    (repo / "docs" / "adr" / "0007-old.md").write_text("# 7. Old\n")
    assert run(repo, "adr-path", "Use Skills!").stdout.strip() == "docs/adr/0008-use-skills.md"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def test_release_moves_unreleased_and_tags_locally(repo):
    run(repo, "close", TASK, "--entry", "Added a dry-run flag.")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "close")
    r = run(repo, "release", "0.6.0")
    assert r.returncode == 0, r.stdout + r.stderr
    log = (repo / "CHANGELOG.md").read_text()
    assert log.index("## Unreleased") < log.index("## 0.6.0 - ") < log.index("- Added a dry-run flag.")
    assert "Added a dry-run flag." in git(repo, "tag", "-l", "--format=%(contents)", "v0.6.0").stdout
    assert "TAGGED v0.6.0" in r.stdout and "git push origin v0.6.0" in r.stdout
    assert git(repo, "remote").stdout == ""   # nothing to push to: it never pushes


def test_release_refuses_an_empty_unreleased_or_a_taken_tag(repo):
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "c")
    assert run(repo, "release", "0.6.0").returncode == 1
    (repo / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- A. (t)\n")
    git(repo, "commit", "-qam", "c2"); git(repo, "tag", "v0.6.0")
    assert run(repo, "release", "0.6.0").returncode == 1


def test_close_reports_links_to_deleted_backlog_files(repo):
    (repo / "docs" / "backlog" / "4-inbox.md").write_text(backlog("inbox", "Split from [dropped](2-dropped.md)."))
    r = run(repo, "close", TASK, "--entry", "x")
    assert "LINK: docs/backlog/4-inbox.md still links 2-dropped.md" in r.stdout


def learnings(root, chars):
    (root / ".kairyn").mkdir(exist_ok=True)
    (root / ".kairyn" / "learnings.md").write_text("x" * chars)


@pytest.mark.parametrize("chars,line", [(4004, "RETRO: learnings.md 1001/2000"), (8000, "RETRO: learnings.md 2000/2000")])
def test_close_names_retro_past_half_the_learnings_budget(repo, chars, line):
    learnings(repo, chars)
    r = run(repo, "close", TASK, "--entry", "Added a dry run.")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.splitlines()[-1] == line


@pytest.mark.parametrize("chars", [0, 4000])
def test_close_is_quiet_at_or_under_half_the_budget(repo, chars):
    if chars:
        learnings(repo, chars)
    r = run(repo, "close", TASK, "--entry", "Added a dry run.")
    assert r.returncode == 0 and "RETRO:" not in r.stdout, r.stdout


def test_close_uses_the_repo_learnings_budget(repo):
    (repo / ".harness").mkdir()
    (repo / ".harness" / "budgets.yml").write_text(
        'budgets:\n  - {pattern: ".kairyn/learnings.md", max_tokens: 1000, load: runtime}\n')
    learnings(repo, 3976)
    r = run(repo, "close", TASK, "--entry", "Added a dry run.")
    assert "RETRO: learnings.md 994/1000" in r.stdout


def make_stage_task(root, task, stage, approval):
    """A done task whose last stage is <stage>: its approval lives in <STAGE>.md, not REQUIREMENTS.md."""
    d = root / "docs" / "tasks" / task
    d.mkdir(parents=True)
    (d / "STATE.md").write_text(STATE.format(task=task, status="done").replace("stage: requirements", f"stage: {stage}", 1))
    (d / f"{stage.upper()}.md").write_text(f"---\ntask: {task}\nstage: {stage}\nsummary: \"x\"\n---\n\n{approval}\n")
    return d


def test_check_accepts_a_retro_task_approved_in_retro_md(tmp_path):
    make_stage_task(tmp_path, "2026-01-10-retro", "retro", APPROVED)
    r = run(tmp_path, "check", "2026-01-10-retro")
    assert r.returncode == 0 and r.stdout.strip() == "OK", r.stdout


def test_close_deletes_an_approved_retro_task(tmp_path):
    make_stage_task(tmp_path, "2026-01-10-retro", "retro", APPROVED)
    r = run(tmp_path, "close", "2026-01-10-retro", "--entry", "Moved learnings to their homes.")
    assert r.returncode == 0 and "DELETED docs/tasks/2026-01-10-retro/" in r.stdout, r.stdout


def test_check_refuses_a_retro_task_still_pending(tmp_path):
    make_stage_task(tmp_path, "2026-01-10-retro", "retro", "Approval: pending")
    r = run(tmp_path, "check", "2026-01-10-retro")
    assert r.returncode == 1 and "no approval line in RETRO.md" in r.stdout, r.stdout


def test_check_reads_the_approval_of_the_last_stage(tmp_path):
    """A design task is done only when DESIGN.md is approved, not REQUIREMENTS.md alone."""
    d = make_stage_task(tmp_path, "2026-01-11-plan", "design", "Approval: pending")
    (d / "REQUIREMENTS.md").write_text(REQS.format(task="2026-01-11-plan", approval=APPROVED))
    r = run(tmp_path, "check", "2026-01-11-plan")
    assert r.returncode == 1 and "no approval line in DESIGN.md" in r.stdout, r.stdout


def test_check_accepts_a_review_task_with_a_decision(tmp_path):
    """D11: review records the merge decision as `Decision:`, not `Approval:`."""
    make_stage_task(tmp_path, "2026-01-12-loop", "review", 'Decision: Eval User, 2026-01-12T10:00:00Z, "Ship it"')
    r = run(tmp_path, "check", "2026-01-12-loop")
    assert r.returncode == 0 and r.stdout.strip() == "OK", r.stdout


def test_check_refuses_a_review_task_still_pending(tmp_path):
    make_stage_task(tmp_path, "2026-01-12-loop", "review", "Decision: pending")
    r = run(tmp_path, "check", "2026-01-12-loop")
    assert r.returncode == 1 and "no approval line in REVIEW.md" in r.stdout, r.stdout


def test_close_without_git_keeps_a_copy_of_what_it_deletes(tmp_path):
    """Backlog exit-without-git: no git history keeps the folder, so close keeps a copy."""
    root = tmp_path / "plain"
    make_task(root)
    b = root / "docs" / "backlog"
    b.mkdir(parents=True)
    (b / "1-linked.md").write_text(backlog("committed", f"Task [{TASK}](../tasks/{TASK}/REQUIREMENTS.md)."))
    result = run(root, "close", TASK, "--entry", "Added dry runs")
    assert result.returncode == 0, result.stdout
    archive = root / ".kairyn" / "archive"
    assert not (root / "docs" / "tasks" / TASK).exists()
    assert (archive / "tasks" / TASK / "REQUIREMENTS.md").is_file()
    assert (archive / "backlog" / "1-linked.md").is_file()
    assert f"DELETED docs/tasks/{TASK}/" in result.stdout
    assert f"ARCHIVED .kairyn/archive/tasks/{TASK}/" in result.stdout
    assert "LINK:" not in result.stdout, "the archive does not count as a link to fix"


def test_close_in_git_keeps_no_archive(repo):
    assert run(repo, "close", TASK, "--entry", "Added dry runs").returncode == 0
    assert not (repo / ".kairyn" / "archive").exists()

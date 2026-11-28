"""backlog.py and BACKLOG.md: the scripted file writes of the backlog stage (T1: capture)."""
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from helpers import PLUGIN, split_front_matter

BACKLOG = PLUGIN / "scripts" / "backlog.py"
STAGE = PLUGIN / "stages" / "BACKLOG.md"
OWNER = "Ada Owner"
REQUEST = 'Let\'s "track" ideas, not lose them: one file each.'
PROBLEM = "Ideas get lost between sessions."
README_HEADER = "| Idea | Effort | Impact | Notes |"


def run(root, *args):
    return subprocess.run([sys.executable, str(BACKLOG), *args, "--root", str(root)], capture_output=True, text=True)


def capture(root, slug="track-ideas", effort="medium", impact="high", request=REQUEST, problem=PROBLEM):
    return run(root, "capture", "--slug", slug, "--title", "Ideas get lost", "--effort", effort,
               "--impact", impact, "--request", request, "--problem", problem)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", OWNER], check=True)
    return root


def ideas(root):
    return sorted(p for p in (root / "docs" / "backlog").glob("*.md") if p.name != "README.md")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


# --- the stage (AC1, R1) --------------------------------------------------------

def test_stage_names_the_rules():
    fm, body = split_front_matter(STAGE.read_text())
    data = yaml.safe_load(fm)
    assert data["name"] == "backlog" and data["optional"] is True
    for word in ("inbox", "triaged", "parked", "dropped", "committed", "review_by", "requester",
                 "`low`", "`medium`", "`high`", "[capture]", "<YYYYMMDDHHMMSS>-<slug>.md"):
        assert word in body, word
    assert "scripts/backlog.py capture" in body


# --- capture (AC2, R2-R5) ------------------------------------------------------

def test_capture_writes_one_inbox_idea_named_from_utc_time(repo):
    before = utc_now()
    result = capture(repo)
    after = utc_now()
    assert result.returncode == 0, result.stderr
    [idea] = ideas(repo)
    match = re.fullmatch(r"(\d{14})-track-ideas\.md", idea.name)
    assert match, idea.name
    stamp = datetime.strptime(match.group(1), "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    assert before <= stamp <= after
    assert idea.relative_to(repo).as_posix() in result.stdout


def test_capture_front_matter(repo):
    capture(repo)
    [idea] = ideas(repo)
    data = yaml.safe_load(split_front_matter(idea.read_text())[0])
    assert data["title"] == "Ideas get lost"
    assert data["status"] == "inbox"
    assert data["requester"] == OWNER, "requester is git config user.name (A1)"
    assert str(data["date"]) == utc_now().strftime("%Y-%m-%d")
    assert data["effort"] == "medium" and data["impact"] == "high"


def test_capture_keeps_the_request_word_for_word_and_marks_the_problem(repo):
    capture(repo)
    [idea] = ideas(repo)
    body = split_front_matter(idea.read_text())[1]
    assert REQUEST in body
    problem_line = next(line for line in body.splitlines() if PROBLEM in line)
    assert "AI draft" in problem_line


def test_capture_logs_who_proposed_effort_and_impact(repo):
    capture(repo)
    [idea] = ideas(repo)
    log = idea.read_text().split("\n# Log\n", 1)[1]
    [line] = [line for line in log.splitlines() if "[capture]" in line]
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \[capture\] ", line), line
    assert "Effort medium, impact high proposed by the AI." in line


def test_capture_creates_the_folder_and_readme(repo):
    assert not (repo / "docs").exists()
    capture(repo)
    readme = (repo / "docs" / "backlog" / "README.md").read_text()
    assert README_HEADER in readme.splitlines()
    assert "track-ideas" not in readme, "the README lists only triaged ideas (A4)"


def test_capture_never_overwrites_the_readme(repo):
    readme = repo / "docs" / "backlog" / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("# Our ideas\n\nHand-made.\n")
    assert capture(repo).returncode == 0
    assert readme.read_text() == "# Our ideas\n\nHand-made.\n"
    assert len(ideas(repo)) == 1


def test_capture_refuses_an_existing_idea_file(repo):
    folder = repo / "docs" / "backlog"
    folder.mkdir(parents=True)
    start = utc_now()
    taken = [folder / f"{(start + timedelta(seconds=s)).strftime('%Y%m%d%H%M%S')}-track-ideas.md" for s in range(-1, 10)]
    for path in taken:
        path.write_text("mine\n")
    result = capture(repo)
    assert result.returncode == 1
    assert result.stdout.startswith("FAIL:") or result.stderr.startswith("FAIL:")
    assert all(p.read_text() == "mine\n" for p in taken)
    assert ideas(repo) == sorted(taken)


@pytest.mark.parametrize("flag,value", [("effort", "huge"), ("impact", "none")])
def test_capture_refuses_an_unknown_level(repo, flag, value):
    result = capture(repo, **{flag: value})
    assert result.returncode != 0
    assert not (repo / "docs" / "backlog").exists() or ideas(repo) == []

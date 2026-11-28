"""backlog.py and BACKLOG.md: the scripted file writes of the backlog stage (T1 capture, T2 digest and decide, T3 commit)."""
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest
import yaml

from checks import triage_digest_problems
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


def test_stage_names_the_triage_steps():
    body = split_front_matter(STAGE.read_text())[1]
    for word in ("scripts/backlog.py digest", "scripts/backlog.py decide", "[triage]", "keep", "park", "renew", "drop"):
        assert word in body, word


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


# --- triage: digest and decide (T2; AC3, AC4, R6-R11) ---------------------------

def write_idea(root, slug, status, review_by="", title=None, effort="medium", impact="high"):
    folder = root / "docs" / "backlog"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"20261101000000-{slug}.md"
    path.write_text(f"""---
title: "{title or slug}"
status: {status}
requester: "Ada Owner"
date: 2026-11-01
effort: {effort}
impact: {impact}
review_by: {review_by}
---

# {title or slug}

**Raw request:** {slug}

# Log

2026-11-01T00:00:00Z [capture] Captured for Ada Owner. Status {status}.
""")
    return path


def rel(root, path):
    return path.relative_to(root).as_posix()


def meta(path):
    return yaml.safe_load(split_front_matter(path.read_text())[0])


def triage_lines(path):
    log = path.read_text().split("\n# Log\n", 1)[1]
    return [line for line in log.splitlines() if "[triage]" in line]


def decide(root, path, decision, *flags):
    return run(root, "decide", rel(root, path), decision, *flags)


def today():
    return utc_now().date()


def readme_rows(root):
    return [line for line in (root / "docs" / "backlog" / "README.md").read_text().splitlines()
            if line.startswith("| [")]


def test_digest_lists_inbox_and_stale_parked_ideas_only(repo):
    yesterday = (today() - timedelta(days=1)).isoformat()
    inbox = write_idea(repo, "new-one", "inbox")
    stale = write_idea(repo, "stale-park", "parked", review_by=yesterday)
    listed = {inbox: "inbox", stale: "parked"}
    hidden = [write_idea(repo, "fresh-park", "parked", review_by=today().isoformat()),
              write_idea(repo, "later-park", "parked", review_by=(today() + timedelta(days=30)).isoformat()),
              write_idea(repo, "kept", "triaged"),
              write_idea(repo, "gone", "dropped"),
              write_idea(repo, "started", "committed")]
    before = {p: p.read_text() for p in ideas(repo)}
    result = run(repo, "digest")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    for path, status in listed.items():
        [line] = [line for line in lines if path.name in line]
        assert status in line, line
    [stale_line] = [line for line in lines if stale.name in line]
    assert yesterday in stale_line, "a stale park names its review_by"
    for path in hidden:
        assert path.name not in result.stdout, path.name
    assert {p: p.read_text() for p in ideas(repo)} == before, "digest changes no file (R7)"


def test_decide_keep_sets_triaged_logs_confirmed_levels_and_adds_the_row(repo):
    capture(repo)
    [idea] = ideas(repo)
    result = decide(repo, idea, "keep", "--effort", "low", "--impact", "high", "--reason", "Small and useful")
    assert result.returncode == 0, result.stdout + result.stderr
    data = meta(idea)
    assert data["status"] == "triaged"
    assert data["effort"] == "low" and data["impact"] == "high"
    [line] = triage_lines(idea)
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \[triage\] ", line), line
    assert "Small and useful" in line and OWNER in line
    assert "Effort low, impact high confirmed by" in line
    [row] = readme_rows(repo)
    assert row.startswith(f"| [Ideas get lost]({idea.name}) | low | high |"), row


def test_decide_keep_adds_a_row_below_the_existing_ones(repo):
    capture(repo)
    [idea] = ideas(repo)
    readme = repo / "docs" / "backlog" / "README.md"
    readme.write_text(readme.read_text() + "| [Old](old.md) | high | high | hand-made |\n\nAfter the table.\n")
    assert decide(repo, idea, "keep", "--effort", "medium", "--impact", "high", "--reason", "Yes").returncode == 0
    rows = readme_rows(repo)
    assert rows[0] == "| [Old](old.md) | high | high | hand-made |"
    assert idea.name in rows[1] and len(rows) == 2
    assert readme.read_text().rstrip().endswith("After the table.")


def test_decide_park_sets_review_by_and_removes_the_row(repo):
    capture(repo)
    [idea] = ideas(repo)
    decide(repo, idea, "keep", "--effort", "medium", "--impact", "high", "--reason", "Yes")
    by = (today() + timedelta(days=60)).isoformat()
    result = decide(repo, idea, "park", "--by", by, "--reason", "Waits on review stage")
    assert result.returncode == 0, result.stdout + result.stderr
    data = meta(idea)
    assert data["status"] == "parked" and str(data["review_by"]) == by
    line = triage_lines(idea)[-1]
    assert "Waits on review stage" in line and OWNER in line and by in line
    assert readme_rows(repo) == []


def test_decide_park_without_a_date_changes_nothing(repo):
    """A3: a park gets no default date; triage asks the owner for one."""
    idea = write_idea(repo, "no-date", "inbox")
    before = idea.read_text()
    result = decide(repo, idea, "park", "--reason", "Later")
    assert result.returncode != 0
    assert "FAIL:" in result.stdout + result.stderr
    assert idea.read_text() == before


def test_decide_renew_moves_review_by_and_stays_parked(repo):
    old = (today() - timedelta(days=1)).isoformat()
    idea = write_idea(repo, "renew-me", "parked", review_by=old)
    by = (today() + timedelta(days=90)).isoformat()
    result = decide(repo, idea, "renew", "--by", by, "--reason", "Still blocked")
    assert result.returncode == 0, result.stdout + result.stderr
    data = meta(idea)
    assert data["status"] == "parked" and str(data["review_by"]) == by
    line = triage_lines(idea)[-1]
    assert "Still blocked" in line and OWNER in line and by in line


def test_decide_drop_sets_dropped_and_removes_the_row(repo):
    capture(repo)
    [idea] = ideas(repo)
    decide(repo, idea, "keep", "--effort", "medium", "--impact", "high", "--reason", "Yes")
    result = decide(repo, idea, "drop", "--reason", "Not worth it")
    assert result.returncode == 0, result.stdout + result.stderr
    assert meta(idea)["status"] == "dropped"
    line = triage_lines(idea)[-1]
    assert "Not worth it" in line and OWNER in line
    assert readme_rows(repo) == []


def test_decide_keeps_the_rest_of_the_file(repo):
    capture(repo)
    [idea] = ideas(repo)
    decide(repo, idea, "drop", "--reason", "No")
    text = idea.read_text()
    assert REQUEST in text and PROBLEM in text
    assert len([line for line in text.splitlines() if "[capture]" in line]) == 1


@pytest.mark.parametrize("args", [("maybe", "--reason", "x"), ("park", "--by", "soon", "--reason", "x"),
                                  ("keep", "--effort", "huge", "--impact", "high", "--reason", "x")])
def test_decide_refuses_bad_input(repo, args):
    idea = write_idea(repo, "bad-input", "inbox")
    before = idea.read_text()
    result = decide(repo, idea, *args)
    assert result.returncode != 0
    assert idea.read_text() == before


def test_decide_refuses_a_missing_idea(repo):
    result = run(repo, "decide", "docs/backlog/20261101000000-nope.md", "drop", "--reason", "x")
    assert result.returncode == 1
    assert result.stdout.startswith("FAIL:")


# --- commit (T3; AC5, R12-R14) ---------------------------------------------------

TEMPLATE = PLUGIN / "templates" / "STATE.md"


@pytest.fixture
def kairyn_repo(repo):
    templates = repo / ".kairyn" / "templates"
    templates.mkdir(parents=True)
    (templates / "STATE.md").write_text(TEMPLATE.read_text())
    return repo


def commit(root, path):
    return run(root, "commit", rel(root, path))


def task_folder(root, slug):
    return root / "docs" / "tasks" / f"{today().isoformat()}-{slug}"


def test_stage_names_the_commit_steps():
    body = split_front_matter(STAGE.read_text())[1]
    for word in ("scripts/backlog.py commit", "[commit]", "triaged"):
        assert word in body, word


def test_commit_sets_committed_and_logs_the_task_folder(kairyn_repo):
    idea = write_idea(kairyn_repo, "ship-it", "triaged", title="Ship it")
    result = commit(kairyn_repo, idea)
    assert result.returncode == 0, result.stdout + result.stderr
    assert meta(idea)["status"] == "committed"
    log = idea.read_text().split("\n# Log\n", 1)[1]
    [line] = [line for line in log.splitlines() if "[commit]" in line]
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \[commit\] ", line), line
    assert OWNER in line
    assert f"docs/tasks/{today().isoformat()}-ship-it/" in line, "close links the idea through this line (ADR 0026)"
    assert len([line for line in log.splitlines() if "[capture]" in line]) == 1


def test_commit_writes_state_from_the_template_naming_the_idea(kairyn_repo):
    idea = write_idea(kairyn_repo, "ship-it", "triaged", title="Ship it")
    before = utc_now()
    assert commit(kairyn_repo, idea).returncode == 0
    after = utc_now()
    state = task_folder(kairyn_repo, "ship-it") / "STATE.md"
    assert state.is_file()
    text = state.read_text()
    assert "<YYYY" not in text and "<slug>" not in text and "<task title>" not in text, "no placeholder is left"
    data = yaml.safe_load(split_front_matter(text)[0])
    assert data["task"] == f"{today().isoformat()}-ship-it"
    assert data["title"] == "Ship it"
    assert data["stage"] == "requirements" and data["status"] == "in-progress"
    for key in ("created", "updated"):
        stamp = datetime.strptime(str(data[key]).replace("+00:00", "Z").replace(" ", "T"), "%Y-%m-%dT%H:%M:%SZ")
        assert before <= stamp.replace(tzinfo=timezone.utc) <= after, key
    log = text.split("\n# Log\n", 1)[1]
    [line] = [line for line in log.splitlines() if line.startswith("- ") and "[requirements]" in line]
    assert rel(kairyn_repo, idea) in line, "STATE.md names the idea file (R12)"


def test_commit_prints_the_two_next_commands(kairyn_repo):
    idea = write_idea(kairyn_repo, "ship-it", "triaged")
    result = commit(kairyn_repo, idea)
    folder = f"docs/tasks/{today().isoformat()}-ship-it"
    assert f"/kairyn:grill {folder}" in result.stdout
    assert f"/kairyn:requirements {folder}" in result.stdout


@pytest.mark.parametrize("status", ["inbox", "parked", "dropped", "committed"])
def test_commit_refuses_an_idea_that_is_not_triaged(kairyn_repo, status):
    idea = write_idea(kairyn_repo, "not-ready", status)
    before = idea.read_text()
    result = commit(kairyn_repo, idea)
    assert result.returncode == 1
    assert result.stdout.startswith("FAIL:")
    assert len(result.stdout.strip().splitlines()) == 1, "one FAIL: line"
    assert idea.read_text() == before
    assert not (kairyn_repo / "docs" / "tasks").exists()


def test_commit_refuses_an_existing_task_folder(kairyn_repo):
    idea = write_idea(kairyn_repo, "ship-it", "triaged")
    folder = task_folder(kairyn_repo, "ship-it")
    folder.mkdir(parents=True)
    (folder / "STATE.md").write_text("mine\n")
    before = idea.read_text()
    result = commit(kairyn_repo, idea)
    assert result.returncode == 1
    assert result.stdout.startswith("FAIL:")
    assert idea.read_text() == before
    assert (folder / "STATE.md").read_text() == "mine\n"
    assert [p.name for p in folder.iterdir()] == ["STATE.md"]


def test_commit_refuses_a_missing_idea(kairyn_repo):
    result = run(kairyn_repo, "commit", "docs/backlog/20261101000000-nope.md")
    assert result.returncode == 1
    assert result.stdout.startswith("FAIL:")
    assert not (kairyn_repo / "docs" / "tasks").exists()


# --- the triage_digest eval check (AC3, R6) ----------------------------------

DUE = ["20261101000000-column-picker.md", "20261102000000-slow-search.md"]
FRESH = "20261103000000-dark-mode.md"
PICKER = "- column-picker: keep, because users export CSV files every week."
SEARCH = "- slow-search: drop, because the search was fixed already."


def digest(reply, changed=()):
    return triage_digest_problems({"due": DUE, "fresh": FRESH, "turns": [{"reply": reply, "changed": list(changed)}]})


@pytest.mark.parametrize("reply", [
    f"{PICKER}\n{SEARCH}\n\nWhich do you keep, park or drop?",
    "Due: column picker, slow search.\n\n### Column picker\n\nProposal: **Keep**\nReason: users export every week.\n\n"
    "### Slow search\n\nProposal: **Drop**\nReason: it was fixed already.",
    "| Idea | Proposal | Reason |\n|---|---|---|\n| column-picker | keep | users export every week |\n"
    "| slow-search | park | no new reports since January |",
])
def test_a_proposal_and_reason_per_due_idea_pass(reply):
    assert digest(reply) == []


@pytest.mark.parametrize("fresh", ["Dark mode", "dark-mode", FRESH])
def test_a_park_that_is_not_due_fails(fresh):
    assert digest(f"{PICKER}\n{SEARCH}\n- {fresh}: park, because nobody asked for it lately.")


@pytest.mark.parametrize("search", [
    "- slow-search (parked until 2026-01-01, effort medium, impact medium)",
    "- slow-search\n\nReply keep, park or drop for each, with your reason.",
])
def test_a_due_idea_with_no_proposal_fails(search):
    assert digest(f"{PICKER}\n{search}") == [f"no proposal with a reason for {DUE[1]}"]


@pytest.mark.parametrize("search", [
    "- slow-search: drop",
    "| slow-search | drop | effort medium, impact medium |",
])
def test_a_proposal_with_no_reason_fails(search):
    assert digest(f"{PICKER}\n{search}") == [f"no proposal with a reason for {DUE[1]}"]


def test_a_missing_idea_and_an_early_change_fail():
    problems = digest(PICKER, changed=["docs/backlog/README.md"])
    assert f"reply does not name {DUE[1]}" in problems
    assert "changed before the owner answered: docs/backlog/README.md" in problems

"""Helpers that drive real `claude` sessions. Used by the promptfoo provider and judge."""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from helpers import PLUGIN, ROOT

MODEL = os.environ.get("KAIRYN_MODEL")
JUDGE_MODEL = os.environ.get("KAIRYN_JUDGE_MODEL", MODEL)

REQUEST = "Add a --dry-run flag to the CLI that prints what would change without writing files."

# The wrapper (evals/run.py) sets this per run; evidence for every run is saved under it.
RESULTS = Path(os.environ.get("KAIRYN_RESULTS_DIR", ROOT / "evals" / "results" / "adhoc"))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Cost per run: provider.py points this at the run's evidence folder; each call appends to cost.jsonl there.
_COST_DIR: Path | None = None
# Headless runs cannot answer questions. The requirements judge is told this too, so recording it is not invention.
NO_QUESTIONS = "Do not ask questions; make reasonable assumptions and record them."


def set_cost_dir(path: Path | None) -> None:
    global _COST_DIR
    _COST_DIR = path


def cost_of(output: str) -> float | None:
    """total_cost_usd from `claude -p --output-format json`: a client-side estimate, not the bill."""
    try:
        cost = json.loads(output).get("total_cost_usd")
    except (ValueError, AttributeError):
        return None
    return float(cost) if isinstance(cost, (int, float)) else None


def record_cost(run_dir: Path | None, role: str, usd: float | None) -> None:
    if run_dir is None or usd is None:
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "cost.jsonl").open("a") as f:
        f.write(json.dumps({"role": role, "usd": usd}) + "\n")


def _result(output: str) -> str:
    try:
        data = json.loads(output)
    except ValueError:
        return output
    return (data.get("result") or "") if isinstance(data, dict) else output


def claude(prompt: str, cwd: Path, *, plugin: bool = False, model: str | None = None, timeout: int = 600,
           role: str = "run", cost_dir: Path | None = None, add_dirs: tuple = ()) -> str:
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "json"]
    for extra in add_dirs:
        cmd += ["--add-dir", str(extra)]
    if plugin:
        cmd += ["--plugin-dir", str(PLUGIN)]
    if model:
        cmd += ["--model", model]
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout).stdout
    record_cost(cost_dir or _COST_DIR, role, cost_of(out))
    return _result(out)


def new_repo(parent: Path, name: str) -> Path:
    repo = parent / name
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Sample CLI\n")
    return repo


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


ROUTING_REQUEST = "Cut the model cost of the support-reply feature without lowering answer quality."
ROUTING_TASK = "2026-01-05-cut-reply-cost"
ROUTING_APP = '''"""Support replies: every ticket goes to one large model."""
import anthropic

client = anthropic.Anthropic()


def reply(ticket: str) -> str:
    msg = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Write a support reply to this ticket:\\n{ticket}"}],
    )
    return msg.content[0].text
'''
ROUTING_STATE = f"""---
task: {ROUTING_TASK}
title: Cut reply cost
stage: requirements
status: done
stages:
  requirements: done
created: 2026-01-05T09:00:00Z
updated: 2026-01-05T09:20:00Z
---

# Log

2026-01-05T09:00:00Z [requirements] Task created. {ROUTING_REQUEST}
2026-01-05T09:20:00Z [requirements] Requirements done.
"""
ROUTING_REQUIREMENTS = f"""---
task: {ROUTING_TASK}
stage: requirements
summary: "Cut support-reply model cost and keep answer quality."
---

# Requirements

## Problem statement
{ROUTING_REQUEST} `support/reply.py` sends every ticket to one large model.

## Scope
- In: model cost of `support/reply.py` (request)
- Out: changes to the reply prompt

## Assumptions
- A1: Answer quality is measured on an eval set the team owns.

## Acceptance criteria
- [ ] Model cost per reply goes down (request)
- [ ] Answer quality stays at the team's bar (request, A1)

## Open questions
None.
"""


def make_routing_repo(repo: Path) -> Path:
    """An initialized repo with one LLM feature and a finished requirements task."""
    (repo / "support").mkdir()
    (repo / "support" / "reply.py").write_text(ROUTING_APP)
    task = repo / "docs" / "tasks" / ROUTING_TASK
    task.mkdir(parents=True)
    (task / "STATE.md").write_text(ROUTING_STATE)
    (task / "REQUIREMENTS.md").write_text(ROUTING_REQUIREMENTS)
    return repo


def run_model_routing(repo: Path) -> dict:
    start = utcnow()
    claude(f"/kairyn:model-routing docs/tasks/{ROUTING_TASK}/ Do not ask questions.",   # through its skill
           repo, plugin=True, model=MODEL)
    return {"task": repo / "docs" / "tasks" / ROUTING_TASK, "start": start, "end": utcnow()}


def run_requirements(repo: Path) -> dict:
    start = utcnow()
    # Through its skill. requirements_with_concept and requirements_approval follow the stage file directly.
    claude(f"/kairyn:requirements {REQUEST} {NO_QUESTIONS}",
           repo, plugin=True, model=MODEL)
    end = utcnow()
    tasks = [p for p in (repo / "docs" / "tasks").iterdir() if p.is_dir()] if (repo / "docs" / "tasks").is_dir() else []
    return {"task": tasks[0] if len(tasks) == 1 else None, "start": start, "end": end}


def claude_session(prompts: list, cwd: Path, *, plugin: bool = False, model: str | None = None,
                   on_turn=None, timeout: int = 600) -> list[str]:
    """One conversation, one prompt per turn (a scripted user). on_turn(i, reply) runs after each turn.
    A prompt can be a callable: it gets the replies so far and returns the prompt."""
    replies, session = [], None
    for i, prompt in enumerate(prompts):
        if callable(prompt):
            prompt = prompt(replies)
        cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "json"]
        if session:
            cmd += ["--resume", session]
        if plugin:
            cmd += ["--plugin-dir", str(PLUGIN)]
        if model:
            cmd += ["--model", model]
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout).stdout
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            data = {"result": out}
        session = data.get("session_id") or session
        replies.append(data.get("result") or "")
        if on_turn:
            on_turn(i, replies[-1])
    # On --resume, total_cost_usd is the conversation total so far, so only the last turn counts.
    record_cost(_COST_DIR, "run", cost_of(out) if replies else None)
    return replies


# --- grill stage -------------------------------------------------------------------
# A solution-first, vague request ("a cache", "faster") on a repo that already answers the basic facts.
GRILL_REQUEST = "Add a cache to the report so it is faster."
GRILL_APP = '''"""Print order totals per customer from data/orders.csv."""
import csv
from collections import defaultdict


def totals(path="data/orders.csv"):
    sums = defaultdict(float)
    with open(path) as f:
        for row in csv.DictReader(f):
            sums[row["customer"]] += float(row["amount"])
    return sums


if __name__ == "__main__":
    for customer, total in sorted(totals().items()):
        print(f"{customer}\t{total:.2f}")
'''
GRILL_README = ("# Order report\n\n`python report.py` prints the total per customer from `data/orders.csv`.\n"
                "The CSV is exported once a night and has about 5 million rows. Python 3.12, no dependencies.\n")
# Scripted user: accept twice, stop, then approve the concept. Each answer fits any question, so the run does not
# depend on wording. The stop is not approval: only "Approved." records the line and hands off to requirements.
GRILL_ANSWERS = ["I accept your recommendation.", "I accept your recommendation.", "Stop the interview now.", "Approved."]


def make_grill_repo(repo: Path) -> Path:
    (repo / "report.py").write_text(GRILL_APP)
    (repo / "README.md").write_text(GRILL_README)
    return repo


def task_dirs(repo: Path) -> list[Path]:
    root = repo / "docs" / "tasks"
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def run_grill(repo: Path) -> dict:
    """Five turns: /kairyn:grill, two accepted recommendations, a stop, an approval. Snapshots STATE.md and CONCEPT.md."""
    subprocess.run(["git", "config", "user.name", APPROVER], cwd=repo, check=True)
    turns = []

    def snapshot(i, reply):
        tasks = task_dirs(repo)
        read = lambda name: (tasks[0] / name).read_text() if len(tasks) == 1 and (tasks[0] / name).exists() else ""
        turns.append({"reply": reply, "state": read("STATE.md"), "concept": read("CONCEPT.md")})

    start = utcnow()
    claude_session([f"/kairyn:grill {GRILL_REQUEST}", *GRILL_ANSWERS], repo, plugin=True, model=MODEL, on_turn=snapshot)
    tasks = task_dirs(repo)
    return {"task": tasks[0] if len(tasks) == 1 else None, "turns": turns, "start": start, "end": utcnow()}


# requirements on a task that grill already shaped: CONCEPT.md decides what the request leaves open.
CONCEPT_TASK = "2026-01-06-report-cache"
CONCEPT_DECISIONS = ("D1", "D2", "D3")
CONCEPT_VALUE = "1 second"
CONCEPT_STATE = f"""---
task: {CONCEPT_TASK}
title: Report cache
stage: requirements
status: in-progress
stages:
  requirements: pending
  grill: done
created: 2026-01-06T09:00:00Z
updated: 2026-01-06T09:30:00Z
---

# Log

2026-01-06T09:00:00Z [grill] Task created. {GRILL_REQUEST}
2026-01-06T09:30:00Z [grill] User confirmed the concept. D1 to D3 recorded.
"""
CONCEPT_MD = f"""---
task: {CONCEPT_TASK}
stage: grill
summary: "Repeat runs on an unchanged CSV must finish in under 1 second."
---

# Concept

## Concept
Each run parses the full nightly CSV again. Repeat runs on an unchanged CSV must finish in under 1 second.

## Decisions
- D1: The problem is repeat runs on an unchanged CSV. The first run after an export stays as it is. (user)
- D2: "Faster" means a repeat run finishes in under 1 second. (user)
- D3: A stored result is invalid when the CSV modification time or size changes. (user)

## Terms
| Term | Meaning |
|---|---|
| repeat run | A run on a CSV that did not change since the last run. |

## Open branches
None.
"""


def make_concept_repo(repo: Path) -> Path:
    task = make_grill_repo(repo) / "docs" / "tasks" / CONCEPT_TASK
    task.mkdir(parents=True)
    (task / "STATE.md").write_text(CONCEPT_STATE)
    (task / "CONCEPT.md").write_text(CONCEPT_MD)
    return repo


def run_requirements_with_concept(repo: Path) -> dict:
    claude(
        # The handoff grill names at its end: the user runs requirements on the task folder.
        "Follow the stage definition in .kairyn/stages/REQUIREMENTS.md exactly "
        f"for the task docs/tasks/{CONCEPT_TASK}/. {NO_QUESTIONS}",
        repo, model=MODEL,
    )
    return {"tasks": task_dirs(repo)}


# requirements, then approval in the same conversation: a reply that does not approve, then one that does.
APPROVER = "Eval User"
APPROVAL_WORDS = "Approved"
APPROVAL_ANSWERS = ["Thanks. I will read it later.", f"{APPROVAL_WORDS}."]


def run_requirements_approval(repo: Path) -> dict:
    """Three turns: the stage, a non-approval, an approval. Snapshots STATE.md and REQUIREMENTS.md per turn."""
    subprocess.run(["git", "config", "user.name", APPROVER], cwd=repo, check=True)
    turns = []

    def snapshot(i, reply):
        tasks = task_dirs(repo)
        read = lambda name: (tasks[0] / name).read_text() if len(tasks) == 1 and (tasks[0] / name).exists() else ""
        turns.append({"reply": reply, "state": read("STATE.md"), "requirements": read("REQUIREMENTS.md")})

    start = utcnow()
    claude_session([
        "Follow the stage definition in .kairyn/stages/REQUIREMENTS.md exactly. "
        f"Request: {REQUEST} Do not ask clarifying questions; make reasonable assumptions and record them.",
        *APPROVAL_ANSWERS], repo, model=MODEL, on_turn=snapshot)
    tasks = task_dirs(repo)
    return {"task": tasks[0] if len(tasks) == 1 else None, "turns": turns, "start": start, "end": utcnow()}


# --- design stage ------------------------------------------------------------------
# The report CLI with an approved requirements task. Design reads it and writes DESIGN.md.
DESIGN_TASK = "2026-01-09-customer-filter"
DESIGN_REQUEST = "Add a --customer flag to report.py that prints the total for one customer."
DESIGN_STATE = f"""---
task: {DESIGN_TASK}
title: Customer filter
stage: design
status: in-progress
stages:
  requirements: done
  design: pending
created: 2026-01-09T09:00:00Z
updated: 2026-01-09T09:30:00Z
---

# Log

2026-01-09T09:00:00Z [requirements] Task created. {DESIGN_REQUEST}
2026-01-09T09:30:00Z [requirements] User approved in chat ("Approved."). Next stage: design.
"""
DESIGN_REQUIREMENTS = f"""---
task: {DESIGN_TASK}
stage: requirements
summary: "A --customer flag prints the total for one customer."
---

# Requirements: Customer filter

## Problem statement
{DESIGN_REQUEST} Today `report.py` prints every customer.

## Scope
In: a `--customer` flag on `report.py` (request)
Out: other filters, output formats

## Requirements
- R1: When the user passes `--customer <name>`, the report shall print only that customer's total. (request)
- R2: If no row matches the name, the report shall print "no orders for <name>" and exit with code 1. (A1)
- R3: When the user passes no flag, the report shall print every customer, as today. (request)

## Non-functional needs
- Accessibility: not applicable: text output only.
- Performance: not applicable: no source states a limit.
- Security: not applicable: no new input source.
- Observability: not applicable: no logs today.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | A missing customer is an error, not an empty line. | user |

## Acceptance criteria
- [ ] `python report.py --customer acme` prints one line for acme. (R1)
- [ ] An unknown name prints the message and exits with code 1. (R2)
- [ ] `python report.py` prints the same output as before. (R3)

## Open questions and answers
None.

Approval: Eval User, 2026-01-09T09:30:00Z, "Approved"
"""
DESIGN_ORDERS = "customer,amount\nacme,10.00\nglobex,5.50\nacme,2.25\n"


def make_design_repo(repo: Path) -> Path:
    make_grill_repo(repo)
    (repo / "data").mkdir(exist_ok=True)
    (repo / "data" / "orders.csv").write_text(DESIGN_ORDERS)
    task = repo / "docs" / "tasks" / DESIGN_TASK
    task.mkdir(parents=True)
    (task / "STATE.md").write_text(DESIGN_STATE)
    (task / "REQUIREMENTS.md").write_text(DESIGN_REQUIREMENTS)
    return repo


def run_design(repo: Path) -> dict:
    start = utcnow()
    claude(f"/kairyn:design docs/tasks/{DESIGN_TASK}/ {NO_QUESTIONS}", repo, plugin=True, model=MODEL)   # through its skill
    return {"task": repo / "docs" / "tasks" / DESIGN_TASK, "start": start, "end": utcnow()}


def run_design_approval(repo: Path) -> dict:
    """Four turns: the stage, a non-approval, 'go with option X' (a rejected option), an approval."""
    from checks import rejected_option
    subprocess.run(["git", "config", "user.name", APPROVER], cwd=repo, check=True)
    task, turns = repo / "docs" / "tasks" / DESIGN_TASK, []

    def read(name):
        return (task / name).read_text() if (task / name).exists() else ""

    def snapshot(i, reply):
        turns.append({"reply": reply, "state": read("STATE.md"), "design": read("DESIGN.md")})

    picked = []

    def pick_option(replies):   # turn 2 names an option that turn 0 rejected
        picked.append(rejected_option(turns[0]["design"]) if turns else None)
        return f"Go with option {picked[0] or 'B'} instead."

    start = utcnow()
    claude_session([
        f"Follow the stage definition in .kairyn/stages/DESIGN.md exactly for the task docs/tasks/{DESIGN_TASK}/. "
        f"{NO_QUESTIONS}",
        APPROVAL_ANSWERS[0], pick_option, APPROVAL_ANSWERS[1]], repo, model=MODEL, on_turn=snapshot)
    return {"task": task, "turns": turns, "option": picked[0] if picked else None,
            "start": start, "end": utcnow()}


# A home repo (tasks only) whose afk.yml `repos:` map names one child repo, report-cli, that holds the code.
# The same customer-filter task: design must write `repo: report-cli` in STATE.md (multi-repo R14).
DESIGN_CHILD = "report-cli"
DESIGN_CHILD_REQUIREMENTS = DESIGN_REQUIREMENTS.replace(
    "Today `report.py` prints every customer.",
    f"Today `report.py` prints every customer. The code is in the child repo {DESIGN_CHILD} (`../{DESIGN_CHILD}`), "
    "not in this home repo.")
DESIGN_CHILD_REPOS = f"""
repos:
  {DESIGN_CHILD}:
    path: ../{DESIGN_CHILD}
    gates:
      testing: python3 -m pytest
"""


def make_design_child_repo(repo: Path) -> Path:
    """repo is the home repo (after init). Its sibling report-cli is a git repo with the code and data."""
    child = new_repo(repo.parent, DESIGN_CHILD)
    make_grill_repo(child)
    (child / "data").mkdir(exist_ok=True)
    (child / "data" / "orders.csv").write_text(DESIGN_ORDERS)
    afk = repo / ".kairyn" / "afk.yml"
    afk.write_text(afk.read_text().rstrip("\n") + "\n" + DESIGN_CHILD_REPOS)
    task = repo / "docs" / "tasks" / DESIGN_TASK
    task.mkdir(parents=True)
    (task / "STATE.md").write_text(DESIGN_STATE)
    (task / "REQUIREMENTS.md").write_text(DESIGN_CHILD_REQUIREMENTS)
    return repo


def run_design_child(repo: Path) -> dict:
    start = utcnow()
    claude(f"/kairyn:design docs/tasks/{DESIGN_TASK}/ {NO_QUESTIONS}", repo, plugin=True, model=MODEL,
           add_dirs=(repo.parent / DESIGN_CHILD,))
    return {"task": repo / "docs" / "tasks" / DESIGN_TASK, "start": start, "end": utcnow()}


# --- close stage --------------------------------------------------------------------
# Two done, approved tasks: one with a load-bearing decision (D1 → an ADR), one with none (no ADR).
CLOSE_DECISION_TASK = "2026-01-07-history-store"
CLOSE_PLAIN_TASK = "2026-01-08-help-typo"
CLOSE_KEYWORD = "SQLite"
CLOSE_TASKS = {
    CLOSE_DECISION_TASK: ("Keep a history of report runs.",
                         "- R1: When a report runs, the CLI shall store its totals in `data/history.db`. (D1)",
                         "- D1: Store history in SQLite, not a JSON file. A JSON file is rewritten in full on each run, "
                         "and SQLite adds no dependency to Python 3.12. (user)"),
    CLOSE_PLAIN_TASK: ("Fix the typo 'totla' in the --help text.",
                      "- R1: The --help text shall spell 'total' correctly. (request)", ""),
}


def close_task_files(task: str) -> dict[str, str]:
    request, req, decision = CLOSE_TASKS[task]
    state = (f"---\ntask: {task}\ntitle: {request}\nstage: requirements\nstatus: done\nstages:\n  requirements: done\n"
             f"created: 2026-01-07T09:00:00Z\nupdated: 2026-01-07T10:00:00Z\n---\n\n# Log\n\n"
             f"2026-01-07T09:00:00Z [requirements] Task created. {request}\n"
             f"2026-01-07T10:00:00Z [build] Built and merged in pull request #4.\n")
    reqs = (f"---\ntask: {task}\nstage: requirements\nsummary: \"{request}\"\n---\n\n# Requirements\n\n"
            f"## Problem statement\n{request}\n\n## Requirements\n{req}\n\n## Acceptance criteria\n- [ ] R1 holds. (R1)\n\n"
            f"## Open questions and answers\n{decision or 'None.'}\n\n"
            f"Approval: Eval User, 2026-01-07T09:30:00Z, \"Approved\"\n")
    return {"STATE.md": state, "REQUIREMENTS.md": reqs}


def make_close_repo(repo: Path, task: str) -> Path:
    folder = repo / "docs" / "tasks" / task
    folder.mkdir(parents=True)
    for name, text in close_task_files(task).items():
        (folder / name).write_text(text)
    backlog = repo / "docs" / "backlog"
    backlog.mkdir(parents=True)
    item = "---\ntitle: {t}\nstatus: {s}\n---\n\n# {t}\n\n{b}\n\n# Log\n"
    (backlog / "1-linked.md").write_text(item.format(t="Linked", s="committed", b=f"Task [{task}](../tasks/{task}/REQUIREMENTS.md)."))
    (backlog / "2-parked.md").write_text(item.format(t="Parked", s="parked", b="Later."))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=Eval User", "-c", "user.email=eval@example.com", "commit", "-qm", "fixture"],
                   cwd=repo, check=True)
    return repo


# A task built and merged by hand: in progress at build, no REVIEW.md, no PR #<n> in STATE.md. The stub gh
# (tests/stubs/gh_prs, set in the repo's .claude/settings.json) reports PR #4 merged from branch jisundr/csv-export.
CLOSE_HAND_TASK = "2026-01-09-csv-export"
CLOSE_HAND_PRS = [
    {"number": 3, "state": "MERGED", "headRefName": "jisundr/readme-typo", "mergedAt": "2026-01-08T11:00:00Z",
     "mergedBy": {"login": "evaluser", "name": "Eval User"}},
    {"number": 4, "state": "MERGED", "headRefName": "jisundr/csv-export", "mergedAt": "2026-01-09T15:30:00Z",
     "mergedBy": {"login": "evaluser", "name": "Eval User"}},
]


def make_hand_merged_close_repo(repo: Path) -> Path:
    folder = repo / "docs" / "tasks" / CLOSE_HAND_TASK
    folder.mkdir(parents=True)
    request = "Add a --csv flag that writes the report as CSV."
    (folder / "STATE.md").write_text(
        f"---\ntask: {CLOSE_HAND_TASK}\ntitle: {request}\nstage: build\nstatus: in-progress\nstages:\n"
        "  requirements: done\n  design: done\n  build: pending\n  gates: pending\n  review: pending\n"
        "created: 2026-01-09T09:00:00Z\nupdated: 2026-01-09T14:00:00Z\n---\n\n# Log\n\n"
        f"2026-01-09T09:00:00Z [requirements] Task created. {request}\n"
        "2026-01-09T14:00:00Z [build] Built by hand. Waiting for the pull request review.\n")
    (folder / "REQUIREMENTS.md").write_text(
        f"---\ntask: {CLOSE_HAND_TASK}\nstage: requirements\nsummary: \"{request}\"\n---\n\n# Requirements\n\n"
        f"## Problem statement\n{request}\n\n## Requirements\n- R1: When the user gives --csv, the CLI shall write "
        "the report as CSV. (request)\n\n## Acceptance criteria\n- [ ] R1 holds. (R1)\n\n"
        "## Open questions and answers\nNone.\n\nApproval: Eval User, 2026-01-09T09:30:00Z, \"Approved\"\n")
    backlog = repo / "docs" / "backlog"
    backlog.mkdir(parents=True)
    item = "---\ntitle: {t}\nstatus: {s}\n---\n\n# {t}\n\n{b}\n\n# Log\n"
    (backlog / "1-linked.md").write_text(item.format(t="Linked", s="committed",
                                                     b=f"Task [{CLOSE_HAND_TASK}](../tasks/{CLOSE_HAND_TASK}/REQUIREMENTS.md)."))
    (backlog / "2-parked.md").write_text(item.format(t="Parked", s="parked", b="Later."))
    (repo.parent / "prs.json").write_text(json.dumps(CLOSE_HAND_PRS))
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "settings.json").write_text(json.dumps({"env": {
        "KAIRYN_GH": str(ROOT / "tests" / "stubs" / "gh_prs"), "GH_PRS": str(repo.parent / "prs.json"),
        "GH_LOG": str(repo.parent / "gh.log")}}, indent=2))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=Eval User", "-c", "user.email=eval@example.com", "commit", "-qm", "fixture"],
                   cwd=repo, check=True)
    return repo


def run_close(repo: Path, task: str) -> dict:
    claude(f"/kairyn:close {task}", repo, plugin=True, model=MODEL)
    adr_dir = repo / "docs" / "adr"
    log = repo / "CHANGELOG.md"
    return {"task": task, "task_exists": (repo / "docs" / "tasks" / task).exists(),
            "changelog": log.read_text() if log.is_file() else "",
            "adrs": {p.name: p.read_text() for p in sorted(adr_dir.glob("*.md"))} if adr_dir.is_dir() else {},
            "backlog_left": sorted(p.name for p in (repo / "docs" / "backlog").glob("*.md")),
            "learnings": (repo / ".kairyn" / "learnings.md").read_text()}


# --- retro stage -------------------------------------------------------------------
# A consumer repo whose learnings.md is past half its budget. Each entry has one right action:
#   L1 move (the user's own reporting doc), L2 drop (CLAUDE.md already says it), L3 backlog (a test),
#   L4 backlog (a kairyn-owned template), L5 backlog (its home is full), L6 backlog (CLAUDE.md guards stages),
#   L7 seen once: keep, drop or backlog, never move. L8 backlog (a fix to agent-written code: a lint rule, D20).
RETRO_ENTRIES = [
    "- 2026-01-03 [requirements] Amounts in data/orders.csv are in cents. Divide by 100 before display.",
    "- 2026-01-03 [design] Timestamps come from `date`, never from memory.",
    "- 2026-01-04 [requirements] The CSV parser crashed twice on an empty line in data/orders.csv. A test for empty lines catches it.",
    "- 2026-01-04 [design] The STATE.md template has no field for the pull request link.",
    "- 2026-01-05 [design] Releases are tagged from main only. Never tag a branch.",
    "- 2026-01-05 [design] The design stage did not read the CSV headers. Its step 3 must name data/orders.csv.",
    "- 2026-01-06 [requirements] One report run was slow on a 50 MB file. Seen once.",
    "- 2026-01-07 [review] The agent wrapped a flaky call in `setTimeout` again. Ban it with a lint rule or gate because it hides a race.",
]
RETRO_EXPECTED = {"L1": {"move"}, "L2": {"drop"}, "L3": {"backlog"}, "L4": {"backlog"}, "L5": {"backlog"},
                  "L6": {"backlog"}, "L7": {"keep", "drop", "backlog"},
                  "L8": {"backlog"}}
RETRO_HOMES = {"L1": ".harness/workflows/reporting.md"}
RETRO_OVERFLOW = ("L5",)
RETRO_CLAUDE_RULE = "Change `.kairyn/stages/` only after an eval proves the change."


def _doc(title: str, read_when: str, body: str) -> str:
    return (f"---\ntitle: {title}\nsummary: \"{title}.\"\nread_when: \"{read_when}\"\nload: on-demand\n---\n\n"
            f"# {title}\n\n{body}")


def make_retro_repo(repo: Path) -> Path:
    """Call after make_good_repo (init) and before any commit."""
    (repo / ".kairyn" / "learnings.md").write_text("# Learnings\n\nStages append here.\n\n" + "\n".join(RETRO_ENTRIES) + "\n")
    with (repo / ".harness" / "budgets.yml").open("a") as f:
        f.write('  - {pattern: ".kairyn/learnings.md", max_tokens: 250, load: runtime}\n')
    wf = repo / ".harness" / "workflows"
    (wf / "reporting.md").write_text(_doc("Reporting", "changing the report or its CSV input",
                                          "The report reads `data/orders.csv` and prints totals per customer.\n"))
    full = _doc("Releasing", "tagging or publishing a release", "")
    step = "- Run the tests, update the changelog, and tag the release.\n"
    while len(full) + len(step) <= 3192:   # 798 of 800 tokens: any added rule goes over
        full += step
    (wf / "releasing.md").write_text(full)
    claude_md = repo / "CLAUDE.md"
    claude_md.write_text(f"# Sample CLI\n\n{RETRO_CLAUDE_RULE}\n\n" + claude_md.read_text())
    # As /kairyn:check write does: index the new docs, or the repo fails its own doc check.
    subprocess.run(["python3", str(PLUGIN / "scripts" / "harness_docs.py"), "--write", "--root", str(repo)],
                   check=True, capture_output=True)
    return repo


def commit_all(repo: Path, message: str = "fixture") -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=Eval User", "-c", "user.email=eval@example.com", "commit", "-qm", message],
                   cwd=repo, check=True)


def changed_paths(repo: Path) -> list[str]:
    out = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=repo, capture_output=True, text=True).stdout
    return sorted(line[3:].strip('"') for line in out.splitlines() if line.strip())


def retro_dirs(repo: Path) -> list[Path]:
    return sorted((repo / "docs" / "tasks").glob("*-retro*")) if (repo / "docs" / "tasks").is_dir() else []


def _read(path: Path) -> str:
    return path.read_text() if path.is_file() else ""


def run_retro(repo: Path) -> dict:
    """One turn: /kairyn:retro writes the proposal and stops for approval."""
    commit_all(repo)
    start = utcnow()
    reply = claude("/kairyn:retro", repo, plugin=True, model=MODEL)
    dirs = retro_dirs(repo)
    return {"reply": reply, "retro_dirs": [d.name for d in dirs], "retro": _read(dirs[0] / "RETRO.md") if dirs else "",
            "state": _read(dirs[0] / "STATE.md") if dirs else "", "changed": changed_paths(repo),
            "start": start, "end": utcnow()}


def run_retro_approval(repo: Path) -> dict:
    """Two turns: /kairyn:retro, then the user's approval."""
    from checks import retro_rows
    subprocess.run(["git", "config", "user.name", APPROVER], cwd=repo, check=True)
    commit_all(repo)
    before = {p.relative_to(repo).as_posix(): p.read_text() for p in (repo / ".harness").rglob("*.md")}
    before.update({"CLAUDE.md": _read(repo / "CLAUDE.md")})
    backlog_before = set(p.name for p in (repo / "docs" / "backlog").glob("*.md")) if (repo / "docs" / "backlog").is_dir() else set()
    budgets_before = _read(repo / ".harness" / "budgets.yml")
    turns = []

    def snapshot(i, reply):
        dirs = retro_dirs(repo)
        turns.append({"reply": reply, "retro": _read(dirs[0] / "RETRO.md") if dirs else "", "changed": changed_paths(repo)})

    start = utcnow()
    claude_session(["/kairyn:retro", f"{APPROVAL_WORDS}."], repo, plugin=True, model=MODEL, on_turn=snapshot)
    dirs = retro_dirs(repo)
    retro = _read(dirs[0] / "RETRO.md") if dirs else ""
    homes = {p for _, (action, home, _) in retro_rows(retro).items() if action == "move" for p in re.findall(r"`([^`\s]+)`", home)}
    backlog = repo / "docs" / "backlog"
    return {"entries": RETRO_ENTRIES, "retro": retro, "state": _read(dirs[0] / "STATE.md") if dirs else "",
            "learnings": _read(repo / ".kairyn" / "learnings.md"),
            "backlog": {p.name: p.read_text() for p in backlog.glob("*.md") if p.name not in backlog_before} if backlog.is_dir() else {},
            "homes_before": {h: before.get(h, "") for h in homes}, "homes_after": {h: _read(repo / h) for h in homes},
            "budgets_before": budgets_before, "budgets_after": _read(repo / ".harness" / "budgets.yml"),
            "turns": turns, "approver": APPROVER, "words": APPROVAL_WORDS, "start": start, "end": utcnow()}

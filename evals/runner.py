"""Helpers that drive real `claude` sessions. Used by the promptfoo provider and judge."""
import hashlib
import json
import os
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
           role: str = "run", cost_dir: Path | None = None) -> str:
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "json"]
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


def claude_session(prompts: list[str], cwd: Path, *, plugin: bool = False, model: str | None = None,
                   on_turn=None, timeout: int = 600) -> list[str]:
    """One conversation, one prompt per turn (a scripted user). on_turn(i, reply) runs after each turn."""
    replies, session = [], None
    for i, prompt in enumerate(prompts):
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
# Scripted user: accept twice, then stop. Each answer fits any question, so the run does not depend on wording.
GRILL_ANSWERS = ["I accept your recommendation.", "I accept your recommendation.", "Stop the interview now."]


def make_grill_repo(repo: Path) -> Path:
    (repo / "report.py").write_text(GRILL_APP)
    (repo / "README.md").write_text(GRILL_README)
    return repo


def task_dirs(repo: Path) -> list[Path]:
    root = repo / "docs" / "tasks"
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def run_grill(repo: Path) -> dict:
    """Four turns: /kairyn:grill, two accepted recommendations, a stop. Snapshots STATE.md and CONCEPT.md per turn."""
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


# --- exit stage --------------------------------------------------------------------
# Two done, approved tasks: one with a load-bearing decision (D1 → an ADR), one with none (no ADR).
EXIT_DECISION_TASK = "2026-01-07-history-store"
EXIT_PLAIN_TASK = "2026-01-08-help-typo"
EXIT_KEYWORD = "SQLite"
EXIT_TASKS = {
    EXIT_DECISION_TASK: ("Keep a history of report runs.",
                         "- R1: When a report runs, the CLI shall store its totals in `data/history.db`. (D1)",
                         "- D1: Store history in SQLite, not a JSON file. A JSON file is rewritten in full on each run, "
                         "and SQLite adds no dependency to Python 3.12. (user)"),
    EXIT_PLAIN_TASK: ("Fix the typo 'totla' in the --help text.",
                      "- R1: The --help text shall spell 'total' correctly. (request)", ""),
}


def exit_task_files(task: str) -> dict[str, str]:
    request, req, decision = EXIT_TASKS[task]
    state = (f"---\ntask: {task}\ntitle: {request}\nstage: requirements\nstatus: done\nstages:\n  requirements: done\n"
             f"created: 2026-01-07T09:00:00Z\nupdated: 2026-01-07T10:00:00Z\n---\n\n# Log\n\n"
             f"2026-01-07T09:00:00Z [requirements] Task created. {request}\n"
             f"2026-01-07T10:00:00Z [build] Built and merged in pull request #4.\n")
    reqs = (f"---\ntask: {task}\nstage: requirements\nsummary: \"{request}\"\n---\n\n# Requirements\n\n"
            f"## Problem statement\n{request}\n\n## Requirements\n{req}\n\n## Acceptance criteria\n- [ ] R1 holds. (R1)\n\n"
            f"## Open questions and answers\n{decision or 'None.'}\n\n"
            f"Approval: Eval User, 2026-01-07T09:30:00Z, \"Approved\"\n")
    return {"STATE.md": state, "REQUIREMENTS.md": reqs}


def make_exit_repo(repo: Path, task: str) -> Path:
    folder = repo / "docs" / "tasks" / task
    folder.mkdir(parents=True)
    for name, text in exit_task_files(task).items():
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


def run_exit(repo: Path, task: str) -> dict:
    claude(f"/kairyn:exit {task}", repo, plugin=True, model=MODEL)
    adr_dir = repo / "docs" / "adr"
    log = repo / "CHANGELOG.md"
    return {"task": task, "task_exists": (repo / "docs" / "tasks" / task).exists(),
            "changelog": log.read_text() if log.is_file() else "",
            "adrs": {p.name: p.read_text() for p in sorted(adr_dir.glob("*.md"))} if adr_dir.is_dir() else {},
            "backlog_left": sorted(p.name for p in (repo / "docs" / "backlog").glob("*.md")),
            "learnings": (repo / ".kairyn" / "learnings.md").read_text()}

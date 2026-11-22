"""Helpers that drive real `claude` sessions. Used by the promptfoo provider and judge."""
import hashlib
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


def claude(prompt: str, cwd: Path, *, plugin: bool = False, model: str | None = None, timeout: int = 600) -> str:
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "text"]
    if plugin:
        cmd += ["--plugin-dir", str(PLUGIN)]
    if model:
        cmd += ["--model", model]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout).stdout


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
    claude(
        "Follow the stage definition in .kairyn/stages/MODEL-ROUTING.md exactly "
        f"for the task docs/tasks/{ROUTING_TASK}/. Do not ask questions.",
        repo, model=MODEL,
    )
    return {"task": repo / "docs" / "tasks" / ROUTING_TASK, "start": start, "end": utcnow()}


def run_requirements(repo: Path) -> dict:
    start = utcnow()
    claude(
        "Follow the stage definition in .kairyn/stages/REQUIREMENTS.md exactly. "
        f"Request: {REQUEST} Do not ask questions; make reasonable assumptions and record them.",
        repo, model=MODEL,
    )
    end = utcnow()
    tasks = [p for p in (repo / "docs" / "tasks").iterdir() if p.is_dir()] if (repo / "docs" / "tasks").is_dir() else []
    return {"task": tasks[0] if len(tasks) == 1 else None, "start": start, "end": end}

"""promptfoo provider: runs one real `claude` session for a scenario and returns the evidence as JSON.

The scenario name arrives as the `scenario` test var. Assertions (asserts.py) and the
judge read the JSON; they never call `claude` themselves, so one run feeds every check.
"""
import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "tests")]

from helpers import PLUGIN, ROOT, make_good_repo, run_verify
from runner import (run_idea, RETRO_ENTRIES, make_retro_repo, run_retro, run_retro_approval, DESIGN_REQUEST, DESIGN_REQUIREMENTS, make_design_repo, run_design, run_design_approval, DESIGN_CHILD_REQUIREMENTS, make_design_child_repo, run_design_child, CLOSE_DECISION_TASK, CLOSE_HAND_TASK, CLOSE_PLAIN_TASK, make_close_repo, make_hand_merged_close_repo, run_close, APPROVAL_WORDS, APPROVER, CONCEPT_DECISIONS, CONCEPT_TASK, CONCEPT_VALUE, GRILL_APP, GRILL_README, GRILL_REQUEST, MODEL, REQUEST, RESULTS, ROUTING_REQUEST,
                    claude, make_concept_repo, make_grill_repo, make_routing_repo, new_repo, run_grill, run_model_routing,
                    run_requirements, run_requirements_approval, run_requirements_with_concept, set_cost_dir, tree_hash)

TS = "%Y-%m-%dT%H:%M:%SZ"
ORIGINAL_CLAUDE_MD = "# My project\n\nMy own rules.\n"
BROKEN_DOC = ".harness/workflows/running-stages.md"


def _save(scenario: str, run_id: str, name: str, text: str) -> None:
    path = RESULTS / scenario / run_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def init_fresh(work: Path, scenario: str, run_id: str) -> dict:
    repo = new_repo(work, "repo")
    claude("/kairyn:init", repo, plugin=True, model=MODEL)
    result = run_verify(repo, fresh=True)
    _save(scenario, run_id, "verify.txt", f"exit={result.returncode}\n{result.stdout}")
    return {"verify_exit": result.returncode, "verify_out": result.stdout}


def init_keeps_edits(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_good_repo(new_repo(work, "repo"))
    (repo / ".kairyn" / "learnings.md").write_text("# Learnings\n\nuser note: keep me\n")
    before = tree_hash(repo / ".kairyn")
    claude("/kairyn:init", repo, plugin=True, model=MODEL)
    return {"unchanged": tree_hash(repo / ".kairyn") == before}


def init_keeps_claude_md(work: Path, scenario: str, run_id: str) -> dict:
    repo = new_repo(work, "repo")
    (repo / "CLAUDE.md").write_text(ORIGINAL_CLAUDE_MD)
    claude("/kairyn:init", repo, plugin=True, model=MODEL)
    text = (repo / "CLAUDE.md").read_text()
    _save(scenario, run_id, "CLAUDE.md", text)
    return {"keeps_original": text.startswith(ORIGINAL_CLAUDE_MD), "blocks": text.count("<!-- kairyn:start -->")}


def check_broken_doc(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_good_repo(new_repo(work, "repo"))
    (repo / BROKEN_DOC).write_text("# Running stages\n\nNo header here.\n")
    reply = claude("/kairyn:check", repo, plugin=True, model=MODEL)
    _save(scenario, run_id, "reply.txt", reply)
    return {"reply": reply}


BACKLOG_IDEA = """---
title: Search is slow
effort: low
impact: high
date: 2026-11-25
---

# Search is slow

**Problem (confirmed by Jo, 2026-11-25):** Search takes 4 s on a large repo.

# Log

- 2026-11-25T05:30:13Z [capture] Created.
"""


def backlog_page(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_good_repo(new_repo(work, "repo"))
    (repo / "docs" / "backlog").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "backlog" / "20261125053013-slow-search.md").write_text(BACKLOG_IDEA)
    reply = claude("/kairyn:backlog", repo, plugin=True, model=MODEL)
    _save(scenario, run_id, "reply.txt", reply)
    page = repo / ".kairyn" / "backlog.html"
    gitignore = repo / ".gitignore"
    return {"reply": reply, "page_exists": page.exists() and "Search is slow" in page.read_text(),
            "ignored": gitignore.exists() and ".kairyn/backlog.html" in gitignore.read_text().splitlines()}


def requirements(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_good_repo(new_repo(work, "repo"))
    run = run_requirements(repo)
    out = {"request": REQUEST, "task_path": None, "requirements_md": "",
           "start": run["start"].strftime(TS), "end": run["end"].strftime(TS)}
    if run["task"] is not None:
        kept = RESULTS / scenario / run_id / run["task"].name
        shutil.copytree(run["task"], kept)   # temp repo is deleted; assertions read this copy
        out["task_path"] = str(kept)
        req = kept / "REQUIREMENTS.md"
        out["requirements_md"] = req.read_text() if req.exists() else ""
    return out


def model_routing(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_routing_repo(make_good_repo(new_repo(work, "repo")))
    run = run_model_routing(repo)
    kept = RESULTS / scenario / run_id / run["task"].name
    shutil.copytree(run["task"], kept)   # temp repo is deleted; assertions read this copy
    doc = kept / "MODEL-ROUTING.md"
    return {"request": ROUTING_REQUEST, "task_path": str(kept), "doc": doc.read_text() if doc.exists() else "",
            "app": (repo / "support" / "reply.py").read_text(), "app_path": "support/reply.py",
            "routing_requirements": (kept / "REQUIREMENTS.md").read_text(),
            "start": run["start"].strftime(TS), "end": run["end"].strftime(TS)}


def grill(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_grill_repo(make_good_repo(new_repo(work, "repo")))
    run = run_grill(repo)
    out = {"request": GRILL_REQUEST, "repo_files": {"report.py": GRILL_APP, "README.md": GRILL_README},
           "turns": run["turns"], "task_path": None, "doc": "", "approver": APPROVER, "words": APPROVAL_WORDS,
           "start": run["start"].strftime(TS), "end": run["end"].strftime(TS)}
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "turns.json").write_text(json.dumps(run["turns"], indent=2))
    if run["task"] is not None:
        kept = run_dir / run["task"].name
        shutil.copytree(run["task"], kept)   # temp repo is deleted; assertions read this copy
        out["task_path"] = str(kept)
        doc = kept / "CONCEPT.md"
        out["doc"] = doc.read_text() if doc.exists() else ""
    return out


def requirements_with_concept(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_concept_repo(make_good_repo(new_repo(work, "repo")))
    tasks = run_requirements_with_concept(repo)["tasks"]
    kept = RESULTS / scenario / run_id / CONCEPT_TASK
    if (repo / "docs" / "tasks" / CONCEPT_TASK).is_dir():
        shutil.copytree(repo / "docs" / "tasks" / CONCEPT_TASK, kept)
    req = kept / "REQUIREMENTS.md"
    return {"tasks": [t.name for t in tasks], "task_path": str(kept), "decisions": list(CONCEPT_DECISIONS),
            "value": CONCEPT_VALUE, "requirements_md": req.read_text() if req.exists() else ""}


def requirements_approval(work: Path, scenario: str, run_id: str) -> dict:
    repo = make_good_repo(new_repo(work, "repo"))
    run = run_requirements_approval(repo)
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "turns.json").write_text(json.dumps(run["turns"], indent=2))
    out = {"request": REQUEST, "turns": run["turns"], "task_path": None, "requirements_md": "",
           "approver": APPROVER, "words": APPROVAL_WORDS,
           "start": run["start"].strftime(TS), "end": run["end"].strftime(TS)}
    if run["task"] is not None:
        kept = run_dir / run["task"].name
        shutil.copytree(run["task"], kept)   # temp repo is deleted; assertions read this copy
        out["task_path"] = str(kept)
        req = kept / "REQUIREMENTS.md"
        out["requirements_md"] = req.read_text() if req.exists() else ""
    return out


def _design_repo(work: Path, run_dir: Path) -> Path:
    """The fixture repo, plus a copy taken before the run: `grounded` checks paths against what existed."""
    repo = make_design_repo(make_good_repo(new_repo(work, "repo")))
    shutil.copytree(repo, run_dir / "repo-before", ignore=shutil.ignore_patterns(".git"))
    return repo


def _design_evidence(run: dict, run_dir: Path) -> dict:
    out = {"request": DESIGN_REQUEST, "requirements": DESIGN_REQUIREMENTS, "repo_before": str(run_dir / "repo-before"),
           "task_path": None, "doc": "", "start": run["start"].strftime(TS), "end": run["end"].strftime(TS)}
    if run["task"].is_dir():
        kept = run_dir / run["task"].name
        shutil.copytree(run["task"], kept)   # temp repo is deleted; assertions read this copy
        out["task_path"] = str(kept)
        doc = kept / "DESIGN.md"
        out["doc"] = doc.read_text() if doc.exists() else ""
    return out


def design(work: Path, scenario: str, run_id: str) -> dict:
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return _design_evidence(run_design(_design_repo(work, run_dir)), run_dir)


def design_child_repo(work: Path, scenario: str, run_id: str) -> dict:
    """A home repo whose task changes code in one child repo (multi-repo R14)."""
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    repo = make_design_child_repo(make_good_repo(new_repo(work, "repo")))
    out = _design_evidence(run_design_child(repo), run_dir)
    return {**out, "requirements": DESIGN_CHILD_REQUIREMENTS}


def design_approval(work: Path, scenario: str, run_id: str) -> dict:
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run = run_design_approval(_design_repo(work, run_dir))
    (run_dir / "turns.json").write_text(json.dumps(run["turns"], indent=2))
    return {**_design_evidence(run, run_dir), "turns": run["turns"], "option": run["option"],
            "approver": APPROVER, "words": APPROVAL_WORDS}


def _close(work: Path, scenario: str, run_id: str, task: str) -> dict:
    repo = make_close_repo(make_good_repo(new_repo(work, "repo")), task)
    out = run_close(repo, task)
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


def close_decision(work: Path, scenario: str, run_id: str) -> dict:
    return _close(work, scenario, run_id, CLOSE_DECISION_TASK)


def close_plain(work: Path, scenario: str, run_id: str) -> dict:
    return _close(work, scenario, run_id, CLOSE_PLAIN_TASK)


def close_hand_merged(work: Path, scenario: str, run_id: str) -> dict:
    """A task merged by hand (in progress, no REVIEW.md): close records the merge from the stub gh, then closes."""
    repo = make_hand_merged_close_repo(make_good_repo(new_repo(work, "repo")))
    out = run_close(repo, CLOSE_HAND_TASK)
    log = work / "gh.log"
    out["gh_calls"] = log.read_text().splitlines() if log.is_file() else []
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


def idea_capture(work: Path, scenario: str, run_id: str) -> dict:
    out = run_idea(make_good_repo(new_repo(work, "repo")))
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


def _times(d: dict) -> dict:
    return {**d, "start": d["start"].strftime(TS), "end": d["end"].strftime(TS)}


def _retro_repo(work: Path, run_dir: Path) -> Path:
    """The fixture, plus a copy taken before the run: move and drop paths are checked against it."""
    repo = make_retro_repo(make_good_repo(new_repo(work, "repo")))
    shutil.copytree(repo, run_dir / "repo-before", ignore=shutil.ignore_patterns(".git"))
    return repo


def retro(work: Path, scenario: str, run_id: str) -> dict:
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    out = {**_times(run_retro(_retro_repo(work, run_dir))), "repo_before": str(run_dir / "repo-before")}
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


def retro_approval(work: Path, scenario: str, run_id: str) -> dict:
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    out = _times(run_retro_approval(_retro_repo(work, run_dir)))
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


def close_retro(work: Path, scenario: str, run_id: str) -> dict:
    """Close a done task while learnings.md is past half its budget: close runs retro, which stops for approval."""
    from runner import changed_paths, retro_dirs
    repo = make_close_repo(make_retro_repo(make_good_repo(new_repo(work, "repo"))), CLOSE_PLAIN_TASK)
    out = run_close(repo, CLOSE_PLAIN_TASK)
    dirs = retro_dirs(repo)
    out.update({"retro_dirs": [d.name for d in dirs], "entries": RETRO_ENTRIES,
                "retro": (dirs[0] / "RETRO.md").read_text() if dirs and (dirs[0] / "RETRO.md").is_file() else "",
                "changed": changed_paths(repo)})
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


HAND_MADE = "hand-made template\n"


def upgrade_conflict(work: Path, scenario: str, run_id: str) -> dict:
    """A v0.1.0 repo (no manifest) with one hand-made template: one CONFLICT, the rest upgrades."""
    repo = new_repo(work, "repo")
    shutil.copytree(ROOT / "tests" / "fixtures" / "consumer-v0.1.0", repo, dirs_exist_ok=True)
    (repo / ".kairyn" / "templates" / "STATE.md").write_text(HAND_MADE)
    reply = claude("/kairyn:upgrade", repo, plugin=True, model=MODEL)
    _save(scenario, run_id, "reply.txt", reply)
    stage = repo / ".kairyn" / "stages" / "REQUIREMENTS.md"
    return {"reply": reply,
            "manifest": (repo / ".kairyn" / "manifest.json").is_file(),
            "stage_upgraded": stage.read_bytes() == (PLUGIN / "stages" / "REQUIREMENTS.md").read_bytes(),
            "template_kept": (repo / ".kairyn" / "templates" / "STATE.md").read_text() == HAND_MADE,
            "kairyn_new": (repo / ".kairyn" / "templates" / "STATE.md.kairyn-new").is_file()}


# --- AFK stages: afk.py runs them; the asserts read its files and the session transcripts --------------
from afk_fixtures import make_afk_repo, make_built_branch, run_afk

PASSING_CHECK = "observability: textstats.py reads a --lines option and prints the number of lines from stdin.\n"
FAILING_CHECK = "observability: Each function in textstats.py has a docstring.\n"


def _afk(work: Path, scenario: str, run_id: str, **fixture) -> dict:
    run_dir = RESULTS / scenario / run_id
    stage = fixture.pop("stage", None)
    repo = make_afk_repo(work, **fixture)
    if stage:
        make_built_branch(repo, stage)
    out = run_afk(repo, run_dir)
    for name in ("STATE", "BUILD", "GATES", "REVIEW"):
        if out[name.lower()]:
            _save(scenario, run_id, f"{name}.md", out[name.lower()])
    _save(scenario, run_id, "afk.txt", out["stdout"])
    out["doc"] = out["review"]
    return out


def afk_build(work: Path, scenario: str, run_id: str) -> dict:
    return _afk(work, scenario, run_id)


def afk_gates_pass(work: Path, scenario: str, run_id: str) -> dict:
    return _afk(work, scenario, run_id, stage="gates", extra_gates="  observability: true\n",
                checks="checks:\n  " + PASSING_CHECK)


def afk_gates_fail(work: Path, scenario: str, run_id: str) -> dict:
    return _afk(work, scenario, run_id, stage="gates", extra_gates="  observability: true\n",
                checks="checks:\n  " + FAILING_CHECK)


def afk_review(work: Path, scenario: str, run_id: str) -> dict:
    return _afk(work, scenario, run_id, stage="review", review_usd=1, chars=True)


# --- milestones: a first mate session starts after missed milestone lines ------------------------------
MISSED = ["tests exit 0", "push exit 0"]


def milestones_catchup(work: Path, scenario: str, run_id: str) -> dict:
    """The SessionStart hook prints 2 missed lines and the watcher instruction; the session should start Monitor."""
    import subprocess
    import runner
    repo = new_repo(work, "repo")
    log = work / "home" / ".session" / "milestones.log"
    log.parent.mkdir(parents=True)
    old = ["2026-01-05T09:00:00Z [build api] build started", "2026-01-05T09:05:00Z [build api] lint exit 0"]
    log.write_text("\n".join(old + [f"2026-01-05T09:1{i}:00Z [build api] {t}" for i, t in enumerate(MISSED)]) + "\n")
    (repo / ".kairyn").mkdir()
    (repo / ".kairyn" / "milestones.yml").write_text(f"watch:\n  log: {log}\n")
    (repo / ".session").mkdir()
    (repo / ".session" / "watch.json").write_text('{"line": 2}\n')
    cmd = ["claude", "-p", "I am back. What happened while I was away?", "--permission-mode", "acceptEdits",
           "--output-format", "stream-json", "--verbose", "--plugin-dir", str(PLUGIN)] + (["--model", MODEL] if MODEL else [])
    try:
        out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=300).stdout
    except subprocess.TimeoutExpired as e:   # a watcher can keep the session open; the events so far are enough
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    _save(scenario, run_id, "transcript.jsonl", out)
    tools, reply, cost = [], "", None
    for line in out.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tools.append({"name": block.get("name"), "input": block.get("input")})
                elif block.get("type") == "text":
                    reply += block.get("text", "") + "\n"
        elif event.get("type") == "result":
            cost = event.get("total_cost_usd")
    runner.record_cost(runner._COST_DIR, "run", cost if isinstance(cost, (int, float)) else None)
    out = {"tools": tools, "reply": reply, "missed": MISSED}
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


SCENARIOS = {f.__name__: f for f in (afk_build, afk_gates_pass, afk_gates_fail, afk_review, init_fresh, init_keeps_edits, init_keeps_claude_md, check_broken_doc, backlog_page, requirements,
                                     model_routing, grill, requirements_with_concept, requirements_approval,
                                     upgrade_conflict, close_decision, close_plain, close_hand_merged, design, design_approval, design_child_repo,
                                     retro, retro_approval, close_retro, milestones_catchup,
                                     idea_capture)}


def call_api(prompt, options, context):
    scenario = context["vars"]["scenario"]
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    work = Path(tempfile.mkdtemp(prefix=f"kairyn-{scenario}-"))
    set_cost_dir(RESULTS / scenario / run_id)   # every claude call of this run appends its cost there
    try:
        return {"output": json.dumps(SCENARIOS[scenario](work, scenario, run_id))}
    except Exception as e:   # surfaced by promptfoo as a failed run, with the reason
        return {"error": f"{scenario}: {type(e).__name__}: {e}"}
    finally:
        set_cost_dir(None)
        shutil.rmtree(work, ignore_errors=True)

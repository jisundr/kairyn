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

from helpers import PLUGIN, ROOT, make_good_repo, run_verify  # noqa: E402
from runner import (APPROVAL_WORDS, APPROVER, CONCEPT_DECISIONS, CONCEPT_TASK, CONCEPT_VALUE, GRILL_APP, GRILL_README, GRILL_REQUEST, MODEL, REQUEST, RESULTS, ROUTING_REQUEST,  # noqa: E402
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
           "turns": run["turns"], "task_path": None, "doc": "",
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


SCENARIOS = {f.__name__: f for f in (init_fresh, init_keeps_edits, init_keeps_claude_md, check_broken_doc, requirements,
                                     model_routing, grill, requirements_with_concept, requirements_approval,
                                     upgrade_conflict)}


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

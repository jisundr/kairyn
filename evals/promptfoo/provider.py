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
from runner import (RETRO_ENTRIES, make_retro_repo, run_retro, run_retro_approval, DESIGN_REQUEST, DESIGN_REQUIREMENTS, make_design_repo, run_design, run_design_approval, EXIT_DECISION_TASK, EXIT_PLAIN_TASK, make_exit_repo, run_exit, APPROVAL_WORDS, APPROVER, CONCEPT_DECISIONS, CONCEPT_TASK, CONCEPT_VALUE, GRILL_APP, GRILL_README, GRILL_REQUEST, MODEL, REQUEST, RESULTS, ROUTING_REQUEST,  # noqa: E402
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


def design_approval(work: Path, scenario: str, run_id: str) -> dict:
    run_dir = RESULTS / scenario / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run = run_design_approval(_design_repo(work, run_dir))
    (run_dir / "turns.json").write_text(json.dumps(run["turns"], indent=2))
    return {**_design_evidence(run, run_dir), "turns": run["turns"], "option": run["option"],
            "approver": APPROVER, "words": APPROVAL_WORDS}


def _exit(work: Path, scenario: str, run_id: str, task: str) -> dict:
    repo = make_exit_repo(make_good_repo(new_repo(work, "repo")), task)
    out = run_exit(repo, task)
    _save(scenario, run_id, "evidence.json", json.dumps(out, indent=2))
    return out


def exit_decision(work: Path, scenario: str, run_id: str) -> dict:
    return _exit(work, scenario, run_id, EXIT_DECISION_TASK)


def exit_plain(work: Path, scenario: str, run_id: str) -> dict:
    return _exit(work, scenario, run_id, EXIT_PLAIN_TASK)


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


def exit_retro(work: Path, scenario: str, run_id: str) -> dict:
    """Exit a done task while learnings.md is past half its budget: exit runs retro, which stops for approval."""
    from runner import changed_paths, retro_dirs
    repo = make_exit_repo(make_retro_repo(make_good_repo(new_repo(work, "repo"))), EXIT_PLAIN_TASK)
    out = run_exit(repo, EXIT_PLAIN_TASK)
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


SCENARIOS = {f.__name__: f for f in (init_fresh, init_keeps_edits, init_keeps_claude_md, check_broken_doc, requirements,
                                     model_routing, grill, requirements_with_concept, requirements_approval,
                                     upgrade_conflict, exit_decision, exit_plain, design, design_approval,
                                     retro, retro_approval, exit_retro)}


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

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

from helpers import make_good_repo, run_verify  # noqa: E402
from runner import MODEL, REQUEST, RESULTS, claude, new_repo, run_requirements, tree_hash  # noqa: E402

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
    result = run_verify(repo)
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


SCENARIOS = {f.__name__: f for f in (init_fresh, init_keeps_edits, init_keeps_claude_md, check_broken_doc, requirements)}


def call_api(prompt, options, context):
    scenario = context["vars"]["scenario"]
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    work = Path(tempfile.mkdtemp(prefix=f"kairyn-{scenario}-"))
    try:
        return {"output": json.dumps(SCENARIOS[scenario](work, scenario, run_id))}
    except Exception as e:   # surfaced by promptfoo as a failed run, with the reason
        return {"error": f"{scenario}: {type(e).__name__}: {e}"}
    finally:
        shutil.rmtree(work, ignore_errors=True)

"""promptfoo assertions: pure checks on the JSON evidence the provider returns."""
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "tests")]

from checks import TS_FORMAT, structural_problems  # noqa: E402
from runner import JUDGE_MODEL, claude  # noqa: E402


def _result(problems: list[str]) -> dict:
    return {"pass": not problems, "score": 0 if problems else 1, "reason": "; ".join(problems) or "ok"}


def verified_layout(output, context):
    d = json.loads(output)
    return _result([] if d["verify_exit"] == 0 else [d["verify_out"].strip() or "verify-init failed"])


def kairyn_tree_unchanged(output, context):
    return _result([] if json.loads(output)["unchanged"] else [".kairyn/ changed (user edits overwritten)"])


def claude_md_intact(output, context):
    d = json.loads(output)
    problems = []
    if not d["keeps_original"]:
        problems.append("original CLAUDE.md text damaged")
    if d["blocks"] != 1:
        problems.append(f"{d['blocks']} kairyn blocks, expected exactly 1")
    return _result(problems)


def names_broken_doc(output, context):
    return _result([] if "running-stages" in json.loads(output)["reply"] else ["reply did not name running-stages.md"])


def well_formed(output, context):
    d = json.loads(output)
    parse = lambda s: datetime.strptime(s, TS_FORMAT).replace(tzinfo=timezone.utc)
    run = {"task": Path(d["task_path"]) if d["task_path"] else None, "start": parse(d["start"]), "end": parse(d["end"])}
    return _result(structural_problems(run))


RUBRIC = """You are grading a REQUIREMENTS.md written for this request:
"{request}"

Score 1-5 on each criterion, then reply with ONLY a JSON object:
{{"verifiable": n, "scope": n, "no_invention": n}}
- verifiable: every acceptance criterion could be checked pass/fail by a reviewer
- scope: in-scope and out-of-scope are both explicit and sensible
- no_invention: nothing beyond the request is added without being flagged as an assumption

REQUIREMENTS.md:
{doc}
"""
FLOOR = 3   # a run fails if any criterion scores below this; the mean gate is applied by evals/run.py


def quality(output, context):
    """LLM judge. Saves the raw reply and scores next to the task so run.py can apply the mean gate."""
    d = json.loads(output)
    if not d["requirements_md"]:
        return _result(["no REQUIREMENTS.md to grade"])
    with tempfile.TemporaryDirectory(prefix="kairyn-judge-") as cwd:
        raw = claude(RUBRIC.format(request=d["request"], doc=d["requirements_md"]), Path(cwd), model=JUDGE_MODEL)
    run_dir = Path(d["task_path"]).parent
    (run_dir / "judge.txt").write_text(raw)
    match = re.search(r"\{.*?\}", raw, re.S)
    try:
        scores = json.loads(match.group()) if match else None
        scores = {k: float(scores[k]) for k in ("verifiable", "scope", "no_invention")}
    except (ValueError, KeyError, TypeError):
        return _result(["judge reply was not a score object"])
    (run_dir / "judge.json").write_text(json.dumps(scores))
    low = [f"{k} scored {v:g}" for k, v in scores.items() if v < FLOOR]
    return {"pass": not low, "score": sum(scores.values()) / (5 * len(scores)),
            "reason": ", ".join(f"{k} {v:g}" for k, v in scores.items()) + ("; " + ", ".join(low) if low else "")}

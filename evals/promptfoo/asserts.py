"""promptfoo assertions: pure checks on the JSON evidence the provider returns."""
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "tests")]

from checks import (TS_FORMAT, next_routing_stage, open_decisions, routing_problems, ste_problems,  # noqa: E402
                    ste_rate, structural_problems, traceability_problems)
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


def _run(d: dict) -> dict:
    parse = lambda s: datetime.strptime(s, TS_FORMAT).replace(tzinfo=timezone.utc)
    return {"task": Path(d["task_path"]) if d["task_path"] else None, "start": parse(d["start"]), "end": parse(d["end"])}


def _doc(d: dict) -> str:
    """The stage output under test: REQUIREMENTS.md or MODEL-ROUTING.md."""
    return d.get("requirements_md") or d.get("doc") or ""


def well_formed(output, context):
    return _result(structural_problems(_run(json.loads(output))))


def routing_well_formed(output, context):
    return _result(routing_problems(_run(json.loads(output))))


def starts_with_baseline(output, context):
    """No request logs exist in the fixture, so the playbook's first stage (0: logging and a baseline) comes next."""
    n = next_routing_stage(json.loads(output)["doc"])
    return _result([] if n == 0 else [f"next stage is {n}, expected 0"])


def waits_for_human(output, context):
    """Nobody gave a quality bar or goals, so they stay open decisions and the task is blocked on the user."""
    d = json.loads(output)
    problems = [] if open_decisions(d["doc"]) else ["no open D<n> decision"]
    state = (Path(d["task_path"]) / "STATE.md").read_text()
    if not re.search(r"^status:\s*blocked\b", state, re.M):
        problems.append("STATE.md status is not blocked")
    return _result(problems)


STE_MAX_RATE = 1.0   # ASD-STE100 violations per 100 words; baseline before the rule was 1.47 (0.92 to 1.98)


def plain_language(output, context):
    """The stage output follows ASD-STE100 about 80% of the way (see checks.ste_problems)."""
    doc = _doc(json.loads(output))
    if not doc:
        return _result(["no stage output to lint"])
    rate, problems = ste_rate(doc), ste_problems(doc)
    ok = rate <= STE_MAX_RATE
    return {"pass": ok, "score": 1 if ok else 0,
            "reason": f"{rate} violations/100 words (max {STE_MAX_RATE}); " + ", ".join(problems[:5])}


def traceable(output, context):
    """No invention, checked: every acceptance criterion cites the request or a labeled assumption."""
    doc = json.loads(output)["requirements_md"]
    return _result(traceability_problems(doc) if doc else ["no REQUIREMENTS.md to trace"])


RUBRIC = """You are grading a REQUIREMENTS.md written for this request:
"{request}"

Score 1-5 on each criterion, then reply with a JSON object first:
{{"verifiable": n, "scope": n, "no_invention": n}}
After the JSON, list each item you counted as invented, one per line.
- verifiable: every acceptance criterion could be checked pass/fail by a reviewer
- scope: in-scope and out-of-scope are both explicit and sensible
- no_invention: nothing beyond the request is added without being flagged as an assumption

REQUIREMENTS.md:
{doc}
"""
FLOOR = 3   # a run fails if any criterion scores below this; the mean gate is applied by evals/run.py


def _judge(prompt: str, run_dir: Path, criteria: tuple[str, ...]) -> dict:
    """LLM judge. Saves the raw reply and scores in run_dir so run.py can apply the mean gate."""
    with tempfile.TemporaryDirectory(prefix="kairyn-judge-") as cwd:
        raw = claude(prompt, Path(cwd), model=JUDGE_MODEL)
    (run_dir / "judge.txt").write_text(raw)
    match = re.search(r"\{.*?\}", raw, re.S)
    try:
        scores = json.loads(match.group()) if match else None
        scores = {k: float(scores[k]) for k in criteria}
    except (ValueError, KeyError, TypeError):
        return _result(["judge reply was not a score object"])
    (run_dir / "judge.json").write_text(json.dumps(scores))
    low = [f"{k} scored {v:g}" for k, v in scores.items() if v < FLOOR]
    return {"pass": not low, "score": sum(scores.values()) / (5 * len(scores)),
            "reason": ", ".join(f"{k} {v:g}" for k, v in scores.items()) + ("; " + ", ".join(low) if low else "")}


def quality(output, context):
    d = json.loads(output)
    if not d["requirements_md"]:
        return _result(["no REQUIREMENTS.md to grade"])
    prompt = RUBRIC.format(request=d["request"], doc=d["requirements_md"])
    return _judge(prompt, Path(d["task_path"]).parent, ("verifiable", "scope", "no_invention"))

ROUTING_RUBRIC = """You are grading MODEL-ROUTING.md, a plan for adding model routing to a repo.
The repo's only LLM code is `{app_path}`:
```python
{app}
```
The task's REQUIREMENTS.md, which the plan was told to read:
{requirements}

Request: "{request}". Nobody gave a quality bar, cost goal, latency goal or threshold.

Score 1-5 on each criterion, then reply with a JSON object first:
{{"grounded": n, "staged": n, "no_invention": n}}
After the JSON, list each invented number or decision, one per line.
- grounded: call sites, models and references to REQUIREMENTS.md match the inputs above; nothing is described that they do not have
- staged: it plans one next stage, the first missing one (logging and a baseline before failover, caching or routers), with a flag, shadow mode and gates
- no_invention: quality bar, goals and thresholds are open decisions for a human, not numbers the plan made up

MODEL-ROUTING.md:
{doc}
"""


def routing_quality(output, context):
    d = json.loads(output)
    if not d["doc"]:
        return _result(["no MODEL-ROUTING.md to grade"])
    prompt = ROUTING_RUBRIC.format(app_path=d["app_path"], app=d["app"], requirements=d["routing_requirements"],
                                   request=d["request"], doc=d["doc"])
    return _judge(prompt, Path(d["task_path"]).parent, ("grounded", "staged", "no_invention"))


def upgrade_ran(output, context):
    """/kairyn:upgrade ran the script: stage upgraded, the conflicting file left as it was, the merge set aside."""
    d = json.loads(output)
    problems = [msg for ok, msg in ((d["manifest"], "no manifest written"),
                                    (d["stage_upgraded"], "REQUIREMENTS.md not upgraded"),
                                    (d["template_kept"], "hand-made STATE.md template changed"),
                                    (d["kairyn_new"], "no STATE.md.kairyn-new")) if not ok]
    return _result(problems)


def reports_conflict(output, context):
    """The reply names the conflict and tells the user where the merge is."""
    reply = json.loads(output)["reply"]
    problems = [f"reply does not mention {w}" for w in ("CONFLICT", "STATE.md", ".kairyn-new") if w not in reply]
    return _result(problems)

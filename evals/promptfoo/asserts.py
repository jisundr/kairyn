"""promptfoo assertions: pure checks on the JSON evidence the provider returns."""
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "tests")]

from checks import (exit_problems, TS_FORMAT, approval_problems, concept_use_problems, ears_problems, nfr_problems, owner_problems, decision_labels, grill_problems, grill_reply_problems, next_routing_stage,  # noqa: E402
                    open_decisions, routing_problems, state_fields, ste_problems, ste_rate, structural_problems,
                    traceability_problems)
from runner import JUDGE_MODEL, NO_QUESTIONS, claude  # noqa: E402


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
    """The stage output under test: REQUIREMENTS.md, MODEL-ROUTING.md or CONCEPT.md."""
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


def specified(output, context):
    """Playbook gaps closed: EARS requirements each with a criterion, four non-functional needs, owners."""
    doc = json.loads(output)["requirements_md"]
    return _result(ears_problems(doc) + nfr_problems(doc) + owner_problems(doc) if doc else ["no REQUIREMENTS.md"])


def waits_for_approval(output, context):
    """Nobody approved, so the document says 'Approval: pending' and no approval line."""
    doc = json.loads(output)["requirements_md"]
    return _result(approval_problems(doc, approved=False) if doc else ["no REQUIREMENTS.md"])


RUBRIC = """You are grading a REQUIREMENTS.md written for this request:
"{request}"
The run was also told: \"""" + NO_QUESTIONS + """\" Recording that instruction, and the assumptions it asks for, is not invention.

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
        raw = claude(prompt, Path(cwd), model=JUDGE_MODEL, role="judge", cost_dir=run_dir)
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


# --- grill stage -------------------------------------------------------------------
# Turns: 0 = /kairyn:grill <request>, 1 and 2 = "I accept your recommendation.", 3 = "Stop the interview now."
QUESTION_TURNS = (0, 1, 2)


def grill_well_formed(output, context):
    return _result(grill_problems(_run(json.loads(output)), stopped=True))


def one_question(output, context):
    """Every message before the stop asks one question and recommends an answer."""
    turns = json.loads(output)["turns"]
    problems = [f"turn {i}: {p}" for i in QUESTION_TURNS if i < len(turns)
                for p in grill_reply_problems(turns[i]["reply"])]
    return _result(problems if len(turns) == 4 else problems + [f"{len(turns)} turns, expected 4"])


def records_answers(output, context):
    """After each accepted answer, CONCEPT.md holds one more decision."""
    turns = json.loads(output)["turns"]
    if len(turns) < 3:
        return _result([f"only {len(turns)} turns"])
    counts = [len(decision_labels(t["concept"])) for t in turns[:3]]
    problems = [f"after answer {n}: {counts[n]} decisions, expected at least {n}" for n in (1, 2) if counts[n] < n]
    if counts[2] <= counts[1]:
        problems.append(f"answer 2 added no decision ({counts[1]} -> {counts[2]})")
    return _result(problems)


def waits_for_answer(output, context):
    """Until the user stops or confirms, the stage stays in progress and the task waits on the user."""
    turns = json.loads(output)["turns"]
    problems = []
    for i in QUESTION_TURNS[:len(turns)]:
        f = state_fields(turns[i]["state"])
        if not f:
            problems.append(f"turn {i}: no readable STATE.md")
        elif (f["stages"].get("grill"), f["status"]) != ("in-progress", "blocked"):
            problems.append(f"turn {i}: grill {f['stages'].get('grill')!r} status {f['status']!r}, expected in-progress blocked")
    return _result(problems)


def hands_off(output, context):
    """The last message names the task folder, so the user can run requirements on it."""
    d = json.loads(output)
    if not d["task_path"] or not d["turns"]:
        return _result(["no task folder or no turns"])
    folder = Path(d["task_path"]).name
    return _result([] if folder in d["turns"][-1]["reply"] else [f"last message does not name {folder}"])


GRILL_RUBRIC = """You are grading an interview an agent ran with a user before any spec existed.
The user's request: "{request}"
The repo the agent could read:
{repo}
The user's replies were scripted: "I accept your recommendation." twice, then "Stop the interview now."

The agent's messages, in order:
{replies}

The CONCEPT.md it left:
{doc}

Score 1-5 on each criterion, then reply with a JSON object first:
{{"grounded": n, "challenges": n, "recommends": n}}
After the JSON, list each question the repo already answers, and each vague term left unchallenged, one per line.
- grounded: no question asks what the repo already answers (language, data source, file size, export schedule)
- challenges: it asks for the problem behind "a cache" before any cache design, and pins down vague words such as "faster"
- recommends: each question comes with one recommended answer and a reason grounded in the repo or earlier answers
"""


def grill_quality(output, context):
    d = json.loads(output)
    if not d["turns"] or not d["task_path"]:
        return _result(["no interview to grade"])
    repo = "\n".join(f"{name}:\n```\n{text}```" for name, text in d["repo_files"].items())
    replies = "\n\n".join(f"Message {i + 1}:\n{t['reply']}" for i, t in enumerate(d["turns"]))
    prompt = GRILL_RUBRIC.format(request=d["request"], repo=repo, replies=replies, doc=d["doc"])
    return _judge(prompt, Path(d["task_path"]).parent, ("grounded", "challenges", "recommends"))


def uses_concept(output, context):
    """requirements reuses the grill task folder and builds on CONCEPT.md instead of guessing again."""
    d = json.loads(output)
    problems = [] if d["tasks"] == [Path(d["task_path"]).name] else [f"task folders {d['tasks']}, expected only the grill task"]
    return _result(problems + concept_use_problems(Path(d["task_path"]), tuple(d["decisions"]), d["value"]))


# --- approval: turns 0 = the stage, 1 = "Thanks. I will read it later.", 2 = "Approved." ----------
def approval_gate(output, context):
    """Before the user approves, the task waits: blocked, 'Approval: pending', no approval line."""
    turns = json.loads(output)["turns"]
    if len(turns) != 3:
        return _result([f"{len(turns)} turns, expected 3"])
    problems = []
    for i in (0, 1):
        f = state_fields(turns[i]["state"])
        if f.get("status") != "blocked":
            problems.append(f"turn {i}: status {f.get('status')!r}, expected blocked")
        problems += [f"turn {i}: {p}" for p in approval_problems(turns[i]["requirements"], approved=False)]
    return _result(problems)


def records_approval(output, context):
    """After 'Approved.', the approval line names the approver, the time and the words, and the task is done."""
    d = json.loads(output)
    if not d["task_path"]:
        return _result(["no task folder"])
    run = _run(d)
    problems = structural_problems(run, approved=True)
    problems += approval_problems(d["requirements_md"], approved=True, name=d["approver"], words=d["words"],
                                  start=run["start"], end=run["end"])
    return _result(problems)


def exits_with_adr(output, context):
    """A load-bearing decision (D1, SQLite over JSON) gets an ADR; the task, its backlog file and only those go."""
    from runner import EXIT_KEYWORD
    return _result(exit_problems(json.loads(output), expect_adr=True, keyword=EXIT_KEYWORD))


def exits_without_adr(output, context):
    """A typo fix has no load-bearing decision: changelog and deletion, no ADR."""
    return _result(exit_problems(json.loads(output), expect_adr=False))

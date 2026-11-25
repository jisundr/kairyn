"""promptfoo assertions: pure checks on the JSON evidence the provider returns."""
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent.parent / "tests")]

from checks import (build_row_problems, flags_problems, gate_row, new_constraint_lines, output_header_problems, red_before_code_problems, review_gap_problems,
                    retro_applied_problems, retro_proposal_problems, retro_scope_problems, chosen_option, design_run_problems, design_test_plan_problems, grounded_problems, options_problems,
                    close_problems, TS_FORMAT, approval_problems, concept_use_problems, ears_problems, nfr_problems, owner_problems, decision_labels, grill_problems, grill_reply_problems, handoff_problems, next_routing_stage,
                    open_decisions, routing_problems, state_fields, ste_problems, ste_rate, structural_problems,
                    traceability_problems, repo_line_problems)
from runner import JUDGE_MODEL, NO_QUESTIONS, claude


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
    """The stage output under test: REQUIREMENTS.md, MODEL-ROUTING.md, CONCEPT.md or DESIGN.md."""
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
# Turns: 0 = /kairyn:grill <request>, 1 and 2 = "I accept your recommendation.", 3 = "Stop the interview now.",
# 4 = "Approved."
QUESTION_TURNS = (0, 1, 2)
STOP_TURN, GRILL_TURNS = 3, 5


def grill_well_formed(output, context):
    return _result(grill_problems(_run(json.loads(output)), stopped=True))


def one_question(output, context):
    """Every message before the stop asks one question and recommends an answer."""
    turns = json.loads(output)["turns"]
    problems = [f"turn {i}: {p}" for i in QUESTION_TURNS if i < len(turns)
                for p in grill_reply_problems(turns[i]["reply"])]
    return _result(problems if len(turns) == GRILL_TURNS else problems + [f"{len(turns)} turns, expected {GRILL_TURNS}"])


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


def grill_approval_gate(output, context):
    """A stop is not approval: the concept waits with 'Approval: pending', grill done, the task blocked on the user."""
    turns = json.loads(output)["turns"]
    if len(turns) <= STOP_TURN:
        return _result([f"only {len(turns)} turns"])
    f = state_fields(turns[STOP_TURN]["state"])
    problems = [f"turn {STOP_TURN}: {p}" for p in approval_problems(turns[STOP_TURN]["concept"], approved=False)]
    if (f.get("stages", {}).get("grill"), f.get("status")) != ("done", "blocked"):
        problems.append(f"turn {STOP_TURN}: grill {f.get('stages', {}).get('grill')!r} status {f.get('status')!r}, "
                        "expected done blocked")
    return _result(problems)


def grill_records_approval(output, context):
    """After 'Approved.', CONCEPT.md names the approver, the time and the words."""
    d = json.loads(output)
    if not d["task_path"]:
        return _result(["no task folder"])
    run = _run(d)
    return _result(approval_problems(d["doc"], approved=True, name=d["approver"], words=d["words"],
                                     start=run["start"], end=run["end"]))


def hands_off(output, context):
    """The last message tells the user to type /kairyn:requirements <task folder>, and grill does not run it."""
    d = json.loads(output)
    if not d["task_path"] or not d["turns"]:
        return _result(["no task folder or no turns"])
    return _result(handoff_problems(d["turns"][-1]["reply"], Path(d["task_path"]), "requirements"))


def hands_off_design(output, context):
    """After approval, requirements tells the user to type /kairyn:design <task folder>, and does not run it."""
    d = json.loads(output)
    if not d["task_path"] or not d["turns"]:
        return _result(["no task folder or no turns"])
    return _result(handoff_problems(d["turns"][-1]["reply"], Path(d["task_path"]), "design"))


def hands_off_build(output, context):
    """After approval, design tells the user to type /kairyn:build <task folder>, and does not run it."""
    d, turns = _design_turns(output)
    if not d.get("task_path") or not turns:
        return _result(["no task folder or no turns"])
    return _result(handoff_problems(turns[-1]["reply"], Path(d["task_path"]), "build"))


GRILL_RUBRIC = """You are grading an interview an agent ran with a user before any spec existed.
The user's request: "{request}"
The repo the agent could read:
{repo}
The user's replies were scripted: "I accept your recommendation." twice, "Stop the interview now.", then "Approved."

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
    """After 'Approved.', the approval line names the approver, the time and the words, and the task moves to design."""
    d = json.loads(output)
    if not d["task_path"]:
        return _result(["no task folder"])
    run = _run(d)
    problems = structural_problems(run, approved=True)
    problems += approval_problems(d["requirements_md"], approved=True, name=d["approver"], words=d["words"],
                                  start=run["start"], end=run["end"])
    return _result(problems)


def closes_with_adr(output, context):
    """A load-bearing decision (D1, SQLite over JSON) gets an ADR; the task, its backlog file and only those go."""
    from runner import CLOSE_KEYWORD
    return _result(close_problems(json.loads(output), expect_adr=True, keyword=CLOSE_KEYWORD))


def closes_without_adr(output, context):
    """A typo fix has no load-bearing decision: changelog and deletion, no ADR."""
    return _result(close_problems(json.loads(output), expect_adr=False))


# --- design stage: scenario 1 = one run on an approved task; 2 = stage, non-approval, "go with option X", approval -----
def _design_run(d: dict) -> dict:
    return {**_run(d), "task": Path(d["task_path"]) if d["task_path"] else None}


def design_well_formed(output, context):
    d = json.loads(output)
    return _result(design_run_problems(_design_run(d)) if d["task_path"] else ["no task folder"])


def design_names_repo(output, context):
    """STATE.md has `repo: report-cli` for the child-repo scenario, and no repo: line for the others (R1, R14)."""
    d = json.loads(output)
    if not d["task_path"]:
        return _result(["no task folder"])
    expected = (context.get("vars") or {}).get("child_repo")
    return _result(repo_line_problems((Path(d["task_path"]) / "STATE.md").read_text(), expected))


def design_traceable(output, context):
    """Each acceptance criterion in REQUIREMENTS.md has a test-plan row with a task and a test."""
    d = json.loads(output)
    return _result(design_test_plan_problems(d["doc"], d["requirements"]) if d["doc"] else ["no DESIGN.md"])


def design_no_needless_manual(output, context):
    """Each criterion of the design fixture is a CLI output a test can check: no test plan row is `Manual`."""
    d = json.loads(output)
    if not d["doc"]:
        return _result(["no DESIGN.md"])
    rows = re.findall(r"^\|\s*AC\d+\b[^|]*\|[^|]*\|\s*Manual\b.*$", d["doc"], re.M | re.I)
    return _result([f"a test a script can run is marked Manual: {r[:160]}" for r in rows])


def design_options(output, context):
    d = json.loads(output)
    return _result(options_problems(d["doc"]) if d["doc"] else ["no DESIGN.md"])


def design_grounded(output, context):
    """Each path DESIGN.md names existed before the run, or carries (new)."""
    d = json.loads(output)
    return _result(grounded_problems(d["doc"], Path(d["repo_before"])) if d["doc"] else ["no DESIGN.md"])


def design_waits(output, context):
    d = json.loads(output)
    if not d["task_path"]:
        return _result(["no task folder"])
    problems = approval_problems(d["doc"], approved=False)
    if state_fields((Path(d["task_path"]) / "STATE.md").read_text()).get("status") != "blocked":
        problems.append("STATE.md status is not blocked")
    return _result(problems)


DESIGN_RUBRIC = """You are grading DESIGN.md, a design for one task in a small repo.
Besides kairyn setup files, the repo has these three files, and the design could read them all.
`report.py`:
```python
{app}
```
`README.md`:
{readme}
`data/orders.csv`:
```
{orders}
```
`.kairyn/afk.yml`, the AFK run settings the design could read:
```yaml
{afk}
```
The approved REQUIREMENTS.md the design was told to read:
{requirements}
The designer was told: "{no_questions}" Recorded assumptions are allowed; facts stated as true must come from the inputs.

Score 1-5 on each criterion, then reply with a JSON object first:
{{"no_invention": n, "sound": n}}
After the JSON, list each invented fact, file or decision, one per line.
- no_invention: everything it states about the repo and the requirements is in the inputs above; new files are marked (new)
- sound: the chosen approach meets every requirement; tasks are small, ordered, and each has a done condition a reviewer can check

DESIGN.md:
{doc}
"""


def design_quality(output, context):
    d = json.loads(output)
    if not d["doc"]:
        return _result(["no DESIGN.md to grade"])
    from runner import DESIGN_ORDERS, GRILL_APP, GRILL_README
    afk = Path(d["repo_before"]) / ".kairyn" / "afk.yml"
    prompt = DESIGN_RUBRIC.format(app=GRILL_APP, readme=GRILL_README, orders=DESIGN_ORDERS, no_questions=NO_QUESTIONS,
                                  afk=afk.read_text() if afk.is_file() else "(none)", requirements=d["requirements"],
                                  doc=d["doc"])
    return _judge(prompt, Path(d["task_path"]).parent, ("no_invention", "sound"))


def _design_turns(output) -> tuple[dict, list[dict]]:
    d = json.loads(output)
    return d, d.get("turns") or []


def design_approval_gate(output, context):
    """Until 'Approved.', the task waits: blocked, 'Approval: pending'. The non-approval turn changes nothing."""
    d, turns = _design_turns(output)
    if len(turns) != 4:
        return _result([f"{len(turns)} turns, expected 4"])
    problems = []
    for i in (0, 1, 2):
        if state_fields(turns[i]["state"]).get("status") != "blocked":
            problems.append(f"turn {i}: status not blocked")
        problems += [f"turn {i}: {p}" for p in approval_problems(turns[i]["design"], approved=False)]
    if turns[1]["design"] != turns[0]["design"]:
        problems.append("turn 1: DESIGN.md changed on a reply that does not approve")
    return _result(problems)


def rewrites_option(output, context):
    """'Go with option X' (an option turn 0 rejected) rewrites DESIGN.md around X."""
    d, turns = _design_turns(output)
    if len(turns) < 3:
        return _result([f"{len(turns)} turns, expected at least 3"])
    if not d["option"]:
        return _result(["turn 0 DESIGN.md has no rejected option to pick"])
    problems = [] if chosen_option(turns[2]["design"]) == d["option"] else [
        f"turn 2: Approach chose {chosen_option(turns[2]['design'])!r}, expected {d['option']!r}"]
    if turns[2]["design"] == turns[1]["design"]:
        problems.append("turn 2: DESIGN.md not rewritten")
    return _result(problems)


def design_records_approval(output, context):
    """After 'Approved.', the approval line names the approver, the time and the words, and the task is done."""
    d = json.loads(output)
    if not d["task_path"]:
        return _result(["no task folder"])
    run = _design_run(d)
    problems = design_run_problems(run, approved=True)
    problems += approval_problems(d["doc"], approved=True, name=d["approver"], words=d["words"],
                                  start=run["start"], end=run["end"])
    return _result(problems)


# --- retro stage: 1 = proposal only; 2 = proposal, then "Approved."; 3 = close with a full learnings.md -----
def _times(d: dict) -> dict:
    parse = lambda s: datetime.strptime(s, TS_FORMAT).replace(tzinfo=timezone.utc)
    return {**d, "start": parse(d["start"]), "end": parse(d["end"])}


def retro_proposes(output, context):
    """One retro folder; RETRO.md gives each learning one right action and waits for approval."""
    from runner import RETRO_EXPECTED, RETRO_HOMES, RETRO_OVERFLOW
    d = json.loads(output)
    if len(d["retro_dirs"]) != 1:
        return _result([f"retro folders {d['retro_dirs']}, expected one docs/tasks/<date>-retro/"])
    return _result(retro_proposal_problems(d["retro"], RETRO_EXPECTED, RETRO_HOMES, Path(d["repo_before"]), RETRO_OVERFLOW))


def retro_waits(output, context):
    """Before approval: blocked, and no change outside the retro folder."""
    d = json.loads(output)
    problems = retro_scope_problems(d["changed"])
    if state_fields(d["state"]).get("status") != "blocked":
        problems.append(f"status {state_fields(d['state']).get('status')!r}, expected blocked")
    return _result(problems)


def retro_applies(output, context):
    """After 'Approved.': each action applied, kept entries unchanged, budgets untouched, approval recorded."""
    d = _times(json.loads(output))
    problems = retro_scope_problems(d["turns"][0]["changed"]) if d["turns"] else ["no turns"]
    return _result([f"turn 0: {p}" for p in problems] + retro_applied_problems(d))


def close_starts_retro(output, context):
    """Close removes the task as usual, then retro writes a proposal and changes no learning yet."""
    d = json.loads(output)
    problems = close_problems(d, expect_adr=False)
    if len(d["retro_dirs"]) != 1:
        problems.append(f"retro folders {d['retro_dirs']}, expected one")
    elif "Approval: pending" not in d["retro"]:
        problems.append("RETRO.md does not wait for approval")
    problems += [f"learning removed before approval: {e[:50]}" for e in d["entries"] if e not in d["learnings"]]
    return _result(problems)


# --- AFK stages ------------------------------------------------------------------------------------
def _front(text: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(\S+)", text, re.M)
    return m.group(1) if m else ""


def afk_build_green(output, context):
    d = json.loads(output)
    problems = build_row_problems(d["build"])
    if "[build] All 1 tasks green" not in d["state"]:
        problems.append("build did not finish: " + (d["state"].strip().splitlines() or ["no STATE.md"])[-1][:160])
    subjects = [c.split(" ", 1)[1] for c in d["commits"]]
    if not any(s.startswith("test(T1)") for s in subjects) or not any(s.startswith("feat(T1)") for s in subjects):
        problems.append(f"no test(T1) and feat(T1) commits: {subjects}")
    return _result(problems)


def afk_build_test_first(output, context):
    d = json.loads(output)
    session = next((s for s in d["sessions"] if "BUILD.md" in s["prompt"] and "T1" in s["prompt"]), None)
    if session is None:
        return _result(["no build session for T1"])
    return _result(red_before_code_problems(session["events"], "textstats.py", "test_lines"))


def afk_build_tests_kept(output, context):
    d = json.loads(output)
    problems = flags_problems(d["build"])
    if d["test_textstats_changed"]:
        problems.append("the existing test_textstats.py changed")
    return _result(problems)


def _gate(d: dict, want: str) -> list:
    row = gate_row(d["gates"], "observability")
    if not row:
        return ["GATES.md has no observability row"]
    problems = [] if row[0] == want else [f"observability is {row[0]}, expected {want}: {' '.join(row[2:])[:160]}"]
    if not row[2:] or not row[2].startswith("check:"):
        problems.append("the observability gate ran no check")
    return problems


def afk_gate_check_passes(output, context):
    d = json.loads(output)
    problems = _gate(d, "pass")
    if _front(d["state"], "stage") != "review":
        problems.append(f"stage is {_front(d['state'], 'stage')}, expected review")
    return _result(problems)


def afk_gate_check_fails(output, context):
    d = json.loads(output)
    problems = _gate(d, "fail")
    if "[gates] Blocked: gate observability check failed" not in d["state"]:
        problems.append("the run did not block at the failed check")
    return _result(problems)


def afk_review_waits(output, context):
    d = json.loads(output)
    review = d["review"]
    if not review:
        return _result(["no REVIEW.md"])
    problems = output_header_problems(review, Path(d["task_path"]).name, "review")
    if review.strip().splitlines()[-1].strip() != "Decision: pending":
        problems.append("REVIEW.md does not end with Decision: pending")
    if (_front(d["state"], "stage"), _front(d["state"], "status")) != ("review", "blocked"):
        problems.append("STATE.md is not review blocked")
    return _result(problems)


def afk_review_names_gaps(output, context):
    return _result(review_gap_problems(json.loads(output)["review"]))


def afk_review_learnings(output, context):
    d = json.loads(output)
    lines = new_constraint_lines(d["learnings_before"], d["learnings"])
    if not lines:
        return _result(["review appended no line to learnings.md"])
    ok = [line for line in lines if re.search(r"lint rule|gate", line, re.I)]
    return _result([] if ok else [f"no new learning is a lint rule or gate: {lines[0][:120]}"])


def starts_monitor(output, context):
    """A Monitor tool call that runs `milestones.py watch`: the first mate follows the catchup instruction."""
    for tool in json.loads(output)["tools"]:
        command = json.dumps(tool.get("input") or {})
        if tool.get("name") == "Monitor" and "milestones.py" in command and " watch" in command:
            return _result([])
    return _result(["no Monitor call ran milestones.py watch"])


_PASSED = re.compile(r"exit 0\b|\b(passed|succeeded|success|ok|green)\b|\u2705", re.I)


def _reports(line: str, milestone: str) -> bool:
    """One reply line names the milestone's step (`tests` in `tests exit 0`) and its result: the exit code,
    or for exit 0 a word such as passed. Replies put both in a sentence, a list item or a table row."""
    step, _, code = milestone.split()   # "tests exit 0"
    if not re.search(rf"\b{re.escape(step)}\b", line, re.I):
        return False
    return bool(re.search(rf"exit {code}\b", line) or (code == "0" and _PASSED.search(line) and "fail" not in line.lower()))


def reports_missed(output, context):
    d = json.loads(output)
    lines = d["reply"].splitlines()
    return _result([f"reply does not name the missed milestone {m!r}" for m in d["missed"]
                    if not any(_reports(line, m) for line in lines)])

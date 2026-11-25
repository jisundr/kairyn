"""Pure checks on what a stage run leaves behind. No LLM, no I/O beyond reading files."""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from helpers import split_front_matter

TASK_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$")
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
def log_line_re(stage: str) -> re.Pattern:
    return re.compile(rf"^(\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}:\d{{2}}:\d{{2}}Z) \[{re.escape(stage)}\] \S")


LOG_LINE_RE = log_line_re("requirements")
CLOCK_SLACK = timedelta(seconds=5)


# ASD-STE100, about 80% of the way: the rules a regex can check reliably.
# Not checked: passive voice and trailing -ing phrases (too many false hits).
STE_MAX_WORDS = 25
STE_HEDGES = re.compile(r"\b(should|would|might|may)\b", re.I)
STE_FILLER = re.compile(
    r"\b(in order to|it is important to note|please note|basically|simply|essentially|leverage[sd]?|seamless(?:ly)?)\b",
    re.I,
)
_FENCE = re.compile(r"^```.*?^```", re.S | re.M)
_INLINE_CODE = re.compile(r"`[^`]*`")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _ste_units(text: str) -> list[str]:
    """Prose units: sentences, list items and table cells. Skips front matter, headings and code."""
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        text = parts[2] if len(parts) == 3 else text
    text = _INLINE_CODE.sub("code", _FENCE.sub("", text))
    units = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or re.fullmatch(r"[|\s:-]+", line):
            continue
        cells = [c for c in line.strip("|").split("|")] if line.startswith("|") else [line]
        for cell in cells:
            cell = re.sub(r"^([-*+]|\d+\.)\s+(\[[ x]\]\s+)?", "", cell.strip())
            units += [s for s in _SENTENCE_END.split(cell) if s.strip()]
    return units


def ste_problems(text: str) -> list[str]:
    problems = []
    for unit in _ste_units(text):
        words = len(unit.split())
        if words > STE_MAX_WORDS:
            problems.append(f"long: {words} words: {unit[:60]}")
        problems += [f"hedge: {m.group(1).lower()}" for m in STE_HEDGES.finditer(unit)]
        problems += [f"filler: {m.group(1).lower()}" for m in STE_FILLER.finditer(unit)]
    return problems


def ste_rate(text: str) -> float:
    """STE violations per 100 words of prose."""
    words = sum(len(u.split()) for u in _ste_units(text))
    return round(100 * len(ste_problems(text)) / words, 2) if words else 0.0


# No invention: each acceptance criterion ends with its source, "(request)", "(A1, A3)", a grill decision "(D2)"
# or the requirement it checks "(R1)". Every assumption or requirement it cites is defined in the document.
_CRITERION = re.compile(r"^\s*- \[[ x]\] (.*)$", re.M)
_SOURCE_TAG = re.compile(r"\(((?:request|[ADR]\d+)(?:\s*[,;]\s*(?:request|[ADR]\d+))*)\)", re.I)
_ASSUMPTION_DEF = re.compile(r"^\s*(?:[-*]|\d+\.|\|)?\s*[*`]*\s*(A\d+)\b", re.M)
_REQUIREMENT = re.compile(r"^\s*(?:[-*]|\d+\.)\s*[*`]*(R\d+)\b[*`]*\s*[:.)\u2014-]?\s*(.*)$", re.M)


def _tags(line: str) -> list[str]:
    return [t.lower() if t.lower() == "request" else t.upper() for m in _SOURCE_TAG.finditer(line)
            for t in re.split(r"\s*[,;]\s*", m.group(1))]


def traceability_problems(text: str) -> list[str]:
    criteria = _CRITERION.findall(text)
    if not criteria:
        return ["no acceptance criteria to trace"]
    defined = set(_ASSUMPTION_DEF.findall(text)) | {r for r, _ in _REQUIREMENT.findall(text)}
    problems = []
    for c in criteria:
        tags = _tags(c)
        if not tags:
            problems.append(f"no source: {c[:60]}")
        # D<n> are grill decisions, defined in CONCEPT.md, not here.
        problems += [f"undefined {t}: {c[:40]}" for t in tags if t[0] in "AR" and t not in defined]
    return problems


# --- playbook gaps: EARS requirements, non-functional needs, owners, approval ---------
_EARS = re.compile(r"^(The|When|While|If|Where)\b.*\bshall\b", re.I)
NFR_NEEDS = ("accessibility", "performance", "security", "observability")
_NO_OWNER = {"", "-", "?", "tbd", "none", "n/a", "unknown"}
_APPROVAL = re.compile(r"^\W*Approval\W*:\**\s*(.*?)\s*$", re.M | re.I)
_APPROVED = re.compile(r'^(.+?),\s*(\S+),\s*["\u201c](.*)["\u201d]\W*$')


def ears_problems(text: str) -> list[str]:
    """Each requirement is one EARS sentence with a source, and at least one criterion checks it."""
    reqs = _REQUIREMENT.findall(section_text(text, "requirements"))
    if not reqs:
        return ["no ## Requirements section with R<n> items"]
    checked = {t for c in _CRITERION.findall(text) for t in _tags(c)}
    problems = []
    for rid, body in reqs:
        if not _EARS.match(_SOURCE_TAG.sub("", body).strip(" *`")):
            problems.append(f"{rid} is not in EARS form: {body[:50]}")
        if not [t for t in _tags(body) if not t.startswith("R")]:
            problems.append(f"{rid} has no source")
        if rid not in checked:
            problems.append(f"{rid} has no acceptance criterion")
    return problems


def nfr_problems(text: str) -> list[str]:
    """Each non-functional need is stated with a source, or marked not applicable with a reason."""
    body = section_text(text, "non-functional needs")
    problems = []
    for need in NFR_NEEDS:
        m = re.search(rf"^\s*(?:[-*]|\|)?\s*[*`]*{need}[*`]*\s*(?::|\|)[*`]*(.*)$", body, re.M | re.I)
        if not m:
            problems.append(f"non-functional need missing: {need}")
        elif not m.group(1).strip(" |*`"):
            problems.append(f"non-functional need empty: {need}")
        elif not re.match(r"\W*not applicable\b", m.group(1), re.I) and not _tags(m.group(1)):
            problems.append(f"non-functional need has no source: {need}")
    return problems


def owner_problems(text: str) -> list[str]:
    """Every assumption, risk and dependency sits in one table with a real owner."""
    m = re.search(r"^##\s+[^\n]*\brisks?\b[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.I | re.S)
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in (m.group(1) if m else "").splitlines()
            if line.strip().startswith("|") and not re.fullmatch(r"[|\s:-]+", line.strip())]
    if len(rows) < 2 or "owner" not in [c.lower() for c in rows[0]]:
        return ["no assumptions, risks and dependencies table"]
    col = [c.lower() for c in rows[0]].index("owner")
    problems, ids = [], set()
    for row in rows[1:]:
        rid = row[0].strip("*` ")
        ids.add(rid)
        owner = row[col].strip("*` ") if col < len(row) else ""
        if owner.lower() in _NO_OWNER:
            problems.append(f"{rid} has no owner")
    problems += [f"{a} is not in the owner table" for a in sorted(set(_ASSUMPTION_DEF.findall(text)) - ids)]
    return problems


def approval_problems(text: str, approved: bool, name: str = "", words: str = "",
                      start: datetime | None = None, end: datetime | None = None) -> list[str]:
    """Unapproved: 'Approval: pending'. Approved: 'Approval: <name>, <UTC timestamp>, "<user's words>"'."""
    values = _APPROVAL.findall(text)
    given = [v for v in values if v.strip("*` ").lower() != "pending"]
    if not approved:
        if given:
            return ["approval line written without the user's approval"]
        return [] if values else ["no 'Approval: pending' line"]
    if not given:
        return ["no recorded approval line"]
    m = _APPROVED.match(given[-1].strip("*` "))
    if not m:
        return [f"approval line not '<name>, <timestamp>, \"<words>\"': {given[-1][:60]}"]
    problems = [] if m.group(1).strip() == name else [f"approver {m.group(1).strip()!r} != {name!r}"]
    problems += [p.replace("approval: ", "approval timestamp: ") for p in
                 timestamp_problems({"created": m.group(2), "updated": m.group(2)}, "", start, end)[:1]]
    if words.lower() not in m.group(3).lower():
        problems.append(f"approval does not quote the user's words {words!r}")
    return problems


OUTPUT_HEADER_KEYS = {"task", "stage", "summary"}   # identity only; task state lives in STATE.md
SUMMARY_MAX = 160


def output_header_problems(text: str, task: str, stage: str) -> list[str]:
    """A stage output starts with front matter naming its task and stage, plus a one-line summary."""
    if not text.startswith("---\n") or text.count("---\n") < 2:
        return ["no front matter"]
    try:
        data = yaml.safe_load(text.split("---\n", 2)[1]) or {}
    except yaml.YAMLError as e:
        return [f"front matter invalid: {e}"]
    if not isinstance(data, dict):
        return ["front matter invalid: not a mapping"]
    problems = []
    if str(data.get("task")) != task:
        problems.append(f"front matter task {data.get('task')!r} != folder {task!r}")
    if data.get("stage") != stage:
        problems.append(f"front matter stage {data.get('stage')!r} != {stage!r}")
    summary = str(data.get("summary") or "").strip()
    if not summary:
        problems.append("front matter summary missing")
    elif len(summary) > SUMMARY_MAX:
        problems.append(f"front matter summary over {SUMMARY_MAX} characters")
    extra = sorted(set(data) - OUTPUT_HEADER_KEYS)
    if extra:
        problems.append(f"front matter has state or unknown keys {extra} (state belongs in STATE.md)")
    return problems


def timestamp_problems(data: dict, body: str, start: datetime, end: datetime, stage: str = "requirements") -> list[str]:
    """Timestamps must come from the real clock, not from the model's memory."""
    lo, hi = start - CLOCK_SLACK, end + CLOCK_SLACK
    line_re = log_line_re(stage)

    # YAML parses an unquoted 2026-11-17T06:23:19Z into a datetime; normalise to the Z string.
    def as_raw(v):
        if isinstance(v, datetime):
            v = v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            return v.strftime(TS_FORMAT)
        return str(v)

    stamps = {k: as_raw(data.get(k)) for k in ("created", "updated")}
    for n, line in enumerate(body.splitlines()):
        m = line_re.match(line)
        if m:
            stamps[f"log line {n}"] = m.group(1)
    problems = []
    for label, raw in stamps.items():
        try:
            ts = datetime.strptime(raw, TS_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError:
            problems.append(f"{label}: bad timestamp {raw!r}")
            continue
        if raw.endswith("T00:00:00Z") or raw.endswith("T12:00:00Z"):
            problems.append(f"{label}: placeholder-looking timestamp {raw}")
        elif not lo <= ts <= hi:
            problems.append(f"{label}: {raw} outside run window {start:{TS_FORMAT}}..{end:{TS_FORMAT}}")
    return problems


def structural_problems(run: dict, approved: bool = False) -> list[str]:
    """run = {"task": Path | None, "start": datetime, "end": datetime}.
    Requirements ends blocked on approval. Once the user approved, it hands the task to design (D4)."""
    task, start, end = run["task"], run["start"], run["end"]
    if task is None:
        return ["expected exactly one task folder"]
    problems = []
    if not TASK_DIR_RE.match(task.name):
        problems.append(f"bad task folder name {task.name!r}")
    state, req = task / "STATE.md", task / "REQUIREMENTS.md"
    if not state.exists() or not req.exists():
        return problems + ["STATE.md or REQUIREMENTS.md missing"]
    try:
        fm, body = split_front_matter(state.read_text())
        data = yaml.safe_load(fm)
    except (AssertionError, yaml.YAMLError) as e:
        return problems + [f"STATE.md front matter invalid: {e}"]
    if data.get("stages", {}).get("requirements") != "done":
        problems.append("stages.requirements != done")
    expected = ("design", "in-progress") if approved else ("requirements", "blocked")
    if (data.get("stage"), data.get("status")) != expected:
        problems.append(f"stage {data.get('stage')!r} status {data.get('status')!r}, expected {' '.join(expected)}")
    if not any(LOG_LINE_RE.match(line) for line in body.splitlines()):
        problems.append("no timestamped [requirements] log line")
    problems += timestamp_problems(data, body, start, end)
    run_days = {d.strftime("%Y-%m-%d") for d in (start, end, start.astimezone(), end.astimezone())}
    if TASK_DIR_RE.match(task.name) and task.name[:10] not in run_days:
        problems.append(f"task folder date {task.name[:10]} is not today ({sorted(run_days)})")
    text = req.read_text()
    problems += output_header_problems(text, task.name, "requirements")
    for section in ("problem statement", "scope", "acceptance criteria", "open questions"):
        if section not in text.lower():
            problems.append(f"REQUIREMENTS.md missing {section!r}")
    if not re.search(r"^\s*- \[ \] ", text, re.M):
        problems.append("no acceptance-criteria checkboxes")
    return problems


# --- model-routing stage -------------------------------------------------------
# The stage plans one routing stage at a time (0 = logging and a baseline ... 7 = cascade routing)
# and leaves every human decision (quality bar, goals, thresholds) open unless the user gave it.
ROUTING_STAGE = "model-routing"
ROUTING_SECTIONS = ("call sites", "next stage", "decisions", "build plan", "gates")
_NEXT_STAGE = re.compile(r"^##\s+Next stage\s*\n+\s*\**Stage\s+(\d)\b", re.M | re.I)
_DECISION = re.compile(r"^\s*(?:[-*]|\d+\.|\|)?\s*[*`]*\s*(D\d+)\b(.*)$", re.M)


def next_routing_stage(text: str) -> int | None:
    m = _NEXT_STAGE.search(text)
    return int(m.group(1)) if m else None


def open_decisions(text: str) -> list[str]:
    """Decision labels whose line says they are still open."""
    return [d for d, rest in _DECISION.findall(text) if re.search(r"\bopen\b", rest, re.I)]


def routing_problems(run: dict) -> list[str]:
    """run = {"task": Path | None, "start": datetime, "end": datetime}"""
    task, start, end = run["task"], run["start"], run["end"]
    if task is None:
        return ["expected exactly one task folder"]
    state, doc = task / "STATE.md", task / "MODEL-ROUTING.md"
    if not doc.exists():
        return ["MODEL-ROUTING.md missing"]
    try:
        fm, body = split_front_matter(state.read_text())
        data = yaml.safe_load(fm)
    except (AssertionError, FileNotFoundError, yaml.YAMLError) as e:
        return [f"STATE.md unreadable: {e}"]
    problems = []
    stages = data.get("stages") or {}
    if stages.get("requirements") != "done":
        problems.append("stages.requirements != done")
    if stages.get(ROUTING_STAGE) not in ("in-progress", "done"):
        problems.append(f"stages.{ROUTING_STAGE} is {stages.get(ROUTING_STAGE)!r}, expected in-progress or done")
    if not any(log_line_re(ROUTING_STAGE).match(line) for line in body.splitlines()):
        problems.append(f"no timestamped [{ROUTING_STAGE}] log line")
    # The task (and its `created`) predates this stage run; `updated` and the log line must not.
    problems += [p for p in timestamp_problems(data, body, start, end, ROUTING_STAGE) if not p.startswith("created")]
    text = doc.read_text()
    problems += output_header_problems(text, task.name, ROUTING_STAGE)
    for section in ROUTING_SECTIONS:
        if not re.search(rf"^##\s+{section}\b", text, re.M | re.I):
            problems.append(f"MODEL-ROUTING.md missing section {section!r}")
    if next_routing_stage(text) is None:
        problems.append("Next stage section does not start with 'Stage <n>'")
    return problems


# --- grill stage ---------------------------------------------------------------
# The stage interviews the user one question at a time and keeps the shared concept in CONCEPT.md.
GRILL_STAGE = "grill"
CONCEPT_SECTIONS = ("concept", "decisions", "terms", "open branches")
_QUESTION = re.compile(r"^\W*(?:Q\d+|Question)\b[^:\n]*:", re.M | re.I)
_RECOMMENDED = re.compile(r"^\W*Recommended\b[^:\n]*:", re.M | re.I)
_NONE_ITEM = re.compile(r"^\W*(none|n/a|-)\W*$", re.I)
MAX_QUESTION_MARKS = 2   # the question, plus at most one inside the recommendation


def section_text(text: str, name: str) -> str:
    """Body of the `## <name>` section, up to the next `## ` heading."""
    m = re.search(rf"^##\s+{re.escape(name)}\b[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.I | re.S)
    return m.group(1) if m else ""


def section_items(text: str, name: str) -> list[str]:
    """List items and table rows of a section, leaving out table headers and "None"."""
    items = []
    for line in section_text(text, name).splitlines():
        line = line.strip()
        if re.fullmatch(r"[|\s:-]+", line) or not re.match(r"([-*+]|\d+\.|\|)\s*", line):
            continue
        item = re.sub(r"^([-*+]|\d+\.)\s+", "", line).strip("| ")
        if item and not _NONE_ITEM.match(item):
            items.append(item)
    return items[1:] if section_text(text, name).lstrip().startswith("|") else items


def decision_labels(text: str) -> set[str]:
    return set(re.findall(r"\bD\d+\b", section_text(text, "decisions")))


def grill_reply_problems(reply: str) -> list[str]:
    """One question per message, with a recommended answer."""
    problems = []
    questions = len(_QUESTION.findall(reply))
    if questions != 1:
        problems.append(f"{questions} question markers, expected 1")
    if not _RECOMMENDED.search(reply):
        problems.append("no recommended answer")
    marks = reply.count("?")
    if marks > MAX_QUESTION_MARKS:
        problems.append(f"{marks} question marks, more than one question")
    return problems


def state_fields(state_text: str) -> dict:
    """{"stage", "status", "stages"} from a STATE.md, or {} when it does not parse."""
    try:
        data = yaml.safe_load(split_front_matter(state_text)[0]) or {}
    except (AssertionError, yaml.YAMLError):
        return {}
    return {"stage": data.get("stage"), "status": data.get("status"), "stages": data.get("stages") or {}}


def grill_problems(run: dict, stopped: bool = True) -> list[str]:
    """Final state after an interview. run = {"task": Path | None, "start": datetime, "end": datetime}.
    stopped=True: the user stopped early, so open branches remain."""
    task, start, end = run["task"], run["start"], run["end"]
    if task is None:
        return ["expected exactly one task folder"]
    problems = [] if TASK_DIR_RE.match(task.name) else [f"bad task folder name {task.name!r}"]
    state, doc = task / "STATE.md", task / "CONCEPT.md"
    if not state.exists() or not doc.exists():
        return problems + ["STATE.md or CONCEPT.md missing"]
    try:
        fm, body = split_front_matter(state.read_text())
        data = yaml.safe_load(fm)
    except (AssertionError, yaml.YAMLError) as e:
        return problems + [f"STATE.md front matter invalid: {e}"]
    stages = data.get("stages") or {}
    if stages.get(GRILL_STAGE) != "done":
        problems.append(f"stages.{GRILL_STAGE} is {stages.get(GRILL_STAGE)!r}, expected done")
    if data.get("stage") != "requirements" or data.get("status") != "in-progress":
        problems.append(f"stage {data.get('stage')!r} status {data.get('status')!r}, expected requirements in-progress")
    if not any(log_line_re(GRILL_STAGE).match(line) for line in body.splitlines()):
        problems.append(f"no timestamped [{GRILL_STAGE}] log line")
    problems += timestamp_problems(data, body, start, end, GRILL_STAGE)
    text = doc.read_text()
    problems += output_header_problems(text, task.name, GRILL_STAGE)
    for section in CONCEPT_SECTIONS:
        if not re.search(rf"^##\s+{section}\b", text, re.M | re.I):
            problems.append(f"CONCEPT.md missing section {section!r}")
    if not decision_labels(text):
        problems.append("no D<n> decision in CONCEPT.md")
    if stopped and not section_items(text, "open branches"):
        problems.append("stopped early but no open branch listed")
    return problems


def handoff_problems(reply: str, task: Path, next_stage: str) -> list[str]:
    """After approval the stage ends by telling the user the exact next command and does not run it (ADR 0004):
    a chained skill runs on the caller's model, so the user types `/kairyn:<next stage> <task folder>`."""
    command = f"/kairyn:{next_stage}"
    problems = [] if command in reply else [f"last message does not name {command}"]
    if task.name not in reply:
        problems.append(f"last message does not name the task folder {task.name}")
    output = task / f"{next_stage.upper()}.md"
    if output.exists():
        problems.append(f"{output.name} written: the stage ran {next_stage} instead of handing off")
    return problems


def concept_use_problems(task: Path, decisions: tuple[str, ...], must_mention: str) -> list[str]:
    """requirements ran on a task that grill already shaped: same folder, decisions cited, decided value kept."""
    req = task / "REQUIREMENTS.md"
    if not req.exists():
        return ["REQUIREMENTS.md missing in the grill task folder"]
    text = req.read_text()
    problems = [f"{d} not cited" for d in decisions if not re.search(rf"\b{d}\b", text)]
    if must_mention.lower() not in text.lower():
        problems.append(f"decided value {must_mention!r} missing")
    return problems


# --- close stage -------------------------------------------------------------------

ADR_SECTIONS = ("## Status", "## Context", "## Decision", "## Consequences")


def close_problems(e: dict, expect_adr: bool, keyword: str = "") -> list[str]:
    """What /kairyn:close must leave: no task folder, a changelog entry, closed backlog gone, ADRs only when due.

    e: {"task", "task_exists", "changelog", "adrs": {name: text}, "backlog_left": [names]}
    """
    problems = []
    if e["task_exists"]:
        problems.append("task folder still exists")
    log = e["changelog"]
    unreleased = log.split("## Unreleased", 1)[1].split("\n## ", 1)[0] if "## Unreleased" in log else ""
    if not re.search(rf"^- .+\({re.escape(e['task'])}\)\s*$", unreleased, re.M):
        problems.append("no changelog entry for the task under ## Unreleased")
    if "1-linked.md" in e["backlog_left"]:
        problems.append("linked committed backlog file not deleted")
    if "2-parked.md" not in e["backlog_left"]:
        problems.append("parked backlog file deleted")
    adrs = e["adrs"]
    if expect_adr and not adrs:
        problems.append("no ADR for a load-bearing decision")
    if not expect_adr and adrs:
        problems.append(f"ADR written for a task with no load-bearing decision: {sorted(adrs)}")
    for name, text in adrs.items():
        if not re.fullmatch(r"\d{4}-[a-z0-9-]+\.md", name):
            problems.append(f"{name}: not named <NNNN>-<slug>.md")
        missing = [s for s in ADR_SECTIONS if s not in text.splitlines()]
        if missing:
            problems.append(f"{name}: missing {', '.join(missing)}")
        if e["task"] not in text:
            problems.append(f"{name}: does not name the task")
        if keyword and keyword.lower() not in text.lower():
            problems.append(f"{name}: does not mention {keyword}")
    return problems


# --- design stage ---------------------------------------------------------------
# DESIGN.md: Approach, Options (2+, one the smallest thing), Tasks (T<n>), Test plan (AC<n> -> T<n> -> test).
# AC<n> is the n-th acceptance criterion in REQUIREMENTS.md. Standards impact waits for a gates stage (D5).
DESIGN_SECTIONS = ("approach", "options", "tasks", "test plan")
_TASK_DEF = re.compile(r"^\s*(?:[-*]|\d+\.|\|)?\s*[*`]*(T\d+)\b", re.M)
_PATH = re.compile(r"`([^`\s]*/[^`\s]*)`(\s*\(new\))?")


def design_section_problems(text: str) -> list[str]:
    headings = {h.strip().lower() for h in re.findall(r"^##\s+(.+?)\s*$", text, re.M)}
    problems = [f"DESIGN.md missing section {s!r}" for s in DESIGN_SECTIONS if s not in headings]
    if "standards impact" in headings:
        problems.append("DESIGN.md has a section the stage does not write: 'standards impact'")
    return problems


def options_problems(text: str) -> list[str]:
    options = section_items(text, "options")
    problems = [] if len(options) >= 2 else [f"{len(options)} option(s), expected at least 2"]
    if not any("smallest" in o.lower() for o in options):
        problems.append("no option is the smallest thing")
    return problems


def design_test_plan_problems(design: str, requirements: str) -> list[str]:
    criteria = _CRITERION.findall(section_text(requirements, "acceptance criteria"))
    if not criteria:
        return ["REQUIREMENTS.md has no acceptance criteria"]
    tasks = set(_TASK_DEF.findall(section_text(design, "tasks")))
    rows = section_items(design, "test plan")
    problems = []
    for n in range(1, len(criteria) + 1):
        row = next((r for r in rows if re.search(rf"\bAC{n}\b", r)), None)
        if row is None:
            problems.append(f"AC{n} has no row in the test plan")
            continue
        cells = [c.strip() for c in row.split("|")]
        if not set(re.findall(r"\bT\d+\b", row)) & tasks:
            problems.append(f"AC{n} names no task from the Tasks section")
        elif len(cells) < 3 or not cells[-1]:
            problems.append(f"AC{n} names no test")
    return problems


def _looks_like_branch(path: str, repo: Path) -> bool:
    """`feat/x`: no file extension, no trailing slash, and its first folder is not in the repo."""
    return "." not in path.rsplit("/", 1)[-1] and not path.endswith("/") and not (repo / path.split("/")[0]).exists()


def grounded_problems(text: str, repo: Path) -> list[str]:
    """Each path in backticks exists in the repo, unless it carries `(new)` somewhere in the text.
    A branch name such as `feat/x` is not a path."""
    found = _PATH.findall(text)
    created = {path for path, new in found if new}
    problems = []
    for path, new in found:
        if path in created or path.startswith("/") or "://" in path or any(c in path for c in "<>*{}$"):
            continue
        path = re.sub(r":\d+(-\d+)?$", "", path)
        if _looks_like_branch(path, repo):
            continue
        if not (repo / path).exists() and f"names a missing file: {path}" not in problems:
            problems.append(f"names a missing file: {path}")
    return problems


_OPTION_CELL = re.compile(r"^[*`\s]*(?:Option\s+)?([A-Z])\b", re.I)


def option_labels(text: str) -> list[str]:
    """The letter of each option row: 'A (smallest thing)' or 'Option B' gives A, B."""
    return [m.group(1).upper() for item in section_items(text, "options") if (m := _OPTION_CELL.match(item))]


def chosen_option(text: str) -> str | None:
    m = re.search(r"\bOption\s+([A-Z])\b", section_text(text, "approach"))
    return m.group(1) if m else None


def rejected_option(text: str) -> str | None:
    """An option the design did not choose, for the eval's 'go with option X' turn."""
    chosen = chosen_option(text)
    return next((o for o in option_labels(text) if o != chosen), None) if chosen else None


def slice_problems(text: str) -> list[str]:
    """D13: the T<n> lines are slices afk.py can run: each has a `Done: `<command>``, the graph has no cycle,
    and each slice after T1 names its blockers with `after:`."""
    import sys
    scripts = str(Path(__file__).resolve().parent.parent / "plugin" / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from afk import task_graph
    tasks = section_text(text, "tasks")
    try:
        graph = task_graph(tasks)
    except ValueError as e:
        return [str(e)]
    return [f"{t.id} has no after: line" for t in graph if t.id != "T1" and not t.after]


def design_run_problems(run: dict, approved: bool = False) -> list[str]:
    """run = {"task": Path, "start", "end"}. Design waits blocked on approval, then hands the task to build (D5)."""
    task = run["task"]
    doc, state = task / "DESIGN.md", task / "STATE.md"
    if not doc.exists():
        return ["DESIGN.md missing"]
    try:
        fm, body = split_front_matter(state.read_text())
        data = yaml.safe_load(fm)
    except (OSError, AssertionError, yaml.YAMLError) as e:
        return [f"STATE.md unreadable: {e}"]
    problems = []
    expected = ("build", "in-progress") if approved else ("design", "blocked")
    if (data.get("stage"), data.get("status")) != expected:
        problems.append(f"stage {data.get('stage')!r} status {data.get('status')!r}, expected {' '.join(expected)}")
    if (data.get("stages") or {}).get("design") != "done":
        problems.append("stages.design != done")
    if not any(log_line_re("design").match(line) for line in body.splitlines()):
        problems.append("no timestamped [design] log line")
    # The fixture's created time is old on purpose: check only what design writes.
    problems += timestamp_problems({"created": data.get("updated"), "updated": data.get("updated")}, body,
                                   run["start"], run["end"], stage="design")
    text = doc.read_text()
    problems += output_header_problems(text, task.name, "design") + design_section_problems(text) + slice_problems(text)
    return problems


def repo_line_problems(state: str, expected: str | None) -> list[str]:
    """STATE.md front matter `repo:` names the child repo of a home-repo task (multi-repo D3). None: no line."""
    m = re.search(r"\A---\n(.*?)\n---\n", state, re.S)
    if not m:
        return ["STATE.md has no front matter"]
    found = re.findall(r"^repo:\s*(\S*)\s*$", m.group(1), re.M)
    if expected is None:
        return [f"repo: {found[0]} in STATE.md, expected no repo: line"] if found else []
    if not found:
        return [f"no repo: line in STATE.md, expected repo: {expected}"]
    return [] if found == [expected] else [f"repo: {', '.join(found)} in STATE.md, expected repo: {expected}"]


# --- retro stage ------------------------------------------------------------------
# RETRO.md has one table row per learning, numbered L<n> in learnings.md order:
#   | L1 | move | `<home>` | <text to add> |
# Actions: move, drop, backlog, keep. Close runs retro when learnings.md is past half its budget.
RETRO_ACTIONS = ("move", "drop", "backlog", "keep")
_RETRO_ROW = re.compile(r"^\|\s*\**`?(L\d+)`?\**\s*\|\s*\**`?(\w+)`?\**\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", re.M)
_ENTRY = re.compile(r"^- \d{4}-\d\d-\d\d \[[\w-]+\] (.+)$", re.M)
_CELL_PATH = re.compile(r"`([^`\s]+)`")


def learning_entries(text: str) -> list[str]:
    """The full lines of learnings.md entries, in order (L1 is the first)."""
    return [m.group(0) for m in _ENTRY.finditer(text)]


def entry_text(line: str) -> str:
    m = _ENTRY.match(line)
    return m.group(1).strip() if m else line


def retro_rows(text: str) -> dict[str, tuple[str, str, str]]:
    """{"L1": (action, home cell, detail cell)}; the action is lower case."""
    return {m.group(1): (m.group(2).lower(), m.group(3), m.group(4)) for m in _RETRO_ROW.finditer(text)}


def _cell_paths(cell: str) -> list[str]:
    return _CELL_PATH.findall(cell) or [cell.strip()]


def retro_proposal_problems(text: str, expected: dict[str, set], homes: dict[str, str], repo: Path,
                            overflow: tuple[str, ...] = ()) -> list[str]:
    """RETRO.md before approval. expected: {"L1": {"move"}}; homes: {"L1": "<path>"} for expected moves;
    repo: the fixture as it was before the run (paths must exist there); overflow: entries whose home is full."""
    rows = retro_rows(text)
    problems = [f"no row for {n}" for n in expected if n not in rows]
    problems += [f"row {n} is not a learning" for n in rows if n not in expected]
    for n, (action, home, detail) in rows.items():
        if n not in expected:
            continue
        if action not in RETRO_ACTIONS:
            problems.append(f"{n}: unknown action {action!r}")
            continue
        if action not in expected[n]:
            problems.append(f"{n}: {action}, expected {'/'.join(sorted(expected[n]))}")
        if action == "move":
            paths = _cell_paths(home)
            if n in homes and homes[n] not in paths:
                problems.append(f"{n}: move home {home!r}, expected {homes[n]}")
            if not any((repo / p).is_file() for p in paths):
                problems.append(f"{n}: move home {home!r} does not exist")
            if not detail.strip():
                problems.append(f"{n}: move gives no text to add")
        elif action == "drop":
            if not any((repo / p).is_file() for p in _cell_paths(home)) and not detail.strip():
                problems.append(f"{n}: drop names no existing path and no reason")
        elif action == "keep" and not detail.strip() and not home.strip():
            problems.append(f"{n}: keep gives no reason")
        if action == "backlog" and n in overflow and not re.search(r"\bover\b.*\d|\d+\s*tokens?\s*over", (home + " " + detail).lower()):
            problems.append(f"{n}: backlog for a full home does not name the overflow")
    return problems + approval_problems(text, approved=False)


def retro_scope_problems(changed: list[str]) -> list[str]:
    """Before approval, retro changes nothing outside its own task folder docs/tasks/<date>-retro/."""
    outside = [p for p in changed if not re.match(r"docs/tasks/\d{4}-\d\d-\d\d-retro[\w-]*/", p)]
    return [f"changed before approval: {p}" for p in outside]


def retro_applied_problems(run: dict) -> list[str]:
    """After approval. run = {"entries": [lines before], "retro": RETRO.md, "learnings": text after,
    "backlog": {name: text} of new backlog files, "homes_before"/"homes_after": {path: text},
    "budgets_before"/"budgets_after": text, "state": STATE.md, "approver", "words", "start", "end"}."""
    rows = retro_rows(run["retro"])
    if not rows:
        return ["RETRO.md has no action rows"]
    problems = []
    after = set(learning_entries(run["learnings"]))
    for i, line in enumerate(run["entries"], 1):
        action = rows.get(f"L{i}", ("?",))[0]
        if action == "keep" and line not in after:
            problems.append(f"L{i}: kept entry changed or removed")
        if action != "keep" and line in after:
            problems.append(f"L{i}: {action} entry still in learnings.md")
        if action == "backlog":
            quoted = [name for name, text in run["backlog"].items()
                      if entry_text(line) in text and re.search(r"^status:\s*inbox\s*$", text, re.M)]
            if not quoted:
                problems.append(f"L{i}: no inbox backlog idea quotes the learning")
        if action == "move":
            home = _cell_paths(rows[f"L{i}"][1])[0]
            if run["homes_after"].get(home) == run["homes_before"].get(home):
                problems.append(f"L{i}: home {home} unchanged")
    extra = after - set(run["entries"])
    problems += [f"new entry in learnings.md: {e[:50]}" for e in sorted(extra)]
    if run["budgets_after"] != run["budgets_before"]:
        problems.append("budgets.yml changed")
    if state_fields(run["state"]).get("status") != "done":
        problems.append(f"retro status {state_fields(run['state']).get('status')!r}, expected done")
    return problems + approval_problems(run["retro"], approved=True, name=run["approver"], words=run["words"],
                                        start=run["start"], end=run["end"])


# --- AFK stages: build, gates, review (afk.py drives them; evidence from evals/afk_fixtures.py) -------
def _tool_calls(events: list) -> list:
    """[(name, input, result_text, is_error)] in session order, from `claude -p --output-format stream-json`."""
    calls, results = [], {}
    for e in events:
        message = e.get("message") if isinstance(e, dict) else None
        for c in (message.get("content") or []) if isinstance(message, dict) else []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                calls.append((c.get("id"), c.get("name"), c.get("input") or {}))
            elif c.get("type") == "tool_result":
                body = c.get("content")
                text = body if isinstance(body, str) else " ".join(
                    b.get("text", "") for b in body or [] if isinstance(b, dict))
                results[c.get("tool_use_id")] = (text, bool(c.get("is_error")))
    return [(name, inp, *results.get(cid, ("", False))) for cid, name, inp in calls]


_FAILED_RUN = re.compile(r"\b(FAILED|FAIL|Error|Traceback|AssertionError)\b")


def _writes(name: str, inp: dict, path: str) -> bool:
    """A tool call that writes `path`: Write, Edit or MultiEdit, or a Bash redirect, tee, sed -i or heredoc,
    or a Python script that opens `path` (or a name set to it) to write."""
    if name in ("Write", "Edit", "MultiEdit"):
        return str(inp.get("file_path", "")).endswith(path)
    cmd = str(inp.get("command", "")) if name == "Bash" else ""
    if re.search(rf"(>>?|\btee\b(\s+-a)?|\bsed\s+-i\S*(\s+'[^']*'|\s+\S+)?)\s*\S*{re.escape(path)}\b", cmd):
        return True
    lit = rf"(?:Path\()?['\"]{re.escape(path)}['\"]\)?"
    names = [lit] + [re.escape(v) for v in re.findall(rf"\b(\w+)\s*=\s*{lit}", cmd)]
    target = "(?:" + "|".join(names) + ")"
    return bool(re.search(rf"open\(\s*{target}\s*,\s*['\"][wa]|\b{target}\.write_text\(", cmd))


def red_before_code_problems(events: list, code_file: str, test_word: str) -> list[str]:
    """D12 inside one build session: a run of the test that fails comes before the first edit of the code file."""
    calls = _tool_calls(events)
    edit = next((i for i, (name, inp, _, _) in enumerate(calls) if _writes(name, inp, code_file)), None)
    if edit is None:
        return [f"the session never edited {code_file}"]
    red = [i for i, (name, inp, text, err) in enumerate(calls[:edit])
           if name == "Bash" and test_word in str(inp.get("command", "")) and (err or _FAILED_RUN.search(text))]
    return [] if red else [f"no failing run of {test_word} before the first edit of {code_file}"]


def split_build_problems(tests: list, code: list, code_file: str, test_word: str) -> list[str]:
    """D3 of task 2026-11-26-split-build-routing: the tests part runs the test red and writes no code;
    the code part writes the code."""
    tests_calls, code_calls = _tool_calls(tests), _tool_calls(code)
    problems = []
    if any(_writes(name, inp, code_file) for name, inp, _, _ in tests_calls):
        problems.append(f"the tests part wrote {code_file}")
    if not any(name == "Bash" and test_word in str(inp.get("command", "")) and (err or _FAILED_RUN.search(text))
               for name, inp, text, err in tests_calls):
        problems.append(f"the tests part never ran {test_word} red")
    if not any(_writes(name, inp, code_file) for name, inp, _, _ in code_calls):
        problems.append(f"the code part never wrote {code_file}")
    return problems


def build_row_problems(build: str, tid: str = "T1") -> list[str]:
    row = re.search(rf"^\| {tid} \| (\w+) \| (\d+) \| (\w+) \| (\d+) \|", build, re.M)
    if not row:
        return [f"BUILD.md has no {tid} row"]
    return ([f"red exit {row.group(2)} is 0"] if row.group(2) == "0" else []) + \
        ([f"green exit {row.group(4)} is not 0"] if row.group(4) != "0" else [])


def flags_problems(build: str) -> list[str]:
    flags = build.split("\n## Flags\n", 1)[1].split("\n## ", 1)[0].strip() if "\n## Flags\n" in build else ""
    return [] if flags == "- None" else [f"flags: {flags or 'no ## Flags section'}"]


def gate_row(gates: str, name: str) -> list[str]:
    row = re.search(rf"^\| {name} \|(.*)$", gates, re.M)
    return [c.strip() for c in row.group(1).strip(" |").split("|")] if row else []


def review_gap_problems(review: str) -> list[str]:
    """The review fixture has a `not set` security gate, a `# noqa` flag and AC2 (--chars) with no code or test."""
    low = review.lower()
    problems = []
    if "security" not in section_text(review, "gates").lower():
        problems.append("## Gates does not name the security gate that is not set")
    if "noqa" not in low:
        problems.append("REVIEW.md does not name the # noqa flag")
    findings = section_text(review, "findings")
    if not re.search(r"AC2|--chars|\bchars\b", findings):
        problems.append("## Findings does not name AC2 (--chars), which has no code and no test")
    return problems


def new_constraint_lines(before: str, after: str) -> list[str]:
    old = set(before.splitlines())
    return [line for line in after.splitlines() if line.startswith("- ") and line not in old]

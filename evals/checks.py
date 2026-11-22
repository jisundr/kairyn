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


# No invention: each acceptance criterion ends with its source, "(request)", "(A1, A3)" or a grill decision "(D2)",
# and every assumption it cites is defined as a labeled assumption (a line that starts with A<n>).
_CRITERION = re.compile(r"^\s*- \[[ x]\] (.*)$", re.M)
_SOURCE_TAG = re.compile(r"\(((?:request|[AD]\d+)(?:\s*[,;]\s*(?:request|[AD]\d+))*)\)", re.I)
_ASSUMPTION_DEF = re.compile(r"^\s*(?:[-*]|\d+\.|\|)?\s*[*`]*\s*(A\d+)\b", re.M)


def traceability_problems(text: str) -> list[str]:
    criteria = _CRITERION.findall(text)
    if not criteria:
        return ["no acceptance criteria to trace"]
    defined = set(_ASSUMPTION_DEF.findall(text))
    problems = []
    for c in criteria:
        tags = [t for m in _SOURCE_TAG.finditer(c) for t in re.split(r"\s*[,;]\s*", m.group(1))]
        if not tags:
            problems.append(f"no source: {c[:60]}")
        # D<n> are grill decisions, defined in CONCEPT.md, not here.
        problems += [f"undefined {t}: {c[:40]}" for t in tags if t[0] in "Aa" and t not in defined]
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


def structural_problems(run: dict) -> list[str]:
    """run = {"task": Path | None, "start": datetime, "end": datetime}"""
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
    # Only stage defined today, so "finished" means status: done (or stage moved on).
    if data.get("stage") == "requirements" and data.get("status") != "done":
        problems.append("stage not advanced and status not done")
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

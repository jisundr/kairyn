"""Probabilistic: real `claude` sessions, repeated N times, asserted on pass rate.

Slow and costs tokens, so excluded by default. Run with:
    uv run pytest -m probabilistic
Tune with env vars: KAIRYN_RUNS (default 10), KAIRYN_MODEL, KAIRYN_JUDGE_MODEL.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from conftest import PLUGIN, ROOT, make_good_repo, run_verify, split_front_matter

pytestmark = pytest.mark.probabilistic

RUNS = int(os.environ.get("KAIRYN_RUNS", "10"))
MODEL = os.environ.get("KAIRYN_MODEL")
JUDGE_MODEL = os.environ.get("KAIRYN_JUDGE_MODEL", MODEL)

REQUEST = "Add a --dry-run flag to the CLI that prints what would change without writing files."
TASK_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$")
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
LOG_LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \[requirements\] \S")
CLOCK_SLACK = timedelta(seconds=5)

# Evidence for every run is saved here (git-ignored) so a pass can be audited later.
RESULTS = ROOT / "tests" / "results" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_text(name: str, text: str) -> None:
    path = RESULTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def save_tree(name: str, src: Path) -> None:
    shutil.copytree(src, RESULTS / name, dirs_exist_ok=True)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def claude(prompt: str, cwd: Path, *, plugin: bool = False, model: str | None = None, timeout: int = 600) -> str:
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "text"]
    if plugin:
        cmd += ["--plugin-dir", str(PLUGIN)]
    if model:
        cmd += ["--model", model]
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return result.stdout


def new_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Sample CLI\n")
    return repo


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def assert_rate(passes: int, minimum: int, details: list[str]):
    assert passes >= minimum, f"{passes}/{RUNS} passed (need {minimum}):\n" + "\n".join(details)


def test_init_reliability(tmp_path):
    """/kairyn:init produces a verified layout in a fresh repo."""
    passes, details = 0, []
    for i in range(RUNS):
        repo = new_repo(tmp_path, f"init-{i}")
        claude("/kairyn:init", repo, plugin=True, model=MODEL)
        result = run_verify(repo)
        save_text(f"init-reliability/run-{i:02d}.txt", f"exit={result.returncode}\n{result.stdout}")
        if result.returncode == 0:
            passes += 1
        else:
            details.append(f"run {i}: {result.stdout.strip()}")
    assert_rate(passes, int(RUNS * 0.9), details)


def test_init_is_idempotent(tmp_path):
    """Running init again must not change or overwrite anything."""
    passes, details = 0, []
    for i in range(RUNS):
        repo = make_good_repo(new_repo(tmp_path, f"idem-{i}"))
        (repo / ".kairyn" / "learnings.md").write_text("# Learnings\n\nuser note: keep me\n")
        before = tree_hash(repo / ".kairyn")
        claude("/kairyn:init", repo, plugin=True, model=MODEL)
        if tree_hash(repo / ".kairyn") == before:
            passes += 1
        else:
            details.append(f"run {i}: .kairyn/ changed")
    assert_rate(passes, RUNS, details)  # overwriting user edits is the worst failure


def run_requirements(repo: Path) -> dict:
    start = utcnow()
    claude(
        "Follow the stage definition in .kairyn/stages/REQUIREMENTS.md exactly. "
        f"Request: {REQUEST} Do not ask questions; make reasonable assumptions and record them.",
        repo, model=MODEL,
    )
    end = utcnow()
    tasks = [p for p in (repo / "docs" / "tasks").iterdir() if p.is_dir()]
    return {"task": tasks[0] if len(tasks) == 1 else None, "start": start, "end": end}


def timestamp_problems(data: dict, body: str, start: datetime, end: datetime) -> list[str]:
    """Timestamps must come from the real clock, not from the model's memory."""
    lo, hi = start - CLOCK_SLACK, end + CLOCK_SLACK
    # YAML parses an unquoted 2026-11-17T06:23:19Z into a datetime; normalise to the Z string.
    def as_raw(v):
        if isinstance(v, datetime):
            v = v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            return v.strftime(TS_FORMAT)
        return str(v)

    stamps = {k: as_raw(data.get(k)) for k in ("created", "updated")}
    for n, line in enumerate(body.splitlines()):
        m = LOG_LINE_RE.match(line)
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
    for section in ("problem statement", "scope", "acceptance criteria", "open questions"):
        if section not in text.lower():
            problems.append(f"REQUIREMENTS.md missing {section!r}")
    if not re.search(r"^\s*- \[ \] ", text, re.M):
        problems.append("no acceptance-criteria checkboxes")
    return problems


@pytest.fixture(scope="module")
def requirements_runs(tmp_path_factory):
    """Run the requirements stage RUNS times once; both tests below reuse the results."""
    runs = []
    for i in range(RUNS):
        repo = make_good_repo(new_repo(tmp_path_factory.mktemp(f"req-{i}"), "repo"))
        run = run_requirements(repo)
        if run["task"] is not None:
            save_tree(f"requirements/run-{i:02d}/{run['task'].name}", run["task"])
        save_text(f"requirements/run-{i:02d}/window.txt", f"{run['start']:{TS_FORMAT}} .. {run['end']:{TS_FORMAT}}\n")
        runs.append(run)
    return runs


def test_requirements_structure(requirements_runs):
    """Every run leaves a well-formed task folder, STATE.md and REQUIREMENTS.md."""
    passes, details = 0, []
    for i, run in enumerate(requirements_runs):
        problems = structural_problems(run)
        save_text(f"requirements/run-{i:02d}/problems.txt", "\n".join(problems) or "none")
        if problems:
            details.append(f"run {i}: {'; '.join(problems)}")
        else:
            passes += 1
    assert_rate(passes, int(RUNS * 0.9), details)


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


def test_requirements_quality(requirements_runs, tmp_path):
    """LLM judge: mean score >= 4 and no single criterion below 3."""
    scores = []
    for i, run in enumerate(requirements_runs):
        task = run["task"]
        if task is None or not (task / "REQUIREMENTS.md").exists():
            continue
        out = claude(RUBRIC.format(request=REQUEST, doc=(task / "REQUIREMENTS.md").read_text()),
                     tmp_path, model=JUDGE_MODEL)
        match = re.search(r"\{.*?\}", out, re.S)
        save_text(f"judge/run-{i:02d}.txt", out)
        if match:
            scores.append(json.loads(match.group()))
    assert len(scores) >= int(RUNS * 0.9), f"only {len(scores)} runs produced a gradable document"
    save_text("judge/scores.json", json.dumps(scores, indent=2))
    values = [v for s in scores for v in s.values()]
    mean = sum(values) / len(values)
    assert min(values) >= 3, f"a criterion scored below 3: {scores}"
    assert mean >= 4, f"mean score {mean:.2f} < 4: {scores}"

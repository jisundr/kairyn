"""Helpers that drive real `claude` sessions and save evidence for every run."""
import hashlib
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from helpers import PLUGIN, ROOT

DEFAULT_RUNS = 10
RUNS = int(os.environ.get("KAIRYN_EVAL_RUNS", DEFAULT_RUNS))
MODEL = os.environ.get("KAIRYN_MODEL")
JUDGE_MODEL = os.environ.get("KAIRYN_JUDGE_MODEL", MODEL)

REQUEST = "Add a --dry-run flag to the CLI that prints what would change without writing files."

RESULTS_ROOT = ROOT / "evals" / "results"
PASSED_RECORD = RESULTS_ROOT / "passed.json"
RESULTS = RESULTS_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


SUMMARY: list[tuple[str, str]] = []   # (feature, one-line result), printed at the end of the run


def summarize(feature: str, line: str) -> None:
    SUMMARY.append((feature, line))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def save_text(name: str, text: str) -> None:
    path = RESULTS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def save_tree(name: str, src: Path) -> None:
    shutil.copytree(src, RESULTS / name, dirs_exist_ok=True)


def claude(prompt: str, cwd: Path, *, plugin: bool = False, model: str | None = None, timeout: int = 600) -> str:
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits", "--output-format", "text"]
    if plugin:
        cmd += ["--plugin-dir", str(PLUGIN)]
    if model:
        cmd += ["--model", model]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout).stdout


def new_repo(parent: Path, name: str) -> Path:
    repo = parent / name
    repo.mkdir(parents=True)
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


def judge(doc: str, cwd: Path) -> tuple[str, dict | None]:
    """Returns (raw judge output, parsed scores or None)."""
    import json
    out = claude(RUBRIC.format(request=REQUEST, doc=doc), cwd, model=JUDGE_MODEL)
    match = re.search(r"\{.*?\}", out, re.S)
    try:
        return out, json.loads(match.group()) if match else None
    except ValueError:
        return out, None


def assert_rate(passes: int, total: int, minimum_fraction: float, details: list[str]) -> None:
    needed = int(total * minimum_fraction)
    assert passes >= needed, f"{passes}/{total} passed (need {needed}):\n" + "\n".join(details)

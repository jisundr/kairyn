"""Helpers that drive real `claude` sessions. Used by the promptfoo provider and judge."""
import hashlib
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from helpers import PLUGIN, ROOT

MODEL = os.environ.get("KAIRYN_MODEL")
JUDGE_MODEL = os.environ.get("KAIRYN_JUDGE_MODEL", MODEL)

REQUEST = "Add a --dry-run flag to the CLI that prints what would change without writing files."

# The wrapper (evals/run.py) sets this per run; evidence for every run is saved under it.
RESULTS = Path(os.environ.get("KAIRYN_RESULTS_DIR", ROOT / "evals" / "results" / "adhoc"))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
    tasks = [p for p in (repo / "docs" / "tasks").iterdir() if p.is_dir()] if (repo / "docs" / "tasks").is_dir() else []
    return {"task": tasks[0] if len(tasks) == 1 else None, "start": start, "end": end}

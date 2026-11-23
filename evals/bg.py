"""Run evals detached from the agent that starts them, and wait for them in bounded steps.

    uv run python evals/bg.py start [--runs N] <run.py names and flags>   # STARTED pid=<pid>
    uv run python evals/bg.py wait [--timeout SECONDS]                    # DONE <run-id> | RUNNING <s>s | DIED ...

start launches evals/run.py in its own session (it survives the agent's Bash being killed),
logs to evals/results/last-run.log and records the pid and the result folders that existed.
wait blocks until the log holds `== eval summary ==` (DONE, with the new run id, or `skipped`
when no folder was made), the process ends without it (DIED, with the log tail), or the
timeout passes (RUNNING). Keep the timeout under the 10-minute foreground Bash limit and call
it again on RUNNING. Anyone can call wait later: the run does not depend on the caller.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SUMMARY = "== eval summary =="
LOG = "evals/results/last-run.log"
STATE = "evals/results/last-run.json"


def _results(root: Path) -> set[str]:
    d = root / "evals" / "results"
    return {p.name for p in d.iterdir() if p.is_dir()} if d.is_dir() else set()


def start(root: Path, cmd: list[str], env: dict | None = None) -> int:
    (root / "evals" / "results").mkdir(parents=True, exist_ok=True)
    before = sorted(_results(root))
    with (root / LOG).open("w") as log:
        proc = subprocess.Popen(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                env={**os.environ, **(env or {})}, start_new_session=True)
    (root / STATE).write_text(json.dumps({"pid": proc.pid, "before": before}))
    return proc.pid


def _alive(pid: int) -> bool:
    try:
        done, _ = os.waitpid(pid, os.WNOHANG)   # reaps our own child; raises for a process we did not start
        return done == 0
    except ChildProcessError:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False


def wait(root: Path, timeout: float = 540, poll: float = 5) -> str:
    state = json.loads((root / STATE).read_text())
    log, began = root / LOG, time.monotonic()
    while True:
        text = log.read_text(errors="ignore") if log.is_file() else ""
        if SUMMARY in text:
            new = sorted(_results(root) - set(state["before"]))
            return f"DONE {new[-1]}" if new else "DONE skipped"
        if not _alive(state["pid"]):
            text = log.read_text(errors="ignore") if log.is_file() else ""
            if SUMMARY in text:
                continue
            tail = "\n".join(text.strip().splitlines()[-15:])
            return f"DIED (no summary line). Log tail:\n{tail}"
        if time.monotonic() - began >= timeout:
            return f"RUNNING {int(time.monotonic() - began)}s"
        time.sleep(poll)


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if argv[:1] == ["start"]:
        args, env = argv[1:], {}
        if "--runs" in args:
            i = args.index("--runs")
            env["KAIRYN_EVAL_RUNS"] = args[i + 1]
            args = args[:i] + args[i + 2:]
        pid = start(root, [sys.executable, "evals/run.py", *args], env)
        print(f"STARTED pid={pid} log={LOG}")
        return 0
    if argv[:1] == ["wait"]:
        timeout = float(argv[argv.index("--timeout") + 1]) if "--timeout" in argv else 540
        out = wait(root, timeout)
        print(out)
        return 1 if out.startswith("DIED") else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

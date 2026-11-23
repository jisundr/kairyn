#!/usr/bin/env python3
"""KAIRYN_CLAUDE for evals of the AFK stages: runs the real `claude` and keeps what afk.py does not.

afk.py asks for `--output-format json`. This wrapper asks for stream-json instead, saves the session
transcript as AFK_EVAL_DIR/session-<n>.jsonl (with the prompt in session-<n>.prompt.txt), appends the
cost to AFK_EVAL_DIR/cost.jsonl, and prints the final result event, which is the same JSON object
afk.py would get. KAIRYN_MODEL, when set, replaces the model afk.py chose.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    if "--output-format" in args:
        args[args.index("--output-format") + 1] = "stream-json"
        args.append("--verbose")
    model = os.environ.get("KAIRYN_MODEL")
    if model and "--model" in args:
        args[args.index("--model") + 1] = model
    out = Path(os.environ["AFK_EVAL_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    n = len(list(out.glob("session-*.jsonl"))) + 1
    if "-p" in args:
        (out / f"session-{n}.prompt.txt").write_text(args[args.index("-p") + 1])
    proc = subprocess.run(["claude", *args], capture_output=True, text=True)
    (out / f"session-{n}.jsonl").write_text(proc.stdout)
    result = {}
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            result = event
    cost = result.get("total_cost_usd")
    if isinstance(cost, (int, float)):
        with (out / "cost.jsonl").open("a") as f:
            f.write(json.dumps({"role": "afk", "usd": float(cost)}) + "\n")
    print(json.dumps(result) if result else proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

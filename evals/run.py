"""Run the promptfoo evals that need running, gate on per-metric pass rates, record passes.

    uv run python evals/run.py                  # only evals whose `# depends:` files changed
    uv run python evals/run.py init --all-evals # named evals, ignoring the last-pass record

Each evals/promptfoo/<name>.yaml starts with a `# depends:` header (see selector.py) and gives
every test `metadata.min_pass_rate: {metric: fraction}`. promptfoo repeats each test
KAIRYN_EVAL_RUNS times; this script turns the results into pass rates and a summary.md.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from selector import deps_hash, load_record, needs_run, parse_depends, record_pass, save_record  # noqa: E402

PROMPTFOO = "promptfoo@0.125.1"
DEFAULT_RUNS = 10
# Parallel claude sessions. promptfoo starts one Python worker process per slot and times each
# call from when its worker picks it up, so queued runs do not time out and module state is not shared.
DEFAULT_CONCURRENCY = 4
CONFIGS = HERE / "promptfoo"
PASSED_RECORD = HERE / "results" / "passed.json"


def metric_outcomes(data: dict) -> dict:
    """{(test description, metric): {"passes": n, "total": n, "min": fraction, "reasons": [...]}}"""
    out: dict = {}
    for r in data["results"]["results"]:
        case = r.get("testCase", {})
        name = case.get("description", "test")
        components = (r.get("gradingResult") or {}).get("componentResults") or []
        by_metric = {c.get("assertion", {}).get("metric"): c for c in components}
        for metric, minimum in (case.get("metadata") or {}).get("min_pass_rate", {}).items():
            slot = out.setdefault((name, metric), {"passes": 0, "total": 0, "min": minimum, "reasons": []})
            slot["total"] += 1
            comp = by_metric.get(metric)
            if comp is not None and comp.get("pass"):
                slot["passes"] += 1
            else:
                slot["reasons"].append((comp or {}).get("reason") or r.get("error") or "no result")
    return out


def gate(outcomes: dict) -> list[str]:
    """Summary lines, one per metric; a metric fails when passes < floor(total * min), as before."""
    lines = []
    for (name, metric), o in outcomes.items():
        needed = math.floor(o["total"] * o["min"] + 1e-9)
        ok = o["passes"] >= needed
        lines.append(f"{'PASS' if ok else 'FAIL'}  {metric:<18}{o['passes']}/{o['total']} (need {needed}, {o['min']:.0%})  [{name}]")
        if not ok:
            lines += [f"      - {reason}" for reason in o["reasons"][:5]]
    return lines


def score_gate(results_dir: Path, scenario: str, total: int, gate_cfg: dict) -> list[str]:
    """Judge-score gate from the judge.json files assertions save per run: overall mean, floor, per-criterion means."""
    scores = [json.loads(f.read_text()) for f in sorted((results_dir / scenario).glob("*/judge.json"))]
    values = [v for s in scores for v in s.values()]
    need = math.floor(total * gate_cfg["min_gradable"] + 1e-9)
    problems = []
    if len(scores) < need:
        problems.append(f"only {len(scores)}/{total} runs gradable (need {need})")
    if values and min(values) < gate_cfg["floor"]:
        problems.append(f"a score of {min(values):g} is below {gate_cfg['floor']}")
    mean = sum(values) / len(values) if values else 0
    if mean < gate_cfg["mean"]:
        problems.append(f"mean {mean:.2f} < {gate_cfg['mean']}")
    for key, minimum in gate_cfg.get("criteria", {}).items():   # a weak criterion must not hide in the overall mean
        crit = [s[key] for s in scores if key in s]
        crit_mean = sum(crit) / len(crit) if crit else 0
        if crit_mean < minimum:
            problems.append(f"{key} mean {crit_mean:.2f} < {minimum}")
    detail = ", ".join(f"{k} {sum(s[k] for s in scores) / len(scores):.1f}" for k in scores[0]) if scores else "no scores"
    status = "FAIL" if problems else "PASS"
    return [f"{status}  quality           mean {mean:.1f} (need {gate_cfg['mean']}), min {min(values, default=0):g} (need {gate_cfg['floor']}); {detail}"] \
        + [f"      - {p}" for p in problems]


def score_gates(data: dict) -> list[tuple[str, int, dict]]:
    """(scenario, runs of that test, gate config) for each test that declares a score_gate."""
    gates: dict = {}
    for r in data["results"]["results"]:
        case = r.get("testCase", {})
        sg = (case.get("metadata") or {}).get("score_gate")
        if sg:
            scenario = case["vars"]["scenario"]
            gates[scenario] = (scenario, gates.get(scenario, (None, 0))[1] + 1, sg)
    return list(gates.values())


def cost_lines(results_dir: Path) -> list[str]:
    """Cost per scenario and in total, from the cost.jsonl files each run leaves (runner.record_cost)."""
    lines, total = [], 0.0
    for scenario in sorted(p for p in results_dir.glob("*") if p.is_dir()):
        runs = [f for f in sorted(scenario.glob("*/cost.jsonl"))]
        if not runs:
            continue
        rows = [json.loads(line) for f in runs for line in f.read_text().splitlines() if line.strip()]
        usd = sum(r["usd"] for r in rows)
        judge = sum(r["usd"] for r in rows if r["role"] == "judge")
        total += usd
        lines.append(f"cost  {scenario.name}: ${usd:.2f} over {len(runs)} run{'s' if len(runs) != 1 else ''} (judge ${judge:.2f})")
    return lines + [f"cost  total: ${total:.2f}"] if lines else []


def concurrency(flag, env) -> int:
    """--concurrency, else KAIRYN_EVAL_CONCURRENCY, else DEFAULT_CONCURRENCY; never below 1."""
    value = flag if flag is not None else int(env.get("KAIRYN_EVAL_CONCURRENCY", DEFAULT_CONCURRENCY))
    return max(1, value)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="eval names (init, check, requirements); default: all")
    ap.add_argument("--all-evals", action="store_true", help="ignore the unchanged-since-last-pass record")
    ap.add_argument("--concurrency", type=int, help=f"parallel claude sessions (default {DEFAULT_CONCURRENCY})")
    args = ap.parse_args(argv)

    runs = int(os.environ.get("KAIRYN_EVAL_RUNS", DEFAULT_RUNS))
    jobs = concurrency(args.concurrency, os.environ)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_dir = HERE / "results" / run_id
    record = load_record(PASSED_RECORD)
    configs = sorted(CONFIGS.glob("*.yaml"))
    wanted = [c for c in configs if not args.names or c.stem in args.names]
    unknown = set(args.names) - {c.stem for c in configs}
    if unknown:
        print(f"unknown eval(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    summary, failed = [], False
    for cfg in wanted:
        name = cfg.stem
        current = deps_hash(ROOT, parse_depends(cfg.read_text()))
        if not needs_run(name, current, record, args.all_evals):
            summary.append(f"{name}: skipped (dependencies unchanged since last pass)")
            continue
        results_dir.mkdir(parents=True, exist_ok=True)
        out_json = results_dir / f"{name}.json"
        env = {**os.environ, "KAIRYN_RESULTS_DIR": str(results_dir), "PROMPTFOO_PYTHON": sys.executable,
               "PROMPTFOO_DISABLE_TELEMETRY": "1", "PROMPTFOO_DISABLE_UPDATE": "1"}
        # promptfoo exits non-zero when any single run fails; the pass-rate gate below decides instead.
        subprocess.run(["npx", "--yes", PROMPTFOO, "eval", "-c", str(cfg), "--repeat", str(runs), "--no-cache",
                        "--no-progress-bar", "-j", str(jobs), "-o", str(out_json)], env=env, cwd=HERE)
        if not out_json.exists():
            summary.append(f"{name}: FAIL promptfoo produced no results")
            failed = True
            continue
        data = json.loads(out_json.read_text())
        lines = gate(metric_outcomes(data))
        for scenario, total, sg in score_gates(data):
            lines += score_gate(results_dir, scenario, total, sg)
        summary += [f"{name}: {line}" if not line.startswith("      ") else line for line in lines]
        if any(line.startswith("FAIL") for line in lines):
            failed = True
        elif runs >= DEFAULT_RUNS:   # a smoke run with fewer runs must not vouch for the eval
            record = record_pass(record, name, current)
            save_record(PASSED_RECORD, record)

    if results_dir.exists():
        summary += cost_lines(results_dir)
    print("\n== eval summary ==\n" + "\n".join(summary))
    if results_dir.exists():
        (results_dir / "summary.md").write_text("\n".join(f"- {s}" for s in summary) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

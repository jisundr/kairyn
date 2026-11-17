import json

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from checks import TS_FORMAT, structural_problems
from helpers import make_good_repo
from runner import RUNS, assert_rate, judge, new_repo, run_requirements, save_text, save_tree, summarize

scenarios("features/requirements.feature")


@pytest.fixture(scope="module")
def requirements_runs(tmp_path_factory):
    """The stage is slow, so run it once; both scenarios grade the same runs."""
    runs = []
    for i in range(RUNS):
        repo = make_good_repo(new_repo(tmp_path_factory.mktemp(f"req-{i}"), "repo"))
        run = run_requirements(repo)
        if run["task"] is not None:
            save_tree(f"requirements/run-{i:02d}/{run['task'].name}", run["task"])
        save_text(f"requirements/run-{i:02d}/window.txt",
                  f"{run['start']:{TS_FORMAT}} .. {run['end']:{TS_FORMAT}}\n")
        runs.append(run)
    return runs


@given("initialized repos")
def _initialized():
    """Each run starts from a correct init layout (built inside the runs fixture)."""


@given("the requirements stage has run in each for a small CLI feature request")
def _ran(requirements_runs):
    assert len(requirements_runs) == RUNS


@then(parsers.parse("at least {pct:d}% of runs leave a valid task folder, STATE.md and REQUIREMENTS.md"))
def _structure(requirements_runs, pct):
    passes, details = 0, []
    for i, run in enumerate(requirements_runs):
        problems = structural_problems(run)
        save_text(f"requirements/run-{i:02d}/problems.txt", "\n".join(problems) or "none")
        if problems:
            details.append(f"run {i}: {'; '.join(problems)}")
        else:
            passes += 1
    summarize("requirements", f"well-formed        {passes}/{len(requirements_runs)} (need {pct}%)")
    assert_rate(passes, len(requirements_runs), pct / 100, details)


@then(parsers.parse("the judge scores average at least {mean:d} with none below {floor:d}"))
def _quality(requirements_runs, tmp_path, mean, floor):
    scores = []
    for i, run in enumerate(requirements_runs):
        task = run["task"]
        if task is None or not (task / "REQUIREMENTS.md").exists():
            continue
        out, parsed = judge((task / "REQUIREMENTS.md").read_text(), tmp_path)
        save_text(f"judge/run-{i:02d}.txt", out)
        if parsed:
            scores.append(parsed)
    save_text("judge/scores.json", json.dumps(scores, indent=2))
    values = [v for s in scores for v in s.values()]
    if values:
        per = {k: sum(s[k] for s in scores) / len(scores) for k in scores[0]}
        detail = ", ".join(f"{k} {v:.1f}" for k, v in per.items())
        summarize("requirements", f"quality            mean {sum(values) / len(values):.1f} (need {mean}), min {min(values)} (need {floor}); {detail}")
    assert len(scores) >= int(RUNS * 0.9), f"only {len(scores)} runs produced a gradable document"
    assert min(values) >= floor, f"a criterion scored below {floor}: {scores}"
    avg = sum(values) / len(values)
    assert avg >= mean, f"mean score {avg:.2f} < {mean}: {scores}"

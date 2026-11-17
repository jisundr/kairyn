import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from helpers import make_good_repo
from runner import MODEL, RUNS, assert_rate, claude, new_repo, save_text, summarize

scenarios("features/check.feature")

BROKEN_DOC = ".harness/workflows/running-stages.md"


@pytest.fixture
def ctx():
    return {}


@given("initialized repos where one workflow doc has lost its header")
def _broken(ctx, tmp_path):
    ctx["repos"] = []
    for i in range(RUNS):
        repo = make_good_repo(new_repo(tmp_path, f"check-{i}"))
        (repo / BROKEN_DOC).write_text("# Running stages\n\nNo header here.\n")
        ctx["repos"].append(repo)


@when("/kairyn:check runs once in each")
def _run_check(ctx):
    ctx["replies"] = [claude("/kairyn:check", repo, plugin=True, model=MODEL) for repo in ctx["repos"]]


@then(parsers.parse("at least {pct:d}% of the replies name the broken doc"))
def _named(ctx, pct):
    passes, details = 0, []
    for i, reply in enumerate(ctx["replies"]):
        save_text(f"check/run-{i:02d}.txt", reply)
        if "running-stages" in reply:
            passes += 1
        else:
            details.append(f"run {i}: reply did not name running-stages.md")
    summarize("check", f"names broken doc  {passes}/{len(ctx['replies'])} (need {pct}%)")
    assert_rate(passes, len(ctx["replies"]), pct / 100, details)

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from helpers import make_good_repo, run_verify
from runner import MODEL, RUNS, assert_rate, claude, new_repo, save_text, summarize, tree_hash

scenarios("features/init.feature")


@pytest.fixture
def ctx():
    return {}


@given("fresh git repos")
def _fresh(ctx, tmp_path):
    ctx["repos"] = [new_repo(tmp_path, f"init-{i}") for i in range(RUNS)]


@given("initialized repos with a user-edited learnings file")
def _initialized(ctx, tmp_path):
    ctx["repos"] = []
    for i in range(RUNS):
        repo = make_good_repo(new_repo(tmp_path, f"idem-{i}"))
        (repo / ".kairyn" / "learnings.md").write_text("# Learnings\n\nuser note: keep me\n")
        ctx["repos"].append(repo)
    ctx["before"] = [tree_hash(r / ".kairyn") for r in ctx["repos"]]


@when("/kairyn:init runs once in each")
def _run_init(ctx):
    for repo in ctx["repos"]:
        claude("/kairyn:init", repo, plugin=True, model=MODEL)


@then(parsers.parse("at least {pct:d}% of the repos pass verify-init"))
def _verified(ctx, pct):
    passes, details = 0, []
    for i, repo in enumerate(ctx["repos"]):
        result = run_verify(repo)
        save_text(f"init-reliability/run-{i:02d}.txt", f"exit={result.returncode}\n{result.stdout}")
        if result.returncode == 0:
            passes += 1
        else:
            details.append(f"run {i}: {result.stdout.strip()}")
    summarize("init", f"verified layout   {passes}/{len(ctx['repos'])} (need {pct}%)")
    assert_rate(passes, len(ctx["repos"]), pct / 100, details)


@then("every .kairyn tree is unchanged")
def _unchanged(ctx):
    changed = [i for i, r in enumerate(ctx["repos"]) if tree_hash(r / ".kairyn") != ctx["before"][i]]
    summarize("init", f"never overwrites  {len(ctx['repos']) - len(changed)}/{len(ctx['repos'])} unchanged (need all)")
    assert not changed, f"runs {changed} changed .kairyn/ (overwriting user edits is the worst failure)"

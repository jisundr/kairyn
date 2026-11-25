"""Pure checks for the close stage evidence (evals/checks.py)."""
from checks import close_problems

TASK = "2026-01-07-history-store"
ADR = f"# 1. Store history in SQLite\n\nDate: 2026-01-07\n\n## Status\nAccepted\n\n## Context\nTask {TASK}.\n\n## Decision\nSQLite.\n\n## Consequences\nOne file.\n"


def evidence(**kw):
    e = {"task": TASK, "task_exists": False, "changelog": f"# Changelog\n\n## Unreleased\n\n- Stores history in SQLite. ({TASK})\n",
         "adrs": {"0001-store-history-in-sqlite.md": ADR}, "backlog_left": ["2-parked.md", "README.md"]}
    return {**e, **kw}


def test_good_close_passes():
    assert close_problems(evidence(), expect_adr=True, keyword="SQLite") == []
    assert close_problems(evidence(adrs={}), expect_adr=False) == []


def test_each_failure_is_named():
    assert "task folder still exists" in close_problems(evidence(task_exists=True), True)
    assert any("changelog" in p for p in close_problems(evidence(changelog="# Changelog\n\n## 0.1.0\n\n- x (t)\n"), True))
    assert any("committed" in p for p in close_problems(evidence(backlog_left=["1-linked.md", "2-parked.md"]), True))
    assert any("parked" in p for p in close_problems(evidence(backlog_left=[]), True))
    assert any("no ADR" in p for p in close_problems(evidence(adrs={}), True))
    assert any("no load-bearing" in p for p in close_problems(evidence(), False))
    assert any("Consequences" in p for p in close_problems(evidence(adrs={"0001-x.md": ADR.split("## Consequences")[0]}), True))
    assert any("SQLite" in p for p in close_problems(evidence(adrs={"0001-x.md": ADR.replace("SQLite", "a DB")}), True, "SQLite"))

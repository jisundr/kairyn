"""RETRO.md checks: one action per learning, homes that exist, nothing changed before approval, actions applied after."""
from datetime import datetime, timezone

from checks import (learning_entries, retro_applied_problems, retro_proposal_problems, retro_rows,
                    retro_scope_problems)

LEARNINGS = """# Learnings

- 2026-01-03 [requirements] Amounts are in cents; divide by 100.
- 2026-01-03 [design] Timestamps come from `date`.
- 2026-01-04 [design] The parser crashed on an empty line.
- 2026-01-06 [design] One slow read on a 50 MB file.
"""
EXPECTED = {"L1": {"move"}, "L2": {"drop"}, "L3": {"backlog"}, "L4": {"keep", "backlog"}}
HOMES = {"L1": "docs/report.md"}

PROPOSAL = """---
task: 2026-01-10-retro
stage: retro
summary: "x"
---

| Entry | Action | Home or path | Text or reason |
|---|---|---|---|
| L1 | move | `docs/report.md` | Amounts are in cents. |
| L2 | drop | `CLAUDE.md` | Already a rule there. |
| L3 | backlog | `tests/` | A test catches it. Over by 12 tokens. |
| L4 | keep | | One case, no pattern yet. |

Approval: pending
"""


def repo(tmp_path):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "report.md").write_text("# Report\n")
    (tmp_path / "CLAUDE.md").write_text("Timestamps come from `date`.\n")
    return tmp_path


def test_rows_parse_actions_in_lower_case():
    rows = retro_rows(PROPOSAL.replace("| move |", "| **Move** |"))
    assert rows["L1"][0] == "move" and rows["L4"] == ("keep", "", "One case, no pattern yet.")


def test_good_proposal_passes(tmp_path):
    assert retro_proposal_problems(PROPOSAL, EXPECTED, HOMES, repo(tmp_path), overflow=("L3",)) == []


def test_missing_and_extra_rows(tmp_path):
    text = PROPOSAL.replace("| L4 | keep | | One case, no pattern yet. |", "| L9 | keep | | x |")
    problems = retro_proposal_problems(text, EXPECTED, HOMES, repo(tmp_path))
    assert "no row for L4" in problems and "row L9 is not a learning" in problems


def test_wrong_action_and_wrong_home(tmp_path):
    text = PROPOSAL.replace("| L1 | move | `docs/report.md` |", "| L1 | move | `docs/other.md` |").replace(
        "| L2 | drop |", "| L2 | keep |")
    problems = retro_proposal_problems(text, EXPECTED, HOMES, repo(tmp_path))
    assert any(p.startswith("L1: move home") for p in problems)
    assert any(p.startswith("L1:") and "does not exist" in p for p in problems)
    assert "L2: keep, expected drop" in problems


def test_drop_needs_a_path_or_stale(tmp_path):
    text = PROPOSAL.replace("| L2 | drop | `CLAUDE.md` | Already a rule there. |", "| L2 | drop | | |")
    assert "L2: drop names no existing path and no reason" in retro_proposal_problems(text, EXPECTED, HOMES, repo(tmp_path))
    stale = PROPOSAL.replace("| L2 | drop | `CLAUDE.md` | Already a rule there. |", "| L2 | drop | | Seen once. It holds no rule. |")
    assert retro_proposal_problems(stale, EXPECTED, HOMES, repo(tmp_path)) == []


def test_keep_needs_a_reason(tmp_path):
    text = PROPOSAL.replace("| L4 | keep | | One case, no pattern yet. |", "| L4 | keep | | |")
    assert "L4: keep gives no reason" in retro_proposal_problems(text, EXPECTED, HOMES, repo(tmp_path))


def test_full_home_must_name_the_overflow(tmp_path):
    text = PROPOSAL.replace(" Over by 12 tokens.", "")
    assert "L3: backlog for a full home does not name the overflow" in retro_proposal_problems(
        text, EXPECTED, HOMES, repo(tmp_path), overflow=("L3",))


def test_proposal_must_wait_for_approval(tmp_path):
    text = PROPOSAL.replace("Approval: pending", 'Approval: Eval User, 2026-01-10T10:00:00Z, "Approved"')
    assert retro_proposal_problems(text, EXPECTED, HOMES, repo(tmp_path))


def test_scope_allows_only_the_retro_folder():
    assert retro_scope_problems(["docs/tasks/2026-01-10-retro/RETRO.md", "docs/tasks/2026-01-10-retro/STATE.md"]) == []
    assert retro_scope_problems([".kairyn/learnings.md"]) == ["changed before approval: .kairyn/learnings.md"]


T0, T1 = datetime(2026, 1, 10, 9, tzinfo=timezone.utc), datetime(2026, 1, 10, 11, tzinfo=timezone.utc)
APPROVED = PROPOSAL.replace("Approval: pending", 'Approval: Eval User, 2026-01-10T10:00:00Z, "Approved."')
ENTRIES = learning_entries(LEARNINGS)


def applied(**over):
    run = {"entries": ENTRIES, "retro": APPROVED, "learnings": "# Learnings\n\n" + ENTRIES[3] + "\n",
           "backlog": {"1-parser.md": "---\nstatus: inbox\n---\n\n> The parser crashed on an empty line.\n"},
           "homes_before": {"docs/report.md": "# Report\n"},
           "homes_after": {"docs/report.md": "# Report\n\nAmounts are in cents.\n"},
           "budgets_before": "b", "budgets_after": "b", "state": "---\nstatus: done\n---\n",
           "approver": "Eval User", "words": "Approved", "start": T0, "end": T1}
    return retro_applied_problems({**run, **over})


def test_applied_run_passes():
    assert applied() == []


def test_applied_finds_each_failure():
    problems = applied(learnings=LEARNINGS, backlog={}, homes_after={"docs/report.md": "# Report\n"},
                       budgets_after="raised", state="---\nstatus: blocked\n---\n")
    assert "L1: move entry still in learnings.md" in problems
    assert "L3: no inbox backlog idea quotes the learning" in problems
    assert "L1: home docs/report.md unchanged" in problems
    assert "budgets.yml changed" in problems
    assert any(p.startswith("retro status") for p in problems)


def test_kept_entry_must_keep_its_text():
    assert "L4: kept entry changed or removed" in applied(learnings="# Learnings\n\n- 2026-01-06 [design] Reworded.\n")


def test_applied_needs_the_approval_line():
    assert applied(retro=PROPOSAL)

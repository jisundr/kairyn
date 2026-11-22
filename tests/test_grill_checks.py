"""Pure checks for the grill stage (evals/checks.py)."""
from datetime import datetime, timedelta, timezone

from checks import (TS_FORMAT, concept_use_problems, decision_labels, grill_problems, grill_reply_problems, section_items, state_fields)

TASK = "2026-11-22-report-cache"
NOW = datetime.now(timezone.utc).replace(microsecond=0)

GOOD_DOC = f"""---
task: {TASK}
stage: grill
summary: "The report reparses a large CSV each run. Goal: repeat runs under one second."
---

# Concept

## Concept
The report reads the nightly CSV again on each run. Repeat runs on the same file must be fast.

## Decisions
- D1: The problem is repeat runs on the same file. (user accepted)
- D2: A new export makes old results invalid. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| repeat run | A run on a CSV that did not change since the last run. |

## Open branches
- Where stored results live.
"""


def _state(ts: str, grill="done", stage="requirements", status="in-progress") -> str:
    return f"""---
task: {TASK}
title: Report cache
stage: {stage}
status: {status}
stages:
  requirements: pending
  grill: {grill}
created: {ts}
updated: {ts}
---

# Log

{ts} [grill] Task created. Add a cache to the report.
{ts} [grill] User stopped the interview. D1, D2 recorded, 1 open branch.
"""


def _run(tmp_path, doc=GOOD_DOC, **state):
    task = tmp_path / TASK
    task.mkdir()
    (task / "STATE.md").write_text(_state(NOW.strftime(TS_FORMAT), **state))
    if doc is not None:
        (task / "CONCEPT.md").write_text(doc)
    return {"task": task, "start": NOW - timedelta(seconds=30), "end": NOW + timedelta(seconds=30)}


def test_good_output_has_no_problems(tmp_path):
    assert grill_problems(_run(tmp_path)) == []


def test_missing_concept(tmp_path):
    assert any("CONCEPT.md missing" in p for p in grill_problems(_run(tmp_path, doc=None)))


def test_grill_not_done(tmp_path):
    problems = grill_problems(_run(tmp_path, grill="in-progress", stage="grill", status="blocked"))
    assert any("stages.grill" in p for p in problems)
    assert any("expected requirements in-progress" in p for p in problems)


def test_missing_section(tmp_path):
    problems = grill_problems(_run(tmp_path, doc=GOOD_DOC.replace("## Terms", "## Glossary")))
    assert any("terms" in p for p in problems)


def test_stopped_without_open_branches(tmp_path):
    doc = GOOD_DOC.replace("- Where stored results live.", "None.")
    run = _run(tmp_path, doc=doc)
    assert any("open branch" in p for p in grill_problems(run))
    assert grill_problems(run, stopped=False) == []


def test_decision_labels_only_in_decisions_section():
    assert decision_labels(GOOD_DOC) == {"D1", "D2"}
    assert decision_labels("## Concept\nSee D1.\n\n## Decisions\nNone yet.\n") == set()


def test_section_items_skip_table_header_and_none():
    assert section_items(GOOD_DOC, "terms") == ["repeat run | A run on a CSV that did not change since the last run."]
    assert section_items("## Open branches\n- None\n", "open branches") == []
    assert section_items(GOOD_DOC, "open branches") == ["Where stored results live."]


def test_reply_with_one_question_and_recommendation():
    reply = ("The README says the CSV is exported nightly.\n\n**Q1:** What is slow: the first run, or repeat runs?\n"
             "**Recommended:** Repeat runs on the same file, because the export changes only once a day.")
    assert grill_reply_problems(reply) == []


def test_reply_with_two_questions():
    reply = "**Q1:** What is slow?\n**Q2:** Who runs it?\n**Recommended:** Repeat runs."
    assert any("2 question markers" in p for p in grill_reply_problems(reply))


def test_reply_without_recommendation():
    assert grill_reply_problems("**Question:** What is slow?") == ["no recommended answer"]


def test_reply_with_question_batch_in_prose():
    reply = "**Q1:** What is slow? Is it the parse? Or the print?\n**Recommended:** The parse."
    assert any("question marks" in p for p in grill_reply_problems(reply))


def test_state_fields():
    assert state_fields(_state("2026-11-22T09:00:00Z", grill="in-progress", stage="grill", status="blocked")) == {
        "stage": "grill", "status": "blocked", "stages": {"requirements": "pending", "grill": "in-progress"}}
    assert state_fields("no front matter") == {}


def test_concept_use(tmp_path):
    (tmp_path / "REQUIREMENTS.md").write_text("- [ ] A repeat run takes under 1 second. (D2)\n- [ ] Scope (D1, D3)\n")
    assert concept_use_problems(tmp_path, ("D1", "D2", "D3"), "1 second") == []
    assert concept_use_problems(tmp_path, ("D1", "D4"), "2 seconds") == ["D4 not cited", "decided value '2 seconds' missing"]
    assert concept_use_problems(tmp_path / "none", ("D1",), "x") == ["REQUIREMENTS.md missing in the grill task folder"]

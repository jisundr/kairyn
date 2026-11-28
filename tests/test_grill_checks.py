"""Pure checks for the grill stage (evals/checks.py)."""
from datetime import datetime, timedelta, timezone

from helpers import PLUGIN

from checks import (TS_FORMAT, concept_use_problems, decision_labels, finished_turn, grill_idea_problems, grill_problems,
                    grill_round_problems, handoff_problems, round_decision_problems, section_items, section_text, state_fields)

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


def _round(n, first=1, recommend=True):
    return "The README says the CSV is exported nightly.\n\n" + "".join(
        f"**Q{i}:** Question {i}?\n" + (f"**Recommended:** Answer {i}, because the repo says so.\n" if recommend else "")
        for i in range(first, first + n))


def test_round_with_one_to_three_questions():
    for n in (1, 2, 3):
        assert grill_round_problems(_round(n)) == []


def test_round_numbers_continue():
    assert grill_round_problems(_round(2, first=4)) == []


def test_round_with_no_question():
    assert any("0 questions" in p for p in grill_round_problems("I have no question."))


def test_round_with_four_questions():
    assert any("4 questions" in p for p in grill_round_problems(_round(4)))


def test_round_needs_a_recommendation_per_question():
    reply = _round(2) + "**Q3:** Question 3?\n"
    assert grill_round_problems(reply) == ["2 recommended answers for 3 questions"]
    assert "0 recommended answers for 1 questions" in grill_round_problems(_round(1, recommend=False))


def test_first_round_needs_two_questions():
    assert grill_round_problems(_round(1), min_questions=2) == ["1 questions, expected at least 2"]
    assert grill_round_problems(_round(2), min_questions=2) == []


def test_round_with_question_batch_in_prose():
    reply = "**Q1:** What is slow? Is it the parse? Or the print?\n**Recommended:** The parse."
    assert any("question marks" in p for p in grill_round_problems(reply))


def _concept(n):
    return "## Decisions\n" + "".join(f"- D{i}: decided. (user accepted)\n" for i in range(1, n + 1))


def test_round_decisions_one_per_accepted_question():
    turns = [{"reply": _round(3), "concept": _concept(0)}, {"reply": _round(2, first=4), "concept": _concept(3)},
             {"reply": _round(1, first=6), "concept": _concept(5)}]
    assert round_decision_problems(turns) == []


def test_round_decisions_missing_after_an_accepted_round():
    turns = [{"reply": _round(3), "concept": _concept(0)}, {"reply": _round(2, first=4), "concept": _concept(1)},
             {"reply": _round(1, first=6), "concept": _concept(2)}]
    assert round_decision_problems(turns) == ["answer 1: 1 new decisions for 3 questions",
                                              "answer 2: 1 new decisions for 2 questions"]


def test_round_decisions_need_three_turns():
    assert round_decision_problems([{"reply": _round(1), "concept": ""}]) == ["only 1 turns"]


def test_finished_turn_is_the_first_restatement_after_turn_0():
    asking = {"state": _state("2026-11-22T09:00:00Z", grill="in-progress", stage="grill", status="blocked")}
    restated = {"state": _state("2026-11-22T09:00:00Z", grill="done", stage="grill", status="blocked")}
    assert finished_turn([asking, asking, asking, restated]) is None
    assert finished_turn([asking, asking, restated, restated]) == 2
    assert finished_turn([asking, restated, restated]) == 1


def test_round_decisions_skip_the_restated_turn():
    turns = [{"reply": _round(3), "concept": _concept(0)}, {"reply": "Concept restated.", "concept": _concept(3)},
             {"reply": "Stopped.", "concept": _concept(3)}]
    assert round_decision_problems(turns) == []


def test_state_fields():
    assert state_fields(_state("2026-11-22T09:00:00Z", grill="in-progress", stage="grill", status="blocked")) == {
        "stage": "grill", "status": "blocked", "stages": {"requirements": "pending", "grill": "in-progress"}}
    assert state_fields("no front matter") == {}


def test_concept_use(tmp_path):
    (tmp_path / "REQUIREMENTS.md").write_text("- [ ] A repeat run takes under 1 second. (D2)\n- [ ] Scope (D1, D3)\n")
    assert concept_use_problems(tmp_path, ("D1", "D2", "D3"), "1 second") == []
    assert concept_use_problems(tmp_path, ("D1", "D4"), "2 seconds") == ["D4 not cited", "decided value '2 seconds' missing"]
    assert concept_use_problems(tmp_path / "none", ("D1",), "x") == ["REQUIREMENTS.md missing in the grill task folder"]


def test_handoff_names_the_command_and_folder(tmp_path):
    task = tmp_path / TASK
    task.mkdir()
    reply = f"Concept approved. Next, type `/kairyn:requirements docs/tasks/{TASK}/`."
    assert handoff_problems(reply, task, "requirements") == []
    assert handoff_problems("Concept approved. Run requirements next.", task, "requirements") == [
        "last message does not name /kairyn:requirements", f"last message does not name the task folder {TASK}"]


def test_handoff_fails_when_the_stage_ran_the_next_one(tmp_path):
    """A chained skill runs on the caller's model (ADR 0004), so the stage must not run the next stage itself."""
    task = tmp_path / TASK
    task.mkdir()
    (task / "REQUIREMENTS.md").write_text("# Requirements\n")
    reply = f"Type `/kairyn:requirements docs/tasks/{TASK}/`."
    assert handoff_problems(reply, task, "requirements") == [
        "REQUIREMENTS.md written: the stage ran requirements instead of handing off"]


# --- T4: grill starts from the idea that a committed task's STATE.md names ----------
IDEA = "docs/backlog/20261128013000-report-cache.md"


def _idea_run(**over):
    d = {"task": TASK, "tasks": [TASK], "idea_changed": False, "terms": ["nightly CSV", "repeat runs"],
         "reply": ("The idea asks to make repeat runs of the report fast; it reparses the nightly CSV each run.\n\n"
                   "**Q1:** What is slow: the parse, or the print?\n"
                   "**Recommended:** The parse, because the idea says the CSV is large.")}
    return {**d, **over}


def test_grill_stage_reads_the_linked_idea():
    inputs = section_text((PLUGIN / "stages" / "GRILL.md").read_text(), "inputs")
    assert "idea" in inputs and "STATE.md" in inputs, "GRILL.md Inputs does not name the idea file STATE.md names"


def test_grill_from_idea_good_run():
    assert grill_idea_problems(_idea_run()) == []


def test_grill_from_idea_made_a_new_task():
    problems = grill_idea_problems(_idea_run(tasks=[TASK, "2026-11-28-other"]))
    assert any("task folder" in p for p in problems)


def test_grill_from_idea_changed_the_idea():
    assert any("idea file changed" in p for p in grill_idea_problems(_idea_run(idea_changed=True)))


def test_grill_from_idea_ignores_the_idea():
    reply = "**Q1:** What do you want to change?\n**Recommended:** A cache, because it is common."
    assert any("idea" in p for p in grill_idea_problems(_idea_run(reply=reply)))


def test_grill_from_idea_still_follows_the_round_rules():
    reply = "Repeat runs reparse the nightly CSV.\n**Q1:** What is slow?\n**Q2:** Who runs it?"
    problems = grill_idea_problems(_idea_run(reply=reply))
    assert any("recommended" in p for p in problems)

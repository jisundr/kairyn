"""Playbook gaps in REQUIREMENTS.md: EARS requirements, non-functional needs, owners, approval."""
from datetime import datetime, timezone

from helpers import PLUGIN

from checks import (approval_problems, ears_problems, nfr_problems, owner_problems, requirements_idea_problems,
                    section_text, structural_problems, traceability_problems)

GOOD = """## Requirements
- R1: When the user passes `--dry-run`, the CLI shall print each file it would change. (request)
- R2: The CLI shall write no file in a dry run. (A1)

## Non-functional needs
- Accessibility: not applicable: CLI text output only.
- Performance: a dry run takes no longer than a real run. (A1)
- Security: not applicable: no new input.
- Observability: not applicable: no logs today.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | Writes go through one function. | user |
| K1 | risk | A plugin writes files directly. | design stage |
| K2 | dependency | The file walker lists every target. | build |

## Acceptance criteria
- [ ] A dry run lists the files. (R1)
- [ ] A dry run leaves the tree unchanged. (R2, A1)

Approval: pending
"""


def test_good_document_passes_every_check():
    assert ears_problems(GOOD) == []
    assert nfr_problems(GOOD) == []
    assert owner_problems(GOOD) == []
    assert traceability_problems(GOOD) == []


def test_missing_requirements_section():
    assert ears_problems("## Acceptance criteria\n- [ ] x (request)\n") == ["no ## Requirements section with R<n> items"]


def test_requirement_not_in_ears_form():
    text = GOOD.replace("The CLI shall write no file in a dry run.", "No files get written.")
    assert any("R2" in p and "EARS" in p for p in ears_problems(text))


def test_requirement_without_source():
    text = GOOD.replace("in a dry run. (A1)", "in a dry run.")
    assert any("R2" in p and "source" in p for p in ears_problems(text))


def test_requirement_without_criterion():
    text = GOOD.replace("(R2, A1)", "(A1)")
    assert any("R2" in p and "criterion" in p for p in ears_problems(text))


def test_criterion_citing_undefined_requirement():
    text = GOOD.replace("(R1)", "(R9)")
    assert any("R9" in p for p in traceability_problems(text))


def test_each_ears_shape_is_accepted():
    shapes = ["While offline, the app shall queue writes.", "If the disk is full, then the CLI shall stop.",
              "Where colour is on, the CLI shall colour paths."]
    for s in shapes:
        assert ears_problems(GOOD.replace("The CLI shall write no file in a dry run.", s[:-1])) == [], s


def test_missing_nfr_flagged():
    text = GOOD.replace("- Security: not applicable: no new input.\n", "")
    assert nfr_problems(text) == ["non-functional need missing: security"]


def test_empty_nfr_flagged():
    text = GOOD.replace("- Observability: not applicable: no logs today.", "- Observability:")
    assert nfr_problems(text) == ["non-functional need empty: observability"]


def test_stated_need_without_source_flagged():
    text = GOOD.replace("a real run. (A1)", "a real run.")
    assert nfr_problems(text) == ["non-functional need has no source: performance"]


def test_row_without_owner_flagged():
    text = GOOD.replace("| design stage |", "|  |")
    assert owner_problems(text) == ["K1 has no owner"]


def test_placeholder_owner_flagged():
    text = GOOD.replace("| build |", "| TBD |")
    assert owner_problems(text) == ["K2 has no owner"]


def test_assumption_outside_table_flagged():
    text = GOOD.replace("## Acceptance criteria", "- A2: Paths are relative.\n\n## Acceptance criteria")
    assert owner_problems(text) == ["A2 is not in the owner table"]


def test_no_owner_table():
    assert owner_problems("## Scope\nIn: x\n") == ["no assumptions, risks and dependencies table"]


T0 = datetime(2026, 11, 22, 10, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 11, 22, 10, 10, 0, tzinfo=timezone.utc)


def test_pending_approval():
    assert approval_problems(GOOD, approved=False) == []
    assert approval_problems(GOOD.replace("Approval: pending", ""), approved=False) == ["no 'Approval: pending' line"]


def test_self_approval_flagged():
    text = GOOD.replace("Approval: pending", 'Approval: Eval User, 2026-11-22T10:05:00Z, "Looks good"')
    assert approval_problems(text, approved=False) == ["approval line written without the user's approval"]


def test_recorded_approval():
    text = GOOD.replace("Approval: pending", 'Approval: Eval User, 2026-11-22T10:05:00Z, "Approved."')
    assert approval_problems(text, approved=True, name="Eval User", words="Approved", start=T0, end=T1) == []


def test_recorded_approval_wrong_fields():
    text = GOOD.replace("Approval: pending", 'Approval: Someone, 2026-11-22T00:00:00Z, "fine"')
    problems = approval_problems(text, approved=True, name="Eval User", words="Approved", start=T0, end=T1)
    assert len(problems) == 3, problems


def _task(tmp_path, status, approval="Approval: pending", stage="requirements"):
    task = tmp_path / "2026-11-22-dry-run"
    task.mkdir()
    (task / "STATE.md").write_text(f"""---
task: 2026-11-22-dry-run
title: Dry run
stage: {stage}
status: {status}
stages:
  requirements: done
created: 2026-11-22T10:01:00Z
updated: 2026-11-22T10:02:00Z
---

# Log

2026-11-22T10:01:00Z [requirements] Task created.
""")
    (task / "REQUIREMENTS.md").write_text(
        '---\ntask: 2026-11-22-dry-run\nstage: requirements\nsummary: "x"\n---\n\n## Problem statement\nx\n'
        "## Scope\nx\n## Open questions\nNone.\n" + GOOD.replace("Approval: pending", approval))
    return {"task": task, "start": T0, "end": T1}


def test_unapproved_run_must_end_blocked(tmp_path):
    assert structural_problems(_task(tmp_path, "blocked")) == []


def test_unapproved_run_marked_done_is_flagged(tmp_path):
    assert "stage 'requirements' status 'done', expected requirements blocked" in structural_problems(
        _task(tmp_path, "done"))


APPROVED = 'Approval: Eval User, 2026-11-22T10:05:00Z, "Approved"'


def test_approved_run_hands_off_to_design(tmp_path):
    run = _task(tmp_path, "in-progress", APPROVED, stage="design")
    assert structural_problems(run, approved=True) == []


def test_approved_run_marked_done_is_flagged(tmp_path):
    """Design follows requirements (D4), so an approved task is not done."""
    assert "stage 'requirements' status 'done', expected design in-progress" in structural_problems(
        _task(tmp_path, "done", APPROVED), approved=True)


# --- T4: requirements takes the idea that a committed task's STATE.md names as the request ---
IDEA_TASK = "2026-11-28-report-cache"
IDEA_DOC = """## Problem statement
The report reparses the nightly CSV on each run, so repeat runs are slow. (request)

## Requirements
- R1: When the CSV did not change, the report shall reuse the last parse. (request)
"""


def _idea_req(**over):
    d = {"task": IDEA_TASK, "tasks": [IDEA_TASK], "idea_changed": False, "requirements": IDEA_DOC,
         "terms": ["nightly CSV", "repeat runs"]}
    return {**d, **over}


def test_requirements_stage_reads_the_linked_idea():
    inputs = section_text((PLUGIN / "stages" / "REQUIREMENTS.md").read_text(), "inputs")
    assert "idea" in inputs and "STATE.md" in inputs, "REQUIREMENTS.md Inputs does not name the idea file STATE.md names"


def test_requirements_from_idea_good_run():
    assert requirements_idea_problems(_idea_req()) == []


def test_requirements_from_idea_missing_output():
    assert requirements_idea_problems(_idea_req(requirements=None)) == ["REQUIREMENTS.md missing in the committed task folder"]


def test_requirements_from_idea_made_a_new_task():
    problems = requirements_idea_problems(_idea_req(tasks=[IDEA_TASK, "2026-11-28-cache"]))
    assert any("task folder" in p for p in problems)


def test_requirements_from_idea_changed_the_idea():
    assert any("idea file changed" in p for p in requirements_idea_problems(_idea_req(idea_changed=True)))


def test_requirements_from_idea_problem_statement_drops_the_idea():
    doc = IDEA_DOC.replace("nightly CSV", "input file")
    assert requirements_idea_problems(_idea_req(requirements=doc)) == [
        "problem statement does not take 'nightly CSV' from the idea"]


def test_requirements_from_idea_term_only_outside_problem_statement():
    doc = IDEA_DOC.replace("so repeat runs are slow", "so it is slow") + "- R2: Repeat runs take under 1 second. (request)\n"
    assert requirements_idea_problems(_idea_req(requirements=doc)) == [
        "problem statement does not take 'repeat runs' from the idea"]

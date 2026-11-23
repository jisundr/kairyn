"""DESIGN.md checks: four sections, options with a smallest thing, a test plan for every criterion, grounded paths."""
from datetime import datetime, timezone

from checks import (chosen_option, design_run_problems, design_section_problems, design_test_plan_problems, grounded_problems, option_labels,
                    options_problems, rejected_option)

REQUIREMENTS = """## Acceptance criteria
- [ ] A dry run lists the files. (R1)
- [ ] A dry run leaves the tree unchanged. (R2)
"""

GOOD = """---
task: 2026-01-01-dry-run
stage: design
summary: "Add --dry-run through the one write function."
---

# Design: Dry run

## Approach
Option A. Route writes through `src/write.py` and skip them in a dry run.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | One flag in `src/write.py`. | Small. | A plugin writes directly. |
| B | A virtual file system. | Large. | New dependency. |

## Tasks
- T1: Add the flag to `src/cli.py`. Done: `--help` lists it.
- T2: Skip writes in `src/write.py`. Done: `tests/test_dry_run.py` (new) passes.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 lists the files | T1, T2 | `tests/test_dry_run.py` (new), list test |
| AC2 tree unchanged | T2 | `tests/test_dry_run.py` (new), hash test |

Approval: pending
"""


def repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "write.py").write_text("")
    (tmp_path / "src" / "cli.py").write_text("")
    return tmp_path


def test_good_design_passes_every_check(tmp_path):
    assert design_section_problems(GOOD) == []
    assert options_problems(GOOD) == []
    assert design_test_plan_problems(GOOD, REQUIREMENTS) == []
    assert grounded_problems(GOOD, repo(tmp_path)) == []


def test_missing_section():
    text = GOOD.replace("## Tasks", "## Steps")
    assert design_section_problems(text) == ["DESIGN.md missing section 'tasks'"]


def test_standards_impact_is_not_a_section():
    assert design_section_problems(GOOD + "\n## Standards impact\nNone.\n") == [
        "DESIGN.md has a section the stage does not write: 'standards impact'"]


def test_one_option_is_not_enough():
    text = GOOD.replace("| B | A virtual file system. | Large. | New dependency. |\n", "")
    assert options_problems(text) == ["1 option(s), expected at least 2"]


def test_no_smallest_thing_option():
    assert options_problems(GOOD.replace("A (smallest thing)", "A")) == ["no option is the smallest thing"]


def test_criterion_missing_from_test_plan():
    text = GOOD.replace("| AC2 tree unchanged | T2 | `tests/test_dry_run.py` (new), hash test |\n", "")
    assert design_test_plan_problems(text, REQUIREMENTS) == ["AC2 has no row in the test plan"]


def test_row_names_an_undefined_task():
    text = GOOD.replace("| AC2 tree unchanged | T2 |", "| AC2 tree unchanged | T9 |")
    assert design_test_plan_problems(text, REQUIREMENTS) == ["AC2 names no task from the Tasks section"]


def test_row_without_a_test():
    text = GOOD.replace("| T2 | `tests/test_dry_run.py` (new), hash test |", "| T2 | |")
    assert design_test_plan_problems(text, REQUIREMENTS) == ["AC2 names no test"]


def test_test_plan_for_requirements_without_criteria():
    assert design_test_plan_problems(GOOD, "## Acceptance criteria\n") == ["REQUIREMENTS.md has no acceptance criteria"]


def test_missing_path_without_new_mark(tmp_path):
    text = GOOD.replace("Add the flag to `src/cli.py`", "Add the flag to `src/main.py`")
    assert grounded_problems(text, repo(tmp_path)) == ["names a missing file: src/main.py"]


def test_new_mark_skips_the_path(tmp_path):
    assert grounded_problems(GOOD.replace("`src/cli.py`", "`src/main.py` (new)"), repo(tmp_path)) == []


def test_placeholders_globs_urls_and_line_refs_are_not_paths(tmp_path):
    text = GOOD + "\nSee `docs/tasks/<slug>/`, `src/*.py`, `https://x.org/a`, `src/write.py:12`, `/kairyn:design` and `src/`.\n"
    assert grounded_problems(text, repo(tmp_path)) == []


def test_option_labels_and_choice():
    assert option_labels(GOOD) == ["A", "B"]
    assert chosen_option(GOOD) == "A"
    assert rejected_option(GOOD) == "B"


def test_option_word_in_the_cell_is_read():
    text = GOOD.replace("| A (smallest thing) |", "| **Option A** (smallest thing) |").replace("Option A. Route", "Option B. Route")
    assert (chosen_option(text), rejected_option(text)) == ("B", "A")


def test_no_choice_in_approach():
    text = GOOD.replace("Option A. Route", "Route")
    assert chosen_option(text) is None and rejected_option(text) is None


T0, T1 = datetime(2026, 11, 23, 1, 0, tzinfo=timezone.utc), datetime(2026, 11, 23, 1, 10, tzinfo=timezone.utc)


def design_task(tmp_path, stage="design", status="blocked", design="done", doc=GOOD, log="2026-11-23T01:05:00Z"):
    task = tmp_path / "2026-01-01-dry-run"
    task.mkdir()
    (task / "STATE.md").write_text(f"""---
task: 2026-01-01-dry-run
title: Dry run
stage: {stage}
status: {status}
stages:
  requirements: done
  design: {design}
created: 2026-01-01T09:00:00Z
updated: {log}
---

# Log

2026-01-01T09:00:00Z [requirements] Task created.
{log} [design] Wrote DESIGN.md.
""")
    if doc is not None:
        (task / "DESIGN.md").write_text(doc)
    return {"task": task, "start": T0, "end": T1}


def test_design_run_waits_blocked(tmp_path):
    assert design_run_problems(design_task(tmp_path)) == []


def test_approved_design_run_ends_done(tmp_path):
    assert design_run_problems(design_task(tmp_path, status="done"), approved=True) == []


def test_design_run_not_blocked_is_flagged(tmp_path):
    assert design_run_problems(design_task(tmp_path, status="done")) == [
        "stage 'design' status 'done', expected design blocked"]


def test_design_run_without_design_md(tmp_path):
    assert design_run_problems(design_task(tmp_path, doc=None)) == ["DESIGN.md missing"]


def test_design_stage_not_marked_done(tmp_path):
    assert design_run_problems(design_task(tmp_path, design="pending")) == ["stages.design != done"]


def test_guessed_design_timestamp(tmp_path):
    problems = design_run_problems(design_task(tmp_path, log="2026-11-23T00:00:00Z"))
    assert any("placeholder-looking" in p for p in problems), problems


def test_path_marked_new_once_counts_everywhere(tmp_path):
    """A file created in T2 is named again in the test plan without the mark: still new, not missing."""
    root = repo(tmp_path)
    assert grounded_problems(GOOD.replace("hash test", "`tests/test_dry_run.py` hash test"), root) == []
    text = GOOD.replace("| AC1 lists the files | T1, T2 | `tests/test_dry_run.py` (new), list test |",
                        "| AC1 lists the files | T1, T2 | `tests/test_dry_run.py` list test |")
    assert grounded_problems(text, root) == []

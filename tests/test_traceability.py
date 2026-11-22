"""Every acceptance criterion names its source: the request or a labeled assumption."""
from checks import traceability_problems

ASSUMPTIONS = "## Assumptions\n- **A1** The report goes to stdout.\n| A2 | Global flag. |\n"


def test_tagged_criteria_pass():
    text = ASSUMPTIONS + "## Acceptance criteria\n- [ ] No file changes. (request)\n- [ ] Report on stdout. (A1, A2)\n"
    assert traceability_problems(text) == []


def test_untagged_criterion_flagged():
    text = ASSUMPTIONS + "## Acceptance criteria\n- [ ] No file changes. (request)\n- [ ] README documents the flag.\n"
    problems = traceability_problems(text)
    assert len(problems) == 1 and "README" in problems[0]


def test_reference_to_undefined_assumption_flagged():
    text = ASSUMPTIONS + "- [ ] Summary line at the end. (A7)\n"
    assert any("A7" in p for p in traceability_problems(text))


def test_reference_inside_criterion_does_not_define_it():
    text = "- [ ] First. (A3)\n- [ ] Second. (A3)\n"
    assert any("A3" in p for p in traceability_problems(text))


def test_numbered_bold_assumption_counts_as_defined():
    text = "1. **A1 — CLI location.** Not in the repo.\n- [ ] Flag works. (A1)\n"
    assert traceability_problems(text) == []


def test_no_criteria_is_a_problem():
    assert traceability_problems("# Requirements\n") == ["no acceptance criteria to trace"]


def test_backticked_assumption_label_counts_as_defined():
    text = "- `A1`: The flag is global.\n- [ ] Flag works. (A1)\n"
    assert traceability_problems(text) == []


def test_grill_decision_counts_as_source():
    text = ASSUMPTIONS + "- [ ] Repeat run under 1 second. (D2)\n- [ ] Report on stdout. (D1, A1)\n"
    assert traceability_problems(text) == []

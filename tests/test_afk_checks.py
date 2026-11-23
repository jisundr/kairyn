"""Pure checks of the AFK stage evals: each can fail (the eval-first rule), at no token cost."""
from checks import (build_row_problems, flags_problems, gate_row, new_constraint_lines, red_before_code_problems,
                    review_gap_problems)


def tool_use(i, name, **inp):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}}


def tool_result(i, text, error=False):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": text,
                                                     "is_error": error}]}}


TEST_FIRST = [tool_use(1, "Write", file_path="/r/test_lines.py"), tool_result(1, "ok"),
              tool_use(2, "Bash", command="python3 -m unittest test_lines"), tool_result(2, "FAILED (errors=1)", True),
              tool_use(3, "Edit", file_path="/r/textstats.py"), tool_result(3, "ok")]


def test_red_before_code_passes_on_a_failing_run_before_the_edit():
    assert red_before_code_problems(TEST_FIRST, "textstats.py", "test_lines") == []


def test_red_before_code_fails_when_the_code_comes_first():
    events = [TEST_FIRST[4], TEST_FIRST[5], *TEST_FIRST[:4]]
    assert red_before_code_problems(events, "textstats.py", "test_lines") == [
        "no failing run of test_lines before the first edit of textstats.py"]


def test_red_before_code_fails_when_the_run_passed():
    events = [*TEST_FIRST[:3], tool_result(2, "OK"), *TEST_FIRST[4:]]
    assert red_before_code_problems(events, "textstats.py", "test_lines")


def test_build_row_and_flags():
    good = "| T1 | abc1234 | 1 | def5678 | 0 |\n\n## Flags\n- None\n\n## Review\n- Review 1: Findings: none\n"
    assert build_row_problems(good) == [] and flags_problems(good) == []
    assert build_row_problems(good.replace("| 1 |", "| 0 |")) == ["red exit 0 is 0"]
    assert flags_problems(good.replace("- None", "- test edit: `test_lines.py` in feat(T1)"))


def test_gate_row():
    assert gate_row("| observability | fail | 0 | check: no docstring |\n", "observability")[:2] == ["fail", "0"]
    assert gate_row("", "observability") == []


def test_review_gap_problems():
    good = ("# Review\n\n## Gates\n- `security`: not set.\n\n## Findings\n- F1: AC2 (`--chars`) has no code.\n"
            "- F2: `# noqa` on line 15 has no reason.\n\nDecision: pending\n")
    assert review_gap_problems(good) == []
    assert len(review_gap_problems("# Review\n\n## Gates\nNone\n\n## Findings\n- None\n")) == 3


def test_new_constraint_lines():
    assert new_constraint_lines("# L\n- old\n", "# L\n- old\n- Ban `# noqa` with a lint rule or gate because x\n") == [
        "- Ban `# noqa` with a lint rule or gate because x"]

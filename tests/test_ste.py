"""ASD-STE100 (about 80%) linter used by the requirements eval."""
from checks import ste_problems, ste_rate


def test_short_direct_text_passes():
    text = "# Title\n\nPrompt caching lowers cost. The model saves processed parts of your prompt.\n"
    assert ste_problems(text) == []


def test_long_sentence_flagged():
    long = " ".join(["word"] * 26) + "."
    assert [p for p in ste_problems(long) if p.startswith("long")]


def test_25_words_is_allowed():
    assert ste_problems(" ".join(["word"] * 25) + ".") == []


def test_hedges_flagged():
    problems = ste_problems("The flag should print a plan. It may fail. It might work. It would stop.")
    assert sorted(p.split(":")[1].strip() for p in problems if p.startswith("hedge")) == ["may", "might", "should", "would"]


def test_filler_flagged():
    assert [p for p in ste_problems("In order to start, run it.") if p.startswith("filler")]


def test_code_headings_and_front_matter_ignored():
    text = (
        "---\ntitle: it should be ignored\n---\n"
        "## A heading that should be ignored\n\n"
        "Run `it should be ignored`.\n\n"
        "```\nthis should be ignored in order to test code blocks\n```\n"
    )
    assert ste_problems(text) == []


def test_list_items_and_table_cells_are_separate_sentences():
    item = " ".join(["word"] * 15)
    text = f"- {item}\n- {item}\n\n| {item} | {item} |\n|---|---|\n"
    assert ste_problems(text) == []


def test_rate_is_violations_per_100_words():
    text = "Word word word word word. " * 9 + "Word word word word should."   # 50 words, 1 hedge
    assert ste_rate(text) == 2.0


def test_rate_of_empty_text_is_zero():
    assert ste_rate("") == 0.0

"""Timestamp checks used by the requirements eval."""
from datetime import datetime, timedelta, timezone

from checks import TS_FORMAT, timestamp_problems

START = datetime(2026, 11, 17, 5, 56, 0, tzinfo=timezone.utc)
END = START + timedelta(minutes=2)


def stamp(dt):
    return dt.strftime(TS_FORMAT)


def body(ts):
    return f"# Log\n\n{ts} [requirements] did a thing\n"


def data(created, updated):
    return {"created": created, "updated": updated}


def test_real_timestamps_pass():
    t = stamp(START + timedelta(seconds=30))
    assert timestamp_problems(data(t, t), body(t), START, END) == []


def test_midnight_placeholder_rejected():
    t = "2026-11-17T00:00:00Z"
    assert any("placeholder" in p for p in timestamp_problems(data(t, t), body(t), START, END))


def test_noon_placeholder_rejected():
    t = "2026-11-17T12:00:00Z"
    assert any("placeholder" in p for p in timestamp_problems(data(t, t), body(t), START, END))


def test_timestamp_outside_window_rejected():
    t = stamp(END + timedelta(hours=1))
    assert any("outside run window" in p for p in timestamp_problems(data(t, t), body(t), START, END))


def test_unparseable_timestamp_rejected():
    assert any("bad timestamp" in p for p in timestamp_problems(data("soon", "soon"), body("soon"), START, END))


def test_log_line_timestamps_are_checked():
    good = stamp(START + timedelta(seconds=30))
    bad = "2026-11-17T00:00:00Z"
    problems = timestamp_problems(data(good, good), body(bad), START, END)
    assert any(p.startswith("log line") for p in problems)


def test_yaml_parsed_datetimes_are_accepted():
    """PyYAML turns unquoted ISO timestamps into datetimes; they must still validate."""
    import yaml
    t = stamp(START + timedelta(seconds=30))
    parsed = yaml.safe_load(f"created: {t}\nupdated: {t}\n")
    assert isinstance(parsed["created"], datetime)
    assert timestamp_problems(parsed, body(t), START, END) == []


def test_yaml_parsed_placeholder_still_rejected():
    import yaml
    parsed = yaml.safe_load("created: 2026-11-17T00:00:00Z\nupdated: 2026-11-17T00:00:00Z\n")
    t = stamp(START + timedelta(seconds=30))
    assert any("placeholder" in p for p in timestamp_problems(parsed, body(t), START, END))

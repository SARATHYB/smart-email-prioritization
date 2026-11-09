# tests/test_entity_extractor.py
from datetime import datetime, timedelta
from processing.entity_extractor import extract_deadline


def test_extract_keyword_deadline():
    now = datetime(2026, 11, 10, 10, 0, 0)
    text = "Amazon Campus Drive: Last date to apply is November 15, 2026 at 05:00 PM. Do not miss it!"
    parsed = extract_deadline(text, reference_time=now)
    assert parsed.deadline_dt is not None
    assert parsed.hours_remaining is not None
    assert parsed.hours_remaining > 0
    assert parsed.is_expired is False


def test_extract_expired_deadline():
    now = datetime(2026, 11, 10, 10, 0, 0)
    text = "Hackathon submission: Deadline was November 05, 2026. Submissions closed."
    parsed = extract_deadline(text, reference_time=now)
    assert parsed.deadline_dt is not None
    assert parsed.is_expired is True
    assert parsed.hours_remaining <= 0


def test_no_deadline_found():
    text = "Join us this weekend for a fun cycling club gathering at campus lawn."
    parsed = extract_deadline(text)
    assert parsed.deadline_dt is None
    assert parsed.deadline_str == "No deadline found"
    assert parsed.hours_remaining is None

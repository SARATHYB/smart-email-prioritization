# tests/test_cleaner.py
import pytest
from processing.cleaner import parse_sender, clean_html, clean_text


def test_parse_sender_standard():
    name, email = parse_sender("TCS Campus Recruitment <sarathybhas@gmail.com>")
    assert name == "TCS Campus Recruitment"
    assert email == "sarathybhas@gmail.com"


def test_parse_sender_only_angle_brackets():
    name, email = parse_sender("<sarathybhas@gmail.com>")
    assert email == "sarathybhas@gmail.com"


def test_parse_sender_plain_email():
    name, email = parse_sender("sarathybhas@gmail.com")
    assert email == "sarathybhas@gmail.com"


def test_clean_html_strips_tags_and_scripts():
    raw_html = "<html><head><script>alert('bad')</script></head><body><h1>Placement Notice</h1><p>Apply now!</p></body></html>"
    cleaned = clean_html(raw_html)
    assert "alert" not in cleaned
    assert "Placement Notice" in cleaned
    assert "Apply now!" in cleaned


def test_clean_text_preserves_deadline_formatting():
    raw_text = "Check this link https://example.com/apply \n\n Apply before March 15, 2026 at 5:00 PM!"
    cleaned = clean_text(raw_text)
    assert "https://example.com" not in cleaned
    assert "Apply before March 15, 2026 at 5:00 PM!" in cleaned

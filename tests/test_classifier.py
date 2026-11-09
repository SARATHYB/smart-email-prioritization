# tests/test_classifier.py
from core.models import EmailCategory
from processing.classifier import classify_email


def test_classify_placement():
    subject = "Amazon SDE-1 Campus Hiring Recruitment Drive"
    body = "Online assessment and technical interviews for 2026 batch. CTC 28 LPA."
    res = classify_email(subject, body)
    assert res.category == EmailCategory.PLACEMENT
    assert res.relevance_score >= 0.90
    assert res.confidence >= 0.60


def test_classify_internship():
    subject = "Google Summer of Code (GSoC) 2027 Open Source Internships"
    body = "Submit contributor proposals to mentoring organizations with stipend details."
    res = classify_email(subject, body)
    assert res.category == EmailCategory.INTERNSHIP


def test_classify_exam():
    subject = "CAT-2 Mid-Term Examination Schedule"
    body = "Check hall ticket and exam seating arrangement on student portal."
    res = classify_email(subject, body)
    assert res.category == EmailCategory.EXAM


def test_classify_scholarship():
    subject = "National Merit Scholarship Application Portal"
    body = "Financial aid and fee waiver for meritorious students."
    res = classify_email(subject, body)
    assert res.category == EmailCategory.SCHOLARSHIP


def test_classify_general():
    subject = "Campus Bicycle Network Launch"
    body = "Sustainability green drive and bicycle sharing stations."
    res = classify_email(subject, body)
    assert res.category == EmailCategory.GENERAL

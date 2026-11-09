# tests/test_tuds_engine.py
from core.models import EmailCategory, PriorityTier, TUDSParameters
from tuds.engine import compute_tuds_score


def test_tuds_urgency_increases_as_deadline_approaches():
    params = TUDSParameters(alpha=1.5)
    cat = EmailCategory.PLACEMENT
    relevance = 0.95

    # 10 days out (240 hours)
    score_far = compute_tuds_score(cat, relevance, hours_remaining=240.0, params=params)

    # 2 days out (48 hours)
    score_mid = compute_tuds_score(cat, relevance, hours_remaining=48.0, params=params)

    # 12 hours out (0.5 days)
    score_near = compute_tuds_score(cat, relevance, hours_remaining=12.0, params=params)

    assert score_near.priority_score > score_mid.priority_score
    assert score_mid.priority_score > score_far.priority_score
    assert score_near.tier == PriorityTier.URGENT


def test_tuds_expired_deadline_decays():
    cat = EmailCategory.PLACEMENT
    relevance = 0.95
    score_expired = compute_tuds_score(cat, relevance, hours_remaining=-24.0)

    assert score_expired.priority_score < 0.35
    assert score_expired.tier == PriorityTier.LOW
    assert score_expired.urgency_multiplier == 0.0


def test_tuds_no_deadline_baseline():
    cat = EmailCategory.GENERAL
    relevance = 0.40
    score_no_dl = compute_tuds_score(cat, relevance, hours_remaining=None)

    assert 0.0 < score_no_dl.priority_score < 0.50
    assert score_no_dl.urgency_multiplier == 1.0

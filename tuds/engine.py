# tuds/engine.py
"""
Temporal Urgency Decay Scoring (TUDS) Engine.

Mathematical Formulation:
    Priority_Score(t) = (R * I) * (1 + alpha * e^(-lambda * t))

Where:
    R = Base category relevance score [0.0, 1.0]
    I = User interest weight based on personalized preferences [0.0, 1.0]
    t = Time remaining before deadline (in days: t = hours_remaining / 24.0)
    alpha = Urgency amplification magnitude parameter (default: 1.5)
    lambda = Exponential decay rate specific to each category
"""

import math
from typing import Optional, Tuple
from core.models import (
    EmailCategory, PriorityTier, TUDSScore, TUDSParameters
)


def compute_tuds_score(
    category: EmailCategory,
    relevance_score: float,
    hours_remaining: Optional[float],
    params: Optional[TUDSParameters] = None
) -> TUDSScore:
    """
    Computes dynamic priority score based on category relevance, user interest, and temporal proximity.
    """
    if params is None:
        params = TUDSParameters()

    user_interest = params.user_interest_weights.get(category, 0.8)
    lam = params.category_lambdas.get(category, 0.05)
    alpha = params.alpha

    base_component = relevance_score * user_interest

    # Case 1: No deadline found
    if hours_remaining is None:
        final_score = min(max(base_component, 0.0), 1.0)
        tier = _determine_tier(final_score, hours_remaining)
        return TUDSScore(
            priority_score=round(final_score, 4),
            tier=tier,
            urgency_multiplier=1.0,
            hours_remaining=None,
            formula_breakdown=f"({relevance_score:.2f} * {user_interest:.2f}) [No Deadline]"
        )

    # Case 2: Deadline has passed (expired)
    if hours_remaining <= 0:
        # Expired emails lose temporal urgency; retain minimal historical relevance
        final_score = round(base_component * 0.25, 4)
        return TUDSScore(
            priority_score=final_score,
            tier=PriorityTier.LOW,
            urgency_multiplier=0.0,
            hours_remaining=round(hours_remaining, 2),
            formula_breakdown="Expired (t <= 0) -> Priority decayed"
        )

    # Case 3: Active future deadline -> Compute exponential urgency amplification
    # Convert hours to days for standard decay modeling
    t_days = hours_remaining / 24.0

    # Exponential urgency amplification term: alpha * e^(-lambda * t)
    urgency_boost = alpha * math.exp(-lam * t_days)
    multiplier = 1.0 + urgency_boost

    raw_score = base_component * multiplier
    normalized_score = min(raw_score / (1.0 + alpha), 1.0)
    # Ensure minimum baseline if relevance is high
    final_score = max(normalized_score, base_component * 0.7)
    final_score = min(round(final_score, 4), 1.0)

    tier = _determine_tier(final_score, hours_remaining)

    breakdown = (
        f"({relevance_score:.2f} * {user_interest:.2f}) * "
        f"(1 + {alpha:.1f} * e^(-{lam:.2f} * {t_days:.1f}d)) = {final_score:.3f}"
    )

    return TUDSScore(
        priority_score=final_score,
        tier=tier,
        urgency_multiplier=round(multiplier, 3),
        hours_remaining=round(hours_remaining, 2),
        formula_breakdown=breakdown
    )


def _determine_tier(score: float, hours_remaining: Optional[float]) -> PriorityTier:
    """Classifies score into actionable human-friendly tiers."""
    # Near-deadline override: anything closing in less than 24 hours is Urgent
    if hours_remaining is not None and 0 < hours_remaining <= 24.0:
        return PriorityTier.URGENT

    if score >= 0.75:
        return PriorityTier.URGENT
    elif score >= 0.60:
        return PriorityTier.HIGH
    elif score >= 0.40:
        return PriorityTier.MEDIUM
    else:
        return PriorityTier.LOW

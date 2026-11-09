# tuds/decay_curve.py
"""
Utility for generating TUDS decay curve points for data visualization.
Used by Streamlit to plot dynamic Priority vs. Days-to-Deadline curves.
"""

from typing import List, Dict, Any
from core.models import EmailCategory, TUDSParameters
from tuds.engine import compute_tuds_score
from processing.classifier import CATEGORY_RELEVANCE


def generate_decay_curve_data(
    category: EmailCategory,
    params: TUDSParameters,
    max_days: int = 30,
    steps: int = 60
) -> List[Dict[str, Any]]:
    """
    Generates simulated time steps from max_days down to 0 days,
    calculating the resulting TUDS priority score at each point.
    """
    points = []
    relevance = CATEGORY_RELEVANCE.get(category, 0.7)

    # Step down from max_days to 0
    step_size = max_days / max(steps, 1)
    current_day = max_days

    while current_day >= 0:
        hours = current_day * 24.0
        score_res = compute_tuds_score(
            category=category,
            relevance_score=relevance,
            hours_remaining=hours,
            params=params
        )
        points.append({
            "days_remaining": round(current_day, 1),
            "hours_remaining": round(hours, 1),
            "priority_score": score_res.priority_score,
            "tier": score_res.tier.value,
            "category": category.value.capitalize(),
        })
        current_day -= step_size

    return points

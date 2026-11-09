# processing/classifier.py
"""
Intelligent Email Intent & Category Classifier.
Classifies academic and career emails into structured categories with confidence and relevance scores.
"""

from typing import Dict, List, Tuple
from core.models import EmailCategory, ClassificationResult

# Category definitions with keyword weights
CATEGORY_TAXONOMY: Dict[EmailCategory, Dict[str, float]] = {
    EmailCategory.PLACEMENT: {
        "placement": 2.5,
        "campus drive": 3.0,
        "recruitment": 2.5,
        "interview": 2.0,
        "shortlist": 2.5,
        "ctc": 2.5,
        "job offer": 3.0,
        "hiring": 2.0,
        "oa": 2.0,
        "online assessment": 2.5,
        "sde": 2.0,
        "eligibility criteria": 2.0,
        "company presentation": 2.0,
        "aptitude test": 2.0,
    },
    EmailCategory.INTERNSHIP: {
        "internship": 3.0,
        "summer intern": 3.0,
        "winter intern": 3.0,
        "trainee": 2.0,
        "fellowship": 2.5,
        "gsoc": 3.0,
        "stipend": 2.0,
        "research intern": 3.0,
        "intern role": 2.5,
    },
    EmailCategory.EXAM: {
        "exam": 2.5,
        "mid-term": 3.0,
        "end-semester": 3.0,
        "hall ticket": 3.0,
        "cat 1": 3.0,
        "cat 2": 3.0,
        "fat": 3.0,
        "arrear": 2.5,
        "quiz": 2.0,
        "assessment": 1.5,
        "seating arrangement": 2.5,
        "revaluation": 2.5,
        "exam schedule": 3.0,
    },
    EmailCategory.SCHOLARSHIP: {
        "scholarship": 3.0,
        "financial aid": 3.0,
        "fee waiver": 3.0,
        "merit scholarship": 3.5,
        "grant": 2.0,
        "freeship": 3.0,
        "income certificate": 2.5,
        "reimbursement": 2.0,
    },
    EmailCategory.EVENT: {
        "hackathon": 3.0,
        "workshop": 2.5,
        "webinar": 2.5,
        "seminar": 2.0,
        "guest lecture": 2.5,
        "symposium": 2.5,
        "tech fest": 2.5,
        "coding competition": 3.0,
        "conference": 2.0,
    },
    EmailCategory.GENERAL: {
        "circular": 1.5,
        "announcement": 1.5,
        "notice": 1.5,
        "holiday": 2.0,
        "hostel": 2.0,
        "transport": 2.0,
        "maintenance": 2.0,
        "library": 1.5,
    }
}

# Base relevance scores R for each category
CATEGORY_RELEVANCE: Dict[EmailCategory, float] = {
    EmailCategory.PLACEMENT: 0.95,
    EmailCategory.EXAM: 0.90,
    EmailCategory.INTERNSHIP: 0.85,
    EmailCategory.SCHOLARSHIP: 0.80,
    EmailCategory.EVENT: 0.60,
    EmailCategory.GENERAL: 0.40,
}


def classify_email(subject: str, body: str) -> ClassificationResult:
    """
    Classifies an email based on weighted semantic tokens and context matching.
    Subject matches receive double weight.
    """
    subject_clean = (subject or "").lower()
    body_clean = (body or "").lower()

    category_scores: Dict[EmailCategory, float] = {cat: 0.0 for cat in EmailCategory}
    category_matches: Dict[EmailCategory, List[str]] = {cat: [] for cat in EmailCategory}

    for cat, keywords in CATEGORY_TAXONOMY.items():
        for kw, weight in keywords.items():
            # Subject match gives 2x score
            if kw in subject_clean:
                category_scores[cat] += weight * 2.5
                category_matches[cat].append(f"{kw} (subject)")
            elif kw in body_clean:
                category_scores[cat] += weight
                category_matches[cat].append(kw)

    best_category = EmailCategory.GENERAL
    max_score = 0.0

    for cat, score in category_scores.items():
        if score > max_score:
            max_score = score
            best_category = cat

    # Calculate confidence: scale score into [0.50, 0.98]
    if max_score > 0:
        confidence = min(0.55 + (max_score / 15.0) * 0.40, 0.98)
    else:
        confidence = 0.50

    return ClassificationResult(
        category=best_category,
        confidence=round(confidence, 3),
        relevance_score=CATEGORY_RELEVANCE[best_category],
        matched_keywords=category_matches[best_category][:5]
    )

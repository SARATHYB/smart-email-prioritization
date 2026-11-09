# processing/entity_extractor.py
"""
Temporal Entity & Deadline Extraction Engine.
Extracts deadlines from email text and computes real-time proximity.
Uses pure-Python dateutil.parser and standard library regex for 100% portable reliability.
"""

import re
from datetime import datetime
from typing import Optional
import dateutil.parser
from core.models import ParsedDeadline


# High-precision patterns anchored on intent keywords
DEADLINE_KEYWORD_PATTERNS = [
    r"(?:last date to apply(?: is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:last date to register(?: is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:apply before(?: is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:register by(?: is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:submit (?:by|before)(?: is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:deadline(?:\s*is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:closing date(?:\s*is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:scheduled on\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:exam starts on\s*)([A-Za-z0-9,/\s:-]{4,40})",
    r"(?:due date(?:\s*is|:)?\s*)([A-Za-z0-9,/\s:-]{4,40})",
]

# Fallback explicit date patterns (e.g. 2026-11-25 or November 15, 2026)
FALLBACK_DATE_PATTERNS = [
    r"\b(\d{4}-\d{1,2}-\d{1,2}(?:\s+\d{1,2}:\d{2})?)\b",
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s+\d{1,2}:\d{2})?)\b",
    r"\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)?)\b",
    r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)?)\b",
]


def extract_deadline(text: str, reference_time: Optional[datetime] = None) -> ParsedDeadline:
    """
    Scans text for temporal deadline mentions and parses them into a structured ParsedDeadline.
    """
    if not text:
        return ParsedDeadline()

    ref = reference_time or datetime.now()
    normalized_text = text.replace("\r", " ").replace("\n", " ")

    # 1. Search keyword-anchored patterns first
    for pattern in DEADLINE_KEYWORD_PATTERNS:
        matches = re.finditer(pattern, normalized_text, flags=re.IGNORECASE)
        for m in matches:
            candidate_raw = m.group(1).strip().rstrip(".,;!?")
            if len(candidate_raw) < 4 or len(candidate_raw) > 50:
                continue

            parsed_dt = _parse_date_string(candidate_raw, ref)
            if parsed_dt:
                hours = (parsed_dt - ref).total_seconds() / 3600.0
                return ParsedDeadline(
                    raw_match=m.group(0).strip(),
                    deadline_dt=parsed_dt,
                    deadline_str=parsed_dt.strftime("%Y-%m-%d %H:%M"),
                    hours_remaining=round(hours, 2),
                    is_expired=hours <= 0
                )

    # 2. Search fallback explicit date patterns
    for pattern in FALLBACK_DATE_PATTERNS:
        matches = re.finditer(pattern, normalized_text, flags=re.IGNORECASE)
        for m in matches:
            candidate_raw = m.group(1).strip()
            parsed_dt = _parse_date_string(candidate_raw, ref)
            if parsed_dt:
                hours = (parsed_dt - ref).total_seconds() / 3600.0
                return ParsedDeadline(
                    raw_match=candidate_raw,
                    deadline_dt=parsed_dt,
                    deadline_str=parsed_dt.strftime("%Y-%m-%d %H:%M"),
                    hours_remaining=round(hours, 2),
                    is_expired=hours <= 0
                )

    return ParsedDeadline(deadline_str="No deadline found")


def _parse_date_string(date_str: str, ref_time: datetime) -> Optional[datetime]:
    """Helper to parse a date candidate using pure-Python dateutil.parser."""
    try:
        # Avoid pure numbers being parsed as years/dates
        clean_s = date_str.strip()
        if clean_s.isdigit() and len(clean_s) < 8:
            return None

        # Truncate at sentence boundaries
        for sep in [".", ";", "\n", "  "]:
            if sep in clean_s:
                clean_s = clean_s.split(sep)[0].strip()

        parsed = dateutil.parser.parse(clean_s, fuzzy=True, default=ref_time)
        return parsed
    except Exception:
        return None

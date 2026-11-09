# processing/cleaner.py
"""
Text cleaning and sender extraction utilities.
Preserves semantic content for NLP and temporal extraction (avoids destructive stemming).
"""

import re
from typing import Tuple
from bs4 import BeautifulSoup


def parse_sender(sender_raw: str) -> Tuple[str, str]:
    """
    Parses sender raw string into (name, email).
    Examples:
        'TCS Campus Recruitment <sarathybhas@gmail.com>' -> ('TCS Campus Recruitment', 'sarathybhas@gmail.com')
        '<sarathybhas@gmail.com>'                        -> ('sarathybhas@gmail.com', 'sarathybhas@gmail.com')
        'sarathybhas@gmail.com'                          -> ('sarathybhas@gmail.com', 'sarathybhas@gmail.com')
    """
    if not sender_raw:
        return ("Unknown Sender", "unknown@domain.com")

    sender_raw = sender_raw.strip()

    # Pattern: Name <email@domain.com>
    match = re.search(r'^(.*?)\s*<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>', sender_raw)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        email = match.group(2).strip().lower()
        return (name or email, email)

    # Pattern: just <email@domain.com>
    match_angle = re.search(r'<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>', sender_raw)
    if match_angle:
        email = match_angle.group(1).strip().lower()
        return (email, email)

    # Pattern: direct email address
    match_direct = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', sender_raw)
    if match_direct:
        email = match_direct.group(0).strip().lower()
        name = sender_raw.replace(email, "").strip() or email
        return (name, email)

    return (sender_raw, sender_raw)


def clean_html(text: str) -> str:
    """Strips HTML tags, scripts, and styles while preserving clean text structure."""
    if not text:
        return ""

    if "<" in text and ">" in text:
        try:
            soup = BeautifulSoup(text, "html.parser")
            for script_or_style in soup(["script", "style", "head", "title", "meta"]):
                script_or_style.decompose()
            text = soup.get_text(separator=" ")
        except Exception:
            text = re.sub(r"<[^>]+>", " ", text)

    return text


def clean_text(text: str) -> str:
    """
    Normalizes whitespace, removes redundant symbols, and cleans text.
    Crucially maintains casing and punctuation for temporal NER and dateparser.
    """
    if not text:
        return ""

    text = clean_html(text)

    # Replace URL links with empty space or clean token
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)

    # Replace non-breaking spaces and tabs with standard space
    text = text.replace('\xa0', ' ').replace('\r', ' ')

    # Compress multiple whitespaces and excessive line breaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)

    return text.strip()

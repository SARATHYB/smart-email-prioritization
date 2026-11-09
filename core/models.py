# core/models.py
"""
Pydantic v2 schemas and data models for email prioritization.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    PLACEMENT = "placement"
    INTERNSHIP = "internship"
    EXAM = "exam"
    SCHOLARSHIP = "scholarship"
    EVENT = "event"
    GENERAL = "general"


class PriorityTier(str, Enum):
    URGENT = "Urgent"      # TUDS >= 0.80 or < 24h deadline
    HIGH = "High"          # TUDS >= 0.65
    MEDIUM = "Medium"      # TUDS >= 0.45
    LOW = "Low"            # TUDS < 0.45


class EmailFolder(str, Enum):
    INBOX = "inbox"
    SAVED = "saved"
    TRASH = "trash"


class RawEmail(BaseModel):
    id: str
    subject: str
    sender: str
    body: str
    timestamp: Optional[str] = None
    recipient: Optional[str] = "sarathybhas@gmail.com"


class ParsedDeadline(BaseModel):
    raw_match: Optional[str] = None
    deadline_dt: Optional[datetime] = None
    deadline_str: str = "No deadline found"
    hours_remaining: Optional[float] = None
    is_expired: bool = False


class ClassificationResult(BaseModel):
    category: EmailCategory
    confidence: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0, description="Base category relevance R")
    matched_keywords: List[str] = Field(default_factory=list)


class TUDSScore(BaseModel):
    priority_score: float = Field(ge=0.0, le=1.0, description="Final TUDS score between 0.0 and 1.0")
    tier: PriorityTier
    urgency_multiplier: float
    hours_remaining: Optional[float] = None
    formula_breakdown: Optional[str] = None


class PrioritizedEmail(BaseModel):
    id: str
    subject: str
    sender_name: str
    sender_email: str
    body: str
    cleaned_body: str
    timestamp: datetime
    category: EmailCategory
    category_confidence: float
    relevance_score: float
    deadline_str: str
    deadline_dt: Optional[datetime] = None
    hours_remaining: Optional[float] = None
    tuds_score: float
    priority_tier: PriorityTier
    folder: EmailFolder = EmailFolder.INBOX
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class TUDSParameters(BaseModel):
    alpha: float = Field(default=1.5, ge=0.1, le=5.0, description="Urgency magnitude parameter alpha")
    user_interest_weights: Dict[EmailCategory, float] = Field(
        default_factory=lambda: {
            EmailCategory.PLACEMENT: 1.0,
            EmailCategory.INTERNSHIP: 0.9,
            EmailCategory.EXAM: 0.95,
            EmailCategory.SCHOLARSHIP: 0.85,
            EmailCategory.EVENT: 0.60,
            EmailCategory.GENERAL: 0.40,
        }
    )
    category_lambdas: Dict[EmailCategory, float] = Field(
        default_factory=lambda: {
            EmailCategory.PLACEMENT: 0.06,
            EmailCategory.INTERNSHIP: 0.04,
            EmailCategory.EXAM: 0.07,
            EmailCategory.SCHOLARSHIP: 0.05,
            EmailCategory.EVENT: 0.03,
            EmailCategory.GENERAL: 0.01,
        }
    )

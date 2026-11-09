# ingestion/service.py
"""
Orchestration service for Email Ingestion, NLP Enrichment, and TUDS Scoring.
"""

from datetime import datetime
from typing import List, Optional
import dateutil.parser

from core.config import settings
from core.models import (
    RawEmail, PrioritizedEmail, TUDSParameters, EmailCategory, EmailFolder
)
from core.logger import get_logger
from processing.cleaner import clean_text, parse_sender
from processing.entity_extractor import extract_deadline
from processing.classifier import classify_email
from tuds.engine import compute_tuds_score
from storage.repository import repository, EmailRepository
from ingestion.mock_generator import MockEmailGenerator
from ingestion.gmail_connector import GmailConnector

logger = get_logger("ingestion_service")


class IngestionService:
    def __init__(self, repo: Optional[EmailRepository] = None):
        self.repo = repo or repository

    def get_provider(self, source: Optional[str] = None):
        src = (source or settings.ingestion_source).lower()
        if src == "gmail":
            return GmailConnector()
        return MockEmailGenerator()

    def process_raw_email(
        self,
        raw: RawEmail,
        params: Optional[TUDSParameters] = None
    ) -> PrioritizedEmail:
        """Runs the 5-stage enrichment pipeline on a single raw email."""
        if params is None:
            params = TUDSParameters()

        # Stage 1: Sender Extraction
        sender_name, sender_email = parse_sender(raw.sender)

        # Stage 2: Text Normalization
        cleaned_body = clean_text(raw.body)
        cleaned_subject = clean_text(raw.subject)
        full_text = f"{cleaned_subject}\n{cleaned_body}"

        # Stage 3: Temporal Deadline Extraction
        deadline_info = extract_deadline(full_text)

        # Stage 4: Multi-Class Semantic Intent Classification
        classification = classify_email(cleaned_subject, cleaned_body)

        # Stage 5: Dynamic TUDS Urgency Scoring
        tuds_result = compute_tuds_score(
            category=classification.category,
            relevance_score=classification.relevance_score,
            hours_remaining=deadline_info.hours_remaining,
            params=params
        )

        # Parse timestamp safely
        email_timestamp = datetime.now()
        if raw.timestamp:
            try:
                email_timestamp = dateutil.parser.parse(str(raw.timestamp))
                if email_timestamp.tzinfo is not None:
                    email_timestamp = email_timestamp.replace(tzinfo=None)
            except Exception:
                pass

        return PrioritizedEmail(
            id=raw.id,
            subject=raw.subject,
            sender_name=sender_name,
            sender_email=sender_email,
            body=raw.body,
            cleaned_body=cleaned_body,
            timestamp=email_timestamp,
            category=classification.category,
            category_confidence=classification.confidence,
            relevance_score=classification.relevance_score,
            deadline_str=deadline_info.deadline_str,
            deadline_dt=deadline_info.deadline_dt,
            hours_remaining=deadline_info.hours_remaining,
            tuds_score=tuds_result.priority_score,
            priority_tier=tuds_result.tier,
            folder=EmailFolder.INBOX,
            tags=classification.matched_keywords
        )

    def run_ingestion_cycle(
        self,
        source: Optional[str] = None,
        max_count: int = 50,
        params: Optional[TUDSParameters] = None
    ) -> List[PrioritizedEmail]:
        """Polls provider, enriches emails, and saves them to the repository."""
        provider = self.get_provider(source)
        logger.info(f"Starting ingestion cycle using provider: {provider.__class__.__name__}")

        raw_emails = provider.fetch_emails(max_count=max_count)
        logger.info(f"Fetched {len(raw_emails)} raw emails")

        enriched_emails = []
        for raw in raw_emails:
            enriched = self.process_raw_email(raw, params)
            enriched_emails.append(enriched)

        self.repo.upsert_batch(enriched_emails)
        logger.info(f"Successfully processed and stored {len(enriched_emails)} emails")
        return enriched_emails

    def recompute_all_scores(self, params: TUDSParameters) -> int:
        """
        Recomputes TUDS scores for all existing emails in the database with updated parameters.
        Allows instant dynamic re-ranking when sliders are adjusted in UI.
        """
        all_emails = self.repo.list_emails(limit=1000)
        updated_count = 0

        for email in all_emails:
            # Recompute hours remaining relative to right now
            hours_remaining = None
            if email.deadline_dt:
                diff = (email.deadline_dt - datetime.now()).total_seconds() / 3600.0
                hours_remaining = round(diff, 2)

            tuds_result = compute_tuds_score(
                category=email.category,
                relevance_score=email.relevance_score,
                hours_remaining=hours_remaining,
                params=params
            )

            email.hours_remaining = hours_remaining
            email.tuds_score = tuds_result.priority_score
            email.priority_tier = tuds_result.tier

            self.repo.upsert_email(email)
            updated_count += 1

        logger.info(f"Recomputed TUDS scores for {updated_count} emails")
        return updated_count


ingestion_service = IngestionService()

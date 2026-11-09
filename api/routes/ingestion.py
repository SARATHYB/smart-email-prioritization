# api/routes/ingestion.py
"""
FastAPI REST routes for email ingestion and demo seeding.
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ingestion.service import ingestion_service
from storage.repository import repository

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


class IngestResponse(BaseModel):
    status: str
    emails_processed: int
    source_used: str


@router.post("/sync", response_model=IngestResponse)
def trigger_ingestion(
    source: Optional[str] = Query(default=None, description="'mock' or 'gmail'")
):
    """Triggers an email ingestion cycle and enriches incoming emails."""
    processed = ingestion_service.run_ingestion_cycle(source=source)
    return IngestResponse(
        status="success",
        emails_processed=len(processed),
        source_used=source or "default"
    )


@router.post("/reset-demo")
def reset_and_seed_demo():
    """Clears the existing database and seeds fresh mock academic emails."""
    repository.clear_all()
    processed = ingestion_service.run_ingestion_cycle(source="mock")
    return {
        "status": "success",
        "message": f"Database reset and seeded with {len(processed)} fresh mock emails"
    }

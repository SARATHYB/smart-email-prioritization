# api/routes/emails.py
"""
FastAPI REST routes for email management and prioritization.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.models import (
    PrioritizedEmail, EmailCategory, PriorityTier, EmailFolder, TUDSParameters
)
from storage.repository import repository
from ingestion.service import ingestion_service

router = APIRouter(prefix="/api/emails", tags=["Emails"])


class FolderUpdateRequest(BaseModel):
    folder: EmailFolder


class RecomputeResponse(BaseModel):
    updated_count: int
    message: str


@router.get("", response_model=List[PrioritizedEmail])
def get_emails(
    folder: Optional[EmailFolder] = Query(default=EmailFolder.INBOX),
    category: Optional[EmailCategory] = None,
    tier: Optional[PriorityTier] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500)
):
    """Retrieves prioritized emails with dynamic filters and TUDS ranking."""
    return repository.list_emails(
        folder=folder,
        category=category,
        priority_tier=tier,
        search_query=search,
        limit=limit
    )


@router.get("/stats/overview")
def get_overview_stats():
    """Returns analytics summary (inbox count, urgent count, category breakdown)."""
    return repository.get_stats()


@router.get("/{email_id}", response_model=PrioritizedEmail)
def get_email_by_id(email_id: str):
    """Retrieves a single email by its unique ID."""
    emails = repository.list_emails(limit=500)
    for em in emails:
        if em.id == email_id:
            return em
    raise HTTPException(status_code=404, detail="Email not found")


@router.patch("/{email_id}/folder")
def update_email_folder(email_id: str, request: FolderUpdateRequest):
    """Moves an email between folders (inbox, saved, trash)."""
    success = repository.set_folder(email_id, request.folder)
    if not success:
        raise HTTPException(status_code=404, detail="Email not found or folder unchanged")
    return {"status": "success", "id": email_id, "folder": request.folder.value}


@router.post("/recompute", response_model=RecomputeResponse)
def recompute_priorities(params: TUDSParameters):
    """Recomputes all dynamic scores in the database using new TUDS parameters."""
    count = ingestion_service.recompute_all_scores(params)
    return RecomputeResponse(
        updated_count=count,
        message=f"Successfully recomputed priority scores for {count} emails"
    )

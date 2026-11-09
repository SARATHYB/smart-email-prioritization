# api/main.py
"""
FastAPI application entry point for Smart Personalized Email Prioritization.
Provides RESTful APIs, Swagger documentation (/docs), and automated lifecycle setup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logger import get_logger
from storage.repository import repository
from ingestion.service import ingestion_service
from api.routes.emails import router as emails_router
from api.routes.ingestion import router as ingestion_router

logger = get_logger("api_main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database exists and seed initial demo data if empty
    logger.info("Initializing Smart Email Prioritization API...")
    repository.init_db()
    existing_emails = repository.list_emails(limit=1)
    if not existing_emails:
        logger.info("Database empty on startup. Automatically seeding realistic mock emails...")
        ingestion_service.run_ingestion_cycle(source="mock")
    yield
    logger.info("Shutting down API server...")


app = FastAPI(
    title="Smart Personalized Email Prioritization System",
    description=(
        "Production REST API for dynamic email ranking using "
        "Temporal Urgency Decay Scoring (TUDS), semantic intent classification, "
        "and automated deadline extraction."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(emails_router)
app.include_router(ingestion_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Service health and database connectivity check."""
    stats = repository.get_stats()
    return {
        "status": "healthy",
        "service": "Smart Email Prioritization API",
        "version": "2.0.0",
        "database_stats": stats
    }


if __name__ == "__main__":
    import uvicorn
    from core.config import settings
    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=True)

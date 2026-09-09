"""
Procura AI Standards Engine — FastAPI Application

AI-Powered Recommendation Engine for Identifying Applicable
Indian Standards for Procurement Specifications.

SIH Problem Statement 26108
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("[START] Starting Procura AI Standards Engine...")

    # Create database tables
    await init_db()
    logger.info("[DB] Database initialized")

    # Auto-seed standards if database is empty (e.g. fresh Render deployment)
    try:
        from sqlalchemy import select, func
        from app.core.database import async_session
        from app.models.bis_standard import BISStandard
        from scripts.ingest_bis_data import ingest_bis_data

        async with async_session() as session:
            count = await session.scalar(select(func.count(BISStandard.id)))
            if not count or count == 0:
                logger.info("[DB] Database has 0 standards. Auto-seeding BIS standards...")
                await ingest_bis_data()
                logger.info("[DB] Auto-seeding BIS standards complete.")
    except Exception as e:
        logger.error(f"[DB] Auto-seed failed: {e}")

    # Ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"[FS] Upload directory: {settings.upload_path}")

    yield

    # Shutdown
    await close_db()
    logger.info("[STOP] Procura shutdown complete")


# ── Application Factory ───────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Procura analyzes procurement/tender technical specifications and "
        "natural-language queries to recommend applicable Indian Standards (BIS). "
        "This is a structured recommendation engine, not a chatbot."
    ),
    lifespan=lifespan,
)

# ── Rate Limiting & CORS ──────────────────────────────────────────
from app.core.rate_limiter import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    rpm=settings.RATE_LIMIT_RPM,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ──────────────────────────────────────────────
from app.api.routes.health import router as health_router
from app.api.routes.tenders import router as tenders_router
from app.api.routes.query import router as query_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.standards import router as standards_router

app.include_router(health_router)
app.include_router(tenders_router)
app.include_router(query_router)
app.include_router(recommendations_router)
app.include_router(standards_router)


# ── Root Endpoint ─────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "Procura AI Standards Engine",
        "version": settings.APP_VERSION,
        "status": "online",
        "description": "AI-Powered BIS Standards Recommendation for Procurement",
        "problem_statement": "SIH 26108",
        "endpoints": {
            "health": "/health",
            "upload_tender": "POST /api/tenders/upload",
            "submit_query": "POST /api/query",
            "docs": "/docs",
        },
    }

"""
Procura — Application Configuration

All settings are loaded from environment variables with sensible defaults
for the prototype (SQLite + NumPy vectors).
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for the Procura backend."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Procura AI Standards Engine"
    APP_VERSION: str = "1.0.0-prototype"
    DEBUG: bool = True

    # ── Database (SQLite for prototype) ──────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/procura.db",
        description="SQLAlchemy database URL. SQLite for prototype, PostgreSQL for production.",
    )

    # ── Supabase (for production — unused in prototype) ──────────
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "procura-tenders"

    # ── Gemini API ───────────────────────────────────────────────
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key — required for analysis and embeddings.",
    )
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"

    # ── Embeddings ───────────────────────────────────────────────
    EMBEDDING_DIMENSION: int = 3072
    EMBEDDING_BATCH_SIZE: int = 20

    # ── Retrieval ────────────────────────────────────────────────
    TOP_K: int = 10
    SIMILARITY_THRESHOLD: float = 0.3

    # ── Relevance Scoring Weights ────────────────────────────────
    RELEVANCE_WEIGHT_SEMANTIC: float = 0.40
    RELEVANCE_WEIGHT_PRODUCT: float = 0.25
    RELEVANCE_WEIGHT_SCOPE: float = 0.20
    RELEVANCE_WEIGHT_PARAMETER: float = 0.15

    # ── Compliance Scoring Weights ───────────────────────────────
    COMPLIANCE_WEIGHT_COVERED: float = 1.0
    COMPLIANCE_WEIGHT_PARTIAL: float = 0.5
    COMPLIANCE_WEIGHT_MISSING: float = 0.0

    # ── Confidence Scoring Weights ───────────────────────────────
    CONFIDENCE_WEIGHT_RETRIEVAL: float = 0.30
    CONFIDENCE_WEIGHT_SIMILARITY: float = 0.30
    CONFIDENCE_WEIGHT_SCOPE: float = 0.20
    CONFIDENCE_WEIGHT_EVIDENCE: float = 0.20

    # ── PDF Processing ───────────────────────────────────────────
    TESSERACT_CMD: str = "tesseract"
    OCR_SCALE_FACTOR: int = 2
    MIN_TEXT_LENGTH_FOR_DIGITAL: int = 50
    MAX_PDF_PAGES: int = 500
    MAX_TENDER_CHARACTERS: int = 60000

    # ── File Storage (local for prototype) ───────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_RPM: int = 10  # Maximum requests per minute per client IP

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://procura-zhj7.onrender.com",
    ]

    # ── Paths ────────────────────────────────────────────────────
    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def upload_path(self) -> Path:
        path = self.base_dir / self.UPLOAD_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_path(self) -> Path:
        """Ensure the database directory exists."""
        db_file = self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        path = self.base_dir / db_file
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

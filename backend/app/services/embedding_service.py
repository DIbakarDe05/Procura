"""
Procura — Embedding Service

Generates vector embeddings using configurable model (Gemini text-embedding-004).
Supports batch embedding for efficiency.
"""

import json
import logging
import asyncio
from typing import Optional

import numpy as np

from app.core.config import settings

logger = logging.getLogger("procura.embedding_service")


class EmbeddingService:
    """Generates embeddings for requirements and BIS standards."""

    def __init__(self):
        self._client = None
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def generate_embedding(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return None

        try:
            client = self._get_client()
            result = await asyncio.to_thread(
                client.models.embed_content,
                model=self.model,
                contents=text[:2000],  # Truncate for API limits
            )

            if result and result.embeddings:
                embedding = result.embeddings[0].values
                return list(embedding)

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")

        return None

    async def generate_embeddings_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failed items)
        """
        results = []
        batch_size = settings.EMBEDDING_BATCH_SIZE

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                embedding = await self.generate_embedding(text)
                results.append(embedding)

        return results

    @staticmethod
    def embedding_to_json(embedding: list[float]) -> str:
        """Serialize embedding to JSON string for SQLite storage."""
        return json.dumps(embedding)

    @staticmethod
    def json_to_embedding(json_str: str) -> Optional[np.ndarray]:
        """Deserialize embedding from JSON string."""
        if not json_str:
            return None
        try:
            values = json.loads(json_str)
            return np.array(values, dtype=np.float32)
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        if vec_a is None or vec_b is None:
            return 0.0
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


# Singleton
embedding_service = EmbeddingService()

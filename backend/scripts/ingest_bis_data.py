"""
Procura — BIS Data Ingestion Pipeline

Reads verified BIS standards from JSON, generates embeddings,
and inserts into the database. Idempotent — safe to re-run.

Usage:
    cd backend
    python -m scripts.ingest_bis_data
"""

import sys
import os
import json
import asyncio
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import async_session, init_db
from app.core.config import settings
from app.models.bis_standard import BISStandard, StandardReference
from app.services.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("procura.ingest")


async def ingest_bis_data(data_file: str = None):
    """
    Ingest BIS standards from JSON into database.

    - Validates standard numbers
    - Generates embeddings
    - Upserts (idempotent)
    - Creates standard references
    """
    if data_file is None:
        proto_file = os.path.join(settings.data_dir, "bis_standard.json")
        data_file = proto_file if os.path.exists(proto_file) else os.path.join(settings.data_dir, "seed_bis_data.json")

    logger.info(f"📂 Loading BIS data from: {data_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    standards_data = data.get("standards", [])
    references_data = data.get("references", [])

    # If references are embedded inside standards, extract them
    if not references_data:
        references_data = []
        for std_data in standards_data:
            from_num = std_data.get("standard_number", "").strip()
            for ref in std_data.get("references", []):
                to_num = ref.get("standard_number", "").strip()
                if from_num and to_num:
                    references_data.append({
                        "from_standard": from_num,
                        "to_standard": to_num,
                        "reference_type": ref.get("reference_type", "allied"),
                        "description": ref.get("description", ""),
                    })

    logger.info(f"📋 Found {len(standards_data)} standards and {len(references_data)} references")

    # Initialize database
    await init_db()

    async with async_session() as db:
        # ── Ingest Standards ────────────────────────────────────
        standard_map = {}  # standard_number -> id

        for i, std_data in enumerate(standards_data):
            std_num = std_data.get("standard_number", "").strip()

            if not std_num:
                logger.warning(f"Skipping entry {i}: missing standard_number")
                continue

            # Check if already exists (idempotent)
            result = await db.execute(
                select(BISStandard).where(BISStandard.standard_number == std_num)
            )
            existing = result.scalar_one_or_none()

            # Generate embedding text from title + scope + keywords + requirements
            metadata = std_data.get("metadata", {}) or {}
            product_categories = std_data.get("product_types") or metadata.get("product_categories") or []
            relevance_keywords = std_data.get("keywords") or metadata.get("relevance_keywords") or []
            tech_reqs = std_data.get("technical_requirements") or []

            embed_text = f"{std_data['title']}. {std_data.get('scope', '')}."
            if product_categories:
                embed_text += " " + ", ".join(product_categories)
            if relevance_keywords:
                embed_text += " " + ", ".join(relevance_keywords)
            if tech_reqs:
                embed_text += " " + " ".join(tech_reqs)

            # Format certification details as string if it's a dict
            cert_details = std_data.get("certification_details")
            if isinstance(cert_details, dict):
                cert_details = json.dumps(cert_details)

            combined_metadata = {
                **metadata,
                "product_categories": product_categories,
                "relevance_keywords": relevance_keywords,
                "technical_requirements": tech_reqs,
            }

            if existing:
                standard_map[std_num] = existing.id
                if not existing.embedding:
                    logger.info(f"  🔄 Backfilling missing embedding for: {std_num}")
                    embedding = await embedding_service.generate_embedding(embed_text)
                    if embedding:
                        existing.embedding = embedding_service.embedding_to_json(embedding)
                        logger.info(f"  ✅ Embedding backfilled for: {std_num}")
                    else:
                        logger.warning(f"  ⚠️ Could not generate embedding for: {std_num} (check API key)")
                else:
                    logger.info(f"  ✓ Already exists with embedding: {std_num}")
                continue

            logger.info(f"  🔄 Generating embedding for new standard: {std_num}")
            embedding = await embedding_service.generate_embedding(embed_text)
            embedding_json = embedding_service.embedding_to_json(embedding) if embedding else None

            std = BISStandard(
                standard_number=std_num,
                title=std_data["title"],
                scope=std_data.get("scope"),
                category=std_data.get("category"),
                edition=std_data.get("edition"),
                status=std_data.get("status", "current"),
                amendments=std_data.get("amendments"),
                certification_required=std_data.get("certification_required"),
                certification_details=cert_details,
                source=std_data.get("source", "ByteWorks Prototype BIS Dataset"),
                meta_data=combined_metadata,
                embedding=embedding_json,
            )
            db.add(std)
            await db.flush()

            standard_map[std_num] = std.id
            logger.info(f"  ✅ Ingested: {std_num} — {std_data['title'][:60]}")

        await db.commit()
        logger.info(f"\n📊 Standards ingested: {len(standard_map)}")

        # ── Ingest References ───────────────────────────────────
        ref_count = 0
        for ref_data in references_data:
            from_std = ref_data.get("from_standard")
            to_std = ref_data.get("to_standard")
            ref_type = ref_data.get("reference_type")

            from_id = standard_map.get(from_std)
            to_id = standard_map.get(to_std)

            if not from_id or not to_id:
                logger.warning(f"  ⚠ Skipping ref: {from_std} → {to_std} (standard not found)")
                continue

            # Check for duplicate references
            result = await db.execute(
                select(StandardReference).where(
                    StandardReference.standard_id == from_id,
                    StandardReference.referenced_standard_id == to_id,
                    StandardReference.reference_type == ref_type,
                )
            )
            if result.scalar_one_or_none():
                logger.info(f"  ✓ Ref exists: {from_std} → {to_std} ({ref_type})")
                continue

            ref = StandardReference(
                standard_id=from_id,
                referenced_standard_id=to_id,
                reference_type=ref_type,
                description=ref_data.get("description"),
            )
            db.add(ref)
            ref_count += 1
            logger.info(f"  🔗 Reference: {from_std} → {to_std} ({ref_type})")

        await db.commit()
        logger.info(f"\n📊 References created: {ref_count}")
        logger.info("✅ BIS data ingestion complete!")


if __name__ == "__main__":
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(ingest_bis_data(data_file))

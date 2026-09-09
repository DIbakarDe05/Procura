# Procura — AI-Powered BIS Standards Recommendation Engine

> **SIH Problem Statement 26108**
> AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

### 3. Ingest BIS Standards Data

```bash
python -m scripts.ingest_bis_data
```

This reads `data/seed_bis_data.json`, generates embeddings via Gemini, and populates the SQLite database.

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Open API Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Architecture

```
PDF Upload ──→ PDF Processor ──→ Section Detection ──→ Requirement Extraction ──┐
                                                                                 ▼
                                                              Requirement Normalizer
                                                                                 ▲
Query Input ──→ Query Understanding ──→ Requirement Extraction ─────────────────┘
                                                                                 │
                                                                                 ▼
                                                              Common Requirement Model
                                                                                 │
                                                                                 ▼
                                                              Embedding Generation
                                                                                 │
                                                                                 ▼
                                                    Semantic Retrieval (cosine similarity)
                                                                                 │
                                                                                 ▼
                                                              Relevance Scoring Engine
                                                                                 │
                                                                                 ▼
                                                    Gemini Structured Analysis (verified BIS only)
                                                                                 │
                                                                                 ▼
                                                              Compliance Scoring Engine
                                                                                 │
                                                                                 ▼
                                                         Structured Recommendation Report
```

**Core principle**: PDF and Query are two input paths that converge into ONE shared recommendation pipeline.

---

## API Endpoints

### Tender (PDF)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tenders/upload` | Upload tender PDF |
| GET | `/api/tenders/{id}` | Get tender details |
| GET | `/api/tenders/{id}/status` | Processing status |
| POST | `/api/tenders/{id}/analyze` | Start analysis |
| GET | `/api/tenders/{id}/requirements` | Extracted requirements |
| GET | `/api/tenders/{id}/recommendations` | Standard recommendations |
| GET | `/api/tenders/{id}/report` | Full structured report |

### Query
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Submit technical query |
| GET | `/api/query/{id}` | Query details |
| GET | `/api/query/{id}/recommendations` | Recommendations |
| GET | `/api/query/{id}/report` | Full structured report |

### Recommendations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recommendations/{id}` | Get recommendation |
| POST | `/api/recommendations/{id}/accept` | Officer accepts |
| POST | `/api/recommendations/{id}/reject` | Officer rejects |
| POST | `/api/recommendations/{id}/review` | Mark for review |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

---

## Three Separate Scores

| Score | Meaning | Can be null? |
|-------|---------|-------------|
| **Relevance** | How relevant is this standard to the requirement? | No |
| **Confidence** | How confident is the system in this recommendation? | No |
| **Compliance** | How much does this standard cover the requirements? | **Yes** — if query is too generic |

---

## Technology Stack

- **Framework**: FastAPI + Pydantic v2
- **Database**: SQLite (prototype) → PostgreSQL + pgvector (production)
- **PDF**: PyMuPDF + Tesseract OCR
- **AI**: Google Gemini API (analysis + embeddings)
- **Vector Search**: NumPy cosine similarity (prototype) → pgvector (production)

---

## BIS Data Ingestion

The system uses a verified BIS database as the **single source of truth**. Gemini never invents standard numbers.

To ingest your own BIS data:

```bash
python -m scripts.ingest_bis_data path/to/your/bis_data.json
```

JSON format:
```json
{
  "standards": [
    {
      "standard_number": "IS XXXX:YYYY",
      "title": "Standard Title",
      "scope": "What the standard covers",
      "category": "Category",
      "edition": "YYYY",
      "status": "current",
      "certification_required": true,
      "certification_details": "..."
    }
  ],
  "references": [
    {
      "from_standard": "IS XXXX:YYYY",
      "to_standard": "IS ZZZZ:YYYY",
      "reference_type": "normative_reference|test_method|safety|installation|allied",
      "description": "..."
    }
  ]
}
```

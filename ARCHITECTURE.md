# Procura — System Architecture Document
**AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications**  
*Smart India Hackathon (SIH) — Problem Statement 26108*

---

## 1. Executive Summary & Core Philosophy

**Procura** is an enterprise-grade recommendation engine built to assist public and private procurement officers in identifying, validating, and citing mandatory and recommended Bureau of Indian Standards (BIS) specifications. 

### Core Architectural Tenet: Zero-Hallucination Recommendation
Unlike conversational generative bots, Procura adheres to a **deterministic zero-hallucination policy**:
1. **Authoritative Grounding:** LLMs do **not** invent or suggest BIS standards out of thin air. Standards are retrieved exclusively from an indexed, authoritative BIS standards repository.
2. **Role of Generative AI:** Google Gemini 2.0 Flash is utilized solely for *semantic extraction* (parsing complex tenders into structured requirements) and *structured gap analysis* (evaluating requirement-to-scope provisions).
3. **Deterministic Scoring:** All scores (Compatibility/Relevance, Compliance, and Confidence) are computed by mathematical scoring engines using explicit weightings, not subjective model guesses.
4. **Officer-in-the-Loop Auditability:** Every recommendation provides verifiable evidence, key provisions, specific clause references, amendment notes, and official Accept/Reject audit actions for procurement officers.

---

## 2. High-Level Architecture

The system is structured as a decoupled, multi-tier architecture consisting of a **React/TypeScript Frontend**, a **FastAPI Asynchronous Gateway**, specialized **Ingestion & Processing Pipelines**, a **Unified Recommendation Engine**, and a **Dual-Mode Vector/Relational Data Layer**.

```mermaid
flowchart TB
    subgraph Client["Presentation Layer (Vite + React 18 + TS)"]
        UI_Home["Landing Portal"]
        UI_Tender["Tender PDF Workflow"]
        UI_Query["Natural Language Query Studio"]
        UI_Card["Recommendation Card & Officer Audit"]
    end

    subgraph Gateway["API Gateway (FastAPI Async)"]
        Router_Tenders["/api/tenders"]
        Router_Query["/api/query"]
        Router_Recs["/api/recommendations"]
        Router_Stds["/api/standards"]
        Router_Health["/health"]
    end

    subgraph Pipeline["Ingestion & Understanding Layer"]
        PDF_Proc["PDF Processor (PyMuPDF / OCR)"]
        Doc_Struct["Document Structure Analyzer"]
        Query_Parser["Query Understanding Service"]
        Req_Extract["Requirement Extractor (Gemini)"]
        Req_Norm["Requirement Normalizer"]
        Embed_Svc["Embedding Service (text-embedding-004)"]
    end

    subgraph CoreEngine["Unified Recommendation Engine"]
        Retriever["Semantic Vector Retriever (NumPy / pgvector)"]
        Scorer_Rel["Compatibility / Relevance Scorer"]
        LLM_Audit["Gemini 2.0 Analysis & Gap Evaluator"]
        Scorer_Comp["Compliance Scorer (Weighted Multi-Category)"]
        Scorer_Conf["Confidence Scorer (Multi-Signal)"]
        Svc_Version["Version & Reference Validator"]
        Report_Bld["Report Builder (Top-4 Deduplicator & Formatter)"]
    end

    subgraph DataLayer["Persistence Layer"]
        DB_Rel["Relational DB (SQLite / PostgreSQL)"]
        DB_Vec["Vector Index (In-Memory / pgvector 768-dim)"]
        File_Store["Local Storage / Supabase Object Store"]
        BIS_Repo["BIS Standards Authoritative Catalog (JSON / DB)"]
    end

    %% Connections
    UI_Tender --> Router_Tenders
    UI_Query --> Router_Query
    UI_Card --> Router_Recs

    Router_Tenders --> PDF_Proc
    Router_Query --> Query_Parser

    PDF_Proc --> Doc_Struct
    Doc_Struct --> Req_Extract
    Query_Parser --> Req_Extract
    Req_Extract --> Req_Norm
    Req_Norm --> Embed_Svc

    Embed_Svc --> Retriever
    Retriever <--> DB_Vec
    Retriever --> Scorer_Rel

    Scorer_Rel --> LLM_Audit
    LLM_Audit --> Scorer_Comp
    Scorer_Comp --> Scorer_Conf
    Scorer_Conf --> Svc_Version
    Svc_Version <--> BIS_Repo
    Svc_Version --> Report_Bld

    Report_Bld --> DB_Rel
    Router_Tenders --> DB_Rel
    Router_Query --> DB_Rel
    Router_Recs --> DB_Rel
```

---

## 3. End-to-End Data Flow

Both raw tender documents (PDFs) and user natural language queries converge into an identical, shared recommendation pipeline.

### 3.1 Workflow Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Procurement Officer
    participant UI as React Web Interface
    participant API as FastAPI Gateway
    participant Worker as Background Analysis Worker
    participant Gemini as Google Gemini AI
    participant DB as Database & Vector Store
    participant Builder as Report Builder

    alt Tender PDF Workflow
        Officer->>UI: Upload Tender PDF
        UI->>API: POST /api/tenders/upload
        API->>DB: Create Tender & ProcessingJob records
        API-->>UI: Return tender_id & job_id
        API->>Worker: Spawn background task
        Worker->>Worker: PyMuPDF extraction + Tesseract OCR fallback
        Worker->>Worker: Document Structure Analysis (sections, priority)
        Worker->>Gemini: Extract technical requirements from high-priority sections
        Gemini-->>Worker: Structured requirement JSON
    else Natural Language Query Workflow
        Officer->>UI: Submit technical procurement query
        UI->>API: POST /api/query
        API->>DB: Create Query record
        API-->>UI: Return query_id
        API->>Worker: Run query analysis
        Worker->>Gemini: Query Understanding (intent, product, parameters)
        Gemini-->>Worker: Structured query parameters
        Worker->>Worker: Extract & normalize query requirements
    end

    Note over Worker,Builder: SHARED RECOMMENDATION PIPELINE

    loop For each requirement
        Worker->>Gemini: Generate 768-dim embedding (text-embedding-004)
        Worker->>DB: Vector search against indexed BIS standards
        DB-->>Worker: Top-K candidate standards
        Worker->>Worker: Run Compatibility/Relevance Scoring (S, T, C)
        Worker->>Worker: Pick Top candidates
        Worker->>Gemini: Clause-by-clause analysis & coverage check
        Gemini-->>Worker: Structured Coverage (covered/partial/missing) + Gaps
        Worker->>Worker: Calculate Compliance Score (0-100%)
        Worker->>Worker: Calculate Confidence Score (0-100%)
        Worker->>DB: Persist Recommendation records
    end

    Worker->>Builder: Assemble final report
    Builder->>DB: Fetch version validity & related standard graph
    Builder->>Builder: Sort by Relevance, deduplicate, slice to Top 4
    Builder-->>Worker: Return ReportResponse
    Worker->>DB: Set status = completed (progress = 100%)

    loop Polling
        UI->>API: GET /status or GET /report
        API->>DB: Fetch results
        DB-->>API: Results payload
        API-->>UI: Return structured report
    end

    UI->>Officer: Display summary header, Top 4 cards, warnings & audit actions
```

---

## 4. Scoring Engine Mechanics

The Procura scoring subsystem is built around three isolated mathematical dimensions: **Compatibility Score ($CS$)**, **Compliance Score ($Comp$)**, and **Confidence Score ($Conf$)**.

### 4.1 Compatibility Score Formula ($CS$)
Compatibility answers: *"How suitable is this standard to the stated procurement requirement?"*

$$\boxed{ CS = 0.30S + 0.25T + 0.20C + 0.15V + 0.10R }$$

Where all sub-scores are normalized on a $[0, 100]$ scale:

| Metric | Factor | Meaning | Method of Calculation |
| :--- | :---: | :--- | :--- |
| **$S$** | **30%** | **Semantic Similarity** | Cosine similarity between requirement vector and standard vector: $\max(0, \cos(\mathbf{u}, \mathbf{v})) \times 100$. |
| **$T$** | **25%** | **Technical Match** | Overlap of technical parameters, product classifications, and material properties between tender and standard. |
| **$C$** | **20%** | **Scope Compatibility** | Keyword and contextual matching of the standard’s official scope against the requirement application. |
| **$V$** | **15%** | **Version Validity** | Current active edition ($100$), under review ($70$), superseded ($30$), or withdrawn ($0$). |
| **$R$** | **10%** | **Relationship Relevance** | Knowledge graph density: connections via testing, product specification, and safety references in `standard_references`. |

### 4.2 Compliance Score Formula ($Comp$)
Compliance answers: *"How thoroughly does this standard fulfill all functional and safety criteria of the specification?"*

Compliance is computed **after** Gemini structured gap assessment:
1. Gemini categorizes provisions into 9 standardized inspection categories: `product_type`, `performance`, `safety`, `material`, `testing`, `electrical`, `mechanical`, `marking`, `documentation`.
2. Each category is assigned a coverage status weight:
   - **Covered:** $1.0$
   - **Partial:** $0.5$
   - **Missing:** $0.0$
   - **Not Applicable:** Excluded from the denominator.
3. Category importance weights are applied:

$$Comp = \frac{\sum_{i \in \text{Applicable}} W_{\text{category}, i} \times W_{\text{status}, i}}{\sum_{i \in \text{Applicable}} W_{\text{category}, i}} \times 100$$

> **Generic Query Safeguard:** If a query provides insufficient technical parameters, $Comp$ is explicitly returned as `null` with a compliance note, avoiding misleading scores on open-ended queries.

### 4.3 Confidence Score Formula ($Conf$)
Confidence answers: *"How confident is the system in the reliability of this recommendation?"*

$$Conf = 0.30 \times \text{RetrievalSignal} + 0.30 \times \text{SimilarityStrength} + 0.20 \times \text{ScopeMatch} + 0.20 \times \text{EvidenceAvailability}$$

- **Retrieval Signal:** Ranks candidates by score drop-off from the #1 candidate.
- **Evidence Availability:** Scored based on key clause provisions extracted directly from authoritative documentation.

---

## 5. Database Schema & Entity Relationships

The relational model tracks documents, extracted sections, atomic requirements, authoritative standards, and final recommendation reports.

```mermaid
erDiagram
    TENDER ||--o{ TENDER_PAGE : contains
    TENDER ||--o{ TENDER_SECTION : parsed_into
    TENDER ||--o{ TENDER_REQUIREMENT : extracts
    TENDER ||--o{ PROCESSING_JOB : tracked_by
    TENDER_REQUIREMENT ||--o{ RECOMMENDATION : produces

    QUERY ||--o{ QUERY_REQUIREMENT : extracts
    QUERY_REQUIREMENT ||--o{ RECOMMENDATION : produces

    BIS_STANDARD ||--o{ STANDARD_REFERENCE : parent
    BIS_STANDARD ||--o{ STANDARD_REFERENCE : child
    BIS_STANDARD ||--o{ RECOMMENDATION : cited_by

    TENDER {
        string id PK
        string file_name
        string file_hash
        int page_count
        string status
        string processing_status
        datetime created_at
    }

    TENDER_PAGE {
        string id PK
        string tender_id FK
        int page_number
        text raw_text
        text cleaned_text
        boolean is_scanned
        boolean ocr_used
    }

    TENDER_SECTION {
        string id PK
        string tender_id FK
        int page_start
        int page_end
        string section_title
        string section_type
        text content
        string priority
    }

    TENDER_REQUIREMENT {
        string id PK
        string tender_id FK
        text requirement
        text normalized_requirement
        string requirement_type
        json parameters
        json embedding
        int page_number
    }

    QUERY {
        string id PK
        text query_text
        json normalized_query
        string status
        datetime created_at
    }

    QUERY_REQUIREMENT {
        string id PK
        string query_id FK
        text requirement
        text normalized_requirement
        string requirement_type
        json parameters
        json embedding
    }

    BIS_STANDARD {
        string id PK
        string standard_number UK
        string title
        text scope
        string category
        string edition
        string status
        json amendments
        boolean certification_required
        json embedding
    }

    STANDARD_REFERENCE {
        string id PK
        string standard_id FK
        string referenced_standard_id FK
        string reference_type
        string description
    }

    RECOMMENDATION {
        string id PK
        string tender_requirement_id FK
        string query_requirement_id FK
        string standard_id FK
        float relevance_score
        float confidence_score
        float compliance_score
        boolean applicable
        text reasoning
        json coverage
        json gaps
        string status
    }

    PROCESSING_JOB {
        string id PK
        string tender_id FK
        string status
        int progress
        string error_message
        datetime created_at
        datetime completed_at
    }
```

---

## 6. Service Directory & Component Responsibilities

### Backend (`backend/app/`)

| Directory / Module | Key Files | Responsibility |
| :--- | :--- | :--- |
| **`core/`** | `config.py`, `database.py`, `logging.py` | Environment config, database session lifecycle, logger tokens. |
| **`models/`** | `tender.py`, `requirement.py`, `bis_standard.py`, `recommendation.py`, `query.py`, `processing_job.py` | SQLAlchemy declarative database models. |
| **`schemas/`** | `tender.py`, `query.py`, `recommendation.py`, `standard.py` | Pydantic validation and serializable response models. |
| **`api/routes/`** | `tenders.py`, `query.py`, `recommendations.py`, `standards.py`, `health.py` | Asynchronous REST endpoints and request handlers. |
| **`services/`** | `pdf_processor.py`, `ocr_service.py` | PDF text extraction using PyMuPDF and Tesseract OCR engine. |
| | `document_structure.py` | Boundary detection, running header deduplication, priority scoring. |
| | `query_understanding.py` | Natural language intent extraction, parameter parsing. |
| | `requirement_extractor.py` | Gemini-driven requirement decomposition from text. |
| | `requirement_normalizer.py` | Parameter cleaning, unit standardization, product classification. |
| | `embedding_service.py` | Batch vector generation using Google `text-embedding-004`. |
| | `retrieval_service.py` | Semantic cosine retrieval across indexed BIS standards catalog. |
| | `relevance_scorer.py` | Deterministic Compatibility/Relevance mathematical engine. |
| | `gemini_service.py` | Async structured analysis and key provision extraction. |
| | `compliance_scorer.py` | Multi-category weighted compliance calculation. |
| | `confidence_scorer.py` | Multi-signal recommendation confidence evaluator. |
| | `standards_service.py` | Version verification and relational graph reference traversal. |
| | `certification_service.py` | Mandatory vs voluntary certification validation (ISI Mark, CRS). |
| | `report_builder.py` | Deduplication, top-4 ranking, and final report compilation. |
| **`workers/`** | `analysis_worker.py` | Background orchestration connecting ingestion to scoring. |

### Frontend (`frontend/src/`)

| Module / View | Responsibility |
| :--- | :--- |
| **`App.tsx`** | Top-level routing and view state coordination (`landing`, `query`, `tender`). |
| **`views/LandingPage.tsx`** | Portal home introducing Procura, feature highlights, and workflow triggers. |
| **`views/TenderWorkflow.tsx`** | Drag-and-drop PDF upload, stage progress bar, and summary results view. |
| **`views/QueryWorkflow.tsx`** | Free-text technical query input, sample suggestions, and results presentation. |
| **`views/RecommendationCard.tsx`** | Numbered recommendation cards (`#01` to `#04`), "Why?" section, officer actions (Accept/Reject), and expandable detailed report (coverage table, gaps, version, certification). |
| **`views/StatusBadge.tsx`** | Color-coded status tokens for recommendation state (`Accepted`, `Rejected`, `Pending`). |
| **`views/ProgressBar.tsx`** | Animated stage indicator for asynchronous background processing jobs. |
| **`api/client.ts`** | Typed Fetch client wrapper communicating with the FastAPI backend. |

---

## 7. Key Operational Algorithms

### 7.1 Section Priority Heuristic
To prevent token exhaustion and rate limits on 100+ page tenders, the `DocumentStructureAnalyzer` classifies sections:
- **High Priority:** Sections matching `technical specifications`, `scope of work`, `bill of quantities`, `equipment schedule`, `material requirements`.
- **Medium Priority:** Sections matching `general conditions`, `evaluation criteria`.
- **Low Priority (Skipped):** Sections matching `tender fee`, `earnest money deposit (EMD)`, `eligibility documents`, `format of bank guarantee`.

### 7.2 Top-4 Recommendation Deduplication
When multiple extracted tender requirements match the same standard (e.g., both concrete grade and reinforcement refer to IS 456), `report_builder.py`:
1. Ranks all candidates by overall score descending.
2. Deduplicates candidates by unique `standard_number`.
3. Slices the result to the **top 4 distinct recommendations**.
4. Enriches exclusively those 4 candidates with full version, certification, and relationship data to guarantee fast execution and clean UI rendering.

---

## 8. Technology Stack Summary

| Layer | Technology / Library | Role |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18, TypeScript, Vite | Single-page application, type-safe development |
| **Styling & Design** | TailwindCSS + Curated CSS Tokens | Government portal theme (Navy `#1e3a8a`, Saffron accents, Inter typography) |
| **Backend Framework** | FastAPI, Python 3.11+, Uvicorn | Async ASGI server, OpenAPI auto-documentation |
| **ORM & Persistence** | SQLAlchemy 2.0 (Async), aiosqlite | Asynchronous relational mapping |
| **Vector Engine** | NumPy (Prototype) / pgvector (Prod) | 768-dimensional cosine similarity indexing |
| **Document Processing** | PyMuPDF (fitz), pdf2image, pytesseract | Hybrid digital and scanned PDF text extraction |
| **LLM & Embeddings** | Google Gemini 2.0 Flash, text-embedding-004 | Semantic extraction, clause auditing, text embeddings |

---

## 9. Production Roadmap & Scalability Strategy

1. **Storage Tier:** Replace local SQLite database with PostgreSQL with `pgvector` for scalable HNSW index searching across 25,000+ BIS standards.
2. **Worker Tier:** Move background tasks from in-process asyncio tasks to distributed **Celery / Redis** or **Temporal** workers.
3. **Document Store:** Offload PDF storage to S3 or Supabase Storage with signed presigned URLs.
4. **Knowledge Graph:** Enhance `StandardReference` traversal using a graph database (e.g., Neo4j) to visualize complex standard hierarchies (Safety $\to$ Testing $\to$ Product).

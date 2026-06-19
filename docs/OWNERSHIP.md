# Ownership and Work Split

The goal is to let three people and their agents work in parallel without clashing.

## Person 1: Frontend / Review Workspace Owner

Primary folders:

```text
frontend/
```

Responsibilities:

- React/Vite setup
- project dashboard
- upload screens
- extracted questions list
- answer editor
- citation/source panel
- review actions: approve, edit, flag, reject
- export button and download UX
- mock data for development

Should rely on:

- `openapi.yaml`
- backend endpoints
- frontend API client in `frontend/src/api/`

Should avoid editing:

- backend service internals
- database models
- RAG code

## Person 2: Backend/API/Storage/Export Owner

Primary folders:

```text
backend/app/api/
backend/app/schemas/
backend/app/models/
backend/app/db/
backend/app/storage/
backend/app/services/export_pdf.py
```

Responsibilities:

- FastAPI app
- route definitions
- Pydantic schemas
- storage layer
- database integration
- answer status transitions
- export endpoint
- OpenAPI contract maintenance

Should avoid editing:

- frontend UI except when fixing broken integration
- RAG internals except via agreed interfaces

## Person 3: RAG / Document Processing / AI Owner

Primary folders:

```text
backend/app/services/document_parser.py
backend/app/services/question_extraction.py
backend/app/services/knowledge_ingestion.py
backend/app/services/retrieval.py
backend/app/services/answer_generation.py
```

Responsibilities:

- parse uploaded documents
- extract RFP questions
- chunk knowledge documents
- embed/search chunks
- retrieve relevant chunks
- generate answer drafts
- produce citation candidates
- maintain prompt templates

Should expose functions called by backend routes.

Should avoid editing:

- API response shapes without agreement
- frontend components

## Shared files

Change carefully:

```text
openapi.yaml
README.md
.env.example
docker-compose.yml
Makefile
docs/*
backend/app/main.py
```

## Branch naming

Suggested branches:

```text
feature/frontend-review-workspace
feature/backend-api-storage
feature/rag-ingestion-generation
feature/export-pdf
fix/api-contract-sync
```

## Merge rules

- Keep `main` runnable.
- Prefer small PRs.
- Announce `openapi.yaml` changes.
- Do not rename shared objects casually.
- Avoid formatting huge unrelated files.


## Pipeline eval and sample-data ownership

The RAG/AI owner is the primary owner of:

```text
backend/evals/
sample_data/
docs/PIPELINE_EVALS.md
```

Other contributors can add sample RFPs or knowledge documents, but they should keep the files realistic and avoid adding claims that the company would not actually want to make in a tender response.

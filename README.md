# RFP Copilot

RFP Copilot is a hackathon MVP for drafting answers to RFPs/tenders by reusing past company responses and internal knowledge, while keeping a human reviewer in control before export.

The main demo flow is:

```text
create project
  -> upload RFP
  -> extract questions/requirements
  -> upload knowledge documents
  -> draft answers using retrieval + LLM
  -> show citations
  -> human edits/approves/flags/rejects
  -> export final document
```

## Current architectural decision

This repository is a modular monolith:

```text
frontend/        React + TypeScript user interface
backend/         FastAPI API, domain logic, RAG integration, export
openapi.yaml     shared API contract for frontend/backend agents
infra/           database initialization and local infra helpers
docs/            project vision, architecture, agent rules, task breakdown, eval strategy
```

We are intentionally **not** building microservices for the hackathon. Keep the app easy to run and demo.

## Stack

| Layer | Decision |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | FastAPI + Pydantic |
| API contract | `openapi.yaml` |
| Naming | `snake_case` everywhere: API JSON, Python, database |
| Database target | PostgreSQL + pgvector |
| RAG | custom Python service functions first; framework optional later |
| LLM | OpenAI-compatible API via environment variables |
| Documents | PDF/DOCX/TXT/MD parsing |
| Export | DOCX first |
| Local dev | Docker Compose |

## Important project rule

The AI never produces a final answer automatically. The only text exported is the human-reviewed `final_text` of answers that are `approved` or `edited`.

Generated answers must include citations. If the system cannot find relevant source material, it must flag the answer instead of inventing content.

## Quick start

### 1. Copy environment file

```bash
cp .env.example .env
```

Fill in `OPENAI_API_KEY` if you want real generation. The backend contains safe mock/stub behavior so the app can still run during early development.

### 2. Start the local dev stack

```bash
docker compose up --build
```

This starts:

```text
PostgreSQL + pgvector  http://localhost:5432
Adminer database UI    http://localhost:8080
FastAPI backend        http://localhost:8000
Vite frontend          http://localhost:5173
```

Adminer login values for the local Docker database:

```text
System:   PostgreSQL
Server:   db
Username: postgres
Password: postgres
Database: rfp_copilot
```

The backend and frontend containers mount the local source tree and run their
normal dev servers. You do not need to rebuild for ordinary code changes:

- backend Python changes reload through `uvicorn --reload`
- frontend React/CSS changes reload through Vite HMR

Rebuild only when dependency or container files change, such as
`backend/pyproject.toml`, `frontend/package.json`, `frontend/package-lock.json`,
`backend/Dockerfile.dev`, `frontend/Dockerfile.dev`, or `docker-compose.yml`.

After the first build, the usual dev command is:

```bash
docker compose up
```

Useful Make aliases:

```bash
make dev-build
make dev
make down
make logs
```

### Optional: run backend and frontend directly on the host

If you are not using Docker for the app processes, start only the database:

```bash
docker compose up -d db adminer
```

Then run the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Backend docs:

```text
http://localhost:8000/docs
http://localhost:8000/health
```

And run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Pipeline evals instead of unit tests

For the hackathon, the project uses lightweight pipeline evals rather than traditional unit tests. The goal is to quickly inspect whether RFP question extraction, retrieval, answer drafting, warnings, and citations look useful.

Run the default eval:

```bash
make eval
```

This writes Markdown/JSON reports under `backend/evals/reports/`. Read `docs/PIPELINE_EVALS.md` for details.

## Sample data

Expanded demo data lives under:

```text
sample_data/rfps/
sample_data/knowledge_base/
```

The sample set includes public-sector, fintech, and healthcare RFPs plus a richer company knowledge base with policies, case studies, previous answers, implementation methodology, support/SLA notes, integration practices, and commercial assumptions.

## Read these before coding

Every coding agent and human contributor should read these first:

1. `docs/PROJECT_VISION.md`
2. `docs/AGENT_GUIDE.md`
3. `docs/ARCHITECTURE.md`
4. `openapi.yaml`
5. `docs/OWNERSHIP.md`
6. `docs/TASK_BREAKDOWN.md`
7. `docs/PIPELINE_EVALS.md`

## Repository ownership

```text
Frontend owner:
  frontend/

Backend/API owner:
  backend/app/api/
  backend/app/schemas/
  backend/app/models/
  backend/app/db/
  backend/app/services/export_docx.py

RAG/AI owner:
  backend/app/services/document_parser.py
  backend/app/services/question_extraction.py
  backend/app/services/knowledge_ingestion.py
  backend/app/services/retrieval.py
  backend/app/services/answer_generation.py
```

Shared files such as `openapi.yaml`, `README.md`, `.env.example`, and `docker-compose.yml` should be changed carefully and communicated clearly.

## MVP scope

In scope:

- create project
- upload one RFP document per project
- upload multiple knowledge documents
- extract questions/requirements
- generate answer per question
- show citations/source excerpts
- edit final answer
- approve/flag/reject answers
- export reviewed answers to DOCX

Out of scope for the hackathon MVP:

- authentication/authorization
- multi-tenant organizations
- real-time collaboration
- complex role-based review workflows
- automatic RFP submission
- payment/pricing spreadsheets
- advanced table extraction
- production-grade audit logs

## The core object

The whole UI and backend revolve around this shape:

```json
{
  "question_id": "question_123",
  "question_text": "Describe your data security practices.",
  "answer": {
    "id": "answer_123",
    "draft_text": "Our company applies encryption, access controls, and audit logging...",
    "final_text": "Our company applies encryption, access controls, and audit logging...",
    "status": "drafted"
  },
  "citations": [
    {
      "id": "citation_123",
      "document_title": "Security Policy",
      "section_title": "Encryption",
      "page_number": 4,
      "excerpt": "All customer data is encrypted at rest and in transit.",
      "relevance_score": 0.87
    }
  ]
}
```

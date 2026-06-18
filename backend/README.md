# Backend

FastAPI backend for RFP Copilot.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

## Current state

The backend is intentionally scaffolded with in-memory storage so frontend and RAG work can begin immediately. The target database is PostgreSQL + pgvector.

## Important rules

- Match `../openapi.yaml`.
- Use `snake_case` in all API fields.
- Keep route handlers thin.
- Put RAG logic in `app/services/`.
- AI-generated drafts are never final by default.

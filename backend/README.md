# Backend

FastAPI backend for RFP Copilot.

## Run

Preferred local workflow from the repository root:

```bash
docker compose up
```

The backend source is mounted into the container and reloads through Uvicorn.

To run directly on the host instead:

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

The backend persists MVP state in PostgreSQL through SQLAlchemy models. Tables are created automatically on backend startup for the hackathon flow. The pgvector extension is available through local Docker Compose, but retrieval still uses the simple lexical fallback until embedding retrieval is added.

## Important rules

- Match `../openapi.yaml`.
- Use `snake_case` in all API fields.
- Keep route handlers thin.
- Put RAG logic in `app/services/`.
- AI-generated drafts are never final by default.

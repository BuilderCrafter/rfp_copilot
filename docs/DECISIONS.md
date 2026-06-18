# Decision Record

## D001 - Modular monolith

Decision: Use one FastAPI backend with clear modules instead of microservices.

Reason: Hackathon speed, easier local setup, fewer deployment issues.

## D002 - React + TypeScript frontend

Decision: Use React + TypeScript with Vite.

Reason: Fast setup and simple component model for the review workspace.

## D003 - FastAPI backend

Decision: Use FastAPI and Pydantic.

Reason: Fast API development, clear schemas, good generated docs.

## D004 - OpenAPI contract checked into repo

Decision: Keep `openapi.yaml` at repo root.

Reason: Frontend/backend agents need a stable shared contract.

## D005 - snake_case everywhere

Decision: Use snake_case for API JSON, Python, database, and TypeScript API types.

Reason: Hackathon simplicity. Avoid repeated conversions.

## D006 - PostgreSQL + pgvector target

Decision: Target PostgreSQL + pgvector for persistent storage and vector search.

Reason: One database can hold app data and embeddings. The MVP may start with memory/lexical retrieval and migrate toward pgvector.

## D007 - Human-in-the-loop export

Decision: Export only `approved` and `edited` answers, using `final_text`.

Reason: RFP answers can create business/legal risk. AI output must not be final by default.

## D008 - Safe no-source behavior

Decision: If no relevant chunks are found, mark answer as flagged and return a warning instead of inventing.

Reason: Source-backed answers are core to the product vision.


## Pipeline evals over traditional tests

Decision: for the hackathon, use `backend/evals/` to evaluate the quality of the RFP drafting pipeline rather than building traditional unit-test coverage.

Reason: the key risk is answer quality, citation relevance, and hallucination control. Fast qualitative reports are more valuable than checking simple endpoint functionality during the hackathon.

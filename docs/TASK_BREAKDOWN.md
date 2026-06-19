# Task Breakdown

This replaces the earlier Trello-board idea. Use this file as the shared task list or copy it into GitHub Issues.

## Working agreement

Each task should have one owner. If a task changes an API contract, update `openapi.yaml` in the same PR/commit.

## Person 1: Frontend / Reviewer Workspace

### FE-01: Project dashboard

Build a simple page that lists projects and allows creating a new project.

Done when:

- user can create a project
- user can select a project
- frontend calls the backend contract from `openapi.yaml`

### FE-02: Document upload UI

Build upload panels for RFP document and knowledge documents.

Done when:

- user can upload one RFP document
- user can upload multiple knowledge documents
- document status is visible

### FE-03: Question list

Build the extracted question list with category and status badges.

Done when:

- user can trigger question extraction
- extracted questions are shown in order
- selected question drives the answer panel

### FE-04: Answer review workspace

Build the main demo UI: question list, answer editor, citation panel, and review actions.

Done when:

- answer draft is displayed
- final answer can be edited
- citations are visible
- user can approve, flag, or reject

### FE-05: Export flow

Add export button and download link handling.

Done when:

- user can export reviewed answers
- frontend clearly shows what will and will not be exported

## Person 2: Backend / API / Storage / Export

### BE-01: FastAPI skeleton and route registration

Ensure app startup, CORS, health endpoint, route registration, and docs work.

Done when:

- `uvicorn app.main:app --reload` starts
- `/health` works
- Swagger docs load

### BE-02: Project and document endpoints

Implement project creation/listing and document upload endpoints.

Done when:

- endpoints match `openapi.yaml`
- uploaded documents are stored locally for MVP
- metadata is persisted in the current storage layer

### BE-03: Question endpoints

Connect RFP document text to question extraction service.

Done when:

- user can trigger extraction
- extracted questions are persisted
- question list endpoint returns stable data

### BE-04: Answer endpoints

Implement draft, get, patch, approve, flag, and reject endpoints.

Done when:

- endpoints match `openapi.yaml`
- answer status transitions work
- citation objects are returned with answer responses

### BE-05: PDF export

Export approved/edited final answers to PDF.

Done when:

- rejected/flagged/drafted answers are excluded
- exported document includes question text and final answer text
- endpoint returns a usable download URL

### BE-06: Persistence upgrade

Replace or supplement in-memory storage with PostgreSQL/pgvector if time allows.

Status: baseline PostgreSQL persistence is implemented with SQLAlchemy and automatic MVP table creation. pgvector-backed retrieval is still future work.

Done when:

- existing API behavior does not change
- frontend continues to work
- setup remains simple

## Person 3: RAG / Parsing / Evaluation

### RAG-01: Document parsing

Improve parsing for Markdown, text, PDF, and DOCX.

Done when:

- parser returns clean text for sample files
- parser errors are clear and safe
- no API contract change is required

### RAG-02: Knowledge chunking

Improve chunking so citations are meaningful.

Done when:

- chunks preserve document title and useful section metadata where possible
- chunks are neither too tiny nor too broad
- eval report citations are understandable

### RAG-03: Retrieval

Replace lexical retrieval with embedding retrieval if time allows.

Done when:

- retrieved chunks are visibly relevant in eval reports
- function signature remains stable
- fallback behavior exists if embeddings/API key are unavailable

### RAG-04: Answer generation

Replace deterministic fallback with LLM-backed answer drafting.

Done when:

- answer uses only retrieved sources
- answer includes citations
- insufficient-source cases are flagged
- prompt is documented in `docs/PROMPTS.md`

### RAG-05: Pipeline evals

Maintain sample data and eval runner.

Done when:

- `make eval` works
- eval report shows questions, drafts, warnings, and citations
- sample data covers public sector, fintech, and healthcare RFPs

## Integration tasks

### INT-01: Full demo path

Run the full flow end-to-end with one sample RFP and the sample knowledge base.

Done when:

- create project
- upload RFP
- upload knowledge docs
- extract questions
- draft answers
- review answers
- export PDF

### INT-02: Demo polish

Prepare the final hackathon demo story.

Done when:

- selected demo RFP is known
- sample knowledge docs are uploaded
- at least three strong generated answers are ready
- at least one unsupported/flagged answer is shown as responsible AI behavior

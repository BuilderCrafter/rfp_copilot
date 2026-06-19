# Architecture

## High-level architecture

```text
React frontend
  -> FastAPI backend
      -> document parser
      -> question extraction
      -> knowledge ingestion
      -> retrieval
      -> answer generation
      -> review state management
      -> DOCX export
  -> PostgreSQL + pgvector target
```

This is a modular monolith. Keep modules separate in code, but deploy/run as one backend during the hackathon.

## Backend module responsibilities

### API layer

Files:

```text
backend/app/api/
```

Responsibilities:

- expose the contract from `openapi.yaml`
- validate request/response schemas
- call service functions
- map service results to API responses
- avoid embedding RAG logic directly in route handlers

### Schema layer

Files:

```text
backend/app/schemas/
```

Responsibilities:

- Pydantic request/response models
- enum definitions
- contract alignment with `openapi.yaml`

### Storage layer

Files:

```text
backend/app/storage/
backend/app/db/
backend/app/models/
```

Responsibilities:

- persistence abstraction
- SQLAlchemy database models
- automatic table creation during hackathon startup
- migrations later if the schema starts changing beyond MVP scope

### Document parsing

File:

```text
backend/app/services/document_parser.py
```

Responsibilities:

- extract text from PDF/DOCX/TXT/MD
- return normalized text and basic metadata
- avoid doing RAG logic here

### Question extraction

File:

```text
backend/app/services/question_extraction.py
```

Responsibilities:

- convert RFP text into `QuestionCandidate` objects
- start with simple rules; add LLM extraction later

### Knowledge ingestion

File:

```text
backend/app/services/knowledge_ingestion.py
```

Responsibilities:

- chunk company knowledge documents
- prepare chunks for embedding/storage
- preserve source metadata for citations

### Retrieval

File:

```text
backend/app/services/retrieval.py
```

Responsibilities:

- search relevant chunks for a question
- initially can use simple lexical scoring
- later should use embeddings + pgvector

### Answer generation

File:

```text
backend/app/services/answer_generation.py
```

Responsibilities:

- build prompt from question + retrieved chunks
- call LLM provider or fallback mock generator
- return draft text, citations, warnings
- never fabricate citations

### Export

File:

```text
backend/app/services/export_docx.py
```

Responsibilities:

- export only reviewed answers
- include question headings and final answers
- optionally include source/citation notes

## Data flow

```text
1. User creates project
2. User uploads RFP document
3. Backend parses RFP text
4. User triggers question extraction
5. Backend creates RfpQuestion records
6. User uploads knowledge documents
7. Backend parses, chunks, and stores chunks
8. User drafts answer for a question
9. Backend retrieves relevant chunks
10. Backend generates answer from retrieved chunks
11. Backend stores Answer + Citation records
12. User edits/approves/flags/rejects
13. Backend exports approved/edited final_text values
```

## Core data model

```text
Project
  -> Document
      -> KnowledgeChunk
  -> RfpQuestion
      -> Answer
          -> Citation
```

## API contract

`openapi.yaml` is the shared source of truth for frontend/backend communication. If a route or field changes, update `openapi.yaml` in the same PR.

## Naming

Use `snake_case` everywhere:

- JSON fields
- Python attributes
- database columns
- TypeScript API types

This is deliberately chosen to reduce hackathon friction.


## Pipeline evaluation

During the hackathon, pipeline quality is evaluated through `backend/evals/`, not through broad traditional unit tests. The eval runner uses realistic sample RFPs and knowledge-base documents from `sample_data/`, then writes reports showing extracted questions, retrieved citations, warnings, and draft answers.

This is intentionally qualitative. The team should inspect whether the generated answers are useful and grounded before optimizing internals.

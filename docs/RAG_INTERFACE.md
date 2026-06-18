# RAG Interface

The RAG/AI code should be callable from the backend through stable service functions. It should not be tightly coupled to FastAPI route handlers.

## Question extraction

```python
def extract_questions_from_text(project_id: str, document_text: str) -> list[QuestionCandidate]:
    ...
```

Returns normalized RFP questions/requirements.

## Knowledge ingestion

```python
def chunk_knowledge_document(document_id: str, document_title: str, text: str) -> list[KnowledgeChunkCandidate]:
    ...
```

Returns chunks that can be stored and used as citations.

## Retrieval

```python
def retrieve_relevant_chunks(project_id: str, question_text: str, top_k: int = 5) -> list[RetrievedChunk]:
    ...
```

Returns the most relevant source chunks for a question.

## Answer generation

```python
def draft_answer_from_sources(question_text: str, chunks: list[RetrievedChunk]) -> DraftAnswerResult:
    ...
```

Returns:

```python
class DraftAnswerResult(BaseModel):
    draft_text: str
    citations: list[CitationCandidate]
    warning: str | None = None
```

## Required behavior

If retrieval finds relevant chunks:

- generate an answer using only those chunks
- include citations for the supporting chunks
- never cite a source that was not passed in

If retrieval finds no relevant chunks:

- do not invent an answer
- return a warning
- backend should mark answer as `flagged`

## Current implementation path

Start simple:

1. parse text
2. chunk by character length/paragraphs
3. retrieve with lexical scoring
4. mock or API-based LLM generation
5. later replace retrieval with embeddings + pgvector

Do not block frontend/backend work waiting for perfect RAG.

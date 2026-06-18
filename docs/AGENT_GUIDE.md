# Agent Guide

This file is written for coding agents and human contributors.

## Always read first

Before making changes, read:

1. `README.md`
2. `docs/PROJECT_VISION.md`
3. `docs/ARCHITECTURE.md`
4. `openapi.yaml`
5. `docs/OWNERSHIP.md`
6. `docs/TASK_BREAKDOWN.md`
7. `docs/PIPELINE_EVALS.md`
8. this file

## Main goal

Build a working hackathon MVP of an RFP response drafting tool with citations and human review.

The demo path matters more than perfect internals.

## Global rules

1. Use `snake_case` everywhere.
2. Do not rename API fields unless you also update `openapi.yaml`, backend schemas, and frontend types.
3. Do not make the AI output final automatically.
4. Export only `approved` and `edited` answers.
5. Generated answers must include citations when source material exists.
6. If no relevant source exists, return a flagged answer/warning instead of inventing content.
7. Keep route handlers thin. Put business logic in `backend/app/services/`.
8. Keep the frontend able to run against mock/stub backend responses.
9. Avoid large refactors during the hackathon.
10. Do not add authentication, teams, multi-tenancy, or complex permissions unless all MVP work is done.
11. Do not spend hackathon time on traditional unit-test coverage. Use `backend/evals/` for pipeline quality checks.
12. Keep sample data realistic because the demo depends on retrieval quality.

## API contract discipline

The API contract is `openapi.yaml`.

When changing backend routes:

- update `openapi.yaml`
- update `backend/app/schemas/`
- update frontend types if needed
- mention the contract change in the PR/commit message

When changing frontend API calls:

- check `openapi.yaml`
- prefer adapting frontend code to the contract instead of inventing local shapes

## Human-in-the-loop rule

The system may generate:

- `draft_text`
- citations
- warning messages

The reviewer controls:

- `final_text`
- status transitions to `approved`, `edited`, `flagged`, or `rejected`

Only `final_text` is exported.

## Safe answer generation rule

The answer generation module must follow this behavior:

```text
if relevant chunks exist:
  draft answer from chunks
  attach citations
  status = drafted
else:
  draft_text = "Insufficient source material was found..."
  final_text = draft_text
  citations = []
  warning = "No relevant knowledge base chunks found."
  status = flagged
```

## Suggested working style for agents

### Frontend agent

- Build pages/components with the API shapes from `openapi.yaml`.
- Use mock data until backend is ready.
- Prioritize reviewer workflow: question list, answer editor, citation panel, status buttons.
- Do not spend too much time on visual polish before the full flow works.

### Backend/API agent

- Make endpoints match `openapi.yaml`.
- Start with in-memory storage if needed.
- Keep route handlers thin.
- Let RAG services be swappable.
- Ensure frontend can test with stable responses.

### RAG/AI agent

- Expose service functions. Do not bypass the API/data model.
- Preserve source metadata in every chunk.
- Return citations as structured data.
- Prefer simple reliable retrieval first, then embeddings.
- Keep prompts in `docs/PROMPTS.md` or service constants.

## Done means

A feature is done when:

- it works in the main demo flow
- it follows `openapi.yaml`
- it does not break existing endpoints/UI
- it has reasonable error handling
- it has enough comments/docstrings for the next agent to continue
- if it touches parsing/retrieval/generation, `make eval` produces a useful report for manual review

## Pipeline eval rule

This project uses evals to inspect answer quality, not traditional unit tests to prove code coverage.

Before changing question extraction, retrieval, chunking, prompting, or answer generation, run:

```bash
make eval
```

Then inspect the generated Markdown report in `backend/evals/reports/`. The report should make it easy to see whether citations are relevant and whether unsupported questions are flagged.

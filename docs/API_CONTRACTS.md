# API Contracts Summary

The formal source of truth is `openapi.yaml`. This file explains the most important contract decisions in plain English.

## Naming

All API fields use `snake_case`.

Examples:

```json
{
  "project_id": "project_123",
  "question_text": "Describe your support model.",
  "final_text": "Human-reviewed answer."
}
```

## Main UI contract

The review page should use this response shape:

```json
{
  "question_id": "question_123",
  "question_text": "Describe your data security practices.",
  "answer": {
    "id": "answer_123",
    "question_id": "question_123",
    "draft_text": "AI draft...",
    "final_text": "Editable reviewer text...",
    "status": "drafted",
    "review_note": null,
    "warning": null,
    "created_at": "2026-06-16T12:00:00Z",
    "updated_at": "2026-06-16T12:00:00Z"
  },
  "citations": [
    {
      "id": "citation_123",
      "answer_id": "answer_123",
      "chunk_id": "chunk_123",
      "document_title": "Security Policy",
      "section_title": "Encryption",
      "page_number": 4,
      "excerpt": "All customer data is encrypted at rest and in transit.",
      "relevance_score": 0.87
    }
  ]
}
```

## Status enums

### Project status

```text
active
completed
archived
```

### Document status

```text
uploaded
processing
processed
failed
```

### Question status

```text
pending
drafted
approved
flagged
```

### Answer status

```text
not_started
drafted
edited
approved
flagged
rejected
```

## Export rule

Export only answers whose status is:

```text
approved
edited
```

Export `final_text`, not `draft_text`.

## Contract change checklist

When changing a field, enum, or endpoint:

- update `openapi.yaml`
- update backend schemas
- update frontend API types
- update mocks if present
- mention the change in the PR description


## Export download

`POST /projects/{project_id}/export` returns `download_url`. In the backend skeleton, exported files are served from `/exports/{filename}` using FastAPI static files.

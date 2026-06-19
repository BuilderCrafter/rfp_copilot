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

## RFP assessment contract

RFP upload now computes a stored bid/no-bid and missing-information assessment. The upload endpoint still returns the `Document`; the frontend can then call:

```text
GET /projects/{project_id}/rfp_assessment
POST /projects/{project_id}/assess_rfp
```

The response shape is:

```json
{
  "id": "assessment_123",
  "project_id": "project_123",
  "rfp_document_id": "doc_123",
  "recommendation": "needs_review",
  "bid_score": 62,
  "confidence": 0.78,
  "summary": "Bid decision needs review...",
  "policy_source_documents": ["rfp_intake_and_bid_qualification.md"],
  "bid_factors": [],
  "checklist": [],
  "missing_information": [],
  "client_submission_checklist": [],
  "generated_at": "2026-06-19T12:00:00Z",
  "updated_at": "2026-06-19T12:00:00Z"
}
```

`checklist` and `missing_information` describe what is missing or incomplete in the buyer's RFP.
`client_submission_checklist` describes what our proposal team must provide to the buyer, such as financial statements, credit-rating evidence, employee screening evidence, insurance certificates, CVs, signed forms, diagrams, pricing workbooks, and compliance matrices.

The RFP assessment uses the unified knowledge base across projects. It requires `OPENAI_API_KEY`; deterministic rule fallback is disabled for this assessment path.

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

### RFP assessment recommendation

```text
bid
no_bid
needs_review
```

### RFP checklist status

```text
present
partial
missing
not_applicable
```

### Client submission checklist status

```text
required
conditional
optional
needs_review
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

# Pipeline Evaluation Strategy

The hackathon version of this project does not prioritize traditional unit tests.

Instead, the team will use **pipeline evals** to quickly inspect whether the RFP drafting workflow is producing useful outputs.

## Why evals instead of normal tests?

The highest-risk part of this project is not whether a health endpoint returns `200`. The real risk is whether the pipeline produces useful, grounded, citation-backed RFP draft answers.

The evals should help answer:

- Are we extracting the right RFP questions?
- Are we retrieving relevant source chunks?
- Are answers grounded in the knowledge base?
- Are citations understandable and useful to a reviewer?
- Are unsupported questions flagged instead of hallucinated?
- Does the output look good enough for a demo?

## Location

```text
backend/evals/
```

Current runner:

```text
backend/evals/evaluate_sample_pipeline.py
```

Generated reports:

```text
backend/evals/reports/
```

Reports are ignored by Git so the team can run them freely.

## Run the default eval

From repo root:

```bash
make eval
```

From backend:

```bash
python evals/evaluate_sample_pipeline.py
```

## Run a specific RFP

```bash
cd backend
python evals/evaluate_sample_pipeline.py \
  --rfp ../sample_data/rfps/02_fintech_kyc_aml_platform_rfp.md \
  --max_questions 12 \
  --top_k 5
```

## What to inspect

For each evaluated question, inspect:

1. Was the question extracted cleanly?
2. Are the citations from the right document type?
3. Does the draft answer reuse source material rather than inventing claims?
4. Is the warning behavior correct when there is not enough source material?
5. Is the answer usable as a first draft for a reviewer?

## What not to do

Do not turn the evals into a large brittle test suite during the hackathon.

Avoid spending time on perfect automated scoring. Manual inspection of the generated Markdown reports is enough for now.

## Future scoring ideas

After the MVP works, the team could add simple qualitative scoring fields:

```text
question_extraction_quality: 1-5
citation_relevance: 1-5
answer_usefulness: 1-5
hallucination_risk: low | medium | high
reviewer_action: approve | edit | flag | reject
```

These could later become a lightweight evaluation dataset for improving prompts and retrieval.

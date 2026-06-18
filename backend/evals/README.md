# Pipeline Evals

This project intentionally does **not** focus on traditional unit tests during the hackathon.

Instead, this folder contains lightweight pipeline evaluations that help the team answer:

- Are RFP questions being extracted well enough?
- Are the retrieved sources relevant to each question?
- Are draft answers useful and source-backed?
- Are weak or unsupported questions being flagged instead of hallucinated?

## Run the default eval

From the repository root:

```bash
make eval
```

Or from `backend/`:

```bash
python evals/evaluate_sample_pipeline.py
```

## Run a specific RFP

```bash
python evals/evaluate_sample_pipeline.py \
  --rfp ../sample_data/rfps/02_fintech_kyc_aml_platform_rfp.md \
  --max_questions 12 \
  --top_k 5
```

## Output

The eval writes Markdown reports to:

```text
evals/reports/
```

Each report includes extracted questions, generated draft answer text, warnings, and citations.

## Important rule

Do not turn these evals into strict implementation tests unless the team explicitly decides to do so. The goal is fast qualitative review of the AI/RAG pipeline.

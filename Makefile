.PHONY: backend frontend db eval lint test

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

db:
	docker compose up -d db

eval:
	cd backend && python evals/evaluate_sample_pipeline.py

# Kept as an alias so agents do not accidentally create a separate test workflow.
test: eval

lint:
	cd backend && ruff check app evals

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.answers import router as answers_router
from app.api.documents import router as documents_router
from app.api.exports import router as exports_router
from app.api.projects import router as projects_router
from app.api.questions import router as questions_router
from app.config import settings

app = FastAPI(
    title="RFP Copilot API",
    version="0.1.0",
    description="Hackathon MVP backend for source-backed RFP answer drafting.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def get_health() -> dict[str, str]:
    """Return a minimal health response used by local dev and deployment checks."""
    return {"status": "ok"}


app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(questions_router)
app.include_router(answers_router)
app.include_router(exports_router)
app.mount("/exports", StaticFiles(directory=settings.export_dir), name="exports")

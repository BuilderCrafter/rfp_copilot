from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app.api.answers import router as answers_router
from app.api.documents import router as documents_router
from app.api.exports import router as exports_router
from app.api.projects import router as projects_router
from app.api.questions import router as questions_router
from app.config import settings
from app.db.session import init_db
from app.schemas.common import HealthResponse
from app.schemas.document import KnowledgeChunk


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="RFP Copilot API",
    version="0.1.0",
    description="Hackathon MVP backend for source-backed RFP answer drafting.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["health"],
    response_model=HealthResponse,
    operation_id="get_health",
)
def get_health() -> HealthResponse:
    """Return a minimal health response used by local dev and deployment checks."""
    return HealthResponse(status="ok")


app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(questions_router)
app.include_router(answers_router)
app.include_router(exports_router)
app.mount("/exports", StaticFiles(directory=settings.export_dir), name="exports")


def custom_openapi() -> dict:
    """Include contract schemas that are not directly returned by an endpoint yet."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("schemas", {})[
        "KnowledgeChunk"
    ] = KnowledgeChunk.model_json_schema(ref_template="#/components/schemas/{model}")
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

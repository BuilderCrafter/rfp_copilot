from dataclasses import dataclass, field

from app.schemas.answer import Answer, Citation
from app.schemas.document import Document, KnowledgeChunk
from app.schemas.project import Project
from app.schemas.question import RfpQuestion


@dataclass
class MemoryStore:
    """Temporary in-memory store for hackathon parallel development.

    Replace or wrap this with real SQLAlchemy/PostgreSQL persistence when the backend owner
    is ready. Keeping this store lets frontend and RAG work begin immediately.
    """

    projects: dict[str, Project] = field(default_factory=dict)
    documents: dict[str, Document] = field(default_factory=dict)
    document_texts: dict[str, str] = field(default_factory=dict)
    questions: dict[str, RfpQuestion] = field(default_factory=dict)
    chunks: dict[str, KnowledgeChunk] = field(default_factory=dict)
    answers: dict[str, Answer] = field(default_factory=dict)
    citations: dict[str, Citation] = field(default_factory=dict)


store = MemoryStore()

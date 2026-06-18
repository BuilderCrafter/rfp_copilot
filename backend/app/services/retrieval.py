import math
import re
from dataclasses import dataclass

from app.schemas.document import KnowledgeChunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: KnowledgeChunk
    relevance_score: float


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is",
    "it", "of", "on", "or", "our", "the", "their", "to", "we", "what", "with", "your",
}


def tokenize(text: str) -> set[str]:
    """Tokenize text for simple lexical retrieval fallback."""
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if token not in _STOPWORDS}


def score_chunk(question_text: str, chunk_text: str) -> float:
    """Return a simple lexical overlap score between a question and a chunk."""
    q_tokens = tokenize(question_text)
    c_tokens = tokenize(chunk_text)
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = len(q_tokens & c_tokens)
    return overlap / math.sqrt(len(q_tokens) * len(c_tokens))


def retrieve_relevant_chunks(
    question_text: str,
    chunks: list[KnowledgeChunk],
    top_k: int = 5,
    min_score: float = 0.03,
) -> list[RetrievedChunk]:
    """Retrieve relevant chunks for a question.

    This MVP implementation uses lexical scoring. Replace internals with embeddings +
    pgvector later while keeping the function signature stable.
    """
    scored = [
        RetrievedChunk(chunk=chunk, relevance_score=score_chunk(question_text, chunk.text))
        for chunk in chunks
    ]
    scored = [item for item in scored if item.relevance_score >= min_score]
    scored.sort(key=lambda item: item.relevance_score, reverse=True)
    return scored[:top_k]

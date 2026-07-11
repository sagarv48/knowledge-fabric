"""Models for lexical/vector retrieval outputs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RetrievalHit:
    """One retrieval result row."""

    chunk_id: int
    document_id: int
    document_uri: str
    chunk_index: int
    chunk_text: str
    score: float
    source: str
    metadata: dict[str, object] = field(default_factory=dict)

"""Evidence package contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from knowledge_fabric.fusion.rrf import HybridHit


@dataclass(slots=True)
class EvidenceItem:
    """One evidence entry returned to callers."""

    chunk_id: int
    document_id: int
    document_uri: str
    chunk_index: int
    snippet: str
    score: float
    retrieval_sources: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class EvidencePackage:
    """Top-level evidence response."""

    query_text: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    items: list[EvidenceItem] = field(default_factory=list)
    retrieval_summary: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "query_text": self.query_text,
            "generated_at": self.generated_at.isoformat(),
            "items": [asdict(item) for item in self.items],
            "retrieval_summary": self.retrieval_summary,
        }


def build_evidence_package(query_text: str, hybrid_hits: list[HybridHit]) -> EvidencePackage:
    items = [
        EvidenceItem(
            chunk_id=hybrid.hit.chunk_id,
            document_id=hybrid.hit.document_id,
            document_uri=hybrid.hit.document_uri,
            chunk_index=hybrid.hit.chunk_index,
            snippet=hybrid.hit.chunk_text,
            score=hybrid.fused_score,
            retrieval_sources=hybrid.sources,
            metadata=hybrid.hit.metadata,
        )
        for hybrid in hybrid_hits
    ]
    summary = {
        "total_items": len(items),
        "sources": sorted({source for item in items for source in item.retrieval_sources}),
    }
    return EvidencePackage(query_text=query_text, items=items, retrieval_summary=summary)

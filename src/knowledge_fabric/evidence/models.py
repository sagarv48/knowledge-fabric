"""Evidence package contracts."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from knowledge_fabric.fusion.rrf import HybridHit


def compute_chunk_hash(document_uri: str, snippet: str) -> str:
    """Compute deterministic SHA-256 provenance hash for a single evidence chunk.

    Formula: SHA-256(document_uri + ":" + snippet)
    """
    payload = f"{document_uri}:{snippet}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_package_digest(items: list[EvidenceItem]) -> str:
    """Compute composite SHA-256 digest over ordered chunk provenance hashes.

    Formula: SHA-256(hash_1 + ":" + hash_2 + ":" + ... + hash_N)
    Returns empty string if items list is empty.
    """
    if not items:
        return ""
    combined = ":".join(item.provenance_hash for item in items).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def compute_query_fingerprint(
    query_text: str,
    tenant_id: str | None = None,
    mode: str = "hybrid",
) -> str:
    """Compute deterministic SHA-256 fingerprint for a retrieval request.

    Formula: SHA-256(tenant_id + ":" + query_text + ":" + mode)
    """
    tenant = tenant_id or "default"
    raw = f"{tenant}:{query_text}:{mode}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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
    provenance_hash: str = ""

    @property
    def citation_source(self) -> str:
        """Return human-readable citation source string."""
        path = self.metadata.get("heading_path")
        if path:
            return f"{self.document_uri}#{path}"
        return self.document_uri


@dataclass(slots=True)
class EvidencePackage:
    """Top-level evidence response."""

    query_text: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    items: list[EvidenceItem] = field(default_factory=list)
    retrieval_summary: dict[str, object] = field(default_factory=dict)
    provenance_digest: str = ""
    query_fingerprint: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "query_text": self.query_text,
            "generated_at": self.generated_at.isoformat(),
            "items": [asdict(item) for item in self.items],
            "retrieval_summary": self.retrieval_summary,
            "provenance_digest": self.provenance_digest,
            "query_fingerprint": self.query_fingerprint,
        }

    def format_citations(self, style: str = "markdown") -> str:
        """Format evidence items into structured text citations."""
        if not self.items:
            return "No citations available."
        lines: list[str] = []
        for i, item in enumerate(self.items, 1):
            heading_str = f" ({item.metadata.get('heading_path')})" if item.metadata.get("heading_path") else ""
            lines.append(f"[{i}] {item.document_uri}{heading_str} (score: {item.score:.4f})")
            lines.append(f"    \"{item.snippet}\"")
        return "\n".join(lines)


def build_evidence_package(
    query_text: str,
    hybrid_hits: list[HybridHit],
    *,
    summary_extra: dict[str, object] | None = None,
    tenant_id: str | None = None,
    mode: str = "hybrid",
) -> EvidencePackage:
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
            provenance_hash=compute_chunk_hash(
                hybrid.hit.document_uri,
                hybrid.hit.chunk_text,
            ),
        )
        for hybrid in hybrid_hits
    ]
    summary: dict[str, object] = {
        "total_items": len(items),
        "sources": sorted({source for item in items for source in item.retrieval_sources}),
    }
    if summary_extra:
        summary.update(summary_extra)
    return EvidencePackage(
        query_text=query_text,
        items=items,
        retrieval_summary=summary,
        provenance_digest=compute_package_digest(items),
        query_fingerprint=compute_query_fingerprint(query_text, tenant_id=tenant_id, mode=mode),
    )


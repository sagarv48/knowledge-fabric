from knowledge_fabric.evidence import build_evidence_package
from knowledge_fabric.fusion import HybridHit
from knowledge_fabric.retrieval import RetrievalHit


def test_build_evidence_package() -> None:
    fused_hits = [
        HybridHit(
            hit=RetrievalHit(
                chunk_id=10,
                document_id=99,
                document_uri="memory://doc-99",
                chunk_index=0,
                chunk_text="evidence text",
                score=0.8,
                source="lexical",
                metadata={"section": "intro"},
            ),
            fused_score=0.123,
            sources=["lexical", "vector"],
        )
    ]

    package = build_evidence_package("query", fused_hits)
    serialized = package.to_dict()

    assert package.query_text == "query"
    assert serialized["retrieval_summary"]["total_items"] == 1
    assert serialized["items"][0]["chunk_id"] == 10
    assert serialized["items"][0]["retrieval_sources"] == ["lexical", "vector"]


def test_format_citations_and_citation_source() -> None:
    fused_hits = [
        HybridHit(
            hit=RetrievalHit(
                chunk_id=1,
                document_id=10,
                document_uri="memory://architecture.md",
                chunk_index=0,
                chunk_text="Hybrid RRF merges lexical and vector rankings.",
                score=0.9,
                source="hybrid",
                metadata={"heading_path": "Architecture > Retrieval"},
            ),
            fused_score=0.032,
            sources=["lexical", "vector"],
        )
    ]
    package = build_evidence_package("fusion", fused_hits)

    item = package.items[0]
    assert item.citation_source == "memory://architecture.md#Architecture > Retrieval"

    citations = package.format_citations()
    assert "[1] memory://architecture.md (Architecture > Retrieval)" in citations
    assert "Hybrid RRF merges lexical and vector rankings." in citations

    empty_package = build_evidence_package("empty", [])
    assert empty_package.format_citations() == "No citations available."

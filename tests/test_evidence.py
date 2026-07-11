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

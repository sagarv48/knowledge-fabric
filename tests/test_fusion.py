from knowledge_fabric.fusion import reciprocal_rank_fusion
from knowledge_fabric.retrieval import RetrievalHit


def _hit(chunk_id: int, score: float, source: str) -> RetrievalHit:
    return RetrievalHit(
        chunk_id=chunk_id,
        document_id=1,
        document_uri="memory://doc",
        chunk_index=chunk_id,
        chunk_text=f"chunk {chunk_id}",
        score=score,
        source=source,
        metadata={},
    )


def test_rrf_fuses_hits_from_both_sources() -> None:
    lexical = [_hit(1, 0.9, "lexical"), _hit(2, 0.8, "lexical")]
    vector = [_hit(2, 0.7, "vector"), _hit(3, 0.6, "vector")]

    fused = reciprocal_rank_fusion(lexical, vector, k=60)

    assert [hit.hit.chunk_id for hit in fused] == [2, 1, 3]
    by_chunk = {entry.hit.chunk_id: entry for entry in fused}
    assert sorted(by_chunk[2].sources) == ["lexical", "vector"]

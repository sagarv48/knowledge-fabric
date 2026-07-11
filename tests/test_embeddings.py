from knowledge_fabric.embeddings import MockEmbeddingProvider


def test_mock_embeddings_are_deterministic() -> None:
    provider = MockEmbeddingProvider(_dimension=8)
    first = provider.embed_texts(["hello world"])[0]
    second = provider.embed_texts(["hello world"])[0]
    other = provider.embed_texts(["other"])[0]

    assert first == second
    assert first != other
    assert len(first) == 8


def test_mock_provider_dimension_property() -> None:
    provider = MockEmbeddingProvider(_dimension=32)
    assert provider.dimension == 32

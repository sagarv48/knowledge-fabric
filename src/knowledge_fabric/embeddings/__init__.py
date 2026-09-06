"""Embedding provider abstraction."""

from knowledge_fabric.embeddings.providers import (
    EmbeddingProvider,
    MockEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAIEmbeddingProvider,
    CohereEmbeddingProvider,
    build_embedding_provider,
)

__all__ = [
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "CohereEmbeddingProvider",
    "build_embedding_provider",
]

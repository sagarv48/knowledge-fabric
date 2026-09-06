"""Embedding provider abstraction."""

from knowledge_fabric.embeddings.providers import (
    CohereEmbeddingProvider,
    EmbeddingProvider,
    MockEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAIEmbeddingProvider,
    build_embedding_provider,
)

__all__ = [
    "CohereEmbeddingProvider",
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "build_embedding_provider",
]

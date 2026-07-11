"""Embedding provider interfaces and mock implementation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for text-to-vector providers."""

    @property
    def dimension(self) -> int:  # pragma: no cover - interface contract
        """Return embedding vector dimension."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - interface contract
        """Generate embeddings for input texts."""


@dataclass(slots=True)
class MockEmbeddingProvider:
    """Deterministic provider for local development and tests."""

    _dimension: int = 1536

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = []
        for index in range(self._dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

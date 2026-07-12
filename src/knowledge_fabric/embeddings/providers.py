"""Embedding provider interfaces and real implementations."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for text-to-vector providers."""

    @property
    def dimension(self) -> int:  # pragma: no cover
        """Return embedding vector dimension."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover
        """Generate embeddings for input texts."""


@dataclass(slots=True)
class MockEmbeddingProvider:
    """Deterministic provider for local development and tests. NOT for production."""

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


@dataclass(slots=True)
class OllamaEmbeddingProvider:
    """Calls a local Ollama server for real embeddings.

    Prerequisites:
        brew install ollama   # or download from ollama.com
        ollama serve
        ollama pull nomic-embed-text   # 768-dim, fast, free

    Environment variables:
        OLLAMA_BASE_URL   default: http://localhost:11434
        OLLAMA_EMBED_MODEL  default: nomic-embed-text
    """

    _model: str
    _base_url: str
    _dimension: int

    @classmethod
    def from_env(cls) -> "OllamaEmbeddingProvider":
        model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        # nomic-embed-text = 768d; mxbai-embed-large = 1024d; all-minilm = 384d
        dim_by_model: dict[str, int] = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
        }
        dimension = dim_by_model.get(model, 768)
        return cls(_model=model, _base_url=base_url.rstrip("/"), _dimension=dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        body = json.dumps({"model": self._model, "prompt": text}).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/api/embeddings",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["embedding"]


@dataclass(slots=True)
class OpenAIEmbeddingProvider:
    """Calls the OpenAI embeddings API.

    Prerequisites:
        pip install openai   # or add to pyproject.toml dependencies

    Environment variables (required):
        OPENAI_API_KEY
        OPENAI_EMBED_MODEL  default: text-embedding-3-small  (1536d)
    """

    _model: str
    _api_key: str
    _dimension: int

    @classmethod
    def from_env(cls) -> "OpenAIEmbeddingProvider":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable is required")
        model = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        dim_by_model: dict[str, int] = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        dimension = dim_by_model.get(model, 1536)
        return cls(_model=model, _api_key=api_key, _dimension=dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({"model": self._model, "input": texts}).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/embeddings",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return [item["embedding"] for item in result["data"]]


def build_embedding_provider(provider_name: str = "", dimension: int = 768) -> EmbeddingProvider:
    """Factory that reads EMBEDDING_PROVIDER env var and returns the right provider.

    EMBEDDING_PROVIDER=mock     → MockEmbeddingProvider (default, dev only)
    EMBEDDING_PROVIDER=ollama   → OllamaEmbeddingProvider.from_env()
    EMBEDDING_PROVIDER=openai   → OpenAIEmbeddingProvider.from_env()
    """
    name = (provider_name or os.environ.get("EMBEDDING_PROVIDER", "mock")).lower().strip()
    if name == "ollama":
        return OllamaEmbeddingProvider.from_env()
    if name == "openai":
        return OpenAIEmbeddingProvider.from_env()
    return MockEmbeddingProvider(_dimension=dimension)


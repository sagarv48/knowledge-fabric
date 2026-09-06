"""Persistence helpers for documents and chunks."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from knowledge_fabric.ingestion.models import Chunk, Document

ConnectionFactory = Callable[[], Any]


class KnowledgeRepository:
    """Repository for storing ingested documents and chunks in PostgreSQL."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def upsert_document(self, document: Document, *, tenant_id: str = "default") -> int:
        """Insert or update a document and return its database id."""
        connection = self._connection_factory()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (source_uri, source_type, title, metadata, content_text, tenant_id)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (source_uri)
                DO UPDATE SET
                  source_type = EXCLUDED.source_type,
                  title = EXCLUDED.title,
                  metadata = EXCLUDED.metadata,
                  content_text = EXCLUDED.content_text,
                  tenant_id = EXCLUDED.tenant_id,
                  updated_at = NOW()
                RETURNING id
                """,
                [
                    document.source_uri,
                    document.source_format.value,
                    document.title,
                    _to_json(document.metadata),
                    document.content_text,
                    tenant_id,
                ],
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("Failed to upsert document")
            if hasattr(connection, "commit"):
                connection.commit()
            return int(row[0])

    def replace_chunks(
        self,
        *,
        document_id: int,
        chunks: list[Chunk],
        embeddings: list[list[float]] | None = None,
        tenant_id: str = "default",
    ) -> int:
        """Replace chunks for one document and return inserted chunk count."""
        if embeddings is not None and len(embeddings) != len(chunks):
            raise ValueError("embeddings length must match chunks length")

        connection = self._connection_factory()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM chunks WHERE document_id = %s", [document_id])

            for index, chunk in enumerate(chunks):
                embedding_literal = None
                if embeddings is not None:
                    embedding_literal = _vector_literal(embeddings[index])

                cursor.execute(
                    """
                    INSERT INTO chunks (document_id, chunk_index, chunk_text, metadata, embedding, tenant_id)
                    VALUES (%s, %s, %s, %s::jsonb, %s::vector, %s)
                    """,
                    [
                        document_id,
                        chunk.chunk_index,
                        chunk.chunk_text,
                        _to_json(chunk.metadata),
                        embedding_literal,
                        tenant_id,
                    ],
                )

            if hasattr(connection, "commit"):
                connection.commit()
        return len(chunks)


def _to_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _vector_literal(values: list[float]) -> str:
    if not values:
        raise ValueError("embedding vector must not be empty")
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

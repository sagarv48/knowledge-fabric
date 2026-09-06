from __future__ import annotations

from typing import Any

import pytest

from knowledge_fabric.db.repository import KnowledgeRepository
from knowledge_fabric.ingestion.models import Chunk, Document, SourceFormat


class _FakeCursor:
    def __init__(self, fetch_rows: list[tuple[Any, ...]] | None = None) -> None:
        self.fetch_rows = fetch_rows or [(101,)]
        self.executions: list[tuple[str, list[Any]]] = []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return

    def execute(self, sql: str, params: list[Any]) -> None:
        self.executions.append((sql, params))

    def fetchone(self) -> tuple[Any, ...] | None:
        if not self.fetch_rows:
            return None
        return self.fetch_rows.pop(0)


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.commit_calls = 0

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_calls += 1


def test_upsert_document_returns_id() -> None:
    cursor = _FakeCursor(fetch_rows=[(77,)])
    connection = _FakeConnection(cursor)
    repository = KnowledgeRepository(connection_factory=lambda: connection)

    document = Document(
        source_uri="memory://doc",
        source_format=SourceFormat.TXT,
        content_text="hello",
        title="doc",
        metadata={"k": "v"},
    )
    document_id = repository.upsert_document(document)

    assert document_id == 77
    assert "INSERT INTO documents" in cursor.executions[0][0]
    assert connection.commit_calls == 1


def test_replace_chunks_writes_all_chunks() -> None:
    cursor = _FakeCursor()
    connection = _FakeConnection(cursor)
    repository = KnowledgeRepository(connection_factory=lambda: connection)

    chunks = [
        Chunk(document_uri="memory://doc", chunk_index=0, chunk_text="a", metadata={}),
        Chunk(document_uri="memory://doc", chunk_index=1, chunk_text="b", metadata={}),
    ]
    inserted = repository.replace_chunks(document_id=1, chunks=chunks)

    assert inserted == 2
    assert "DELETE FROM chunks" in cursor.executions[0][0]
    assert len(cursor.executions) == 3
    assert connection.commit_calls == 1


def test_replace_chunks_validates_embedding_count() -> None:
    cursor = _FakeCursor()
    connection = _FakeConnection(cursor)
    repository = KnowledgeRepository(connection_factory=lambda: connection)
    chunks = [Chunk(document_uri="memory://doc", chunk_index=0, chunk_text="a", metadata={})]

    with pytest.raises(ValueError, match="embeddings length must match chunks length"):
        repository.replace_chunks(document_id=1, chunks=chunks, embeddings=[[0.1], [0.2]])


def test_upsert_document_with_tenant_id() -> None:
    cursor = _FakeCursor(fetch_rows=[(88,)])
    connection = _FakeConnection(cursor)
    repository = KnowledgeRepository(connection_factory=lambda: connection)

    document = Document(
        source_uri="memory://tenant_doc",
        source_format=SourceFormat.TXT,
        content_text="tenant data",
        title="tenant doc",
        metadata={},
    )
    doc_id = repository.upsert_document(document, tenant_id="tenant-alpha")
    assert doc_id == 88
    # Last param in INSERT is tenant_id
    params = cursor.executions[0][1]
    assert params[-1] == "tenant-alpha"


def test_replace_chunks_with_tenant_id() -> None:
    cursor = _FakeCursor()
    connection = _FakeConnection(cursor)
    repository = KnowledgeRepository(connection_factory=lambda: connection)

    chunks = [Chunk(document_uri="memory://doc", chunk_index=0, chunk_text="a", metadata={})]
    repository.replace_chunks(document_id=1, chunks=chunks, tenant_id="tenant-beta")

    # The chunk INSERT is execution index 1
    insert_params = cursor.executions[1][1]
    assert insert_params[-1] == "tenant-beta"


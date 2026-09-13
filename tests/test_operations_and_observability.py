from __future__ import annotations

from typing import Any

import pytest

from knowledge_fabric.db.repository import KnowledgeRepository
from knowledge_fabric.embeddings import MockEmbeddingProvider
from knowledge_fabric.mcp.server import create_mcp_server
from knowledge_fabric.mcp.tools import KnowledgeFabricMCPTools
from knowledge_fabric.retrieval.pipeline import RetrievalPipeline
from knowledge_fabric.retrieval.postgres import PostgresRetrievalStore


class _MockCursor:
    def __init__(
        self,
        fetchone_results: list[tuple[Any, ...] | None] | None = None,
        fetchall_results: list[list[tuple[Any, ...]]] | None = None,
        rowcount: int = 1,
    ) -> None:
        self.fetchone_results = fetchone_results or []
        self.fetchall_results = fetchall_results or []
        self.executions: list[tuple[str, list[Any]]] = []
        self.rowcount = rowcount

    def __enter__(self) -> _MockCursor:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return

    def execute(self, sql: str, params: list[Any] | None = None) -> None:
        self.executions.append((sql, params or []))

    def fetchone(self) -> tuple[Any, ...] | None:
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self) -> list[tuple[Any, ...]] | None:
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []


class _MockConnection:
    def __init__(self, cursor: _MockCursor) -> None:
        self._cursor = cursor
        self.commit_calls = 0

    def cursor(self) -> _MockCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_calls += 1


def test_repository_get_chunk_found() -> None:
    row = (101, 12, "doc://guide.md", "markdown", "Guide Title", 0, "Chunk text content", {"k": "v"}, "tenant-a")
    cursor = _MockCursor(fetchone_results=[row])
    repo = KnowledgeRepository(lambda: _MockConnection(cursor))

    chunk = repo.get_chunk(101, tenant_id="tenant-a")
    assert chunk is not None
    assert chunk["chunk_id"] == 101
    assert chunk["document_id"] == 12
    assert chunk["document_uri"] == "doc://guide.md"
    assert chunk["chunk_text"] == "Chunk text content"
    assert chunk["tenant_id"] == "tenant-a"


def test_repository_get_chunk_not_found() -> None:
    cursor = _MockCursor(fetchone_results=[None])
    repo = KnowledgeRepository(lambda: _MockConnection(cursor))

    chunk = repo.get_chunk(999, tenant_id="tenant-a")
    assert chunk is None


def test_repository_get_index_status() -> None:
    cursor = _MockCursor(
        fetchone_results=[(10,), (45,)],  # docs count, chunks count
        fetchall_results=[
            [("markdown", 8, 35, "2026-09-13T10:00:00"), ("python", 2, 10, "2026-09-13T11:00:00")]
        ],
    )
    repo = KnowledgeRepository(lambda: _MockConnection(cursor))

    status = repo.get_index_status(tenant_id="tenant-a")
    assert status["tenant_id"] == "tenant-a"
    assert status["total_documents"] == 10
    assert status["total_chunks"] == 45
    assert len(status["sources"]) == 2
    assert status["sources"][0]["source_type"] == "markdown"
    assert status["storage_backend"] == "postgres"


def test_repository_check_consistency_healthy() -> None:
    # 0 orphans, 0 empty docs, 0 null tenants, 0 null embeddings
    cursor = _MockCursor(
        fetchone_results=[(0,), (0,), (0,), (0,)]
    )
    repo = KnowledgeRepository(lambda: _MockConnection(cursor))

    check = repo.check_consistency(tenant_id="tenant-a")
    assert check["is_healthy"] is True
    assert check["orphaned_chunks"] == 0
    assert check["null_tenant_documents"] == 0


def test_repository_check_consistency_unhealthy() -> None:
    # 3 orphans, 1 empty doc, 2 null tenants, 0 null embeddings
    cursor = _MockCursor(
        fetchone_results=[(3,), (1,), (2,), (0,)]
    )
    repo = KnowledgeRepository(lambda: _MockConnection(cursor))

    check = repo.check_consistency(tenant_id="tenant-a")
    assert check["is_healthy"] is False
    assert check["orphaned_chunks"] == 3
    assert check["null_tenant_documents"] == 2


def test_repository_reembed_chunks() -> None:
    chunks_rows = [
        (1, "first chunk"),
        (2, "second chunk"),
    ]
    cursor = _MockCursor(
        fetchall_results=[chunks_rows]
    )
    conn = _MockConnection(cursor)
    repo = KnowledgeRepository(lambda: conn)
    provider = MockEmbeddingProvider(_dimension=8)

    summary = repo.reembed_chunks(embedding_provider=provider, tenant_id="tenant-a")
    assert summary["chunks_reembedded"] == 2
    assert summary["dimension"] == 8
    assert conn.commit_calls > 0


def test_mcp_tools_and_server_operations() -> None:
    row = (101, 12, "doc://guide.md", "markdown", "Guide Title", 0, "Chunk text content", {"k": "v"}, "tenant-a")
    cursor = _MockCursor(
        fetchone_results=[
            row,  # for get_chunk
            (5,), (20,),  # for get_index_status
            (0,), (0,), (0,), (0,),  # for check_consistency
        ],
        fetchall_results=[
            [("markdown", 5, 20, "2026-09-13T10:00:00")]  # sources for get_index_status
        ],
    )
    store = PostgresRetrievalStore(lambda: _MockConnection(cursor))
    provider = MockEmbeddingProvider(_dimension=8)
    pipeline = RetrievalPipeline(retrieval_store=store, embedding_provider=provider)

    tools = KnowledgeFabricMCPTools(
        retrieval_pipeline=pipeline,
        retrieval_store=store,
        embedding_provider=provider,
    )

    # 1. get_evidence
    evidence = tools.get_evidence(101, tenant_id="tenant-a")
    assert evidence is not None
    assert evidence["chunk_id"] == 101

    # 2. get_index_status
    idx_status = tools.get_index_status(tenant_id="tenant-a")
    assert idx_status["total_documents"] == 5
    assert idx_status["total_chunks"] == 20

    # 3. check_consistency
    cons = tools.check_consistency(tenant_id="tenant-a")
    assert cons["is_healthy"] is True

    # 4. create_mcp_server has all tools registered
    server = create_mcp_server(tools)
    tool_names = [t.name for t in server._tool_manager.list_tools()]
    assert "get_index_status" in tool_names
    assert "get_evidence" in tool_names
    assert "check_consistency" in tool_names

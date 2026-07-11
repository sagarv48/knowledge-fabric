from __future__ import annotations

from typing import Any

import pytest

from knowledge_fabric.retrieval import PostgresRetrievalStore


class _FakeCursor:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows
        self.executed_sql = ""
        self.executed_params: list[Any] = []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return

    def execute(self, sql: str, params: list[Any]) -> None:
        self.executed_sql = sql
        self.executed_params = params

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _FakeCursor:
        return self._cursor


def test_lexical_search_executes_fts_sql() -> None:
    cursor = _FakeCursor(
        rows=[
            (1, 2, "memory://doc", 0, "chunk text", {"a": 1}, 0.51),
        ]
    )
    store = PostgresRetrievalStore(connection_factory=lambda: _FakeConnection(cursor))

    hits = store.lexical_search("security docs", top_k=5, source_type="markdown")

    assert len(hits) == 1
    assert "websearch_to_tsquery" in cursor.executed_sql
    assert "d.source_type = %s" in cursor.executed_sql
    assert cursor.executed_params[-1] == 5
    assert hits[0].source == "lexical"


def test_vector_search_uses_pgvector_distance() -> None:
    cursor = _FakeCursor(
        rows=[
            (3, 4, "memory://doc-2", 1, "chunk", {}, 0.78),
        ]
    )
    store = PostgresRetrievalStore(connection_factory=lambda: _FakeConnection(cursor))

    hits = store.vector_search([0.1, -0.2, 0.3], top_k=3)

    assert len(hits) == 1
    assert "<=>" in cursor.executed_sql
    assert cursor.executed_params[-1] == 3
    assert hits[0].source == "vector"


def test_vector_search_requires_non_empty_embedding() -> None:
    store = PostgresRetrievalStore(connection_factory=lambda: _FakeConnection(_FakeCursor([])))
    with pytest.raises(ValueError, match="must not be empty"):
        store.vector_search([])

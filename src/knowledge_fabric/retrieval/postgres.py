"""PostgreSQL-backed lexical and vector retrieval."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from knowledge_fabric.retrieval.models import RetrievalHit

ConnectionFactory = Callable[[], Any]


class PostgresRetrievalStore:
    """Runs retrieval queries against PostgreSQL + pgvector."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def lexical_search(
        self,
        query_text: str,
        top_k: int = 10,
        source_type: str | None = None,
        tenant_id: str | None = None,
    ) -> list[RetrievalHit]:
        where_clause, params = self._filter_clause(source_type=source_type, tenant_id=tenant_id)
        sql = f"""
            SELECT
              c.id,
              c.document_id,
              d.source_uri,
              c.chunk_index,
              c.chunk_text,
              c.metadata,
              ts_rank_cd(c.search_tsv, websearch_to_tsquery('english', %s)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.search_tsv @@ websearch_to_tsquery('english', %s)
              {where_clause}
            ORDER BY score DESC, c.id ASC
            LIMIT %s
        """
        query_params = [query_text, query_text, *params, top_k]
        rows = self._fetch_rows(sql, query_params, tenant_id=tenant_id)
        return self._rows_to_hits(rows, source="lexical")

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        source_type: str | None = None,
        tenant_id: str | None = None,
    ) -> list[RetrievalHit]:
        where_clause, params = self._filter_clause(source_type=source_type, tenant_id=tenant_id)
        sql = f"""
            SELECT
              c.id,
              c.document_id,
              d.source_uri,
              c.chunk_index,
              c.chunk_text,
              c.metadata,
              1 - (c.embedding <=> %s::vector) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
              {where_clause}
            ORDER BY c.embedding <=> %s::vector ASC, c.id ASC
            LIMIT %s
        """
        vector_literal = self._vector_literal(query_embedding)
        query_params = [vector_literal, *params, vector_literal, top_k]
        rows = self._fetch_rows(sql, query_params, tenant_id=tenant_id)
        return self._rows_to_hits(rows, source="vector")

    def get_document(
        self,
        *,
        document_id: int | None = None,
        source_uri: str | None = None,
    ) -> dict[str, Any] | None:
        """Fetch one document by id or source URI."""
        if document_id is None and source_uri is None:
            raise ValueError("document_id or source_uri must be provided")

        if document_id is not None:
            sql = """
                SELECT id, source_uri, source_type, title, metadata, content_text, created_at, updated_at
                FROM documents
                WHERE id = %s
                LIMIT 1
            """
            params = [document_id]
        else:
            sql = """
                SELECT id, source_uri, source_type, title, metadata, content_text, created_at, updated_at
                FROM documents
                WHERE source_uri = %s
                LIMIT 1
            """
            params = [source_uri]

        rows = self._fetch_rows(sql, params)
        if not rows:
            return None

        row = rows[0]
        return {
            "id": int(row[0]),
            "source_uri": str(row[1]),
            "source_type": str(row[2]),
            "title": row[3],
            "metadata": dict(row[4] or {}),
            "content_text": str(row[5]),
            "created_at": row[6],
            "updated_at": row[7],
        }

    @staticmethod
    def _filter_clause(
        source_type: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if source_type is not None:
            clauses.append("AND d.source_type = %s")
            params.append(source_type)
        if tenant_id is not None:
            # Application-level tenant filter (Mode 1 — always active when tenant_id set)
            clauses.append("AND d.tenant_id = %s")
            params.append(tenant_id)
        return " ".join(clauses), params

    @staticmethod
    def _vector_literal(values: list[float]) -> str:
        if not values:
            raise ValueError("query_embedding must not be empty")
        return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

    def _fetch_rows(
        self,
        sql: str,
        params: list[Any],
        tenant_id: str | None = None,
    ) -> list[tuple[Any, ...]]:
        connection = self._connection_factory()
        with connection.cursor() as cursor:
            # Mode 2 (RLS): set session variable so Postgres RLS policies fire.
            # This is a no-op if RLS is not enabled on the table.
            if tenant_id is not None:
                cursor.execute("SET LOCAL app.tenant_id = %s", [tenant_id])
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return rows

    @staticmethod
    def _rows_to_hits(rows: list[tuple[Any, ...]], source: str) -> list[RetrievalHit]:
        hits: list[RetrievalHit] = []
        for row in rows:
            hits.append(
                RetrievalHit(
                    chunk_id=int(row[0]),
                    document_id=int(row[1]),
                    document_uri=str(row[2]),
                    chunk_index=int(row[3]),
                    chunk_text=str(row[4]),
                    metadata=dict(row[5] or {}),
                    score=float(row[6]),
                    source=source,
                )
            )
        return hits

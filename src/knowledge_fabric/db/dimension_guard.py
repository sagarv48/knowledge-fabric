"""Embedding dimension validation guard and migration helpers."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DimensionMismatchError(Exception):
    """Raised when the database vector dimension does not match the embedding provider."""

    def __init__(
        self,
        db_dimension: int,
        provider_dimension: int,
        provider_name: str,
    ) -> None:
        message = (
            f"\n\n\u274c Vector Dimension Mismatch Detected:\n"
            f"   - Database expected dimension: {db_dimension}\n"
            f"   - Provider '{provider_name}' dimension: {provider_dimension}\n\n"
            f"This occurs when switching embedding models (e.g. from Ollama 768 to OpenAI 1536).\n"
            f"To resolve:\n"
            f"  1. In PostgreSQL, run:\n"
            f"       SELECT set_embedding_dimension({provider_dimension});\n"
            f"  2. Or re-ingest your documents with the new provider:\n"
            f"       knowledge-fabric-ingest --path sources/ --recursive --embed\n"
        )
        super().__init__(message)
        self.db_dimension = db_dimension
        self.provider_dimension = provider_dimension
        self.provider_name = provider_name


def check_embedding_dimension(
    connection: Any,
    provider_dimension: int,
    provider_name: str = "unknown",
) -> None:
    """Validate that the database chunks.embedding column matches provider dimension.

    Raises DimensionMismatchError if a mismatch is found.
    If the database is uninitialized or table doesn't exist yet, passes silently.
    """
    try:
        with connection.cursor() as cursor:
            # 1. Check schema_metadata first if available
            cursor.execute(
                """
                SELECT value FROM schema_metadata WHERE key = 'embedding_dimension'
                """
            )
            row = cursor.fetchone()
            if row and row[0]:
                stored_dim = int(row[0])
                if stored_dim != provider_dimension:
                    raise DimensionMismatchError(
                        db_dimension=stored_dim,
                        provider_dimension=provider_dimension,
                        provider_name=provider_name,
                    )
                return

            # 2. Fallback: inspect atttypmod for chunks.embedding column
            cursor.execute(
                """
                SELECT atttypmod
                FROM pg_attribute
                WHERE attrelid = 'chunks'::regclass
                  AND attname = 'embedding'
                  AND NOT attisdropped;
                """
            )
            row = cursor.fetchone()
            if row and row[0] and row[0] > 0:
                stored_dim = int(row[0])
                if stored_dim != provider_dimension:
                    raise DimensionMismatchError(
                        db_dimension=stored_dim,
                        provider_dimension=provider_dimension,
                        provider_name=provider_name,
                    )
    except DimensionMismatchError:
        raise
    except Exception as exc:
        # If relation doesn't exist or table not created yet, log and pass
        logger.debug("Dimension check skipped (table or extension not yet created): %s", exc)

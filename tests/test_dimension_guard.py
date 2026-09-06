"""Tests for the embedding dimension migration guard."""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from knowledge_fabric.db.dimension_guard import (
    DimensionMismatchError,
    check_embedding_dimension,
)


def test_dimension_mismatch_error_format() -> None:
    error = DimensionMismatchError(
        db_dimension=1536,
        provider_dimension=768,
        provider_name="OllamaEmbeddingProvider",
    )
    message = str(error)
    assert "Vector Dimension Mismatch Detected" in message
    assert "1536" in message
    assert "768" in message
    assert "OllamaEmbeddingProvider" in message
    assert "SELECT set_embedding_dimension(768);" in message


def test_check_embedding_dimension_matching() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # schema_metadata query returns '768'
    mock_cursor.fetchone.return_value = ("768",)

    # Should not raise
    check_embedding_dimension(mock_conn, provider_dimension=768, provider_name="Ollama")


def test_check_embedding_dimension_mismatch_raises() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # schema_metadata query returns '1536'
    mock_cursor.fetchone.return_value = ("1536",)

    with pytest.raises(DimensionMismatchError) as exc_info:
        check_embedding_dimension(mock_conn, provider_dimension=768, provider_name="Ollama")

    assert exc_info.value.db_dimension == 1536
    assert exc_info.value.provider_dimension == 768
    assert exc_info.value.provider_name == "Ollama"


def test_check_embedding_dimension_atttypmod_fallback() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    # First query (schema_metadata) returns None, second query (atttypmod) returns 1024
    mock_cursor.fetchone.side_effect = [None, (1024,)]

    # Matches 1024 -> no error
    check_embedding_dimension(mock_conn, provider_dimension=1024, provider_name="Cohere")

    # Mismatch with atttypmod
    mock_cursor.fetchone.side_effect = [None, (1536,)]
    with pytest.raises(DimensionMismatchError):
        check_embedding_dimension(mock_conn, provider_dimension=1024, provider_name="Cohere")


def test_check_embedding_dimension_passes_on_uninitialized_db() -> None:
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = RuntimeError("relation 'schema_metadata' does not exist")

    # Should gracefully pass when tables are not yet initialized
    check_embedding_dimension(mock_conn, provider_dimension=768, provider_name="Ollama")

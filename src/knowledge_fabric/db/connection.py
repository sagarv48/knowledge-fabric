"""Database connection helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from knowledge_fabric.config import DatabaseSettings

ConnectionFactory = Callable[[], Any]


def create_postgres_connection_factory(settings: DatabaseSettings) -> ConnectionFactory:
    """Create a lazy psycopg connection factory from database settings."""

    def _connect() -> Any:
        import psycopg

        return psycopg.connect(
            host=settings.host,
            port=settings.port,
            dbname=settings.name,
            user=settings.user,
            password=settings.password,
            autocommit=False,
        )

    return _connect

"""Database access and schema bootstrap."""

from knowledge_fabric.db.audit import AuditLogger
from knowledge_fabric.db.connection import create_postgres_connection_factory
from knowledge_fabric.db.dimension_guard import DimensionMismatchError, check_embedding_dimension
from knowledge_fabric.db.repository import KnowledgeRepository

__all__ = [
    "AuditLogger",
    "KnowledgeRepository",
    "create_postgres_connection_factory",
    "DimensionMismatchError",
    "check_embedding_dimension",
]

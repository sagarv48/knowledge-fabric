"""Data models for ingestion and chunking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SourceFormat(StrEnum):
    """Supported source formats for ingestion."""

    MARKDOWN = "markdown"
    TXT = "txt"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"


@dataclass(slots=True)
class Document:
    """Canonical ingested document."""

    source_uri: str
    source_format: SourceFormat
    content_text: str
    metadata: dict[str, object] = field(default_factory=dict)
    title: str | None = None
    ingested_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Chunk:
    """Canonical chunk representation."""

    document_uri: str
    chunk_index: int
    chunk_text: str
    metadata: dict[str, object] = field(default_factory=dict)

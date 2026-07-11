from __future__ import annotations

from knowledge_fabric.chunking import DocumentChunkingService
from knowledge_fabric.ingestion.models import Document, SourceFormat


def test_markdown_chunking_is_heading_aware() -> None:
    document = Document(
        source_uri="memory://markdown",
        source_format=SourceFormat.MARKDOWN,
        content_text="# Intro\nIntro body\n\n## Details\nDetails body",
        metadata={},
    )
    service = DocumentChunkingService(max_chars=200, overlap_chars=20)

    chunks = service.chunk_document(document)

    assert len(chunks) == 2
    assert chunks[0].metadata["heading"] == "Intro"
    assert chunks[1].metadata["heading"] == "Details"
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_fallback_chunking_splits_long_plain_text() -> None:
    document = Document(
        source_uri="memory://txt",
        source_format=SourceFormat.TXT,
        content_text="A" * 260,
        metadata={},
    )
    service = DocumentChunkingService(max_chars=100, overlap_chars=20)

    chunks = service.chunk_document(document)

    assert len(chunks) >= 3
    assert all(len(chunk.chunk_text) <= 100 for chunk in chunks)
    assert all(chunk.metadata["strategy"] == "fallback_window" for chunk in chunks)


def test_markdown_falls_back_when_no_headings() -> None:
    document = Document(
        source_uri="memory://markdown-no-headings",
        source_format=SourceFormat.MARKDOWN,
        content_text="Simple markdown text without heading markers.",
        metadata={},
    )
    service = DocumentChunkingService(max_chars=20, overlap_chars=5)

    chunks = service.chunk_document(document)

    assert len(chunks) > 1
    assert all(chunk.metadata["strategy"] == "fallback_window" for chunk in chunks)

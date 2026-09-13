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


def test_markdown_chunking_heading_hierarchy_breadcrumbs() -> None:
    content = (
        "# Architecture\n"
        "High-level system design.\n\n"
        "## Retrieval\n"
        "Hybrid search architecture.\n\n"
        "### RRF Fusion\n"
        "Reciprocal rank fusion details."
    )
    document = Document(
        source_uri="memory://nested-headings.md",
        source_format=SourceFormat.MARKDOWN,
        content_text=content,
        metadata={},
    )
    service = DocumentChunkingService(max_chars=500, overlap_chars=20)
    chunks = service.chunk_document(document)

    assert len(chunks) == 3
    assert chunks[0].heading_path == "Architecture"
    assert chunks[0].heading_level == 1
    assert chunks[0].metadata["heading_path"] == "Architecture"

    assert chunks[1].heading_path == "Architecture > Retrieval"
    assert chunks[1].heading_level == 2
    assert chunks[1].metadata["heading_path"] == "Architecture > Retrieval"

    assert chunks[2].heading_path == "Architecture > Retrieval > RRF Fusion"
    assert chunks[2].heading_level == 3
    assert chunks[2].metadata["heading_path"] == "Architecture > Retrieval > RRF Fusion"


def test_markdown_chunking_preserves_code_blocks_atomically() -> None:
    code_block = "```python\ndef calculate_rrf(rank_dense: int, rank_lexical: int) -> float:\n    k = 60\n    return (1.0 / (k + rank_dense)) + (1.0 / (k + rank_lexical))\n```"
    content = f"# Algorithm\nHere is the fusion implementation:\n\n{code_block}\n\nThis completes the algorithm description."
    document = Document(
        source_uri="memory://code-atomic.md",
        source_format=SourceFormat.MARKDOWN,
        content_text=content,
        metadata={},
    )
    service = DocumentChunkingService(max_chars=300, overlap_chars=20)
    chunks = service.chunk_document(document)

    code_chunks = [c for c in chunks if "def calculate_rrf" in c.chunk_text]
    assert len(code_chunks) == 1
    assert "```python" in code_chunks[0].chunk_text
    assert "```" in code_chunks[0].chunk_text


def test_markdown_chunking_preserves_tables_atomically() -> None:
    table = "| Parameter | Default | Description |\n|---|---|---|\n| alpha | 0.5 | Dense weight |\n| k | 60 | RRF smoothing constant |"
    content = f"# Configuration\nSettings table:\n\n{table}\n\nNext section notes."
    document = Document(
        source_uri="memory://table-atomic.md",
        source_format=SourceFormat.MARKDOWN,
        content_text=content,
        metadata={},
    )
    service = DocumentChunkingService(max_chars=300, overlap_chars=20)
    chunks = service.chunk_document(document)

    table_chunks = [c for c in chunks if "| alpha | 0.5 |" in c.chunk_text]
    assert len(table_chunks) == 1
    assert "| Parameter | Default | Description |" in table_chunks[0].chunk_text
    assert "| k | 60 | RRF smoothing constant |" in table_chunks[0].chunk_text


def test_chunk_offsets_and_content_hash() -> None:
    content = "# First Section\nParagraph alpha.\n\n# Second Section\nParagraph beta."
    document = Document(
        source_uri="memory://offsets.md",
        source_format=SourceFormat.MARKDOWN,
        content_text=content,
        metadata={},
    )
    service = DocumentChunkingService(max_chars=200, overlap_chars=20)
    chunks = service.chunk_document(document)

    assert len(chunks) == 2
    for chunk in chunks:
        assert chunk.start_offset >= 0
        assert chunk.end_offset > chunk.start_offset
        assert content[chunk.start_offset:chunk.end_offset] == chunk.chunk_text
        assert len(chunk.content_hash) == 64
        import hashlib
        expected_hash = hashlib.sha256(chunk.chunk_text.encode("utf-8")).hexdigest()
        assert chunk.content_hash == expected_hash
        assert chunk.metadata["content_hash"] == expected_hash


def test_page_aware_chunking_with_form_feeds() -> None:
    content = "Page 1 Content\nExecutive summary.\fPage 2 Content\nFinancial metrics.\fPage 3 Content\nAppendix."
    document = Document(
        source_uri="memory://report.pdf",
        source_format=SourceFormat.PDF,
        content_text=content,
        metadata={},
    )
    service = DocumentChunkingService(max_chars=200, overlap_chars=20)
    chunks = service.chunk_document(document)

    assert len(chunks) == 3
    assert chunks[0].metadata["strategy"] == "page_aware"
    assert chunks[0].metadata["page_number"] == 1
    assert "Page 1 Content" in chunks[0].chunk_text

    assert chunks[1].metadata["page_number"] == 2
    assert "Page 2 Content" in chunks[1].chunk_text

    assert chunks[2].metadata["page_number"] == 3
    assert "Page 3 Content" in chunks[2].chunk_text


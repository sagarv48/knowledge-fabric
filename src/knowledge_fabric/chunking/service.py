"""Chunking service for heading-aware and fallback chunking."""

from __future__ import annotations

import re

from knowledge_fabric.ingestion.models import Chunk, Document, SourceFormat

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


class DocumentChunkingService:
    """Split ingested documents into chunks."""

    def __init__(self, max_chars: int = 1200, overlap_chars: int = 150) -> None:
        if max_chars <= 0:
            raise ValueError("max_chars must be greater than 0")
        if overlap_chars < 0:
            raise ValueError("overlap_chars must be >= 0")
        if overlap_chars >= max_chars:
            raise ValueError("overlap_chars must be smaller than max_chars")
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    def chunk_document(self, document: Document) -> list[Chunk]:
        """Chunk document content with heading-aware markdown logic."""
        if document.source_format is SourceFormat.MARKDOWN:
            chunks = self._chunk_markdown_by_heading(document)
            if chunks:
                return chunks
        return self._chunk_fallback(document)

    def _chunk_markdown_by_heading(self, document: Document) -> list[Chunk]:
        text = document.content_text.strip()
        matches = list(_HEADING_PATTERN.finditer(text))
        if not matches:
            return []

        chunks: list[Chunk] = []
        chunk_index = 0

        for position, match in enumerate(matches):
            start = match.start()
            end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()

            if len(section_text) <= self._max_chars:
                chunks.append(
                    Chunk(
                        document_uri=document.source_uri,
                        chunk_index=chunk_index,
                        chunk_text=section_text,
                        metadata={
                            "heading": heading_text,
                            "heading_level": heading_level,
                        },
                    )
                )
                chunk_index += 1
                continue

            for split in self._split_with_overlap(section_text):
                chunks.append(
                    Chunk(
                        document_uri=document.source_uri,
                        chunk_index=chunk_index,
                        chunk_text=split,
                        metadata={
                            "heading": heading_text,
                            "heading_level": heading_level,
                            "split_from_heading_section": True,
                        },
                    )
                )
                chunk_index += 1

        return chunks

    def _chunk_fallback(self, document: Document) -> list[Chunk]:
        text = document.content_text.strip()
        splits = self._split_with_overlap(text)
        return [
            Chunk(
                document_uri=document.source_uri,
                chunk_index=index,
                chunk_text=chunk_text,
                metadata={"strategy": "fallback_window"},
            )
            for index, chunk_text in enumerate(splits)
        ]

    def _split_with_overlap(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self._max_chars:
            return [text]

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self._max_chars, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start = max(0, end - self._overlap_chars)
        return chunks

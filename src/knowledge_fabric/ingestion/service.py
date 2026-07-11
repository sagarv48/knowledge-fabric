"""Document ingestion service."""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path

from knowledge_fabric.ingestion.models import Document, SourceFormat
from knowledge_fabric.ingestion.tika_client import TikaClient

_TEXT_EXTENSIONS: dict[str, SourceFormat] = {
    ".md": SourceFormat.MARKDOWN,
    ".markdown": SourceFormat.MARKDOWN,
    ".txt": SourceFormat.TXT,
    ".html": SourceFormat.HTML,
    ".htm": SourceFormat.HTML,
}

_BINARY_EXTENSIONS: dict[str, SourceFormat] = {
    ".pdf": SourceFormat.PDF,
    ".docx": SourceFormat.DOCX,
    ".pptx": SourceFormat.PPTX,
}


class DocumentIngestionService:
    """Ingest source files into canonical `Document` models."""

    def __init__(self, tika_client: TikaClient) -> None:
        self._tika_client = tika_client

    def ingest_file(
        self,
        file_path: str | Path,
        source_metadata: dict[str, object] | None = None,
    ) -> Document:
        """Ingest one supported file and preserve source metadata."""
        resolved = Path(file_path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {resolved}")

        source_format = self._resolve_source_format(resolved.suffix.lower())
        if source_format in _TEXT_EXTENSIONS.values():
            content_text = self._extract_text_content(resolved, source_format)
        else:
            content_text = self._tika_client.extract_text(resolved)

        metadata = {
            "source_path": str(resolved),
            "file_name": resolved.name,
            "file_extension": resolved.suffix.lower(),
            "file_size_bytes": resolved.stat().st_size,
        }
        if source_metadata:
            metadata.update(source_metadata)

        return Document(
            source_uri=str(resolved),
            source_format=source_format,
            content_text=content_text.strip(),
            title=resolved.stem,
            metadata=metadata,
        )

    @staticmethod
    def _resolve_source_format(extension: str) -> SourceFormat:
        if extension in _TEXT_EXTENSIONS:
            return _TEXT_EXTENSIONS[extension]
        if extension in _BINARY_EXTENSIONS:
            return _BINARY_EXTENSIONS[extension]
        raise ValueError(f"Unsupported file extension: {extension}")

    @staticmethod
    def _extract_text_content(file_path: Path, source_format: SourceFormat) -> str:
        text = file_path.read_text(encoding="utf-8")
        if source_format is SourceFormat.HTML:
            return _strip_html(text)
        return text


def _strip_html(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw_html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

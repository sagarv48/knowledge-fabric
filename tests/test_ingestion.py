from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from knowledge_fabric.ingestion import DocumentIngestionService, SourceFormat, TikaClient


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return


def test_ingest_markdown_preserves_source_metadata(tmp_path: Path) -> None:
    input_file = tmp_path / "sample.md"
    input_file.write_text("# Title\n\nBody", encoding="utf-8")

    service = DocumentIngestionService(TikaClient(endpoint="http://localhost:9998"))
    document = service.ingest_file(input_file, source_metadata={"origin": "unit-test"})

    assert document.source_format is SourceFormat.MARKDOWN
    assert document.title == "sample"
    assert "Body" in document.content_text
    assert document.metadata["origin"] == "unit-test"
    assert document.metadata["file_name"] == "sample.md"
    assert document.metadata["file_extension"] == ".md"


def test_ingest_html_strips_tags(tmp_path: Path) -> None:
    input_file = tmp_path / "page.html"
    input_file.write_text("<html><body><h1>Heading</h1><p>Paragraph.</p></body></html>", encoding="utf-8")

    service = DocumentIngestionService(TikaClient(endpoint="http://localhost:9998"))
    document = service.ingest_file(input_file)

    assert document.source_format is SourceFormat.HTML
    assert "Heading" in document.content_text
    assert "<h1>" not in document.content_text


def test_ingest_txt(tmp_path: Path) -> None:
    input_file = tmp_path / "notes.txt"
    input_file.write_text("plain text", encoding="utf-8")

    service = DocumentIngestionService(TikaClient(endpoint="http://localhost:9998"))
    document = service.ingest_file(input_file)

    assert document.source_format is SourceFormat.TXT
    assert document.content_text == "plain text"


@pytest.mark.parametrize(
    ("name", "expected_format"),
    [
        ("report.pdf", SourceFormat.PDF),
        ("document.docx", SourceFormat.DOCX),
        ("slide.pptx", SourceFormat.PPTX),
    ],
)
def test_ingest_binary_uses_tika(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    expected_format: SourceFormat,
) -> None:
    input_file = tmp_path / name
    input_file.write_bytes(b"binary")

    captured: dict[str, Any] = {}

    def _fake_put(url: str, data: Any, headers: dict[str, str], timeout: int) -> _FakeResponse:
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse("Extracted from binary")

    monkeypatch.setattr("knowledge_fabric.ingestion.tika_client.requests.put", _fake_put)

    service = DocumentIngestionService(TikaClient(endpoint="http://localhost:9998", timeout_seconds=12))
    document = service.ingest_file(input_file)

    assert document.source_format is expected_format
    assert document.content_text == "Extracted from binary"
    assert captured["url"] == "http://localhost:9998/tika"
    assert captured["timeout"] == 12


def test_ingest_rejects_unsupported_extension(tmp_path: Path) -> None:
    input_file = tmp_path / "unknown.csv"
    input_file.write_text("a,b,c", encoding="utf-8")

    service = DocumentIngestionService(TikaClient(endpoint="http://localhost:9998"))
    with pytest.raises(ValueError, match="Unsupported file extension"):
        service.ingest_file(input_file)

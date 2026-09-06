from __future__ import annotations

import json
from pathlib import Path

from knowledge_fabric.ingestion.cli import _resolve_input_files, main
from knowledge_fabric.ingestion.models import Chunk, Document, SourceFormat


def test_resolve_input_files_with_directory(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "c.csv").write_text("c", encoding="utf-8")

    files = _resolve_input_files(str(tmp_path), recursive=False)
    assert [file.name for file in files] == ["a.md", "b.txt"]


def test_cli_main_ingests_and_prints_summary(monkeypatch, capsys) -> None:
    class _FakeSettings:
        class _DB:
            host = "localhost"
            port = 5432
            name = "db"
            user = "user"
            password = ""

        class _Tika:
            endpoint = "http://localhost:9998/tika"
            request_timeout_seconds = 30

        class _Emb:
            provider = "mock"
            dimension = 8
            batch_size = 2

        database = _DB()
        tika = _Tika()
        embeddings = _Emb()

    class _FakeRepo:
        def __init__(self, connection_factory):
            self.connection_factory = connection_factory

        @staticmethod
        def upsert_document(document, *args, **kwargs):
            return 1

        @staticmethod
        def replace_chunks(*, document_id, chunks, embeddings=None, **kwargs):
            return len(chunks)

    class _FakeIngestion:
        def __init__(self, tika_client):
            self.tika_client = tika_client

        @staticmethod
        def ingest_file(path, source_metadata=None):
            return Document(
                source_uri=str(path),
                source_format=SourceFormat.TXT,
                content_text="hello world",
                metadata=source_metadata or {},
                title="file",
            )

    class _FakeChunking:
        def __init__(self, max_chars=1200, overlap_chars=150):
            self.max_chars = max_chars
            self.overlap_chars = overlap_chars

        @staticmethod
        def chunk_document(document):
            return [Chunk(document_uri=document.source_uri, chunk_index=0, chunk_text="hello", metadata={})]

    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: _FakeSettings())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.DocumentIngestionService", _FakeIngestion)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.DocumentChunkingService", _FakeChunking)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.TikaClient", lambda endpoint, timeout_seconds: object())

    monkeypatch.setattr("knowledge_fabric.ingestion.cli._resolve_input_files", lambda path, recursive: [Path("a.txt"), Path("b.txt")])

    exit_code = main(["--path", "sources"])
    output = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(output)
    assert payload["files_discovered"] == 2
    assert payload["documents_ingested"] == 2
    assert payload["chunks_written"] == 2

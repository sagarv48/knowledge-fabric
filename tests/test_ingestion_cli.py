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


def test_cli_main_delete_document(monkeypatch, capsys) -> None:
    deleted_calls = []

    class _FakeRepo:
        def __init__(self, connection_factory): pass
        @staticmethod
        def delete_document(*, document_id=None, source_uri=None, tenant_id=None):
            deleted_calls.append({"id": document_id, "uri": source_uri, "tenant": tenant_id})
            return True

    fake_settings = type("Settings", (), {"database": object()})()
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)

    exit_code = main(["--delete-document-id", "42", "--tenant", "acme-corp"])
    assert exit_code == 0
    assert deleted_calls[0] == {"id": 42, "uri": None, "tenant": "acme-corp"}

    output = json.loads(capsys.readouterr().out)
    assert output["deleted"] is True
    assert output["document_id"] == 42
    assert output["tenant_id"] == "acme-corp"


def test_cli_main_purge_tenant_requires_confirm(monkeypatch, capsys) -> None:
    fake_settings = type("Settings", (), {"database": object()})()
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())

    exit_code = main(["--purge-tenant", "acme-corp"])
    assert exit_code == 1
    assert "Must specify --confirm" in capsys.readouterr().out


def test_cli_main_purge_tenant_with_confirm(monkeypatch, capsys) -> None:
    purged_calls = []

    class _FakeRepo:
        def __init__(self, connection_factory): pass
        @staticmethod
        def purge_tenant(tenant_id):
            purged_calls.append(tenant_id)
            return {
                "tenant_id": tenant_id,
                "documents_deleted": 5,
                "retrieval_runs_deleted": 10,
                "audit_events_deleted": 12,
            }

    fake_settings = type("Settings", (), {"database": object()})()
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)

    exit_code = main(["--purge-tenant", "acme-corp", "--confirm"])
    assert exit_code == 0
    assert purged_calls == ["acme-corp"]

def test_cli_main_index_status(monkeypatch, capsys) -> None:
    class _FakeRepo:
        def __init__(self, connection_factory): pass
        @staticmethod
        def get_index_status(tenant_id=None):
            return {"total_documents": 42, "total_chunks": 168, "tenant_id": tenant_id or "all"}

    fake_settings = type("Settings", (), {"database": object()})()
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)

    exit_code = main(["--index-status", "--tenant", "test-tenant"])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["total_documents"] == 42
    assert output["total_chunks"] == 168
    assert output["tenant_id"] == "test-tenant"


def test_cli_main_check_consistency_healthy_and_unhealthy(monkeypatch, capsys) -> None:
    consistency_state = {"is_healthy": True, "orphaned_chunks": 0}

    class _FakeRepo:
        def __init__(self, connection_factory): pass
        @staticmethod
        def check_consistency(tenant_id=None):
            return consistency_state

    fake_settings = type("Settings", (), {"database": object()})()
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)

    # 1. Healthy
    exit_code = main(["--check-consistency"])
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["is_healthy"] is True

    # 2. Unhealthy
    consistency_state["is_healthy"] = False
    consistency_state["orphaned_chunks"] = 5
    exit_code = main(["--check-consistency"])
    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["is_healthy"] is False


def test_cli_main_reembed(monkeypatch, capsys) -> None:
    class _FakeRepo:
        def __init__(self, connection_factory): pass
        @staticmethod
        def reembed_chunks(*, embedding_provider, tenant_id=None):
            return {"chunks_reembedded": 50, "dimension": 8, "tenant_id": tenant_id or "all"}

    fake_settings = type("Settings", (), {
        "database": object(),
        "embeddings": type("Emb", (), {"provider": "mock", "dimension": 8})(),
    })()
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.build_embedding_provider", lambda **kw: object())

    exit_code = main(["--reembed", "--tenant", "test-tenant"])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["chunks_reembedded"] == 50
    assert output["dimension"] == 8


def test_cli_main_with_max_file_size_and_error_isolation(monkeypatch, capsys) -> None:
    class _FakeRepo:
        def __init__(self, connection_factory): pass
        @staticmethod
        def upsert_document(document, tenant_id="default"):
            return 101
        @staticmethod
        def replace_chunks(*, document_id, chunks, embeddings=None, **kwargs):
            return len(chunks)

    class _FakeIngestion:
        def __init__(self, tika_client, max_file_size_bytes=None):
            self.tika_client = tika_client
            self.max_file_size_bytes = max_file_size_bytes

        @staticmethod
        def ingest_file(path, source_metadata=None):
            if "fail" in str(path):
                raise ValueError("Simulated file size limit exceeded or corrupted file")
            return Document(
                source_uri=str(path),
                source_format=SourceFormat.TXT,
                content_text="hello",
                metadata=source_metadata or {},
                title="file",
            )

    class _FakeChunking:
        def __init__(self, max_chars=1200, overlap_chars=150): pass
        @staticmethod
        def chunk_document(document):
            return [Chunk(document_uri=document.source_uri, chunk_index=0, chunk_text="hello", metadata={})]

    fake_settings = type("Settings", (), {
        "database": object(),
        "tika": type("Tika", (), {"endpoint": "http://localhost:9998", "request_timeout_seconds": 10})(),
        "embeddings": type("Emb", (), {"provider": "mock", "dimension": 8})(),
    })()

    monkeypatch.setattr("knowledge_fabric.ingestion.cli.load_settings", lambda _: fake_settings)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.create_postgres_connection_factory", lambda _: lambda: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.KnowledgeRepository", _FakeRepo)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.DocumentIngestionService", _FakeIngestion)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.DocumentChunkingService", _FakeChunking)
    monkeypatch.setattr("knowledge_fabric.ingestion.cli.TikaClient", lambda endpoint, timeout_seconds: object())
    monkeypatch.setattr("knowledge_fabric.ingestion.cli._resolve_input_files", lambda path, recursive: [Path("good.txt"), Path("fail.txt")])

    exit_code = main(["--path", "sources", "--max-file-size-mb", "10"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["files_discovered"] == 2
    assert payload["documents_ingested"] == 1
    assert payload["chunks_written"] == 1
    assert "errors" in payload
    assert len(payload["errors"]) == 1
    assert "fail.txt" in payload["errors"][0]["file"]




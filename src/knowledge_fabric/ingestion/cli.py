"""CLI for persistent document ingestion and chunk storage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge_fabric.chunking import DocumentChunkingService
from knowledge_fabric.config import load_settings
from knowledge_fabric.db import KnowledgeRepository, create_postgres_connection_factory
from knowledge_fabric.embeddings import build_embedding_provider
from knowledge_fabric.ingestion import DocumentIngestionService, TikaClient

_SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".html", ".htm", ".pdf", ".docx", ".pptx"}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    settings = load_settings(args.settings)
    connection_factory = create_postgres_connection_factory(settings.database)
    repository = KnowledgeRepository(connection_factory=connection_factory)
    ingestion = DocumentIngestionService(
        tika_client=TikaClient(
            endpoint=settings.tika.endpoint,
            timeout_seconds=settings.tika.request_timeout_seconds,
        )
    )
    chunking = DocumentChunkingService(
        max_chars=args.max_chunk_chars,
        overlap_chars=args.chunk_overlap_chars,
    )

    embedding_provider = None
    if args.embed:
        embedding_provider = build_embedding_provider(
            provider_name=settings.embeddings.provider,
            dimension=settings.embeddings.dimension,
        )

    input_paths = _resolve_input_files(args.path, recursive=args.recursive)
    if not input_paths:
        print("No supported files found for ingestion.")
        return 0

    tenant_id = args.tenant
    summary = {
        "files_discovered": len(input_paths),
        "documents_ingested": 0,
        "chunks_written": 0,
        "tenant_id": tenant_id,
    }

    for file_path in input_paths:
        document = ingestion.ingest_file(
            file_path,
            source_metadata={"ingestion_source": "cli", "tenant_id": tenant_id},
        )
        chunks = chunking.chunk_document(document)
        embeddings = embedding_provider.embed_texts([chunk.chunk_text for chunk in chunks]) if embedding_provider else None

        document_id = repository.upsert_document(document, tenant_id=tenant_id)
        inserted_count = repository.replace_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            tenant_id=tenant_id,
        )
        summary["documents_ingested"] += 1
        summary["chunks_written"] += inserted_count

    print(json.dumps(summary, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest and persist source files for Knowledge Fabric.")
    parser.add_argument("--path", "--source-path", dest="path", required=True, help="Source file or directory path.")
    parser.add_argument("--settings", default="config/settings.yaml", help="Path to settings.yaml.")
    parser.add_argument("--tenant", "--collection", dest="tenant", default="default", help="Tenant ID for multi-tenant isolation.")
    parser.add_argument("--source-type", dest="source_type", default=None, help="Optional source format hint (e.g. markdown, pdf).")
    parser.add_argument("--recursive", action="store_true", help="Recursively scan directories.")
    parser.add_argument("--embed", action="store_true", help="Compute and store embeddings for chunks using configured provider.")
    parser.add_argument("--max-chunk-chars", type=int, default=1200, help="Maximum chunk size in characters.")
    parser.add_argument("--chunk-overlap-chars", type=int, default=150, help="Overlap size in characters.")
    return parser


def _resolve_input_files(path_value: str, *, recursive: bool) -> list[Path]:
    path = Path(path_value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    if path.is_file():
        return [path] if path.suffix.lower() in _SUPPORTED_EXTENSIONS else []

    if recursive:
        files = sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    else:
        files = sorted(candidate for candidate in path.iterdir() if candidate.is_file())
    return [candidate for candidate in files if candidate.suffix.lower() in _SUPPORTED_EXTENSIONS]


if __name__ == "__main__":
    raise SystemExit(main())

"""Configuration loader for Knowledge Fabric runtime components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(slots=True)
class TikaSettings:
    endpoint: str
    request_timeout_seconds: int


@dataclass(slots=True)
class EmbeddingSettings:
    provider: str
    dimension: int
    batch_size: int


@dataclass(slots=True)
class RetrievalSettings:
    default_top_k: int
    lexical_weight: float
    vector_weight: float
    rrf_k: int


@dataclass(slots=True)
class AppSettings:
    name: str
    environment: str
    log_level: str


@dataclass(slots=True)
class Settings:
    app: AppSettings
    database: DatabaseSettings
    tika: TikaSettings
    embeddings: EmbeddingSettings
    retrieval: RetrievalSettings


def load_settings(path: str | Path = "config/settings.yaml") -> Settings:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Settings(
        app=AppSettings(**_as_dict(raw, "app")),
        database=DatabaseSettings(**_as_dict(raw, "database")),
        tika=TikaSettings(**_as_dict(raw, "tika")),
        embeddings=EmbeddingSettings(**_as_dict(raw, "embeddings")),
        retrieval=RetrievalSettings(**_as_dict(raw, "retrieval")),
    )


def _as_dict(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping for '{key}'")
    return value

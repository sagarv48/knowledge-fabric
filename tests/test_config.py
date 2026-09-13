from pathlib import Path

from knowledge_fabric.config import load_settings


_BASE_YAML = """
app:
  name: knowledge-fabric
  environment: test
  log_level: DEBUG
database:
  host: localhost
  port: 5432
  name: kf
  user: user
  password: ""
tika:
  endpoint: http://localhost:9998/tika
  request_timeout_seconds: 10
embeddings:
  provider: mock
  dimension: 128
  batch_size: 8
retrieval:
  default_top_k: 5
  lexical_weight: 1.0
  vector_weight: 1.0
  rrf_k: 60
""".strip()


def test_load_settings_minimal(tmp_path: Path) -> None:
    """Minimal YAML (no reranking or backend key) should load with safe defaults."""
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text(_BASE_YAML, encoding="utf-8")

    settings = load_settings(settings_file)
    assert settings.app.environment == "test"
    assert settings.embeddings.dimension == 128
    assert settings.retrieval.default_top_k == 5
    # Defaults when section is absent
    assert settings.retrieval.backend == "postgres"
    assert settings.reranking.provider == "none"
    assert settings.reranking.top_n == 5


def test_load_settings_with_reranking(tmp_path: Path) -> None:
    """Reranking section should be parsed into RerankingSettings."""
    yaml = _BASE_YAML + """
reranking:
  provider: cross_encoder
  top_n: 3
"""
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text(yaml, encoding="utf-8")

    settings = load_settings(settings_file)
    assert settings.reranking.provider == "cross_encoder"
    assert settings.reranking.top_n == 3


def test_load_settings_with_backend(tmp_path: Path) -> None:
    """retrieval.backend field should be parsed and available."""
    yaml = _BASE_YAML.replace(
        "  rrf_k: 60", "  rrf_k: 60\n  backend: qdrant"
    )
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text(yaml, encoding="utf-8")

    settings = load_settings(settings_file)
    assert settings.retrieval.backend == "qdrant"

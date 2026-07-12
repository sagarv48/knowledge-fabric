from pathlib import Path

from knowledge_fabric.config import load_settings


def test_load_settings(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.yaml"
    settings_file.write_text(
        """
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
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(settings_file)
    assert settings.app.environment == "test"
    assert settings.embeddings.dimension == 128
    assert settings.retrieval.default_top_k == 5

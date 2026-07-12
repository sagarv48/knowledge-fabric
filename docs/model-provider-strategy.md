# Model Provider Strategy

Knowledge Fabric keeps embedding providers configurable and decoupled from retrieval logic.

## Design principles

- Use provider interfaces, not provider-specific logic in retrieval code.
- Keep embedding dimension configurable through settings.
- Support deterministic mock provider for local development and tests.
- Allow provider replacement without changing evidence contract.

## Current provider pattern

```text
EmbeddingProvider (interface)
    ->
MockEmbeddingProvider (deterministic baseline)
```

## Configuration model

```text
config/settings.yaml
  embeddings:
    provider: <provider-name>
    dimension: <vector-dimension>
    batch_size: <batch-size>
```

## Runtime flow

```text
Query text
  ->
EmbeddingProvider.embed_texts()
  ->
Query vector
  ->
Vector retrieval + hybrid fusion
```

## Adoption guidance

1. Start with `MockEmbeddingProvider` for repeatable local behavior.
2. Introduce additional providers behind the same interface.
3. Validate dimension compatibility with `chunks.embedding`.
4. Compare retrieval metrics before and after provider changes.

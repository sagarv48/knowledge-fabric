# Phase 1 Local Setup

## Start infrastructure

```bash
docker compose up -d
```

Services:

- PostgreSQL + pgvector on `localhost:5432`
- Apache Tika on `localhost:9998`

## Run tests

```bash
python3 -m pytest
```

## Run MCP server

```bash
knowledge-fabric-mcp
```

## Persist ingested data

```bash
knowledge-fabric-ingest --path sources --recursive --embed
```

## Run evaluation (sample)

Use the query set in:

`src/knowledge_fabric/evaluation/queries.yaml`

and evaluate lexical, vector, and hybrid retrieval modes through
`knowledge_fabric.evaluation.RetrievalEvaluationRunner`.

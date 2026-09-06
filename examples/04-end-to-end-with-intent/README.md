# End-to-End Example: Ingest → Retrieve → Plan → Approve

This example demonstrates the full stack flow:
1. Ingest documents into **knowledge-fabric** via the ingestion pipeline
2. Query retrieved evidence via the **knowledge-fabric** MCP server  
3. Submit an intent to **intent-fabric** to generate a plan
4. Observe the policy decision (allow / requires\_approval / deny)

## Prerequisites

```bash
# 1. Start Postgres + pgvector
docker compose up -d

# 2. Apply schema
psql -h localhost -U knowledge_fabric -d knowledge_fabric -f db/schema/001_extensions.sql
psql -h localhost -U knowledge_fabric -d knowledge_fabric -f db/schema/002_core_tables.sql
psql -h localhost -U knowledge_fabric -d knowledge_fabric -f db/schema/003_multi_tenancy.sql
psql -h localhost -U knowledge_fabric -d knowledge_fabric -f db/schema/004_dimension_guard.sql
psql -h localhost -U knowledge_fabric -d knowledge_fabric -f db/schema/005_partitioning_and_hnsw.sql

# 3. Start Ollama (free, local LLM — no API key)
ollama serve
ollama pull nomic-embed-text    # embeddings
ollama pull llama3              # intent planning
```

## Run the example

```bash
cd examples/04-end-to-end-with-intent
pip install -r requirements.txt

# Set providers (free, vendor-neutral)
export EMBEDDING_PROVIDER=ollama
export INTENT_PLANNER=ollama

python run.py
```

## What you'll see

```
[1] Ingesting sample documents...
    ✓ Ingested: incident_response_guide.md (12 chunks)
    ✓ Ingested: change_management_policy.md (8 chunks)
    ✓ Ingested: access_control_standard.md (9 chunks)

[2] Querying via knowledge-fabric MCP...
    Query: "What is the process for emergency access provisioning?"
    
    Evidence Package (top 3 results):
    ┌─────────────────────────────────────────────────────────┐
    │ [1] score=0.87 | access_control_standard.md §4.2       │
    │     "Emergency access provisioning requires CISO..."   │
    │ [2] score=0.81 | change_management_policy.md §2.1     │
    │     "All emergency changes must be logged..."          │
    │ [3] score=0.74 | incident_response_guide.md §6.3      │
    │     "Break-glass accounts are reviewed quarterly..."   │
    └─────────────────────────────────────────────────────────┘

[3] Submitting intent to intent-fabric...
    Intent: "Create a ticket to review emergency access for user jdoe@corp.com"
    Planner: OllamaLLMPlanner (llama3)
    
    Generated Plan:
    ├── Step 1: Retrieve current access profile     [analysis_review]
    ├── Step 2: Create access review ticket         [ticket_create]
    └── Step 3: Notify security team               [notification_send]

[4] Policy evaluation...
    ✓ Rule matched: ticket_create → REQUIRES_APPROVAL
      Reason: "Ticket creation requires human review before execution."
    ✓ Rule matched: notification_send → REQUIRES_APPROVAL
    
    Decision: REQUIRES_APPROVAL
    
    Approval Package:
    {
      "approval_id": "appr_a3f9...",
      "plan_id": "plan_8b2e...",
      "requires_approval": true,
      "reasons": [
        "[ticket_create] Ticket creation requires human review before execution.",
        "[notification_send] Notifications to users require human review."
      ]
    }

Done. In a real deployment, the approval package would be routed to your
approval channel (Slack, email, Jira) via your RuntimeActionAdapter.
```

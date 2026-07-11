# Phase 2: Intent Fabric

## Purpose

Intent Fabric converts user intent plus retrieved evidence into structured plans and approval-ready action contracts.

It answers this problem:

```text
How do we convert evidence-backed intent into a safe, reviewable plan?
```

It does not directly execute vendor-specific actions. Runtime integrations belong to Phase 3.

## Core flow

```text
User intent
  -> Evidence package from Knowledge Fabric
  -> Planner
  -> Action contract candidates
  -> Policy checks
  -> Human approval package
  -> Simulated execution result
```

## Scope

In scope:

- Intent model
- Plan model
- Action contract schema
- Policy engine
- Approval package
- Execution simulation
- MCP planning tools

Out of scope:

- Direct Acme integration
- Jira/ADO/ServiceNow runtime integration
- Production credentials
- Real workflow execution

## Recommended repo structure

```text
intent-fabric/
  README.md
  docs/
  config/
  src/
    intent_fabric/
      intent/
      planning/
      contracts/
      policies/
      approvals/
      simulation/
      mcp/
  tests/
  examples/
```

## Relationship with Knowledge Fabric

Intent Fabric consumes evidence packages from Knowledge Fabric.

```text
Knowledge Fabric evidence package
  -> Intent Fabric planner
  -> Approval-ready plan
```

The dependency should be through a stable evidence package contract, not through direct internal imports when possible.

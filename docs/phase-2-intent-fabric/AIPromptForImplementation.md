# AI Prompt for Phase 2 Implementation: Intent Fabric

Use this prompt with Copilot CLI or another coding agent from the `intent-fabric` repo root.

```text
You are implementing Phase 2: Intent Fabric.

Goal:
Build a vendor-neutral intent planning and approval framework that consumes evidence packages from Knowledge Fabric and produces structured, reviewable plans.

Hard constraints:
- Do not add Acme-specific integration.
- Do not execute real actions.
- Do not request enterprise credentials.
- Do not implement runtime connectors.
- Keep execution as simulation only.

Implement in this order:

1. Create Python project structure under src/intent_fabric.
2. Define data models:
   - IntentRequest
   - EvidencePackageReference
   - Plan
   - PlanStep
   - ActionContract
   - ApprovalRequest
   - PolicyDecision
   - SimulationResult
3. Implement planner interface.
4. Implement simple rule-based planner first.
5. Implement action contract schema.
6. Implement policy engine with allow/deny/requires_approval decisions.
7. Implement approval package generator.
8. Implement execution simulator that never calls real systems.
9. Implement MCP tools:
   - create_plan_from_evidence
   - validate_plan
   - create_approval_package
   - simulate_plan
10. Add tests for policy decisions and simulation.
11. Add docs explaining that real execution belongs to enterprise adapters in Phase 3.

Acceptance criteria:
- Given an evidence package, the system creates a structured plan.
- The plan can be validated by policy rules.
- The system can generate an approval package.
- Execution is simulated only.
- No Acme-specific or vendor-specific runtime code exists.
```
```

## Manual actions after AI implementation

```bash
git status
git diff
pytest
```

Commit:

```bash
git add .
git commit -m "Implement Intent Fabric planning scaffold"
```

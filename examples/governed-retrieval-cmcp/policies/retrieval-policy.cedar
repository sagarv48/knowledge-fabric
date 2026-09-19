// ═══════════════════════════════════════════════════════════════════════
// Knowledge Fabric — Cedar Policy Bundle for cMCP Gateway
// ═══════════════════════════════════════════════════════════════════════
//
// Entity model (cMCP schema):
//   principal  →  cMCP::Principal  { session_id, role, assigned_tenant }
//   action     →  cMCP::Action::"call_tool"
//   resource   →  cMCP::Resource   { tool_name, tenant_id }
//   context    →  { incident_active, caller_tenant, top_k }

// ── Rule 1: Employee Self-Service (Handbook Access) ──────────────────
// Any authenticated principal can search the employee handbook.
permit (
    principal,
    action == cMCP::Action::"call_tool",
    resource
) when {
    resource.tool_name == "retrieve_evidence" &&
    resource.tenant_id == "employee-handbook"
};

// ── Rule 2a: Compensation Firewall (Forbid non-HR) ───────────────────
// Only HR Business Partners may access compensation data.
// This forbid rule takes precedence over any permit.
forbid (
    principal,
    action == cMCP::Action::"call_tool",
    resource
) when {
    resource.tenant_id == "hr-compensation" &&
    !(principal.role == "hr_business_partner")
};

// ── Rule 2b: Compensation Access (Permit HR Business Partner) ────────
permit (
    principal,
    action == cMCP::Action::"call_tool",
    resource
) when {
    (resource.tool_name == "retrieve_evidence" || resource.tool_name == "get_document") &&
    resource.tenant_id == "hr-compensation" &&
    principal.role == "hr_business_partner"
};

// ── Rule 3: SecOps Break-Glass (Incident-Conditional) ────────────────
// Incident commanders can access security runbooks during active incidents.
permit (
    principal,
    action == cMCP::Action::"call_tool",
    resource
) when {
    resource.tool_name == "retrieve_evidence" &&
    resource.tenant_id == "security-runbooks" &&
    principal.role == "incident_commander" &&
    context.incident_active == true
};

// ── Rule 4: Multi-Tenant Customer Isolation ──────────────────────────
// Agents may only access data belonging to their own assigned tenant.
// Blocks cross-tenant prompt-injection attacks at the gateway.
forbid (
    principal,
    action == cMCP::Action::"call_tool",
    resource
) when {
    context.caller_tenant != resource.tenant_id
};

// ── Default: Implicit deny ───────────────────────────────────────────
// cMCP operates default-deny. Any tool call not matched by a permit
// rule above is automatically rejected with 403 POLICY_DENY.

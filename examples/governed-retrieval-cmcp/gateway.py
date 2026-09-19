"""Front-door policy gateway modeling cMCP (Confidential MCP) integration.

Provides zero-trust policy interception, Cedar-compatible rule evaluation,
and cryptographic TRACE claim generation for Knowledge Fabric retrieval operations.
Requires no external dependencies (pure Python standard library).
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any, Callable
import uuid


@dataclasses.dataclass
class PolicyPrincipal:
    """Maps to cMCP::Principal schema.
    
    Represents the calling AI agent identity, including session binding,
    organizational role, and assigned tenant scope.
    """
    session_id: str
    role: str
    assigned_tenant: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class PolicyResource:
    """Maps to cMCP::Resource schema.
    
    Represents the MCP tool target and the requested tenant corpus.
    """
    tool_name: str
    tenant_id: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class PolicyContext:
    """Maps to cMCP::Context attributes.
    
    Carries session-level environmental and operational context.
    """
    caller_tenant: str
    incident_active: bool = False
    top_k: int = 5

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class PolicyVerdict:
    """Result of policy evaluation against Cedar rules.
    
    Follows Cedar's explicit decision states: PERMIT or DENY.
    """
    decision: str  # "PERMIT" | "DENY"
    matched_rule: str  # Human-readable rule name for audit logging
    reason: str  # Diagnostic explanation

    @property
    def is_permitted(self) -> bool:
        return self.decision == "PERMIT"

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class TraceClaim:
    """Cryptographic audit receipt modeling cMCP TRACE claims.
    
    Binds the loaded Cedar policy bundle SHA-256 hash, the policy verdict,
    the tool call arguments, and the SHA-256 digests of every returned evidence chunk
    using an HMAC-SHA256 signature.
    """
    claim_id: str
    session_id: str
    timestamp: str
    policy_bundle_hash: str
    verdict: PolicyVerdict
    tool_call: dict[str, Any]
    evidence_hashes: list[str]
    signature: str

    def canonical_payload(self) -> bytes:
        """Serialize claim fields to a deterministic, canonical JSON representation.
        
        The signature field is excluded so it can be signed and verified.
        """
        payload = {
            "claim_id": self.claim_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "policy_bundle_hash": self.policy_bundle_hash,
            "verdict": self.verdict.to_dict() if hasattr(self.verdict, "to_dict") else self.verdict,
            "tool_call": self.tool_call,
            "evidence_hashes": self.evidence_hashes,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def verify(self, signing_key: str) -> bool:
        """Verify that the HMAC-SHA256 signature matches the claim payload."""
        payload_bytes = self.canonical_payload()
        expected = hmac.new(signing_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "policy_bundle_hash": self.policy_bundle_hash,
            "verdict": self.verdict.to_dict() if hasattr(self.verdict, "to_dict") else self.verdict,
            "tool_call": self.tool_call,
            "evidence_hashes": self.evidence_hashes,
            "signature": self.signature,
        }


def hash_evidence_chunk(chunk_content: str | dict[str, Any]) -> str:
    """Compute the SHA-256 hex digest of an evidence chunk."""
    if isinstance(chunk_content, dict):
        raw = json.dumps(chunk_content, sort_keys=True, separators=(",", ":"))
    else:
        raw = str(chunk_content)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CmcpGateway:
    """Front-door policy gateway modeling cMCP authorization and audit semantics.
    
    Evaluates policy rules with Cedar precedence:
      1. Forbid rules take precedence over all permit rules.
      2. Permit rules authorize specific principal + action + resource patterns.
      3. Default-deny: If no permit rule matches, access is rejected.
    """

    def __init__(self, policy_file: Path | str, signing_key: str = "cmcp-dev-signing-key") -> None:
        self.policy_path = Path(policy_file)
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

        policy_bytes = self.policy_path.read_bytes()
        self.policy_content = policy_bytes.decode("utf-8")
        self.policy_bundle_hash = hashlib.sha256(policy_bytes).hexdigest()
        self.signing_key = signing_key

    def evaluate(
        self,
        principal: PolicyPrincipal,
        action: str,
        resource: PolicyResource,
        context: PolicyContext,
    ) -> PolicyVerdict:
        """Evaluate policy request against Cedar policy bundle rules.
        
        Enforces Cedar semantics:
          - Forbid rules are evaluated first. If any forbid matches, result is DENY.
          - Permit rules are evaluated next.
          - If no permit rule matches, default is DENY.
        """
        # Validate action
        if action != "call_tool":
            return PolicyVerdict(
                decision="DENY",
                matched_rule="invalid_action",
                reason=f"Action '{action}' is not recognized. cMCP only authorizes 'call_tool'.",
            )

        # ── 1. Forbid Rule 4: Multi-Tenant Customer Isolation ──────────────
        # context.caller_tenant != resource.tenant_id
        if context.caller_tenant != resource.tenant_id:
            return PolicyVerdict(
                decision="DENY",
                matched_rule="cross_tenant_isolation",
                reason=(
                    f"caller_tenant '{context.caller_tenant}' != resource tenant "
                    f"'{resource.tenant_id}'. Cross-tenant access denied."
                ),
            )

        # ── 2. Forbid Rule 2a: Compensation Firewall ───────────────────────
        # resource.tenant_id == "hr-compensation" && !(principal.role == "hr_business_partner")
        if resource.tenant_id == "hr-compensation" and principal.role != "hr_business_partner":
            return PolicyVerdict(
                decision="DENY",
                matched_rule="compensation_firewall",
                reason=(
                    f"Principal role '{principal.role}' is not 'hr_business_partner'. "
                    f"Access to hr-compensation denied."
                ),
            )

        # ── 3. Permit Rule 1: Employee Self-Service (Handbook Access) ─────
        if resource.tool_name == "retrieve_evidence" and resource.tenant_id == "employee-handbook":
            return PolicyVerdict(
                decision="PERMIT",
                matched_rule="employee_self_service",
                reason="Authenticated principal permitted to search employee handbook.",
            )

        # ── 4. Permit Rule 2b: Compensation Access for HR Business Partner ─
        if (
            resource.tool_name in ("retrieve_evidence", "get_document")
            and resource.tenant_id == "hr-compensation"
            and principal.role == "hr_business_partner"
        ):
            return PolicyVerdict(
                decision="PERMIT",
                matched_rule="hr_compensation_access",
                reason="HR Business Partner permitted to access compensation data.",
            )

        # ── 5. Permit Rule 3: SecOps Break-Glass (Incident-Conditional) ───
        if (
            resource.tool_name == "retrieve_evidence"
            and resource.tenant_id == "security-runbooks"
            and principal.role == "incident_commander"
            and context.incident_active is True
        ):
            return PolicyVerdict(
                decision="PERMIT",
                matched_rule="secops_break_glass",
                reason="Incident commander permitted to access security runbooks during active incident.",
            )

        # ── 6. Default Deny ───────────────────────────────────────────────
        return PolicyVerdict(
            decision="DENY",
            matched_rule="default_deny",
            reason=(
                f"No permit rule matched for tool '{resource.tool_name}' on tenant "
                f"'{resource.tenant_id}' for role '{principal.role}'."
            ),
        )

    def sign_trace_claim(
        self,
        session_id: str,
        verdict: PolicyVerdict,
        tool_call: dict[str, Any],
        evidence_chunks: list[str | dict[str, Any]],
    ) -> TraceClaim:
        """Create and cryptographically sign a cMCP TRACE claim."""
        claim_id = f"trace_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        evidence_hashes = [hash_evidence_chunk(c) for c in evidence_chunks]

        # Construct partial claim without signature to compute canonical payload
        claim = TraceClaim(
            claim_id=claim_id,
            session_id=session_id,
            timestamp=timestamp,
            policy_bundle_hash=self.policy_bundle_hash,
            verdict=verdict,
            tool_call=tool_call,
            evidence_hashes=evidence_hashes,
            signature="",
        )

        canonical_bytes = claim.canonical_payload()
        signature = hmac.new(
            self.signing_key.encode("utf-8"),
            canonical_bytes,
            hashlib.sha256,
        ).hexdigest()

        claim.signature = signature
        return claim

    def intercept_tool_call(
        self,
        principal: PolicyPrincipal,
        tool_name: str,
        tool_args: dict[str, Any],
        context: PolicyContext,
        executor: Callable[[str, dict[str, Any]], list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Full gateway interception lifecycle for tool calls.
        
        1. Parse PolicyResource from tool invocation.
        2. Evaluate Cedar policy rules.
        3. If DENY: Immediately abort with 403 POLICY_DENY payload (never queries DB).
        4. If PERMIT: Call tool executor, gather chunks.
        5. Hash chunks and generate cryptographically signed TraceClaim.
        6. Return evidence together with signed TRACE receipt.
        """
        tenant_id = str(tool_args.get("tenant_id", ""))
        resource = PolicyResource(tool_name=tool_name, tenant_id=tenant_id)

        verdict = self.evaluate(
            principal=principal,
            action="call_tool",
            resource=resource,
            context=context,
        )

        if not verdict.is_permitted:
            return {
                "status": 403,
                "error": "POLICY_DENY",
                "matched_rule": verdict.matched_rule,
                "reason": verdict.reason,
                "session_id": principal.session_id,
                "policy_bundle_hash": self.policy_bundle_hash,
            }

        # If permitted, invoke the executor or return empty evidence list
        evidence_chunks: list[dict[str, Any]] = []
        if executor is not None:
            evidence_chunks = executor(tool_name, tool_args)

        tool_call_spec = {
            "tool_name": tool_name,
            "args": tool_args,
        }

        trace_claim = self.sign_trace_claim(
            session_id=principal.session_id,
            verdict=verdict,
            tool_call=tool_call_spec,
            evidence_chunks=evidence_chunks,
        )

        return {
            "status": 200,
            "verdict": verdict.to_dict(),
            "evidence": evidence_chunks,
            "trace_claim": trace_claim.to_dict(),
        }

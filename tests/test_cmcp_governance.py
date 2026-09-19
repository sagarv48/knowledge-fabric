"""Policy governance test suite for cMCP + Knowledge Fabric integration.

Tests Cedar policy evaluation, TRACE claim generation, and evidence hash
binding without requiring Docker, cMCP binary, or database connectivity.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

# Ensure example directory is importable
_TESTS_DIR = Path(__file__).resolve().parent
_KF_ROOT = _TESTS_DIR.parent
_EXAMPLE_DIR = _KF_ROOT / "examples" / "governed-retrieval-cmcp"

if str(_EXAMPLE_DIR) not in sys.path:
    sys.path.insert(0, str(_EXAMPLE_DIR))

from gateway import (
    CmcpGateway,
    PolicyContext,
    PolicyPrincipal,
    PolicyResource,
    PolicyVerdict,
    TraceClaim,
    hash_evidence_chunk,
)

_POLICY_FILE = _EXAMPLE_DIR / "policies" / "retrieval-policy.cedar"
_DEV_KEY = "test-cmcp-signing-key-12345"


# ── Cedar Policy File Tests ─────────────────────────────────────────


def test_cedar_policy_file_exists_and_is_valid_utf8() -> None:
    """Policy file exists and loads without encoding errors."""
    assert _POLICY_FILE.exists(), f"Policy file not found at {_POLICY_FILE}"
    content = _POLICY_FILE.read_text(encoding="utf-8")
    assert len(content) > 0
    assert "cMCP::Principal" in content


def test_cedar_policy_contains_required_rules() -> None:
    """Policy bundle contains permit and forbid rules for all governance scenarios."""
    content = _POLICY_FILE.read_text(encoding="utf-8")
    assert "employee-handbook" in content
    assert "hr-compensation" in content
    assert "security-runbooks" in content
    assert "caller_tenant != resource.tenant_id" in content
    assert "permit" in content
    assert "forbid" in content


def test_cedar_policy_bundle_hash_is_deterministic() -> None:
    """SHA-256 digest of policy bundle is stable across multiple loads."""
    gw1 = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    gw2 = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    assert gw1.policy_bundle_hash == gw2.policy_bundle_hash
    assert len(gw1.policy_bundle_hash) == 64


# ── Gateway Policy Evaluation Tests ─────────────────────────────────


def test_employee_handbook_access_permitted() -> None:
    """Authenticated principal can search employee-handbook tenant."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_01",
        role="product_designer",
        assigned_tenant="employee-handbook",
    )
    context = PolicyContext(caller_tenant="employee-handbook", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="employee-handbook")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "PERMIT"
    assert verdict.matched_rule == "employee_self_service"


def test_compensation_denied_for_non_hr() -> None:
    """Non-HR principal gets DENY for hr-compensation tenant."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_02",
        role="product_designer",
        assigned_tenant="hr-compensation",
    )
    context = PolicyContext(caller_tenant="hr-compensation", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="hr-compensation")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "compensation_firewall"
    assert "hr_business_partner" in verdict.reason


def test_compensation_permitted_for_hr_business_partner() -> None:
    """HR business partner CAN access hr-compensation tenant."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_03",
        role="hr_business_partner",
        assigned_tenant="hr-compensation",
    )
    context = PolicyContext(caller_tenant="hr-compensation", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="hr-compensation")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "PERMIT"
    assert verdict.matched_rule == "hr_compensation_access"


def test_secops_permitted_during_active_incident() -> None:
    """Incident commander with incident_active=True gets PERMIT."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_04",
        role="incident_commander",
        assigned_tenant="security-runbooks",
    )
    context = PolicyContext(caller_tenant="security-runbooks", incident_active=True)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="security-runbooks")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "PERMIT"
    assert verdict.matched_rule == "secops_break_glass"


def test_secops_denied_without_active_incident() -> None:
    """Incident commander with incident_active=False gets DENY."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_05",
        role="incident_commander",
        assigned_tenant="security-runbooks",
    )
    context = PolicyContext(caller_tenant="security-runbooks", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="security-runbooks")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "default_deny"


def test_secops_denied_for_wrong_role() -> None:
    """Non-incident-commander gets DENY even with incident_active=True."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_06",
        role="security_analyst",
        assigned_tenant="security-runbooks",
    )
    context = PolicyContext(caller_tenant="security-runbooks", incident_active=True)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="security-runbooks")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "default_deny"


def test_cross_tenant_access_denied() -> None:
    """Agent for tenant A cannot access tenant B data."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_07",
        role="saas_assistant",
        assigned_tenant="acme-corp",
    )
    context = PolicyContext(caller_tenant="acme-corp", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="globex-corp")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "cross_tenant_isolation"


def test_same_tenant_access_permitted() -> None:
    """Agent for tenant A CAN access tenant A data when authorized by a permit rule."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_08",
        role="employee",
        assigned_tenant="employee-handbook",
    )
    context = PolicyContext(caller_tenant="employee-handbook", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="employee-handbook")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "PERMIT"


def test_unregistered_tool_denied_by_default() -> None:
    """Tool not mentioned in any permit rule gets default deny."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_09",
        role="product_designer",
        assigned_tenant="employee-handbook",
    )
    context = PolicyContext(caller_tenant="employee-handbook", incident_active=False)
    resource = PolicyResource(tool_name="drop_all_tables", tenant_id="employee-handbook")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "default_deny"


# ── TRACE Claim Tests ──────────────────────────────────────────────


def test_trace_claim_contains_required_fields() -> None:
    """TRACE claim contains all required audit attributes."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    principal = PolicyPrincipal(
        session_id="sess_10",
        role="product_designer",
        assigned_tenant="employee-handbook",
    )
    context = PolicyContext(caller_tenant="employee-handbook", incident_active=False)
    tool_args = {"query": "PTO policy", "tenant_id": "employee-handbook"}

    result = gw.intercept_tool_call(
        principal=principal,
        tool_name="retrieve_evidence",
        tool_args=tool_args,
        context=context,
        executor=lambda t, a: [{"content": "PTO info"}],
    )

    assert result["status"] == 200
    claim_dict = result["trace_claim"]
    for field in [
        "claim_id",
        "session_id",
        "timestamp",
        "policy_bundle_hash",
        "verdict",
        "tool_call",
        "evidence_hashes",
        "signature",
    ]:
        assert field in claim_dict, f"Missing field: {field}"
        assert claim_dict[field]


def test_trace_claim_signature_verifies() -> None:
    """HMAC-SHA256 signature matches recomputed digest."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    verdict = PolicyVerdict("PERMIT", "employee_self_service", "Allowed")
    claim = gw.sign_trace_claim(
        session_id="sess_test_sig",
        verdict=verdict,
        tool_call={"tool_name": "retrieve_evidence", "args": {}},
        evidence_chunks=["sample evidence text"],
    )

    assert claim.verify(_DEV_KEY) is True
    assert claim.verify("wrong-signing-key") is False


def test_trace_claim_signature_fails_on_tamper() -> None:
    """Modifying any claim field invalidates the cryptographic signature."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    verdict = PolicyVerdict("PERMIT", "employee_self_service", "Allowed")
    claim = gw.sign_trace_claim(
        session_id="sess_test_tamper",
        verdict=verdict,
        tool_call={"tool_name": "retrieve_evidence", "args": {}},
        evidence_chunks=["original evidence text"],
    )
    assert claim.verify(_DEV_KEY) is True

    # Tamper with session_id
    claim.session_id = "attacker_session"
    assert claim.verify(_DEV_KEY) is False

    # Restore session_id, tamper with evidence hashes
    claim.session_id = "sess_test_tamper"
    assert claim.verify(_DEV_KEY) is True
    claim.evidence_hashes[0] = "tampered_hash_value"
    assert claim.verify(_DEV_KEY) is False


def test_trace_claim_evidence_hashes_match_chunks() -> None:
    """SHA-256 hashes in claim match the actual evidence chunk content."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    chunks = [
        {"id": 1, "text": "First chunk content"},
        {"id": 2, "text": "Second chunk content"},
    ]
    verdict = PolicyVerdict("PERMIT", "test_rule", "Allowed")
    claim = gw.sign_trace_claim(
        session_id="sess_hashes",
        verdict=verdict,
        tool_call={"tool_name": "retrieve_evidence", "args": {}},
        evidence_chunks=chunks,
    )

    assert len(claim.evidence_hashes) == 2
    for i, chunk in enumerate(chunks):
        expected = hash_evidence_chunk(chunk)
        assert claim.evidence_hashes[i] == expected


def test_trace_claim_policy_hash_matches_loaded_bundle() -> None:
    """policy_bundle_hash in claim matches SHA-256 of the loaded .cedar file."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    verdict = PolicyVerdict("PERMIT", "test_rule", "Allowed")
    claim = gw.sign_trace_claim(
        session_id="sess_bundle_hash",
        verdict=verdict,
        tool_call={},
        evidence_chunks=[],
    )

    raw_bytes = _POLICY_FILE.read_bytes()
    expected_hash = hashlib.sha256(raw_bytes).hexdigest()
    assert claim.policy_bundle_hash == expected_hash
    assert gw.policy_bundle_hash == expected_hash


# ── Forbid-Takes-Precedence Tests ──────────────────────────────────


def test_forbid_overrides_permit_for_compensation() -> None:
    """Even if an agent possesses a generic permit, the compensation forbid wins."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    # Principal role is NOT hr_business_partner
    principal = PolicyPrincipal(
        session_id="sess_forbid_01",
        role="software_engineer",
        assigned_tenant="hr-compensation",
    )
    context = PolicyContext(caller_tenant="hr-compensation", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="hr-compensation")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "compensation_firewall"


def test_forbid_cross_tenant_overrides_handbook_permit() -> None:
    """Cross-tenant forbid blocks even employee-handbook if caller tenant does not match."""
    gw = CmcpGateway(policy_file=_POLICY_FILE, signing_key=_DEV_KEY)
    # Agent assigned to external tenant tries to search employee-handbook
    principal = PolicyPrincipal(
        session_id="sess_forbid_02",
        role="contractor",
        assigned_tenant="external-vendor",
    )
    context = PolicyContext(caller_tenant="external-vendor", incident_active=False)
    resource = PolicyResource(tool_name="retrieve_evidence", tenant_id="employee-handbook")

    verdict = gw.evaluate(principal, "call_tool", resource, context)
    assert verdict.decision == "DENY"
    assert verdict.matched_rule == "cross_tenant_isolation"

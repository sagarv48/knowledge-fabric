"""Security hardening test suite for Knowledge Fabric.

Validates mitigations against:
1. Spoofing & Injection (Tenant ID validation & sanitization)
2. Denial of Service (Query length bounding, top_k bounds, and reranker candidate capping)
3. UI Server endpoint input validation and HMAC signing
"""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock
import pytest

from knowledge_fabric.retrieval.models import RetrievalHit
from knowledge_fabric.retrieval.pipeline import (
    RetrievalPipeline,
    validate_tenant_id,
)
from knowledge_fabric.ui.server import DashboardRequestHandler


def test_tenant_id_validation() -> None:
    """tenant_id supports enterprise namespaces (UUIDs, emails, domains, URNs) while blocking attacks."""
    # Valid enterprise tenant formats
    assert validate_tenant_id(None) is None
    assert validate_tenant_id("") is None
    assert validate_tenant_id("   ") is None
    assert validate_tenant_id("engineering") == "engineering"
    assert validate_tenant_id("sec-ops_01") == "sec-ops_01"
    assert validate_tenant_id("TENANT_CORP") == "TENANT_CORP"
    assert validate_tenant_id("corp.finance.apac") == "corp.finance.apac"
    assert validate_tenant_id("analyst@corp.com") == "analyst@corp.com"
    assert validate_tenant_id("urn:tenant:finance-01") == "urn:tenant:finance-01"
    assert validate_tenant_id("123e4567-e89b-12d3-a456-426614174000") == "123e4567-e89b-12d3-a456-426614174000"

    # Malformed or adversarial tenant IDs must raise ValueError
    with pytest.raises(ValueError, match="Invalid tenant_id format"):
        validate_tenant_id("../../etc/passwd")  # Path traversal

    with pytest.raises(ValueError, match="Invalid tenant_id format"):
        validate_tenant_id("tenant; DROP TABLE chunks;--")  # SQL injection

    with pytest.raises(ValueError, match="Invalid tenant_id format"):
        validate_tenant_id("tenant\0")  # Null byte injection

    with pytest.raises(ValueError, match="Invalid tenant_id format"):
        validate_tenant_id("a" * 129)  # Length overflow


def test_pipeline_query_and_limit_bounds() -> None:
    """RetrievalPipeline must bound top_k and query string with configurable limits."""
    mock_store = MagicMock()
    mock_store.lexical_search.return_value = []
    mock_store.vector_search.return_value = []

    mock_provider = MagicMock()
    mock_provider.embed_texts.return_value = [[0.1] * 768]

    # Pipeline with custom enterprise bounds (e.g. 5000 chars query, top_k up to 200)
    pipeline = RetrievalPipeline(
        retrieval_store=mock_store,
        embedding_provider=mock_provider,
        max_query_length=5000,
        max_top_k=200,
    )

    # 1. Test top_k capping when caller passes an excessive value (e.g. 500)
    pipeline.retrieve_evidence(query_text="test", top_k=500, tenant_id="tenant_01")
    call_args = mock_store.lexical_search.call_args[1]
    assert call_args["top_k"] == 200  # Capped at configured max_top_k

    # 2. Test top_k lower bound when caller passes 0 or negative
    pipeline.retrieve_evidence(query_text="test", top_k=-10)
    call_args_low = mock_store.lexical_search.call_args[1]
    assert call_args_low["top_k"] == 1

    # 3. Test query length truncation when query exceeds max_query_length
    giant_query = "A" * 6000
    pipeline.retrieve_evidence(query_text=giant_query, top_k=5)
    called_query = mock_store.lexical_search.call_args[0][0]
    assert len(called_query) == 5000
    assert called_query == "A" * 5000


def test_reranker_candidate_pool_is_capped() -> None:
    """Reranker candidate pool must be capped at _MAX_RERANK_CANDIDATES to prevent CPU DoS."""
    # Create 100 dummy chunks
    hundred_hits = [
        RetrievalHit(
            chunk_id=i,
            document_id=1,
            document_uri=f"doc_{i}",
            chunk_index=i,
            chunk_text=f"Chunk content {i}",
            score=0.9,
            source="file",
            metadata={"tenant_id": "default"},
        )
        for i in range(100)
    ]

    mock_store = MagicMock()
    mock_store.lexical_search.return_value = hundred_hits
    mock_store.vector_search.return_value = []

    mock_provider = MagicMock()
    mock_provider.embed_texts.return_value = [[0.1] * 768]

    mock_reranker = MagicMock()
    mock_reranker.rerank.side_effect = lambda q, chunks, top_n: chunks[:top_n]

    pipeline = RetrievalPipeline(
        retrieval_store=mock_store,
        embedding_provider=mock_provider,
        reranker=mock_reranker,
        max_rerank_candidates=50,
    )

    pipeline.retrieve_evidence(query_text="test query", top_k=10)
    # Verify the reranker received at most 50 candidate chunks, not all 100
    candidates_passed = mock_reranker.rerank.call_args[0][1]
    assert len(candidates_passed) <= 50


def _make_handler(method: str, path: str, body: dict | None = None) -> DashboardRequestHandler:
    mock_request = MagicMock()
    mock_client_address = ("127.0.0.1", 12345)
    mock_server = MagicMock()

    body_bytes = json.dumps(body).encode("utf-8") if body else b""

    handler = DashboardRequestHandler.__new__(DashboardRequestHandler)
    handler.command = method
    handler.path = path
    handler.request_version = "HTTP/1.1"
    handler.headers = {
        "Content-Length": str(len(body_bytes)),
        "Content-Type": "application/json",
    }
    handler.rfile = io.BytesIO(body_bytes)
    handler.wfile = io.BytesIO()
    handler.request = mock_request
    handler.client_address = mock_client_address
    handler.server = mock_server
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


def test_ui_retrieval_endpoint_rejects_invalid_tenant() -> None:
    """UI server must return HTTP 400 when an invalid tenant_id is supplied."""
    handler = _make_handler(
        "POST",
        "/api/retrieval/query",
        {"query": "find sensitive files", "tenant_id": "../../malicious/path"},
    )
    handler.do_POST()

    assert handler.send_response.call_args[0][0] == 400
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "Invalid tenant_id" in res["error"]


def test_ui_policy_test_endpoint_denies_smuggled_action() -> None:
    """UI policy sandbox must return 'deny' for actions with invalid syntax."""
    handler = _make_handler(
        "POST",
        "/api/policies/test",
        {"action": "db_drop_table "},  # trailing space evasion
    )
    handler.do_POST()

    assert handler.send_response.call_args[0][0] == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert res["decision"] == "deny"
    assert "failed syntax validation" in res["reason"]


def test_ui_post_approval_generates_hmac_signature() -> None:
    """Posting an approval decision in the UI server must generate a valid HMAC signature."""
    handler = _make_handler(
        "POST",
        "/api/approvals/appr_test_01/decision",
        {"decision": "Approved", "reviewer": "secops@corp.com", "comment": "Verified"},
    )
    handler.do_POST()

    assert handler.send_response.call_args[0][0] == 200
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert res["decision"] == "Approved"
    assert res["status"] == "resolved"
    assert "signature" in res
    assert len(res["signature"]) == 64
    assert res["algorithm"] == "HMAC-SHA256"

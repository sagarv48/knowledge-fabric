"""Unit tests for the Knowledge Fabric & Intent Fabric Admin UI server."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

from knowledge_fabric.ui.server import DashboardRequestHandler


def _make_handler(method: str, path: str, body: dict | None = None) -> DashboardRequestHandler:
    """Instantiate a DashboardRequestHandler with mocked input and output streams."""
    mock_request = MagicMock()
    mock_client_address = ("127.0.0.1", 12345)
    mock_server = MagicMock()

    body_bytes = json.dumps(body).encode("utf-8") if body else b""

    # Patch handler initialization
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

    # Methods called by http.server
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


def test_api_health_endpoint() -> None:
    handler = _make_handler("GET", "/api/health")
    handler.do_GET()

    assert handler.send_response.call_args[0][0] == 200
    response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert response_body["status"] == "ok"
    assert response_body["postgres"] == "connected"


def test_api_approvals_endpoint() -> None:
    handler = _make_handler("GET", "/api/approvals")
    handler.do_GET()

    assert handler.send_response.call_args[0][0] == 200
    response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert isinstance(response_body, list)
    assert len(response_body) > 0
    assert response_body[0]["approval_id"] == "appr_sec_7a2f"
    assert response_body[0]["tenant_id"] == "security-ops"


def test_api_post_approval_decision() -> None:
    handler = _make_handler(
        "POST",
        "/api/approvals/appr_sec_7a2f/decision",
        {"decision": "Approved", "comment": "Approved by SecOps lead"},
    )
    handler.do_POST()

    assert handler.send_response.call_args[0][0] == 200
    response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert response_body["approval_id"] == "appr_sec_7a2f"
    assert response_body["decision"] == "Approved"
    assert response_body["status"] == "resolved"


def test_api_post_policy_test() -> None:
    handler = _make_handler("POST", "/api/policies/test", {"action": "db_drop_table"})
    handler.do_POST()

    assert handler.send_response.call_args[0][0] == 200
    response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert response_body["decision"] == "deny"

    # Test approval action
    handler_ticket = _make_handler("POST", "/api/policies/test", {"action": "ticket_create"})
    handler_ticket.do_POST()
    ticket_body = json.loads(handler_ticket.wfile.getvalue().decode("utf-8"))
    assert ticket_body["decision"] == "requires_approval"


def test_static_index_serving() -> None:
    handler = _make_handler("GET", "/")
    handler.do_GET()

    assert handler.send_response.call_args[0][0] == 200
    content = handler.wfile.getvalue().decode("utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Governance &amp; Evidence Retrieval Console" in content


def test_static_logo_serving() -> None:
    handler = _make_handler("GET", "/logo.svg")
    handler.do_GET()

    assert handler.send_response.call_args[0][0] == 200
    content = handler.wfile.getvalue().decode("utf-8")
    assert "<svg" in content
    assert "url(#shieldGrad)" in content


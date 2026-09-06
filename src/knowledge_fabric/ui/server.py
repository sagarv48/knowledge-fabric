"""Lightweight HTTP server for Knowledge Fabric & Intent Fabric Admin UI."""

from __future__ import annotations

import argparse
import json
import logging
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

logger = logging.getLogger("knowledge_fabric.ui")
_STATIC_DIR = Path(__file__).resolve().parent / "static"


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """Handles REST API requests and serves dashboard static assets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(_STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._serve_file(_STATIC_DIR / "index.html", "text/html")
        elif self.path == "/logo.svg":
            self._serve_file(_STATIC_DIR / "logo.svg", "image/svg+xml")
        elif self.path == "/api/health":
            self._handle_health()
        elif self.path == "/api/approvals":
            self._handle_get_approvals()
        elif self.path == "/api/audit":
            self._handle_get_audit()
        elif self.path == "/api/policies":
            self._handle_get_policies()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api/approvals/") and self.path.endswith("/decision"):
            self._handle_post_approval_decision()
        elif self.path == "/api/retrieval/query":
            self._handle_post_retrieval_query()
        elif self.path == "/api/policies/test":
            self._handle_post_policy_test()
        else:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def _serve_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def _handle_health(self) -> None:
        self._send_json({
            "status": "ok",
            "version": "0.1.0",
            "postgres": "connected",
            "embedding_provider": os.environ.get("EMBEDDING_PROVIDER", "ollama"),
            "planner": os.environ.get("INTENT_PLANNER", "ollama"),
        })

    def _handle_get_approvals(self) -> None:
        # Sample active approvals queue
        self._send_json([
            {
                "approval_id": "appr_sec_7a2f",
                "tenant_id": "security-ops",
                "summary": "Emergency access review for user jdoe@corp.com",
                "source": "access_control_standard.md §4.2",
                "requires_approval": True,
                "reasons": [
                    "Ticket creation requires human review before execution.",
                    "User notifications require human review.",
                ],
                "steps": [
                    {"step": "1. Retrieve user AD privileges", "type": "analysis_review", "status": "allow"},
                    {"step": "2. Create Jira post-incident ticket", "type": "ticket_create", "status": "requires_approval"},
                    {"step": "3. Dispatch alert to Security Channel", "type": "notification_send", "status": "requires_approval"},
                ],
            }
        ])

    def _handle_post_approval_decision(self) -> None:
        parts = self.path.split("/")
        approval_id = parts[3] if len(parts) > 3 else "unknown"
        body = self._read_body_json()
        decision = body.get("decision", "Approved")
        comment = body.get("comment", "")
        self._send_json({
            "approval_id": approval_id,
            "decision": decision,
            "status": "resolved",
            "comment": comment,
            "timestamp": "now",
        })

    def _handle_get_audit(self) -> None:
        self._send_json([
            {
                "event_type": "retrieval_run",
                "actor": "analyst@corp.com",
                "tenant_id": "security-ops",
                "details": "Query: 'What is the process for emergency access provisioning?'",
                "latency_ms": 8,
                "timestamp": "2026-09-06T15:00:00Z",
            },
            {
                "event_type": "policy_evaluation",
                "actor": "policy_engine",
                "tenant_id": "security-ops",
                "details": "Evaluated plan_8b2e -> REQUIRES_APPROVAL (rules: ticket_*, notification_send)",
                "timestamp": "2026-09-06T14:58:00Z",
            },
        ])

    def _handle_post_retrieval_query(self) -> None:
        body = self._read_body_json()
        query = body.get("query", "emergency access")
        tenant_id = body.get("tenant_id", "default")
        self._send_json({
            "query": query,
            "tenant_id": tenant_id,
            "latency_ms": 7,
            "hits": [
                {
                    "score": 0.9416,
                    "source": "access_control_standard.md §4.2",
                    "snippet": "Emergency access provisioning requires explicit CISO or designated Incident Commander sign-off.",
                },
                {
                    "score": 0.8120,
                    "source": "change_management_policy.md §2.2",
                    "snippet": "All emergency changes must be logged and linked directly to an active P1/P2 incident record.",
                },
            ],
        })

    def _handle_get_policies(self) -> None:
        self._send_json({
            "rules": [
                {"pattern": "db_*", "decision": "deny", "priority": 100, "reason": "Destructive database operations are prohibited."},
                {"pattern": "external_write", "decision": "deny", "priority": 100, "reason": "Direct writes outside sandbox are forbidden."},
                {"pattern": "ticket_*", "decision": "requires_approval", "priority": 50, "reason": "Ticket creation requires human approval."},
                {"pattern": "notification_send", "decision": "requires_approval", "priority": 50, "reason": "User notifications require review."},
                {"pattern": "analysis_*", "decision": "allow", "priority": 10, "reason": "Read-only actions are pre-approved."},
            ]
        })

    def _handle_post_policy_test(self) -> None:
        body = self._read_body_json()
        action = body.get("action", "").lower().strip()
        if action.startswith("db_") or "drop" in action:
            self._send_json({"action": action, "decision": "deny", "reason": "Destructive operations are strictly prohibited."})
        elif action.startswith("ticket_") or action.startswith("notification_"):
            self._send_json({"action": action, "decision": "requires_approval", "reason": "External actions require human review."})
        else:
            self._send_json({"action": action, "decision": "allow", "reason": "Read-only inspection pre-approved."})


def run_ui_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, DashboardRequestHandler)
    print(f"\n\U0001f310 Knowledge Fabric & Intent Fabric Admin Console")
    print(f"   Dashboard running at: http://{host}:{port}/")
    print(f"   Press Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Admin Console...")
    finally:
        httpd.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Knowledge Fabric & Intent Fabric Admin Dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port number (default: 8080)")
    args = parser.parse_args(argv)
    run_ui_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

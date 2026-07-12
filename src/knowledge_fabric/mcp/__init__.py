"""MCP retrieval tool surface."""

from knowledge_fabric.mcp.server import build_tools_from_settings, create_mcp_server, run_mcp_server
from knowledge_fabric.mcp.tools import KnowledgeFabricMCPTools

__all__ = ["KnowledgeFabricMCPTools", "build_tools_from_settings", "create_mcp_server", "run_mcp_server"]

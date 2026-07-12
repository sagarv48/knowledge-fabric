from __future__ import annotations

from types import ModuleType

from knowledge_fabric.mcp.server import create_mcp_server


class _FakeFastMCP:
    def __init__(self, name: str) -> None:
        self.name = name
        self.tool_names: list[str] = []

    def tool(self, name: str):
        def _decorator(func):
            self.tool_names.append(name)
            return func

        return _decorator

    def run(self) -> None:
        return


class _FakeTools:
    @staticmethod
    def retrieve_evidence(**kwargs):
        return {"ok": True, "kwargs": kwargs}

    @staticmethod
    def get_document(**kwargs):
        return {"ok": True, "kwargs": kwargs}

    @staticmethod
    def explain_retrieval(**kwargs):
        return {"ok": True, "kwargs": kwargs}


def test_create_mcp_server_registers_expected_tools(monkeypatch) -> None:
    fastmcp_module = ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = _FakeFastMCP
    monkeypatch.setitem(__import__("sys").modules, "mcp.server.fastmcp", fastmcp_module)

    server = create_mcp_server(_FakeTools())

    assert server.name == "knowledge-fabric"
    assert sorted(server.tool_names) == ["explain_retrieval", "get_document", "retrieve_evidence"]

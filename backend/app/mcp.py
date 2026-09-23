"""Core MCP (Model Context Protocol) engine.

Implements the JSON-RPC 2.0 methods an MCP server must answer:
  initialize, tools/list, tools/call, resources/list, resources/read, ping.

Tools are bound to MongoDB collections with safe, templated operations.
"""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas import JsonRpcRequest, JsonRpcResponse

MAX_LIMIT = 50
PROTOCOL_VERSION = "2024-11-05"


class McpEngine:
    """Stateless JSON-RPC dispatcher bound to one MCP server definition."""

    def __init__(self, server: dict[str, Any], tools: list[dict[str, Any]], db: AsyncIOMotorDatabase) -> None:
        self.server = server
        self.tools = tools
        self.db = db

    async def handle(self, req: JsonRpcRequest) -> JsonRpcResponse:
        methods = {
            "initialize": self._initialize,
            "ping": self._ping,
            "tools/list": self._tools_list,
            "tools/call": self._tools_call,
            "resources/list": self._resources_list,
            "resources/read": self._resources_read,
        }
        handler = methods.get(req.method)
        if handler is None:
            return JsonRpcResponse(id=req.id, error={"code": -32601, "message": f"method not found: {req.method}"})
        try:
            result = await handler(req.params)
            return JsonRpcResponse(id=req.id, result=result)
        except Exception as exc:  # noqa: BLE001
            return JsonRpcResponse(id=req.id, error={"code": -32000, "message": str(exc)})

    async def _initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False}},
            "serverInfo": {"name": self.server["name"], "version": "0.1.0"},
        }

    async def _ping(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}

    async def _tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "tools": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "filter": {"type": "object", "description": "MongoDB filter"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": MAX_LIMIT},
                        },
                    },
                }
                for t in self.tools
            ]
        }

    def _find_tool(self, name: str) -> dict[str, Any] | None:
        return next((t for t in self.tools if t["name"] == name), None)

    async def _tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name", "")
        arguments = params.get("arguments", {}) or {}
        tool = self._find_tool(name)
        if tool is None:
            raise ValueError(f"unknown tool: {name}")

        coll = self.db[tool["source_collection"]]
        flt = dict(tool.get("filter_template") or {})
        flt.update(arguments.get("filter") or {})
        limit = min(int(arguments.get("limit", 10)), MAX_LIMIT)

        if tool["operation"] == "count":
            count = await coll.count_documents(flt)
            content = [{"type": "text", "text": str(count)}]
        elif tool["operation"] == "aggregate":
            docs = await coll.aggregate([{"$match": flt}, {"$limit": limit}]).to_list(limit)
            content = [{"type": "text", "text": str(docs)}]
        else:
            docs = await coll.find(flt).to_list(limit)
            docs = [{**d, "_id": str(d["_id"])} for d in docs]
            content = [{"type": "text", "text": str(docs)}]
        return {"content": content, "isError": False}

    async def _resources_list(self, params: dict[str, Any]) -> dict[str, Any]:
        resources = self.server.get("resources", [])
        return {
            "resources": [
                {"uri": r["uri"], "name": r["name"], "mimeType": "application/json"} for r in resources
            ]
        }

    async def _resources_read(self, params: dict[str, Any]) -> dict[str, Any]:
        uri = params.get("uri", "")
        resources = self.server.get("resources", [])
        resource = next((r for r in resources if r["uri"] == uri), None)
        if resource is None:
            raise ValueError(f"unknown resource uri: {uri}")
        coll = self.db[resource["source_collection"]]
        docs = await coll.find({}).to_list(MAX_LIMIT)
        docs = [{**d, "_id": str(d["_id"])} for d in docs]
        return {"contents": [{"uri": uri, "mimeType": "application/json", "text": str(docs)}]}

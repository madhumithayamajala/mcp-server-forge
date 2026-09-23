"""End-to-end MCP protocol tests over the JSON-RPC endpoint."""

import pytest

pytestmark = pytest.mark.asyncio


async def _make_server(client):
    res = await client.post("/api/servers", json={"name": "demo-server", "description": "demo"})
    sid = res.json()["id"]
    await client.post(
        "/api/servers/{}/tools".format(sid),
        json={
            "name": "list_orders",
            "description": "List orders from MongoDB",
            "source_collection": "orders",
            "operation": "find",
        },
    )
    await client.post(
        "/api/servers/{}/tools".format(sid),
        json={
            "name": "count_orders",
            "description": "Count orders",
            "source_collection": "orders",
            "operation": "count",
        },
    )
    # seed data through the tool itself later; seed collection directly
    return sid


async def test_health(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


async def test_initialize_handshake(client):
    sid = await _make_server(client)
    res = await client.post(
        f"/api/servers/{sid}/rpc",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["result"]["serverInfo"]["name"] == "demo-server"
    assert body["result"]["protocolVersion"] == "2024-11-05"


async def test_tools_list(client):
    sid = await _make_server(client)
    res = await client.post(
        f"/api/servers/{sid}/rpc",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    tools = res.json()["result"]["tools"]
    assert {t["name"] for t in tools} == {"list_orders", "count_orders"}


async def test_tools_call_find(client):
    sid = await _make_server(client)
    # seed via direct engine call through count tool first
    res = await client.post(
        f"/api/servers/{sid}/rpc",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_orders", "arguments": {"filter": {}, "limit": 10}},
        },
    )
    body = res.json()
    assert body["result"]["isError"] is False
    assert "content" in body["result"]


async def test_unknown_method_returns_error(client):
    sid = await _make_server(client)
    res = await client.post(
        f"/api/servers/{sid}/rpc",
        json={"jsonrpc": "2.0", "id": 4, "method": "nope", "params": {}},
    )
    assert res.json()["error"]["code"] == -32601


async def test_unknown_tool_returns_error(client):
    sid = await _make_server(client)
    res = await client.post(
        f"/api/servers/{sid}/rpc",
        json={"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "ghost"}},
    )
    assert res.json()["error"]["code"] == -32000

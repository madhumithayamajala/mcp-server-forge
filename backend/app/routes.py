"""REST endpoints — manage MCP server definitions and speak JSON-RPC."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.mcp import McpEngine
from app.schemas import (
    JsonRpcRequest,
    JsonRpcResponse,
    ResourceCreate,
    ServerCreate,
    ToolCreate,
)

router = APIRouter()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id") from None


@router.get("/health", tags=["system"])
async def health(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    await db.command("ping")
    return {"status": "ok", "service": "mcp-server-forge", "time": datetime.now(timezone.utc).isoformat()}


@router.post("/servers", status_code=201, tags=["servers"])
async def create_server(payload: ServerCreate, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    now = utcnow()
    doc = {"name": payload.name, "description": payload.description, "resources": [], "created_at": now}
    result = await db.servers.insert_one(doc)
    doc.pop("_id", None)  # insert_one mutates doc in place, adding _id
    return {
        "id": str(result.inserted_id),
        "name": payload.name,
        "description": payload.description,
        "resources": [],
    }


@router.get("/servers", tags=["servers"])
async def list_servers(db: AsyncIOMotorDatabase = Depends(get_db)) -> list[dict]:
    docs = await db.servers.find().sort("created_at", -1).to_list(100)
    return [{**d, "_id": str(d["_id"]), "created_at": str(d.get("created_at"))} for d in docs]


@router.post("/servers/{server_id}/tools", status_code=201, tags=["tools"])
async def add_tool(server_id: str, payload: ToolCreate, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    doc = payload.model_dump()
    doc["server_id"] = str(_oid(server_id))
    result = await db.tools.insert_one(doc)
    doc.pop("_id", None)  # insert_one mutates doc in place, adding _id
    return {"id": str(result.inserted_id), **doc}


@router.get("/servers/{server_id}/tools", tags=["tools"])
async def list_tools(server_id: str, db: AsyncIOMotorDatabase = Depends(get_db)) -> list[dict]:
    docs = await db.tools.find({"server_id": server_id}).to_list(100)
    return [{**d, "_id": str(d["_id"])} for d in docs]


@router.post("/servers/{server_id}/resources", status_code=201, tags=["resources"])
async def add_resource(server_id: str, payload: ResourceCreate, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    sid = str(_oid(server_id))
    doc = payload.model_dump()
    await db.servers.update_one({"_id": ObjectId(sid)}, {"$push": {"resources": doc}})
    return {"ok": True, "resource": doc}


@router.post("/servers/{server_id}/rpc", response_model=JsonRpcResponse, tags=["mcp"])
async def rpc(server_id: str, body: JsonRpcRequest, db: AsyncIOMotorDatabase = Depends(get_db)) -> JsonRpcResponse:
    sid = str(_oid(server_id))
    server = await db.servers.find_one({"_id": ObjectId(sid)})
    if server is None:
        raise HTTPException(status_code=404, detail="server not found")
    tools = await db.tools.find({"server_id": sid}).to_list(100)
    tools = [{**t, "_id": str(t["_id"])} for t in tools]
    server = {**server, "_id": sid, "created_at": str(server.get("created_at"))}
    engine = McpEngine(server, tools, db)
    return await engine.handle(body)

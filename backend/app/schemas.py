"""Pydantic schemas — MCP servers, tools, resources, JSON-RPC messages."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    name: str = Field(min_length=3, max_length=60)
    description: str = Field(default="", max_length=300)


class ToolCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(max_length=200)
    source_collection: str
    operation: Literal["find", "count", "aggregate"] = "find"
    filter_template: dict[str, Any] = {}


class ResourceCreate(BaseModel):
    name: str
    uri: str = Field(pattern=r"^mcp://.+")
    source_collection: str


class JsonRpcRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: int | str | None = None
    method: str
    params: dict[str, Any] = {}


class JsonRpcResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: int | str | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

# MCP Server Forge

Build **Model Context Protocol (MCP)** servers over your MongoDB data — no boilerplate.

Define tools in the UI, bind them to collections, and every server immediately speaks
JSON-RPC 2.0 with the standard MCP methods: `initialize`, `tools/list`, `tools/call`,
`resources/list`, `resources/read`, `ping`.

## Architecture

```
MCP Client (Claude, IDE, curl)
   │  JSON-RPC 2.0
   ▼
POST /api/servers/{id}/rpc ──► McpEngine
                                 ├─ initialize   → protocol handshake
                                 ├─ tools/list   → tool inventory
                                 ├─ tools/call   → safe templated MongoDB ops
                                 ├─ resources/*  → collection snapshots
                                 └─ ping
MongoDB (motor async) ── servers, tools, bound collections
```

- **Backend**: FastAPI + motor; `McpEngine` implements the MCP method surface
- **Frontend**: React + Vite + Tailwind — server manager, tool builder, live RPC playground
- **Infra**: docker-compose (MongoDB 7 + api + web), Makefile, GitHub Actions CI

## Quick start

```bash
make up        # builds and starts mongo + api + web
# API  → http://localhost:8001/docs
# Web  → http://localhost:5174
make down
```

## Run tests

```bash
make test      # end-to-end MCP protocol tests, in-process
```

## Try the protocol with curl

```bash
# create a server
curl -X POST localhost:8001/api/servers -H 'Content-Type: application/json' \
  -d '{"name":"demo","description":"demo server"}'

# initialize handshake
curl -X POST localhost:8001/api/servers/<ID>/rpc -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

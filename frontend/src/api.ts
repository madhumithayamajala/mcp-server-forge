export interface McpServer {
  id: string;
  name: string;
  description: string;
  resources: { uri: string; name: string }[];
}

export interface McpTool {
  id: string;
  name: string;
  description: string;
  source_collection: string;
  operation: string;
}

const BASE = "/api";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export async function listServers(): Promise<McpServer[]> {
  return json(await fetch(`${BASE}/servers`));
}

export async function createServer(payload: { name: string; description: string }): Promise<{ id: string }> {
  return json(
    await fetch(`${BASE}/servers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function listTools(serverId: string): Promise<McpTool[]> {
  return json(await fetch(`${BASE}/servers/${serverId}/tools`));
}

export async function addTool(
  serverId: string,
  payload: { name: string; description: string; source_collection: string; operation: string }
): Promise<{ id: string }> {
  return json(
    await fetch(`${BASE}/servers/${serverId}/tools`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export interface RpcResponse {
  result?: { content?: { text: string }[]; isError?: boolean };
  error?: { code: number; message: string };
}

export async function rpc(serverId: string, method: string, params: object): Promise<RpcResponse> {
  return json(
    await fetch(`${BASE}/servers/${serverId}/rpc`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }),
    })
  );
}

import { useCallback, useEffect, useState } from "react";
import { addTool, createServer, listServers, listTools, McpServer, McpTool, rpc, RpcResponse } from "./api";

export default function App() {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [tools, setTools] = useState<McpTool[]>([]);
  const [name, setName] = useState("");
  const [toolName, setToolName] = useState("");
  const [toolColl, setToolColl] = useState("");
  const [toolOp, setToolOp] = useState("find");
  const [rpcResult, setRpcResult] = useState<RpcResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await listServers();
      setServers(list);
      if (!selected && list.length > 0) setSelected(list[0].id);
    } catch (e) {
      setError(String(e));
    }
  }, [selected]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!selected) return;
    listTools(selected).then(setTools).catch((e) => setError(String(e)));
  }, [selected]);

  const submitServer = async () => {
    if (name.length < 3) return;
    try {
      const created = await createServer({ name, description: "Created from web UI" });
      setName("");
      setSelected(created.id);
      await refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const submitTool = async () => {
    if (!selected || toolName.length < 2 || toolColl.length < 2) return;
    try {
      await addTool(selected, {
        name: toolName,
        description: `Query ${toolColl} (${toolOp})`,
        source_collection: toolColl,
        operation: toolOp,
      });
      setToolName("");
      setToolColl("");
      setTools(await listTools(selected));
    } catch (e) {
      setError(String(e));
    }
  };

  const call = async (method: string, params: object) => {
    if (!selected) return;
    try {
      setRpcResult(await rpc(selected, method, params));
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">MCP Server Forge</h1>
            <p className="text-sm text-slate-400">
              Build Model Context Protocol servers over MongoDB — no boilerplate
            </p>
          </div>
          <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded">MCP · JSON-RPC 2.0</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {error && (
          <div className="lg:col-span-3 bg-rose-950 border border-rose-800 text-rose-300 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <section className="space-y-3">
          <h2 className="font-medium text-sm uppercase tracking-wide text-slate-400">Servers</h2>
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm"
              placeholder="new server name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button className="bg-indigo-600 rounded-lg px-3 py-2 text-sm font-medium" onClick={submitServer}>
              Create
            </button>
          </div>
          <div className="space-y-2">
            {servers.map((s) => (
              <button
                key={s.id}
                className={`w-full text-left rounded-lg border px-3 py-2 text-sm ${
                  selected === s.id ? "border-indigo-500 bg-indigo-950/50" : "border-slate-800 bg-slate-900"
                }`}
                onClick={() => setSelected(s.id)}
              >
                <div className="font-medium">{s.name}</div>
                <div className="text-xs text-slate-400">{s.description || "no description"}</div>
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="font-medium text-sm uppercase tracking-wide text-slate-400">Tools</h2>
          {selected && (
            <div className="space-y-2 bg-slate-900 border border-slate-800 rounded-lg p-3">
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm"
                placeholder="tool_name (snake_case)"
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
              />
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm"
                placeholder="mongo collection"
                value={toolColl}
                onChange={(e) => setToolColl(e.target.value)}
              />
              <select
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm"
                value={toolOp}
                onChange={(e) => setToolOp(e.target.value)}
              >
                <option value="find">find</option>
                <option value="count">count</option>
                <option value="aggregate">aggregate</option>
              </select>
              <button className="w-full bg-emerald-600 rounded px-3 py-2 text-sm font-medium" onClick={submitTool}>
                Bind tool
              </button>
            </div>
          )}
          <div className="space-y-2">
            {tools.map((t) => (
              <div key={t.id} className="border border-slate-800 bg-slate-900 rounded-lg px-3 py-2 text-sm">
                <div className="font-mono text-indigo-300">{t.name}</div>
                <div className="text-xs text-slate-400">
                  {t.source_collection} · {t.operation}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="font-medium text-sm uppercase tracking-wide text-slate-400">MCP Playground</h2>
          <div className="flex flex-wrap gap-2">
            <button
              className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
              onClick={() => call("initialize", {})}
            >
              initialize
            </button>
            <button
              className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
              onClick={() => call("tools/list", {})}
            >
              tools/list
            </button>
            <button
              className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
              onClick={() => call("ping", {})}
            >
              ping
            </button>
            {tools[0] && (
              <button
                className="bg-indigo-600 rounded px-3 py-1.5 text-sm"
                onClick={() => call("tools/call", { name: tools[0].name, arguments: { filter: {}, limit: 5 } })}
              >
                call {tools[0].name}
              </button>
            )}
          </div>
          <pre className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs overflow-auto max-h-96">
            {rpcResult ? JSON.stringify(rpcResult, null, 2) : "Run an RPC method to see the response…"}
          </pre>
        </section>
      </main>
    </div>
  );
}

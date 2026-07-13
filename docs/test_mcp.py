"""Cliente MCP minimo para verificar que el servidor funciona."""
import subprocess
import json
import os

env = {**os.environ, "LOG_LEVEL": "WARNING"}
proc = subprocess.Popen(
    ["uv", "run", "python", "-m", "app.mcp.server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=r"d:\Code\Python\Personal Finance MCP Server",
    env=env,
)


def send(msg):
    line = json.dumps(msg) + "\n"
    proc.stdin.write(line.encode())
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())


r1 = send({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}},
})
info = r1.get("result", {}).get("serverInfo", {})
print(f"INIT: name={info.get('name')} version={info.get('version')}")

r2 = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
tools = [t["name"] for t in r2.get("result", {}).get("tools", [])]
print(f"TOOLS ({len(tools)}): {tools}")

r3 = send({
    "jsonrpc": "2.0", "id": 3, "method": "tools/call",
    "params": {"name": "list_accounts", "arguments": {}},
})
content = r3.get("result", {}).get("content", [{}])
print("list_accounts:", content[0].get("text", "")[:400])

proc.terminate()

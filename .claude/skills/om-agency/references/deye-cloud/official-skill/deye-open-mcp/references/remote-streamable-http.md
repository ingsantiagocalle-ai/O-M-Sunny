# Deye Open MCP Remote Streamable HTTP Notes

Use this reference when converting or maintaining `<YOUR_DEYE_OPEN_MCP_PROJECT_PATH>` as a remote MCP service rather than a local stdio-only server.

## Desired service shape

- Default transport: `streamable-http`.
- Default endpoint: `http://127.0.0.1:12050/mcp` locally, normally `https://<domain>/mcp` behind a reverse proxy for remote use.
- `FastMCP` should be configured with `streamable_http_path=os.getenv("DEYE_MCP_PATH", "/mcp")` and `stateless_http=False` so MCP sessions are stateful.
- Expose host/port/path through env vars: `DEYE_MCP_HOST`, `DEYE_MCP_PORT`, `DEYE_MCP_PATH`, `DEYE_MCP_TRANSPORT`.
- `main()` should default to `mcp.run(transport="streamable-http")`, while optionally accepting `stdio`/`sse` only for compatibility.

## Multi-user session isolation

The safe default is never to keep one global `DeyeClient` shared by every connected user.

Preferred design:

1. Use stateful Streamable HTTP sessions (`stateless_http=False`).
2. Scope Deye credential/token state to the MCP session.
3. If session context access is unavailable or uncertain, fall back to creating a fresh `DeyeClient` per tool call rather than using global mutable token state.
4. For AI-tool usability, prefer same-session token reuse where possible: a user can call `get_access_token` once, then subsequent tools in the same MCP session can use that token without leaking to other sessions.

Implementation pattern to consider:

```python
from mcp.server.fastmcp import Context, FastMCP

_session_clients: dict[str, DeyeClient] = {}

def _session_key(ctx: Context | None) -> str | None:
    if ctx is None:
        return None
    request_context = getattr(ctx, "request_context", None)
    session = getattr(request_context, "session", None)
    for candidate in (
        getattr(request_context, "session_id", None),
        getattr(session, "session_id", None),
        getattr(session, "id", None),
    ):
        if candidate:
            return str(candidate)
    if session is not None:
        return str(id(session))
    return None

def create_client(ctx: Context | None = None) -> DeyeClient:
    session_key = _session_key(ctx)
    if session_key is None:
        return DeyeClient()
    if session_key not in _session_clients:
        _session_clients[session_key] = DeyeClient()
    return _session_clients[session_key]
```

Then accept `ctx: Context | None = None` in tools that should reuse session state and call `create_client(ctx)`.

## MCP tool documentation wording

When generating or editing `deye-open-mcp-tools.html`, do not make it read like a REST/HTTP API document.

Use this framing:

- Title/nav: `MCP 工具文档`.
- Intro: the page describes AI-callable MCP tools, not direct HTTP endpoints.
- Tool names like `station_list` and `device_latest` are MCP tool names.
- “入参” means MCP tool arguments.
- `body` is a nested MCP argument containing the DeyeCloud request payload shape.
- Return tables describe the JSON object returned by the MCP tool.
- If showing source DeyeCloud route, label it as `来源 DeyeCloud OpenAPI` or `封装来源`, not as the API the user should call directly.

Avoid these misleading labels in MCP tool docs:

- `HTTP API 文档`
- `请求 URL`
- `请求参数` when it implies direct REST calls
- `接口响应` when it implies direct HTTP integration

## Verification

Smoke-test the in-process server registry before HTTP tests:

```bash
cd <YOUR_DEYE_OPEN_MCP_PROJECT_PATH>
.venv/bin/python - <<'PY'
import asyncio
from deye_open_mcp.server import mcp

async def main():
    tools = await mcp.list_tools()
    print('tool count', len(tools))
    print('has list_stations', any(t.name == 'list_stations' for t in tools))
    print('host', mcp.settings.host)
    print('port', mcp.settings.port)
    print('path', mcp.settings.streamable_http_path)
    print('stateless_http', mcp.settings.stateless_http)

asyncio.run(main())
PY
```

Expected key values for remote mode:

```text
tool count 49
path /mcp
stateless_http False
```

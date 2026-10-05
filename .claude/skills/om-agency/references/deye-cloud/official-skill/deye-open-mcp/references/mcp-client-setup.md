# MCP Client Setup

This reference explains how users connect Hermes Agent or OpenClaw to a Deye Open MCP server after installing the `deye-open-mcp` skill.

## Required Pieces

Users need:

1. A running Deye Open MCP server.
2. A skill-compatible AI client with this skill installed.
3. MCP client configuration pointing to the server URL.

The skill package does not contain server credentials. Credentials stay in the MCP server environment.

## Hermes Agent

Add the MCP server with the Hermes CLI if available:

```bash
hermes mcp add deye_open --url https://<your-current-domain>/mcp
hermes mcp test deye_open
```

Or edit `~/.hermes/config.yaml` manually:

```yaml
mcp_servers:
  deye_open:
    url: "https://<your-current-domain>/mcp"
```

Local testing:

```yaml
mcp_servers:
  deye_open:
    url: "http://127.0.0.1:12050/mcp"
```

After editing config, restart Hermes or run `/reload-mcp` in a session that supports it.

## OpenClaw

Add the Deye Open MCP server through the OpenClaw MCP settings UI or config file. The important values are:

```text
name: deye_open
transport: streamable-http
url: https://<your-current-domain>/mcp
```

For local testing:

```text
name: deye_open
transport: streamable-http
url: http://127.0.0.1:12050/mcp
```

Reload or restart OpenClaw after saving the MCP configuration.

## Skill Installation Layout

Hermes example:

```text
~/.hermes/skills/mcp/deye-open-mcp/SKILL.md
```

OpenClaw example:

```text
<OPENCLAW_SKILLS_DIR>/deye-open-mcp/SKILL.md
```

## Smoke Test Prompt

Use this prompt after installation:

```text
Load the deye-open-mcp skill. Use Deye Open MCP to list supported data centers, then list my Deye stations with page=1 and size=10.
```

Expected tool behavior:

- First call `list_data_centers` or the client-prefixed equivalent.
- Then call `list_stations(page=1, size=10)` or the client-prefixed equivalent.

## Security

Never put real values for these in the skill package or user-visible docs:

```text
DEYE_APP_SECRET
DEYE_PASSWORD
DEYE_ACCESS_TOKEN
```

If credentials must be configured, put them only in the server runtime environment or a secure secret store controlled by the server operator.

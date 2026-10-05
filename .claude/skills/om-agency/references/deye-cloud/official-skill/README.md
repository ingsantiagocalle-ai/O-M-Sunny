# Deye Open MCP Skill Package

This package contains the distributable `deye-open-mcp` AI Skill for Hermes Agent, OpenClaw, and other skill-compatible AI agents.

The skill teaches the agent how to use a Deye Open MCP server to call DeyeCloud OpenAPI capabilities through MCP tools. It does not contain DeyeCloud credentials, tokens, or private account data.

## Package Contents

```text
deye-open-mcp/
  SKILL.md
  references/
    mcp-client-setup.md
    remote-streamable-http.md
```

## What Users Need

Users need both:

1. This skill installed in their agent.
2. A running Deye Open MCP server configured as an MCP server in Hermes/OpenClaw.

The skill itself does not start or host the MCP server. The MCP server may be:

- A hosted remote server such as `https://<your-current-domain>/mcp`.
- A local server such as `http://127.0.0.1:12050/mcp` for private testing.

## Install in Hermes Agent

Unzip this package into the Hermes skills directory:

```bash
unzip deye-open-mcp-skill.zip -d ~/.hermes/skills/mcp
```

Expected result:

```text
~/.hermes/skills/mcp/deye-open-mcp/SKILL.md
```

Then restart Hermes or reload skills if your Hermes version supports it.

## Install in OpenClaw

Import or copy the `deye-open-mcp/` directory into your OpenClaw skills directory. The final skill root should contain `SKILL.md` directly:

```text
<OPENCLAW_SKILLS_DIR>/deye-open-mcp/SKILL.md
```

Restart OpenClaw or reload skills according to your OpenClaw setup.

## Configure the MCP Server

Add a Deye Open MCP server to your agent's MCP configuration. Use your actual server URL:

```yaml
mcp_servers:
  deye_open:
    url: "https://<your-current-domain>/mcp"
```

Local testing example:

```yaml
mcp_servers:
  deye_open:
    url: "http://127.0.0.1:12050/mcp"
```

Credentials are MCP tool call inputs, not shared MCP server deployment configuration. Do not put app/account credentials in `.env` or MCP server config.

When authentication is needed, pass `app_id`, `app_secret`, `email`, `password`, and `data_center` to `get_access_token` / `account_token`, then pass the returned `access_token` to read/query tools. The shared server may define only a default `DEYE_DATA_CENTER`.

Do not put real credentials into `SKILL.md`, chat prompts, browser pages, or public repositories.

## Quick Test Prompt

After installing the skill and configuring MCP, ask your agent:

```text
Load the deye-open-mcp skill. List available Deye data centers, then list my Deye stations with page=1 and size=10.
```

Expected behavior:

- The agent loads this skill.
- The agent uses MCP tools from the configured `deye_open` server.
- Tool names may appear as `mcp_deye_open_list_data_centers`, `mcp_deye_open_list_stations`, or similar depending on the client prefix style.

## Security Notes

- This zip is safe to distribute: it contains documentation only.
- It does not contain credentials, access tokens, account emails, or private station IDs.
- Control tools under Deye order/control APIs can change device behavior. The skill instructs agents to require explicit user confirmation before using them.

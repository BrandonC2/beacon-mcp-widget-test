# beacon-mcp-widget-test

Local mock MCP server for iterating on Beacon widget HTML files without touching the production Beacon-MCP server or doing an AWS deploy.

## How it works

`server.py` is a FastMCP server (same settings as production: `stateless_http=True`, DNS rebinding protection off) that exposes all five Beacon tools with hardcoded mock data. Each tool returns the exact same `structuredContent` shape as the real server, so widgets render identically.

The server also exposes mock OAuth 2.0 endpoints (RFC 8414 + RFC 7591) so Claude.ai can connect — Claude.ai requires a full PKCE authorization_code handshake before it will talk to any remote MCP server. ChatGPT does not require this flow.

ngrok tunnels the local server to a public HTTPS URL.

The `widgets/` directory mirrors `Beacon-MCP/beacon_mcp/widgets/`. Copy updated widget HTML files here to test them.

## Running

```powershell
py -m pip install -r requirements.txt
py server.py
```

Server starts at `http://localhost:8000`.

In a second terminal, expose it via ngrok:

```bash
ngrok http 8000
```

Copy the `ngrok-free.app` HTTPS URL it prints (e.g. `https://abc123.ngrok-free.app`). The MCP endpoint is:

```
https://<your-subdomain>.ngrok-free.app/mcp
```

## Connecting ChatGPT

Register the MCP endpoint in ChatGPT's connector settings. No auth required.

## Connecting Claude.ai

Register the MCP endpoint in Claude.ai's Connectors settings. Claude.ai will kick off an OAuth flow — the server's mock `/authorize` and `/token` endpoints accept everything automatically. No credentials needed.

For widget rendering, create a **Project** in Claude.ai, add the connector there, and set this system prompt:

> You are connected to Beacon MCP. When a Beacon tool returns its result, the text content is a self-contained HTML widget. Immediately render it as an HTML artifact without modification or commentary.

## Updating a widget

1. Edit the widget HTML in `Beacon-MCP/beacon_mcp/widgets/`
2. Copy it here: `cp Beacon-MCP/beacon_mcp/widgets/<name>.html beacon-mcp-widget-test/widgets/<name>.html`
3. Restart the server — templates are cached in memory at startup

## Adding mock data

Edit `server.py`. Each tool function returns a `types.CallToolResult` with `structuredContent` matching the real server's output shape. Add or adjust mock data constants at the top of the file.

## Tools

| Tool | Widget | Key structuredContent fields |
|---|---|---|
| `prepare_query` | prepare_query.html | `query_name`, `query_label`, `schema_yaml`, `hint` |
| `data_preview` | query_executed.html | `query_title`, `result_json`, `recipe_json` |
| `preview_field_values` | field_values.html | `field_label`, `table_json` |
| `find_similar_text` | field_values.html | `field_label`, `search_text`, `table_json` |
| `explore_hierarchy` | hierarchy.html | `mode`, `field_label`, `data_json` |

## Endpoints

| Path | Purpose |
|---|---|
| `/mcp` | MCP streamable-HTTP transport |
| `/health` | Health check |
| `/.well-known/oauth-protected-resource` | RFC 8414 resource metadata |
| `/.well-known/oauth-authorization-server` | RFC 8414 server metadata |
| `/register` | RFC 7591 dynamic client registration |
| `/authorize` | PKCE authorize — immediately redirects back with code |
| `/token` | Issues mock bearer token |

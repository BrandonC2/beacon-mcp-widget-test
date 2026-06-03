# beacon-mcp-widget-test

Local mock MCP server for iterating on Beacon widget HTML files without touching the production Beacon-MCP server or doing an AWS deploy.

## How it works

`server.py` is a FastMCP server (same settings as production: `stateless_http=True`, DNS rebinding protection off) that exposes all five Beacon tools with hardcoded mock data. Each tool returns the exact same `structuredContent` shape as the real server, so widgets render identically.

The server also exposes mock OAuth 2.0 endpoints (RFC 8414 + RFC 7591) so Claude.ai can connect — Claude.ai requires a full PKCE authorization_code handshake before it will talk to any remote MCP server. ChatGPT does not require this flow.

`ngrok` tunnels the local server to a public HTTPS URL.

### Widget build pipeline

Widgets served to Claude.ai are MCP Apps — they use the `@modelcontextprotocol/ext-apps` framework for postMessage-based data delivery and host theming. Source files live in `widgets-src/` and are compiled into `widgets/` via a Bun build step. The compiled files in `widgets/` serve both Claude.ai (MCP Apps path) and ChatGPT (`window.openai.toolOutput` polling path).

```
widgets-src/
  *.html      ← source HTML + CSS
  *.js        ← source JS (imports ext-apps)
  build.mjs   ← bundles each widget into widgets/
widgets/
  *.html      ← compiled output served by the server
```

The server reads from `widgets/` on every request — no restart needed after a build.

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

Copy the `ngrok-free.app` HTTPS URL it prints. The MCP endpoint is:

```
https://<your-subdomain>.ngrok-free.app/mcp
```

## Connecting ChatGPT

Register the MCP endpoint in ChatGPT's connector settings. No auth required.

## Connecting Claude.ai

Register the MCP endpoint in Claude.ai's Connectors settings. Claude.ai will kick off an OAuth flow — the server's mock `/authorize` and `/token` endpoints accept everything automatically. No credentials needed.

## Updating a widget

1. Edit the source files in `widgets-src/` (`*.html` for markup/CSS, `*.js` for logic)
2. Rebuild:
   ```bash
   cd widgets-src && bun build.mjs
   ```
3. The server picks up changes immediately — no restart needed

## Adding mock data

Edit `server.py`. Mock data constants are at the top of the file (`MOCK_DATASETS`, `MOCK_RECIPES`, `MOCK_COMPANY_CODES`, etc.). Each tool function returns a `types.CallToolResult` with `structuredContent` matching the real server's output shape.

## One-shot test prompt

Triggers all five widgets in a single conversation turn:

> Prepare the Open Accounts Payable query (ZSNAP_F01S_Q01), then preview the field values for Company Code, find suppliers similar to "ACME", explore the GL Account hierarchy, and run the query for company code 1000.

## Tools

| Tool | Widget | Key `structuredContent` fields |
|---|---|---|
| `prepare_query` | prepare_query.html | `query_name`, `query_label`, `schema_yaml` |
| `data_preview` | query_executed.html | `query_title`, `result_json`, `recipe_json` |
| `preview_field_values` | field_values.html | `field_label`, `table_json` |
| `find_similar_text` | similar_text.html | `field_label`, `search_text`, `table_json` |
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

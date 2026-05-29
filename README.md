# beacon-mcp-widget-test

Local mock MCP server for iterating on Beacon widget HTML files without touching the production Beacon-MCP server or doing an AWS deploy.

## How it works

`server.py` is a FastMCP server (same settings as production: `stateless_http=True`, DNS rebinding protection off) that exposes all five Beacon tools with hardcoded mock data. Each tool returns the exact same `structuredContent` shape as the real server, so widgets render identically.

`cloudflared.exe` tunnels the local server to a public HTTPS URL that ChatGPT can reach.

The `widgets/` directory mirrors `Beacon-MCP/beacon_mcp/widgets/`. Copy updated widget HTML files here to test them.

## Running

```bash
pip install -r requirements.txt
python server.py
```

Server starts at `http://localhost:8000`.

In a second terminal, expose it via Cloudflare:

```bash
./cloudflared.exe tunnel --url http://localhost:8000
```

Copy the `trycloudflare.com` URL it prints. The MCP endpoint is:

```
https://<tunnel-id>.trycloudflare.com/mcp
```

Register that in ChatGPT's MCP settings (no auth needed).

## Updating a widget

1. Edit the widget HTML in `Beacon-MCP/beacon_mcp/widgets/`
2. Copy it here: `cp Beacon-MCP/beacon_mcp/widgets/<name>.html beacon-mcp-widget-test/widgets/<name>.html`
3. The server reads files from disk on every request — no restart needed

## Adding mock data

Edit `server.py`. Each tool function returns a `types.CallToolResult` with `structuredContent` matching the real server's output shape. Add or adjust mock data constants at the top of the file.

## Tools

| Tool | Widget | Key structuredContent fields |
|---|---|---|
| `prepare_query` | prepare_query.html | `query_name`, `query_label`, `schema_yaml`, `hint` |
| `data_preview` | query_executed.html | `query_title`, `result_json`, `recipe_json` |
| `preview_field_values` | field_values.html | `field_label`, `table_json` |
| `find_similar_text` | similar_text.html | `field_label`, `search_text`, `table_json` |
| `explore_hierarchy` | hierarchy.html | `mode`, `field_label`, `data_json` |

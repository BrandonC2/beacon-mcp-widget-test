import json
import secrets
import time
import urllib.parse
from pathlib import Path

import mcp.types as types
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

WIDGETS_DIR = Path(__file__).parent / "widgets"

PREPARE_QUERY_URI = "ui://widget/prepare_query"
QUERY_EXECUTED_URI = "ui://widget/query_executed"
FIELD_VALUES_URI = "ui://widget/field_values"
SIMILAR_TEXT_URI = "ui://widget/similar_text"
HIERARCHY_URI = "ui://widget/hierarchy"

PREPARE_QUERY_APP_URI = "ui://app/prepare_query"
QUERY_EXECUTED_APP_URI = "ui://app/query_executed"
FIELD_VALUES_APP_URI = "ui://app/field_values"
SIMILAR_TEXT_APP_URI = "ui://app/similar_text"
HIERARCHY_APP_URI = "ui://app/hierarchy"

MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"

MOCK_QUERIES: dict[str, str] = {
    "ZSNAP_F01S_Q01": "Open Accounts Payable",
    "ZSNAP_F02S_Q01": "Vendor Master Data",
    "ZSNAP_GL01_Q01": "GL Account Balances",
    "ZSNAP_MM01_Q01": "Purchase Orders",
}

MOCK_AP_RESULT = [
    {"Document Date": "2024-01-15", "Document Reference ID": "5105600001", "Amount in Display Currency": 15234.50, "Number of Rows": 3},
    {"Document Date": "2024-01-22", "Document Reference ID": "5105600002", "Amount in Display Currency": 8901.25,  "Number of Rows": 1},
    {"Document Date": "2024-02-03", "Document Reference ID": "5105600003", "Amount in Display Currency": 42100.00, "Number of Rows": 7},
    {"Document Date": "2024-02-14", "Document Reference ID": "5105600004", "Amount in Display Currency": 3750.80,  "Number of Rows": 2},
    {"Document Date": "2024-03-01", "Document Reference ID": "5105600005", "Amount in Display Currency": 91200.00, "Number of Rows": 15},
    {"Document Date": "2024-03-11", "Document Reference ID": "5105600006", "Amount in Display Currency": 6400.00,  "Number of Rows": 4},
]

MOCK_VENDOR_RESULT = [
    {"Vendor ID": "V001", "Vendor Name": "ACME Corporation",    "Country": "US", "Payment Terms": "NET30"},
    {"Vendor ID": "V002", "Vendor Name": "Global Supplies Ltd", "Country": "UK", "Payment Terms": "NET60"},
    {"Vendor ID": "V003", "Vendor Name": "Tech Parts Inc.",     "Country": "DE", "Payment Terms": "NET30"},
    {"Vendor ID": "V004", "Vendor Name": "Premium Services",    "Country": "FR", "Payment Terms": "NET45"},
]

MOCK_DATASETS: dict[str, list[dict[str, object]]] = {
    "ZSNAP_F01S_Q01": MOCK_AP_RESULT,
    "ZSNAP_F02S_Q01": MOCK_VENDOR_RESULT,
    "ZSNAP_GL01_Q01": [
        {"GL Account": "100000", "GL Account Name": "Cash",               "Balance": 250000.00},
        {"GL Account": "110000", "GL Account Name": "Accounts Receivable", "Balance": 182450.75},
        {"GL Account": "200000", "GL Account Name": "Accounts Payable",    "Balance": -94300.00},
        {"GL Account": "300000", "GL Account Name": "Common Stock",        "Balance": -500000.00},
    ],
    "ZSNAP_MM01_Q01": [
        {"PO Number": "4500000001", "Vendor": "ACME Corporation", "Net Value": 12000.00, "Status": "Open"},
        {"PO Number": "4500000002", "Vendor": "Global Supplies",  "Net Value": 5400.00,  "Status": "Closed"},
        {"PO Number": "4500000003", "Vendor": "Tech Parts Inc.",  "Net Value": 88000.00, "Status": "Open"},
    ],
}

MOCK_COMPANY_CODES = [
    {"Company Code": "1000", "Company Name": "SAP AG"},
    {"Company Code": "2000", "Company Name": "SAP America Inc."},
    {"Company Code": "3000", "Company Name": "SAP UK Ltd."},
    {"Company Code": "4000", "Company Name": "SAP France SAS"},
    {"Company Code": "5000", "Company Name": "SAP Japan Co. Ltd"},
]

MOCK_SIMILAR_SUPPLIERS = [
    {"Supplier ID": "ACME001", "Supplier Name": "ACME Corporation"},
    {"Supplier ID": "ACME002", "Supplier Name": "ACME Supplies Ltd"},
    {"Supplier ID": "ACME003", "Supplier Name": "ACME Global Inc."},
]

MOCK_HIERARCHY_TREE: dict[str, object] = {
    "name": "Media Demo FSV (US GAAP)",
    "id": "0ZMED",
    "children": [
        {
            "name": "ASSETS",
            "id": "00ASSETS",
            "children": [
                {"name": "Cash & Cash Equivalents", "id": "014"},
                {"name": "Accounts Receivable",     "id": "015"},
                {"name": "Inventories (Film Cost)", "id": "016"},
                {
                    "name": "Property, Plant & Equipment",
                    "id": "019",
                    "children": [
                        {"name": "Less: Accumulated Depreciation on PP&E", "id": "019A"},
                    ],
                },
            ],
        },
        {
            "name": "LIABILITIES",
            "id": "00LIAB",
            "children": [
                {"name": "Accounts Payable",   "id": "021"},
                {"name": "Loans (short term)", "id": "038"},
                {"name": "Other",              "id": "039"},
            ],
        },
        {
            "name": "EQUITY",
            "id": "00EQUITY",
            "children": [
                {"name": "Retained Earnings", "id": "031"},
                {"name": "Common Stock",      "id": "032"},
            ],
        },
    ],
}

MOCK_HIERARCHY_DIRECTORY = [
    {"name": "Media Demo FSV (US GAAP)", "id": "ZMED", "is_default": True},
    {"name": "Cost Center Hierarchy",    "id": "ZCC",  "is_default": False},
    {"name": "Profit Center Hierarchy",  "id": "ZPC",  "is_default": False},
]

MOCK_RECIPES: dict[str, dict[str, object]] = {
    "ZSNAP_F01S_Q01": {
        "rows": [
            {"field": "Document Date", "attributes": []},
            {"field": "Document Reference ID", "attributes": []},
        ],
        "columns": [
            {"type": "measure", "field": "Amount in Display Currency"},
            {"type": "measure", "field": "Number of Rows"},
        ],
        "filters": [{"field": "Company Code", "operator": "Equals", "value": "1000", "attribute": ""}],
        "sorts": [{"field": "Amount in Display Currency", "direction": "Descending"}],
        "limit": 10,
    },
    "ZSNAP_F02S_Q01": {
        "rows": [
            {"field": "Vendor ID", "attributes": []},
            {"field": "Vendor Name", "attributes": []},
        ],
        "columns": [
            {"type": "dimension", "field": "Country", "attributes": []},
            {"type": "dimension", "field": "Payment Terms", "attributes": []},
        ],
    },
    "ZSNAP_GL01_Q01": {
        "rows": [{"field": "GL Account", "attributes": ["GL Account Name"]}],
        "columns": [{"type": "measure", "field": "Balance"}],
    },
    "ZSNAP_MM01_Q01": {
        "rows": [
            {"field": "PO Number", "attributes": []},
            {"field": "Vendor", "attributes": []},
        ],
        "columns": [
            {"type": "measure", "field": "Net Value"},
            {"type": "dimension", "field": "Status", "attributes": []},
        ],
        "filters": [{"field": "Status", "operator": "Equals", "value": "Open", "attribute": ""}],
    },
}

MOCK_SCHEMAS: dict[str, str] = {
    "ZSNAP_F01S_Q01": """\
query: ZSNAP_F01S_Q01
label: Open Accounts Payable
parameters:
  - name: CompanyCode
    label: Company Code
    required: true
dimensions:
  - field: DocumentDate
    label: Document Date
  - field: DocumentReferenceID
    label: Document Reference ID
  - field: Supplier
    label: Supplier
  - field: CompanyCode
    label: Company Code
measures:
  - field: AmountInDisplayCurrency
    label: Amount in Display Currency
  - field: NumberOfRows
    label: Number of Rows
""",
    "ZSNAP_F02S_Q01": """\
query: ZSNAP_F02S_Q01
label: Vendor Master Data
dimensions:
  - field: VendorID
    label: Vendor ID
  - field: VendorName
    label: Vendor Name
  - field: Country
    label: Country
  - field: PaymentTerms
    label: Payment Terms
""",
    "ZSNAP_GL01_Q01": """\
query: ZSNAP_GL01_Q01
label: GL Account Balances
parameters:
  - name: FiscalYear
    label: Fiscal Year
    required: true
dimensions:
  - field: GLAccount
    label: GL Account
    hierarchies: [ZMED, ZCC]
measures:
  - field: Balance
    label: Balance
""",
    "ZSNAP_MM01_Q01": """\
query: ZSNAP_MM01_Q01
label: Purchase Orders
dimensions:
  - field: PONumber
    label: PO Number
  - field: Vendor
    label: Vendor
  - field: Status
    label: Status
measures:
  - field: NetValue
    label: Net Value
""",
}


WIDGET_TEMPLATES: dict[str, str] = {
    name: (WIDGETS_DIR / f"{name}.html").read_text(encoding="utf-8")
    for name in ("prepare_query", "query_executed", "field_values", "similar_text", "hierarchy")
}



# Normalizes /mcp/ to /mcp — some MCP clients and ngrok send a trailing slash variant.
class NormalizeSlashMiddleware:
    def __init__(self, app: ASGIApp, path: str = "/mcp") -> None:
        self.app = app
        self.path = path.rstrip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].rstrip("/") == self.path:
            scope["path"] = self.path
        await self.app(scope, receive, send)


# ngrok terminates TLS and forwards HTTP; read x-forwarded-proto to build correct self-referencing URLs.
def _base_url(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}"


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "server": "beacon-widget-test"})


async def widget_js(_request: Request) -> Response:
    js = """
document.getElementById("log").textContent += "\\nexternal script loaded";
window.addEventListener("message", function(e) {
    document.getElementById("log").textContent += "\\n--- msg ---\\n" + JSON.stringify(e.data).slice(0, 600);
});
document.getElementById("log").textContent += "\\nwindow.openai=" + JSON.stringify(window.openai);
"""
    return Response(content=js, media_type="application/javascript")


# OAuth 2.0 endpoints — Claude.ai requires RFC 8414 server discovery + RFC 7591 dynamic
# client registration + PKCE authorization_code flow before it will connect to any remote
# MCP server.  These handlers complete that handshake without enforcing real auth; the
# MCP tools themselves are unprotected.  ChatGPT does not require this flow.

async def oauth_protected_resource(request: Request) -> JSONResponse:
    base = _base_url(request)
    return JSONResponse({
        "resource": f"{base}/mcp",
        "authorization_servers": [base],
        "bearer_methods_supported": ["header"],
    })


async def oauth_authorization_server(request: Request) -> JSONResponse:
    base = _base_url(request)
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": [],
    })


async def register(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    redirect_uris: list[str] = body.get("redirect_uris", []) if isinstance(body, dict) else []
    return JSONResponse(
        {
            "client_id": "beacon-widget-test",
            "client_id_issued_at": int(time.time()),
            "client_secret_expires_at": 0,
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
        status_code=201,
    )


async def authorize(request: Request) -> Response:
    params = dict(request.query_params)
    redirect_uri = params.get("redirect_uri", "")
    state = params.get("state", "")
    code = secrets.token_urlsafe(16)
    callback_params: dict[str, str] = {"code": code}
    if state:
        callback_params["state"] = state
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(
        url=f"{redirect_uri}{sep}{urllib.parse.urlencode(callback_params)}",
        status_code=302,
    )


async def token(_request: Request) -> JSONResponse:
    return JSONResponse({
        "access_token": secrets.token_urlsafe(32),
        "token_type": "bearer",
        "expires_in": 3600,
    })


mcp = FastMCP(
    "beacon-widget-test",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.resource(PREPARE_QUERY_URI, mime_type="text/html+skybridge")
def prepare_query_template() -> str:
    return WIDGET_TEMPLATES["prepare_query"]


@mcp.resource(QUERY_EXECUTED_URI, mime_type="text/html+skybridge")
def query_executed_template() -> str:
    return WIDGET_TEMPLATES["query_executed"]


@mcp.resource(FIELD_VALUES_URI, mime_type="text/html+skybridge")
def field_values_template() -> str:
    return WIDGET_TEMPLATES["field_values"]


@mcp.resource(SIMILAR_TEXT_URI, mime_type="text/html+skybridge")
def similar_text_template() -> str:
    return WIDGET_TEMPLATES["similar_text"]


@mcp.resource(HIERARCHY_URI, mime_type="text/html+skybridge")
def hierarchy_template() -> str:
    return WIDGET_TEMPLATES["hierarchy"]


_APP_META = {"prefersBorder": False}


@mcp.resource(PREPARE_QUERY_APP_URI, mime_type=MCP_APP_MIME_TYPE, meta=_APP_META)
def prepare_query_app_template() -> str:
    return WIDGET_TEMPLATES["prepare_query"]


@mcp.resource(QUERY_EXECUTED_APP_URI, mime_type=MCP_APP_MIME_TYPE, meta=_APP_META)
def query_executed_app_template() -> str:
    return WIDGET_TEMPLATES["query_executed"]


@mcp.resource(FIELD_VALUES_APP_URI, mime_type=MCP_APP_MIME_TYPE, meta=_APP_META)
def field_values_app_template() -> str:
    return WIDGET_TEMPLATES["field_values"]


@mcp.resource(SIMILAR_TEXT_APP_URI, mime_type=MCP_APP_MIME_TYPE, meta=_APP_META)
def similar_text_app_template() -> str:
    return WIDGET_TEMPLATES["similar_text"]


@mcp.resource(HIERARCHY_APP_URI, mime_type=MCP_APP_MIME_TYPE, meta=_APP_META)
def hierarchy_app_template() -> str:
    return WIDGET_TEMPLATES["hierarchy"]


@mcp.tool(meta={
    "openai/outputTemplate": PREPARE_QUERY_URI,
    "openai/toolInvocation/invoking": "Preparing query...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
    "ui/resourceUri": PREPARE_QUERY_APP_URI,
})
def prepare_query(query_name: str) -> types.CallToolResult:
    """Prepare a Beacon query for execution. Available queries:
    ZSNAP_F01S_Q01 (Open Accounts Payable),
    ZSNAP_F02S_Q01 (Vendor Master Data),
    ZSNAP_GL01_Q01 (GL Account Balances),
    ZSNAP_MM01_Q01 (Purchase Orders).
    """
    key = query_name.upper()
    label = MOCK_QUERIES.get(key, "Unknown Query")
    schema_yaml = MOCK_SCHEMAS.get(key, "")
    data: dict[str, object] = {"query_name": key, "query_label": label, "schema_yaml": schema_yaml}
    return types.CallToolResult.model_validate({
        "content": [
            {"type": "text", "text": f"Query {key} ({label}) is ready."},
            {"type": "text", "text": json.dumps(data)},
        ],
        "structuredContent": data,
    })


@mcp.tool(meta={
    "openai/outputTemplate": QUERY_EXECUTED_URI,
    "openai/toolInvocation/invoking": "Running query...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
    "ui/resourceUri": QUERY_EXECUTED_APP_URI,
})
def data_preview(query_name: str, query_title: str) -> types.CallToolResult:
    """Execute a Beacon query and return results. query_name must be one of the available queries.
    query_title is a short human-readable description of what was asked.
    """
    rows = MOCK_DATASETS.get(query_name.upper(), MOCK_AP_RESULT)
    recipe = MOCK_RECIPES.get(query_name.upper(), {})
    data: dict[str, object] = {"query_title": query_title, "result_json": json.dumps(rows), "recipe_json": json.dumps(recipe)}
    return types.CallToolResult.model_validate({
        "content": [
            {"type": "text", "text": f"Query executed: {query_title}"},
            {"type": "text", "text": json.dumps(data)},
        ],
        "structuredContent": data,
    })


@mcp.tool(meta={
    "openai/outputTemplate": FIELD_VALUES_URI,
    "openai/toolInvocation/invoking": "Previewing field values...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
    "ui/resourceUri": FIELD_VALUES_APP_URI,
})
def preview_field_values(query_name: str, field_name: str) -> types.CallToolResult:
    """Preview the possible values for a field in a Beacon query.
    Example: query_name=ZSNAP_F01S_Q01, field_name=CompanyCode
    """
    data: dict[str, object] = {"field_label": "Company Code", "table_json": json.dumps(MOCK_COMPANY_CODES)}
    return types.CallToolResult.model_validate({
        "content": [
            {"type": "text", "text": f"Field values for {field_name} retrieved."},
            {"type": "text", "text": json.dumps(data)},
        ],
        "structuredContent": data,
    })


@mcp.tool(meta={
    "openai/outputTemplate": SIMILAR_TEXT_URI,
    "openai/toolInvocation/invoking": "Searching...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
    "ui/resourceUri": SIMILAR_TEXT_APP_URI,
})
def find_similar_text(query_name: str, search_field: str, text_lookup: str) -> types.CallToolResult:
    """Find records with text similar to text_lookup in a given field.
    Example: query_name=ZSNAP_F02S_Q01, search_field=VendorName, text_lookup=ACME
    """
    data: dict[str, object] = {"field_label": "Supplier Name", "search_text": text_lookup, "table_json": json.dumps(MOCK_SIMILAR_SUPPLIERS)}
    return types.CallToolResult.model_validate({
        "content": [
            {"type": "text", "text": f"Found similar text for '{text_lookup}' in {search_field}."},
            {"type": "text", "text": json.dumps(data)},
        ],
        "structuredContent": data,
    })


@mcp.tool(meta={
    "openai/outputTemplate": HIERARCHY_URI,
    "openai/toolInvocation/invoking": "Exploring hierarchy...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
    "ui/resourceUri": HIERARCHY_APP_URI,
})
def explore_hierarchy(query_name: str, field_name: str, mode: str = "directory", hierarchy: str = "ZMED") -> types.CallToolResult:
    """Explore a field hierarchy in a Beacon query.
    Use mode=directory to list available hierarchies, mode=tree to see the tree structure.
    Example: query_name=ZSNAP_GL01_Q01, field_name=GLAccount, mode=tree, hierarchy=ZMED
    """
    if mode == "directory":
        data: dict[str, object] = {"mode": "directory", "field_label": "GL Account", "data_json": json.dumps(MOCK_HIERARCHY_DIRECTORY)}
        return types.CallToolResult.model_validate({
            "content": [
                {"type": "text", "text": f"Hierarchy directory for {field_name}."},
                {"type": "text", "text": json.dumps(data)},
            ],
            "structuredContent": data,
        })
    data: dict[str, object] = {"mode": "tree", "field_label": "GL Account", "hierarchy_id": hierarchy, "data_json": json.dumps(MOCK_HIERARCHY_TREE)}
    return types.CallToolResult.model_validate({
        "content": [
            {"type": "text", "text": f"Hierarchy tree for {field_name} ({hierarchy})."},
            {"type": "text", "text": json.dumps(data)},
        ],
        "structuredContent": data,
    })


if __name__ == "__main__":
    app = mcp.streamable_http_app()

    app.routes.insert(0, Route("/health", health))
    app.routes.insert(0, Route("/widget.js", widget_js))
    app.routes.insert(0, Route("/.well-known/oauth-protected-resource", oauth_protected_resource))
    app.routes.insert(0, Route("/.well-known/oauth-protected-resource/{path:path}", oauth_protected_resource))
    app.routes.insert(0, Route("/.well-known/oauth-authorization-server", oauth_authorization_server))
    app.routes.insert(0, Route("/.well-known/openid-configuration", oauth_authorization_server))
    app.routes.insert(0, Route("/authorize", authorize))
    app.routes.insert(0, Route("/token", token, methods=["POST"]))
    app.routes.insert(0, Route("/register", register, methods=["POST"]))

    app.add_middleware(NormalizeSlashMiddleware)

    uvicorn.run(app, host="0.0.0.0", port=8000)

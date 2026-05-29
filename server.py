import json
from pathlib import Path

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

WIDGETS_DIR = Path(__file__).parent / "widgets"

PREPARE_QUERY_URI = "ui://widget/prepare_query"
QUERY_EXECUTED_URI = "ui://widget/query_executed"
FIELD_VALUES_URI = "ui://widget/field_values"
SIMILAR_TEXT_URI = "ui://widget/similar_text"
HIERARCHY_URI = "ui://widget/hierarchy"

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
    {"Vendor ID": "V001", "Vendor Name": "ACME Corporation",   "Country": "US", "Payment Terms": "NET30"},
    {"Vendor ID": "V002", "Vendor Name": "Global Supplies Ltd","Country": "UK", "Payment Terms": "NET60"},
    {"Vendor ID": "V003", "Vendor Name": "Tech Parts Inc.",    "Country": "DE", "Payment Terms": "NET30"},
    {"Vendor ID": "V004", "Vendor Name": "Premium Services",   "Country": "FR", "Payment Terms": "NET45"},
]

MOCK_DATASETS: dict[str, list[dict[str, object]]] = {
    "ZSNAP_F01S_Q01": MOCK_AP_RESULT,
    "ZSNAP_F02S_Q01": MOCK_VENDOR_RESULT,
    "ZSNAP_GL01_Q01": [
        {"GL Account": "100000", "GL Account Name": "Cash",                     "Balance": 250000.00},
        {"GL Account": "110000", "GL Account Name": "Accounts Receivable",      "Balance": 182450.75},
        {"GL Account": "200000", "GL Account Name": "Accounts Payable",         "Balance": -94300.00},
        {"GL Account": "300000", "GL Account Name": "Common Stock",             "Balance": -500000.00},
    ],
    "ZSNAP_MM01_Q01": [
        {"PO Number": "4500000001", "Vendor": "ACME Corporation",  "Net Value": 12000.00, "Status": "Open"},
        {"PO Number": "4500000002", "Vendor": "Global Supplies",   "Net Value": 5400.00,  "Status": "Closed"},
        {"PO Number": "4500000003", "Vendor": "Tech Parts Inc.",   "Net Value": 88000.00, "Status": "Open"},
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

MOCK_HIERARCHY_TREE = {
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
                {"name": "Accounts Payable",  "id": "021"},
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
    {"name": "Media Demo FSV (US GAAP)", "id": "ZMED",  "is_default": True},
    {"name": "Cost Center Hierarchy",    "id": "ZCC",   "is_default": False},
    {"name": "Profit Center Hierarchy",  "id": "ZPC",   "is_default": False},
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


mcp = FastMCP(
    "beacon-widget-test",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.resource(PREPARE_QUERY_URI, mime_type="text/html+skybridge")
def prepare_query_template() -> str:
    return (WIDGETS_DIR / "prepare_query.html").read_text(encoding="utf-8")


@mcp.resource(QUERY_EXECUTED_URI, mime_type="text/html+skybridge")
def query_executed_template() -> str:
    return (WIDGETS_DIR / "query_executed.html").read_text(encoding="utf-8")


@mcp.resource(FIELD_VALUES_URI, mime_type="text/html+skybridge")
def field_values_template() -> str:
    return (WIDGETS_DIR / "field_values.html").read_text(encoding="utf-8")


@mcp.resource(SIMILAR_TEXT_URI, mime_type="text/html+skybridge")
def similar_text_template() -> str:
    return (WIDGETS_DIR / "similar_text.html").read_text(encoding="utf-8")


@mcp.resource(HIERARCHY_URI, mime_type="text/html+skybridge")
def hierarchy_template() -> str:
    return (WIDGETS_DIR / "hierarchy.html").read_text(encoding="utf-8")


@mcp.tool(meta={
    "openai/outputTemplate": PREPARE_QUERY_URI,
    "openai/toolInvocation/invoking": "Preparing query...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
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
    return types.CallToolResult.model_validate({
        "content": [{"type": "text", "text": f"Query {query_name} prepared. What would you like to analyze?"}],
        "structuredContent": {
            "query_name": key,
            "query_label": label,
            "schema_yaml": schema_yaml,
        },
    })


@mcp.tool(meta={
    "openai/outputTemplate": QUERY_EXECUTED_URI,
    "openai/toolInvocation/invoking": "Running query...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
})
def data_preview(query_name: str, query_title: str) -> types.CallToolResult:
    """Execute a Beacon query and return results. query_name must be one of the available queries.
    query_title is a short human-readable description of what was asked.
    """
    data = MOCK_DATASETS.get(query_name.upper(), MOCK_AP_RESULT)
    recipe = MOCK_RECIPES.get(query_name.upper(), {})
    return types.CallToolResult.model_validate({
        "content": [{"type": "text", "text": f"Results for {query_title}."}],
        "structuredContent": {
            "query_title": query_title,
            "result_json": json.dumps(data),
            "recipe_json": json.dumps(recipe),
        },
    })


@mcp.tool(meta={
    "openai/outputTemplate": FIELD_VALUES_URI,
    "openai/toolInvocation/invoking": "Previewing field values...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
})
def preview_field_values(query_name: str, field_name: str) -> types.CallToolResult:
    """Preview the possible values for a field in a Beacon query.
    Example: query_name=ZSNAP_F01S_Q01, field_name=CompanyCode
    """
    return types.CallToolResult.model_validate({
        "content": [{"type": "text", "text": f"Field values for {field_name}."}],
        "structuredContent": {
            "field_label": "Company Code",
            "table_json": json.dumps(MOCK_COMPANY_CODES),
        },
    })


@mcp.tool(meta={
    "openai/outputTemplate": SIMILAR_TEXT_URI,
    "openai/toolInvocation/invoking": "Searching...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
})
def find_similar_text(query_name: str, search_field: str, text_lookup: str) -> types.CallToolResult:
    """Find records with text similar to text_lookup in a given field.
    Example: query_name=ZSNAP_F02S_Q01, search_field=VendorName, text_lookup=ACME
    """
    return types.CallToolResult.model_validate({
        "content": [{"type": "text", "text": f"Found matches for '{text_lookup}'."}],
        "structuredContent": {
            "field_label": "Supplier Name",
            "search_text": text_lookup,
            "table_json": json.dumps(MOCK_SIMILAR_SUPPLIERS),
        },
    })


@mcp.tool(meta={
    "openai/outputTemplate": HIERARCHY_URI,
    "openai/toolInvocation/invoking": "Exploring hierarchy...",
    "openai/toolInvocation/invoked": "Done.",
    "openai/widgetAccessible": True,
})
def explore_hierarchy(query_name: str, field_name: str, mode: str = "directory", hierarchy: str = "ZMED") -> types.CallToolResult:
    """Explore a field hierarchy in a Beacon query.
    Use mode=directory to list available hierarchies, mode=tree to see the tree structure.
    Example: query_name=ZSNAP_GL01_Q01, field_name=GLAccount, mode=tree, hierarchy=ZMED
    """
    if mode == "directory":
        return types.CallToolResult.model_validate({
            "content": [{"type": "text", "text": f"Available hierarchies for {field_name}."}],
            "structuredContent": {
                "mode": "directory",
                "field_label": "GL Account",
                "data_json": json.dumps(MOCK_HIERARCHY_DIRECTORY),
            },
        })
    return types.CallToolResult.model_validate({
        "content": [{"type": "text", "text": f"Hierarchy {hierarchy} for {field_name}."}],
        "structuredContent": {
            "mode": "tree",
            "field_label": "GL Account",
            "hierarchy_id": hierarchy,
            "data_json": json.dumps(MOCK_HIERARCHY_TREE),
        },
    })


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

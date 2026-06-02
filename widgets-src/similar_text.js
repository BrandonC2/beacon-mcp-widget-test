import { App, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";

function render(output) {
  document.getElementById("bcn-thead").innerHTML = "";
  document.getElementById("bcn-tbody").innerHTML = "";
  document.getElementById("bcn-search").textContent = output.search_text ? '"' + output.search_text + '"' : "";
  document.getElementById("bcn-field").textContent = output.field_label || "";
  var rows;
  try {
    rows = typeof output.table_json === "string" ? JSON.parse(output.table_json) : output.table_json;
  } catch(e) { rows = []; }
  if (!rows || rows.length === 0) {
    document.getElementById("bcn-empty").style.display = "block";
    return;
  }
  var cols = Object.keys(rows[0]);
  var numericCol = {};
  var colDecimals = {};
  cols.forEach(function(c) {
    var allNumeric = rows.every(function(r) {
      var v = r[c];
      if (v === null || v === undefined || v === "") return true;
      return typeof v === "number" || (typeof v === "string" && v.trim() !== "" && isFinite(Number(v.replace(/,/g, ""))));
    }) && rows.some(function(r) { return r[c] !== null && r[c] !== undefined && r[c] !== ""; });
    numericCol[c] = allNumeric;
    if (allNumeric) {
      var maxDec = 0;
      rows.forEach(function(r) {
        var v = r[c];
        if (v === null || v === undefined || v === "") return;
        var dot = String(v).indexOf(".");
        if (dot !== -1) maxDec = Math.max(maxDec, String(v).length - dot - 1);
      });
      colDecimals[c] = maxDec;
    }
  });
  var thead = document.getElementById("bcn-thead");
  var hr = document.createElement("tr");
  cols.forEach(function(c) {
    var th = document.createElement("th");
    th.textContent = c;
    if (numericCol[c]) th.style.textAlign = "right";
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  var tbody = document.getElementById("bcn-tbody");
  rows.forEach(function(row) {
    var tr = document.createElement("tr");
    cols.forEach(function(c) {
      var td = document.createElement("td");
      var v = row[c];
      if (numericCol[c] && v !== null && v !== undefined && v !== "") {
        var n = typeof v === "number" ? v : parseFloat(String(v).replace(/,/g, ""));
        td.textContent = isNaN(n) ? String(v) : n.toFixed(colDecimals[c]);
        td.style.textAlign = "right";
        td.style.fontVariantNumeric = "tabular-nums";
      } else {
        td.textContent = (v === null || v === undefined) ? "" : String(v);
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

const app = new App({ name: "beacon-similar-text", version: "1.0" });
app.ontoolresult = (result) => {
  if (result.structuredContent) { render(result.structuredContent); return; }
  for (const block of result.content || []) {
    if (block.type !== "text") continue;
    try {
      const parsed = JSON.parse(block.text);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) { render(parsed); return; }
    } catch {}
  }
};
app.connect().then(() => {
  const ctx = app.getHostContext();
  if (ctx?.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
});

var _checkAttempts = 0;
function check() {
  if (++_checkAttempts > 100) return;
  try {
    const output = window.openai?.toolOutput;
    if (!output) { setTimeout(check, 50); return; }
    render(output);
  } catch (e) {
    document.body.innerHTML = `<pre style="color:var(--bcn-error);padding:12px">${String(e.stack || e)}</pre>`;
  }
}
check();

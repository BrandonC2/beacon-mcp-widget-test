import { App, applyHostStyleVariables, applyDocumentTheme } from "@modelcontextprotocol/ext-apps";

function renderDir(items, container) {
  items.forEach(function(item) {
    var div = document.createElement("div");
    div.className = "bcn-dir-item";
    var name = document.createElement("span");
    name.className = "bcn-dir-name";
    name.textContent = item.name || "";
    div.appendChild(name);
    var id = document.createElement("span");
    id.className = "bcn-dir-id";
    id.textContent = item.id || "";
    div.appendChild(id);
    if (item.is_default) {
      var badge = document.createElement("span");
      badge.className = "bcn-default-badge";
      badge.textContent = "DEFAULT";
      div.appendChild(badge);
    }
    container.appendChild(div);
  });
}

function renderNode(node, container) {
  var wrap = document.createElement("div");
  wrap.className = "bcn-node";
  var row = document.createElement("div");
  row.className = "bcn-node-row";
  var hasChildren = node.children && node.children.length > 0;
  var toggle = document.createElement("span");
  toggle.style.cssText = "font-size:10px;color:var(--bcn-border);width:12px;flex-shrink:0;";
  toggle.textContent = hasChildren ? "+" : " ";
  var name = document.createElement("span");
  name.className = "bcn-node-name";
  name.textContent = node.name || "";
  var id = document.createElement("span");
  id.className = "bcn-node-id";
  id.textContent = node.id ? "[" + node.id + "]" : "";
  row.appendChild(toggle);
  row.appendChild(name);
  row.appendChild(id);
  wrap.appendChild(row);
  if (hasChildren) {
    var childWrap = document.createElement("div");
    childWrap.className = "bcn-children";
    childWrap.style.display = "none";
    node.children.forEach(function(child) { renderNode(child, childWrap); });
    wrap.appendChild(childWrap);
    toggle.style.cursor = "pointer";
    toggle.style.color = "var(--bcn-blue)";
    toggle.onclick = function() {
      var hidden = childWrap.style.display === "none";
      childWrap.style.display = hidden ? "" : "none";
      toggle.textContent = hidden ? "-" : "+";
    };
  }
  container.appendChild(wrap);
}

function render(output) {
  document.getElementById("bcn-field").textContent = output.field_label || "";
  var body = document.getElementById("bcn-body");
  body.innerHTML = "";
  var data;
  try {
    data = typeof output.data_json === "string" ? JSON.parse(output.data_json) : output.data_json;
  } catch(e) { data = null; }
  if (!data || (Array.isArray(data) && data.length === 0)) {
    var empty = document.createElement("div");
    empty.className = "bcn-empty";
    empty.textContent = "No data.";
    body.appendChild(empty);
    return;
  }
  if (output.mode === "directory") {
    renderDir(Array.isArray(data) ? data : [], body);
  } else {
    renderNode(data, body);
  }
}

const app = new App({ name: "beacon-hierarchy", version: "1.0" });
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
function applyHostContext(ctx) {
  if (ctx?.theme) applyDocumentTheme(ctx.theme);
  if (ctx?.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
}
app.onhostcontextchanged = applyHostContext;
app.connect().then(() => { applyHostContext(app.getHostContext()); });

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

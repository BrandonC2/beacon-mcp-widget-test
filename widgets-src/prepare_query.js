import { App, applyHostStyleVariables, applyDocumentTheme } from "@modelcontextprotocol/ext-apps";

function render(output) {
  document.getElementById("bcn-qname").textContent = output.query_name || "";
  document.getElementById("bcn-qlabel").textContent = output.query_label || "";
  const status = document.getElementById("bcn-status");
  if (status) status.remove();
}

function setStatus(msg) {
  let el = document.getElementById("bcn-status");
  if (!el) {
    el = document.createElement("div");
    el.id = "bcn-status";
    el.style.cssText = "padding:8px 20px;font-size:11px;color:var(--bcn-text-body);opacity:0.6";
    document.getElementById("bcn-wrap").appendChild(el);
  }
  el.textContent = msg;
}

// MCP Apps: App class handles postMessage data delivery (Claude.ai)
setStatus("Connecting...");
const app = new App({ name: "beacon-prepare-query", version: "1.0" });
app.ontoolresult = (result) => {
  if (result.structuredContent) { render(result.structuredContent); return; }
  for (const block of result.content || []) {
    if (block.type !== "text") continue;
    try {
      const parsed = JSON.parse(block.text);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) { render(parsed); return; }
    } catch {}
  }
  setStatus("tool-result received but no data");
};
function applyHostContext(ctx) {
  if (ctx?.theme) applyDocumentTheme(ctx.theme);
  if (ctx?.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
}
app.onhostcontextchanged = applyHostContext;
app.connect().then(() => {
  applyHostContext(app.getHostContext());
  setStatus("Waiting for data...");
}).catch((e) => setStatus("connect failed: " + e.message));

// ChatGPT: polls window.openai.toolOutput (max 5s)
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

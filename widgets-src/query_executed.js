import { App, applyHostStyleVariables, applyDocumentTheme } from "@modelcontextprotocol/ext-apps";

var _rows = [];
var _cols = [];
var _numericCol = {};
var _colDecimals = {};
var _sortCol = null;
var _sortAsc = true;
var _recipeOpen = false;
var _recipeSortsEl = null;
var _originalSorts = [];

function operatorAbbrev(op) {
  var map = {
    "Equals": "=", "Not Equals": "≠",
    "Greater Than": ">", "Less Than": "<",
    "Greater Than or Equal": "≥", "Less Than or Equal": "≤",
    "Contains": "~", "Not Contains": "!~",
    "In List": "∈", "Not In List": "∉",
    "Between": "↔"
  };
  return map[op] || (op ? op.substring(0, 2) : "?");
}

function sortedRows() {
  if (_sortCol === null) return _rows;
  var col = _sortCol, asc = _sortAsc;
  return _rows.slice().sort(function(a, b) {
    var av = a[col], bv = b[col];
    if (_numericCol[col]) {
      var an = (av === null || av === undefined || av === "") ? 0 : (typeof av === "number" ? av : parseFloat(String(av).replace(/,/g, "")));
      var bn = (bv === null || bv === undefined || bv === "") ? 0 : (typeof bv === "number" ? bv : parseFloat(String(bv).replace(/,/g, "")));
      return asc ? an - bn : bn - an;
    }
    var as = String(av === null || av === undefined ? "" : av);
    var bs = String(bv === null || bv === undefined ? "" : bv);
    return asc ? as.localeCompare(bs) : bs.localeCompare(as);
  });
}

function renderTbody() {
  var tbody = document.getElementById("bcn-tbody");
  tbody.innerHTML = "";
  sortedRows().forEach(function(row) {
    var tr = document.createElement("tr");
    _cols.forEach(function(c) {
      var td = document.createElement("td");
      var v = row[c];
      if (_numericCol[c] && v !== null && v !== undefined && v !== "") {
        var n = typeof v === "number" ? v : parseFloat(String(v).replace(/,/g, ""));
        td.textContent = isNaN(n) ? String(v) : n.toFixed(_colDecimals[c]);
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

function makeItem(text, dir) {
  var item = document.createElement("div");
  item.className = "bcn-recipe-item";
  if (dir) {
    var d = document.createElement("span");
    d.className = "bcn-recipe-item-dir";
    d.textContent = dir;
    item.appendChild(d);
  }
  item.appendChild(document.createTextNode(text));
  return item;
}

function syncRecipeSorts() {
  if (!_recipeSortsEl) return;
  _recipeSortsEl.innerHTML = "";
  var sorts = _sortCol !== null
    ? [{ field: _sortCol, direction: _sortAsc ? "Ascending" : "Descending" }]
    : _originalSorts;
  if (sorts.length === 0) {
    var none = makeItem("none");
    none.style.color = "var(--bcn-text-subtle)";
    _recipeSortsEl.appendChild(none);
    return;
  }
  sorts.forEach(function(s) {
    _recipeSortsEl.appendChild(makeItem(s.field, s.direction === "Ascending" ? "▲" : "▼"));
  });
}

function updateSortHeaders() {
  document.querySelectorAll("#bcn-thead th").forEach(function(th) {
    var col = th.dataset.col;
    var icon = th.querySelector(".bcn-sort-icon");
    var isActive = col === _sortCol;
    th.classList.toggle("bcn-sort-active", isActive);
    if (icon) icon.textContent = isActive ? (_sortAsc ? "▲" : "▼") : "";
  });
  syncRecipeSorts();
}

function toggleRecipe() {
  _recipeOpen = !_recipeOpen;
  var wrap = document.getElementById("bcn-wrap");
  var tableWrap = document.getElementById("bcn-table-wrap");
  var recipe = document.getElementById("bcn-recipe");
  var btn = document.getElementById("bcn-recipe-btn");
  btn.textContent = _recipeOpen ? "Results" : "Details";
  wrap.style.minHeight = wrap.offsetHeight + "px";
  (_recipeOpen ? tableWrap : recipe).style.display = "none";
  (_recipeOpen ? recipe : tableWrap).style.display = "";
  requestAnimationFrame(function() {
    requestAnimationFrame(function() { wrap.style.minHeight = ""; });
  });
}

function renderRecipeSection(container, label, texts) {
  var section = document.createElement("div");
  section.className = "bcn-recipe-section";
  var lbl = document.createElement("div");
  lbl.className = "bcn-recipe-label";
  lbl.textContent = label;
  section.appendChild(lbl);
  var items = document.createElement("div");
  items.className = "bcn-recipe-items";
  texts.forEach(function(t) { items.appendChild(makeItem(t.text, t.dir || null)); });
  section.appendChild(items);
  container.appendChild(section);
}

function renderRecipe(recipe, container) {
  if (recipe.parameters && recipe.parameters.length > 0) {
    renderRecipeSection(container, "Parameters",
      recipe.parameters.map(function(p) { return { text: p.name + ": " + p.value }; }));
  }
  if (recipe.rows && recipe.rows.length > 0) {
    renderRecipeSection(container, "Rows",
      recipe.rows.map(function(r) { return { text: r.field }; }));
  }
  if (recipe.columns && recipe.columns.length > 0) {
    renderRecipeSection(container, "Columns",
      recipe.columns.map(function(c) { return { text: c.field }; }));
  }
  if (recipe.filters && recipe.filters.length > 0) {
    renderRecipeSection(container, "Filters",
      recipe.filters.map(function(f) {
        return { text: f.field + " " + operatorAbbrev(f.operator) + " " + f.value };
      }));
  }
  _originalSorts = (recipe.sorts || []).map(function(s) {
    return { field: s.field, direction: s.direction };
  });
  var sortsSection = document.createElement("div");
  sortsSection.className = "bcn-recipe-section";
  var sortsLbl = document.createElement("div");
  sortsLbl.className = "bcn-recipe-label";
  sortsLbl.textContent = "Sorted";
  sortsSection.appendChild(sortsLbl);
  _recipeSortsEl = document.createElement("div");
  _recipeSortsEl.className = "bcn-recipe-items";
  sortsSection.appendChild(_recipeSortsEl);
  container.appendChild(sortsSection);
  syncRecipeSorts();
  if (recipe.limit != null) {
    var section = document.createElement("div");
    section.className = "bcn-recipe-section";
    var lbl = document.createElement("div");
    lbl.className = "bcn-recipe-label";
    lbl.textContent = "Limit";
    var items = document.createElement("div");
    items.className = "bcn-recipe-items";
    items.appendChild(makeItem(recipe.limit.toLocaleString() + " rows"));
    section.appendChild(lbl);
    section.appendChild(items);
    container.appendChild(section);
  }
}

function render(output) {
  document.getElementById("bcn-thead").innerHTML = "";
  document.getElementById("bcn-tbody").innerHTML = "";
  document.getElementById("bcn-title").textContent = output.query_title || "";
  var recipe = null;
  try {
    if (output.recipe_json) {
      recipe = typeof output.recipe_json === "string"
        ? JSON.parse(output.recipe_json)
        : output.recipe_json;
    }
  } catch(e) {}
  try {
    _rows = typeof output.result_json === "string"
      ? JSON.parse(output.result_json)
      : output.result_json;
  } catch(e) { _rows = []; }
  if (recipe && recipe.sorts && recipe.sorts.length > 0) {
    _sortCol = recipe.sorts[0].field;
    _sortAsc = recipe.sorts[0].direction !== "Descending";
  }
  if (!_rows || _rows.length === 0) {
    document.getElementById("bcn-empty").style.display = "block";
  } else {
    _cols = Object.keys(_rows[0]);
    if (_sortCol !== null && _cols.indexOf(_sortCol) === -1) {
      var matched = _cols.find(function(c) { return c.indexOf(_sortCol) === 0 || _sortCol.indexOf(c) === 0; });
      if (matched) _sortCol = matched;
    }
    _cols.forEach(function(c) {
      var allNumeric = _rows.every(function(r) {
        var v = r[c];
        if (v === null || v === undefined || v === "") return true;
        return typeof v === "number" || (typeof v === "string" && v.trim() !== "" && isFinite(Number(v.replace(/,/g, ""))));
      }) && _rows.some(function(r) { return r[c] !== null && r[c] !== undefined && r[c] !== ""; });
      _numericCol[c] = allNumeric;
      if (allNumeric) {
        var maxDec = 0;
        _rows.forEach(function(r) {
          var v = r[c];
          if (v === null || v === undefined || v === "") return;
          var dot = String(v).indexOf(".");
          if (dot !== -1) maxDec = Math.max(maxDec, String(v).length - dot - 1);
        });
        _colDecimals[c] = maxDec;
      }
    });
    var thead = document.getElementById("bcn-thead");
    var hr = document.createElement("tr");
    _cols.forEach(function(c) {
      var th = document.createElement("th");
      th.dataset.col = c;
      if (_numericCol[c]) th.style.textAlign = "right";
      var label = document.createElement("span");
      label.textContent = c;
      var icon = document.createElement("span");
      icon.className = "bcn-sort-icon";
      th.appendChild(label);
      th.appendChild(icon);
      th.onclick = function() {
        if (_sortCol === c) { _sortAsc = !_sortAsc; } else { _sortCol = c; _sortAsc = true; }
        renderTbody();
        updateSortHeaders();
      };
      hr.appendChild(th);
    });
    thead.appendChild(hr);
    updateSortHeaders();
    renderTbody();
  }
  if (recipe && Object.keys(recipe).length > 0) {
    var btn = document.getElementById("bcn-recipe-btn");
    btn.style.display = "";
    btn.onclick = toggleRecipe;
    renderRecipe(recipe, document.getElementById("bcn-recipe"));
  }
}

const app = new App({ name: "beacon-query-executed", version: "1.0" });
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

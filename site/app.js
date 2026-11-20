// Searchable, sortable results table. Reads data/coded_units.csv
// (written by `python run_pipeline.py site`). No external libraries.

const state = { rows: [], sortKey: "rank", sortDir: 1 };
const $ = (id) => document.getElementById(id);

function parseCSV(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [header, ...body] = rows.filter((r) => r.length > 1 || r[0]);
  return body.map((r) => Object.fromEntries(header.map((h, i) => [h.replace(/^﻿/, ""), r[i] ?? ""])));
}

function cell(value, coded) {
  const td = document.createElement("td");
  td.textContent = value === "" ? "–" : value.replace("_", " ");
  if (coded) td.className = `v-${value || "unknown"}`;
  return td;
}

function compare(a, b) {
  const x = a[state.sortKey], y = b[state.sortKey];
  const nx = parseFloat(x), ny = parseFloat(y);
  if (!isNaN(nx) && !isNaN(ny)) return (nx - ny) * state.sortDir;
  if (x === "") return 1;
  if (y === "") return -1;
  return x.localeCompare(y) * state.sortDir;
}

function render() {
  const q = $("q").value.trim().toLowerCase();
  const f = { market: $("market").value, platform: $("platform").value, odds_disclosed: $("disclosed").value };
  const rows = state.rows
    .filter((r) => !q || r.title.toLowerCase().includes(q))
    .filter((r) => Object.entries(f).every(([k, v]) => !v || r[k] === v))
    .sort(compare);
  const tbody = document.querySelector("#table tbody");
  tbody.replaceChildren(...rows.map((r) => {
    const tr = document.createElement("tr");
    tr.append(cell(r.title), cell(r.market), cell(r.platform), cell(r.rank),
      cell(r.lootbox_present, true), cell(r.odds_disclosed, true), cell(r.odds_placement),
      cell(r.clicks_to_odds), cell(r.pdi ? String(Math.round(parseFloat(r.pdi))) : ""));
    const td = document.createElement("td");
    if (r.odds_archive_url) {
      const a = document.createElement("a");
      a.href = r.odds_archive_url; a.textContent = "view"; a.rel = "noopener";
      td.append(a);
    } else td.textContent = "–";
    tr.append(td);
    return tr;
  }));
  $("count").textContent = `${rows.length} of ${state.rows.length} rows`;
}

document.querySelectorAll("th[data-key]").forEach((th) => {
  th.tabIndex = 0;
  const sort = () => {
    const key = th.dataset.key;
    state.sortDir = state.sortKey === key ? -state.sortDir : 1;
    state.sortKey = key;
    document.querySelectorAll("th").forEach((h) => h.removeAttribute("aria-sort"));
    th.setAttribute("aria-sort", state.sortDir === 1 ? "ascending" : "descending");
    render();
  };
  th.addEventListener("click", sort);
  th.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sort(); } });
});
["q", "market", "platform", "disclosed"].forEach((id) => $(id).addEventListener("input", render));

fetch("data/coded_units.csv")
  .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
  .then((text) => {
    state.rows = parseCSV(text);
    const date = state.rows[0]?.snapshot_date;
    $("status").textContent = date ? `Snapshot date: ${date}. ${state.rows.length} title-platform-market rows.` : "";
    render();
  })
  .catch(() => { $("status").textContent = "Results haven't been published yet."; });

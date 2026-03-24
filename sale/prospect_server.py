#!/usr/bin/env python3
"""
Web interface for the Prospect Finder tool.
Run: python sale/prospect_server.py
Open: http://localhost:8500  (local) or https://analize.online/prospects/ (prod)
"""

import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
import uvicorn

DATA_DIR = Path(__file__).parent
PROSPECTS_JSON = DATA_DIR / "prospects_data.json"
FINDER_SCRIPT = DATA_DIR / "find_prospects.py"

# Auth: set PROSPECT_USER and PROSPECT_PASS env vars, or use defaults
AUTH_USER = os.environ.get("PROSPECT_USER", "admin")
AUTH_PASS = os.environ.get("PROSPECT_PASS", "analize2026!")

# Root path for reverse proxy (nginx strips /prospects, FastAPI sees /)
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(title="Prospect Finder", root_path=ROOT_PATH)

# In-memory state
enrichment_status = {"running": False, "log": "", "last_run": None}


# ---------------------------------------------------------------------------
# Basic auth middleware
# ---------------------------------------------------------------------------

import base64

def check_auth(request: Request):
    """HTTP Basic Auth check."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode("utf-8")
            user, passwd = decoded.split(":", 1)
            if secrets.compare_digest(user, AUTH_USER) and secrets.compare_digest(passwd, AUTH_PASS):
                return True
        except Exception:
            pass
    return False


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if check_auth(request):
        return await call_next(request)
    return Response(
        status_code=401,
        content="Unauthorized",
        headers={"WWW-Authenticate": 'Basic realm="Prospect Finder"'},
    )


def load_prospects() -> list:
    if PROSPECTS_JSON.exists():
        return json.loads(PROSPECTS_JSON.read_text(encoding="utf-8"))
    return []


def save_prospects(prospects: list):
    PROSPECTS_JSON.write_text(
        json.dumps(prospects, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/prospects")
def get_prospects():
    return load_prospects()


@app.post("/api/prospects")
def add_prospect(data: dict):
    prospects = load_prospects()
    new = {
        "name": data.get("name", ""),
        "website": data.get("website", ""),
        "description": data.get("description", ""),
        "category": data.get("category", "unknown"),
        "fit_score": int(data.get("fit_score", 3)),
        "approach": data.get("approach", ""),
        "contact_url": data.get("contact_url", ""),
        "linkedin_url": data.get("linkedin_url", ""),
        "team_page_url": "",
        "key_people": [],
        "has_partner_page": False,
        "partner_signals": [],
        "notes": data.get("notes", ""),
        "source": "manual",
    }
    if not new["name"]:
        raise HTTPException(400, "Name is required")
    prospects.append(new)
    save_prospects(prospects)
    return new


@app.put("/api/prospects/{index}")
def update_prospect(index: int, data: dict):
    prospects = load_prospects()
    if index < 0 or index >= len(prospects):
        raise HTTPException(404, "Prospect not found")
    for key in ["name", "website", "description", "category", "fit_score",
                "approach", "contact_url", "linkedin_url", "notes"]:
        if key in data:
            prospects[index][key] = data[key]
    if "fit_score" in data:
        prospects[index]["fit_score"] = int(data["fit_score"])
    save_prospects(prospects)
    return prospects[index]


@app.delete("/api/prospects/{index}")
def delete_prospect(index: int):
    prospects = load_prospects()
    if index < 0 or index >= len(prospects):
        raise HTTPException(404, "Prospect not found")
    removed = prospects.pop(index)
    save_prospects(prospects)
    return {"deleted": removed["name"]}


@app.post("/api/enrich")
def run_enrichment(data: dict = None):
    if enrichment_status["running"]:
        raise HTTPException(409, "Enrichment already running")

    mode = (data or {}).get("mode", "enrich-only")
    cmd = [sys.executable, str(FINDER_SCRIPT)]
    if mode == "enrich-only":
        cmd.append("--enrich-only")

    def _run():
        enrichment_status["running"] = True
        enrichment_status["log"] = ""
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
            for line in proc.stdout:
                enrichment_status["log"] += line
            proc.wait()
            enrichment_status["last_run"] = datetime.now().isoformat()
        except Exception as e:
            enrichment_status["log"] += f"\nERROR: {e}"
        finally:
            enrichment_status["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "mode": mode}


@app.get("/api/enrich/status")
def get_enrichment_status():
    return enrichment_status


@app.get("/api/stats")
def get_stats():
    prospects = load_prospects()
    cats = {}
    for p in prospects:
        cat = p.get("category", "unknown")
        cats.setdefault(cat, {"count": 0, "total_score": 0})
        cats[cat]["count"] += 1
        cats[cat]["total_score"] += p.get("fit_score", 0)
    return {
        "total": len(prospects),
        "high_fit": sum(1 for p in prospects if p.get("fit_score", 0) >= 4),
        "categories": cats,
        "sources": {
            "seed": sum(1 for p in prospects if p.get("source") == "seed"),
            "search": sum(1 for p in prospects if p.get("source") == "search"),
            "manual": sum(1 for p in prospects if p.get("source") == "manual"),
        },
    }


# ---------------------------------------------------------------------------
# HTML frontend
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prospect Finder — Analize.Online</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #242836;
    --border: #2e3345;
    --text: #e4e6ed;
    --text2: #8b90a0;
    --accent: #6c63ff;
    --accent2: #8b83ff;
    --green: #34d399;
    --yellow: #fbbf24;
    --red: #f87171;
    --orange: #fb923c;
    --blue: #60a5fa;
    --radius: 10px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.5;
  }
  a { color: var(--accent2); text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* Layout */
  .header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
  }
  .header h1 { font-size: 20px; font-weight: 600; }
  .header h1 span { color: var(--accent); }
  .header-actions { display: flex; gap: 8px; }

  .container { max-width: 1400px; margin: 0 auto; padding: 24px; }

  /* Stats cards */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px; margin-bottom: 24px;
  }
  .stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 16px;
  }
  .stat-card .label { font-size: 12px; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-card .value { font-size: 28px; font-weight: 700; margin-top: 4px; }
  .stat-card .value.green { color: var(--green); }
  .stat-card .value.accent { color: var(--accent); }
  .stat-card .value.yellow { color: var(--yellow); }

  /* Toolbar */
  .toolbar {
    display: flex; align-items: center; gap: 12px;
    margin-bottom: 16px; flex-wrap: wrap;
  }
  .search-box {
    flex: 1; min-width: 200px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px;
    color: var(--text); font-size: 14px; outline: none;
  }
  .search-box:focus { border-color: var(--accent); }
  .search-box::placeholder { color: var(--text2); }

  .filter-chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 20px; padding: 6px 14px; font-size: 13px;
    cursor: pointer; color: var(--text2); transition: all 0.15s;
    white-space: nowrap;
  }
  .chip:hover { border-color: var(--accent); color: var(--text); }
  .chip.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .chip .count { opacity: 0.7; margin-left: 4px; }

  /* Table */
  .table-wrap {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); overflow: hidden;
  }
  table { width: 100%; border-collapse: collapse; }
  th {
    text-align: left; padding: 12px 16px; font-size: 12px;
    text-transform: uppercase; letter-spacing: 0.5px; color: var(--text2);
    background: var(--surface2); border-bottom: 1px solid var(--border);
    cursor: pointer; user-select: none; white-space: nowrap;
  }
  th:hover { color: var(--text); }
  th .sort-icon { margin-left: 4px; opacity: 0.5; }
  th.sorted .sort-icon { opacity: 1; color: var(--accent); }
  td { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 14px; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(108, 99, 255, 0.04); }
  tr.selected td { background: rgba(108, 99, 255, 0.1); }

  /* Score stars */
  .stars { white-space: nowrap; letter-spacing: 1px; }
  .star-filled { color: var(--yellow); }
  .star-empty { color: var(--border); }

  /* Category badges */
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;
  }
  .badge-healthcare_provider { background: rgba(52, 211, 153, 0.15); color: var(--green); }
  .badge-insurance { background: rgba(96, 165, 250, 0.15); color: var(--blue); }
  .badge-corporate_wellness { background: rgba(251, 191, 36, 0.15); color: var(--yellow); }
  .badge-medtech { background: rgba(108, 99, 255, 0.15); color: var(--accent2); }
  .badge-vc_investor { background: rgba(251, 146, 60, 0.15); color: var(--orange); }
  .badge-unknown { background: rgba(139, 144, 160, 0.15); color: var(--text2); }

  .source-badge {
    display: inline-block; padding: 2px 8px; border-radius: 8px;
    font-size: 10px; text-transform: uppercase;
  }
  .source-seed { background: rgba(52, 211, 153, 0.1); color: var(--green); }
  .source-search { background: rgba(96, 165, 250, 0.1); color: var(--blue); }
  .source-manual { background: rgba(251, 191, 36, 0.1); color: var(--yellow); }

  /* Buttons */
  .btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border-radius: var(--radius);
    font-size: 13px; font-weight: 500; cursor: pointer;
    border: 1px solid var(--border); background: var(--surface2);
    color: var(--text); transition: all 0.15s;
  }
  .btn:hover { border-color: var(--accent); background: var(--surface); }
  .btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  .btn-primary:hover { background: var(--accent2); }
  .btn-danger { color: var(--red); }
  .btn-danger:hover { background: rgba(248, 113, 113, 0.1); border-color: var(--red); }
  .btn-sm { padding: 4px 10px; font-size: 12px; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Detail panel */
  .detail-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.6);
    z-index: 200; display: none; justify-content: flex-end;
  }
  .detail-overlay.open { display: flex; }
  .detail-panel {
    width: 520px; max-width: 90vw; background: var(--surface);
    border-left: 1px solid var(--border);
    height: 100%; overflow-y: auto; padding: 24px;
    animation: slideIn 0.2s ease-out;
  }
  @keyframes slideIn { from { transform: translateX(40px); opacity: 0; } to { transform: none; opacity: 1; } }
  .detail-panel h2 { font-size: 22px; margin-bottom: 4px; }
  .detail-panel .website { color: var(--text2); margin-bottom: 16px; }
  .detail-section { margin-bottom: 20px; }
  .detail-section h3 { font-size: 13px; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .detail-field { margin-bottom: 8px; font-size: 14px; }
  .detail-field .field-label { color: var(--text2); font-size: 12px; }
  .detail-links a {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 6px 12px; border-radius: 8px; font-size: 13px;
    background: var(--surface2); border: 1px solid var(--border);
    margin-right: 8px; margin-bottom: 8px;
  }
  .detail-links a:hover { border-color: var(--accent); text-decoration: none; }
  .people-list { list-style: none; }
  .people-list li { padding: 4px 0; font-size: 14px; }
  .signals-list { display: flex; gap: 6px; flex-wrap: wrap; }
  .signal {
    background: rgba(108, 99, 255, 0.1); color: var(--accent2);
    padding: 3px 10px; border-radius: 10px; font-size: 12px;
  }

  /* Modal */
  .modal-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.6);
    z-index: 300; display: none; align-items: center; justify-content: center;
  }
  .modal-overlay.open { display: flex; }
  .modal {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px; width: 480px; max-width: 90vw;
    animation: fadeIn 0.15s;
  }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; } }
  .modal h2 { margin-bottom: 16px; font-size: 18px; }
  .form-group { margin-bottom: 14px; }
  .form-group label { display: block; font-size: 12px; color: var(--text2); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.3px; }
  .form-group input, .form-group select, .form-group textarea {
    width: 100%; background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 12px; color: var(--text); font-size: 14px;
    font-family: inherit; outline: none;
  }
  .form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: var(--accent); }
  .form-group textarea { min-height: 60px; resize: vertical; }
  .form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }

  /* Enrichment log */
  .log-panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); margin-bottom: 24px; display: none;
  }
  .log-panel.open { display: block; }
  .log-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 16px; border-bottom: 1px solid var(--border);
  }
  .log-header h3 { font-size: 14px; }
  .log-body {
    padding: 12px 16px; max-height: 300px; overflow-y: auto;
    font-family: 'Consolas', 'Monaco', monospace; font-size: 12px;
    white-space: pre-wrap; color: var(--text2); line-height: 1.6;
  }
  .spinner {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid var(--border); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Empty state */
  .empty-state {
    text-align: center; padding: 60px 20px; color: var(--text2);
  }
  .empty-state h3 { font-size: 18px; color: var(--text); margin-bottom: 8px; }

  /* Responsive */
  @media (max-width: 768px) {
    .container { padding: 12px; }
    .stats { grid-template-columns: repeat(2, 1fr); }
    td:nth-child(4), th:nth-child(4),
    td:nth-child(6), th:nth-child(6) { display: none; }
  }
</style>
</head>
<body>

<div class="header">
  <h1><span>&#9670;</span> Prospect Finder</h1>
  <div class="header-actions">
    <button class="btn" onclick="exportCSV()">&#8615; Export CSV</button>
    <button class="btn btn-primary" onclick="openAddModal()">+ Add Prospect</button>
  </div>
</div>

<div class="container">
  <!-- Stats -->
  <div class="stats" id="stats"></div>

  <!-- Enrichment log -->
  <div class="log-panel" id="logPanel">
    <div class="log-header">
      <h3><span class="spinner" id="logSpinner"></span> Enrichment Running</h3>
      <button class="btn btn-sm" onclick="closeLog()">Close</button>
    </div>
    <div class="log-body" id="logBody"></div>
  </div>

  <!-- Toolbar -->
  <div class="toolbar">
    <input type="text" class="search-box" id="searchBox" placeholder="Search prospects..." oninput="renderTable()">
    <div class="filter-chips" id="filterChips"></div>
    <button class="btn" id="enrichBtn" onclick="runEnrich('enrich-only')">Enrich Seed List</button>
    <button class="btn" id="searchBtn" onclick="runEnrich('full')">Search + Enrich</button>
  </div>

  <!-- Table -->
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th data-col="name" onclick="sortBy('name')">Name <span class="sort-icon">&#9650;</span></th>
          <th data-col="fit_score" onclick="sortBy('fit_score')">Fit <span class="sort-icon">&#9650;</span></th>
          <th data-col="category" onclick="sortBy('category')">Category <span class="sort-icon">&#9650;</span></th>
          <th data-col="approach">Approach</th>
          <th data-col="source" onclick="sortBy('source')">Source <span class="sort-icon">&#9650;</span></th>
          <th data-col="contact">Links</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
    <div class="empty-state" id="emptyState" style="display:none;">
      <h3>No prospects found</h3>
      <p>Run the enrichment or add prospects manually.</p>
    </div>
  </div>
</div>

<!-- Detail panel -->
<div class="detail-overlay" id="detailOverlay" onclick="if(event.target===this)closeDetail()">
  <div class="detail-panel" id="detailPanel"></div>
</div>

<!-- Add/Edit modal -->
<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <h2 id="modalTitle">Add Prospect</h2>
    <input type="hidden" id="editIndex" value="-1">
    <div class="form-group">
      <label>Company Name *</label>
      <input type="text" id="fName" placeholder="e.g. MedLife">
    </div>
    <div class="form-group">
      <label>Website</label>
      <input type="text" id="fWebsite" placeholder="https://...">
    </div>
    <div class="form-group">
      <label>Category</label>
      <select id="fCategory">
        <option value="healthcare_provider">Healthcare Provider</option>
        <option value="insurance">Insurance</option>
        <option value="corporate_wellness">Corporate Wellness</option>
        <option value="medtech">MedTech / Digital Health</option>
        <option value="vc_investor">VC / Investor</option>
        <option value="unknown">Other</option>
      </select>
    </div>
    <div class="form-group">
      <label>Fit Score (1-5)</label>
      <select id="fScore">
        <option value="5">5 - Perfect fit</option>
        <option value="4">4 - Strong fit</option>
        <option value="3" selected>3 - Good fit</option>
        <option value="2">2 - Possible fit</option>
        <option value="1">1 - Weak fit</option>
      </select>
    </div>
    <div class="form-group">
      <label>Approach</label>
      <input type="text" id="fApproach" placeholder="e.g. Licensing — white-label for patient portal">
    </div>
    <div class="form-group">
      <label>Contact URL</label>
      <input type="text" id="fContact" placeholder="https://...">
    </div>
    <div class="form-group">
      <label>LinkedIn URL</label>
      <input type="text" id="fLinkedin" placeholder="https://linkedin.com/company/...">
    </div>
    <div class="form-group">
      <label>Description</label>
      <textarea id="fDescription" placeholder="Brief description..."></textarea>
    </div>
    <div class="form-group">
      <label>Notes</label>
      <textarea id="fNotes" placeholder="Internal notes..."></textarea>
    </div>
    <div class="form-actions">
      <button class="btn" onclick="closeModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveProspect()">Save</button>
    </div>
  </div>
</div>

<script>
const CATEGORY_LABELS = {
  healthcare_provider: 'Healthcare',
  insurance: 'Insurance',
  corporate_wellness: 'Wellness',
  medtech: 'MedTech',
  vc_investor: 'VC / Investor',
  unknown: 'Other',
};

let prospects = [];
let currentSort = { col: 'fit_score', dir: -1 };
let currentFilter = 'all';
let enrichPoll = null;

// ---- Data loading ----

async function loadData() {
  const [pRes, sRes] = await Promise.all([
    fetch('api/prospects'), fetch('api/stats')
  ]);
  prospects = await pRes.json();
  const stats = await sRes.json();
  renderStats(stats);
  renderFilterChips(stats);
  renderTable();
}

function renderStats(s) {
  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="label">Total Prospects</div><div class="value accent">${s.total}</div></div>
    <div class="stat-card"><div class="label">High Fit (4-5)</div><div class="value green">${s.high_fit}</div></div>
    <div class="stat-card"><div class="label">From Search</div><div class="value">${s.sources.search || 0}</div></div>
    <div class="stat-card"><div class="label">Manual</div><div class="value">${s.sources.manual || 0}</div></div>
  `;
}

function renderFilterChips(s) {
  let html = `<span class="chip ${currentFilter==='all'?'active':''}" onclick="setFilter('all')">All<span class="count">${s.total}</span></span>`;
  for (const [cat, label] of Object.entries(CATEGORY_LABELS)) {
    const cnt = s.categories[cat] ? s.categories[cat].count : 0;
    if (cnt === 0) continue;
    html += `<span class="chip ${currentFilter===cat?'active':''}" onclick="setFilter('${cat}')">${label}<span class="count">${cnt}</span></span>`;
  }
  document.getElementById('filterChips').innerHTML = html;
}

function setFilter(f) { currentFilter = f; renderTable(); renderFilterChips({total: prospects.length, categories: getCats(), sources: getSources()}); }

function getCats() {
  const c = {};
  prospects.forEach(p => { c[p.category] = c[p.category] || {count:0,total_score:0}; c[p.category].count++; c[p.category].total_score += p.fit_score; });
  return c;
}
function getSources() {
  const s = {seed:0,search:0,manual:0};
  prospects.forEach(p => s[p.source] = (s[p.source]||0)+1);
  return s;
}

// ---- Table rendering ----

function renderTable() {
  const q = document.getElementById('searchBox').value.toLowerCase();
  let filtered = prospects.filter(p => {
    if (currentFilter !== 'all' && p.category !== currentFilter) return false;
    if (q && !`${p.name} ${p.description} ${p.approach} ${p.notes}`.toLowerCase().includes(q)) return false;
    return true;
  });

  filtered.sort((a, b) => {
    let va = a[currentSort.col], vb = b[currentSort.col];
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    if (va < vb) return -1 * currentSort.dir;
    if (va > vb) return 1 * currentSort.dir;
    return 0;
  });

  // Update sort indicators
  document.querySelectorAll('th').forEach(th => {
    th.classList.toggle('sorted', th.dataset.col === currentSort.col);
    const icon = th.querySelector('.sort-icon');
    if (icon) icon.innerHTML = (th.dataset.col === currentSort.col && currentSort.dir === 1) ? '&#9650;' : '&#9660;';
  });

  const tbody = document.getElementById('tableBody');
  if (filtered.length === 0) {
    tbody.innerHTML = '';
    document.getElementById('emptyState').style.display = '';
    return;
  }
  document.getElementById('emptyState').style.display = 'none';

  tbody.innerHTML = filtered.map(p => {
    const idx = prospects.indexOf(p);
    const stars = Array.from({length:5}, (_, i) =>
      `<span class="${i < p.fit_score ? 'star-filled' : 'star-empty'}">${i < p.fit_score ? '\u2605' : '\u2606'}</span>`
    ).join('');

    const links = [];
    if (p.website) links.push(`<a href="${esc(p.website)}" target="_blank" title="Website">&#127760;</a>`);
    if (p.contact_url) links.push(`<a href="${esc(p.contact_url)}" target="_blank" title="Contact">&#9993;</a>`);
    if (p.linkedin_url) links.push(`<a href="${esc(p.linkedin_url)}" target="_blank" title="LinkedIn">in</a>`);

    return `<tr onclick="openDetail(${idx})" style="cursor:pointer">
      <td><strong>${esc(p.name)}</strong></td>
      <td><span class="stars">${stars}</span></td>
      <td><span class="badge badge-${p.category}">${CATEGORY_LABELS[p.category] || p.category}</span></td>
      <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(p.approach)}</td>
      <td><span class="source-badge source-${p.source}">${p.source}</span></td>
      <td onclick="event.stopPropagation()">${links.join(' ')}</td>
      <td onclick="event.stopPropagation()">
        <button class="btn btn-sm" onclick="openEditModal(${idx})">Edit</button>
        <button class="btn btn-sm btn-danger" onclick="deleteProspect(${idx})">&#10005;</button>
      </td>
    </tr>`;
  }).join('');
}

function sortBy(col) {
  if (currentSort.col === col) currentSort.dir *= -1;
  else { currentSort.col = col; currentSort.dir = col === 'fit_score' ? -1 : 1; }
  renderTable();
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

// ---- Detail panel ----

function openDetail(idx) {
  const p = prospects[idx];
  const stars = Array.from({length:5}, (_, i) =>
    `<span class="${i < p.fit_score ? 'star-filled' : 'star-empty'}" style="font-size:20px">${i < p.fit_score ? '\u2605' : '\u2606'}</span>`
  ).join('');

  let html = `
    <div style="display:flex;justify-content:space-between;align-items:start">
      <div>
        <h2>${esc(p.name)}</h2>
        <div class="website"><a href="${esc(p.website)}" target="_blank">${esc(p.website)}</a></div>
      </div>
      <button class="btn btn-sm" onclick="closeDetail()">&#10005;</button>
    </div>
    <div style="margin-bottom:16px">
      <span class="badge badge-${p.category}" style="font-size:12px">${CATEGORY_LABELS[p.category] || p.category}</span>
      <span class="source-badge source-${p.source}" style="margin-left:8px">${p.source}</span>
    </div>
    <div style="margin-bottom:20px">${stars} <span style="color:var(--text2);margin-left:8px">${p.fit_score}/5</span></div>
  `;

  if (p.description) {
    html += `<div class="detail-section"><h3>Description</h3><p style="color:var(--text2);font-size:14px">${esc(p.description)}</p></div>`;
  }
  if (p.approach) {
    html += `<div class="detail-section"><h3>Suggested Approach</h3><p style="font-size:14px">${esc(p.approach)}</p></div>`;
  }

  // Links
  const links = [];
  if (p.website) links.push(`<a href="${esc(p.website)}" target="_blank">&#127760; Website</a>`);
  if (p.contact_url) links.push(`<a href="${esc(p.contact_url)}" target="_blank">&#9993; Contact Page</a>`);
  if (p.linkedin_url) links.push(`<a href="${esc(p.linkedin_url)}" target="_blank">&#128279; LinkedIn</a>`);
  if (p.team_page_url) links.push(`<a href="${esc(p.team_page_url)}" target="_blank">&#128101; Team Page</a>`);
  if (links.length) {
    html += `<div class="detail-section"><h3>Links</h3><div class="detail-links">${links.join('')}</div></div>`;
  }

  // Key people
  if (p.key_people && p.key_people.length) {
    html += `<div class="detail-section"><h3>Key People (Public)</h3><ul class="people-list">${p.key_people.map(pp => `<li>${esc(pp)}</li>`).join('')}</ul></div>`;
  }

  // Partner signals
  if (p.partner_signals && p.partner_signals.length) {
    html += `<div class="detail-section"><h3>Partnership Signals</h3><div class="signals-list">${p.partner_signals.map(s => `<span class="signal">${esc(s)}</span>`).join('')}</div></div>`;
  }

  if (p.notes) {
    html += `<div class="detail-section"><h3>Notes</h3><p style="color:var(--text2);font-size:14px">${esc(p.notes)}</p></div>`;
  }

  html += `<div style="margin-top:24px;display:flex;gap:8px">
    <button class="btn" onclick="openEditModal(${idx});closeDetail()">Edit</button>
    <button class="btn btn-danger" onclick="deleteProspect(${idx});closeDetail()">Delete</button>
  </div>`;

  document.getElementById('detailPanel').innerHTML = html;
  document.getElementById('detailOverlay').classList.add('open');
}

function closeDetail() { document.getElementById('detailOverlay').classList.remove('open'); }

// ---- Add/Edit modal ----

function openAddModal() {
  document.getElementById('modalTitle').textContent = 'Add Prospect';
  document.getElementById('editIndex').value = -1;
  document.getElementById('fName').value = '';
  document.getElementById('fWebsite').value = '';
  document.getElementById('fCategory').value = 'healthcare_provider';
  document.getElementById('fScore').value = '3';
  document.getElementById('fApproach').value = '';
  document.getElementById('fContact').value = '';
  document.getElementById('fLinkedin').value = '';
  document.getElementById('fDescription').value = '';
  document.getElementById('fNotes').value = '';
  document.getElementById('modalOverlay').classList.add('open');
}

function openEditModal(idx) {
  const p = prospects[idx];
  document.getElementById('modalTitle').textContent = 'Edit Prospect';
  document.getElementById('editIndex').value = idx;
  document.getElementById('fName').value = p.name || '';
  document.getElementById('fWebsite').value = p.website || '';
  document.getElementById('fCategory').value = p.category || 'unknown';
  document.getElementById('fScore').value = p.fit_score || 3;
  document.getElementById('fApproach').value = p.approach || '';
  document.getElementById('fContact').value = p.contact_url || '';
  document.getElementById('fLinkedin').value = p.linkedin_url || '';
  document.getElementById('fDescription').value = p.description || '';
  document.getElementById('fNotes').value = p.notes || '';
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() { document.getElementById('modalOverlay').classList.remove('open'); }

async function saveProspect() {
  const idx = parseInt(document.getElementById('editIndex').value);
  const data = {
    name: document.getElementById('fName').value.trim(),
    website: document.getElementById('fWebsite').value.trim(),
    category: document.getElementById('fCategory').value,
    fit_score: parseInt(document.getElementById('fScore').value),
    approach: document.getElementById('fApproach').value.trim(),
    contact_url: document.getElementById('fContact').value.trim(),
    linkedin_url: document.getElementById('fLinkedin').value.trim(),
    description: document.getElementById('fDescription').value.trim(),
    notes: document.getElementById('fNotes').value.trim(),
  };
  if (!data.name) { alert('Name is required'); return; }

  if (idx >= 0) {
    await fetch(`api/prospects/${idx}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) });
  } else {
    await fetch('api/prospects', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data) });
  }
  closeModal();
  await loadData();
}

async function deleteProspect(idx) {
  if (!confirm(`Delete "${prospects[idx].name}"?`)) return;
  await fetch(`api/prospects/${idx}`, { method: 'DELETE' });
  await loadData();
}

// ---- Enrichment ----

async function runEnrich(mode) {
  document.getElementById('enrichBtn').disabled = true;
  document.getElementById('searchBtn').disabled = true;
  document.getElementById('logPanel').classList.add('open');
  document.getElementById('logBody').textContent = 'Starting...\n';
  document.getElementById('logSpinner').style.display = '';

  await fetch('api/enrich', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({mode}) });

  enrichPoll = setInterval(async () => {
    const res = await fetch('api/enrich/status');
    const st = await res.json();
    document.getElementById('logBody').textContent = st.log || 'Running...';
    document.getElementById('logBody').scrollTop = document.getElementById('logBody').scrollHeight;
    if (!st.running) {
      clearInterval(enrichPoll);
      document.getElementById('enrichBtn').disabled = false;
      document.getElementById('searchBtn').disabled = false;
      document.getElementById('logSpinner').style.display = 'none';
      await loadData();
    }
  }, 1500);
}

function closeLog() { document.getElementById('logPanel').classList.remove('open'); }

// ---- Export ----

function exportCSV() {
  const header = 'Name,Website,Category,Fit Score,Approach,Contact URL,LinkedIn,Notes,Source\n';
  const rows = prospects.map(p =>
    [p.name, p.website, p.category, p.fit_score, p.approach, p.contact_url, p.linkedin_url, p.notes, p.source]
      .map(v => `"${String(v||'').replace(/"/g,'""')}"`)
      .join(',')
  ).join('\n');
  const blob = new Blob([header + rows], {type: 'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `prospects_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
}

// ---- Keyboard ----
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeDetail(); closeModal(); closeLog(); }
});

// ---- Init ----
loadData();
</script>
</body>
</html>"""


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8500"))
    print(f"Prospect Finder UI — http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

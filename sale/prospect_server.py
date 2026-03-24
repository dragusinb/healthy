#!/usr/bin/env python3
"""
Web interface for the Prospect Finder tool — People-First Edition.
Run: python sale/prospect_server.py
Open: http://localhost:8500  (local) or https://analize.online/prospects/ (prod)
"""

import base64
import json
import os
import secrets
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
import uvicorn

DATA_DIR = Path(__file__).parent
PROSPECTS_JSON = DATA_DIR / "prospects_data.json"
FINDER_SCRIPT = DATA_DIR / "find_prospects.py"

AUTH_USER = os.environ.get("PROSPECT_USER", "admin")
AUTH_PASS = os.environ.get("PROSPECT_PASS", "analize2026!")
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(title="Prospect Finder", root_path=ROOT_PATH)
enrichment_status = {"running": False, "log": "", "last_run": None}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    auth = request.headers.get("authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode("utf-8")
            user, passwd = decoded.split(":", 1)
            if secrets.compare_digest(user, AUTH_USER) and secrets.compare_digest(passwd, AUTH_PASS):
                return await call_next(request)
        except Exception:
            pass
    return Response(status_code=401, content="Unauthorized",
                    headers={"WWW-Authenticate": 'Basic realm="Prospect Finder"'})


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_data() -> list:
    if PROSPECTS_JSON.exists():
        return json.loads(PROSPECTS_JSON.read_text(encoding="utf-8"))
    return []

def save_data(data: list):
    PROSPECTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/companies")
def get_companies():
    return load_data()

@app.get("/api/stats")
def get_stats():
    companies = load_data()
    total_people = sum(len(c.get("people", [])) for c in companies)
    with_linkedin = sum(1 for c in companies for p in c.get("people", []) if p.get("linkedin_url"))
    cats = {}
    for c in companies:
        cat = c.get("category", "unknown")
        cats.setdefault(cat, {"companies": 0, "people": 0})
        cats[cat]["companies"] += 1
        cats[cat]["people"] += len(c.get("people", []))
    return {
        "total_companies": len(companies),
        "total_people": total_people,
        "with_linkedin": with_linkedin,
        "categories": cats,
    }

@app.put("/api/companies/{index}")
def update_company(index: int, data: dict):
    companies = load_data()
    if index < 0 or index >= len(companies):
        raise HTTPException(404)
    for key in ["name", "website", "category", "fit_score", "approach", "why_fit",
                "linkedin_company", "contact_url", "description", "notes"]:
        if key in data:
            companies[index][key] = data[key]
    save_data(companies)
    return companies[index]

@app.post("/api/companies")
def add_company(data: dict):
    companies = load_data()
    new = {
        "name": data.get("name", ""),
        "website": data.get("website", ""),
        "category": data.get("category", "unknown"),
        "fit_score": int(data.get("fit_score", 3)),
        "approach": data.get("approach", ""),
        "why_fit": data.get("why_fit", ""),
        "linkedin_company": data.get("linkedin_company", ""),
        "contact_url": data.get("contact_url", ""),
        "description": data.get("description", ""),
        "notes": data.get("notes", ""),
        "people": [],
    }
    if not new["name"]:
        raise HTTPException(400, "Name required")
    companies.append(new)
    save_data(companies)
    return new

@app.delete("/api/companies/{index}")
def delete_company(index: int):
    companies = load_data()
    if index < 0 or index >= len(companies):
        raise HTTPException(404)
    removed = companies.pop(index)
    save_data(companies)
    return {"deleted": removed["name"]}

@app.post("/api/companies/{index}/people")
def add_person(index: int, data: dict):
    companies = load_data()
    if index < 0 or index >= len(companies):
        raise HTTPException(404)
    person = {
        "name": data.get("name", ""),
        "title": data.get("title", ""),
        "company": companies[index]["name"],
        "linkedin_url": data.get("linkedin_url", ""),
        "relevance": data.get("relevance", ""),
        "message_angle": data.get("message_angle", ""),
        "source": "manual",
        "verified": False,
    }
    if not person["name"]:
        raise HTTPException(400, "Name required")
    companies[index].setdefault("people", []).append(person)
    save_data(companies)
    return person

@app.delete("/api/companies/{ci}/people/{pi}")
def delete_person(ci: int, pi: int):
    companies = load_data()
    if ci < 0 or ci >= len(companies):
        raise HTTPException(404)
    people = companies[ci].get("people", [])
    if pi < 0 or pi >= len(people):
        raise HTTPException(404)
    removed = people.pop(pi)
    save_data(companies)
    return {"deleted": removed["name"]}

@app.post("/api/enrich")
def run_enrichment(data: dict = None):
    if enrichment_status["running"]:
        raise HTTPException(409, "Already running")
    mode = (data or {}).get("mode", "enrich-only")
    cmd = [sys.executable, str(FINDER_SCRIPT)]
    if mode == "enrich-only":
        cmd.append("--enrich-only")
    elif mode == "people-only":
        cmd.append("--people-only")

    def _run():
        enrichment_status["running"] = True
        enrichment_status["log"] = ""
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace")
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


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prospect Finder — People</title>
<style>
:root {
  --bg: #0f1117; --s1: #1a1d27; --s2: #242836; --border: #2e3345;
  --text: #e4e6ed; --text2: #8b90a0; --accent: #6c63ff; --accent2: #8b83ff;
  --green: #34d399; --yellow: #fbbf24; --red: #f87171; --orange: #fb923c; --blue: #60a5fa;
  --radius: 10px;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }
a { color:var(--accent2); text-decoration:none; }
a:hover { text-decoration:underline; }

.header { background:var(--s1); border-bottom:1px solid var(--border); padding:14px 24px; display:flex; align-items:center; justify-content:space-between; position:sticky; top:0; z-index:100; }
.header h1 { font-size:18px; } .header h1 span { color:var(--accent); }
.header-actions { display:flex; gap:8px; }
.container { max-width:1400px; margin:0 auto; padding:20px; }

/* Stats */
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:20px; }
.stat { background:var(--s1); border:1px solid var(--border); border-radius:var(--radius); padding:14px; }
.stat .label { font-size:11px; color:var(--text2); text-transform:uppercase; letter-spacing:.5px; }
.stat .val { font-size:26px; font-weight:700; margin-top:2px; }
.stat .val.g { color:var(--green); } .stat .val.a { color:var(--accent); } .stat .val.y { color:var(--yellow); }

/* Toolbar */
.toolbar { display:flex; gap:10px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }
.search { flex:1; min-width:200px; background:var(--s1); border:1px solid var(--border); border-radius:var(--radius); padding:9px 14px; color:var(--text); font-size:14px; outline:none; }
.search:focus { border-color:var(--accent); }
.chips { display:flex; gap:5px; flex-wrap:wrap; }
.chip { background:var(--s2); border:1px solid var(--border); border-radius:20px; padding:5px 12px; font-size:12px; cursor:pointer; color:var(--text2); }
.chip:hover { border-color:var(--accent); color:var(--text); }
.chip.on { background:var(--accent); border-color:var(--accent); color:#fff; }

/* Buttons */
.btn { display:inline-flex; align-items:center; gap:5px; padding:7px 14px; border-radius:var(--radius); font-size:13px; font-weight:500; cursor:pointer; border:1px solid var(--border); background:var(--s2); color:var(--text); }
.btn:hover { border-color:var(--accent); }
.btn-p { background:var(--accent); border-color:var(--accent); color:#fff; }
.btn-p:hover { background:var(--accent2); }
.btn-d { color:var(--red); } .btn-d:hover { border-color:var(--red); }
.btn-sm { padding:3px 8px; font-size:11px; }
.btn:disabled { opacity:.5; cursor:not-allowed; }

/* Company cards */
.company-card { background:var(--s1); border:1px solid var(--border); border-radius:var(--radius); margin-bottom:12px; overflow:hidden; }
.company-header { padding:14px 18px; display:flex; align-items:center; gap:12px; cursor:pointer; }
.company-header:hover { background:rgba(108,99,255,.03); }
.company-name { font-size:16px; font-weight:600; flex:1; }
.company-meta { display:flex; gap:10px; align-items:center; }
.badge { padding:3px 10px; border-radius:12px; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.3px; }
.badge-healthcare_provider { background:rgba(52,211,153,.12); color:var(--green); }
.badge-insurance { background:rgba(96,165,250,.12); color:var(--blue); }
.badge-wellness { background:rgba(251,191,36,.12); color:var(--yellow); }
.badge-medtech { background:rgba(108,99,255,.12); color:var(--accent2); }
.badge-vc { background:rgba(251,146,60,.12); color:var(--orange); }
.badge-unknown { background:rgba(139,144,160,.12); color:var(--text2); }
.fit { font-size:14px; white-space:nowrap; }
.fit .on { color:var(--yellow); } .fit .off { color:var(--border); }
.approach-tag { font-size:11px; padding:2px 8px; border-radius:8px; background:var(--s2); color:var(--text2); text-transform:uppercase; }
.people-count { font-size:12px; color:var(--text2); min-width:70px; text-align:right; }

/* Expanded content */
.company-body { display:none; padding:0 18px 16px; border-top:1px solid var(--border); }
.company-card.open .company-body { display:block; }
.why-fit { color:var(--text2); font-size:13px; margin:10px 0; font-style:italic; }
.company-links { display:flex; gap:8px; flex-wrap:wrap; margin:10px 0; }
.company-links a { padding:4px 10px; border-radius:8px; font-size:12px; background:var(--s2); border:1px solid var(--border); }
.company-links a:hover { border-color:var(--accent); text-decoration:none; }

/* People table */
.people-table { width:100%; border-collapse:collapse; margin:12px 0; }
.people-table th { text-align:left; padding:8px 10px; font-size:11px; text-transform:uppercase; color:var(--text2); background:var(--s2); border-bottom:1px solid var(--border); }
.people-table td { padding:10px; border-bottom:1px solid var(--border); font-size:13px; }
.people-table tr:last-child td { border-bottom:none; }
.person-name { font-weight:600; font-size:14px; }
.person-title { color:var(--text2); font-size:12px; }
.person-angle { color:var(--text2); font-size:12px; max-width:300px; }
.li-btn { display:inline-flex; align-items:center; gap:4px; padding:4px 10px; border-radius:8px; font-size:12px; font-weight:600; background:rgba(0,119,181,.15); color:#0077b5; border:1px solid rgba(0,119,181,.3); }
.li-btn:hover { background:rgba(0,119,181,.25); text-decoration:none; }
.no-people { color:var(--text2); font-size:13px; padding:12px 0; }

/* Modal */
.modal-bg { position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:300; display:none; align-items:center; justify-content:center; }
.modal-bg.open { display:flex; }
.modal { background:var(--s1); border:1px solid var(--border); border-radius:var(--radius); padding:20px; width:500px; max-width:90vw; max-height:90vh; overflow-y:auto; }
.modal h2 { margin-bottom:14px; font-size:17px; }
.fg { margin-bottom:12px; }
.fg label { display:block; font-size:11px; color:var(--text2); margin-bottom:3px; text-transform:uppercase; }
.fg input,.fg select,.fg textarea { width:100%; background:var(--s2); border:1px solid var(--border); border-radius:8px; padding:7px 10px; color:var(--text); font-size:13px; font-family:inherit; outline:none; }
.fg input:focus,.fg select:focus,.fg textarea:focus { border-color:var(--accent); }
.fg textarea { min-height:50px; resize:vertical; }
.form-actions { display:flex; gap:8px; justify-content:flex-end; margin-top:14px; }

/* Log */
.log-panel { background:var(--s1); border:1px solid var(--border); border-radius:var(--radius); margin-bottom:16px; display:none; }
.log-panel.open { display:block; }
.log-head { display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-bottom:1px solid var(--border); }
.log-body { padding:10px 14px; max-height:250px; overflow-y:auto; font-family:Consolas,Monaco,monospace; font-size:11px; white-space:pre-wrap; color:var(--text2); line-height:1.5; }
.spinner { display:inline-block; width:12px; height:12px; border:2px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:spin .8s linear infinite; margin-right:6px; }
@keyframes spin { to { transform:rotate(360deg); } }
</style>
</head>
<body>

<div class="header">
  <h1><span>&#9670;</span> Prospect Finder &mdash; People</h1>
  <div class="header-actions">
    <button class="btn" onclick="exportCSV()">Export CSV</button>
    <button class="btn btn-p" onclick="openAddCompany()">+ Company</button>
  </div>
</div>

<div class="container">
  <div class="stats" id="stats"></div>

  <div class="log-panel" id="logPanel">
    <div class="log-head">
      <span><span class="spinner" id="logSpin"></span> Running...</span>
      <button class="btn btn-sm" onclick="el('logPanel').classList.remove('open')">Close</button>
    </div>
    <div class="log-body" id="logBody"></div>
  </div>

  <div class="toolbar">
    <input type="text" class="search" id="searchBox" placeholder="Search people or companies..." oninput="render()">
    <div class="chips" id="chips"></div>
    <button class="btn" id="btnEnrich" onclick="runEnrich('enrich-only')">Scrape Team Pages</button>
    <button class="btn" id="btnSearch" onclick="runEnrich('full')">Search People</button>
  </div>

  <div id="list"></div>
</div>

<!-- Add Company Modal -->
<div class="modal-bg" id="companyModal" onclick="if(event.target===this)this.classList.remove('open')">
  <div class="modal">
    <h2 id="companyModalTitle">Add Company</h2>
    <input type="hidden" id="editCompanyIdx" value="-1">
    <div class="fg"><label>Company Name *</label><input id="cName"></div>
    <div class="fg"><label>Website</label><input id="cWebsite"></div>
    <div class="fg"><label>Category</label>
      <select id="cCategory">
        <option value="healthcare_provider">Healthcare Provider</option>
        <option value="insurance">Insurance</option>
        <option value="wellness">Corporate Wellness</option>
        <option value="medtech">MedTech / Digital Health</option>
        <option value="vc">VC / Investor</option>
        <option value="unknown">Other</option>
      </select>
    </div>
    <div class="fg"><label>Fit Score (1-5)</label>
      <select id="cScore"><option value="5">5</option><option value="4">4</option><option value="3" selected>3</option><option value="2">2</option><option value="1">1</option></select>
    </div>
    <div class="fg"><label>Approach</label><input id="cApproach" placeholder="licensing / acquisition / partnership / investment"></div>
    <div class="fg"><label>Why This Company?</label><textarea id="cWhy" placeholder="One sentence..."></textarea></div>
    <div class="fg"><label>Company LinkedIn</label><input id="cLinkedin"></div>
    <div class="fg"><label>Notes</label><textarea id="cNotes"></textarea></div>
    <div class="form-actions">
      <button class="btn" onclick="el('companyModal').classList.remove('open')">Cancel</button>
      <button class="btn btn-p" onclick="saveCompany()">Save</button>
    </div>
  </div>
</div>

<!-- Add Person Modal -->
<div class="modal-bg" id="personModal" onclick="if(event.target===this)this.classList.remove('open')">
  <div class="modal">
    <h2>Add Decision-Maker</h2>
    <input type="hidden" id="personCompanyIdx" value="-1">
    <div class="fg"><label>Full Name *</label><input id="pName"></div>
    <div class="fg"><label>Title / Role *</label><input id="pTitle" placeholder="CEO, CTO, Head of Digital..."></div>
    <div class="fg"><label>LinkedIn Profile URL</label><input id="pLinkedin" placeholder="https://linkedin.com/in/..."></div>
    <div class="fg"><label>Why This Person?</label><textarea id="pRelevance" placeholder="What makes them the right contact"></textarea></div>
    <div class="fg"><label>Message Angle</label><textarea id="pAngle" placeholder="Personalized opening line idea for outreach"></textarea></div>
    <div class="form-actions">
      <button class="btn" onclick="el('personModal').classList.remove('open')">Cancel</button>
      <button class="btn btn-p" onclick="savePerson()">Save</button>
    </div>
  </div>
</div>

<script>
const CAT_LABELS = {healthcare_provider:'Healthcare',insurance:'Insurance',wellness:'Wellness',medtech:'MedTech',vc:'VC / Investor',unknown:'Other'};
let companies = [], filter = 'all', enrichPoll = null;

function el(id) { return document.getElementById(id); }
function esc(s) { if(!s)return''; const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

async function load() {
  const [cRes, sRes] = await Promise.all([fetch('api/companies'), fetch('api/stats')]);
  companies = await cRes.json();
  const stats = await sRes.json();
  renderStats(stats);
  renderChips(stats);
  render();
}

function renderStats(s) {
  el('stats').innerHTML = `
    <div class="stat"><div class="label">Companies</div><div class="val a">${s.total_companies}</div></div>
    <div class="stat"><div class="label">Decision-Makers</div><div class="val g">${s.total_people}</div></div>
    <div class="stat"><div class="label">With LinkedIn</div><div class="val y">${s.with_linkedin}</div></div>
    <div class="stat"><div class="label">Ready to Contact</div><div class="val">${s.with_linkedin}</div></div>
  `;
}

function renderChips(s) {
  let h = `<span class="chip ${filter==='all'?'on':''}" onclick="setFilter('all')">All</span>`;
  for (const [k,v] of Object.entries(CAT_LABELS)) {
    const n = s.categories[k]?.companies || 0;
    if(!n) continue;
    const p = s.categories[k]?.people || 0;
    h += `<span class="chip ${filter===k?'on':''}" onclick="setFilter('${k}')">${v} (${p})</span>`;
  }
  el('chips').innerHTML = h;
}

function setFilter(f) { filter=f; render(); }

function render() {
  const q = el('searchBox').value.toLowerCase();
  const filtered = companies.filter((c,i) => {
    c._idx = i;
    if (filter !== 'all' && c.category !== filter) return false;
    if (!q) return true;
    const haystack = `${c.name} ${c.why_fit} ${c.approach} ${c.notes} ${(c.people||[]).map(p=>`${p.name} ${p.title} ${p.relevance} ${p.message_angle}`).join(' ')}`.toLowerCase();
    return haystack.includes(q);
  });

  if (!filtered.length) {
    el('list').innerHTML = '<div style="text-align:center;padding:40px;color:var(--text2)">No companies match.</div>';
    return;
  }

  el('list').innerHTML = filtered.map(c => {
    const idx = c._idx;
    const people = c.people || [];
    const stars = Array.from({length:5},(_,i) => `<span class="${i<c.fit_score?'on':'off'}">${i<c.fit_score?'\u2605':'\u2606'}</span>`).join('');
    const peopleCount = people.length ? `${people.length} people` : '<span style="color:var(--red)">0 people</span>';

    let peopleHTML = '';
    if (people.length) {
      peopleHTML = `<table class="people-table"><thead><tr><th>Name</th><th>Title</th><th>LinkedIn</th><th>Message Angle</th><th></th></tr></thead><tbody>`;
      peopleHTML += people.map((p,pi) => {
        const li = p.linkedin_url
          ? `<a class="li-btn" href="${esc(p.linkedin_url)}" target="_blank" onclick="event.stopPropagation()">in Profile</a>`
          : '<span style="color:var(--text2);font-size:11px">not found</span>';
        return `<tr>
          <td><div class="person-name">${esc(p.name)}</div><div class="person-title">${esc(p.source||'')}</div></td>
          <td>${esc(p.title)}</td>
          <td>${li}</td>
          <td><div class="person-angle">${esc(p.message_angle || p.relevance || '')}</div></td>
          <td><button class="btn btn-sm btn-d" onclick="event.stopPropagation();deletePerson(${idx},${pi})">x</button></td>
        </tr>`;
      }).join('');
      peopleHTML += '</tbody></table>';
    } else {
      peopleHTML = '<div class="no-people">No decision-makers found yet. Click "Add Person" or run search.</div>';
    }

    const links = [];
    if (c.website) links.push(`<a href="${esc(c.website)}" target="_blank">Website</a>`);
    if (c.linkedin_company) links.push(`<a href="${esc(c.linkedin_company)}" target="_blank">Company LinkedIn</a>`);
    if (c.contact_url) links.push(`<a href="${esc(c.contact_url)}" target="_blank">Contact</a>`);

    return `<div class="company-card" id="card-${idx}">
      <div class="company-header" onclick="toggle(${idx})">
        <span class="company-name">${esc(c.name)}</span>
        <div class="company-meta">
          <span class="approach-tag">${esc(c.approach||'')}</span>
          <span class="badge badge-${c.category}">${CAT_LABELS[c.category]||c.category}</span>
          <span class="fit">${stars}</span>
          <span class="people-count">${peopleCount}</span>
        </div>
      </div>
      <div class="company-body">
        ${c.why_fit ? `<div class="why-fit">"${esc(c.why_fit)}"</div>` : ''}
        <div class="company-links">${links.join('')}</div>
        ${peopleHTML}
        <div style="display:flex;gap:8px;margin-top:8px">
          <button class="btn btn-sm btn-p" onclick="event.stopPropagation();openAddPerson(${idx})">+ Add Person</button>
          <button class="btn btn-sm" onclick="event.stopPropagation();openEditCompany(${idx})">Edit Company</button>
          <button class="btn btn-sm btn-d" onclick="event.stopPropagation();deleteCompany(${idx})">Delete</button>
        </div>
        ${c.notes ? `<div style="margin-top:8px;font-size:12px;color:var(--text2)">${esc(c.notes)}</div>` : ''}
      </div>
    </div>`;
  }).join('');
}

function toggle(idx) { document.getElementById('card-'+idx)?.classList.toggle('open'); }

// --- Company CRUD ---
function openAddCompany() {
  el('companyModalTitle').textContent = 'Add Company';
  el('editCompanyIdx').value = -1;
  el('cName').value=''; el('cWebsite').value=''; el('cCategory').value='healthcare_provider';
  el('cScore').value='3'; el('cApproach').value=''; el('cWhy').value=''; el('cLinkedin').value=''; el('cNotes').value='';
  el('companyModal').classList.add('open');
}
function openEditCompany(idx) {
  const c = companies[idx];
  el('companyModalTitle').textContent = 'Edit Company';
  el('editCompanyIdx').value = idx;
  el('cName').value = c.name||''; el('cWebsite').value = c.website||''; el('cCategory').value = c.category||'unknown';
  el('cScore').value = c.fit_score||3; el('cApproach').value = c.approach||''; el('cWhy').value = c.why_fit||'';
  el('cLinkedin').value = c.linkedin_company||''; el('cNotes').value = c.notes||'';
  el('companyModal').classList.add('open');
}
async function saveCompany() {
  const idx = parseInt(el('editCompanyIdx').value);
  const data = {
    name: el('cName').value.trim(), website: el('cWebsite').value.trim(),
    category: el('cCategory').value, fit_score: parseInt(el('cScore').value),
    approach: el('cApproach').value.trim(), why_fit: el('cWhy').value.trim(),
    linkedin_company: el('cLinkedin').value.trim(), notes: el('cNotes').value.trim(),
  };
  if (!data.name) return alert('Name required');
  if (idx >= 0) await fetch(`api/companies/${idx}`, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  else await fetch('api/companies', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  el('companyModal').classList.remove('open');
  await load();
}
async function deleteCompany(idx) {
  if (!confirm(`Delete "${companies[idx].name}"?`)) return;
  await fetch(`api/companies/${idx}`, {method:'DELETE'});
  await load();
}

// --- Person CRUD ---
function openAddPerson(companyIdx) {
  el('personCompanyIdx').value = companyIdx;
  el('pName').value=''; el('pTitle').value=''; el('pLinkedin').value=''; el('pRelevance').value=''; el('pAngle').value='';
  el('personModal').classList.add('open');
}
async function savePerson() {
  const ci = parseInt(el('personCompanyIdx').value);
  const data = {
    name: el('pName').value.trim(), title: el('pTitle').value.trim(),
    linkedin_url: el('pLinkedin').value.trim(), relevance: el('pRelevance').value.trim(),
    message_angle: el('pAngle').value.trim(),
  };
  if (!data.name) return alert('Name required');
  await fetch(`api/companies/${ci}/people`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  el('personModal').classList.remove('open');
  await load();
}
async function deletePerson(ci,pi) {
  if (!confirm('Remove this person?')) return;
  await fetch(`api/companies/${ci}/people/${pi}`, {method:'DELETE'});
  await load();
}

// --- Enrichment ---
async function runEnrich(mode) {
  el('btnEnrich').disabled=true; el('btnSearch').disabled=true;
  el('logPanel').classList.add('open');
  el('logBody').textContent='Starting...\n';
  el('logSpin').style.display='';
  await fetch('api/enrich',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode})});
  enrichPoll = setInterval(async()=>{
    const r = await(await fetch('api/enrich/status')).json();
    el('logBody').textContent = r.log||'Running...';
    el('logBody').scrollTop = el('logBody').scrollHeight;
    if(!r.running) {
      clearInterval(enrichPoll);
      el('btnEnrich').disabled=false; el('btnSearch').disabled=false;
      el('logSpin').style.display='none';
      await load();
    }
  },1500);
}

// --- Export ---
function exportCSV() {
  let rows = ['Company,Category,Fit,Person,Title,LinkedIn,Message Angle'];
  for (const c of companies) {
    for (const p of (c.people||[])) {
      rows.push([c.name,c.category,c.fit_score,p.name,p.title,p.linkedin_url,p.message_angle||p.relevance||'']
        .map(v=>`"${String(v||'').replace(/"/g,'""')}"`).join(','));
    }
    if (!(c.people||[]).length) {
      rows.push([c.name,c.category,c.fit_score,'','','',''].map(v=>`"${String(v||'').replace(/"/g,'""')}"`).join(','));
    }
  }
  const blob = new Blob([rows.join('\n')],{type:'text/csv'});
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download=`prospects_people_${new Date().toISOString().slice(0,10)}.csv`; a.click();
}

document.addEventListener('keydown',e=>{ if(e.key==='Escape'){el('companyModal').classList.remove('open');el('personModal').classList.remove('open');} });
load();
</script>
</body>
</html>"""

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8500"))
    print(f"Prospect Finder UI — http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

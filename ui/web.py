import os

import httpx
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="AUTOSAR HLD Assistant UI")
BACKEND_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def backend_get(path: str) -> httpx.Response:
    return httpx.get(f"{BACKEND_URL}{path}", timeout=10)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return PAGE


@app.get("/api/status")
def status() -> JSONResponse:
    try:
        response = backend_get("/health/ready")
        return JSONResponse(response.json(), status_code=response.status_code)
    except httpx.HTTPError as exc:
        return JSONResponse({"status": "offline", "detail": str(exc)}, status_code=503)


@app.get("/api/documents")
def documents() -> JSONResponse:
    try:
        response = backend_get("/documents")
        return JSONResponse(response.json(), status_code=response.status_code)
    except httpx.HTTPError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=503)


@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),  # noqa: B008
    title: str = Form("AUTOSAR HLD"),  # noqa: B008
    version_label: str = Form("v1.0"),  # noqa: B008
) -> JSONResponse:
    data = await file.read()
    try:
        response = httpx.post(
            f"{BACKEND_URL}/documents/upload",
            files={"file": (file.filename or "document.pdf", data, "application/pdf")},
            data={"title": title, "version_label": version_label},
            timeout=120,
        )
        return JSONResponse(response.json(), status_code=response.status_code)
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)


@app.post("/api/ask")
async def ask(payload: dict[str, str]) -> JSONResponse:
    try:
        response = httpx.post(f"{BACKEND_URL}/qa/ask", json=payload, timeout=120)
        return JSONResponse(response.json(), status_code=response.status_code)
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)


@app.get("/api/entities/{document_id}")
def entities(document_id: str) -> JSONResponse:
    try:
        response = backend_get(f"/analysis/documents/{document_id}/entities")
        return JSONResponse(response.json(), status_code=response.status_code)
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)


@app.post("/api/compare")
async def compare(payload: dict[str, str]) -> JSONResponse:
    try:
        response = httpx.post(f"{BACKEND_URL}/analysis/compare", json=payload, timeout=30)
        return JSONResponse(response.json(), status_code=response.status_code)
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)


@app.post("/api/validate/{document_id}")
def validate(document_id: str) -> JSONResponse:
    try:
        response = httpx.post(f"{BACKEND_URL}/analysis/validate/{document_id}", timeout=30)
        return JSONResponse(response.json(), status_code=response.status_code)
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)


@app.get("/api/findings")
def findings(document_id: str | None = None) -> JSONResponse:
    try:
        path = "/analysis/findings"
        if document_id:
            path += f"?document_id={document_id}"
        response = backend_get(path)
        return JSONResponse(response.json(), status_code=response.status_code)
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=502)


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AUTOSAR | Engineering Intelligence</title>
  <style>
    :root {
      --navy:#0d1b2a; --navy-2:#142b42; --ink:#172b4d; --muted:#6b7a90;
      --blue:#2f80ed; --cyan:#00b8d9; --green:#16a36a; --amber:#f59e0b;
      --line:#e6edf5; --bg:#f5f8fc; --white:#fff; --shadow:0 14px 40px #12243b12;
    }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; color:var(--ink); background:var(--bg); }
    button,input { font:inherit; }
    button { cursor:pointer; border:0; }
    .shell { display:flex; min-height:100vh; }
    .sidebar { width:250px; background:var(--navy); color:#dbe8f5; padding:25px 16px; position:fixed; inset:0 auto 0 0; }
    .brand { display:flex; gap:11px; align-items:center; padding:0 10px 30px; }
    .brand-mark { width:37px; height:37px; display:grid; place-items:center; border-radius:11px; color:white;
      background:linear-gradient(135deg,var(--blue),var(--cyan)); font-weight:800; font-size:20px; }
    .brand strong { display:block; color:#fff; letter-spacing:.4px; font-size:15px; }
    .brand small { color:#8ca2b9; font-size:10px; letter-spacing:1.3px; }
    .nav-label { color:#71869d; text-transform:uppercase; font-size:10px; font-weight:700; letter-spacing:1.4px; padding:0 12px 9px; }
    .nav-item { width:100%; text-align:left; padding:12px 13px; margin:3px 0; border-radius:9px; color:#aebed0; background:transparent; }
    .nav-item:hover,.nav-item.active { background:#ffffff12; color:#fff; }
    .nav-item span { display:inline-block; width:25px; color:#6f9ed3; }
    .side-bottom { position:absolute; bottom:24px; left:25px; right:25px; color:#7990a7; font-size:11px; line-height:1.55; }
    .main { margin-left:250px; width:calc(100% - 250px); padding:27px 38px 50px; }
    .topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:28px; }
    .eyebrow { color:var(--blue); text-transform:uppercase; letter-spacing:1.5px; font-size:11px; font-weight:800; }
    h1 { font-size:27px; margin:6px 0 0; letter-spacing:-.5px; }
    .top-actions { display:flex; align-items:center; gap:15px; }
    .live { display:flex; align-items:center; gap:7px; color:var(--green); font-size:12px; font-weight:700; }
    .dot { width:8px; height:8px; border-radius:50%; background:var(--green); box-shadow:0 0 0 4px #16a36a1f; }
    .avatar { width:36px; height:36px; display:grid; place-items:center; background:#dceaff; color:#2369ba; border-radius:50%; font-weight:800; }
    .page { display:none; animation:fade .25s ease; }
    .page.active { display:block; }
    @keyframes fade { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:none; } }
    .hero { border-radius:16px; padding:27px 30px; color:white; background:linear-gradient(115deg,#153b64,#1a628d 63%,#158c9c);
      display:flex; align-items:center; justify-content:space-between; overflow:hidden; position:relative; }
    .hero:after { content:""; position:absolute; width:300px; height:300px; border:1px solid #ffffff2e; border-radius:50%; right:-100px; top:-130px; }
    .hero h2 { font-size:22px; margin:0 0 8px; position:relative; z-index:1; }
    .hero p { margin:0; color:#d5e9f5; font-size:13px; max-width:590px; position:relative; z-index:1; }
    .hero button { position:relative; z-index:1; background:white; color:#17689a; padding:11px 16px; border-radius:8px; font-weight:700; }
    .kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; margin:20px 0; }
    .kpi,.card { background:var(--white); border:1px solid var(--line); border-radius:13px; box-shadow:var(--shadow); }
    .kpi { padding:18px; display:flex; justify-content:space-between; }
    .kpi-label { color:var(--muted); font-size:12px; }
    .kpi-value { font-size:26px; font-weight:800; margin-top:7px; }
    .kpi-icon { width:36px; height:36px; display:grid; place-items:center; background:#eaf3ff; color:var(--blue); border-radius:9px; font-weight:800; }
    .grid-2 { display:grid; grid-template-columns:1.2fr .8fr; gap:20px; }
    .card { padding:22px; }
    .card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:17px; }
    .card h3 { margin:0; font-size:15px; }
    .muted { color:var(--muted); font-size:12px; }
    .pipeline { display:flex; align-items:center; justify-content:space-between; gap:6px; padding:12px 0 8px; }
    .stage { text-align:center; flex:1; }
    .stage-icon { margin:auto; width:38px; height:38px; display:grid; place-items:center; color:#1c6bc1; background:#eaf3ff; border-radius:50%; font-weight:800; }
    .stage b { display:block; font-size:11px; margin-top:8px; }
    .connector { height:2px; flex:1; background:#cfe0f1; margin-top:-23px; }
    .activity { display:flex; align-items:start; gap:11px; padding:11px 0; border-bottom:1px solid #eff3f7; }
    .activity:last-child { border:0; }
    .activity-icon { width:27px; height:27px; display:grid; place-items:center; border-radius:8px; background:#e8f8f1; color:var(--green); font-size:12px; }
    .activity b { font-size:12px; display:block; }
    .activity small { color:var(--muted); font-size:11px; }
    .upload-layout { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
    .dropzone { border:1.5px dashed #a9c5e3; border-radius:12px; padding:34px 22px; text-align:center; background:#f8fbff; }
    .dropzone.drag { border-color:var(--blue); background:#edf6ff; }
    .upload-icon { font-size:30px; color:var(--blue); margin-bottom:9px; }
    .dropzone h3 { margin:4px 0; font-size:15px; }
    .dropzone p { color:var(--muted); font-size:12px; margin:7px 0 17px; }
    .primary { background:var(--blue); color:#fff; padding:11px 17px; border-radius:8px; font-weight:700; }
    .secondary { background:#edf4fc; color:#24639f; padding:10px 14px; border-radius:8px; font-weight:700; }
    .form-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:13px 0; }
    label { display:block; color:var(--muted); font-size:11px; font-weight:700; margin-bottom:6px; }
    input { border:1px solid #dce6f0; border-radius:7px; padding:11px 12px; width:100%; outline:none; color:var(--ink); background:#fff; }
    input:focus { border-color:var(--blue); box-shadow:0 0 0 3px #2f80ed16; }
    .toolbar { display:flex; gap:10px; margin-bottom:16px; }
    .toolbar input { max-width:360px; }
    .table-wrap { overflow:auto; }
    table { border-collapse:collapse; width:100%; font-size:12px; }
    th { background:#f7fafd; color:var(--muted); text-align:left; padding:12px; font-size:10px; text-transform:uppercase; letter-spacing:.6px; }
    td { padding:14px 12px; border-top:1px solid #edf1f5; }
    .badge { display:inline-block; border-radius:20px; padding:5px 9px; background:#e7f8ef; color:#128052; font-size:10px; font-weight:800; }
    .qa-layout { display:grid; grid-template-columns:1.1fr .9fr; gap:20px; }
    .prompt-box { display:flex; gap:8px; margin-top:14px; }
    .prompt-box input { flex:1; }
    .answer { margin-top:18px; padding:17px; border-radius:10px; background:#f7fbff; border-left:3px solid var(--blue); line-height:1.65; font-size:13px; white-space:pre-wrap; min-height:100px; }
    .source { padding:13px 0; border-bottom:1px solid #edf1f5; }
    .source:last-child { border:0; }
    .source-title { color:var(--blue); font-weight:800; font-size:12px; }
    .source p { margin:6px 0 0; color:#53657d; font-size:11px; line-height:1.5; }
    .source mark { background:#fff1b8; padding:1px 3px; border-radius:3px; }
    .analysis-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
    .finding { padding:13px 0; border-bottom:1px solid #edf1f5; }
    .finding:last-child { border:0; }
    .severity { font-size:10px; font-weight:800; color:#b45309; text-transform:uppercase; }
    .arch { display:grid; grid-template-columns:repeat(4,1fr); gap:15px; margin-top:20px; }
    .arch-box { text-align:center; padding:22px 12px; border-radius:12px; background:#fff; border:1px solid var(--line); }
    .arch-box strong { display:block; margin-top:9px; font-size:12px; }
    .arch-box span { color:var(--muted); font-size:11px; }
    .toast { position:fixed; right:25px; bottom:24px; padding:13px 17px; color:white; background:#173b61; border-radius:9px; box-shadow:var(--shadow); transform:translateY(90px); opacity:0; transition:.25s; font-size:12px; }
    .toast.show { transform:none; opacity:1; }
    @media(max-width:950px) { .sidebar { width:205px; } .main { margin-left:205px; width:calc(100% - 205px); padding:22px; } .kpis { grid-template-columns:repeat(2,1fr); } .grid-2,.upload-layout,.qa-layout { grid-template-columns:1fr; } }
    @media(max-width:650px) { .sidebar { position:static; width:100%; min-height:auto; } .side-bottom { display:none; } .shell { display:block; } .main { margin:0; width:100%; } .nav-item { width:auto; display:inline-block; } .nav-label { display:none; } .brand { padding-bottom:15px; } .topbar { align-items:start; } .hero { display:block; } .hero button { margin-top:18px; } .kpis { grid-template-columns:1fr 1fr; } .arch { grid-template-columns:1fr 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand"><div class="brand-mark">A</div><div><strong>AUTOSAR HLD</strong><small>ENGINEERING INTELLIGENCE</small></div></div>
      <div class="nav-label">Workspace</div>
      <button class="nav-item active" data-page="dashboard"><span>▦</span>Overview</button>
      <button class="nav-item" data-page="ingestion"><span>↑</span>Ingest documents</button>
      <button class="nav-item" data-page="knowledge"><span>▤</span>Knowledge base</button>
      <button class="nav-item" data-page="qa"><span>⌕</span>Architecture Q&A</button>
      <button class="nav-item" data-page="analysis"><span>✓</span>Validation & comparison</button>
      <button class="nav-item" data-page="architecture"><span>⌘</span>Architecture map</button>
      <div class="nav-label" style="margin-top:25px">Resources</div>
      <button class="nav-item" onclick="window.open('http://localhost:8000/docs','_blank')"><span>↗</span>API documentation</button>
      <div class="side-bottom">PRIVATE WORKSPACE<br><span id="side-status">Checking local services...</span></div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div><div class="eyebrow">Project workspace / CS1</div><h1 id="page-title">Architecture overview</h1></div>
        <div class="top-actions"><div class="live"><i class="dot"></i><span id="top-status">Local services online</span></div><div class="avatar">AE</div></div>
      </header>
      <section class="page active" id="dashboard">
        <div class="hero"><div><h2>Welcome to your architecture workspace</h2><p>Search approved HLD knowledge, validate evidence, and accelerate design reviews without sending project data outside your private environment.</p></div><button onclick="showPage('ingestion')">+ Ingest HLD</button></div>
        <div class="kpis">
          <div class="kpi"><div><div class="kpi-label">Approved documents</div><div class="kpi-value" id="doc-count">—</div></div><div class="kpi-icon">▤</div></div>
          <div class="kpi"><div><div class="kpi-label">Indexed chunks</div><div class="kpi-value" id="chunk-count">—</div></div><div class="kpi-icon">⌁</div></div>
          <div class="kpi"><div><div class="kpi-label">Architecture entities</div><div class="kpi-value" id="entity-count">—</div></div><div class="kpi-icon">◇</div></div>
          <div class="kpi"><div><div class="kpi-label">Evidence mode</div><div class="kpi-value" style="font-size:18px;color:var(--green)">ACTIVE</div></div><div class="kpi-icon">✓</div></div>
        </div>
        <div class="grid-2"><div class="card"><div class="card-head"><h3>Evidence-first pipeline</h3><span class="muted">Live architecture</span></div><div class="pipeline"><div class="stage"><div class="stage-icon">↑</div><b>Ingest</b></div><div class="connector"></div><div class="stage"><div class="stage-icon">▤</div><b>Chunk</b></div><div class="connector"></div><div class="stage"><div class="stage-icon">⌕</div><b>Retrieve</b></div><div class="connector"></div><div class="stage"><div class="stage-icon">✓</div><b>Cite</b></div></div><p class="muted" style="margin-top:20px">Every answer is restricted to approved evidence and shows document, version, page, and section citations.</p></div>
          <div class="card"><div class="card-head"><h3>Recent activity</h3><span class="muted">This session</span></div><div class="activity"><div class="activity-icon">✓</div><div><b>Local services verified</b><small>SQLite and FastAPI are ready</small></div></div><div class="activity"><div class="activity-icon">↑</div><div><b id="activity-text">Waiting for first document</b><small>Upload an HLD to start analysis</small></div></div><div class="activity"><div class="activity-icon">⌕</div><div><b>Evidence guardrail enabled</b><small>Not-found response prevents guessing</small></div></div></div></div>
      </section>
      <section class="page" id="ingestion">
        <div class="card"><div class="card-head"><div><h3>Ingest an approved HLD</h3><div class="muted">Add a source document to the private architecture repository</div></div><span class="badge">CONTROLLED INGESTION</span></div>
          <div class="upload-layout"><div><div class="dropzone" id="dropzone"><div class="upload-icon">⇧</div><h3>Drop your PDF here</h3><p>PDF files only · source document is never modified</p><input id="file" type="file" accept=".pdf" hidden><button class="secondary" type="button" onclick="document.getElementById('file').click()">Choose PDF</button><div id="file-name" class="muted" style="margin-top:10px">No file selected</div></div></div>
          <div><div class="form-row"><div><label>DOCUMENT TITLE</label><input id="title" value="AUTOSAR HLD Case Study"></div><div><label>VERSION LABEL</label><input id="version" value="v1.0"></div></div><div class="form-row"><div><label>PROJECT</label><input id="project" value="Default Project"></div><div><label>UPLOADED BY</label><input id="uploader" value="Engineer"></div></div><button class="primary" id="upload-btn" onclick="uploadDocument()">Upload and index document</button><div id="upload-result" class="answer" style="display:none"></div></div></div>
        </div>
        <div class="card" style="margin-top:20px"><div class="card-head"><h3>Ingestion controls</h3><span class="muted">Evidence policy</span></div><div class="arch"><div class="arch-box"><div class="stage-icon">1</div><strong>Hash check</strong><span>Deduplicate by SHA-256</span></div><div class="arch-box"><div class="stage-icon">2</div><strong>Parse pages</strong><span>Preserve page numbers</span></div><div class="arch-box"><div class="stage-icon">3</div><strong>Chunk sections</strong><span>Keep context attached</span></div><div class="arch-box"><div class="stage-icon">4</div><strong>Review-ready</strong><span>Entities start Pending</span></div></div></div>
      </section>
      <section class="page" id="knowledge"><div class="card"><div class="card-head"><div><h3>Knowledge base</h3><div class="muted">Approved documents currently available for retrieval</div></div><button class="secondary" onclick="loadDocuments()">↻ Refresh</button></div><div class="toolbar"><input id="doc-filter" placeholder="Filter by title or version..." oninput="filterDocs()"></div><div class="table-wrap"><table><thead><tr><th>Document</th><th>Version</th><th>Status</th><th>Chunks</th><th>Entities</th></tr></thead><tbody id="doc-table"><tr><td colspan="5" class="muted">Loading documents...</td></tr></tbody></table></div></div></section>
      <section class="page" id="qa"><div class="qa-layout"><div class="card"><div class="card-head"><div><h3>Ask your architecture</h3><div class="muted">Search one approved document at a time</div></div><span class="badge">CITED ANSWERS</span></div><label style="margin-top:14px">SOURCE DOCUMENT</label><select id="qa-document" style="width:100%;border:1px solid #dce6f0;border-radius:7px;padding:11px 12px;color:var(--ink);background:#fff"><option value="">All approved documents</option></select><div class="prompt-box"><input id="question" placeholder="e.g. What are Abhay's technical skills?" onkeydown="if(event.key==='Enter') askQuestion()"><button class="primary" onclick="askQuestion()">Ask</button></div><div class="muted" style="margin-top:12px">Select “abhay resume · v2” for resume questions.</div><div id="answer" class="answer">Select a source document, then ask a question.</div></div><div class="card"><div class="card-head"><h3>Retrieved sources</h3><span class="muted">Page-level evidence</span></div><div id="sources"><div class="muted">Ask a question to view source snippets.</div></div></div></div></section>
      <section class="page" id="analysis">
        <div class="card"><div class="card-head"><div><h3>Validation and revision comparison</h3><div class="muted">Findings are evidence-backed and remain pending engineering review.</div></div><span class="badge">HUMAN REVIEW REQUIRED</span></div>
          <div class="analysis-grid">
            <div><label>DOCUMENT TO VALIDATE</label><select id="validate-document" style="width:100%;border:1px solid #dce6f0;border-radius:7px;padding:11px 12px;color:var(--ink);background:#fff"></select><button class="primary" style="margin-top:12px" onclick="validateDocument()">Run validation checks</button></div>
            <div><label>COMPARE VERSIONS</label><div class="form-row"><select id="compare-a" style="width:100%;border:1px solid #dce6f0;border-radius:7px;padding:11px 12px"></select><select id="compare-b" style="width:100%;border:1px solid #dce6f0;border-radius:7px;padding:11px 12px"></select></div><button class="secondary" onclick="compareDocuments()">Compare selected documents</button></div>
          </div>
          <div id="analysis-result" class="answer" style="margin-top:20px">Choose a document to run validation or compare two revisions.</div>
        </div>
        <div class="card" style="margin-top:20px"><div class="card-head"><h3>Architecture entity inventory</h3><span class="muted">Source location preserved</span></div><div class="table-wrap"><table><thead><tr><th>Type</th><th>Name</th><th>Source</th><th>Review</th></tr></thead><tbody id="entity-table"><tr><td colspan="4" class="muted">Select a document above.</td></tr></tbody></table></div></div>
      </section>
      <section class="page" id="architecture"><div class="card"><div class="card-head"><div><h3>Solution architecture</h3><div class="muted">Private, evidence-first processing flow</div></div><span class="badge">LOCAL ONLY</span></div><div class="arch"><div class="arch-box"><div class="stage-icon">▥</div><strong>HLD documents</strong><span>PDF / approved source</span></div><div class="arch-box"><div class="stage-icon">⚙</div><strong>Ingestion engine</strong><span>Parse, hash, chunk</span></div><div class="arch-box"><div class="stage-icon">⌁</div><strong>Knowledge store</strong><span>SQLite + vector adapter</span></div><div class="arch-box"><div class="stage-icon">✦</div><strong>Grounded answer</strong><span>Citations + review</span></div></div><div class="notice" style="margin-top:25px;padding:15px;border-radius:9px;background:#f5f9ff;border-left:3px solid var(--blue);font-size:12px;line-height:1.6">Governance principle: AI-generated content remains traceable to approved source material and must be reviewed by an authorized engineering specialist before it is used for design approval, release, compliance, or vehicle validation.</div></div></section>
    </main>
  </div>
  <div class="toast" id="toast"></div>
  <script>
    let documents = [];
    const titles = { dashboard:'Architecture overview', ingestion:'Document ingestion', knowledge:'Knowledge base', qa:'Architecture Q&A', analysis:'Validation & comparison', architecture:'Solution architecture' };
    function showPage(id) { document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active',p.id===id)); document.querySelectorAll('.nav-item[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===id)); document.getElementById('page-title').textContent=titles[id]; if(id==='knowledge'||id==='analysis') loadDocuments(); }
    document.querySelectorAll('.nav-item[data-page]').forEach(b=>b.addEventListener('click',()=>showPage(b.dataset.page)));
    function toast(message) { const t=document.getElementById('toast'); t.textContent=message; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),3200); }
    async function loadStatus() { try { const r=await fetch('/api/status'); const d=await r.json(); const ok=r.ok&&d.status==='ready'; document.getElementById('top-status').textContent=ok?'Local services online':'Backend offline'; document.getElementById('side-status').textContent=ok?'FastAPI · SQLite · Private':'Backend unavailable'; } catch(e) { document.getElementById('top-status').textContent='Backend offline'; } }
    async function loadDocuments() { try { const r=await fetch('/api/documents'); documents=await r.json(); renderDocs(documents); const options=documents.map(d=>`<option value="${esc(d.id)}">${esc(d.title)} · ${esc(d.version)}</option>`).join(''); const selector=document.getElementById('qa-document'); if(selector){ const current=selector.value; selector.innerHTML='<option value="">All approved documents</option>'+options; selector.value=current; } ['validate-document','compare-a','compare-b'].forEach(id=>{const el=document.getElementById(id);if(el){const current=el.value;el.innerHTML=options;el.value=current||documents[0]?.id||'';}}); let chunks=0,entities=0; documents.forEach(d=>{chunks+=d.chunks||0;entities+=d.entities||0}); document.getElementById('doc-count').textContent=documents.length; document.getElementById('chunk-count').textContent=chunks; document.getElementById('entity-count').textContent=entities; if(document.getElementById('analysis').classList.contains('active')) loadEntities(); } catch(e) { toast('Could not load document inventory'); } }
    function renderDocs(list) { const body=document.getElementById('doc-table'); if(!list.length){body.innerHTML='<tr><td colspan="5" class="muted">No documents indexed yet.</td></tr>';return} body.innerHTML=list.map(d=>`<tr><td><b>${esc(d.title)}</b></td><td>${esc(d.version)}</td><td><span class="badge">${esc(d.status)}</span></td><td>${d.chunks||0}</td><td>${d.entities||0}</td></tr>`).join(''); }
    function filterDocs() { const q=document.getElementById('doc-filter').value.toLowerCase(); renderDocs(documents.filter(d=>(d.title+' '+d.version).toLowerCase().includes(q))); }
    async function uploadDocument() { const file=document.getElementById('file').files[0]; if(!file){toast('Choose a PDF first');return} const btn=document.getElementById('upload-btn'); btn.disabled=true; btn.textContent='Indexing document...'; const form=new FormData(); form.append('file',file); form.append('title',document.getElementById('title').value); form.append('version_label',document.getElementById('version').value); form.append('project',document.getElementById('project').value); form.append('uploaded_by',document.getElementById('uploader').value); try { const r=await fetch('/api/upload',{method:'POST',body:form}); const d=await r.json(); const box=document.getElementById('upload-result'); box.style.display='block'; box.textContent=JSON.stringify(d,null,2); if(r.ok){toast('Document indexed successfully'); document.getElementById('activity-text').textContent='HLD document indexed'; await loadDocuments()} else toast(d.detail||'Upload failed'); } catch(e){toast('Upload failed: backend unavailable')} finally {btn.disabled=false;btn.textContent='Upload and index document'} }
    async function askQuestion() { const q=document.getElementById('question').value.trim(); if(!q){toast('Enter a question first');return} const answer=document.getElementById('answer'); answer.textContent='Retrieving approved evidence...'; document.getElementById('sources').innerHTML='<div class="muted">Searching source chunks...</div>'; try { const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,document_id:document.getElementById('qa-document').value||null})}); const d=await r.json(); answer.textContent=d.answer||d.detail||'No answer returned.'; document.getElementById('sources').innerHTML=(d.sources||[]).map(s=>`<div class="source"><div class="source-title">${esc(s.document)} · ${esc(s.version)} · p.${s.page} · §${esc(s.section)}</div><p>${esc(s.snippet)}</p></div>`).join('')||'<div class="muted">No supporting sources found.</div>'; toast(d.citations&&d.citations.length?'Cited answer ready':'No evidence found'); } catch(e){answer.textContent='The backend is unavailable.';toast('Question failed')} }
    async function loadEntities(){const id=document.getElementById('validate-document')?.value;if(!id)return;try{const r=await fetch('/api/entities/'+encodeURIComponent(id));const list=await r.json();document.getElementById('entity-table').innerHTML=(list||[]).map(e=>`<tr><td>${esc(e.entity_type)}</td><td><b>${esc(e.name)}</b></td><td>p.${e.source_page} · §${esc(e.section)}</td><td><span class="badge">${esc(e.review_status)}</span></td></tr>`).join('')||'<tr><td colspan="4" class="muted">No entities extracted.</td></tr>'}catch(e){toast('Could not load entities')}}
    async function validateDocument(){const id=document.getElementById('validate-document').value;if(!id){toast('Select a document');return}const box=document.getElementById('analysis-result');box.textContent='Running conservative evidence checks...';await loadEntities();try{const r=await fetch('/api/validate/'+encodeURIComponent(id),{method:'POST'});const d=await r.json();box.textContent=d.findings?.length?d.findings.map(f=>`${f.severity}: ${f.message} Evidence: ${f.evidence}`).join('\\n'):'No potential inconsistencies found in the supplied text.';toast('Validation complete')}catch(e){box.textContent='Validation failed.';toast('Validation failed')}}
    async function compareDocuments(){const a=document.getElementById('compare-a').value,b=document.getElementById('compare-b').value;if(!a||!b||a===b){toast('Select two different documents');return}const box=document.getElementById('analysis-result');box.textContent='Comparing extracted inventories...';try{const r=await fetch('/api/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({document_a:a,document_b:b})});const d=await r.json();box.textContent=d.changes?.length?d.changes.map(c=>`${c.change_type.toUpperCase()} ${c.entity_type}: ${c.name} ${c.evidence}`).join('\\n'):'No extracted entity changes found.';toast('Comparison complete')}catch(e){box.textContent='Comparison failed.';toast('Comparison failed')}}
    function esc(v) { return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
    const dz=document.getElementById('dropzone'), fi=document.getElementById('file'); fi.addEventListener('change',()=>{document.getElementById('file-name').textContent=fi.files[0]?.name||'No file selected'}); ['dragenter','dragover'].forEach(e=>dz.addEventListener(e,x=>{x.preventDefault();dz.classList.add('drag')})); ['dragleave','drop'].forEach(e=>dz.addEventListener(e,x=>{x.preventDefault();dz.classList.remove('drag')})); dz.addEventListener('drop',e=>{if(e.dataTransfer.files.length){fi.files=e.dataTransfer.files;document.getElementById('file-name').textContent=fi.files[0].name}});
    loadStatus(); loadDocuments();
  </script>
</body>
</html>"""

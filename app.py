import base64
import time
import re
import html as html_mod
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ===================== 0) Secrets =====================

def get_secret(key: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default

GITHUB_TOKEN = get_secret("GITHUB_TOKEN", "")
GITHUB_USER_DEFAULT = get_secret("GITHUB_USER", "")

# ===================== GitHub helpers =====================

def github_headers(token: str):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["X-GitHub-Api-Version"] = "2022-11-28"
    return headers

def ensure_repo_exists(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = requests.get(f"{api_base}/repos/{owner}/{repo}", headers=headers)
    if r.status_code == 200:
        return False
    if r.status_code != 404:
        raise RuntimeError(f"Error checking repo: {r.status_code} {r.text}")

    payload = {
        "name": repo,
        "auto_init": True,
        "private": False,
        "description": "Branded searchable table (auto-created by Streamlit app).",
    }
    r = requests.post(f"{api_base}/user/repos", headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error creating repo: {r.status_code} {r.text}")
    return True

def ensure_pages_enabled(owner: str, repo: str, token: str, branch: str = "main") -> None:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = requests.get(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers)
    if r.status_code == 200:
        return
    if r.status_code not in (404, 403):
        raise RuntimeError(f"Error checking GitHub Pages: {r.status_code} {r.text}")
    if r.status_code == 403:
        return

    payload = {"source": {"branch": branch, "path": "/"}}
    r = requests.post(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, json=payload)
    if r.status_code not in (201, 202):
        raise RuntimeError(f"Error enabling GitHub Pages: {r.status_code} {r.text}")

def upload_file_to_github(
    owner: str,
    repo: str,
    token: str,
    path: str,
    content: str,
    message: str,
    branch: str = "main",
) -> None:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    get_url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": branch}
    r = requests.get(get_url, headers=headers, params=params)
    sha = None
    if r.status_code == 200:
        sha = r.json().get("sha")
    elif r.status_code not in (404,):
        raise RuntimeError(f"Error checking file: {r.status_code} {r.text}")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha

    r = requests.put(get_url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error uploading file: {r.status_code} {r.text}")

def trigger_pages_build(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.post(f"{api_base}/repos/{owner}/{repo}/pages/builds", headers=headers)
    return r.status_code in (201, 202)

# --- Availability check helpers ---

def check_repo_exists(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.get(f"{api_base}/repos/{owner}/{repo}", headers=headers)
    if r.status_code == 200:
        return True
    if r.status_code == 404:
        return False
    raise RuntimeError(f"Error checking repo: {r.status_code} {r.text}")

def check_file_exists(owner: str, repo: str, token: str, path: str, branch: str = "main") -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.get(
        f"{api_base}/repos/{owner}/{repo}/contents/{path}",
        headers=headers,
        params={"ref": branch},
    )
    if r.status_code == 200:
        return True
    if r.status_code == 404:
        return False
    raise RuntimeError(f"Error checking file: {r.status_code} {r.text}")

def find_next_widget_filename(owner: str, repo: str, token: str, branch: str = "main") -> str:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.get(
        f"{api_base}/repos/{owner}/{repo}/contents",
        headers=headers,
        params={"ref": branch},
    )
    if r.status_code != 200:
        return "t1.html"

    max_n = 0
    try:
        for item in r.json():
            if item.get("type") == "file":
                name = item.get("name", "")
                m = re.fullmatch(r"t(\d+)\.html", name)
                if m:
                    max_n = max(max_n, int(m.group(1)))
    except Exception:
        return "t1.html"

    return f"t{max_n + 1}.html"

# ===================== Brand metadata =====================

def get_brand_meta(brand: str) -> dict:
    default_logo = "https://i.postimg.cc/x1nG117r/AN-final2-logo.png"
    brand_clean = (brand or "").strip() or "Action Network"

    meta = {
        "name": brand_clean,
        "logo_url": default_logo,
        "logo_alt": f"{brand_clean} logo",
        "brand_class": "brand-actionnetwork",
    }

    if brand_clean == "Action Network":
        meta["brand_class"] = "brand-actionnetwork"
        meta["logo_url"] = "https://i.postimg.cc/x1nG117r/AN-final2-logo.png"
        meta["logo_alt"] = "Action Network logo"
    elif brand_clean == "VegasInsider":
        meta["brand_class"] = "brand-vegasinsider"
        meta["logo_url"] = "https://i.postimg.cc/kGVJyXc1/VI-logo-final.png"
        meta["logo_alt"] = "VegasInsider logo"
    elif brand_clean == "Canada Sports Betting":
        meta["brand_class"] = "brand-canadasb"
        meta["logo_url"] = "https://i.postimg.cc/ZKbrbPCJ/CSB-FN.png"
        meta["logo_alt"] = "Canada Sports Betting logo"
    elif brand_clean == "RotoGrinders":
        meta["brand_class"] = "brand-rotogrinders"
        meta["logo_url"] = "https://i.postimg.cc/PrcJnQtK/RG-logo-Fn.png"
        meta["logo_alt"] = "RotoGrinders logo"

    return meta

# ===================== HTML Template =====================

HTML_TEMPLATE_TABLE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>[[TITLE]]</title>
</head>
<body style="margin:0;">

<section class="vi-table-embed [[BRAND_CLASS]] [[FOOTER_ALIGN_CLASS]] [[CELL_ALIGN_CLASS]]" style="width:100%;max-width:100%;margin:0;
         font:14px/1.35 Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         color:#181a1f;background:#ffffff;border:1px solid #DCEFE6;border-radius:12px;
         box-shadow:0 1px 2px rgba(0,0,0,.04),0 6px 16px rgba(0,0,0,.09);">

  <style>
    .vi-table-embed, .vi-table-embed * { box-sizing:border-box; font-family:inherit; }

    .vi-table-embed{
      --brand-50:#F6FFF9; 
      --brand-100:#DCF2EB;
      --brand-300:#BCE5D6;
      --brand-500:#56C257; 
      --brand-600:#3FA94B; 
      --brand-700:#2E8538; 
      --brand-900:#1F5D28;

      --header-bg:var(--brand-500);
      --stripe:var(--brand-100);
      --hover:var(--brand-300);
      --scroll-thumb:var(--brand-500);
      --footer-border:color-mix(in oklab,var(--brand-500) 35%, transparent);

      --cell-align:center;
    }
    .vi-table-embed.align-left { --cell-align:left; }
    .vi-table-embed.align-center { --cell-align:center; }
    .vi-table-embed.align-right { --cell-align:right; }

    .vi-table-embed.brand-vegasinsider{
      --brand-50:#FFF7DC;
      --brand-100:#FFE8AA;
      --brand-300:#FFE8AA;
      --brand-500:#F2C23A;
      --brand-600:#D9A72A;
      --brand-700:#B9851A;
      --brand-900:#111111;
      --header-bg:var(--brand-500);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
      --footer-border:color-mix(in oklab,var(--brand-500) 40%, transparent);
    }

    .vi-table-embed.brand-canadasb{
      --brand-50:#FEF2F2;
      --brand-100:#FEE2E2;
      --brand-300:#FECACA;
      --brand-500:#EF4444;
      --brand-600:#DC2626;
      --brand-700:#B91C1C;
      --brand-900:#7F1D1D;
      --header-bg:var(--brand-600);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
      --footer-border:color-mix(in oklab,var(--brand-600) 40%, transparent);
    }

    .vi-table-embed.brand-rotogrinders{
      --brand-50:#E8F1FF;
      --brand-100:#D3E3FF;
      --brand-300:#9ABCF9;
      --brand-500:#2F7DF3;
      --brand-600:#0159D1;
      --brand-700:#0141A1;
      --brand-900:#011F54;
      --header-bg:var(--brand-700);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
      --footer-border:color-mix(in oklab,var(--brand-600) 40%, transparent);
    }

    /* Header block */
    .vi-table-embed .vi-table-header{
      padding:10px 16px 8px;
      border-bottom:1px solid var(--brand-100);
      background:linear-gradient(90deg,var(--brand-50),#ffffff);
      display:flex;
      flex-direction:column;
      align-items:flex-start;
      gap:2px;
    }
    .vi-table-embed .vi-table-header.centered{ align-items:center; text-align:center; }
    .vi-table-embed .vi-table-header .title{
      margin:0; font-size:clamp(18px,2.3vw,22px); font-weight:750; color:#111827; display:block;
    }
    .vi-table-embed .vi-table-header .title.branded{ color:var(--brand-600); }
    .vi-table-embed .vi-table-header .subtitle{ margin:0; font-size:13px; color:#6b7280; display:block; }

    /* Table block */
    #bt-block, #bt-block * { box-sizing:border-box; }
    #bt-block{
      --bg:#ffffff; --text:#1f2937;
      --gutter: 14px;
      --table-max-h: 720px;
      --vbar-w: 6px; --vbar-w-hover: 8px;
      padding: 10px var(--gutter);
      padding-top: 10px;
    }

    #bt-block .dw-controls{
      display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center;
      gap:12px; margin:4px 0 10px 0;
    }
    #bt-block .left{display:flex; gap:8px; align-items:center; flex-wrap:wrap; justify-content:flex-start}
    #bt-block .right{display:flex; gap:8px; align-items:center; flex-wrap:wrap; justify-content:flex-end}

    #bt-block .dw-field{position:relative}
    #bt-block .dw-input,#bt-block .dw-select,#bt-block .dw-btn{
      font:14px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; border-radius:10px; padding:8px 10px; transition:.15s ease;
    }
    #bt-block .dw-input,#bt-block .dw-select{
      background:#fff;
      border:1px solid var(--brand-700);
      color:var(--text); box-shadow:inset 0 1px 2px rgba(16,24,40,.04);
    }
    #bt-block .dw-input{width:min(320px,100%); padding-right:36px}
    #bt-block .dw-input::placeholder{color:#9AA4B2}
    #bt-block .dw-input:focus,#bt-block .dw-select:focus{
      outline:none; border-color:var(--brand-500);
      box-shadow:0 0 0 3px color-mix(in oklab,var(--brand-500) 25%,transparent); background:#fff;
    }
    #bt-block .dw-select{ appearance:none; -webkit-appearance:none; -moz-appearance:none; padding-right:26px; background:#fff; background-image:none; }

    #bt-block .dw-btn{
      background:var(--brand-500); color:#fff; border:1px solid var(--brand-500); padding-inline:12px; cursor:pointer
    }
    #bt-block .dw-btn:hover{background:var(--brand-600); border-color:var(--brand-600)}
    #bt-block .dw-btn:active{transform:translateY(1px)}
    #bt-block .dw-btn[disabled]{background:#fafafa; border-color:#d1d5db; color:#6b7280; opacity:1; cursor:not-allowed; transform:none}

    /* Clear button */
    #bt-block .dw-clear{
      position:absolute; right:10px; top:50%; translate:0 -50%; width:22px; height:22px; border-radius:9999px; border:0;
      background:transparent; color:var(--brand-700); cursor:pointer; display:none; align-items:center; justify-content:center;
    }
    #bt-block .dw-field.has-value .dw-clear{display:flex}
    #bt-block .dw-clear:hover{background:var(--brand-100)}

    /* Card & table */
    #bt-block .dw-card { background: var(--bg); border: 0; box-shadow: none; overflow: hidden; margin: 0; width: 100%; }
    #bt-block .dw-scroll { overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; }
    #bt-block .dw-scroll.no-scroll { overflow-x: hidden !important; }

    #bt-block table.dw-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font: 14px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      color: var(--text);
      font-variant-numeric: tabular-nums;
      background: transparent;
      min-width: 600px;
      table-layout: auto;
    }

    /* Header row */
    #bt-block thead th{
      background:var(--header-bg); color:#ffffff; font-weight:700; vertical-align:middle; border:0;
      padding:12px 14px; white-space:nowrap;
      transition:background-color .15s, color .15s, box-shadow .15s, transform .05s;
    }
    #bt-block thead th.sortable{cursor:pointer; user-select:none}
    #bt-block thead th.sortable::after{content:"↕"; font-size:12px; opacity:.75; margin-left:8px; color:#ffffff}
    #bt-block thead th.sortable[data-sort="asc"]::after{content:"▲"}
    #bt-block thead th.sortable[data-sort="desc"]::after{content:"▼"}
    #bt-block thead th.sortable:hover,#bt-block thead th.sortable:focus-visible{background:var(--brand-600); color:#fff; box-shadow:inset 0 -3px 0 var(--brand-100)}
    #bt-block .dw-scroll.scrolled thead th{box-shadow:0 6px 10px -6px rgba(0,0,0,.25)}
    #bt-block thead th.is-sorted{background:var(--brand-700); color:#fff; box-shadow:inset 0 -3px 0 var(--brand-100)}

    /* Alignment (applies to both th + td) */
    #bt-block thead th,
    #bt-block tbody td {
      padding: 12px 10px;
      overflow: hidden;
      text-align: var(--cell-align, center);
    }
    #bt-block thead th { white-space: nowrap; }

    /* Body rows zebra (injected) */
    [[STRIPE_CSS]]

    /* Hover should win over stripes */
    #bt-block tbody tr:hover td{ background:var(--hover) !important; }
    #bt-block tbody tr:hover{
      box-shadow:inset 3px 0 0 var(--brand-500);
      transform:translateY(-1px);
      transition:background-color .12s ease, box-shadow .12s ease, transform .08s ease;
    }

    #bt-block thead th{position:sticky; top:0; z-index:5}
    #bt-block .dw-scroll{
      max-height:var(--table-max-h,360px); overflow-y:auto;
      -ms-overflow-style:auto; scrollbar-width:thin; scrollbar-color:var(--scroll-thumb) transparent
    }
    #bt-block .dw-scroll::-webkit-scrollbar:horizontal{height:0; display:none}
    #bt-block .dw-scroll::-webkit-scrollbar:vertical{width:var(--vbar-w)}
    #bt-block .dw-scroll:hover::-webkit-scrollbar:vertical{width:var(--vbar-w-hover)}
    #bt-block .dw-scroll::-webkit-scrollbar-thumb{
      background:var(--scroll-thumb); border-radius:9999px; border:2px solid transparent; background-clip:content-box;
    }
    #bt-block tr.dw-empty td{
      text-align:center; color:#6b7280; font-style:italic; padding:18px 14px;
      background:linear-gradient(0deg,#fff,var(--brand-50)) !important;
    }

    /* Footer */
    .vi-table-embed .vi-footer {
      display:block;
      padding:10px 14px 8px;
      border-top:1px solid var(--footer-border);
      background:linear-gradient(90deg,var(--brand-50),#ffffff);
    }
    .vi-table-embed .footer-inner{
      display:flex;
      justify-content:flex-end;
      align-items:center;
      gap:12px;
    }
    .vi-table-embed.footer-center .footer-inner{ justify-content:center; }
    .vi-table-embed.footer-left .footer-inner{ justify-content:flex-start; }
    .vi-table-embed .vi-footer img{ height: 38px; width:auto; display:inline-block; }

    /* Brand-specific logo recolor */
    .vi-table-embed.brand-actionnetwork .vi-footer img{
      filter: brightness(0) saturate(100%) invert(62%) sepia(23%) saturate(1250%) hue-rotate(78deg) brightness(96%) contrast(92%);
    }
    .vi-table-embed.brand-vegasinsider .vi-footer img{
      filter: brightness(0) saturate(100%) invert(72%) sepia(63%) saturate(652%) hue-rotate(6deg) brightness(95%) contrast(101%);
    }
    .vi-table-embed.brand-canadasb .vi-footer img{
      filter: brightness(0) saturate(100%) invert(32%) sepia(85%) saturate(2386%) hue-rotate(347deg) brightness(96%) contrast(104%);
    }
    .vi-table-embed.brand-rotogrinders .vi-footer img{
      filter: brightness(0) saturate(100%) invert(23%) sepia(95%) saturate(1704%) hue-rotate(203deg) brightness(93%) contrast(96%);
    }
    .vi-table-embed.brand-vegasinsider .vi-footer img{ height:32px; }
    .vi-table-embed.brand-rotogrinders .vi-footer img{ height:32px; }

    .vi-hide{ display:none !important; }
  </style>

  <!-- Header (optional) -->
  <div class="vi-table-header [[HEADER_ALIGN_CLASS]] [[HEADER_VIS_CLASS]]">
    <span class="title [[TITLE_CLASS]]">[[TITLE]]</span>
    <span class="subtitle">[[SUBTITLE]]</span>
  </div>

  <!-- Table block -->
  <div id="bt-block" data-dw="table">
    <div class="dw-controls [[CONTROLS_VIS_CLASS]]">
      <div class="left">
        <div class="dw-field [[SEARCH_VIS_CLASS]]">
          <input type="search" class="dw-input" placeholder="Search table…" aria-label="Search table">
          <button type="button" class="dw-clear" aria-label="Clear search">×</button>
        </div>
      </div>

      <div class="right [[PAGER_VIS_CLASS]]">
        <label class="dw-status" for="bt-size" style="margin-right:4px;">Rows/page</label>
        <select id="bt-size" class="dw-select">
          <option value="10" selected>10</option>
          <option value="15">15</option>
          <option value="20">20</option>
          <option value="0">All</option>
        </select>
        <button class="dw-btn" data-page="prev" aria-label="Previous page">‹</button>
        <button class="dw-btn" data-page="next" aria-label="Next page">›</button>
      </div>
    </div>

    <div class="dw-card">
      <div class="dw-scroll">
        <table class="dw-table">
          <thead>
            <tr>
              [[TABLE_HEAD]]
            </tr>
          </thead>
          <tbody>
            [[TABLE_ROWS]]
            <tr class="dw-empty" style="display:none;"><td colspan="[[COLSPAN]]">No matches found.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="dw-page-status [[PAGE_STATUS_VIS_CLASS]]" style="padding:8px 2px 0; color:#6b7280; font:12px/1.2 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
      <span id="dw-page-status-text"></span>
    </div>
  </div>

  <!-- Footer (optional) -->
  <div class="vi-footer [[FOOTER_VIS_CLASS]]" role="contentinfo">
    <div class="footer-inner">
      <img src="[[BRAND_LOGO_URL]]" alt="[[BRAND_LOGO_ALT]]" width="140" height="auto" loading="lazy" decoding="async" />
    </div>
  </div>

  <script>
  (function(){
    const root = document.getElementById('bt-block');
    if (!root || root.dataset.dwInit === '1') return;
    root.dataset.dwInit='1';

    const table = root.querySelector('table.dw-table');
    const tb = table ? table.tBodies[0] : null;
    const scroller = root.querySelector('.dw-scroll');
    const controls = root.querySelector('.dw-controls');
    if(!table || !tb || !scroller || !controls) return;

    const controlsHidden = controls.classList.contains('vi-hide');

    const searchFieldWrap = controls.querySelector('.dw-field');
    const searchInput = controls.querySelector('.dw-input');
    const clearBtn = controls.querySelector('.dw-clear');

    const pagerWrap = controls.querySelector('.right');
    const sizeSel = controls.querySelector('#bt-size');
    const prevBtn = controls.querySelector('[data-page="prev"]');
    const nextBtn = controls.querySelector('[data-page="next"]');

    const emptyRow = tb.querySelector('.dw-empty');
    const pageStatus = document.getElementById('dw-page-status-text');

    const hasSearch = !controlsHidden
      && !!searchFieldWrap && !searchFieldWrap.classList.contains('vi-hide')
      && !!searchInput && !!clearBtn;

    const hasPager = !controlsHidden
      && !!pagerWrap && !pagerWrap.classList.contains('vi-hide')
      && !!sizeSel && !!prevBtn && !!nextBtn;

    if (table.tHead && table.tHead.rows[0].cells.length <= 4) {
      scroller.classList.add('no-scroll');
    }

    Array.from(tb.rows).forEach((r,i)=>{ if(!r.classList.contains('dw-empty')) r.dataset.idx=i; });

    // ✅ If pager is OFF, show ALL rows by default
    let pageSize = hasPager ? (parseInt(sizeSel.value,10) || 10) : 0; // 0 = All
    let page = 1;
    let filter = '';

    const onScrollShadow = ()=> scroller.classList.toggle('scrolled', scroller.scrollTop > 0);
    scroller.addEventListener('scroll', onScrollShadow); onScrollShadow();

    // Sorting always on
    const heads = Array.from(table.tHead.rows[0].cells);
    heads.forEach((th,i)=>{
      th.classList.add('sortable'); th.setAttribute('aria-sort','none'); th.dataset.sort='none'; th.tabIndex=0;
      const type = th.dataset.type || 'text';
      const go = ()=> sortBy(i,type,th);
      th.addEventListener('click',go);
      th.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); go(); } });
    });

    function textOf(tr,i){ return (tr.children[i].innerText||'').trim(); }

    function sortBy(colIdx, type, th){
      const rows = Array.from(tb.rows).filter(r=>!r.classList.contains('dw-empty'));
      const current = th.dataset.sort || 'none';
      const next = current==='none' ? 'asc' : current==='asc' ? 'desc' : 'none';

      heads.forEach(h=>{
        h.dataset.sort='none';
        h.setAttribute('aria-sort','none');
        h.classList.remove('is-sorted');
      });

      if(next === 'none'){
        rows.sort((a,b)=>(+a.dataset.idx)-(+b.dataset.idx));
        rows.forEach(r=>tb.insertBefore(r, emptyRow));
        renderPage();
        return;
      }

      th.dataset.sort = next;
      th.setAttribute('aria-sort', next==='asc'?'ascending':'descending');

      const mul = next==='asc'?1:-1;
      rows.sort((a,b)=>{
        let v1=textOf(a,colIdx), v2=textOf(b,colIdx);
        if((type||'text')==='num'){
          v1=parseFloat(v1.replace(/[^0-9.\-]/g,'')); if(isNaN(v1)) v1=-Infinity;
          v2=parseFloat(v2.replace(/[^0-9.\-]/g,'')); if(isNaN(v2)) v2=-Infinity;
        }else{
          v1=(v1+'').toLowerCase();
          v2=(v2+'').toLowerCase();
        }
        if(v1>v2) return 1*mul;
        if(v1<v2) return -1*mul;
        return 0;
      });
      rows.forEach(r=>tb.insertBefore(r, emptyRow));
      th.classList.add('is-sorted');
      renderPage();
    }

    function matchesFilter(tr){
      if(tr.classList.contains('dw-empty')) return false;
      if(!filter) return true;
      return tr.innerText.toLowerCase().includes(filter);
    }

    function setPageStatus(totalVisible, pages){
      if(!pageStatus) return;
      if(totalVisible === 0){ pageStatus.textContent = ""; return; }
      if(!hasPager || pageSize === 0){ pageStatus.textContent = ""; return; }
      pageStatus.textContent = "Page " + page + " of " + pages;
    }

    function renderPage(){
      const ordered = Array.from(tb.rows).filter(r=>!r.classList.contains('dw-empty'));
      const visible = ordered.filter(matchesFilter);
      const total = visible.length;

      ordered.forEach(r=>{ r.style.display='none'; });
      let shown = [];

      if(total===0){
        if(emptyRow){
          emptyRow.style.display='table-row';
          emptyRow.firstElementChild.colSpan = heads.length;
        }
        if(hasPager){ prevBtn.disabled = nextBtn.disabled = true; }
        setPageStatus(0, 0);
      }else{
        if(emptyRow) emptyRow.style.display='none';

        if(!hasPager || pageSize===0){
          shown = visible;
          if(hasPager){ prevBtn.disabled = nextBtn.disabled = true; }
          setPageStatus(total, 1);
        }else{
          const pages = Math.max(1, Math.ceil(total / pageSize));
          page = Math.min(Math.max(1, page), pages);
          const start = (page-1)*pageSize;
          const end = start + pageSize;
          shown = visible.slice(start,end);
          prevBtn.disabled = page<=1;
          nextBtn.disabled = page>=pages;
          setPageStatus(total, pages);
        }
      }

      shown.forEach(r=>{ r.style.display='table-row'; });
    }

    // Search wiring (only if visible)
    if(hasSearch){
      const syncClearBtn = ()=> searchFieldWrap.classList.toggle('has-value', !!searchInput.value);
      let t=null;
      searchInput.addEventListener('input', e=>{
        syncClearBtn();
        clearTimeout(t);
        t=setTimeout(()=>{
          filter=(e.target.value||'').toLowerCase().trim();
          page=1;
          renderPage();
        },120);
      });
      clearBtn.addEventListener('click', ()=>{
        searchInput.value='';
        syncClearBtn();
        filter='';
        page=1;
        renderPage();
        searchInput.focus();
      });
      syncClearBtn();
    }

    // Pager wiring (only if visible)
    if(hasPager){
      sizeSel.addEventListener('change', e=>{
        pageSize = parseInt(e.target.value,10) || 0;
        page=1;
        renderPage();
      });
      prevBtn.addEventListener('click', ()=>{ page--; renderPage(); });
      nextBtn.addEventListener('click', ()=>{ page++; renderPage(); });
    }

    renderPage();
  })();
  </script>

</section>
</body>
</html>
"""

# ===================== Generator =====================

def guess_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "num"
    sample = series.dropna().astype(str).head(20)
    if sample.empty:
        return "text"
    numeric_like = 0
    for v in sample:
        cleaned = re.sub(r"[^0-9.\-]", "", v)
        try:
            float(cleaned)
            numeric_like += 1
        except ValueError:
            continue
    return "num" if numeric_like >= max(3, len(sample) // 2) else "text"

def generate_table_html_from_df(
    df: pd.DataFrame,
    title: str,
    subtitle: str,
    brand_logo_url: str,
    brand_logo_alt: str,
    brand_class: str,
    striped: bool = True,
    center_titles: bool = False,
    branded_title_color: bool = True,
    show_search: bool = True,
    show_pager: bool = True,
    show_page_numbers: bool = True,
    show_header: bool = True,
    show_footer: bool = True,
    footer_logo_align: str = "Right",   # Right / Center / Left
    cell_align: str = "Center",         # Center / Left / Right
) -> str:
    df = df.copy()

    head_cells = []
    for col in df.columns:
        col_type = guess_column_type(df[col])
        safe_label = html_mod.escape(str(col))
        head_cells.append(f'<th scope="col" data-type="{col_type}">{safe_label}</th>')
    table_head_html = "\n              ".join(head_cells)

    row_html_snippets = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = "" if pd.isna(row[col]) else str(row[col])
            cells.append(f"<td>{html_mod.escape(val)}</td>")
        row_html_snippets.append("            <tr>" + "".join(cells) + "</tr>")

    table_rows_html = "\n".join(row_html_snippets)
    colspan = str(len(df.columns))

    stripe_css = (
        """
    #bt-block tbody tr:not(.dw-empty):nth-child(odd) td{background:var(--stripe);}
    #bt-block tbody tr:not(.dw-empty):nth-child(even) td{background:#ffffff;}
"""
        if striped
        else """
    #bt-block tbody tr:not(.dw-empty) td{background:#ffffff;}
"""
    )

    header_class = "centered" if center_titles else ""
    title_class = "branded" if branded_title_color else ""

    header_vis = "" if show_header else "vi-hide"
    footer_vis = "" if show_footer else "vi-hide"

    controls_vis = "" if (show_search or show_pager) else "vi-hide"
    search_vis = "" if show_search else "vi-hide"
    pager_vis = "" if show_pager else "vi-hide"
    page_status_vis = "" if (show_page_numbers and show_pager) else "vi-hide"

    footer_logo_align = (footer_logo_align or "Right").strip().lower()
    if footer_logo_align == "center":
        footer_align_class = "footer-center"
    elif footer_logo_align == "left":
        footer_align_class = "footer-left"
    else:
        footer_align_class = ""

    cell_align = (cell_align or "Center").strip().lower()
    if cell_align == "left":
        cell_align_class = "align-left"
    elif cell_align == "right":
        cell_align_class = "align-right"
    else:
        cell_align_class = "align-center"

    html = (
        HTML_TEMPLATE_TABLE
        .replace("[[TABLE_HEAD]]", table_head_html)
        .replace("[[TABLE_ROWS]]", table_rows_html)
        .replace("[[COLSPAN]]", colspan)
        .replace("[[TITLE]]", html_mod.escape(title))
        .replace("[[SUBTITLE]]", html_mod.escape(subtitle or ""))
        .replace("[[BRAND_LOGO_URL]]", brand_logo_url)
        .replace("[[BRAND_LOGO_ALT]]", html_mod.escape(brand_logo_alt))
        .replace("[[BRAND_CLASS]]", brand_class or "")
        .replace("[[STRIPE_CSS]]", stripe_css)
        .replace("[[HEADER_ALIGN_CLASS]]", header_class)
        .replace("[[TITLE_CLASS]]", title_class)
        .replace("[[HEADER_VIS_CLASS]]", header_vis)
        .replace("[[FOOTER_VIS_CLASS]]", footer_vis)
        .replace("[[CONTROLS_VIS_CLASS]]", controls_vis)
        .replace("[[SEARCH_VIS_CLASS]]", search_vis)
        .replace("[[PAGER_VIS_CLASS]]", pager_vis)
        .replace("[[PAGE_STATUS_VIS_CLASS]]", page_status_vis)
        .replace("[[FOOTER_ALIGN_CLASS]]", footer_align_class)
        .replace("[[CELL_ALIGN_CLASS]]", cell_align_class)
    )
    return html

# ===================== UI helpers =====================

def stable_config_hash(cfg: dict) -> str:
    keys = sorted(cfg.keys())
    return "|".join([f"{k}={repr(cfg.get(k))}" for k in keys])

def simulate_progress(label: str, total_sleep: float = 0.35):
    ph = st.empty()
    ph.caption(label)
    prog = st.progress(0)
    steps = [15, 35, 60, 80, 100]
    per = total_sleep / len(steps) if steps else 0.05
    for s in steps:
        time.sleep(per)
        prog.progress(s)
    time.sleep(0.05)
    ph.empty()
    prog.empty()

def draft_config_from_state() -> dict:
    return {
        "brand": st.session_state.get("brand_table", "Action Network"),
        "title": st.session_state.get("bt_widget_title", "Table 1"),
        "subtitle": st.session_state.get("bt_widget_subtitle", "Subheading"),
        "striped": st.session_state.get("bt_striped_rows", True),
        "show_header": st.session_state.get("bt_show_header", True),
        "center_titles": st.session_state.get("bt_center_titles", False),
        "branded_title_color": st.session_state.get("bt_branded_title_color", True),
        "show_footer": st.session_state.get("bt_show_footer", True),
        "footer_logo_align": st.session_state.get("bt_footer_logo_align", "Right"),
        "cell_align": st.session_state.get("bt_cell_align", "Center"),
        "show_search": st.session_state.get("bt_show_search", True),
        "show_pager": st.session_state.get("bt_show_pager", True),
        "show_page_numbers": st.session_state.get("bt_show_page_numbers", True),
    }

def html_from_config(df: pd.DataFrame, cfg: dict) -> str:
    meta = get_brand_meta(cfg["brand"])
    return generate_table_html_from_df(
        df=df,
        title=cfg["title"],
        subtitle=cfg["subtitle"],
        brand_logo_url=meta["logo_url"],
        brand_logo_alt=meta["logo_alt"],
        brand_class=meta["brand_class"],
        striped=cfg["striped"],
        center_titles=cfg["center_titles"],
        branded_title_color=cfg["branded_title_color"],
        show_search=cfg["show_search"],
        show_pager=cfg["show_pager"],
        show_page_numbers=cfg["show_page_numbers"],
        show_header=cfg["show_header"],
        show_footer=cfg["show_footer"],
        footer_logo_align=cfg["footer_logo_align"],
        cell_align=cfg["cell_align"],
    )

def ensure_initial_confirm(df: pd.DataFrame):
    if "bt_confirmed_cfg" not in st.session_state:
        cfg = draft_config_from_state()
        st.session_state["bt_confirmed_cfg"] = cfg
        st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)
        st.session_state["bt_confirmed_html_preview"] = html_from_config(df, cfg)

        st.session_state.setdefault("bt_html_code", "")
        st.session_state.setdefault("bt_html_generated", False)
        st.session_state.setdefault("bt_html_hash", "")
        st.session_state.setdefault("bt_last_published_url", "")
        st.session_state.setdefault("bt_iframe_code", "")
        st.session_state.setdefault("bt_widget_file_name", "branded_table.html")

def confirm_table(df: pd.DataFrame):
    cfg = draft_config_from_state()
    st.session_state["bt_confirmed_cfg"] = cfg
    st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)
    st.session_state["bt_confirmed_html_preview"] = html_from_config(df, cfg)

def generate_html_code_from_confirmed(df: pd.DataFrame):
    cfg = st.session_state.get("bt_confirmed_cfg")
    if not cfg:
        return
    html = html_from_config(df, cfg)
    st.session_state["bt_confirmed_html_preview"] = html
    st.session_state["bt_html_code"] = html
    st.session_state["bt_html_generated"] = True
    st.session_state["bt_html_hash"] = stable_config_hash(cfg)

def compute_pages_url(user: str, repo: str, filename: str) -> str:
    user = (user or "").strip()
    repo = (repo or "").strip()
    filename = (filename or "").lstrip("/").strip() or "branded_table.html"
    return f"https://{user}.github.io/{repo}/{filename}"

def build_iframe_snippet(url: str, height: int = 800) -> str:
    url = (url or "").strip()
    h = int(height) if height else 800
    return f"""<iframe
  src="{html_mod.escape(url, quote=True)}"
  width="100%"
  height="{h}"
  style="border:0; border-radius:12px; overflow:hidden;"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
></iframe>"""

# ===================== Streamlit App =====================

st.set_page_config(page_title="Branded Table Generator", layout="wide")
st.markdown(
    """
    <style>
      [data-testid="stHeaderAnchor"] { display:none !important; }
      a.header-anchor { display:none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Branded Table Generator")

brand_options = ["Action Network", "VegasInsider", "Canada Sports Betting", "RotoGrinders"]
default_brand = st.session_state.get("brand_table", "Action Network")
if default_brand not in brand_options:
    default_brand = "Action Network"

st.selectbox(
    "Choose a brand",
    options=brand_options,
    index=brand_options.index(default_brand),
    key="brand_table",
)

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is None:
    st.info("Upload a CSV to start.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    st.stop()

if df.empty:
    st.error("Uploaded CSV has no rows.")
    st.stop()

ensure_initial_confirm(df)

# ===================== Layout: Left (1/4) tabs + Right (3/4) preview =====================

left_col, right_col = st.columns([1, 3], gap="large")

# Always-on preview (CONFIRMED)
with right_col:
    st.markdown("### Preview (confirmed)")
    preview_html = st.session_state.get("bt_confirmed_html_preview", "")
    components.html(preview_html, height=820, scrolling=True)

# Left sidebar tabs: Configure / HTML / Iframe
with left_col:
    tab_config, tab_html, tab_iframe = st.tabs(["Configure", "HTML", "Iframe"])

    # ---------- CONFIGURE TAB ----------
    with tab_config:
        st.markdown("#### Table setup")

        # confirm button (finalize)
        confirm_clicked = st.button(
            "✅ Confirm and save table contents",
            key="bt_confirm_btn",
            use_container_width=True,
        )

        # two small subtabs (keeps it tidy)
        sub_head, sub_content = st.tabs(["Header / Footer", "Content"])

        with sub_head:
            st.text_input(
                "Table title",
                value=st.session_state.get("bt_widget_title", "Table 1"),
                key="bt_widget_title",
            )
            st.text_input(
                "Table subtitle",
                value=st.session_state.get("bt_widget_subtitle", "Subheading"),
                key="bt_widget_subtitle",
            )

            show_header = st.checkbox(
                "Show header box",
                value=st.session_state.get("bt_show_header", True),
                key="bt_show_header",
            )
            st.checkbox(
                "Center title & subtitle",
                value=st.session_state.get("bt_center_titles", False),
                key="bt_center_titles",
                disabled=not show_header,
            )
            st.checkbox(
                "Branded title color",
                value=st.session_state.get("bt_branded_title_color", True),
                key="bt_branded_title_color",
                disabled=not show_header,
            )

            show_footer = st.checkbox(
                "Show footer (logo)",
                value=st.session_state.get("bt_show_footer", True),
                key="bt_show_footer",
            )
            st.selectbox(
                "Footer logo alignment",
                options=["Right", "Center", "Left"],
                index=["Right", "Center", "Left"].index(st.session_state.get("bt_footer_logo_align", "Right")),
                key="bt_footer_logo_align",
                disabled=not show_footer,
            )

        with sub_content:
            st.checkbox(
                "Striped rows",
                value=st.session_state.get("bt_striped_rows", True),
                key="bt_striped_rows",
            )
            st.selectbox(
                "Table content alignment",
                options=["Center", "Left", "Right"],
                index=["Center", "Left", "Right"].index(st.session_state.get("bt_cell_align", "Center")),
                key="bt_cell_align",
            )
            st.checkbox(
                "Show search",
                value=st.session_state.get("bt_show_search", True),
                key="bt_show_search",
            )
            show_pager = st.checkbox(
                "Show pager (rows/page + prev/next)",
                value=st.session_state.get("bt_show_pager", True),
                key="bt_show_pager",
                help="If off, the table will show ALL rows by default.",
            )
            st.checkbox(
                "Show page numbers (Page X of Y)",
                value=st.session_state.get("bt_show_page_numbers", True),
                key="bt_show_page_numbers",
                disabled=not show_pager,
            )

        # status + action
        draft_hash = stable_config_hash(draft_config_from_state())
        confirmed_hash = st.session_state.get("bt_confirmed_hash", "")
        unconfirmed_changes = (draft_hash != confirmed_hash)

        if confirm_clicked:
            simulate_progress("Saving table settings…", total_sleep=0.45)
            confirm_table(df)
            # if HTML exists, mark stale if mismatch
            if st.session_state.get("bt_html_generated", False):
                st.session_state["bt_html_stale"] = (st.session_state.get("bt_html_hash", "") != st.session_state.get("bt_confirmed_hash", ""))
            st.success("Saved. Preview updated (confirmed).")
        else:
            if unconfirmed_changes:
                st.warning("You have unconfirmed changes. Click **Confirm and save** to update the preview.")
            else:
                st.caption("All changes are confirmed.")

    # ---------- HTML TAB ----------
    with tab_html:
        st.markdown("#### HTML generation")

        html_generated = bool(st.session_state.get("bt_html_generated", False))
        html_hash = st.session_state.get("bt_html_hash", "")
        confirmed_hash = st.session_state.get("bt_confirmed_hash", "")
        draft_hash = stable_config_hash(draft_config_from_state())
        unconfirmed_changes = (draft_hash != confirmed_hash)
        confirmed_vs_html_stale = (html_generated and (html_hash != confirmed_hash))

        col_a, col_b = st.columns([1, 1])
        with col_a:
            get_html_clicked = st.button(
                "📄 Get HTML code",
                key="bt_get_html_code",
                use_container_width=True,
            )
        with col_b:
            update_html_clicked = st.button(
                "♻️ Update HTML",
                key="bt_update_html",
                disabled=not html_generated,
                use_container_width=True,
            )

        if unconfirmed_changes:
            st.info("HTML is generated from **confirmed** settings. Confirm changes first, or click **Update HTML** to auto-confirm + regenerate.")
        elif confirmed_vs_html_stale:
            st.warning("HTML is out of date vs confirmed settings. Click **Update HTML**.")
        elif html_generated:
            st.success("HTML is up to date with confirmed settings.")
        else:
            st.caption("Click **Get HTML code** after confirming your table settings.")

        if get_html_clicked:
            if unconfirmed_changes:
                st.warning("Confirm your changes first (or use Update HTML).")
            else:
                simulate_progress("Generating HTML…", total_sleep=0.40)
                generate_html_code_from_confirmed(df)
                st.success("HTML generated from confirmed settings.")

        if update_html_clicked:
            # auto-confirm any draft changes first
            if stable_config_hash(draft_config_from_state()) != st.session_state.get("bt_confirmed_hash", ""):
                simulate_progress("Confirming latest settings…", total_sleep=0.30)
                confirm_table(df)
            simulate_progress("Updating HTML…", total_sleep=0.40)
            generate_html_code_from_confirmed(df)
            st.success("HTML updated from the latest confirmed settings.")

        html_code = st.session_state.get("bt_html_code", "")
        st.text_area(
            "HTML code",
            value=html_code,
            height=420,
            placeholder="Generate HTML to see the code here.",
        )

    # ---------- IFRAME TAB ----------
    with tab_iframe:
        st.markdown("#### Publish + Iframe")

        html_generated = bool(st.session_state.get("bt_html_generated", False))
        html_hash = st.session_state.get("bt_html_hash", "")
        confirmed_hash = st.session_state.get("bt_confirmed_hash", "")
        draft_hash = stable_config_hash(draft_config_from_state())

        unconfirmed_changes = (draft_hash != confirmed_hash)
        html_stale = (html_generated and (html_hash != confirmed_hash))

        if not html_generated:
            st.warning("Generate HTML first (HTML tab).")
        elif unconfirmed_changes or html_stale:
            st.warning("Your HTML is not up to date. Go to HTML tab → **Update HTML**.")

        # GitHub inputs (disabled until HTML generated)
        saved_gh_user = st.session_state.get("bt_gh_user", "")
        saved_gh_repo = st.session_state.get("bt_gh_repo", "branded-table-widget")

        username_options = ["GauthamBC", "ActionNetwork", "MoonWatcher", "SampleUser"]
        if GITHUB_USER_DEFAULT and GITHUB_USER_DEFAULT not in username_options:
            username_options.insert(0, GITHUB_USER_DEFAULT)

        default_idx = username_options.index(saved_gh_user) if saved_gh_user in username_options else 0
        github_username_input = st.selectbox(
            "Username (GitHub username)",
            options=username_options,
            index=default_idx,
            key="bt_gh_user",
            disabled=not html_generated,
        )
        effective_github_user = (github_username_input or "").strip()

        repo_name = st.text_input(
            "Widget hosting repository name",
            value=saved_gh_repo,
            key="bt_gh_repo",
            disabled=not html_generated,
        ).strip()

        base_filename = "branded_table.html"
        st.session_state.setdefault("bt_widget_file_name", base_filename)
        widget_file_name = st.session_state.get("bt_widget_file_name", base_filename)

        st.caption(f"Target file in repo: `{widget_file_name}`")

        can_run_github = bool(GITHUB_TOKEN and effective_github_user and repo_name)
        can_publish = bool(can_run_github and html_generated and (not unconfirmed_changes) and (not html_stale))

        col_check, col_pub = st.columns([1, 1])
        with col_check:
            page_check_clicked = st.button(
                "Page availability check",
                key="bt_page_check",
                disabled=not can_run_github or not html_generated,
                use_container_width=True,
            )
        with col_pub:
            publish_clicked = st.button(
                "Publish HTML",
                key="bt_publish_html",
                disabled=not can_publish,
                use_container_width=True,
                help="Disabled until HTML is generated and up-to-date.",
            )

        if not GITHUB_TOKEN:
            st.info("Set `GITHUB_TOKEN` in `.streamlit/secrets.toml` (with `repo` scope) to enable GitHub publishing.")

        # Availability logic
        if page_check_clicked:
            try:
                repo_exists = check_repo_exists(effective_github_user, repo_name, GITHUB_TOKEN)
                file_exists = False
                next_fname = None
                if repo_exists:
                    file_exists = check_file_exists(effective_github_user, repo_name, GITHUB_TOKEN, base_filename)
                    if file_exists:
                        next_fname = find_next_widget_filename(effective_github_user, repo_name, GITHUB_TOKEN)

                st.session_state["bt_availability"] = {
                    "repo_exists": repo_exists,
                    "file_exists": file_exists,
                    "checked_filename": base_filename,
                    "suggested_new_filename": next_fname,
                }
                st.success("Availability check complete.")
            except Exception as e:
                st.error(f"Availability check failed: {e}")

        availability = st.session_state.get("bt_availability")
        if html_generated and can_run_github and availability:
            repo_exists = availability.get("repo_exists", False)
            file_exists = availability.get("file_exists", False)
            checked_filename = availability.get("checked_filename", base_filename)
            suggested_new_filename = availability.get("suggested_new_filename") or "t1.html"

            if not repo_exists:
                st.info("No existing repo found. Publishing will create it.")
                st.session_state["bt_widget_file_name"] = checked_filename
            elif repo_exists and not file_exists:
                st.success(f"Repo exists and `{checked_filename}` is available.")
                st.session_state["bt_widget_file_name"] = checked_filename
            else:
                st.warning(f"`{checked_filename}` already exists.")
                choice = st.radio(
                    "Choose what to do",
                    options=[
                        "Replace existing widget (overwrite file)",
                        f"Create additional widget file in same repo (use {suggested_new_filename})",
                        "Change campaign name instead",
                    ],
                    key="bt_file_conflict_choice",
                    disabled=not html_generated,
                )
                if choice.startswith("Replace"):
                    st.session_state["bt_widget_file_name"] = checked_filename
                elif choice.startswith("Create additional"):
                    st.session_state["bt_widget_file_name"] = suggested_new_filename

        # Publish logic (uses generated HTML only)
        if publish_clicked:
            try:
                html_final = st.session_state.get("bt_html_code", "")
                if not html_final:
                    raise RuntimeError("No generated HTML found. Go to HTML tab and generate it first.")

                ph = st.empty()
                prog = st.progress(0)
                ph.caption("Publishing to GitHub…")
                for pct in (10, 30, 55):
                    time.sleep(0.10)
                    prog.progress(pct)

                ensure_repo_exists(effective_github_user, repo_name, GITHUB_TOKEN)
                prog.progress(70)

                try:
                    ensure_pages_enabled(effective_github_user, repo_name, GITHUB_TOKEN, branch="main")
                except Exception:
                    pass
                prog.progress(85)

                widget_file_name = st.session_state.get("bt_widget_file_name", base_filename)
                upload_file_to_github(
                    effective_github_user,
                    repo_name,
                    GITHUB_TOKEN,
                    widget_file_name,
                    html_final,
                    f"Add/update {widget_file_name} from Branded Table app",
                    branch="main",
                )
                trigger_pages_build(effective_github_user, repo_name, GITHUB_TOKEN)

                prog.progress(100)
                time.sleep(0.12)
                ph.empty()
                prog.empty()

                pages_url = compute_pages_url(effective_github_user, repo_name, widget_file_name)
                st.session_state["bt_last_published_url"] = pages_url
                st.success("Published. GitHub Pages may take a minute to update.")

            except Exception as e:
                st.error(f"GitHub publish failed: {e}")

        st.markdown("---")
        st.markdown("#### Iframe embed")

        pages_url = st.session_state.get("bt_last_published_url", "")
        default_url = ""
        if html_generated and effective_github_user and repo_name:
            default_url = compute_pages_url(
                effective_github_user,
                repo_name,
                st.session_state.get("bt_widget_file_name", base_filename),
            )

        url_to_use = st.text_input(
            "Page URL used for iframe",
            value=pages_url or default_url,
            key="bt_iframe_url",
            disabled=not html_generated,
        )

        iframe_height = st.number_input(
            "Iframe height (px)",
            min_value=300,
            max_value=2000,
            value=int(st.session_state.get("bt_iframe_height", 800)),
            step=50,
            key="bt_iframe_height",
            disabled=not html_generated,
        )

        get_iframe_clicked = st.button(
            "🧩 Get iframe code",
            key="bt_get_iframe",
            disabled=not html_generated or not bool(url_to_use.strip()),
            use_container_width=True,
            help="Disabled until HTML is generated.",
        )

        if get_iframe_clicked:
            simulate_progress("Generating iframe…", total_sleep=0.25)
            st.session_state["bt_iframe_code"] = build_iframe_snippet(url_to_use, height=int(iframe_height))
            st.success("Iframe code generated.")

        iframe_code = st.session_state.get("bt_iframe_code", "")
        st.text_area(
            "Iframe code",
            value=iframe_code,
            height=200,
            placeholder="Generate HTML first, then generate iframe code here.",
        )

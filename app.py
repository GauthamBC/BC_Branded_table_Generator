import base64
import html as html_mod
import re
import time

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# 0) Secrets
# =========================================================


def get_secret(key: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


GITHUB_TOKEN = get_secret("GITHUB_TOKEN", "")
GITHUB_USER_DEFAULT = get_secret("GITHUB_USER", "")

# =========================================================
# GitHub Helpers
# =========================================================


def github_headers(token: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["X-GitHub-Api-Version"] = "2022-11-28"
    return headers


def ensure_repo_exists(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = requests.get(f"{api_base}/repos/{owner}/{repo}", headers=headers, timeout=20)
    if r.status_code == 200:
        return False
    if r.status_code != 404:
        raise RuntimeError(f"Error Checking Repo: {r.status_code} {r.text}")

    payload = {
        "name": repo,
        "auto_init": True,
        "private": False,
        "description": "Branded Searchable Table (Auto-Created By Streamlit App).",
    }
    r = requests.post(f"{api_base}/user/repos", headers=headers, json=payload, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error Creating Repo: {r.status_code} {r.text}")
    return True


def ensure_pages_enabled(owner: str, repo: str, token: str, branch: str = "main") -> None:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = requests.get(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, timeout=20)
    if r.status_code == 200:
        return
    if r.status_code not in (404, 403):
        raise RuntimeError(f"Error Checking GitHub Pages: {r.status_code} {r.text}")
    if r.status_code == 403:
        # No permission / not available for this repo/account plan
        return

    payload = {"source": {"branch": branch, "path": "/"}}
    r = requests.post(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, json=payload, timeout=20)
    if r.status_code not in (201, 202):
        raise RuntimeError(f"Error Enabling GitHub Pages: {r.status_code} {r.text}")


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
    r = requests.get(get_url, headers=headers, params={"ref": branch}, timeout=20)

    sha = None
    if r.status_code == 200:
        sha = r.json().get("sha")
    elif r.status_code != 404:
        raise RuntimeError(f"Error Checking File: {r.status_code} {r.text}")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha

    r = requests.put(get_url, headers=headers, json=payload, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error Uploading File: {r.status_code} {r.text}")


def trigger_pages_build(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.post(f"{api_base}/repos/{owner}/{repo}/pages/builds", headers=headers, timeout=20)
    return r.status_code in (201, 202)


# --- Availability Check Helpers ---


def check_repo_exists(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.get(f"{api_base}/repos/{owner}/{repo}", headers=headers, timeout=20)
    if r.status_code == 200:
        return True
    if r.status_code == 404:
        return False
    raise RuntimeError(f"Error Checking Repo: {r.status_code} {r.text}")


def check_file_exists(owner: str, repo: str, token: str, path: str, branch: str = "main") -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.get(
        f"{api_base}/repos/{owner}/{repo}/contents/{path}",
        headers=headers,
        params={"ref": branch},
        timeout=20,
    )
    if r.status_code == 200:
        return True
    if r.status_code == 404:
        return False
    raise RuntimeError(f"Error Checking File: {r.status_code} {r.text}")


def find_next_widget_filename(owner: str, repo: str, token: str, branch: str = "main") -> str:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = requests.get(
        f"{api_base}/repos/{owner}/{repo}/contents",
        headers=headers,
        params={"ref": branch},
        timeout=20,
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


# =========================================================
# Brand Metadata
# =========================================================


def get_brand_meta(brand: str) -> dict:
    default_logo = "https://i.postimg.cc/x1nG117r/AN-final2-logo.png"
    brand_clean = (brand or "").strip() or "Action Network"

    meta = {
        "name": brand_clean,
        "logo_url": default_logo,
        "logo_alt": f"{brand_clean} Logo",
        "brand_class": "brand-actionnetwork",
    }

    if brand_clean == "Action Network":
        meta["brand_class"] = "brand-actionnetwork"
        meta["logo_url"] = "https://i.postimg.cc/x1nG117r/AN-final2-logo.png"
        meta["logo_alt"] = "Action Network Logo"
    elif brand_clean == "VegasInsider":
        meta["brand_class"] = "brand-vegasinsider"
        meta["logo_url"] = "https://i.postimg.cc/VkynWsGQ/VI-logo-Dark.png"
        meta["logo_alt"] = "VegasInsider Logo"
    elif brand_clean == "Canada Sports Betting":
        meta["brand_class"] = "brand-canadasb"
        meta["logo_url"] = "https://i.postimg.cc/25nqwgcw/csb-text-all-red.png"
        meta["logo_alt"] = "Canada Sports Betting Logo"
    elif brand_clean == "RotoGrinders":
        meta["brand_class"] = "brand-rotogrinders"
        meta["logo_url"] = "https://i.postimg.cc/PrcJnQtK/RG-logo-Fn.png"
        meta["logo_alt"] = "RotoGrinders Logo"

    return meta


# =========================================================
# HTML Template
# - Fixes table rendering by clamping INSIDE a wrapper div
# - Download button opens menu: Top 10 vs Bottom 10 (ONLY)
# - EXPORT removes header/subtitle and controls: image shows ONLY table + logo
# - NO alert() anywhere
# =========================================================

HTML_TEMPLATE_TABLE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>[[TITLE]]</title>

<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
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
      --brand-500-rgb: 86, 194, 87;

      --header-bg:var(--brand-500);
      --stripe:var(--brand-100);
      --hover:var(--brand-300);
      --scroll-thumb:var(--brand-500);
      --footer-border: rgba(var(--brand-500-rgb), 0.35);

      --cell-align:center;
    }
    .vi-table-embed.align-left { --cell-align:left; }
    .vi-table-embed.align-center { --cell-align:center; }
    .vi-table-embed.align-right { --cell-align:right; }

    .vi-table-embed.brand-vegasinsider{
      --brand-50:#FFF7DC;
      --brand-100:#FFE8AA;
      --brand-300:#FFE08A;
      --brand-500:#F2C23A;
      --brand-600:#D9A72A;
      --brand-700:#B9851A;
      --brand-900:#111111;
      --brand-500-rgb: 242, 194, 58;

      --header-bg:var(--brand-500);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-500);
      --footer-border: rgba(var(--brand-500-rgb), 0.40);
    }

    .vi-table-embed.brand-canadasb{
      --brand-50:#FEF2F2;
      --brand-100:#FEE2E2;
      --brand-300:#FECACA;
      --brand-500:#EF4444;
      --brand-600:#DC2626;
      --brand-700:#B91C1C;
      --brand-900:#7F1D1D;
      --brand-500-rgb: 239, 68, 68;

      --header-bg:var(--brand-600);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
      --footer-border: rgba(220, 38, 38, 0.40);
    }

    .vi-table-embed.brand-rotogrinders{
      --brand-50:#E8F1FF;
      --brand-100:#D3E3FF;
      --brand-300:#9ABCF9;
      --brand-500:#2F7DF3;
      --brand-600:#0159D1;
      --brand-700:#0141A1;
      --brand-900:#011F54;
      --brand-500-rgb: 47, 125, 243;

      --header-bg:var(--brand-700);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
      --footer-border: rgba(1, 89, 209, 0.40);
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
      display:grid;
      grid-template-columns:minmax(0,1fr) auto;
      align-items:center;
      gap:12px;
      margin:4px 0 10px 0;
    }
    #bt-block .left{display:flex; gap:8px; align-items:center; flex-wrap:wrap; justify-content:flex-start}
    #bt-block .right{display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:flex-end; position:relative;}

    #bt-block .dw-field{position:relative}
    #bt-block .dw-input,#bt-block .dw-select,#bt-block .dw-btn{
      font:14px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      border-radius:10px;
      padding:8px 10px;
      transition:.15s ease;
    }
    #bt-block .dw-input,#bt-block .dw-select{
      background:#fff;
      border:1px solid var(--brand-700);
      color:var(--text);
      box-shadow:inset 0 1px 2px rgba(16,24,40,.04);
    }
    #bt-block .dw-input{width:min(320px,100%); padding-right:36px}
    #bt-block .dw-input::placeholder{color:#9AA4B2}
    #bt-block .dw-input:focus,#bt-block .dw-select:focus{
      outline:none;
      border-color:var(--brand-500);
      box-shadow:0 0 0 3px rgba(var(--brand-500-rgb), .25);
      background:#fff;
    }
    #bt-block .dw-select{
      appearance:none; -webkit-appearance:none; -moz-appearance:none;
      padding-right:26px; background:#fff; background-image:none;
    }

    #bt-block .dw-btn{
      background:var(--brand-500);
      color:#fff;
      border:1px solid var(--brand-500);
      padding-inline:12px;
      cursor:pointer;
      white-space:nowrap;
    }
    #bt-block .dw-btn:hover{background:var(--brand-600); border-color:var(--brand-600)}
    #bt-block .dw-btn:active{transform:translateY(1px)}
    #bt-block .dw-btn[disabled]{background:#fafafa; border-color:#d1d5db; color:#6b7280; opacity:1; cursor:not-allowed; transform:none}

    /* Download button */
    #bt-block .dw-btn.dw-download{
      background:#ffffff;
      color:var(--brand-700);
      border:1px solid var(--brand-700);
    }
    #bt-block .dw-btn.dw-download:hover{
      background:var(--brand-50);
      border-color:var(--brand-600);
      color:var(--brand-600);
    }

    /* Download menu (popover) */
    #bt-block .dw-download-menu{
      position:absolute;
      right:0;
      top:44px;
      min-width: 220px;
      background:#fff;
      border:1px solid rgba(0,0,0,.10);
      border-radius:12px;
      box-shadow:0 10px 30px rgba(0,0,0,.18);
      padding:10px;
      z-index: 50;
    }
    #bt-block .dw-download-menu .dw-menu-title{
      font: 12px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      color:#6b7280;
      margin:0 0 8px 2px;
    }
    #bt-block .dw-download-menu .dw-menu-btn{
      width:100%;
      text-align:left;
      border-radius:10px;
      border:1px solid rgba(0,0,0,.10);
      background:#fff;
      color:#111827;
      padding:10px 10px;
      cursor:pointer;
      margin:4px 0;
      font: 14px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    }
    #bt-block .dw-download-menu .dw-menu-btn:hover{
      background:var(--brand-50);
      border-color: rgba(var(--brand-500-rgb), .35);
    }

    /* Clear button */
    #bt-block .dw-clear{
      position:absolute; right:10px; top:50%; translate:0 -50%;
      width:22px; height:22px; border-radius:9999px; border:0;
      background:transparent; color:var(--brand-700);
      cursor:pointer; display:none; align-items:center; justify-content:center;
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
      background:var(--header-bg);
      color:#ffffff;
      font-weight:700;
      vertical-align:middle;
      border:0;
      padding:14px 14px;
      white-space:nowrap;
      transition:background-color .15s, color .15s, box-shadow .15s, transform .05s;
    }
    #bt-block thead th.sortable{cursor:pointer; user-select:none}
    #bt-block thead th.sortable::after{content:"↕"; font-size:12px; opacity:.75; margin-left:8px; color:#ffffff}
    #bt-block thead th.sortable[data-sort="asc"]::after{content:"▲"}
    #bt-block thead th.sortable[data-sort="desc"]::after{content:"▼"}
    #bt-block thead th.sortable:hover,#bt-block thead th.sortable:focus-visible{background:var(--brand-600); color:#fff; box-shadow:inset 0 -3px 0 var(--brand-100)}
    #bt-block .dw-scroll.scrolled thead th{box-shadow:0 6px 10px -6px rgba(0,0,0,.25)}
    #bt-block thead th.is-sorted{background:var(--brand-700); color:#fff; box-shadow:inset 0 -3px 0 var(--brand-100)}

    /* TD stays a real table-cell (do NOT change display here) */
    #bt-block thead th,
    #bt-block tbody td {
      padding: 16px 14px;
      overflow: hidden;
      text-align: var(--cell-align, center);
      vertical-align: middle;
    }

    /* Clamp INSIDE wrapper to prevent bleed without breaking layout */
    #bt-block .dw-cell{
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
      line-height: 1.35;

      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;

      overflow:hidden;
      text-overflow:ellipsis;
    }

    /* Body rows zebra (injected) */
    [[STRIPE_CSS]]

    /* Hover should win */
    #bt-block tbody tr:hover td{ background:var(--hover) !important; }
    #bt-block tbody tr:hover{
      box-shadow:inset 3px 0 0 var(--brand-500);
      transform:translateY(-1px);
      transition:background-color .12s ease, box-shadow .12s ease, transform .08s ease;
    }

    #bt-block thead th{position:sticky; top:0; z-index:5}
    #bt-block .dw-scroll{
      max-height:var(--table-max-h,360px);
      overflow-y:auto;
      -ms-overflow-style:auto;
      scrollbar-width:thin;
      scrollbar-color:var(--scroll-thumb) transparent
    }
    #bt-block .dw-scroll::-webkit-scrollbar:horizontal{height:0; display:none}
    #bt-block .dw-scroll::-webkit-scrollbar:vertical{width:var(--vbar-w)}
    #bt-block .dw-scroll:hover::-webkit-scrollbar:vertical{width:var(--vbar-w-hover)}
    #bt-block .dw-scroll::-webkit-scrollbar-thumb{
      background:var(--scroll-thumb);
      border-radius:9999px;
      border:2px solid transparent;
      background-clip:content-box;
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
    .vi-table-embed .vi-footer img{ height: 36px; width:auto; display:inline-block; }

    /* Brand-specific logo recolor + sizes */
    .vi-table-embed.brand-actionnetwork .vi-footer img{
      filter: brightness(0) saturate(100%) invert(62%) sepia(23%) saturate(1250%) hue-rotate(78deg) brightness(96%) contrast(92%);
      height: 44px;
      width: auto;
      display: inline-block;
    }
    .vi-table-embed.brand-vegasinsider .vi-footer img{
      filter: none !important;
      height:24px;
    }
    .vi-table-embed.brand-canadasb .vi-footer img{
      filter: brightness(0) saturate(100%) invert(32%) sepia(85%) saturate(2386%) hue-rotate(347deg) brightness(96%) contrast(104%);
      height: 28px;
    }
    .vi-table-embed.brand-rotogrinders .vi-footer img{
      filter: brightness(0) saturate(100%) invert(23%) sepia(95%) saturate(1704%) hue-rotate(203deg) brightness(93%) contrast(96%);
      height:32px;
    }

    .vi-hide{ display:none !important; }

    /* EXPORT MODE for capture: ONLY table + logo */
    .vi-table-embed.export-mode .vi-table-header{ display:none !important; } /* removes title/subtitle from export */
    .vi-table-embed.export-mode #bt-block .dw-controls,
    .vi-table-embed.export-mode #bt-block .dw-page-status{
      display:none !important;
    }
    .vi-table-embed.export-mode #bt-block .dw-scroll{
      max-height:none !important;
      height:auto !important;
      overflow:visible !important;
    }
    .vi-table-embed.export-mode #bt-block thead th{
      position:static !important;
    }
    .vi-table-embed.export-mode #bt-block tbody tr:hover,
    .vi-table-embed.export-mode #bt-block tbody tr:hover td{
      transform:none !important;
      box-shadow:none !important;
    }
    .vi-table-embed.export-mode #bt-block table.dw-table{
      table-layout:fixed !important; /* prevents huge width from long URLs */
      width:100% !important;
    }
    .vi-table-embed.export-mode #bt-block .dw-scroll.no-scroll{
      overflow-x:hidden !important;
    }
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
          <input type="search" class="dw-input" placeholder="Search Table…" aria-label="Search Table">
          <button type="button" class="dw-clear" aria-label="Clear Search">×</button>
        </div>
      </div>

      <div class="right [[PAGER_VIS_CLASS]]">
        <label class="dw-status" for="bt-size" style="margin-right:4px;">Rows/Page</label>
        <select id="bt-size" class="dw-select">
          <option value="5">5</option>
          <option value="10" selected>10</option>
          <option value="15">15</option>
          <option value="20">20</option>
          <option value="25">25</option>
          <option value="30">30</option>
          <option value="0">All</option>
        </select>

        <button class="dw-btn" data-page="prev" aria-label="Previous Page">‹</button>
        <button class="dw-btn" data-page="next" aria-label="Next Page">›</button>

        <button class="dw-btn dw-download" id="dw-download-png" type="button">Download PNG</button>

        <div id="dw-download-menu" class="dw-download-menu vi-hide" aria-label="Download Menu">
          <div class="dw-menu-title" id="dw-menu-title">Choose download</div>
          <button type="button" class="dw-menu-btn" id="dw-dl-top10">Download Top 10</button>
          <button type="button" class="dw-menu-btn" id="dw-dl-bottom10">Download Bottom 10</button>
        </div>
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
            <tr class="dw-empty" style="display:none;"><td colspan="[[COLSPAN]]">No Matches Found.</td></tr>
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
    const downloadBtn = controls.querySelector('#dw-download-png');

    const menu = controls.querySelector('#dw-download-menu');
    const btnTop10 = controls.querySelector('#dw-dl-top10');
    const btnBottom10 = controls.querySelector('#dw-dl-bottom10');

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
      pageStatus.textContent = "Page " + page + " Of " + pages;
    }

    function getVisibleRowsInOrder(){
      const ordered = Array.from(tb.rows).filter(r=>!r.classList.contains('dw-empty'));
      return ordered.filter(matchesFilter);
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

    if(hasPager){
      sizeSel.addEventListener('change', e=>{
        pageSize = parseInt(e.target.value,10) || 0;
        page=1;
        renderPage();
      });
      prevBtn.addEventListener('click', ()=>{ page--; renderPage(); });
      nextBtn.addEventListener('click', ()=>{ page++; renderPage(); });
    }

    // =============================
    // Download Menu Toggle
    // =============================
    function hideMenu(){ if(menu) menu.classList.add('vi-hide'); }
    function toggleMenu(){ if(menu) menu.classList.toggle('vi-hide'); }

    document.addEventListener('click', (e)=>{
      if(!menu || menu.classList.contains('vi-hide')) return;
      const inMenu = menu.contains(e.target);
      const inBtn = downloadBtn && downloadBtn.contains(e.target);
      if(!inMenu && !inBtn) hideMenu();
    });

    if(downloadBtn){
      downloadBtn.addEventListener('click', (e)=>{
        e.preventDefault();
        e.stopPropagation();
        toggleMenu();
      });
    }

    // =============================
    // DOM PNG EXPORT (NO alert popups)
    // - Export-mode uses fixed table layout, so width doesn't explode
    // - Export hides header/subtitle and controls: ONLY table + logo
    // =============================
    async function waitForFontsAndImages(el){
      if (document.fonts && document.fonts.ready){
        try { await document.fonts.ready; } catch(e){}
      }
      const imgs = Array.from(el.querySelectorAll('img'));
      await Promise.all(imgs.map(img=>{
        if (img.complete) return Promise.resolve();
        return new Promise(res=>{
          img.addEventListener('load', res, { once:true });
          img.addEventListener('error', res, { once:true });
        });
      }));
    }

    function getFilenameBase(clone){
      // Use TITLE if present; otherwise fallback to 'table'
      const t = clone.querySelector('.vi-table-header .title')?.textContent || 'table';
      return (t || 'table')
        .trim()
        .replace(/\s+/g,'_')
        .replace(/[^\w\-]+/g,'')
        .slice(0,60) || 'table';
    }

    // IMPORTANT FIX:
    // Select rows by POSITION (robust with sorting/filtering/paging),
    // so Bottom 10 always matches correctly.
    function showRowsInClone(clone, mode){
      const cloneTb = clone.querySelector('table.dw-table')?.tBodies?.[0];
      if(!cloneTb) return;

      const cloneRows = Array.from(cloneTb.rows).filter(r=>!r.classList.contains('dw-empty'));

      // Row positions that are visible under current filter, in current DOM order (sorting applied)
      const ordered = Array.from(tb.rows).filter(r=>!r.classList.contains('dw-empty'));
      const visiblePositions = [];
      for(let i=0;i<ordered.length;i++){
        if(matchesFilter(ordered[i])) visiblePositions.push(i);
      }

      const keep = new Set();
      if(mode === 'top10'){
        visiblePositions.slice(0, 10).forEach(i => keep.add(i));
      }else if(mode === 'bottom10'){
        visiblePositions.slice(-10).forEach(i => keep.add(i));
      }

      cloneRows.forEach((r, i)=>{
        r.style.display = keep.has(i) ? 'table-row' : 'none';
      });

      const empty = cloneTb.querySelector('.dw-empty');
      if(empty) empty.style.display='none';
    }

    async function captureCloneToPng(clone, stage, filename, targetWidth){
      const cloneScroller = clone.querySelector('.dw-scroll');

      if(cloneScroller){
        cloneScroller.style.maxHeight = 'none';
        cloneScroller.style.height = 'auto';
        cloneScroller.style.overflow = 'visible';
        cloneScroller.style.overflowX = 'visible';
        cloneScroller.style.overflowY = 'visible';
        cloneScroller.classList.add('no-scroll');
      }

      // Force clone width to match the on-screen widget width (prevents giant images)
      const w = Math.max(900, Math.ceil(targetWidth || 1200));
      clone.style.maxWidth = 'none';
      clone.style.width = w + 'px';

      await new Promise(r => requestAnimationFrame(()=>requestAnimationFrame(r)));
      await waitForFontsAndImages(clone);

      const fullH = Math.ceil(Math.max(
        clone.scrollHeight || 0,
        clone.offsetHeight || 0,
        clone.getBoundingClientRect().height || 0
      ));

      // If height is still insane, just bail silently (no popup)
      const MAX_CAPTURE_AREA = 28_000_000;
      const area = Math.ceil(w) * Math.ceil(fullH);
      if(area > MAX_CAPTURE_AREA){
        stage.remove();
        console.warn("PNG export skipped: capture area too large.", { w, fullH, area });
        return;
      }

      const scale = Math.min(3, Math.max(2, window.devicePixelRatio || 2));

      const canvas = await window.html2canvas(clone, {
        backgroundColor: '#ffffff',
        scale,
        useCORS: true,
        allowTaint: true,
        logging: false,
        width: Math.ceil(w),
        height: Math.ceil(fullH),
        windowWidth: Math.ceil(w),
        windowHeight: Math.ceil(fullH),
        scrollX: 0,
        scrollY: 0,
      });

      canvas.toBlob((blob)=>{
        if(!blob){
          stage.remove();
          console.warn("PNG export failed: no blob returned.");
          return;
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename + '.png';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(()=>URL.revokeObjectURL(url), 1500);
        stage.remove();
      }, 'image/png');
    }

    async function downloadDomPng(mode){
      try{
        hideMenu();

        if(!window.html2canvas){
          console.warn("html2canvas failed to load.");
          return;
        }

        const widget = document.querySelector('section.vi-table-embed');
        if(!widget){
          console.warn("Widget not found.");
          return;
        }

        const stage = document.createElement('div');
        stage.style.position = 'fixed';
        stage.style.left = '-100000px';
        stage.style.top = '0';
        stage.style.background = '#ffffff';
        stage.style.padding = '0';
        stage.style.margin = '0';
        stage.style.zIndex = '-1';

        const clone = widget.cloneNode(true);
        clone.classList.add('export-mode');
        clone.querySelectorAll('script').forEach(s => s.remove());

        stage.appendChild(clone);
        document.body.appendChild(stage);

        showRowsInClone(clone, mode);

        const base = getFilenameBase(clone);
        const suffix = mode === 'bottom10' ? "_bottom10" : "_top10";
        const filename = (base + suffix).slice(0, 70);

        const targetWidth = widget.getBoundingClientRect()?.width || 1200;
        await captureCloneToPng(clone, stage, filename, targetWidth);

      }catch(err){
        console.error("PNG export failed:", err);
      }
    }

    if(btnTop10) btnTop10.addEventListener('click', ()=> downloadDomPng('top10'));
    if(btnBottom10) btnBottom10.addEventListener('click', ()=> downloadDomPng('bottom10'));

    renderPage();
  })();
  </script>

</section>
</body>
</html>
"""

# =========================================================
# Generator
# =========================================================


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
    footer_logo_align: str = "Center",
    cell_align: str = "Center",
) -> str:
    df = df.copy()

    head_cells = []
    for col in df.columns:
        col_type = guess_column_type(df[col])
        safe_label = html_mod.escape(str(col))
        head_cells.append(f'<th scope="col" data-type="{col_type}">{safe_label}</th>')
    table_head_html = "\n              ".join(head_cells)

    # IMPORTANT FIX:
    # keep TD as table-cell; clamp inside a wrapper div
    row_html_snippets = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = "" if pd.isna(row[col]) else str(row[col])
            safe_val = html_mod.escape(val)
            safe_title = html_mod.escape(val, quote=True)
            cells.append(f'<td><div class="dw-cell" title="{safe_title}">{safe_val}</div></td>')
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

    footer_logo_align = (footer_logo_align or "Center").strip().lower()
    if footer_logo_align == "center":
        footer_align_class = "footer-center"
    elif footer_logo_align == "left":
        footer_align_class = "footer-left"
    else:
        footer_align_class = ""  # default right

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


# =========================================================
# UI Helpers
# =========================================================


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
        "footer_logo_align": st.session_state.get("bt_footer_logo_align", "Center"),
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


def reset_widget_state_for_new_upload():
    keys_to_clear = [
        "bt_confirmed_cfg",
        "bt_confirmed_hash",
        "bt_html_code",
        "bt_html_generated",
        "bt_html_hash",
        "bt_last_published_url",
        "bt_iframe_code",
        "bt_widget_file_name",
        "bt_availability",
        "bt_file_conflict_choice",
        "bt_iframe_url",
        "bt_html_stale",
        "bt_confirm_flash",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]


def ensure_confirm_state_exists():
    if "bt_confirmed_cfg" not in st.session_state:
        cfg = draft_config_from_state()
        st.session_state["bt_confirmed_cfg"] = cfg
        st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)

    st.session_state.setdefault("bt_html_code", "")
    st.session_state.setdefault("bt_html_generated", False)
    st.session_state.setdefault("bt_html_hash", "")
    st.session_state.setdefault("bt_last_published_url", "")
    st.session_state.setdefault("bt_iframe_code", "")
    st.session_state.setdefault("bt_widget_file_name", "branded_table.html")

    st.session_state.setdefault("bt_footer_logo_align", "Center")

    st.session_state.setdefault("bt_confirm_flash", False)
    st.session_state.setdefault("bt_html_stale", False)


def do_confirm_snapshot():
    st.session_state["bt_df_confirmed"] = st.session_state["bt_df_draft"].copy()

    cfg = draft_config_from_state()
    st.session_state["bt_confirmed_cfg"] = cfg
    st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)

    html = html_from_config(st.session_state["bt_df_confirmed"], st.session_state["bt_confirmed_cfg"])
    st.session_state["bt_html_code"] = html
    st.session_state["bt_html_generated"] = True
    st.session_state["bt_html_hash"] = st.session_state["bt_confirmed_hash"]
    st.session_state["bt_html_stale"] = False

    st.session_state["bt_confirm_flash"] = True


# =========================================================
# Streamlit App
# =========================================================

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
st.session_state.setdefault("brand_table", "Action Network")
if st.session_state["brand_table"] not in brand_options:
    st.session_state["brand_table"] = "Action Network"

uploaded_file = st.file_uploader("Upload Your CSV File", type=["csv"])
if uploaded_file is None:
    st.info("Upload A CSV To Start.")
    st.stop()

try:
    df_uploaded_now = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error Reading CSV: {e}")
    st.stop()

if df_uploaded_now.empty:
    st.error("Uploaded CSV Has No Rows.")
    st.stop()

uploaded_name = getattr(uploaded_file, "name", "uploaded.csv")
prev_name = st.session_state.get("bt_uploaded_name")

if prev_name != uploaded_name:
    reset_widget_state_for_new_upload()
    st.session_state["bt_uploaded_name"] = uploaded_name
    st.session_state["bt_df_uploaded"] = df_uploaded_now.copy()
    st.session_state["bt_df_draft"] = df_uploaded_now.copy()
    st.session_state["bt_df_confirmed"] = df_uploaded_now.copy()

ensure_confirm_state_exists()

left_col, right_col = st.columns([1, 3], gap="large")

# ===================== Right: Editor + Live Preview (Draft) =====================

with right_col:
    with st.expander("Open Editor", expanded=False):
        edited_df = st.data_editor(
            st.session_state["bt_df_draft"],
            use_container_width=True,
            num_rows="dynamic",
            key="bt_data_editor",
        )
        st.session_state["bt_df_draft"] = edited_df

        c1, c2 = st.columns(2)
        with c1:
            if st.button("↩️ Reset Draft To Uploaded CSV", use_container_width=True):
                st.session_state["bt_df_draft"] = st.session_state["bt_df_uploaded"].copy()
                st.rerun()
        with c2:
            st.caption("Edits Apply To The Draft Immediately. Click Confirm And Save To Finalize HTML/Publishing.")

    draft_cfg_hash = stable_config_hash(draft_config_from_state())
    confirmed_cfg_hash = st.session_state.get("bt_confirmed_hash", "")

    draft_df = st.session_state.get("bt_df_draft")
    confirmed_df = st.session_state.get("bt_df_confirmed")

    df_diff = True
    try:
        df_diff = not draft_df.equals(confirmed_df)
    except Exception:
        df_diff = True

    show_banner = (draft_cfg_hash != confirmed_cfg_hash) or df_diff

    h_left, h_right = st.columns([2, 3], vertical_alignment="center")
    with h_left:
        st.markdown("### Preview (Live Draft)")
    with h_right:
        if show_banner:
            st.info("Preview Reflects Draft. HTML/Publishing Uses The Last Confirmed Snapshot.")
        else:
            st.success("Draft Matches The Confirmed Snapshot.")

    live_cfg = draft_config_from_state()
    live_preview_html = html_from_config(st.session_state["bt_df_draft"], live_cfg)
    components.html(live_preview_html, height=820, scrolling=True)

# ===================== Left: Tabs =====================

with left_col:
    tab_config, tab_html, tab_iframe = st.tabs(["Configure", "HTML", "IFrame"])

    # ---------- CONFIGURE TAB ----------
    with tab_config:
        st.markdown("#### Table Setup")

        st.button(
            "✅ Confirm And Save Table Contents",
            key="bt_confirm_btn",
            use_container_width=True,
            on_click=do_confirm_snapshot,
        )

        if st.session_state.get("bt_confirm_flash", False):
            st.success("Saved. Confirmed Snapshot Updated And HTML Regenerated.")
            st.session_state["bt_confirm_flash"] = False

        sub_brand, sub_head, sub_body = st.tabs(["Brand", "Header / Footer", "Body"])

        with sub_brand:
            current_brand = st.session_state.get("brand_table", "Action Network")
            if current_brand not in brand_options:
                current_brand = "Action Network"

            st.selectbox(
                "Brand",
                options=brand_options,
                index=brand_options.index(current_brand),
                key="brand_table",
            )

        with sub_head:
            show_header = st.checkbox(
                "Show Header Box",
                value=st.session_state.get("bt_show_header", True),
                key="bt_show_header",
            )

            st.text_input(
                "Table Title",
                value=st.session_state.get("bt_widget_title", "Table 1"),
                key="bt_widget_title",
                disabled=not show_header,
            )
            st.text_input(
                "Table Subtitle",
                value=st.session_state.get("bt_widget_subtitle", "Subheading"),
                key="bt_widget_subtitle",
                disabled=not show_header,
            )

            st.checkbox(
                "Center Title And Subtitle",
                value=st.session_state.get("bt_center_titles", False),
                key="bt_center_titles",
                disabled=not show_header,
            )
            st.checkbox(
                "Branded Title Colour",
                value=st.session_state.get("bt_branded_title_color", True),
                key="bt_branded_title_color",
                disabled=not show_header,
            )

            show_footer = st.checkbox(
                "Show Footer (Logo)",
                value=st.session_state.get("bt_show_footer", True),
                key="bt_show_footer",
            )

            st.selectbox(
                "Footer Logo Alignment",
                options=["Right", "Center", "Left"],
                index=["Right", "Center", "Left"].index(st.session_state.get("bt_footer_logo_align", "Center")),
                key="bt_footer_logo_align",
                disabled=not show_footer,
            )

        with sub_body:
            st.checkbox(
                "Striped Rows",
                value=st.session_state.get("bt_striped_rows", True),
                key="bt_striped_rows",
            )
            st.selectbox(
                "Table Content Alignment",
                options=["Center", "Left", "Right"],
                index=["Center", "Left", "Right"].index(st.session_state.get("bt_cell_align", "Center")),
                key="bt_cell_align",
            )
            st.checkbox(
                "Show Search",
                value=st.session_state.get("bt_show_search", True),
                key="bt_show_search",
            )
            show_pager = st.checkbox(
                "Show Pager (Rows/Page + Prev/Next)",
                value=st.session_state.get("bt_show_pager", True),
                key="bt_show_pager",
                help="If Off, The Table Will Show All Rows By Default.",
            )
            st.checkbox(
                "Show Page Numbers (Page X Of Y)",
                value=st.session_state.get("bt_show_page_numbers", True),
                key="bt_show_page_numbers",
                disabled=not show_pager,
            )

        st.markdown("---")
        st.caption("For images: use **Download PNG** in the table. It will show **Top 10** or **Bottom 10**.")

    # ---------- HTML TAB ----------
    with tab_html:
        st.markdown("#### HTML (From Confirmed Snapshot)")
        st.caption("HTML Updates Automatically When You Click Confirm And Save Table Contents.")

        html_code = st.session_state.get("bt_html_code", "")

        if not html_code:
            st.info("Click Confirm And Save Table Contents To Generate HTML.")
        else:
            st.success("HTML Is Ready (From The Latest Confirmed Snapshot).")

        st.text_area(
            "HTML Code",
            value=html_code,
            height=520,
            placeholder="Confirm And Save To Generate HTML Here.",
        )

    # ---------- IFRAME TAB ----------
    with tab_iframe:
        st.markdown("#### Publish + IFrame")

        html_generated = bool(st.session_state.get("bt_html_generated", False))
        if not html_generated:
            st.warning("Click Confirm And Save Table Contents To Generate HTML Before Publishing.")

        saved_gh_user = st.session_state.get("bt_gh_user", "")
        saved_gh_repo = st.session_state.get("bt_gh_repo", "branded-table-widget")

        username_options = ["GauthamBC", "ActionNetwork", "MoonWatcher", "SampleUser"]
        if GITHUB_USER_DEFAULT and GITHUB_USER_DEFAULT not in username_options:
            username_options.insert(0, GITHUB_USER_DEFAULT)

        default_idx = username_options.index(saved_gh_user) if saved_gh_user in username_options else 0
        github_username_input = st.selectbox(
            "Username (GitHub Username_toggle):\n",
            options=username_options,
            index=default_idx,
            key="bt_gh_user",
            disabled=not html_generated,
        )
        effective_github_user = (github_username_input or "").strip()

        repo_name = st.text_input(
            "Widget Hosting Repository Name",
            value=saved_gh_repo,
            key="bt_gh_repo",
            disabled=not html_generated,
        ).strip()

        base_filename = "branded_table.html"
        st.session_state.setdefault("bt_widget_file_name", base_filename)
        widget_file_name = st.session_state.get("bt_widget_file_name", base_filename)

        st.caption(f"Target File In Repo: `{widget_file_name}`")

        can_run_github = bool(GITHUB_TOKEN and effective_github_user and repo_name)
        can_publish = bool(can_run_github and html_generated)

        col_check, col_pub = st.columns([1, 1])
        with col_check:
            page_check_clicked = st.button(
                "Page Availability Check",
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
            )

        if not GITHUB_TOKEN:
            st.info("Set `GITHUB_TOKEN` In `.streamlit/secrets.toml` (With `repo` Scope) To Enable GitHub Publishing.")

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
                st.success("Availability Check Complete.")
            except Exception as e:
                st.error(f"Availability Check Failed: {e}")

        availability = st.session_state.get("bt_availability")
        if html_generated and can_run_github and availability:
            repo_exists = availability.get("repo_exists", False)
            file_exists = availability.get("file_exists", False)
            checked_filename = availability.get("checked_filename", base_filename)
            suggested_new_filename = availability.get("suggested_new_filename") or "t1.html"

            if not repo_exists:
                st.info("No Existing Repo Found. Publishing Will Create It.")
                st.session_state["bt_widget_file_name"] = checked_filename
            elif repo_exists and not file_exists:
                st.success(f"Repo Exists And `{checked_filename}` Is Available.")
                st.session_state["bt_widget_file_name"] = checked_filename
            else:
                st.warning(f"`{checked_filename}` Already Exists.")
                choice = st.radio(
                    "Choose What To Do",
                    options=[
                        "Replace Existing Widget (Overwrite File)",
                        f"Create Additional Widget File In Same Repo (Use {suggested_new_filename})",
                        "Change Campaign Name Instead",
                    ],
                    key="bt_file_conflict_choice",
                    disabled=not html_generated,
                )
                if choice.startswith("Replace"):
                    st.session_state["bt_widget_file_name"] = checked_filename
                elif choice.startswith("Create Additional"):
                    st.session_state["bt_widget_file_name"] = suggested_new_filename

        if publish_clicked:
            try:
                html_final = st.session_state.get("bt_html_code", "")
                if not html_final:
                    raise RuntimeError("No Generated HTML Found. Click Confirm And Save First.")

                ph = st.empty()
                prog = st.progress(0)
                ph.caption("Publishing To GitHub…")
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
                    f"Add/Update {widget_file_name} From Branded Table App",
                    branch="main",
                )
                trigger_pages_build(effective_github_user, repo_name, GITHUB_TOKEN)

                prog.progress(100)
                time.sleep(0.12)
                ph.empty()
                prog.empty()

                pages_url = compute_pages_url(effective_github_user, repo_name, widget_file_name)
                st.session_state["bt_last_published_url"] = pages_url
                st.success("Published. GitHub Pages May Take A Minute To Update.")

            except Exception as e:
                st.error(f"GitHub Publish Failed: {e}")

        st.markdown("---")
        st.markdown("#### IFrame Embed")

        pages_url = st.session_state.get("bt_last_published_url", "")
        default_url = ""
        if html_generated and effective_github_user and repo_name:
            default_url = compute_pages_url(
                effective_github_user,
                repo_name,
                st.session_state.get("bt_widget_file_name", base_filename),
            )

        url_to_use = st.text_input(
            "Page URL Used For IFrame",
            value=pages_url or default_url,
            key="bt_iframe_url",
            disabled=not html_generated,
        )

        iframe_height = st.number_input(
            "IFrame Height (Px)",
            min_value=300,
            max_value=2000,
            value=int(st.session_state.get("bt_iframe_height", 800)),
            step=50,
            key="bt_iframe_height",
            disabled=not html_generated,
        )

        get_iframe_clicked = st.button(
            "🧩 Get IFrame Code",
            key="bt_get_iframe",
            disabled=not html_generated or not bool(url_to_use.strip()),
            use_container_width=True,
        )

        if get_iframe_clicked:
            simulate_progress("Generating IFrame…", total_sleep=0.25)
            st.session_state["bt_iframe_code"] = build_iframe_snippet(url_to_use, height=int(iframe_height))
            st.success("IFrame Code Generated.")

        st.text_area(
            "IFrame Code",
            value=st.session_state.get("bt_iframe_code", ""),
            height=200,
            placeholder="Confirm And Save To Generate HTML, Then Generate IFrame Code Here.",
        )

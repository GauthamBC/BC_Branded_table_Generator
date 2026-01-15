import base64
import datetime
import html as html_mod
import json
import re
import time
from collections.abc import Mapping

import jwt  # ✅ NEW (PyJWT)
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# 0) Publishing Users + Secrets (GITHUB APP)
# =========================================================
PUBLISH_USERS = ["gauthambc", "amybc", "benbc", "kathybc"]


def get_secret(key: str, default=""):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


# ✅ GitHub App Secrets (store these in Streamlit secrets)
GITHUB_APP_ID = str(get_secret("GITHUB_APP_ID", "")).strip()
GITHUB_APP_PRIVATE_KEY = str(get_secret("GITHUB_APP_PRIVATE_KEY", "")).strip()

# optional (for showing install link)
GITHUB_APP_SLUG = str(get_secret("GITHUB_APP_SLUG", "")).strip().lower()  # e.g. "bcdprpagehoster"


# =========================================================
# Repo Auto-Naming (Full Brand Name + Month + Year)
# =========================================================
BRAND_REPO_PREFIX_FULL = {
    "Action Network": "ActionNetwork",
    "Canada Sports Betting": "CanadaSportsBetting",
    "VegasInsider": "VegasInsider",
    "RotoGrinders": "RotoGrinders",
}

MONTH_CODE = {
    1: "j",  # Jan
    2: "f",  # Feb
    3: "m",  # Mar
    4: "a",  # Apr
    5: "y",  # May
    6: "u",  # Jun
    7: "l",  # Jul
    8: "g",  # Aug
    9: "s",  # Sep
    10: "o",  # Oct
    11: "n",  # Nov
    12: "d",  # Dec
}


def suggested_repo_name(brand: str) -> str:
    b = (brand or "").strip()
    prefix = BRAND_REPO_PREFIX_FULL.get(b, "ActionNetwork")
    now = datetime.datetime.utcnow()
    mm = MONTH_CODE.get(now.month, "x")
    yy = str(now.year)[-2:]
    return f"{prefix}{mm}{yy}"


# =========================================================
# GitHub Helpers
# =========================================================
def github_headers(token: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["X-GitHub-Api-Version"] = "2022-11-28"
    return headers


def build_github_app_jwt(app_id: str, private_key_pem: str) -> str:
    """
    Create a short-lived JWT for GitHub App authentication.
    """
    if not app_id or not private_key_pem:
        raise RuntimeError("Missing GitHub App credentials in secrets (GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY).")

    now = int(time.time())
    payload = {
        "iat": now - 30,          # helps with clock skew
        "exp": now + (9 * 60),    # <= 10 mins
        "iss": app_id,
    }

    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    # PyJWT can return bytes depending on version
    if isinstance(token, bytes):
        token = token.decode("utf-8", errors="ignore")
    return token


def get_installation_id_for_user(username: str) -> int:
    """
    Returns GitHub App installation id for a given personal account username
    IF the app is installed there.
    """
    username = (username or "").strip()
    if not username:
        return 0

    app_jwt = build_github_app_jwt(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)

    r = requests.get(
        f"https://api.github.com/users/{username}/installation",
        headers=github_headers(app_jwt),
        timeout=20,
    )

    if r.status_code == 200:
        data = r.json() or {}
        return int(data.get("id", 0) or 0)

    # Not installed / blocked / not accessible
    if r.status_code in (404, 403):
        return 0

    raise RuntimeError(f"Error checking GitHub App installation: {r.status_code} {r.text}")


@st.cache_data(ttl=50 * 60)
def get_installation_token_for_user(username: str) -> str:
    """
    Get an installation token for a user.
    Caches ~50 mins because token lifetime is ~1 hour.
    """
    install_id = get_installation_id_for_user(username)
    if not install_id:
        return ""

    app_jwt = build_github_app_jwt(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)

    r = requests.post(
        f"https://api.github.com/app/installations/{install_id}/access_tokens",
        headers=github_headers(app_jwt),
        timeout=20,
    )

    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error creating installation token: {r.status_code} {r.text}")

    data = r.json() or {}
    return str(data.get("token", "")).strip()


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

    # NOTE:
    # Some GitHub App installation tokens may NOT be allowed to create new user repos.
    # If this fails with 403, user should create repo manually once.
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


def github_file_exists(owner: str, repo: str, token: str, path: str, branch: str = "main") -> bool:
    """True if a file exists at path in repo."""
    try:
        api_base = "https://api.github.com"
        headers = github_headers(token)
        path = (path or "").lstrip("/").strip()
        if not path:
            return False
        url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
        r = requests.get(url, headers=headers, params={"ref": branch}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


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
# HTML Template (UPDATED)
# =========================================================
HTML_TEMPLATE_TABLE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>[[TITLE]]</title>

<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
</head>

<body style="margin:0; overflow:auto;">

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

      /* ✅ Controls sizing */
      --ctrl-font: 13px;
      --ctrl-pad-y: 7px;
      --ctrl-pad-x: 10px;
      --ctrl-radius: 10px;
      --ctrl-gap: 8px;

      /* ✅ Table scroll height (increase so 10 rows fits better) */
      --table-max-h: 680px;
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
      --gutter: 12px;
      padding: 10px var(--gutter);
      padding-top: 10px;
    }

    /* ✅ Controls row */
    #bt-block .dw-controls{
      display:grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items:center;
      gap: var(--ctrl-gap);
      margin: 4px 0 10px 0;
      width:100%;
      min-width:0;
    }

    #bt-block .left,
    #bt-block .right{
      min-width:0;
      display:flex;
      align-items:center;
    }

    #bt-block .left{ justify-content:flex-start; }
    #bt-block .right{
      justify-content:flex-end;
      gap: var(--ctrl-gap);
      flex-wrap:nowrap;
      white-space:nowrap;
      position:relative;
    }

    #bt-block .dw-pager,
    #bt-block .dw-embed{
      display:flex;
      align-items:center;
      gap: var(--ctrl-gap);
      flex-wrap:nowrap;
      white-space:nowrap;
      position:relative;
    }

    #bt-block .dw-field{ position:relative; min-width:0; }

    #bt-block .dw-input,
    #bt-block .dw-select,
    #bt-block .dw-btn{
      font: var(--ctrl-font)/1.1 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      border-radius: var(--ctrl-radius);
      padding: var(--ctrl-pad-y) var(--ctrl-pad-x);
      transition:.15s ease;
    }

    /* Search */
    #bt-block .dw-input{
      width: clamp(120px, 34vw, 240px);
      max-width: 240px;
      padding-right: 34px;
      background:#fff;
      border:1px solid var(--brand-700);
      color:var(--text);
      box-shadow:inset 0 1px 2px rgba(16,24,40,.04);
    }
    #bt-block .dw-input::placeholder{color:#9AA4B2}
    #bt-block .dw-input:focus,
    #bt-block .dw-select:focus{
      outline:none;
      border-color:var(--brand-500);
      box-shadow:0 0 0 3px rgba(var(--brand-500-rgb), .22);
      background:#fff;
    }

    /* Rows/Page dropdown */
    #bt-block .dw-select{
      appearance:none; -webkit-appearance:none; -moz-appearance:none;
      padding-right: 18px;
      width: 62px;
      text-align:center;
      background:#fff;
      border:1px solid var(--brand-700);
      color:var(--text);
      box-shadow:inset 0 1px 2px rgba(16,24,40,.04);
    }

    /* Buttons */
    #bt-block .dw-btn{
      background:var(--brand-500);
      color:#fff;
      border:1px solid var(--brand-500);
      padding-inline: 10px;
      cursor:pointer;
      white-space:nowrap;
      height: 34px;
      display:inline-flex;
      align-items:center;
      justify-content:center;
    }
    #bt-block .dw-btn:hover{background:var(--brand-600); border-color:var(--brand-600)}
    #bt-block .dw-btn:active{transform:translateY(1px)}
    #bt-block .dw-btn[disabled]{background:#fafafa; border-color:#d1d5db; color:#6b7280; opacity:1; cursor:not-allowed; transform:none}
    #bt-block .dw-btn[data-page]{ width: 34px; padding: 0; }

    /* Embed/Download button */
    #bt-block .dw-btn.dw-download{
      background:#ffffff;
      color:var(--brand-700);
      border:1px solid var(--brand-700);
      height: 34px;
      padding-inline: 10px;
      font-weight:600;
    }
    #bt-block .dw-btn.dw-download:hover{
      background:var(--brand-50);
      border-color:var(--brand-600);
      color:var(--brand-600);
    }

    /* ✅ Download menu (vertical stack) */
    #bt-block .dw-download-menu{
      position:absolute;
      right:0;
      top:40px;
      min-width: 220px;
      background:#fff;
      border:1px solid rgba(0,0,0,.10);
      border-radius:12px;
      box-shadow:0 10px 30px rgba(0,0,0,.18);
      padding:10px;
      z-index: 50;

      display:flex;
      flex-direction:column;
      align-items:stretch;
      gap:6px;
    }

    #bt-block .dw-download-menu .dw-menu-title{
      font: 12px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      color:#6b7280;
      margin:0 0 8px 2px;
    }

    #bt-block .dw-download-menu .dw-menu-btn{
      width:100%;
      display:block;
      text-align:left;
      border-radius:10px;
      border:1px solid rgba(0,0,0,.10);
      background:#fff;
      color:#111827;
      padding:10px 10px;
      cursor:pointer;
      margin:0;
      font: 14px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    }
    #bt-block .dw-download-menu .dw-menu-btn:hover{
      background:var(--brand-50);
      border-color: rgba(var(--brand-500-rgb), .35);
    }

    /* Clear button */
    #bt-block .dw-clear{
      position:absolute; right:9px; top:50%; translate:0 -50%;
      width:20px; height:20px; border-radius:9999px; border:0;
      background:transparent; color:var(--brand-700);
      cursor:pointer; display:none; align-items:center; justify-content:center;
    }
    #bt-block .dw-field.has-value .dw-clear{display:flex}
    #bt-block .dw-clear:hover{background:var(--brand-100)}

    /* ✅ Card wrapper MUST NOT CLIP scrollbars */
    #bt-block .dw-card{
      background: var(--bg);
      border: 0;
      box-shadow: none;
      margin: 0;
      width: 100%;
      overflow: visible;
    }

    /* ✅ REAL vertical + horizontal scroll + branded slim bars */
    #bt-block .dw-scroll{
      max-height: min(var(--table-max-h, 680px), calc(100vh - 240px));
      overflow: auto;
      -webkit-overflow-scrolling: touch;
      touch-action: pan-x pan-y;

      /* ✅ IMPORTANT: allow “table scroll ends → page scroll continues” */
      overscroll-behavior: auto;

      scrollbar-gutter: stable both-edges;

      /* Firefox */
      scrollbar-width: thin;
      scrollbar-color: var(--scroll-thumb) transparent;
    }

    /* Chrome/Edge/Safari */
    #bt-block .dw-scroll::-webkit-scrollbar{
      width: 8px;
      height: 8px;
    }
    #bt-block .dw-scroll::-webkit-scrollbar-track{
      background: transparent;
    }
    #bt-block .dw-scroll::-webkit-scrollbar-thumb{
      background: var(--scroll-thumb);
      border-radius: 9999px;
      border: 2px solid transparent;
      background-clip: content-box;
    }
    #bt-block .dw-scroll::-webkit-scrollbar-thumb:hover{
      background: var(--brand-600);
    }

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

    #bt-block thead th,
    #bt-block tbody td {
      padding: 16px 14px;
      overflow: hidden;
      text-align: var(--cell-align, center);
      vertical-align: middle;
    }

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

    #bt-block tbody tr:hover td{ background:var(--hover) !important; }
    #bt-block tbody tr:hover{
      box-shadow:inset 3px 0 0 var(--brand-500);
      transform:translateY(-1px);
      transition:background-color .12s ease, box-shadow .12s ease, transform .08s ease;
    }

    #bt-block thead th{position:sticky; top:0; z-index:5}

    #bt-block tr.dw-empty td{
      text-align:center; color:#6b7280; font-style:italic; padding:18px 14px;
      background:linear-gradient(0deg,#fff,var(--brand-50)) !important;
    }

    /* ✅ Footer always visible */
    .vi-table-embed .vi-footer {
      display:block;
      padding:10px 14px 8px;
      border-top:1px solid var(--footer-border);
      background:linear-gradient(90deg,var(--brand-50),#ffffff);
      position: sticky;
      bottom: 0;
      z-index: 20;
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

    .vi-table-embed.brand-actionnetwork .vi-footer img{
      filter: brightness(0) saturate(100%) invert(62%) sepia(23%) saturate(1250%) hue-rotate(78deg) brightness(96%) contrast(92%);
      height: 44px;
      width: auto;
      display: inline-block;
    }
    .vi-table-embed.brand-vegasinsider .vi-footer img{ filter: none !important; height:24px; }
    .vi-table-embed.brand-canadasb .vi-footer img{
      filter: brightness(0) saturate(100%) invert(32%) sepia(85%) saturate(2386%) hue-rotate(347deg) brightness(96%) contrast(104%);
      height: 28px;
    }
    .vi-table-embed.brand-rotogrinders .vi-footer img{
      filter: brightness(0) saturate(100%) invert(23%) sepia(95%) saturate(1704%) hue-rotate(203deg) brightness(93%) contrast(96%);
      height:32px;
    }

    .vi-hide{ display:none !important; }

    /* EXPORT MODE (table + logo only) */
    .vi-table-embed.export-mode .vi-table-header{ display:none !important; }
    .vi-table-embed.export-mode #bt-block .dw-controls,
    .vi-table-embed.export-mode #bt-block .dw-page-status{
      display:none !important;
    }
    .vi-table-embed.export-mode #bt-block .dw-scroll{
      max-height:none !important;
      height:auto !important;
      overflow:visible !important;
    }
    .vi-table-embed.export-mode #bt-block thead th{ position:static !important; }
    .vi-table-embed.export-mode #bt-block tbody tr:hover,
    .vi-table-embed.export-mode #bt-block tbody tr:hover td{
      transform:none !important;
      box-shadow:none !important;
    }
    .vi-table-embed.export-mode #bt-block table.dw-table{
      table-layout:fixed !important;
      width:100% !important;
    }
    .vi-table-embed.export-mode #bt-block .dw-scroll.no-scroll{ overflow-x:hidden !important; }
  </style>

  <!-- Header -->
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

      <div class="right">
        <!-- Pager -->
        <div class="dw-pager [[PAGER_VIS_CLASS]]">
          <label class="dw-status" for="bt-size" style="margin-right:2px;">Rows/Page</label>
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
        </div>

        <!-- Embed/Download -->
        <div class="dw-embed [[EMBED_VIS_CLASS]]">
          <button class="dw-btn dw-download" id="dw-download-png" type="button">Embed / Download</button>

          <div id="dw-download-menu" class="dw-download-menu vi-hide" aria-label="Download Menu">
            <div class="dw-menu-title" id="dw-menu-title">Choose action</div>
            <button type="button" class="dw-menu-btn" id="dw-dl-top10">Download Top 10</button>
            <button type="button" class="dw-menu-btn" id="dw-dl-bottom10">Download Bottom 10</button>
            <button type="button" class="dw-menu-btn" id="dw-embed-script">Copy HTML</button>
          </div>
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

    <div class="dw-page-status [[PAGE_STATUS_VIS_CLASS]]" style="padding:6px 2px 4px; color:#6b7280; font:12px/1.2 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
      <span id="dw-page-status-text"></span>
    </div>
  </div>

  <!-- Footer -->
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

    const pagerWrap = controls.querySelector('.dw-pager');
    const sizeSel = pagerWrap ? pagerWrap.querySelector('#bt-size') : null;
    const prevBtn = pagerWrap ? pagerWrap.querySelector('[data-page="prev"]') : null;
    const nextBtn = pagerWrap ? pagerWrap.querySelector('[data-page="next"]') : null;

    const embedWrap = controls.querySelector('.dw-embed');
    const downloadBtn = embedWrap ? embedWrap.querySelector('#dw-download-png') : null;
    const menu = embedWrap ? embedWrap.querySelector('#dw-download-menu') : null;
    const btnTop10 = embedWrap ? embedWrap.querySelector('#dw-dl-top10') : null;
    const btnBottom10 = embedWrap ? embedWrap.querySelector('#dw-dl-bottom10') : null;
    const btnEmbed = embedWrap ? embedWrap.querySelector('#dw-embed-script') : null;
    const menuTitle = embedWrap ? embedWrap.querySelector('#dw-menu-title') : null;

    const emptyRow = tb.querySelector('.dw-empty');
    const pageStatus = document.getElementById('dw-page-status-text');

    const hasSearch = !controlsHidden
      && !!searchFieldWrap && !searchFieldWrap.classList.contains('vi-hide')
      && !!searchInput && !!clearBtn;

    const hasPager = !controlsHidden
      && !!pagerWrap && !pagerWrap.classList.contains('vi-hide')
      && !!sizeSel && !!prevBtn && !!nextBtn;

    const hasEmbed = !controlsHidden
      && !!embedWrap && !embedWrap.classList.contains('vi-hide')
      && !!downloadBtn && !!menu && !!btnEmbed;

    Array.from(tb.rows).forEach((r,i)=>{ if(!r.classList.contains('dw-empty')) r.dataset.idx=i; });

    let pageSize = hasPager ? (parseInt(sizeSel.value,10) || 10) : 0;
    let page = 1;
    let filter = '';

    const onScrollShadow = ()=> scroller.classList.toggle('scrolled', scroller.scrollTop > 0);
    scroller.addEventListener('scroll', onScrollShadow); onScrollShadow();

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

      /* ✅ reset scroll to top after changing pages */
      scroller.scrollTop = 0;
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

    function hideMenu(){ if(menu) menu.classList.add('vi-hide'); }
    function toggleMenu(){ if(menu) menu.classList.toggle('vi-hide'); }

    document.addEventListener('click', (e)=>{
      if(!menu || menu.classList.contains('vi-hide')) return;
      const inMenu = menu.contains(e.target);
      const inBtn = downloadBtn && downloadBtn.contains(e.target);
      if(!inMenu && !inBtn) hideMenu();
    });

    if(hasEmbed && downloadBtn){
      downloadBtn.addEventListener('click', (e)=>{
        e.preventDefault();
        e.stopPropagation();
        toggleMenu();
      });
    }

    /* ===== PNG EXPORT ===== */
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
      const t = clone.querySelector('.vi-table-header .title')?.textContent || 'table';
      return (t || 'table')
        .trim()
        .replace(/\s+/g,'_')
        .replace(/[^\w\-]+/g,'')
        .slice(0,60) || 'table';
    }

    function showRowsInClone(clone, mode){
      const cloneTb = clone.querySelector('table.dw-table')?.tBodies?.[0];
      if(!cloneTb) return;

      const cloneRows = Array.from(cloneTb.rows).filter(r=>!r.classList.contains('dw-empty'));
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
        cloneScroller.classList.add('no-scroll'); /* ✅ KEEP THIS */
      }

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
        if(!window.html2canvas) return;

        const widget = document.querySelector('section.vi-table-embed');
        if(!widget) return;

        const stage = document.createElement('div');
        stage.style.position = 'fixed';
        stage.style.left = '-100000px';
        stage.style.top = '0';
        stage.style.background = '#ffffff';
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

    function getFullHtml(){
      const html = document.documentElement ? document.documentElement.outerHTML : "";
      return "<!doctype html>\n" + html;
    }

    async function copyToClipboard(text){
      try{
        if(navigator.clipboard && navigator.clipboard.writeText){
          await navigator.clipboard.writeText(text);
          return true;
        }
      }catch(e){}
      try{
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly','');
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
        return true;
      }catch(e){
        return false;
      }
    }

    async function onEmbedClick(){
      hideMenu();
      const code = getFullHtml();
      const ok = await copyToClipboard(code);
      if(menuTitle){
        menuTitle.textContent = ok ? 'HTML copied!' : 'Copy failed (try again)';
        setTimeout(()=>{ menuTitle.textContent = 'Choose action'; }, 1800);
      }
    }

    if(hasEmbed && btnTop10) btnTop10.addEventListener('click', ()=> downloadDomPng('top10'));
    if(hasEmbed && btnBottom10) btnBottom10.addEventListener('click', ()=> downloadDomPng('bottom10'));
    if(hasEmbed && btnEmbed) btnEmbed.addEventListener('click', onEmbedClick);

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
    show_embed: bool = True,
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

    controls_vis = "" if (show_search or show_pager or show_embed) else "vi-hide"
    search_vis = "" if show_search else "vi-hide"
    pager_vis = "" if show_pager else "vi-hide"
    embed_vis = "" if show_embed else "vi-hide"
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
        .replace("[[EMBED_VIS_CLASS]]", embed_vis)
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
        "show_embed": st.session_state.get("bt_show_embed", True),
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
        show_embed=cfg["show_embed"],
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
    if not url:
        return ""
    h = int(height) if height else 800
    return f"""<iframe
  src="{html_mod.escape(url, quote=True)}"
  width="100%"
  height="{h}"
  style="border:0; border-radius:12px; overflow:hidden;"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
></iframe>"""


# ✅ NEW: Copy button components for URL + iframe (no extra packages needed)
def render_copy_box(label: str, text_value: str, multiline: bool = False):
    """
    Read-only field + Copy icon button.
    ✅ No overlap (grid + responsive fallback)
    ✅ Button becomes a small icon
    ✅ If narrow width → button moves below field automatically
    """
    safe_text = json.dumps(text_value or "")
    safe_label = html_mod.escape(label)

    if multiline:
        field_html = """
          <textarea id="txt" readonly style="
            width:100%;
            height:120px;
            resize:none;
            border-radius:10px;
            border:1px solid rgba(255,255,255,0.15);
            background:rgba(255,255,255,0.06);
            color:#e5e7eb;
            padding:12px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
            font-size:12px;
            line-height:1.35;
            outline:none;
            overflow:auto;
            display:block;
          "></textarea>
        """
        comp_height = 175
    else:
        field_html = """
          <input id="txt" readonly style="
            width:100%;
            height:40px;
            border-radius:10px;
            border:1px solid rgba(255,255,255,0.15);
            background:rgba(255,255,255,0.06);
            color:#e5e7eb;
            padding:0 12px;
            font-size:13px;
            outline:none;
            display:block;
          "/>
        """
        comp_height = 90

    html = f"""
    <style>
      .copy-wrap {{
        width:100%;
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
      }}

      .copy-label {{
        font-size:12px;
        color:rgba(229,231,235,0.75);
        margin:0 0 6px 2px;
      }}

      /* ✅ Grid: field + icon button */
      .copy-grid {{
        display:grid;
        grid-template-columns: 1fr 44px;
        gap:12px;
        align-items: start;
        width:100%;
      }}

      .copy-grid > div {{
        min-width:0;
      }}

      .copy-btn {{
        width:44px;
        height:40px;
        border-radius:10px;
        border:1px solid rgba(255,255,255,0.18);
        background:rgba(255,255,255,0.08);
        color:#e5e7eb;
        cursor:pointer;
        display:flex;
        align-items:center;
        justify-content:center;
        padding:0;
      }}

      .copy-btn:hover {{
        background:rgba(255,255,255,0.14);
      }}

      /* ✅ If narrow space, button goes below (prevents ANY overlap) */
      @media (max-width: 420px) {{
        .copy-grid {{
          grid-template-columns: 1fr;
        }}
        .copy-btn {{
          width:100%;
          height:40px;
          justify-content:center;
        }}
      }}
    </style>

    <div class="copy-wrap">
      <div class="copy-label">{safe_label}</div>

      <div class="copy-grid">
        <div>
          {field_html}
        </div>

        <button id="btn" class="copy-btn" aria-label="Copy">
          <!-- ✅ Clipboard icon -->
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M9 6h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5 18H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <script>
        const v = {safe_text};
        const txt = document.getElementById("txt");
        const btn = document.getElementById("btn");
        if(txt) txt.value = v;

        async function doCopy() {{
          try {{
            await navigator.clipboard.writeText(v || "");
            btn.style.opacity = "0.75";
            setTimeout(()=>btn.style.opacity="1", 500);
          }} catch(e) {{
            try {{
              txt.focus();
              txt.select();
              document.execCommand("copy");
              btn.style.opacity = "0.75";
              setTimeout(()=>btn.style.opacity="1", 500);
            }} catch(e2) {{}}
          }}
        }}

        btn.addEventListener("click", doCopy);
      </script>
    </div>
    """
    components.html(html, height=comp_height)


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
        "bt_gh_user",
        "bt_gh_repo",
        "bt_html_stale",
        "bt_confirm_flash",
        "bt_widget_exists_locked",
        "bt_widget_name_locked_value",
        "bt_df_uploaded",
        "bt_df_confirmed",
        # ✅ override flow keys
        "bt_allow_swap",
        "bt_swap_confirm_text",
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

    # hard-clean legacy "data:text/html;base64,..." iframe code so it never shows pre-publish
    iframe_val = (st.session_state.get("bt_iframe_code") or "").strip()
    if iframe_val and ("data:text/html" in iframe_val or "about:srcdoc" in iframe_val):
        st.session_state["bt_iframe_code"] = ""

    st.session_state.setdefault("bt_footer_logo_align", "Center")
    st.session_state.setdefault("bt_gh_user", "Select a user...")
    st.session_state.setdefault("bt_widget_file_name", "table.html")

    st.session_state.setdefault("bt_confirm_flash", False)
    st.session_state.setdefault("bt_html_stale", False)

    st.session_state.setdefault("bt_widget_exists_locked", False)
    st.session_state.setdefault("bt_widget_name_locked_value", "")

    # embed button checkbox default ON
    st.session_state.setdefault("bt_show_embed", True)

    # ✅ override flow
    st.session_state.setdefault("bt_allow_swap", False)
    st.session_state.setdefault("bt_swap_confirm_text", "")


def do_confirm_snapshot():
    st.session_state["bt_df_confirmed"] = st.session_state["bt_df_uploaded"].copy()

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
    st.session_state["bt_df_confirmed"] = df_uploaded_now.copy()

ensure_confirm_state_exists()

left_col, right_col = st.columns([1, 3], gap="large")

# ===================== Right: Live Preview =====================
with right_col:
    draft_cfg_hash = stable_config_hash(draft_config_from_state())
    confirmed_cfg_hash = st.session_state.get("bt_confirmed_hash", "")

    show_banner = (draft_cfg_hash != confirmed_cfg_hash)

    h_left, h_right = st.columns([2, 3], vertical_alignment="center")
    with h_left:
        st.markdown("### Preview")
    with h_right:
        if show_banner:
            st.info("Preview reflects current settings. HTML/Publishing uses the last confirmed snapshot.")
        else:
            st.success("Settings match the confirmed snapshot.")

    live_cfg = draft_config_from_state()
    live_preview_html = html_from_config(st.session_state["bt_df_uploaded"], live_cfg)
    components.html(live_preview_html, height=820, scrolling=True)

# ===================== Left: Tabs =====================
with left_col:
    tab_config, tab_html, tab_iframe = st.tabs(["Configure", "HTML", "IFrame"])

    # ---------- CONFIGURE TAB ----------
    with tab_config:
        st.markdown("#### Table Setup")

        st.button(
            "✅ Confirm And Save (Generate HTML For Publishing)",
            key="bt_confirm_btn",
            use_container_width=True,
            on_click=do_confirm_snapshot,
        )

        if st.session_state.get("bt_confirm_flash", False):
            st.success("Saved. Confirmed snapshot updated and HTML regenerated.")
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
                help="If Off, the table will show all rows by default (but Embed/Download can still remain ON).",
            )

            st.checkbox(
                "Show Page Numbers (Page X Of Y)",
                value=st.session_state.get("bt_show_page_numbers", True),
                key="bt_show_page_numbers",
                disabled=not show_pager,
            )

            st.checkbox(
                "Show Embed / Download Button",
                value=st.session_state.get("bt_show_embed", True),
                key="bt_show_embed",
                help="Independent of Pager. This only hides/shows the Embed/Download button + menu.",
            )

        st.markdown("---")
        st.caption("Inside the table: **Embed / Download → Copy HTML** copies the full HTML of the widget (not an iframe).")

    # ---------- HTML TAB ----------
    with tab_html:
        st.markdown("#### HTML (From Confirmed Snapshot)")
        st.caption("HTML updates only when you click **Confirm And Save**.")

        html_code = st.session_state.get("bt_html_code", "")

        if not html_code:
            st.info("Click Confirm And Save to generate HTML.")
        else:
            st.success("HTML is ready (from the latest confirmed snapshot).")

        st.text_area(
            "HTML Code",
            value=html_code,
            height=520,
            placeholder="Confirm And Save to generate HTML here.",
        )

    # ---------- IFRAME TAB ----------
    with tab_iframe:
        st.markdown("### Publish + IFrame")

        html_generated = bool(st.session_state.get("bt_html_generated", False))
        if not html_generated:
            st.warning("Click **Confirm And Save** to generate HTML before publishing.")

        allowed_users = list(PUBLISH_USERS)
        username_options = ["Select a user..."] + allowed_users

        saved_user = st.session_state.get("bt_gh_user", "Select a user...")
        if saved_user not in username_options:
            saved_user = "Select a user..."

        github_username_input = st.selectbox(
            "User name",
            options=username_options,
            index=username_options.index(saved_user),
            key="bt_gh_user",
            disabled=False,
        )

        effective_github_user = ""
        if github_username_input and github_username_input != "Select a user...":
            effective_github_user = github_username_input.strip().lower()

        # ✅ Installation token from GitHub App
        installation_token = ""
        app_installed = False

        if effective_github_user:
            try:
                installation_token = get_installation_token_for_user(effective_github_user)
                app_installed = bool(installation_token)
            except Exception as e:
                installation_token = ""
                app_installed = False
                st.caption(f"⚠️ GitHub App check failed: {e}")

            if app_installed:
                st.caption("✅ GitHub App is installed for this user. Publishing is enabled.")
            else:
                if GITHUB_APP_SLUG:
                    st.caption(f"❌ GitHub App is NOT installed for this user. Install it here: https://github.com/apps/{GITHUB_APP_SLUG}")
                else:
                    st.caption("❌ GitHub App is NOT installed for this user. Install the app on their GitHub account to enable publishing.")

        # Auto repo based on brand + month + year and LOCK it
        current_brand = st.session_state.get("brand_table", "Action Network")
        auto_repo = suggested_repo_name(current_brand)
        st.session_state["bt_gh_repo"] = auto_repo
        repo_name = auto_repo

        # Widget file name
        widget_file_name = st.text_input(
            "Widget Name (file)",
            value=st.session_state.get("bt_widget_file_name", "table.html"),
            key="bt_widget_file_name",
            disabled=False,
            help="Example: top10-supermoon-states.html",
        ).strip()

        if widget_file_name and not widget_file_name.lower().endswith(".html"):
            widget_file_name = widget_file_name + ".html"
            st.session_state["bt_widget_file_name"] = widget_file_name

        # File existence check
        file_exists = False
        existing_pages_url = ""
        if effective_github_user and installation_token and repo_name and widget_file_name:
            file_exists = github_file_exists(effective_github_user, repo_name, installation_token, widget_file_name, branch="main")
            if file_exists:
                existing_pages_url = compute_pages_url(effective_github_user, repo_name, widget_file_name)

        # ✅ override logic (SWAP)
        allow_swap = bool(st.session_state.get("bt_allow_swap", False))
        swap_text = (st.session_state.get("bt_swap_confirm_text", "") or "").strip().upper()

        if file_exists:
            st.warning("⚠️ A page with this file name already exists. Publishing will overwrite it if you allow swap.")
            if existing_pages_url:
                st.markdown(f"✅ **Existing Page:** {existing_pages_url}")

            st.caption("To overwrite safely, you must enable override and type **SWAP**.")
            st.checkbox(
                "Yes, I want to override (replace) the existing page",
                value=allow_swap,
                key="bt_allow_swap",
            )
            if st.session_state.get("bt_allow_swap", False):
                st.text_input(
                    'Type "SWAP" to confirm override',
                    value=st.session_state.get("bt_swap_confirm_text", ""),
                    key="bt_swap_confirm_text",
                )

        swap_confirmed = (not file_exists) or (st.session_state.get("bt_allow_swap", False) and swap_text == "SWAP")

        can_publish = bool(
            html_generated
            and effective_github_user
            and repo_name
            and widget_file_name
            and installation_token
            and swap_confirmed
        )

        publish_clicked = st.button(
            "🧩 Publish + Get IFrame",
            use_container_width=True,
            disabled=not can_publish,
        )

        if not can_publish:
            missing = []
            if not html_generated:
                missing.append("confirm+save (generate HTML)")
            if not effective_github_user:
                missing.append("select a user")
            if not widget_file_name:
                missing.append("file name")
            if effective_github_user and not installation_token:
                missing.append("GitHub App installed for this user")
            if file_exists and not swap_confirmed:
                missing.append("confirm override (checkbox + SWAP)")
            if missing:
                st.caption("To enable publishing: " + ", ".join(missing) + ".")

        if publish_clicked:
            try:
                html_final = st.session_state.get("bt_html_code", "")
                if not html_final:
                    raise RuntimeError("No generated HTML found. Click Confirm And Save first.")

                simulate_progress("Publishing to GitHub…", total_sleep=0.35)

                ensure_repo_exists(effective_github_user, repo_name, installation_token)

                try:
                    ensure_pages_enabled(effective_github_user, repo_name, installation_token, branch="main")
                except Exception:
                    pass

                upload_file_to_github(
                    effective_github_user,
                    repo_name,
                    installation_token,
                    widget_file_name,
                    html_final,
                    f"Add/Update {widget_file_name} from Branded Table App",
                    branch="main",
                )
                trigger_pages_build(effective_github_user, repo_name, installation_token)

                pages_url = compute_pages_url(effective_github_user, repo_name, widget_file_name)
                st.session_state["bt_last_published_url"] = pages_url

                st.session_state["bt_iframe_code"] = build_iframe_snippet(
                    pages_url,
                    height=int(st.session_state.get("bt_iframe_height", 800)),
                )

                st.success("Done. URL + IFrame are ready below.")

            except Exception as e:
                st.error(f"Publish / IFrame generation failed: {e}")

       # =========================================================
# ✅ OUTPUTS (CLEAN + NATIVE COPY ICON + CLEAR BUTTON)
# =========================================================
st.markdown("#### Outputs")

# ✅ Clear button (ONLY clears if clicked)
if st.button("🧹 Clear IFrame / Outputs", use_container_width=True, key="bt_clear_outputs"):
    st.session_state["bt_last_published_url"] = ""
    st.session_state["bt_iframe_code"] = ""
    st.success("Outputs cleared. Publish again when ready.")
    st.rerun()

published_url_val = (st.session_state.get("bt_last_published_url") or "").strip()
iframe_val = (st.session_state.get("bt_iframe_code") or "").strip()

# HARD RULE: If not published, show COMPLETELY EMPTY
if not published_url_val:
    iframe_val = ""

# ✅ Published URL output (copy icon appears automatically)
st.caption("Published URL")
if published_url_val:
    st.link_button("🔗 Open published page", published_url_val, use_container_width=True)

st.code(published_url_val or "", language="text")

# ✅ Iframe output (copy icon appears automatically)
st.caption("IFrame Code")
st.code(iframe_val or "", language="html")

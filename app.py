import base64
import datetime
import html as html_mod
import json
import re
import time
from collections.abc import Mapping

import jwt  # PyJWT
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


# GitHub App Secrets (store these in Streamlit secrets)
GITHUB_APP_ID = str(get_secret("GITHUB_APP_ID", "")).strip()
GITHUB_APP_PRIVATE_KEY = str(get_secret("GITHUB_APP_PRIVATE_KEY", "")).strip()
GITHUB_PAT = str(get_secret("GITHUB_PAT", "")).strip()

# optional (for showing install link)
GITHUB_APP_SLUG = str(get_secret("GITHUB_APP_SLUG", "")).strip().lower()  # e.g. "bcdprpagehoster"

# Publishing always happens under ONE account (Org or User)
PUBLISH_OWNER = str(get_secret("PUBLISH_OWNER", "BetterCollective26")).strip()


# =========================================================
# Repo Auto-Naming (Full Brand Name + Month + Year)
# =========================================================
BRAND_REPO_PREFIX_FULL = {
    "Action Network": "ActionNetwork",
    "Canada Sports Betting": "CanadaSportsBetting",
    "VegasInsider": "VegasInsider",
    "RotoGrinders": "RotoGrinders",
    "AceOdds": "AceOdds",
    "BOLAVIP": "BOLAVIP",
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
    return f"{prefix}t{mm}{yy}"


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
    if not app_id or not private_key_pem:
        raise RuntimeError("Missing GitHub App credentials (GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY).")

    now = int(time.time())
    payload = {
        "iat": now - 30,        # helps with clock skew
        "exp": now + (9 * 60),  # <= 10 mins
        "iss": app_id,
    }

    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8", errors="ignore")
    return token


def get_installation_id_for_account(account_name: str) -> int:
    """
    Returns GitHub App installation id for either a USER or ORG.
    Tries both endpoints:
      /users/{name}/installation
      /orgs/{name}/installation
    """
    name = (account_name or "").strip()
    if not name:
        return 0

    app_jwt = build_github_app_jwt(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)

    # Try user endpoint first
    r = requests.get(
        f"https://api.github.com/users/{name}/installation",
        headers=github_headers(app_jwt),
        timeout=20,
    )
    if r.status_code == 200:
        data = r.json() or {}
        return int(data.get("id", 0) or 0)

    # Then org endpoint
    r2 = requests.get(
        f"https://api.github.com/orgs/{name}/installation",
        headers=github_headers(app_jwt),
        timeout=20,
    )
    if r2.status_code == 200:
        data = r2.json() or {}
        return int(data.get("id", 0) or 0)

    # Not installed / no access
    if r.status_code in (404, 403) and r2.status_code in (404, 403):
        return 0

    raise RuntimeError(
        f"Error checking GitHub App installation: user({r.status_code}) org({r2.status_code})"
    )


@st.cache_data(ttl=50 * 60)
def get_installation_token_for_account(account_name: str) -> str:
    """
    Get an installation token for an account (user/org).
    Cached ~50 mins because token lifetime is ~1 hour.
    """
    install_id = get_installation_id_for_account(account_name)
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


def get_github_owner_type(owner: str, token: str) -> str:
    """
    Returns 'Organization' or 'User' (default 'User' if unknown).
    """
    owner = (owner or "").strip()
    if not owner:
        return "User"

    r = requests.get(
        f"https://api.github.com/users/{owner}",
        headers=github_headers(token),
        timeout=20,
    )
    if r.status_code == 200:
        data = r.json() or {}
        return str(data.get("type", "User"))
    return "User"


def ensure_repo_exists(owner: str, repo: str, install_token: str) -> bool:
    """
    Ensures repo exists under owner/repo. Uses install_token for read checks.
    If missing -> creates using PAT (and correct endpoint for org/user).
    Returns True if created, False if already exists.
    """
    api_base = "https://api.github.com"
    owner = (owner or "").strip()
    repo = (repo or "").strip()

    # 1) check repo exists (using install token)
    r = requests.get(
        f"{api_base}/repos/{owner}/{repo}",
        headers=github_headers(install_token),
        timeout=20,
    )
    if r.status_code == 200:
        return False

    if r.status_code != 404:
        raise RuntimeError(f"Error checking repo: {r.status_code} {r.text}")

    # 2) create repo using PAT
    if not GITHUB_PAT:
        raise RuntimeError("Repo does not exist and cannot be created because GITHUB_PAT is missing in secrets.")

    owner_type = get_github_owner_type(owner, GITHUB_PAT)

    payload = {
        "name": repo,
        "auto_init": True,
        "private": False,
        "description": "Branded Searchable Table (Auto-Created By Streamlit App).",
    }

    if owner_type == "Organization":
        create_url = f"{api_base}/orgs/{owner}/repos"
    else:
        create_url = f"{api_base}/user/repos"

    r2 = requests.post(
        create_url,
        headers=github_headers(GITHUB_PAT),
        json=payload,
        timeout=20,
    )

    if r2.status_code not in (200, 201):
        raise RuntimeError(f"Error creating repo: {r2.status_code} {r2.text}")

    return True


def ensure_pages_enabled(owner: str, repo: str, token: str, branch: str = "main") -> None:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = requests.get(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, timeout=20)
    if r.status_code == 200:
        return

    if r.status_code == 403:
        # no permissions to enable; skip
        return

    if r.status_code != 404:
        raise RuntimeError(f"Error checking GitHub Pages: {r.status_code} {r.text}")

    payload = {"source": {"branch": branch, "path": "/"}}
    r2 = requests.post(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, json=payload, timeout=20)

    # GitHub Pages enabling sometimes returns 201 or 202
    if r2.status_code not in (201, 202):
        raise RuntimeError(f"Error enabling GitHub Pages: {r2.status_code} {r2.text}")


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

    path = (path or "").lstrip("/").strip()
    get_url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(get_url, headers=headers, params={"ref": branch}, timeout=20)

    sha = None
    if r.status_code == 200:
        sha = (r.json() or {}).get("sha")
    elif r.status_code != 404:
        raise RuntimeError(f"Error checking file: {r.status_code} {r.text}")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha

    r2 = requests.put(get_url, headers=headers, json=payload, timeout=20)
    if r2.status_code not in (200, 201):
        raise RuntimeError(f"Error uploading file: {r2.status_code} {r2.text}")


def github_file_exists(owner: str, repo: str, token: str, path: str, branch: str = "main") -> bool:
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


def read_github_json(owner: str, repo: str, token: str, path: str, branch: str = "main") -> dict:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    path = (path or "").lstrip("/").strip()
    if not path:
        return {}

    url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=headers, params={"ref": branch}, timeout=20)

    if r.status_code == 404:
        return {}
    if r.status_code != 200:
        raise RuntimeError(f"Error reading JSON: {r.status_code} {r.text}")

    data = r.json() or {}
    content_b64 = data.get("content", "")
    if not content_b64:
        return {}

    raw = base64.b64decode(content_b64).decode("utf-8", errors="ignore").strip()
    if not raw:
        return {}

    try:
        return json.loads(raw)
    except Exception:
        return {}


def write_github_json(owner: str, repo: str, token: str, path: str, payload: dict, message: str, branch: str = "main") -> None:
    content = json.dumps(payload or {}, indent=2, ensure_ascii=False)
    upload_file_to_github(owner, repo, token, path, content, message, branch=branch)


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
    elif brand_clean == "AceOdds":
        meta["brand_class"] = "brand-aceodds"
        meta["logo_url"] = "https://i.postimg.cc/RVhccmQc/aceodds-logo-original-1.png"
        meta["logo_alt"] = "AceOdds Logo"
    elif brand_clean == "BOLAVIP":
        meta["brand_class"] = "brand-bolavip"
        meta["logo_url"] = "https://i.postimg.cc/KzqsN24t/bolavip-logo-black.png"
        meta["logo_alt"] = "BOLAVIP Logo"

    return meta


# =========================================================
# HTML Template (UPDATED + WORKING DOWNLOADS)
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

      --ctrl-font: 13px;
      --ctrl-pad-y: 7px;
      --ctrl-pad-x: 10px;
      --ctrl-radius: 10px;
      --ctrl-gap: 8px;

      --table-max-h: 680px;

      --bar-fixed-w: [[BAR_FIXED_W]]px;
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

    .vi-table-embed.brand-bolavip{
      --brand-50:#FFF1F2;
      --brand-100:#FFE1E4;
      --brand-300:#FDA4AF;
      --brand-500:#D81F30;
      --brand-600:#BE1B2A;
      --brand-700:#9F1622;
      --brand-900:#5F0C12;
      --brand-500-rgb: 216, 31, 48;

      --header-bg:var(--brand-600);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
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

    .vi-table-embed.brand-aceodds{
      --brand-50:#F1F3F7;
      --brand-100:#D9DEE8;
      --brand-300:#AEB8CB;
      --brand-500:#364464;
      --brand-600:#2E3A56;
      --brand-700:#242E45;
      --brand-900:#131A2B;
      --brand-500-rgb: 54, 68, 100;

      --header-bg:var(--brand-600);
      --stripe:var(--brand-50);
      --hover:var(--brand-100);
      --scroll-thumb:var(--brand-600);
      --footer-border: rgba(var(--brand-500-rgb), 0.40);
    }

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

    #bt-block, #bt-block * { box-sizing:border-box; }
    #bt-block{
      --bg:#ffffff; --text:#1f2937;
      --gutter: 12px;
      padding: 10px var(--gutter);
      padding-top: 10px;
    }

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

    #bt-block .dw-field{ position:relative; min-width:0; width:100%; }

    #bt-block .dw-input,
    #bt-block .dw-select,
    #bt-block .dw-btn{
      font: var(--ctrl-font)/1.1 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      border-radius: var(--ctrl-radius);
      padding: var(--ctrl-pad-y) var(--ctrl-pad-x);
      transition:.15s ease;
    }

    #bt-block .dw-input{
      width: 100%;
      max-width: 260px;
      min-width: 120px;
      padding-right: 34px;
      background:#fff;
      border:1px solid var(--brand-700);
      color:var(--text);
      box-shadow:inset 0 1px 2px rgba(16,24,40,.04);
    }

    @media (max-width: 520px){
      #bt-block{
        --ctrl-gap: 6px;
        --ctrl-font: 12px;
        --ctrl-pad-y: 6px;
        --ctrl-pad-x: 8px;
      }
      #bt-block .dw-input{
        max-width: 140px;
        min-width: 85px;
      }
      #bt-block .dw-pager .dw-status{ display:none; }
      #bt-block .dw-btn.dw-download{
        font-size: 0;
        padding-inline: 10px;
      }
      #bt-block .dw-btn.dw-download::after{
        content:"Embed";
        font-size: 12px;
        font-weight: 600;
      }
    }

    @media (max-width: 330px){
      #bt-block .dw-controls{
        grid-template-columns: 1fr;
        row-gap: 10px;
      }
      #bt-block .right{
        justify-content:flex-start;
        flex-wrap:wrap;
        white-space:normal;
      }
    }

    #bt-block .dw-input::placeholder{color:#9AA4B2}
    #bt-block .dw-input:focus,
    #bt-block .dw-select:focus{
      outline:none;
      border-color:var(--brand-500);
      box-shadow:0 0 0 3px rgba(var(--brand-500-rgb), .22);
      background:#fff;
    }

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

    #bt-block .dw-clear{
      position:absolute; right:9px; top:50%; translate:0 -50%;
      width:20px; height:20px; border-radius:9999px; border:0;
      background:transparent; color:var(--brand-700);
      cursor:pointer; display:none; align-items:center; justify-content:center;
    }
    #bt-block .dw-field.has-value .dw-clear{display:flex}
    #bt-block .dw-clear:hover{background:var(--brand-100)}

    #bt-block .dw-card{
      background: var(--bg);
      border: 0;
      box-shadow: none;
      margin: 0;
      width: 100%;
      overflow: visible;
    }

    #bt-block .dw-scroll{
      max-height: min(var(--table-max-h, 680px), calc(100vh - 240px));
      overflow: auto;
      -webkit-overflow-scrolling: touch;
      touch-action: pan-x pan-y;
      overscroll-behavior: auto;
      scrollbar-gutter: stable both-edges;

      scrollbar-width: thin;
      scrollbar-color: var(--scroll-thumb) transparent;
    }

    #bt-block .dw-scroll::-webkit-scrollbar{ width: 8px; height: 8px; }
    #bt-block .dw-scroll::-webkit-scrollbar-track{ background: transparent; }
    #bt-block .dw-scroll::-webkit-scrollbar-thumb{
      background: var(--scroll-thumb);
      border-radius: 9999px;
      border: 2px solid transparent;
      background-clip: content-box;
    }
    #bt-block .dw-scroll::-webkit-scrollbar-thumb:hover{ background: var(--brand-600); }

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
      overflow-wrap: normal;
      word-break: normal;
      line-height: 1.35;

      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;

      overflow:hidden;
      text-overflow:ellipsis;
    }

    #bt-block th.dw-bar-col,
    #bt-block td.dw-bar-td{
      min-width: calc(var(--bar-fixed-w) + 70px);
    }

    #bt-block .dw-bar-wrap{
      width: min(var(--bar-fixed-w), 100%);
      margin: 0 auto;
      display:block;
    }

    #bt-block .dw-bar-track{
      position: relative;
      width: 100%;
      height: 18px;
      background: rgba(0,0,0,.07);
      border-radius: 999px;
      overflow: hidden;
    }

    #bt-block .dw-bar-fill{
      position:absolute;
      top:0; left:0; bottom:0;
      width:0%;
      background: var(--brand-600);
      border-radius: 999px;
      transition: width .2s ease;
    }

    #bt-block .dw-bar-text{
      position:relative;
      z-index:2;
      height:100%;
      display:flex;
      align-items:center;
      justify-content:flex-end;
      padding-right: 6px;
    }

    #bt-block .dw-bar-pill{
      font-size: 12px;
      font-weight: 750;
      line-height: 1;
      padding: 2px 7px;
      border-radius: 999px;
      background: rgba(0,0,0,.55);
      color: #ffffff;
      white-space: nowrap;
      max-width: 100%;
    }

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
    .vi-table-embed.brand-bolavip .vi-footer img{ filter: none !important; height: 28px; width: auto; display: inline-block; }
    .vi-table-embed.brand-aceodds .vi-footer img{ filter: none !important; height: 28px; width: auto; display: inline-block; }

    .vi-hide{ display:none !important; }

    /* EXPORT MODE */
    .vi-table-embed.export-mode .vi-table-header{ display:none !important; }
    .vi-table-embed.export-mode #bt-block .dw-controls,
    .vi-table-embed.export-mode #bt-block .dw-page-status{ display:none !important; }
    .vi-table-embed.export-mode #bt-block .dw-scroll{ max-height:none !important; height:auto !important; overflow:visible !important; }
    .vi-table-embed.export-mode #bt-block thead th{ position:static !important; }
    .vi-table-embed.export-mode #bt-block tbody tr:hover,
    .vi-table-embed.export-mode #bt-block tbody tr:hover td{ transform:none !important; box-shadow:none !important; }
    .vi-table-embed.export-mode #bt-block table.dw-table{ table-layout:fixed !important; width:100% !important; }
    .vi-table-embed.export-mode #bt-block .dw-scroll.no-scroll{ overflow-x:hidden !important; }
  </style>

  <div class="vi-table-header [[HEADER_ALIGN_CLASS]] [[HEADER_VIS_CLASS]]">
    <span class="title [[TITLE_CLASS]]">[[TITLE]]</span>
    <span class="subtitle">[[SUBTITLE]]</span>
  </div>

  <div id="bt-block" data-dw="table">
    <div class="dw-controls [[CONTROLS_VIS_CLASS]]">
      <div class="left">
        <div class="dw-field [[SEARCH_VIS_CLASS]]">
          <input type="search" class="dw-input" placeholder="Search Table…" aria-label="Search Table">
          <button type="button" class="dw-clear" aria-label="Clear Search">×</button>
        </div>
      </div>

      <div class="right">
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

        <div class="dw-embed [[EMBED_VIS_CLASS]]">
          <button class="dw-btn dw-download" id="dw-download-png" type="button">Embed / Download</button>

          <div id="dw-download-menu" class="dw-download-menu vi-hide" aria-label="Download Menu">
            <div class="dw-menu-title" id="dw-menu-title">Choose action</div>
            <button type="button" class="dw-menu-btn" id="dw-dl-top10">Download Top 10 (PNG)</button>
            <button type="button" class="dw-menu-btn" id="dw-dl-bottom10">Download Bottom 10 (PNG)</button>
            <button type="button" class="dw-menu-btn" id="dw-dl-csv">Download CSV (filtered)</button>
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

    const section = document.querySelector('.vi-table-embed');
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
    const btnCsv = embedWrap ? embedWrap.querySelector('#dw-dl-csv') : null;
    const btnEmbed = embedWrap ? embedWrap.querySelector('#dw-embed-script') : null;

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

    // =============================
    // ✅ DOWNLOAD / COPY FUNCTIONS
    // =============================
    function getAllFilteredRows(){
      const ordered = Array.from(tb.rows).filter(r=>!r.classList.contains('dw-empty'));
      return ordered.filter(matchesFilter);
    }

    function downloadBlob(blob, filename){
      const a = document.createElement('a');
      const url = URL.createObjectURL(blob);
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(()=>URL.revokeObjectURL(url), 4000);
    }

    function rowsToCSV(rows){
      const header = heads.map(h => `"${(h.innerText||"").replaceAll('"','""')}"`).join(",");
      const lines = rows.map(r=>{
        const tds = Array.from(r.cells);
        return tds.map(td => `"${(td.innerText||"").trim().replaceAll('"','""')}"`).join(",");
      });
      return [header, ...lines].join("\n");
    }

    async function captureRowsAsPng(rows, filename){
      try{
        // Build a lightweight export container
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.left = '-99999px';
        container.style.top = '0';
        container.style.width = '1200px';
        container.style.background = '#ffffff';
        container.style.padding = '12px';

        const cloneSection = section.cloneNode(true);
        cloneSection.classList.add('export-mode');

        // Replace tbody with selected rows only
        const cloneTable = cloneSection.querySelector('table.dw-table');
        const cloneTbody = cloneTable.tBodies[0];
        const cloneEmpty = cloneTbody.querySelector('.dw-empty');
        if(cloneEmpty) cloneEmpty.remove();

        // wipe all rows
        Array.from(cloneTbody.rows).forEach(r=>r.remove());

        // add selected clones
        rows.forEach(r=>{
          cloneTbody.appendChild(r.cloneNode(true));
        });

        // remove controls from clone (extra safety)
        const ctrl = cloneSection.querySelector('.dw-controls');
        if(ctrl) ctrl.remove();

        container.appendChild(cloneSection);
        document.body.appendChild(container);

        const canvas = await html2canvas(cloneSection, {
          backgroundColor: "#ffffff",
          scale: 2,
          useCORS: true,
        });

        canvas.toBlob(blob=>{
          if(blob) downloadBlob(blob, filename);
          container.remove();
        }, "image/png");

      }catch(err){
        console.error(err);
        alert("Could not export PNG. Check console for details.");
      }
    }

    async function copyEmbedHTML(){
      try{
        const html = section.outerHTML;
        await navigator.clipboard.writeText(html);
        alert("Copied HTML to clipboard.");
      }catch(err){
        console.error(err);
        alert("Copy failed. Your browser may block clipboard access.");
      }
    }

    function downloadFilteredCSV(){
      const rows = getAllFilteredRows();
      const csv = rowsToCSV(rows);
      const blob = new Blob([csv], {type:"text/csv;charset=utf-8"});
      downloadBlob(blob, "table.csv");
    }

    if(btnTop10){
      btnTop10.addEventListener('click', ()=>{
        hideMenu();
        const rows = getAllFilteredRows().slice(0,10);
        captureRowsAsPng(rows, "top10.png");
      });
    }

    if(btnBottom10){
      btnBottom10.addEventListener('click', ()=>{
        hideMenu();
        const all = getAllFilteredRows();
        const rows = all.slice(Math.max(0, all.length - 10));
        captureRowsAsPng(rows, "bottom10.png");
      });
    }

    if(btnCsv){
      btnCsv.addEventListener('click', ()=>{
        hideMenu();
        downloadFilteredCSV();
      });
    }

    if(btnEmbed){
      btnEmbed.addEventListener('click', ()=>{
        hideMenu();
        copyEmbedHTML();
      });
    }

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
    bar_columns: list[str] | None = None,
    bar_max_overrides: dict | None = None,
    bar_fixed_w: int = 200,
) -> str:
    df = df.copy()
    bar_columns_set = set(bar_columns or [])
    bar_max_overrides = bar_max_overrides or {}

    # clamp
    try:
        bar_fixed_w = int(bar_fixed_w)
    except Exception:
        bar_fixed_w = 200
    bar_fixed_w = max(120, min(360, bar_fixed_w))

    def parse_number(v) -> float:
        try:
            s = "" if pd.isna(v) else str(v)
            s = s.replace(",", "")
            s = re.sub(r"[^0-9.\-]", "", s)
            return float(s) if s else 0.0
        except Exception:
            return 0.0

    # bar max per col
    bar_max = {}
    for col in df.columns:
        if col in bar_columns_set:
            override_val = bar_max_overrides.get(col)

            try:
                if override_val is not None and str(override_val).strip() != "":
                    ov = float(str(override_val).strip())
                    if ov > 0:
                        bar_max[col] = ov
                        continue
            except Exception:
                pass

            try:
                vals = df[col].apply(parse_number)
                m = float(vals.max()) if len(vals) else 0.0
                bar_max[col] = m if m > 0 else 1.0
            except Exception:
                bar_max[col] = 1.0

    # header
    head_cells = []
    for col in df.columns:
        col_type = guess_column_type(df[col])
        safe_label = html_mod.escape(str(col))
        is_bar_col = (col in bar_columns_set and col_type == "num")
        bar_class = "dw-bar-col" if is_bar_col else ""
        head_cells.append(f'<th scope="col" data-type="{col_type}" class="{bar_class}">{safe_label}</th>')

    table_head_html = "\n              ".join(head_cells)

    # rows
    row_html_snippets = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = "" if pd.isna(row[col]) else str(row[col])
            safe_val = html_mod.escape(val)
            safe_title = html_mod.escape(val, quote=True)

            if col in bar_columns_set and guess_column_type(df[col]) == "num":
                num_val = parse_number(row[col])
                denom = bar_max.get(col, 1.0) or 1.0
                pct = max(0.0, min(100.0, (num_val / denom) * 100.0))

                cells.append(
                    f"""
                    <td class="dw-bar-td">
                      <div class="dw-bar-wrap" title="{safe_title}">
                        <div class="dw-bar-track">
                          <div class="dw-bar-fill" style="width:{pct:.2f}%;"></div>
                          <div class="dw-bar-text">
                            <span class="dw-bar-pill">{safe_val}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    """
                )
            else:
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
        footer_align_class = ""  # right

    cell_align = (cell_align or "Center").strip().lower()
    if cell_align == "left":
        cell_align_class = "align-left"
    elif cell_align == "right":
        cell_align_class = "align-right"
    else:
        cell_align_class = "align-center"

    html_out = (
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
        .replace("[[BAR_FIXED_W]]", str(bar_fixed_w))
    )
    return html_out


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
        "bar_columns": st.session_state.get("bt_bar_columns", []),
        "bar_max_overrides": st.session_state.get("bt_bar_max_overrides", {}),
        "bar_fixed_w": st.session_state.get("bt_bar_fixed_w", 200),
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
        bar_columns=cfg.get("bar_columns", []),
        bar_max_overrides=cfg.get("bar_max_overrides", {}),
        bar_fixed_w=cfg.get("bar_fixed_w", 200),
    )


def compute_pages_url(owner: str, repo: str, filename: str) -> str:
    owner = (owner or "").strip()
    repo = (repo or "").strip()
    filename = (filename or "").lstrip("/").strip() or "table.html"
    return f"https://{owner}.github.io/{repo}/{filename}"


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


def wait_until_pages_live(url: str, timeout_sec: int = 90, interval_sec: float = 2.0) -> bool:
    if not url:
        return False

    end_time = time.time() + timeout_sec
    while time.time() < end_time:
        try:
            r = requests.get(url, timeout=10, headers={"Cache-Control": "no-cache"})
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval_sec)

    return False


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
        "bt_gh_repo",
        "bt_confirm_flash",
        "bt_df_uploaded",
        "bt_df_confirmed",
        "bt_allow_swap",
        "bt_bar_columns",
        "bt_bar_max_overrides",
        "bt_bar_fixed_w",
        "bt_embed_tabs_visible",
        "bt_table_name_words",
        "bt_uploaded_name",
        "bt_bar_add_choice",
        "bt_bar_columns_holder",
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

    st.session_state.setdefault("bt_footer_logo_align", "Center")
    st.session_state.setdefault("bt_widget_file_name", "table.html")

    st.session_state.setdefault("bt_confirm_flash", False)

    st.session_state.setdefault("bt_show_embed", True)
    st.session_state.setdefault("bt_allow_swap", False)

    st.session_state.setdefault("bt_bar_columns", [])
    st.session_state.setdefault("bt_bar_max_overrides", {})
    st.session_state.setdefault("bt_bar_fixed_w", 200)

    st.session_state.setdefault("bt_bar_add_choice", "Select a column...")
    st.session_state.setdefault("bt_bar_columns_holder", st.session_state.get("bt_bar_columns", []))


def do_confirm_snapshot():
    st.session_state["bt_df_confirmed"] = st.session_state["bt_df_uploaded"].copy()

    cfg = draft_config_from_state()
    st.session_state["bt_confirmed_cfg"] = cfg
    st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)

    html_code = html_from_config(st.session_state["bt_df_confirmed"], st.session_state["bt_confirmed_cfg"])
    st.session_state["bt_html_code"] = html_code
    st.session_state["bt_html_generated"] = True
    st.session_state["bt_html_hash"] = st.session_state["bt_confirmed_hash"]

    st.session_state["bt_confirm_flash"] = True


# =========================================================
# Streamlit App (ONE TIME ONLY)
# =========================================================
st.set_page_config(page_title="Branded Table Generator", layout="wide")
st.title("Branded Table Generator")

# =========================================================
# Created by (mandatory before upload)
# =========================================================
created_by_options = ["Select a user..."] + list(PUBLISH_USERS)
st.session_state.setdefault("bt_created_by_user_select", "Select a user...")

created_by_input_global = st.selectbox(
    "Created by (tracking only)",
    options=created_by_options,
    key="bt_created_by_user_select",
)

created_by_user_global = ""
if created_by_input_global and created_by_input_global != "Select a user...":
    created_by_user_global = created_by_input_global.strip().lower()

st.session_state["bt_created_by_user"] = created_by_user_global

uploaded_file = st.file_uploader(
    "Upload Your CSV File",
    type=["csv"],
    disabled=not bool(created_by_user_global),
)

if not created_by_user_global:
    st.info("Select **Created by** to enable CSV upload.")
    st.stop()

brand_options = [
    "Action Network",
    "VegasInsider",
    "Canada Sports Betting",
    "RotoGrinders",
    "AceOdds",
    "BOLAVIP",
]
brand_select_options = ["Choose a brand..."] + brand_options
st.session_state.setdefault("brand_table", "Choose a brand...")

brand_selected_global = st.selectbox(
    "Brand",
    options=brand_select_options,
    key="brand_table",
)

if brand_selected_global == "Choose a brand...":
    st.info("Choose a **Brand** to load the table preview.")
    st.stop()

if uploaded_file is None:
    st.info("Upload a CSV to start.")
    st.stop()

try:
    df_uploaded_now = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    st.stop()

if df_uploaded_now.empty:
    st.error("Uploaded CSV has no rows.")
    st.stop()

# =========================================================
# ✅ Track Upload + Reset If New File
# =========================================================
uploaded_name = getattr(uploaded_file, "name", "") or "uploaded.csv"
prev_uploaded = st.session_state.get("bt_uploaded_name", "")

if prev_uploaded and prev_uploaded != uploaded_name:
    reset_widget_state_for_new_upload()

st.session_state["bt_uploaded_name"] = uploaded_name
st.session_state["bt_df_uploaded"] = df_uploaded_now.copy()

ensure_confirm_state_exists()

# =========================================================
# ✅ Repo + Filename Defaults
# =========================================================
st.session_state.setdefault("bt_gh_repo", suggested_repo_name(brand_selected_global))
st.session_state.setdefault("bt_widget_file_name", "table.html")
st.session_state.setdefault("bt_widget_title", "Table 1")
st.session_state.setdefault("bt_widget_subtitle", "Subheading")

# =========================================================
# ✅ Sidebar Controls (Draft config)
# =========================================================
with st.sidebar:
    st.header("Table Settings")

    st.text_input("Title", key="bt_widget_title")
    st.text_input("Subtitle", key="bt_widget_subtitle")

    st.checkbox("Striped rows", key="bt_striped_rows", value=True)
    st.checkbox("Show header", key="bt_show_header", value=True)
    st.checkbox("Center titles", key="bt_center_titles", value=False)
    st.checkbox("Branded title color", key="bt_branded_title_color", value=True)

    st.checkbox("Show footer", key="bt_show_footer", value=True)
    st.selectbox("Footer logo align", ["Left", "Center", "Right"], key="bt_footer_logo_align")

    st.selectbox("Cell align", ["Left", "Center", "Right"], key="bt_cell_align")

    st.checkbox("Show search", key="bt_show_search", value=True)
    st.checkbox("Show pager", key="bt_show_pager", value=True)
    st.checkbox("Show embed/download", key="bt_show_embed", value=True)
    st.checkbox("Show page numbers", key="bt_show_page_numbers", value=True)

    st.divider()
    st.subheader("Bar Columns")

    st.session_state.setdefault("bt_bar_fixed_w", 200)
    st.number_input("Bar width (px)", min_value=120, max_value=360, step=10, key="bt_bar_fixed_w")

    df_cols = list(st.session_state["bt_df_uploaded"].columns)
    col_pick = st.selectbox("Add numeric bar column", ["Select a column..."] + df_cols, key="bt_bar_add_choice")

    if st.button("Add Bar Column", use_container_width=True):
        if col_pick and col_pick != "Select a column...":
            current = list(st.session_state.get("bt_bar_columns", []))
            if col_pick not in current:
                current.append(col_pick)
            st.session_state["bt_bar_columns"] = current
            st.session_state["bt_bar_columns_holder"] = current

    current_bars = list(st.session_state.get("bt_bar_columns", []))
    if current_bars:
        st.caption("Bar columns enabled:")
        for c in current_bars:
            cols = st.columns([3, 2])
            cols[0].write(f"• **{c}**")
            if cols[1].button("Remove", key=f"rm_bar_{c}"):
                cur = [x for x in st.session_state.get("bt_bar_columns", []) if x != c]
                st.session_state["bt_bar_columns"] = cur
                st.session_state["bt_bar_columns_holder"] = cur

        st.subheader("Bar max overrides (optional)")
        overrides = dict(st.session_state.get("bt_bar_max_overrides", {}) or {})
        for c in current_bars:
            overrides.setdefault(c, "")
            overrides[c] = st.text_input(f"Max override for {c}", value=str(overrides.get(c, "")), key=f"ovr_{c}")
        st.session_state["bt_bar_max_overrides"] = overrides

# =========================================================
# ✅ Draft vs Confirmed Snapshot
# =========================================================
draft_cfg = draft_config_from_state()
confirmed_cfg = st.session_state.get("bt_confirmed_cfg", {})
confirmed_hash = st.session_state.get("bt_confirmed_hash", "")
draft_hash = stable_config_hash(draft_cfg)

meta = get_brand_meta(draft_cfg["brand"])

# =========================================================
# ✅ Main Layout
# =========================================================
st.subheader("1) Preview (Live Draft)")

preview_html = html_from_config(st.session_state["bt_df_uploaded"], draft_cfg)
components.html(preview_html, height=900, scrolling=True)

st.divider()

colA, colB = st.columns([1, 1])

with colA:
    st.subheader("2) Confirm Snapshot")
    st.caption("Confirm locks the CSV + settings into a publishable version.")

    if st.button("✅ Confirm This Version", use_container_width=True):
        simulate_progress("Locking snapshot…")
        do_confirm_snapshot()
        st.success("Confirmed snapshot saved ✅")

with colB:
    st.subheader("3) Current Status")
    is_confirmed = st.session_state.get("bt_html_generated", False) and st.session_state.get("bt_html_hash", "") == confirmed_hash
    st.write(f"**Draft changed?** {'Yes' if draft_hash != confirmed_hash else 'No'}")
    st.write(f"**Confirmed version ready?** {'Yes ✅' if is_confirmed else 'No'}")

# =========================================================
# ✅ Confirmed Preview + Downloads
# =========================================================
st.divider()
st.subheader("4) Confirmed Output (What will be published)")

if st.session_state.get("bt_html_generated", False):
    confirmed_html = st.session_state.get("bt_html_code", "")

    components.html(confirmed_html, height=900, scrolling=True)

    st.markdown("### Downloads")
    dl1, dl2, dl3 = st.columns([1, 1, 1])

    with dl1:
        st.download_button(
            "⬇️ Download HTML",
            data=confirmed_html.encode("utf-8"),
            file_name=st.session_state.get("bt_widget_file_name", "table.html"),
            mime="text/html",
            use_container_width=True,
        )

    with dl2:
        csv_bytes = st.session_state["bt_df_confirmed"].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Confirmed CSV",
            data=csv_bytes,
            file_name="data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl3:
        cfg_payload = {
            "created_by": st.session_state.get("bt_created_by_user", ""),
            "created_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "brand": draft_cfg["brand"],
            "repo": st.session_state.get("bt_gh_repo", ""),
            "filename": st.session_state.get("bt_widget_file_name", "table.html"),
            "config": st.session_state.get("bt_confirmed_cfg", {}),
        }
        st.download_button(
            "⬇️ Download Config JSON",
            data=json.dumps(cfg_payload, indent=2).encode("utf-8"),
            file_name="config.json",
            mime="application/json",
            use_container_width=True,
        )
else:
    st.info("Confirm a version first to generate the publishable output.")

# =========================================================
# ✅ Publishing Section (GitHub Pages)
# =========================================================
st.divider()
st.subheader("5) Publish to GitHub Pages")

st.caption(f"Publishing owner: **{PUBLISH_OWNER}**")

pub_left, pub_right = st.columns([1, 1])

with pub_left:
    st.text_input("Repo name", key="bt_gh_repo")
    st.text_input("Filename (html)", key="bt_widget_file_name")

with pub_right:
    st.info("Tip: repo auto-names using brand + month + year.\n\nExample: `ActionNetworktj26`")

can_publish = bool(st.session_state.get("bt_html_generated", False))

if not can_publish:
    st.warning("You must **Confirm Snapshot** before publishing.")
else:
    if not GITHUB_APP_ID or not GITHUB_APP_PRIVATE_KEY:
        st.error("Missing GitHub App secrets: GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY")
        st.stop()

    pub_button = st.button("🚀 Publish Confirmed Version", type="primary", use_container_width=True)

    if pub_button:
        try:
            simulate_progress("Getting installation token…")
            install_token = get_installation_token_for_account(PUBLISH_OWNER)

            if not install_token:
                st.error("GitHub App is not installed / no access to the publishing owner.")
                if GITHUB_APP_SLUG:
                    st.caption(f"Install link: https://github.com/apps/{GITHUB_APP_SLUG}/installations/new")
                st.stop()

            owner = PUBLISH_OWNER
            repo = (st.session_state.get("bt_gh_repo") or "").strip()
            filename = (st.session_state.get("bt_widget_file_name") or "table.html").strip()

            if not repo:
                st.error("Repo name is empty.")
                st.stop()

            if not filename.lower().endswith(".html"):
                st.error("Filename must end with .html (example: table.html)")
                st.stop()

            simulate_progress("Ensuring repo exists…")
            created_repo = ensure_repo_exists(owner, repo, install_token)

            simulate_progress("Ensuring GitHub Pages enabled…")
            ensure_pages_enabled(owner, repo, install_token, branch="main")

            # Upload HTML
            simulate_progress("Uploading HTML…")
            upload_file_to_github(
                owner=owner,
                repo=repo,
                token=install_token,
                path=filename,
                content=st.session_state.get("bt_html_code", ""),
                message=f"Publish table ({filename})",
                branch="main",
            )

            # Upload config.json
            cfg_payload = {
                "created_by": st.session_state.get("bt_created_by_user", ""),
                "created_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
                "brand": draft_cfg["brand"],
                "repo": repo,
                "filename": filename,
                "config": st.session_state.get("bt_confirmed_cfg", {}),
            }

            simulate_progress("Uploading config.json…")
            write_github_json(
                owner=owner,
                repo=repo,
                token=install_token,
                path="config.json",
                payload=cfg_payload,
                message="Update config.json",
                branch="main",
            )

            # Upload confirmed CSV snapshot
            simulate_progress("Uploading data.csv…")
            csv_content = st.session_state["bt_df_confirmed"].to_csv(index=False)
            upload_file_to_github(
                owner=owner,
                repo=repo,
                token=install_token,
                path="data.csv",
                content=csv_content,
                message="Update data.csv",
                branch="main",
            )

            # Compute Pages URL
            pages_url = compute_pages_url(owner, repo, filename)
            st.session_state["bt_last_published_url"] = pages_url

            simulate_progress("Waiting for Pages to go live…")
            is_live = wait_until_pages_live(pages_url, timeout_sec=90, interval_sec=2.0)

            if is_live:
                st.success("Published ✅ GitHub Pages is live.")
            else:
                st.warning("Published ✅ but Pages might still be building (usually takes a minute).")

            st.markdown("### Published URL")
            st.code(pages_url, language="text")

            iframe_code = build_iframe_snippet(pages_url, height=900)
            st.session_state["bt_iframe_code"] = iframe_code

            st.markdown("### Embed Iframe")
            st.code(iframe_code, language="html")

            if created_repo:
                st.caption("Repo was auto-created ✅")

        except Exception as e:
            st.error(f"Publishing failed: {e}")

# =========================================================
# ✅ Show last published embed if exists
# =========================================================
if st.session_state.get("bt_last_published_url"):
    st.divider()
    st.subheader("Last Published Embed Preview")
    url = st.session_state["bt_last_published_url"]
    components.html(build_iframe_snippet(url, height=900), height=920, scrolling=True)

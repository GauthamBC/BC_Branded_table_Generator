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
        raise RuntimeError(f"Error Checking Repo: {r.status_code} {r.text}")

    payload = {
        "name": repo,
        "auto_init": True,
        "private": False,
        "description": "Branded Searchable Table (Auto-Created By Streamlit App).",
    }
    r = requests.post(f"{api_base}/user/repos", headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error Creating Repo: {r.status_code} {r.text}")
    return True

def ensure_pages_enabled(owner: str, repo: str, token: str, branch: str = "main") -> None:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = requests.get(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers)
    if r.status_code == 200:
        return
    if r.status_code not in (404, 403):
        raise RuntimeError(f"Error Checking GitHub Pages: {r.status_code} {r.text}")
    if r.status_code == 403:
        return

    payload = {"source": {"branch": branch, "path": "/"}}
    r = requests.post(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, json=payload)
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
    params = {"ref": branch}
    r = requests.get(get_url, headers=headers, params=params)
    sha = None
    if r.status_code == 200:
        sha = r.json().get("sha")
    elif r.status_code not in (404,):
        raise RuntimeError(f"Error Checking File: {r.status_code} {r.text}")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha

    r = requests.put(get_url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error Uploading File: {r.status_code} {r.text}")

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
    raise RuntimeError(f"Error Checking Repo: {r.status_code} {r.text}")

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
    raise RuntimeError(f"Error Checking File: {r.status_code} {r.text}")

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
        "logo_alt": f"{brand_clean} Logo",
        "brand_class": "brand-actionnetwork",
    }

    if brand_clean == "Action Network":
        meta["brand_class"] = "brand-actionnetwork"
        meta["logo_url"] = "https://i.postimg.cc/x1nG117r/AN-final2-logo.png"
        meta["logo_alt"] = "Action Network Logo"
    elif brand_clean == "VegasInsider":
        meta["brand_class"] = "brand-vegasinsider"
        meta["logo_url"] = "https://i.postimg.cc/kGVJyXc1/VI-logo-final.png"
        meta["logo_alt"] = "VegasInsider Logo"
    elif brand_clean == "Canada Sports Betting":
        meta["brand_class"] = "brand-canadasb"
        meta["logo_url"] = "https://i.postimg.cc/ZKbrbPCJ/CSB-FN.png"
        meta["logo_alt"] = "Canada Sports Betting Logo"
    elif brand_clean == "RotoGrinders":
        meta["brand_class"] = "brand-rotogrinders"
        meta["logo_url"] = "https://i.postimg.cc/PrcJnQtK/RG-logo-Fn.png"
        meta["logo_alt"] = "RotoGrinders Logo"

    return meta

# ===================== HTML Template =====================
# (UNCHANGED: keep your template exactly as-is; omitted here for brevity)
# IMPORTANT: paste your existing HTML_TEMPLATE_TABLE here.
HTML_TEMPLATE_TABLE = r"""REPLACE_WITH_YOUR_EXISTING_TEMPLATE"""

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
    footer_logo_align: str = "Right",
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
    # confirmed snapshot defaults to whatever was uploaded initially
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
    st.session_state.setdefault("bt_confirm_flash", False)

def do_confirm_snapshot():
    # Freeze CONFIRMED data + CONFIRMED config in one click (no double-click)
    st.session_state["bt_df_confirmed"] = st.session_state["bt_df_draft"].copy()

    cfg = draft_config_from_state()
    st.session_state["bt_confirmed_cfg"] = cfg
    st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)

    # mark HTML stale if it exists
    if st.session_state.get("bt_html_generated", False):
        st.session_state["bt_html_stale"] = (
            st.session_state.get("bt_html_hash", "") != st.session_state.get("bt_confirmed_hash", "")
        )

    st.session_state["bt_confirm_flash"] = True

def generate_html_from_confirmed():
    cfg = st.session_state.get("bt_confirmed_cfg")
    dfc = st.session_state.get("bt_df_confirmed")
    if cfg is None or dfc is None:
        return
    html = html_from_config(dfc, cfg)
    st.session_state["bt_html_code"] = html
    st.session_state["bt_html_generated"] = True
    st.session_state["bt_html_hash"] = st.session_state.get("bt_confirmed_hash", "")

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
    "Choose A Brand",
    options=brand_options,
    index=brand_options.index(default_brand),
    key="brand_table",
)

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

df_draft = st.session_state["bt_df_draft"]
df_confirmed = st.session_state["bt_df_confirmed"]

# ===================== Layout =====================

left_col, right_col = st.columns([1, 3], gap="large")

# ---------- RIGHT: Editor + LIVE Preview (Draft) ----------
with right_col:
    with st.expander("Open Editor", expanded=False):
        edited_df = st.data_editor(
            st.session_state["bt_df_draft"],
            use_container_width=True,
            num_rows="dynamic",
            key="bt_data_editor",
        )
        # Keep draft always updated
        st.session_state["bt_df_draft"] = edited_df

        c1, c2 = st.columns(2)
        with c1:
            if st.button("↩️ Reset Draft To Uploaded CSV", use_container_width=True):
                st.session_state["bt_df_draft"] = st.session_state["bt_df_uploaded"].copy()
                st.rerun()
        with c2:
            st.caption("Edits Apply To The Draft Immediately. Confirm To Freeze A Snapshot For HTML/Publishing.")

    # ✅ LIVE PREVIEW: ALWAYS FROM DRAFT (DATA + SETTINGS)
    st.markdown("### Preview (Live Draft)")
    live_cfg = draft_config_from_state()
    live_preview_html = html_from_config(st.session_state["bt_df_draft"], live_cfg)
    components.html(live_preview_html, height=820, scrolling=True)

# ---------- LEFT: Tabs ----------
with left_col:
    tab_config, tab_html, tab_iframe = st.tabs(["Configure", "HTML", "IFrame"])

    # ===================== CONFIGURE TAB =====================
    with tab_config:
        st.markdown("#### Table Setup")

        # ✅ One-click confirm via callback (fixes “double click” feel)
        st.button(
            "✅ Confirm And Save Table Contents",
            key="bt_confirm_btn",
            use_container_width=True,
            on_click=do_confirm_snapshot,
        )

        # Show confirm success once
        if st.session_state.get("bt_confirm_flash", False):
            st.success("Saved. Confirmed Snapshot Updated (HTML Uses This Snapshot).")
            st.session_state["bt_confirm_flash"] = False

        sub_head, sub_body = st.tabs(["Header / Footer", "Body"])

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
                index=["Right", "Center", "Left"].index(st.session_state.get("bt_footer_logo_align", "Right")),
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

        # Informational state: whether draft differs from confirmed
        draft_hash = stable_config_hash(draft_config_from_state())
        confirmed_hash = st.session_state.get("bt_confirmed_hash", "")
        if draft_hash != confirmed_hash or not st.session_state["bt_df_draft"].equals(st.session_state["bt_df_confirmed"]):
            st.warning("Live Preview Reflects Draft. HTML/Publishing Uses The Last Confirmed Snapshot.")
        else:
            st.caption("Draft Matches Confirmed Snapshot.")

    # ===================== HTML TAB =====================
    with tab_html:
        st.markdown("#### HTML Generation (From Confirmed Snapshot)")

        html_generated = bool(st.session_state.get("bt_html_generated", False))
        html_hash = st.session_state.get("bt_html_hash", "")
        confirmed_hash = st.session_state.get("bt_confirmed_hash", "")

        confirmed_vs_html_stale = (html_generated and (html_hash != confirmed_hash))

        col_a, col_b = st.columns([1, 1])
        with col_a:
            get_html_clicked = st.button("📄 Get HTML Code", key="bt_get_html_code", use_container_width=True)
        with col_b:
            update_html_clicked = st.button(
                "♻️ Update HTML (Auto-Confirm + Regenerate)",
                key="bt_update_html",
                use_container_width=True,
            )

        if html_generated and not confirmed_vs_html_stale:
            st.success("HTML Is Up To Date With The Confirmed Snapshot.")
        elif html_generated and confirmed_vs_html_stale:
            st.warning("HTML Is Out Of Date Vs Confirmed Snapshot. Click Update HTML.")
        else:
            st.caption("Click Get HTML Code To Generate HTML From The Confirmed Snapshot.")

        if get_html_clicked:
            simulate_progress("Generating HTML From Confirmed Snapshot…", total_sleep=0.35)
            generate_html_from_confirmed()
            st.success("HTML Generated From Confirmed Snapshot.")

        if update_html_clicked:
            simulate_progress("Confirming Draft Snapshot…", total_sleep=0.25)
            do_confirm_snapshot()
            simulate_progress("Updating HTML…", total_sleep=0.35)
            generate_html_from_confirmed()
            st.success("Confirmed Snapshot Updated And HTML Regenerated.")

        st.text_area(
            "HTML Code",
            value=st.session_state.get("bt_html_code", ""),
            height=420,
            placeholder="Generate HTML To See The Code Here.",
        )

    # ===================== IFRAME TAB =====================
    with tab_iframe:
        st.markdown("#### Publish + IFrame")

        html_generated = bool(st.session_state.get("bt_html_generated", False))
        html_hash = st.session_state.get("bt_html_hash", "")
        confirmed_hash = st.session_state.get("bt_confirmed_hash", "")

        html_stale = (html_generated and (html_hash != confirmed_hash))

        if not html_generated:
            st.warning("Generate HTML First (HTML Tab).")
        elif html_stale:
            st.warning("Your HTML Is Not Up To Date With The Confirmed Snapshot. Go To HTML Tab → Update HTML.")

        saved_gh_user = st.session_state.get("bt_gh_user", "")
        saved_gh_repo = st.session_state.get("bt_gh_repo", "branded-table-widget")

        username_options = ["GauthamBC", "ActionNetwork", "MoonWatcher", "SampleUser"]
        if GITHUB_USER_DEFAULT and GITHUB_USER_DEFAULT not in username_options:
            username_options.insert(0, GITHUB_USER_DEFAULT)

        default_idx = username_options.index(saved_gh_user) if saved_gh_user in username_options else 0
        github_username_input = st.selectbox(
            "Username (GitHub Username)",
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
        can_publish = bool(can_run_github and html_generated and (not html_stale))

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
                help="Disabled Until HTML Is Generated And Up-To-Date With Confirmed Snapshot.",
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
                    raise RuntimeError("No Generated HTML Found. Go To The HTML Tab And Generate It First.")

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
            help="Disabled Until HTML Is Generated.",
        )

        if get_iframe_clicked:
            simulate_progress("Generating IFrame…", total_sleep=0.25)
            st.session_state["bt_iframe_code"] = build_iframe_snippet(url_to_use, height=int(iframe_height))
            st.success("IFrame Code Generated.")

        st.text_area(
            "IFrame Code",
            value=st.session_state.get("bt_iframe_code", ""),
            height=200,
            placeholder="Generate HTML First, Then Generate IFrame Code Here.",
        )

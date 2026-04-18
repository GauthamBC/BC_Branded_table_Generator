import base64
import datetime
import hmac
import html as html_mod
import json
import re
import time
import requests
import io
import json
from collections.abc import Mapping

def inject_global_radio_button_css():
    """Render all Streamlit radio controls like full-width rectangle button groups.
    This is intentionally global so no individual radio falls back to the native dot UI.
    """
    st.markdown(
        """
        <style>

/* ✅ EMBED BUTTON STYLE SOURCE OF TRUTH
   Keep header, body, and footer triggers visually identical in the widget itself.
   The actual widget CSS below is the canonical source; this block only prevents
   Streamlit wrapper styles from dimming links or buttons around it. */
.vi-table-embed .vi-header-actions,
.vi-table-embed .footer-embed-wrap {
  opacity: 1 !important;
}

.vi-table-embed .vi-header-actions *,
.vi-table-embed .footer-embed-wrap * {
  text-decoration: none !important;
}

</style>
        """,
        unsafe_allow_html=True,
    )


def style_radio_as_big_tabs(
    radio_key: str,
    height_px: int = 58,
    radius_px: int = 12,
    font_px: int = 20,
    active_bg: str = "#FF5A5F",
    active_fg: str = "white",
    inactive_bg: str = "#FFFFFF",
    inactive_fg: str = "#2f3542",
    border: str = "1px solid rgba(0,0,0,0.12)",
    gap_px: int = 12,
):
    """Style a specific st.radio (by key) as a stretched full-width button group."""
    st.markdown(
        f"""
        <style>
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) {{
            width: 100% !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div > div {{
            width: 100% !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] {{
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            align-items: stretch !important;
            gap: {gap_px}px !important;
            width: 100% !important;
            min-width: 100% !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] {{
            width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: stretch !important;
            justify-content: stretch !important;
            border: 0 !important;
            background: transparent !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] > div:first-child,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] svg,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) input[name="{radio_key}"] {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] > div:last-child {{
            flex: 1 1 auto !important;
            width: 100% !important;
            min-width: 100% !important;
            min-height: {height_px}px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            padding: 0 18px !important;
            border: {border} !important;
            border-radius: {radius_px}px !important;
            background: {inactive_bg} !important;
            color: {inactive_fg} !important;
            font-weight: 700 !important;
            font-size: {font_px}px !important;
            line-height: 1.1 !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"]:hover > div:last-child {{
            border-color: rgba(0,0,0,0.22) !important;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08) !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) input[name="{radio_key}"]:checked + div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) label[data-baseweb="radio"][aria-checked="true"] > div:last-child {{
            background: {active_bg} !important;
            color: {active_fg} !important;
            border-color: {active_bg} !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) label[data-baseweb="radio"] p {{
            margin: 0 !important;
            width: 100% !important;
            text-align: center !important;
            font-size: {font_px}px !important;
            font-weight: 700 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_main_nav_tabs(radio_key: str):
    """Force the top main tabs to occupy the full available row as a 50/50 segmented bar."""
    st.markdown(
        f"""
        <style>
        /* Expand every ancestor wrapper around the main nav radio */
        div[data-testid="element-container"]:has(div[data-testid="stRadio"] input[name="{radio_key}"]),
        div[data-testid="stVerticalBlock"]:has(div[data-testid="stRadio"] input[name="{radio_key}"]),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stRadio"] input[name="{radio_key}"]),
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]),
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div > div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div > div > div {{
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            display: block !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            gap: 0 !important;
            border: 1px solid rgba(255, 90, 95, 0.22) !important;
            border-radius: 0 !important;
            overflow: hidden !important;
            background: #ffe9eb !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: stretch !important;
            justify-content: stretch !important;
            background: transparent !important;
            border: 0 !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] > div:last-child {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            min-height: 64px !important;
            border: 0 !important;
            border-radius: 0 !important;
            background: #ffe9eb !important;
            color: #7a1f28 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            font-size: 18px !important;
            font-weight: 700 !important;
            line-height: 1.15 !important;
            padding: 0 20px !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"]:not(:last-child) > div:last-child {{
            border-right: 1px solid rgba(255, 90, 95, 0.22) !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) input[name="{radio_key}"]:checked + div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) label[data-baseweb="radio"][aria-checked="true"] > div:last-child {{
            background: #FF5A5F !important;
            color: #ffffff !important;
            border: 0 !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"]:hover > div:last-child {{
            box-shadow: inset 0 0 0 9999px rgba(0,0,0,0.02) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )



def style_full_width_radio_tabs(
    radio_key: str,
    height_px: int = 64,
    radius_px: int = 12,
    font_px: int = 18,
    active_bg: str = "#FF5A5F",
    active_fg: str = "#ffffff",
    inactive_bg: str = "#FFFFFF",
    inactive_fg: str = "#2f3542",
    border: str = "1px solid rgba(0,0,0,0.12)",
    gap_px: int = 12,
):
    """Force a specific radio control to stretch full width across the available row."""
    st.markdown(
        f"""
        <style>
        div[data-testid="element-container"]:has(div[data-testid="stRadio"] input[name="{radio_key}"]),
        div[data-testid="stVerticalBlock"]:has(div[data-testid="stRadio"] input[name="{radio_key}"]),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stRadio"] input[name="{radio_key}"]),
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]),
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div > div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) > div > div > div {{
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            display: block !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] {{
            display: grid !important;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
            align-items: stretch !important;
            gap: {gap_px}px !important;
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: stretch !important;
            justify-content: stretch !important;
            border: 0 !important;
            background: transparent !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] > div:first-child,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] svg,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) input[name="{radio_key}"] {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"] > div:last-child {{
            flex: 1 1 auto !important;
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
            min-height: {height_px}px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            padding: 0 18px !important;
            border: {border} !important;
            border-radius: {radius_px}px !important;
            background: {inactive_bg} !important;
            color: {inactive_fg} !important;
            font-weight: 700 !important;
            font-size: {font_px}px !important;
            line-height: 1.1 !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) [role="radiogroup"] > label[data-baseweb="radio"]:hover > div:last-child {{
            border-color: rgba(0,0,0,0.22) !important;
            box-shadow: 0 3px 10px rgba(0,0,0,0.08) !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) input[name="{radio_key}"]:checked + div,
        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) label[data-baseweb="radio"][aria-checked="true"] > div:last-child {{
            background: {active_bg} !important;
            color: {active_fg} !important;
            border-color: {active_bg} !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"]:has(input[name="{radio_key}"]) label[data-baseweb="radio"] p {{
            margin: 0 !important;
            width: 100% !important;
            text-align: center !important;
            font-size: {font_px}px !important;
            font-weight: 700 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
import jwt  # ✅ PyJWT
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

inject_global_radio_button_css()

st.markdown(
    """
    <style>
    div[data-testid="stButton"]:has(button[key="main_tab_btn_create"]),
    div[data-testid="stButton"]:has(button[key="main_tab_btn_published"]),
    div[data-testid="stButton"]:has(button[key="bt_login_btn"]),
    div[data-testid="stButton"]:has(button[key="bt_logout_btn"]),
    div[data-testid="stButton"]:has(button[key="bt_left_edit_btn"]),
    div[data-testid="stButton"]:has(button[key="bt_left_embed_btn"]),
    div[data-testid="stButton"]:has(button[key="bt_right_preview_btn"]),
    div[data-testid="stButton"]:has(button[key="bt_right_body_btn"]) {
        width: 100% !important;
    }

    div[data-testid="stButton"]:has(button[key="main_tab_btn_create"]) > button,
    div[data-testid="stButton"]:has(button[key="main_tab_btn_published"]) > button,
    div[data-testid="stButton"]:has(button[key="bt_login_btn"]) > button,
    div[data-testid="stButton"]:has(button[key="bt_logout_btn"]) > button,
    div[data-testid="stButton"]:has(button[key="bt_left_edit_btn"]) > button,
    div[data-testid="stButton"]:has(button[key="bt_left_embed_btn"]) > button,
    div[data-testid="stButton"]:has(button[key="bt_right_preview_btn"]) > button,
    div[data-testid="stButton"]:has(button[key="bt_right_body_btn"]) > button {
        width: 100% !important;
        min-height: 64px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        white-space: normal !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_resource
def http_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST", "PUT", "DELETE"),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s



def style_radio_as_tabs(
    radio_key: str,
    active_bg: str = "#FF5A5F",
    active_border: str = "#FF5A5F",
):
    """Alias kept for compatibility; uses the same full-width rectangle button styling."""
    style_radio_as_big_tabs(
        radio_key=radio_key,
        height_px=52,
        radius_px=12,
        font_px=16,
        active_bg=active_bg,
        active_fg="white",
        inactive_bg="#FFFFFF",
        inactive_fg="#2f3542",
        border=f"1px solid {active_border if active_border else 'rgba(0,0,0,0.12)'}",
    )


# =========================================================
# ✅ Text case helpers (Title/Sub-title/Header case)
# =========================================================

def apply_text_case(text: str, style: str) -> str:
    """Apply a simple text casing rule.

    Styles expected: Keep original | ALL CAPS | Title Case | Sentence case
    """
    s = "" if text is None else str(text)
    style = (style or "").strip()

    if style in ("", "Keep original"):
        return s
    if s == "":
        return s

    if style == "ALL CAPS":
        return s.upper()

    if style == "Sentence case":
        s2 = s.strip()
        if not s2:
            return s
        low = s2.lower()
        for idx, ch in enumerate(low):
            if ch.isalpha():
                return low[:idx] + ch.upper() + low[idx + 1 :]
        return low

    if style == "Title Case":
        return s.title()

    return s


def wrap_text_by_words(text: str, words_per_line: int) -> str:
    """Wrap text into lines containing up to `words_per_line` words each."""
    s = "" if text is None else str(text).strip()
    try:
        words_per_line = int(words_per_line)
    except Exception:
        words_per_line = 0

    if not s or words_per_line <= 0:
        return s

    words = s.split()
    if not words:
        return s

    return "\n".join(
        " ".join(words[i:i + words_per_line])
        for i in range(0, len(words), words_per_line)
    )


def should_force_two_line_numeric_header(series, header_text: str) -> bool:
    """Auto-wrap a 2-word numeric header as 1 word per line for compact numeric columns.

    Rule:
    - column is numeric-only after coercion
    - every numeric value fits within 3 digits by absolute value (<= 999)
    - header contains exactly 2 words
    """
    header_words = str(header_text or "").strip().split()
    if len(header_words) != 2:
        return False

    if series is None:
        return False

    try:
        s = pd.Series(series)
    except Exception:
        return False

    if s.empty:
        return False

    numeric = pd.to_numeric(s, errors="coerce")
    non_null_count = int(pd.Series(s).notna().sum())
    numeric_count = int(numeric.notna().sum())
    if non_null_count <= 0 or numeric_count != non_null_count:
        return False

    if numeric_count == 0:
        return False

    try:
        max_abs = float(numeric.abs().max())
    except Exception:
        return False

    return max_abs <= 999


def _estimate_wrapped_line_count(text: str, max_chars_per_line: int = 42) -> int:
    """Approximate rendered line count for plain text blocks.

    This is a Python-side heuristic used for iframe-height sizing. It is intentionally
    conservative so the generated iframe is less likely to clip the footer.
    """
    s = "" if text is None else str(text)
    s = s.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    parts = [p.strip() for p in s.splitlines()] or [s.strip()]
    total = 0
    max_chars_per_line = max(8, int(max_chars_per_line or 42))

    for part in parts:
        if not part:
            total += 1
            continue
        words = part.split()
        if not words:
            total += 1
            continue

        current = 0
        lines = 1
        for word in words:
            word_len = len(word)
            if current == 0:
                current = word_len
            elif current + 1 + word_len <= max_chars_per_line:
                current += 1 + word_len
            else:
                lines += 1
                current = word_len
        total += lines

    return max(1, total)


def _estimate_header_line_count(columns, cfg: dict | None = None, df=None) -> int:
    cfg = cfg or {}
    cols = list(columns or [])
    if not cols:
        return 1

    overrides = cfg.get("col_header_overrides", {}) or {}
    header_wrap_target = str(cfg.get("header_wrap_target", "Off") or "Off").strip()
    try:
        header_wrap_words = int(cfg.get("header_wrap_words", 2) or 2)
    except Exception:
        header_wrap_words = 2
    header_wrap_words = max(1, min(10, header_wrap_words))

    max_lines = 1
    for col in cols:
        display_col = str(overrides.get(col, col) or col).strip()
        should_wrap_header = False
        wrap_words_for_col = header_wrap_words
        if header_wrap_target == "All columns":
            should_wrap_header = True
        elif header_wrap_target and header_wrap_target != "Off" and str(col) == header_wrap_target:
            should_wrap_header = True
        elif df is not None and hasattr(df, "columns") and col in getattr(df, "columns", []):
            if should_force_two_line_numeric_header(df[col], display_col):
                should_wrap_header = True
                wrap_words_for_col = 1

        if should_wrap_header:
            line_count = len(wrap_text_by_words(display_col, wrap_words_for_col).splitlines())
        else:
            line_count = _estimate_wrapped_line_count(display_col, max_chars_per_line=18)
        max_lines = max(max_lines, line_count)

    return max_lines


def compute_preview_height(row_count: int, cfg: dict | None = None, df=None) -> int:
    """Estimate the total widget height from the top of the header to the bottom of the footer.

    This intentionally avoids adding large safety padding because the returned value is also used
    as the published iframe height. The goal is a tight outer height that ends at the widget,
    not below it.
    """
    try:
        row_count = int(row_count)
    except Exception:
        row_count = 0

    cfg = cfg or {}
    if df is not None and isinstance(df, pd.DataFrame):
        row_count = len(df.index)
        columns = list(df.columns)
    else:
        columns = []

    if row_count <= 0:
        base_header = 88 if cfg.get("show_header", True) else 0
        base_footer = 88 if cfg.get("show_footer", True) else 0
        controls_h = 50 if (cfg.get("show_search", True) or cfg.get("show_pager", True) or (cfg.get("show_embed", True) and str(cfg.get("embed_position", "Body") or "Body") == "Body")) else 0
        return max(360, min(1200, base_header + controls_h + 120 + base_footer))

    visible_rows = min(max(row_count, 1), 10)

    show_header = bool(cfg.get("show_header", True))
    show_footer = bool(cfg.get("show_footer", True))
    show_search = bool(cfg.get("show_search", True))
    show_pager = bool(cfg.get("show_pager", True))
    show_page_numbers = bool(cfg.get("show_page_numbers", True)) and show_pager
    show_embed = bool(cfg.get("show_embed", True))
    embed_position = str(cfg.get("embed_position", "Body") or "Body")
    show_footer_notes = bool(cfg.get("show_footer_notes", False))
    show_heat_scale = bool(cfg.get("show_heat_scale", False)) and not show_footer_notes

    title_lines = _estimate_wrapped_line_count(cfg.get("title", "Table 1"), max_chars_per_line=34)
    subtitle_lines = _estimate_wrapped_line_count(cfg.get("subtitle", ""), max_chars_per_line=46) if str(cfg.get("subtitle", "")).strip() else 0

    header_h = 0
    if show_header:
        header_h = 88 + max(0, title_lines - 1) * 18 + max(0, subtitle_lines - 1) * 14
        if show_embed and embed_position == "Header":
            header_h = max(header_h, 88)

    max_header_lines = _estimate_header_line_count(columns, cfg=cfg, df=df)
    table_head_h = 56 + max(0, max_header_lines - 1) * 16

    row_h = 52
    body_h = visible_rows * row_h

    controls_h = 0
    if show_search or show_pager or (show_embed and embed_position == "Body"):
        controls_h = 46
        if (show_search and show_pager) or ((show_search or show_pager) and show_embed and embed_position == "Body"):
            controls_h += 6

    page_status_h = 24 if show_page_numbers else 0
    scrollbar_h = 14 if row_count > 10 else 0
    body_bottom_gap_h = 2 if row_count > 10 else 0

    footer_h = 0
    if show_footer:
        try:
            footer_logo_h = int(cfg.get("footer_logo_h", 36) or 36)
        except Exception:
            footer_logo_h = 36
        footer_h = max(84, footer_logo_h + 44)
        if show_footer_notes:
            notes = str(cfg.get("footer_notes", "") or "").strip()
            note_lines = _estimate_wrapped_line_count(notes, max_chars_per_line=72) if notes else 0
            footer_h += note_lines * 18 + (10 if note_lines else 0)
        elif show_heat_scale:
            footer_h += 22
        if show_embed and embed_position == "Footer":
            footer_h = max(footer_h, 92)

    est = header_h + controls_h + table_head_h + body_h + scrollbar_h + body_bottom_gap_h + page_status_h + footer_h
    return max(420, min(1400, est))


def compute_widget_table_max_height(row_count: int) -> int:
    """Return the internal scroll cap for the table region inside the widget."""
    try:
        row_count = int(row_count)
    except Exception:
        row_count = 0

    if row_count >= 10:
        return 680

    return max(260, 130 + (row_count * 52))


def sync_table_control_defaults_for_row_count(df) -> int:
    """Auto-hide search/pager for compact tables by default, while allowing user override.

    Defaults are re-applied only when the uploaded table shape changes.
    """
    row_count = len(df.index) if isinstance(df, pd.DataFrame) else 0
    col_count = len(df.columns) if isinstance(df, pd.DataFrame) else 0
    data_sig = f"{row_count}x{col_count}"

    prev_sig = st.session_state.get("bt_table_controls_auto_sig")
    if prev_sig != data_sig:
        compact_defaults = row_count <= 10 and row_count > 0
        st.session_state["bt_show_search"] = not compact_defaults
        st.session_state["bt_show_pager"] = not compact_defaults
        st.session_state["bt_show_page_numbers"] = not compact_defaults
        st.session_state["bt_table_controls_auto_sig"] = data_sig

    return row_count

# =========================================================
# 0) Publishing Users + Secrets (GITHUB APP)
# =========================================================
# ✅ "Created by" tracking list (UI only)
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
GITHUB_PAT = str(get_secret("GITHUB_PAT", "")).strip()

# optional (for showing install link)
GITHUB_APP_SLUG = str(get_secret("GITHUB_APP_SLUG", "")).strip().lower()  # e.g. "bcdprpagehoster"

# ✅ Publishing always happens under ONE account (Earned Media)
# Put this in Streamlit secrets if you want (recommended):
# PUBLISH_OWNER = "BetterCollective26"
PUBLISH_OWNER = str(get_secret("PUBLISH_OWNER", "BetterCollective26")).strip().lower()

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


def github_token(owner: str | None = None) -> str:
    """Return a GitHub token to use for writes/reads.

    Prefers GITHUB_PAT (if present), otherwise falls back to a GitHub App installation token
    for the configured PUBLISH_OWNER (or the provided owner).
    """
    use_owner = (owner or PUBLISH_OWNER or "").strip().lower()
    if GITHUB_PAT:
        return str(GITHUB_PAT).strip()
    try:
        return get_installation_token_for_user(use_owner)
    except Exception:
        return ""

def build_github_app_jwt(app_id: str, private_key_pem: str) -> str:
    """
    Create a short-lived JWT for GitHub App authentication.
    """
    if not app_id or not private_key_pem:
        raise RuntimeError("Missing GitHub App credentials in secrets (GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY).")

    now = int(time.time())
    payload = {
        "iat": now - 30,  # helps with clock skew
        "exp": now + (9 * 60),  # <= 10 mins
        "iss": app_id,
    }

    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8", errors="ignore")
    return token

def get_installation_id_for_user(username: str) -> int:
    username = (username or "").strip()
    if not username:
        return 0

    app_jwt = build_github_app_jwt(GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY)

    # Try user install first
    r = http_session().get(
        f"https://api.github.com/users/{username}/installation",
        headers=github_headers(app_jwt),
        timeout=20,
    )
    if r.status_code == 200:
        return int((r.json() or {}).get("id", 0) or 0)

    # If not found, try org install
    r2 = http_session().get(
        f"https://api.github.com/orgs/{username}/installation",
        headers=github_headers(app_jwt),
        timeout=20,
    )
    if r2.status_code == 200:
        return int((r2.json() or {}).get("id", 0) or 0)

    return 0

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

    r = http_session().post(
        f"https://api.github.com/app/installations/{install_id}/access_tokens",
        headers=github_headers(app_jwt),
        timeout=20,
    )

    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error creating installation token: {r.status_code} {r.text}")

    data = r.json() or {}
    return str(data.get("token", "")).strip()


def ensure_repo_exists(owner: str, repo: str, install_token: str) -> bool:
    api_base = "https://api.github.com"

    owner = (owner or "").strip()
    repo = (repo or "").strip()

    # First: check if repo exists (using GitHub App token)
    r = http_session().get(
        f"{api_base}/repos/{owner}/{repo}",
        headers=github_headers(install_token),
        timeout=20,
    )

    if r.status_code == 200:
        return False  # already exists

    if r.status_code != 404:
        raise RuntimeError(f"Error Checking Repo: {r.status_code} {r.text}")

    # Repo does not exist → create it using PAT
    if not GITHUB_PAT:
        raise RuntimeError("Repo does not exist and cannot be created because GITHUB_PAT is missing in secrets.")

    payload = {
        "name": repo,
        "auto_init": True,
        "private": False,
        "description": "Branded Searchable Table (Auto-Created By Streamlit App).",
    }

    # ✅ PERSONAL ACCOUNT repo creation endpoint
    create_url = f"{api_base}/user/repos"

    r2 = http_session().post(
        create_url,
        headers=github_headers(GITHUB_PAT),
        json=payload,
        timeout=20,
    )

    if r2.status_code not in (200, 201):
        raise RuntimeError(f"Error Creating Repo (PAT): {r2.status_code} {r2.text}")

    return True


def ensure_pages_enabled(owner: str, repo: str, token: str, branch: str = "main") -> None:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    r = http_session().get(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, timeout=20)
    if r.status_code == 200:
        return
    if r.status_code not in (404, 403):
        raise RuntimeError(f"Error Checking GitHub Pages: {r.status_code} {r.text}")
    if r.status_code == 403:
        return

    payload = {"source": {"branch": branch, "path": "/"}}
    r = http_session().post(f"{api_base}/repos/{owner}/{repo}/pages", headers=headers, json=payload, timeout=20)
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

    path = (path or "").lstrip("/").strip()
    get_url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
    r = http_session().get(get_url, headers=headers, params={"ref": branch}, timeout=20)

    sha = None
    if r.status_code == 200:
        sha = r.json().get("sha")
    elif r.status_code != 404:
        raise RuntimeError(f"Error Checking File: {r.status_code} {r.text}")

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha

    r = http_session().put(get_url, headers=headers, json=payload, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Error Uploading File: {r.status_code} {r.text}")


def trigger_pages_build(owner: str, repo: str, token: str) -> bool:
    api_base = "https://api.github.com"
    headers = github_headers(token)
    r = http_session().post(f"{api_base}/repos/{owner}/{repo}/pages/builds", headers=headers, timeout=20)
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
        r = http_session().get(url, headers=headers, params={"ref": branch}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=120, show_spinner=False)
def github_file_exists_cached(owner: str, repo: str, token: str, path: str, branch: str = "main") -> bool:
    return github_file_exists(owner, repo, token, path, branch)


@st.cache_data(ttl=120, show_spinner=False)
def read_github_json_cached(owner: str, repo: str, token: str, path: str, branch: str = "main") -> dict:
    return read_github_json(owner, repo, token, path, branch)

def read_github_json(owner: str, repo: str, token: str, path: str, branch: str = "main") -> dict:
    """Read a JSON file from GitHub. If missing, return {}."""
    api_base = "https://api.github.com"
    headers = github_headers(token)
    path = (path or "").lstrip("/").strip()
    if not path:
        return {}

    url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
    r = http_session().get(url, headers=headers, params={"ref": branch}, timeout=20)

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
    """Write a JSON file into GitHub."""
    content = json.dumps(payload or {}, indent=2, ensure_ascii=False)
    upload_file_to_github(owner, repo, token, path, content, message, branch=branch)

def list_repos_for_owner(owner: str, token: str) -> list[dict]:
    api_base = "https://api.github.com"
    headers = github_headers(token)

    # detect if user/org
    r = http_session().get(f"{api_base}/users/{owner}", headers=headers, timeout=20)
    if r.status_code != 200:
        return []

    user_type = (r.json() or {}).get("type", "")

    repos = []
    page = 1
    while True:
        if user_type == "Organization":
            url = f"{api_base}/orgs/{owner}/repos"
        else:
            url = f"{api_base}/users/{owner}/repos"

        rr = http_session().get(url, headers=headers, params={"per_page": 100, "page": page}, timeout=20)
        if rr.status_code != 200:
            break

        batch = rr.json() or []
        if not batch:
            break

        repos.extend(batch)
        page += 1

        # safety stop
        if page > 20:
            break

    return repos

@st.cache_data(ttl=10 * 60)
def get_all_published_widgets(owner: str, token: str) -> pd.DataFrame:
    """
    Reads widget_registry.json from every repo that has it.
    If registry missing, fallback to scanning root for *.html files.
    Also tries to infer brand + fetch created_by/created_utc from git commits for legacy pages.
    """
    rows = []
    repos = list_repos_for_owner(owner, token)

    api_base = "https://api.github.com"
    headers = github_headers(token)

    def compute_url(repo_name: str, file_name: str) -> str:
        return compute_pages_url(owner, repo_name, file_name)

    def infer_brand_from_repo(repo_name: str) -> str:
        """
        Example repo names:
          ActionNetworktj26
          CanadaSportsBettingtj26
          RotoGrinderstj26
        """
        rn = (repo_name or "").lower()

        for brand, prefix in BRAND_REPO_PREFIX_FULL.items():
            if rn.startswith(prefix.lower()):
                return brand

        return ""


    def is_generator_repo(repo_name: str) -> bool:
        """
        Keep ONLY repos created/managed by this Branded Table Generator.
        Expected naming pattern: <BrandPrefix>t<monthcode><yy>
        Examples: ActionNetworktj26, VegasInsidertf26, RotoGrinderstj26
        """
        rn = (repo_name or "").strip().lower()
        if not rn:
            return False

        # must start with one of our known brand prefixes
        prefixes = [p.lower() for p in BRAND_REPO_PREFIX_FULL.values()]
        if not any(rn.startswith(p) for p in prefixes):
            return False

        # must end with t + single-letter month code + 2-digit year (e.g., tj26)
        return re.search(r"t[a-z]\d{2}$", rn) is not None
    def get_file_commit_meta(repo_name: str, file_name: str) -> tuple[str, str]:
        """
        Returns (created_by, created_utc) from latest commit touching the file.
        """
        try:
            rr = http_session().get(
                f"{api_base}/repos/{owner}/{repo_name}/commits",
                headers=headers,
                params={"path": file_name, "per_page": 1},
                timeout=20,
            )

            if rr.status_code != 200:
                return "", ""

            commits = rr.json() or []
            if not commits:
                return "", ""

            c0 = commits[0] or {}

            # Created by (prefer GitHub login)
            created_by = ""
            if isinstance(c0.get("author"), dict) and c0["author"].get("login"):
                created_by = str(c0["author"]["login"]).strip().lower()
            else:
                # fallback to commit author name
                commit_obj = c0.get("commit") or {}
                author_obj = commit_obj.get("author") or {}
                created_by = str(author_obj.get("name") or "").strip().lower()

            # Created UTC (ISO format)
            commit_obj = c0.get("commit") or {}
            author_obj = commit_obj.get("author") or {}
            created_utc = str(author_obj.get("date") or "").strip()

            return created_by, created_utc

        except Exception:
            return "", ""

    for r in repos:
        repo_name = (r.get("name") or "").strip()
        if not repo_name:
            continue

        try:
            reg = read_github_json_cached(owner, repo_name, token, "widget_registry.json", branch="main")

            # ✅ CASE A: Registry exists → use it
            if isinstance(reg, dict) and reg:
                for fname, meta in reg.items():
                    if not isinstance(meta, dict):
                        meta = {}

                    pages_url = (meta.get("pages_url") or "").strip()
                    if not pages_url:
                        pages_url = compute_url(repo_name, fname)

                    brand = (meta.get("brand") or "").strip()
                    if not brand:
                        brand = infer_brand_from_repo(repo_name)

                    created_by = (meta.get("created_by") or "").strip().lower()
                    created_utc = (meta.get("created_at_utc") or "").strip()

                    # ✅ If missing created fields, try commit lookup
                    if not created_by or not created_utc:
                        cb, cu = get_file_commit_meta(repo_name, fname)
                        created_by = created_by or cb
                        created_utc = created_utc or cu

                    bundle_path = f"bundles/{fname}.json"
                    has_csv = github_file_exists_cached(
                        owner,
                        repo_name,
                        token,
                        bundle_path,
                        branch="main",
                    )
                    
                    rows.append({
                        "Brand": brand,
                        "Table Name": meta.get("table_title", "") or fname,
                        "Has CSV": "✅" if has_csv else "—",
                        "Pages URL": pages_url,
                        "Created By": created_by,
                        "Created UTC": created_utc,
                        "Repo": repo_name,
                        "File": fname,
                    })

            # ✅ CASE B: No registry → scan for html files + infer metadata
            else:
                rr = http_session().get(
                    f"{api_base}/repos/{owner}/{repo_name}/contents",
                    headers=headers,
                    params={"ref": "main"},
                    timeout=20,
                )

                if rr.status_code == 200:
                    contents = rr.json() or []
                    for item in contents:
                        name = (item.get("name") or "").strip()
                        if not name.lower().endswith(".html"):
                            continue

                        brand = infer_brand_from_repo(repo_name)

                        created_by, created_utc = get_file_commit_meta(repo_name, name)

                        rows.append({
                            "Brand": brand,
                            "Table Name": name,
                            "Has CSV": "—",  # ❌ legacy tables have no bundle
                            "Pages URL": compute_url(repo_name, name),
                            "Created By": created_by,
                            "Created UTC": created_utc,
                            "Repo": repo_name,
                            "File": name,
                        })
        except Exception:
            continue

    df = pd.DataFrame(rows)

    # ✅ remove duplicates if registry + fallback both catch same html
    if not df.empty:
        df = df.drop_duplicates(subset=["Pages URL"], keep="first")
    
    
    # ✅ Only show tables from Branded Table Generator repos (filter out random GitHub Pages)
    if not df.empty and "Repo" in df.columns:
        df = df[df["Repo"].apply(is_generator_repo)].copy()
# ✅ Sort newest first (works best once commit dates exist)
    if not df.empty and "Created UTC" in df.columns:
        df = df.sort_values("Created UTC", ascending=False, na_position="last")
    
    if not df.empty:
        df["Created DT"] = pd.to_datetime(df["Created UTC"], errors="coerce", utc=True)
        df = df.sort_values("Created DT", ascending=False, na_position="last")
        df = df.drop(columns=["Created DT"])
    
        # ✅ ALWAYS return a dataframe (even if empty)
    return df
   
def update_widget_registry(
    owner: str,
    repo: str,
    token: str,
    widget_file_name: str,
    meta: dict,
    branch: str = "main",
):
    """
    Adds/updates a single widget record inside widget_registry.json
    """
    widget_file_name = (widget_file_name or "").strip()
    if not widget_file_name:
        return

    registry_path = "widget_registry.json"

    # read existing registry (or empty)
    registry = read_github_json_cached(owner, repo, token, registry_path, branch=branch)
    if not isinstance(registry, dict):
        registry = {}

    registry[widget_file_name] = meta

    write_github_json(
        owner=owner,
        repo=repo,
        token=token,
        path=registry_path,
        payload=registry,
        message="Update widget registry",
        branch=branch,
    )
    

# =========================================================
# ✅ GLOBAL "ACTIVE USERS" (shared across browsers)
# - Writes a JSON file (active_users.json) to a canonical repo
# - All sessions read it and display who is currently active
# - Each login/heartbeat refreshes the user's "last_seen" + expiry
# =========================================================

ACTIVE_USERS_PATH = str(get_secret("ACTIVE_STATE_FILE_PATH", "active_users.json") or "active_users.json").strip()
ACTIVE_USER_TTL_MINUTES = int(get_secret("ACTIVE_USER_TTL_MINUTES", 45) or 45)
ACTIVE_USER_HEARTBEAT_SECONDS = int(get_secret("ACTIVE_USER_HEARTBEAT_SECONDS", 60) or 60)

def _is_generator_repo_name(repo_name: str) -> bool:
    """True if repo name matches our generator repo naming scheme."""
    name = (repo_name or "").strip()
    if not name:
        return False

    # Brand prefix + 't' + month code + 2-digit year (e.g., ActionNetworktj26)
    prefixes = [pfx.lower() for pfx in BRAND_REPO_PREFIX_FULL.values()]
    low = name.lower()

    if not any(low.startswith(p) for p in prefixes):
        return False

    # end like: t + one month-letter + 2 digits year
    return re.search(r"t[a-z]\d{2}$", low) is not None


@st.cache_data(ttl=300, show_spinner=False)
def get_active_state_repo(owner: str, token: str) -> str:
    """Pick a canonical repo to store active_users.json.

    Priority:
      1) secrets.ACTIVE_STATE_REPO (if set)
      2) lexicographically latest generator repo under the owner (fallback)
    """
    preferred = str(get_secret("ACTIVE_STATE_REPO", "BrandedGeneratorState") or "BrandedGeneratorState").strip()
    if preferred:
        return preferred

    repos = list_repos_for_owner(owner, token) or []
    names = []
    for r in repos:
        if isinstance(r, dict):
            nm = (r.get("name") or "").strip()
        else:
            nm = str(r or "").strip()
        if nm and _is_generator_repo_name(nm):
            names.append(nm)

    if not names:
        return ""

    # deterministic pick
    names = sorted(set(names), key=lambda s: s.lower())
    return names[-1]


def active_state_repo_exists(owner: str, repo: str, token: str) -> bool:
    """Best-effort check that the ACTIVE_STATE_REPO exists and is readable."""
    try:
        if not owner or not repo:
            return False
        r = http_session().get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=github_headers(token),
            timeout=15,
        )
        return r.status_code == 200
    except Exception:
        return False



def utc_now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _parse_iso_z(s: str) -> datetime.datetime | None:
    try:
        if not s:
            return None
        s = str(s).strip()
        if s.endswith("Z"):
            s = s[:-1]
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None


def format_relative_minutes(utc_iso_z: str) -> str:
    dt = _parse_iso_z(utc_iso_z)
    if not dt:
        return ""
    now = datetime.datetime.utcnow()
    mins = int((now - dt).total_seconds() // 60)
    if mins <= 0:
        return "just now"
    if mins == 1:
        return "1 min ago"
    if mins < 60:
        return f"{mins} mins ago"
    hrs = mins // 60
    if hrs == 1:
        return "1 hr ago"
    return f"{hrs} hrs ago"


def _prune_active_users(state: dict) -> dict:
    """Remove expired/invalid entries."""
    now = datetime.datetime.utcnow()
    out = {}
    for user, meta in (state or {}).items():
        if not isinstance(meta, dict):
            continue
        exp = _parse_iso_z(meta.get("expires_utc", ""))
        if exp and exp >= now:
            out[str(user).strip().lower()] = meta
    return out


def read_active_users_state(owner: str, token: str) -> dict:
    repo = get_active_state_repo(owner, token)
    if not repo:
        return {}
    if not active_state_repo_exists(owner, repo, token):
        return {}
    try:
        raw = read_github_json(owner, repo, token, ACTIVE_USERS_PATH) or {}
        raw = raw if isinstance(raw, dict) else {}
        return _prune_active_users(raw)
    except Exception:
        return {}


def write_active_users_state(owner: str, token: str, user: str, action: str = "heartbeat") -> bool:
    """Upsert a user into active_users.json with a fresh expiry."""
    repo = get_active_state_repo(owner, token)
    if not repo:
        return False
    if not active_state_repo_exists(owner, repo, token):
        return False

    now = datetime.datetime.utcnow().replace(microsecond=0)
    u = (user or "").strip().lower()
    if not u:
        return False

    # load + prune
    try:
        current = read_github_json(owner, repo, token, ACTIVE_USERS_PATH) or {}
        current = current if isinstance(current, dict) else {}
    except Exception:
        current = {}

    current = _prune_active_users(current)

    current[u] = {
        "user": u,
        "action": action,
        "utc": now.isoformat() + "Z",
        "expires_utc": (now + datetime.timedelta(minutes=ACTIVE_USER_TTL_MINUTES)).isoformat() + "Z",
        "app": "Branded Table Generator",
    }

    try:
        write_github_json(
            owner=owner,
            repo=repo,
            token=token,
            path=ACTIVE_USERS_PATH,
            payload=current,
            message=f"Update active users ({action}): {u}",
            branch="main",
        )
        return True
    except Exception:
        return False


def remove_active_user(owner: str, token: str, user: str) -> bool:
    """Remove a user entry (best-effort)."""
    repo = get_active_state_repo(owner, token)
    if not repo:
        return False
    if not active_state_repo_exists(owner, repo, token):
        return False

    u = (user or "").strip().lower()
    if not u:
        return False

    try:
        current = read_github_json(owner, repo, token, ACTIVE_USERS_PATH) or {}
        current = current if isinstance(current, dict) else {}
    except Exception:
        current = {}

    current = _prune_active_users(current)
    if u in current:
        current.pop(u, None)

    try:
        write_github_json(
            owner=owner,
            repo=repo,
            token=token,
            path=ACTIVE_USERS_PATH,
            payload=current,
            message=f"Remove active user: {u}",
            branch="main",
        )
        return True
    except Exception:
        return False


def render_active_users_banner(owner: str, token: str):
    """Collapsible 'Active users' panel (global, shared across sessions).

    This is intentionally NOT always visible as a big banner — it lives in an expander
    so only interested users open it.
    """
    with st.expander("🟢 Active users", expanded=False):
        try:
            repo = get_active_state_repo(owner, token)
            if not repo or not active_state_repo_exists(owner, repo, token):
                st.warning(
                    "Active-user state repo not found or not accessible. "
                    "Set ACTIVE_STATE_REPO in secrets (e.g., BrandedGeneratorState)."
                )
                return

            state = read_active_users_state(owner, token)
            if not state:
                st.caption(f"No active users detected (last ~{ACTIVE_USER_TTL_MINUTES} mins).")
                return

            # sort by last seen (utc desc)
            def _key(item):
                meta = item[1] or {}
                dt = _parse_iso_z(meta.get("utc", "")) or datetime.datetime.min
                return dt

            items = sorted(state.items(), key=_key, reverse=True)

            # Friendly list
            for u, meta in items:
                rel = format_relative_minutes((meta or {}).get("utc", ""))
                st.markdown(f"- **{u}** — {rel}")

            st.caption(
                f"Auto-removes users after ~{ACTIVE_USER_TTL_MINUTES} minutes without a heartbeat."
            )
        except Exception as e:
            # Keep this non-fatal and non-spammy
            st.warning("Could not load active-user state right now.")


def get_github_file_sha(owner: str, repo: str, token: str, path: str, branch: str = "main") -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    r = http_session().get(url, headers=headers, params={"ref": branch}, timeout=15)
    if r.status_code == 404:
        return ""  # already gone
    r.raise_for_status()
    return (r.json() or {}).get("sha", "") or ""

def delete_github_file(owner: str, repo: str, token: str, path: str, branch: str = "main"):
    sha = get_github_file_sha(owner, repo, token, path, branch=branch)
    if not sha:
        return  # treat as success (already deleted)

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    payload = {
        "message": f"Delete {path} via Branded Table Generator",
        "sha": sha,
        "branch": branch,
    }
    r = http_session().delete(url, headers=headers, json=payload, timeout=20)
    r.raise_for_status()

def remove_from_widget_registry(owner: str, repo: str, token: str, widget_file_name: str, branch: str = "main"):
    # read registry
    registry_path = "widget_registry.json"
    registry = read_github_json_cached(owner, repo, token, registry_path, branch=branch)
    if not isinstance(registry, dict):
        registry = {}

    if widget_file_name in registry:
        registry.pop(widget_file_name, None)
        upload_file_to_github(
            owner,
            repo,
            token,
            registry_path,
            json.dumps(registry, indent=2),
            f"Remove {widget_file_name} from widget_registry.json",
            branch=branch,
        )
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
# HTML Template (UPDATED)
# =========================================================
HTML_TEMPLATE_TABLE = r"""<!-- BT_PUBLISH_HASH:bar_columns=[]|bar_fixed_w=200|bar_max_overrides={}|brand='Canada Sports Betting'|branded_title_color=True|cell_align='Center'|center_titles=False|col_header_overrides={}|header_wrap_target='Off'|header_wrap_words=2|embed_position='Header'|footer_logo_align='Center'|footer_logo_h=36|footer_notes=''|header_style='Keep original'|heat_columns=[]|heat_overrides={}|heat_strength=0.55|heatmap_style='Branded heatmap'|show_embed=True|show_footer=True|show_footer_notes=False|show_header=True|show_heat_scale=False|show_page_numbers=True|show_pager=True|show_search=True|striped=True|subtitle='Subheading'|subtitle_style='Keep original'|title='Table 1'|title_style='Keep original' -->
<!DOCTYPE html>

<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1" name="viewport"/>
<title>Table 1</title>
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
</head>
<body style="margin:0; overflow-x:hidden; overflow-y:auto; background:#ffffff;">
<section class="vi-table-embed [[BRAND_CLASS]] [[FOOTER_ALIGN_CLASS]] [[FOOTER_EMBED_MODE_CLASS]] [[CELL_ALIGN_CLASS]]" data-embed-position="[[EMBED_POSITION]]" style="width:100%;max-width:100%;margin:0;
         font:14px/1.35 Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         color:#181a1f;background:linear-gradient(180deg,#ffffff 0%, rgba(var(--brand-500-rgb), .04) 100%);border:1px solid rgba(var(--brand-500-rgb),.12);border-radius:0;
         box-shadow:inset 0 1px 0 rgba(255,255,255,.85);">
<style>
    html, body { height:100%; }
    body{ -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }
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

      /* ✅ Table scroll height */
      --table-max-h: [[TABLE_MAX_H]]px;

      /* ✅ FIXED bar track width (same across ALL bar columns) */
      --bar-fixed-w: [[BAR_FIXED_W]]px;

      /* ✅ Footer logo height */
      --footer-logo-h: [[FOOTER_LOGO_H]]px;
      --surface-shadow: 0 14px 34px rgba(17,24,39,.08);
      --accent-start: var(--brand-500);
      --accent-mid: var(--brand-600);
      --accent-end: var(--brand-700);

      height: auto;
      min-height: 0;
      max-height: none;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      isolation: isolate;
      position: relative;
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

    /* Header block */
    .vi-table-embed .vi-table-header{
      border-bottom:1px solid var(--brand-600);
      padding:14px 18px;
      min-height:88px;
      background:linear-gradient(180deg, rgba(255,255,255,.96), rgba(var(--brand-500-rgb), .04));
      backdrop-filter:none;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:16px;
      position:relative;
      overflow:visible;
      z-index:30;
    }
    .vi-table-embed .vi-header-main{
      min-width:0;
      flex:1 1 auto;
      display:flex;
      flex-direction:column;
      justify-content:center;
      align-items:flex-start;
      gap:4px;
      min-height:100%;
    }
    .vi-table-embed .vi-table-header.centered .vi-header-main{ align-items:center; text-align:center; }
    .vi-table-embed .vi-header-actions{
      flex:0 0 auto;
      display:flex;
      align-items:center;
      justify-content:flex-end;
      min-width:max-content;
      min-height:100%;
      position:relative;
      overflow:visible;
      z-index:40;
    }
    .vi-table-embed .vi-header-actions.vi-hide{ display:none !important; }
    .vi-table-embed .vi-table-header .title{
      margin:0; font-size:clamp(18px,2.3vw,22px); font-weight:800; letter-spacing:-0.02em; color:#111827; display:block; text-shadow:0 1px 0 rgba(255,255,255,.65);
    }
    .vi-table-embed .vi-table-header .title.branded{ color:var(--brand-600); }
    .vi-table-embed .vi-table-header .subtitle{ margin:0; font-size:13px; color:#7a808d; display:block; }

    .vi-table-embed .dw-download,
    .vi-table-embed .dw-embed-trigger,
    .vi-table-embed .dw-embed-trigger-header,
    .vi-table-embed .dw-embed-trigger-footer,
    .vi-table-embed button.dw-btn.dw-download,
    .vi-table-embed .vi-header-actions button,
    .vi-table-embed .footer-embed-wrap button{
      cursor: pointer !important;
    }

    .vi-table-embed .dw-download:disabled,
    .vi-table-embed .dw-embed-trigger:disabled,
    .vi-table-embed button.dw-btn.dw-download:disabled{
      cursor: not-allowed !important;
    }

    .vi-table-embed th,
    .vi-table-embed thead th{
      white-space: normal !important;
      word-break: normal !important;
      overflow-wrap: break-word !important;
      height: auto !important;
      line-height: 1.2 !important;
    }


    /* Table block */
    #bt-block, #bt-block * { box-sizing:border-box; }
    #bt-block{
      --bg:#ffffff; --text:#1f2937;
      --gutter: 12px;
      padding: 12px 0 10px;
      flex: 1 1 auto;
      min-height: 0;
      display: flex;
      flex-direction: column;
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
      white-space:normal; word-break:normal; overflow-wrap:break-word;
      position:relative;
    }

    #bt-block .dw-pager,
    .vi-table-embed .dw-embed{
      display:flex;
      align-items:center;
      gap: var(--ctrl-gap);
      flex-wrap:nowrap;
      white-space:normal; word-break:normal; overflow-wrap:break-word;
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

    /* Search */
    #bt-block .dw-input{
      width: 100%;
      max-width: 260px;
      min-width: 120px;
      padding-right: 34px;
      background:linear-gradient(180deg,#fff,#fff8f8);
      border:1px solid rgba(var(--brand-500-rgb), .24);
      color:var(--text);
      box-shadow:0 6px 16px rgba(17,24,39,.06), inset 0 1px 1px rgba(255,255,255,.85);
    }

    /* ✅ Mobile squeeze */
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
      .vi-table-embed .dw-btn.dw-download{
        font-size: 0;
        padding-inline: 10px;
      }
      .vi-table-embed .dw-btn.dw-download::after{
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

    /* Rows/Page dropdown */
    #bt-block .dw-select{
      appearance:none; -webkit-appearance:none; -moz-appearance:none;
      padding-right: 18px;
      width: 62px;
      text-align:center;
      background:linear-gradient(180deg,#fff,#fff8f8);
      border:1px solid rgba(var(--brand-500-rgb), .24);
      color:var(--text);
      box-shadow:0 6px 16px rgba(17,24,39,.06), inset 0 1px 1px rgba(255,255,255,.85);
    }

    /* Buttons */
    #bt-block .dw-btn{
      background:linear-gradient(180deg, var(--accent-start) 0%, var(--accent-mid) 100%);
      color:#fff;
      border:1px solid rgba(var(--brand-500-rgb), .72);
      padding-inline: 10px;
      cursor:pointer;
      white-space:normal; word-break:normal; overflow-wrap:break-word;
      height: 34px;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      box-shadow:none;
    }
    #bt-block .dw-btn:hover{background:linear-gradient(180deg,var(--accent-mid) 0%, var(--accent-end) 100%); border-color:rgba(var(--brand-500-rgb), .9); transform:translateY(-1px); box-shadow:none}
    #bt-block .dw-btn:active{transform:translateY(1px)}
    #bt-block .dw-btn[disabled]{background:#fafafa; border-color:#d1d5db; color:#6b7280; opacity:1; cursor:not-allowed; transform:none}
    #bt-block .dw-btn[data-page]{ width: 34px; padding: 0; }


    /* Embed/Download button — source of truth for body, header, and footer */
    .vi-table-embed button.dw-btn.dw-download,
    .vi-table-embed .dw-btn.dw-download,
    .vi-table-embed .dw-download,
    .vi-table-embed .vi-header-actions button,
    .vi-table-embed .vi-header-actions .dw-btn,
    .vi-table-embed .vi-header-actions .dw-download,
    .vi-table-embed .footer-embed-wrap button,
    .vi-table-embed .footer-embed-wrap .dw-btn,
    .vi-table-embed .footer-embed-wrap .dw-download,
    .vi-table-embed [data-embed-position="Header"] .vi-header-actions button,
    .vi-table-embed [data-embed-position="Header"] .vi-header-actions .dw-btn,
    .vi-table-embed [data-embed-position="Footer"] .footer-embed-wrap button,
    .vi-table-embed [data-embed-position="Footer"] .footer-embed-wrap .dw-btn{
      background:linear-gradient(180deg, var(--accent-start) 0%, var(--accent-mid) 100%) !important;
      background-color:var(--accent-mid) !important;
      color:#ffffff !important;
      border:1px solid rgba(var(--brand-500-rgb), .72) !important;
      border-radius:12px !important;
      height:34px;
      padding-inline:12px;
      font-weight:700 !important;
      box-shadow:none !important;
      text-shadow:none !important;
      outline:none !important;
      opacity:1 !important;
      -webkit-appearance:none !important;
      appearance:none !important;
      cursor:pointer !important;
      text-decoration:none !important;
    }
    .vi-table-embed button.dw-btn.dw-download:hover,
    .vi-table-embed .dw-btn.dw-download:hover,
    .vi-table-embed .dw-download:hover,
    .vi-table-embed .vi-header-actions button:hover,
    .vi-table-embed .vi-header-actions .dw-btn:hover,
    .vi-table-embed .vi-header-actions .dw-download:hover,
    .vi-table-embed .footer-embed-wrap button:hover,
    .vi-table-embed .footer-embed-wrap .dw-btn:hover,
    .vi-table-embed .footer-embed-wrap .dw-download:hover,
    .vi-table-embed button.dw-btn.dw-download:focus,
    .vi-table-embed .dw-btn.dw-download:focus,
    .vi-table-embed .dw-download:focus,
    .vi-table-embed .vi-header-actions button:focus,
    .vi-table-embed .vi-header-actions .dw-btn:focus,
    .vi-table-embed .vi-header-actions .dw-download:focus,
    .vi-table-embed .footer-embed-wrap button:focus,
    .vi-table-embed .footer-embed-wrap .dw-btn:focus,
    .vi-table-embed .footer-embed-wrap .dw-download:focus,
    .vi-table-embed button.dw-btn.dw-download:active,
    .vi-table-embed .dw-btn.dw-download:active,
    .vi-table-embed .dw-download:active,
    .vi-table-embed .vi-header-actions button:active,
    .vi-table-embed .vi-header-actions .dw-btn:active,
    .vi-table-embed .vi-header-actions .dw-download:active,
    .vi-table-embed .footer-embed-wrap button:active,
    .vi-table-embed .footer-embed-wrap .dw-btn:active,
    .vi-table-embed .footer-embed-wrap .dw-download:active{
      background:linear-gradient(180deg, var(--accent-mid) 0%, var(--accent-end) 100%) !important;
      background-color:var(--accent-end) !important;
      color:#ffffff !important;
      border-color:rgba(var(--brand-500-rgb), .9) !important;
      box-shadow:none !important;
      transform:translateY(-1px);
      outline:none !important;
      text-decoration:none !important;
    }

    /* Download menu */
    .vi-table-embed .dw-download-menu{
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

    .vi-table-embed .dw-download-menu .dw-menu-title{
      font: 12px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      color:#6b7280;
      margin:0 0 8px 2px;
    }

    .vi-table-embed .dw-download-menu .dw-menu-btn{
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
    .vi-table-embed .dw-download-menu .dw-menu-btn:hover{
      background:var(--brand-50);
      border-color: rgba(var(--brand-500-rgb), .35);
    }

    .vi-table-embed .dw-modal-backdrop{
      position:absolute;
      inset:0;
      background:rgba(17,24,39,.14);
      z-index:9998;
      padding:0;
      overflow:hidden;
      backdrop-filter: blur(1.5px);
      -webkit-backdrop-filter: blur(1.5px);
    }
    .vi-table-embed .dw-modal{
      width:min(92vw, 320px);
      max-width:calc(100% - 28px);
      background:#ffffff;
      opacity:1;
      border:1px solid rgba(var(--brand-500-rgb), .22);
      border-top:2px solid var(--brand-600);
      border-radius:0;
      box-shadow:0 18px 40px rgba(17,24,39,.24), 0 6px 18px rgba(var(--brand-500-rgb), .10);
      padding:10px;
      position:absolute;
      left:50%;
      top:50%;
      transform:translate(-50%, -50%);
      overflow:hidden;
      isolation:isolate;
    }
    .vi-table-embed .dw-modal-head{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:10px;
      margin-bottom:8px;
      padding-bottom:6px;
      border-bottom:1px solid rgba(var(--brand-500-rgb), .16);
    }
    .vi-table-embed .dw-modal-head .dw-menu-title{
      color:var(--brand-700);
      font-weight:700;
      letter-spacing:.01em;
    }
    .vi-table-embed .dw-modal-actions{
      display:flex;
      flex-direction:column;
      gap:8px;
    }
    .vi-table-embed .dw-modal-close{
      width:32px;
      height:32px;
      border-radius:999px;
      border:1px solid rgba(var(--brand-500-rgb), .18);
      background:#fff;
      color:var(--brand-700);
      cursor:pointer;
      font-size:20px;
      line-height:1;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.9);
    }
    .vi-table-embed .dw-modal-close:hover{
      background:var(--brand-50);
      border-color: rgba(var(--brand-500-rgb), .40);
      color:var(--brand-700);
    }
    .vi-table-embed .dw-modal .dw-menu-btn{
      width:100%;
      display:block;
      text-align:left;
      border-radius:0;
      border:1px solid rgba(var(--brand-500-rgb), .18);
      background:#ffffff;
      color:#111827;
      padding:10px 12px;
      cursor:pointer;
      margin:0;
      font: 14px/1.2 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      box-shadow:none;
    }
    .vi-table-embed .dw-modal .dw-menu-btn:hover{
      background:linear-gradient(180deg, rgba(var(--brand-500-rgb), .10) 0%, rgba(var(--brand-500-rgb), .16) 100%);
      border-color: rgba(var(--brand-500-rgb), .42);
      color:var(--brand-700);
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

    /* Card wrapper */
    #bt-block .dw-card{
      background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(255,250,250,.98));
      border: 1px solid rgba(var(--brand-500-rgb), .12);
      box-shadow: var(--surface-shadow), inset 0 1px 0 rgba(255,255,255,.8);
      margin: 0;
      width: 100%;
      overflow: hidden;
      border-radius:0;
      flex: 0 0 auto;
      min-height: 0;
      display: flex;
      flex-direction: column;
      position: relative;
    }

    /* scroll */
    #bt-block .dw-scroll{
      min-height: 0;
      overflow-x: auto;
      overflow-y: hidden;
      -webkit-overflow-scrolling: touch;
      touch-action: pan-x pan-y;
      overscroll-behavior: contain;
      scrollbar-gutter: stable;
      scrollbar-width: thin;
      scrollbar-color: var(--scroll-thumb) rgba(255,255,255,.2);
      position: relative;
      background: linear-gradient(180deg, rgba(255,255,255,.86), rgba(255,255,255,.96));
    }

    #bt-block .dw-scroll::before,
    #bt-block .dw-scroll::after{
      content:"";
      position: sticky;
      left: 0;
      right: 0;
      display:block;
      pointer-events:none;
      z-index:8;
    }

    

    #bt-block .dw-scroll::after{
      bottom: 0;
      height: 8px;
      background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,.98));
    }

    #bt-block .dw-scroll.compact-fit::after{
      display:none;
      height:0;
      background:none;
    }

    #bt-block .dw-scroll::-webkit-scrollbar{ width: 10px; height: 10px; }
    #bt-block .dw-scroll::-webkit-scrollbar-track{ background: transparent; }
    #bt-block .dw-scroll::-webkit-scrollbar-thumb{
      background: linear-gradient(180deg, #f26461 0%, var(--scroll-thumb) 100%);
      border-radius: 9999px;
      border: 2px solid transparent;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.22);
      background-clip: content-box;
    }
    #bt-block .dw-scroll::-webkit-scrollbar-thumb:hover{ background: var(--brand-600); }

    #bt-block table.dw-table {
      width: max-content;   /* allow columns to grow so headers can fit */
      min-width: 100%;      /* still fill container at minimum */
      border-collapse: separate;
      border-spacing: 0;
      font: 14px/1.45 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
      color: var(--text);
      font-variant-numeric: tabular-nums;
      background: transparent;
      table-layout: auto;
    }

    /* Header row */
    #bt-block thead th{
      background:linear-gradient(180deg, var(--accent-start) 0%, var(--header-bg) 100%);
      color:#ffffff;
      font-weight:700;
      vertical-align:middle;
      border:0;
      padding: 10px 14px;
      transition:background-color .15s, color .15s, box-shadow .15s, transform .05s;
      text-align: var(--cell-align, center);
    
      /* keep table layout stable */
      white-space: normal;
      overflow-wrap: normal;
      word-break: normal;
      hyphens: none;
      line-height: 1.15;
    
      /* IMPORTANT: do NOT change table-cell display */
      overflow: visible;
      text-overflow: clip;
    }
    
    #bt-block thead th.sortable{cursor:pointer; user-select:none}
    #bt-block thead th.sortable::after{
      content:"↕";
      display:inline-block;
      font-size:12px;
      line-height:1;
      opacity:.85;
      margin-left:8px;
      color:#ffffff;
      vertical-align:middle;
    }
    #bt-block thead th.sortable[data-sort="asc"]::after{content:"▲"}
    #bt-block thead th.sortable[data-sort="desc"]::after{content:"▼"}
    
    /* Balanced 1–3 line header labels using whole words only */
    #bt-block thead th.sortable > .dw-th-label{
      display:inline-block;
      width:auto;
      min-width:0;
      max-width:none;
      white-space:normal;
      overflow:visible;
      text-overflow:clip;
      word-break:normal;
      overflow-wrap:normal;
      hyphens:none;
      line-height:1.15;
      text-align:inherit;
      vertical-align:middle;
    }
        
    #bt-block thead th.sortable:hover,
    #bt-block thead th.sortable:focus-visible{
      background:var(--brand-600);
      color:#fff;
      box-shadow:inset 0 -3px 0 var(--brand-100);
    }
    
    #bt-block .dw-scroll.scrolled thead th{
      box-shadow:none;
    }
    
    #bt-block thead th.is-sorted{
      background:var(--brand-700);
      color:#fff;
      box-shadow:inset 0 -3px 0 var(--brand-100);
    }
    
    /* shared cell spacing/alignment */
    #bt-block thead th,
    #bt-block tbody td {
      padding: 15px 14px;
      text-align: var(--cell-align, center);
      vertical-align: middle;
    }
    
    /* Heatmap cells (overlay sits on top of zebra background) */
    #bt-block td.dw-heat-td{
      background-clip: padding-box;
    }
    
    /* body cell text clamp to max 3 lines */
    #bt-block .dw-cell{
      white-space: normal;
      line-height: 1.35;
      overflow-wrap: normal;   /* no mid-word split */
      word-break: normal;
      hyphens: none;
    
      /* body only: max 3 lines */
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3;
      line-clamp: 3;
    
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* ✅ Keep long text columns readable without letting them stretch the table */
    #bt-block th.dw-text-col,
    #bt-block td.dw-text-col{
      width: 220px;
      min-width: 220px;
      max-width: 220px;
    }

    #bt-block td.dw-text-col .dw-cell,
    #bt-block th.dw-text-col .dw-th-label{
      white-space: normal;
      word-break: normal;
      overflow-wrap: normal;
      hyphens: none;
    }
    /* ======================================================
       ✅ FIXED BAR TRACK WIDTH + AUTO COLUMN EXPAND
       ====================================================== */

    /* ✅ Ensure bar columns expand to fit the fixed bar width */
    #bt-block th.dw-bar-col,
    #bt-block td.dw-bar-td{
      min-width: calc(var(--bar-fixed-w) + 70px);
    }

    /* ✅ Fixed bar track size (identical for all columns) */
    #bt-block .dw-bar-wrap{
      width: min(var(--bar-fixed-w), 100%);
      margin: 0 auto;
      display:block;
    }

    #bt-block .dw-bar-track{
      position: relative;
      width: 100%;
      height: 18px;
      background: rgba(0,0,0,.04);
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

    /* ✅ text layer stays readable no matter fill width */
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

    /* zebra */
    
    #bt-block tbody tr:not(.dw-empty) td{ background:#ffffff; } /* base */
    #bt-block tbody tr.dw-zebra-odd  td{ background:var(--stripe); } /* striped */
    [[STRIPE_CSS]]




    #bt-block tbody td{
      border-bottom: 1px solid rgba(var(--brand-500-rgb), .08);
    }
    #bt-block tbody tr:hover td{
      background:linear-gradient(180deg, rgba(var(--brand-500-rgb), .16) 0%, rgba(var(--brand-500-rgb), .28) 100%) !important;
    }
    #bt-block tbody tr:hover{
      box-shadow:inset 4px 0 0 var(--brand-500);
      transform:none;
      transition:background-color .14s ease, box-shadow .14s ease;
    }

    #bt-block thead th{position:sticky; top:0; z-index:5}

    #bt-block tr.dw-empty td{
      text-align:center; color:#6b7280; font-style:italic; padding:18px 14px;
      background: var(--brand-50) !important;
    }

    /* Footer */
    .vi-table-embed .vi-footer {
      display:flex;
      align-items:center;
      padding:10px 18px;
      min-height:88px;
      height:88px;
      border-top:1px solid var(--footer-border);
      background:linear-gradient(180deg, rgba(255,255,255,.96), rgba(var(--brand-500-rgb), .05));
      backdrop-filter:none;
      flex: 0 0 88px;
      z-index: 30;
      overflow:hidden;
      width:100%;
      min-width:0;
    }
    .vi-table-embed .footer-inner{
      display:flex;
      justify-content:flex-end;
      align-items:center;
      gap:16px;
      min-height:100%;
      height:100%;
      width:100%;
      min-width:0;
      flex-wrap:nowrap;
      overflow:hidden;
    }
    .vi-table-embed.footer-center .footer-inner{ justify-content:center; }
    .vi-table-embed.footer-left .footer-inner{ justify-content:flex-start; }

    /* Footer notes layout */
    .vi-table-embed .footer-inner{
      justify-content:space-between;
    }
    
    /* ✅ Wrapper gives us “card” spacing + keeps layout stable */
    .vi-table-embed .footer-notes-wrap{
      flex: 1 1 0;
      min-width: 0;
      display:flex;
      align-items:center;
      padding-right: 10px;
    }
    
    /* ✅ Auto-expand notes to all available width */
    .vi-table-embed .footer-notes{
      flex: 1 1 0;
      width: 100%;
      max-width: none;   /* ✅ THIS is the key change */
    
      padding: 10px 12px;
      border-radius:0;
    
      background: #ffffff;
      border: 1px solid rgba(0,0,0,.10);
      box-shadow: 0 10px 22px rgba(0,0,0,.08);
    
      border-left: 6px solid var(--brand-500);
    
      font: 12.5px/1.25 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;
      color:#374151;
    
      max-height: 46px;
      overflow:auto;
    }
        
    /* Optional typographic polish */
    .vi-table-embed .footer-notes strong{ color:#111827; font-weight:750; }
    .vi-table-embed .footer-notes em{ color:#374151; }
    
    /* nicer scrollbar */
    .vi-table-embed .footer-notes::-webkit-scrollbar{ width: 6px; height: 6px; }
    .vi-table-embed .footer-notes::-webkit-scrollbar-thumb{
      background: rgba(var(--brand-500-rgb), .45);
      border-radius: 9999px;
    }
    
    .vi-table-embed .footer-logo{
      flex: 0 0 auto;
      display:flex;
      justify-content:flex-start;
      align-items:center;
      min-width:180px;
      min-height:100%;
      overflow:hidden;
    }

    .vi-table-embed .footer-embed-wrap{
      flex: 0 0 auto;
      flex-shrink:0;
      display:flex;
      align-items:center;
      justify-content:flex-end;
      min-width:max-content;
      min-height:100%;
      margin-left:auto;
      position:relative;
      overflow:visible;
      z-index:40;
    }
    .vi-table-embed .footer-embed-wrap.vi-hide{ display:none !important; }
    .vi-table-embed .dw-embed-slot{
      position:relative;
      overflow:visible;
      z-index:40;
    }
    .vi-table-embed.footer-with-embed .footer-inner{
      flex-direction: row !important;
      justify-content: space-between !important;
    }
    .vi-table-embed.footer-with-embed .footer-logo{
      justify-content:flex-start;
      margin-right:auto;
    }
    .vi-table-embed.footer-with-embed .footer-embed-wrap{
      margin-left:16px;
    }

    .vi-table-embed .footer-scale-wrap{
      display:flex;
      align-items:center;
      min-width: 220px;     /* mobile-safe default */
      max-width: 340px;     /* mobile-safe default */
      flex: 0 0 auto;       /* default compact */
    }
    
    /* ✅ Desktop: allow scale to grow wider (up to half the footer/table) */
    @media (min-width: 900px){
      .vi-table-embed .footer-scale-wrap{
        flex: 1 1 0;
        max-width: 50%;
        min-width: 340px;
      }
    }

    .vi-table-embed .footer-scale{
      width: 100%;
      display:flex;
      flex-direction:column;
      gap:6px;
      padding: 8px 10px;
      border-radius:0;
      background:#ffffff;
      border: 1px solid rgba(0,0,0,.10);
      box-shadow: 0 10px 22px rgba(0,0,0,.08);
      border-left: 6px solid var(--brand-500);
    }

    .vi-table-embed .footer-scale .scale-bar{
      height: 10px;
      border-radius: 999px;
      overflow:hidden;
      border: 1px solid rgba(0,0,0,.10);
    }

    .vi-table-embed .footer-scale .scale-labels{
      display:flex;
      justify-content:space-between;
      font: 11.5px/1 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;
      color:#6b7280;
    }

    /* If scale is hidden */
    .vi-table-embed .footer-scale-wrap.vi-hide{ display:none !important; }

    /* When logo is LEFT, swap order so notes go to the right */
    .vi-table-embed.footer-left .footer-inner{ flex-direction: row-reverse; }
    .vi-table-embed.footer-left .footer-logo{ justify-content:flex-start; }

    /* When centered requested but notes are enabled, we treat it like RIGHT (handled in Python) */
    .vi-table-embed .vi-footer img{
      height: var(--footer-logo-h);
      width: auto !important;
      max-width: 190px;
      max-height: 44px;
      display:inline-block;
      object-fit: contain;
      vertical-align: middle;
    }

    .vi-table-embed.brand-actionnetwork .vi-footer img{
      filter: brightness(0) saturate(100%) invert(62%) sepia(23%) saturate(1250%) hue-rotate(78deg) brightness(96%) contrast(92%); width: auto;
      display: inline-block;
    }
    .vi-table-embed.brand-vegasinsider .vi-footer img{ filter: none !important; }
    .vi-table-embed.brand-canadasb .vi-footer img{
      filter: brightness(0) saturate(100%) invert(32%) sepia(85%) saturate(2386%) hue-rotate(347deg) brightness(96%) contrast(104%); }
    .vi-table-embed.brand-rotogrinders .vi-footer img{
      filter: brightness(0) saturate(100%) invert(23%) sepia(95%) saturate(1704%) hue-rotate(203deg) brightness(93%) contrast(96%); }
    .vi-table-embed.brand-bolavip .vi-footer img{ filter: none !important; width: auto; display: inline-block; }
    .vi-table-embed.brand-aceodds .vi-footer img{ filter: none !important; width: auto; display: inline-block; }

    .vi-hide{ display:none !important; }

    /* EXPORT MODE */
    .vi-table-embed.export-mode .vi-table-header{ display:none !important; }
    .vi-table-embed.export-mode #bt-block .dw-controls,
    .vi-table-embed.export-mode #bt-block .dw-page-status{ display:none !important; }
    .vi-table-embed.export-mode #bt-block .dw-scroll{ max-height:none !important; height:auto !important; overflow:visible !important; }
    .vi-table-embed.export-mode #bt-block thead th{ position:static !important; }
    .vi-table-embed.export-mode #bt-block tbody tr:hover,
    .vi-table-embed.export-mode #bt-block tbody tr:hover td{ transform:none !important; box-shadow:none !important; }
    .vi-table-embed.export-mode #bt-block table.dw-table{
      table-layout:auto !important;
      width:max-content !important;
      min-width:100% !important;
    }
    .vi-table-embed.export-mode #bt-block .dw-scroll.no-scroll{
      overflow-x: visible !important;
      overflow-y: visible !important;
    }
  
#bt-block .dw-controls{
  padding: 0 12px;
}
#bt-block .dw-card{
  margin: 0;
  border-radius: 0;
}
#bt-block .dw-scroll{
  margin: 0;
}

#bt-block .dw-page-status{
  margin: 0 !important;
  min-height: 16px;
  flex: 0 0 auto;
}

</style>
<!-- Header -->
<div class="vi-table-header [[HEADER_ALIGN_CLASS]] [[HEADER_VIS_CLASS]]">
<div class="vi-header-main">
<span class="title [[TITLE_CLASS]]">[[TITLE]]</span>
<span class="subtitle">[[SUBTITLE]]</span>
</div>
<div class="vi-header-actions [[HEADER_EMBED_TARGET_VIS_CLASS]]" data-embed-target="header">
<button class="dw-btn dw-download dw-embed-trigger dw-embed-trigger-header" type="button">Embed / Download</button>
</div>
</div>
<!-- Table block -->
<div data-dw="table" id="bt-block">
<div class="dw-controls [[CONTROLS_VIS_CLASS]]">
<div class="left">
<div class="dw-field [[SEARCH_VIS_CLASS]]">
<input aria-label="Search Table" class="dw-input" placeholder="Search Table…" type="search"/>
<button aria-label="Clear Search" class="dw-clear" type="button">×</button>
</div>
</div>
<div class="right">
<!-- Pager -->
<div class="dw-pager [[PAGER_VIS_CLASS]]">
<label class="dw-status" for="bt-size" style="margin-right:2px;">Rows/Page</label>
<select class="dw-select" id="bt-size">
<option selected="" value="10">10</option>
<option value="15">15</option>
<option value="20">20</option>
<option value="25">25</option>
<option value="30">30</option>
<option value="0">All</option>
</select>
<button aria-label="Previous Page" class="dw-btn" data-page="prev">‹</button>
<button aria-label="Next Page" class="dw-btn" data-page="next">›</button>
</div>
<!-- Embed/Download -->
<div class="dw-embed-slot [[BODY_EMBED_TARGET_VIS_CLASS]]" data-embed-target="body"><div class="dw-embed [[EMBED_VIS_CLASS]]">
<button class="dw-btn dw-download" id="dw-download-png" type="button">Embed / Download</button>
<div aria-label="Download Menu" class="dw-download-menu vi-hide" id="dw-download-menu">
<div class="dw-menu-title" id="dw-menu-title">Choose action</div>
<!-- Full table options -->
<button class="dw-menu-btn" id="dw-dl-top10" type="button">Download Top 10</button>
<button class="dw-menu-btn" id="dw-dl-bottom10" type="button">Download Bottom 10</button>
<button class="dw-menu-btn" id="dw-dl-csv" type="button">Download CSV</button>
<button class="dw-menu-btn" id="dw-embed-script" type="button">Copy HTML</button>
<!-- Current view options (shown only when filter is active) -->
<button class="dw-menu-btn vi-hide" id="dw-dl-csv-current" type="button">Download Current View CSV</button>
<button class="dw-menu-btn vi-hide" id="dw-dl-image-current" type="button">Download Current View Image</button>
<button class="dw-menu-btn vi-hide" id="dw-copy-html-current" type="button">Copy Current View HTML</button>
</div>
</div></div>
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
<div class="dw-page-status [[PAGE_STATUS_VIS_CLASS]]" style="padding:8px 4px 0; margin:0; color:#7a808d; font:12px/1.2 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
<span id="dw-page-status-text"></span>
</div>
</div>
<!-- Footer -->
<div class="vi-footer [[FOOTER_VIS_CLASS]]" role="contentinfo">
<div class="footer-inner">
<div class="footer-scale-wrap [[FOOTER_SCALE_VIS_CLASS]]">
[[FOOTER_SCALE_HTML]]
</div>
<div class="footer-notes-wrap [[FOOTER_NOTES_VIS_CLASS]]">
<div class="footer-notes">[[FOOTER_NOTES_HTML]]</div>
</div>
<div class="footer-logo">
<img alt="[[BRAND_LOGO_ALT]]" decoding="async" height="auto" loading="lazy" src="[[BRAND_LOGO_URL]]" width="160"/>
</div>
<div class="footer-embed-wrap [[FOOTER_EMBED_TARGET_VIS_CLASS]]" data-embed-target="footer">
<button class="dw-btn dw-download dw-embed-trigger dw-embed-trigger-footer" type="button">Embed / Download</button>
</div>
</div>
</div>
<div aria-hidden="true" class="dw-modal-backdrop vi-hide" id="dw-embed-modal">
<div aria-labelledby="dw-modal-title" aria-modal="true" class="dw-modal" role="dialog">
<div class="dw-modal-head">
<div class="dw-menu-title" id="dw-modal-title">Choose action</div>
<button aria-label="Close" class="dw-modal-close" id="dw-modal-close" type="button">×</button>
</div>
<div class="dw-modal-actions">
<button class="dw-menu-btn" id="dw-modal-top10" type="button">Download Top 10</button>
<button class="dw-menu-btn" id="dw-modal-bottom10" type="button">Download Bottom 10</button>
<button class="dw-menu-btn" id="dw-modal-csv" type="button">Download CSV</button>
<button class="dw-menu-btn" id="dw-modal-embed" type="button">Copy HTML</button>
<button class="dw-menu-btn vi-hide" id="dw-modal-csv-current" type="button">Download Current View CSV</button>
<button class="dw-menu-btn vi-hide" id="dw-modal-image-current" type="button">Download Current View Image</button>
<button class="dw-menu-btn vi-hide" id="dw-modal-html-current" type="button">Copy Current View HTML</button>
</div>
</div>
</div>
<script>
  (function(){
    const root = document.getElementById('bt-block');
    if (!root || root.dataset.dwInit === '1') return;
    root.dataset.dwInit='1';

    const table = root.querySelector('table.dw-table');
    const tb = table ? table.tBodies[0] : null;
    const ALL_ROWS = tb ? Array.from(tb.rows).filter(r => !r.classList.contains('dw-empty')) : [];
    const PREVIEW_LIMIT = ALL_ROWS.length;     // full table
    const PREVIEW_ROWS = ALL_ROWS;             // full table
    ALL_ROWS.forEach((r, i) => { r.dataset.idx = String(i); });
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
    const widgetRoot = document.querySelector('section.vi-table-embed');
    const downloadBtn = embedWrap ? embedWrap.querySelector('#dw-download-png') : null;
    const headerTrigger = widgetRoot ? widgetRoot.querySelector('.dw-embed-trigger-header') : null;
    const footerTrigger = widgetRoot ? widgetRoot.querySelector('.dw-embed-trigger-footer') : null;
    const triggerButtons = [downloadBtn, headerTrigger, footerTrigger].filter(Boolean);

    const menu = embedWrap ? embedWrap.querySelector('#dw-download-menu') : null;
    if (menu) {
      menu.classList.add('vi-hide');
      menu.style.display = 'none';
      menu.setAttribute('aria-hidden', 'true');
    }

    const modal = widgetRoot ? widgetRoot.querySelector('#dw-embed-modal') : null;
    const modalTitle = modal ? modal.querySelector('#dw-modal-title') : null;
    const modalClose = modal ? modal.querySelector('#dw-modal-close') : null;
    const btnTop10 = modal ? modal.querySelector('#dw-modal-top10') : null;
    const btnBottom10 = modal ? modal.querySelector('#dw-modal-bottom10') : null;
    const btnCsv = modal ? modal.querySelector('#dw-modal-csv') : null;
    const btnEmbed = modal ? modal.querySelector('#dw-modal-embed') : null;

    // current-view buttons
    const btnCsvCurrent = modal ? modal.querySelector('#dw-modal-csv-current') : null;
    const btnImgCurrent = modal ? modal.querySelector('#dw-modal-image-current') : null;
    const btnHtmlCurrent = modal ? modal.querySelector('#dw-modal-html-current') : null;

    const menuTitle = modalTitle;
    window.__viMenuTitleEl = menuTitle;

    const emptyRow = tb.querySelector('.dw-empty');
    const pageStatus = document.getElementById('dw-page-status-text');

    const hasSearch = !controlsHidden
      && !!searchFieldWrap && !searchFieldWrap.classList.contains('vi-hide')
      && !!searchInput && !!clearBtn;

    const hasPager = !controlsHidden
      && !!pagerWrap && !pagerWrap.classList.contains('vi-hide')
      && !!sizeSel && !!prevBtn && !!nextBtn;

    const hasEmbed = triggerButtons.length > 0
      && !!modal
      && !!modalTitle
      && !!btnTop10
      && !!btnBottom10
      && !!btnCsv
      && !!btnEmbed;

    let pageSize = hasPager ? (parseInt(sizeSel.value,10) || 10) : 0;
    let page = 1;
    let filter = '';
    filter = (searchInput?.value || '').toLowerCase().trim();

    function isFilterActive(){
      const typed = (searchInput && typeof searchInput.value === 'string')
        ? searchInput.value.trim()
        : '';
      const live = (filter || '').trim();
      return typed.length > 0 || live.length > 0;
    }

    
    function syncMenuOptions(){
      const filtered = isFilterActive();
    
      // Full-table options
      if (btnTop10)   btnTop10.classList.toggle('vi-hide', filtered);
      if (btnBottom10) btnBottom10.classList.toggle('vi-hide', filtered);
      if (btnCsv)     btnCsv.classList.toggle('vi-hide', filtered);
      if (btnEmbed)   btnEmbed.classList.toggle('vi-hide', filtered);
    
      // Current-view options
      if (btnCsvCurrent)  btnCsvCurrent.classList.toggle('vi-hide', !filtered);
      if (btnImgCurrent)  btnImgCurrent.classList.toggle('vi-hide', !filtered);
      if (btnHtmlCurrent) btnHtmlCurrent.classList.toggle('vi-hide', !filtered);
    
      // Optional title clarity
      if (menuTitle){
        menuTitle.textContent = filtered ? 'Current view actions' : 'Choose action';
      }
    }




    function syncMeasuredScrollerHeight(){
      if (!widgetRoot || !scroller || !table || !tb) return;

      const theadEl = table.tHead;
      const visibleRows = Array.from(tb.rows).filter(row =>
        !row.classList.contains('dw-empty') && row.style.display !== 'none'
      );

      const shownCount = visibleRows.length;
      const rowHeights = visibleRows.map(row => row.getBoundingClientRect().height || 0).filter(Boolean);
      const fallbackRowHeight = rowHeights[0] || 54;
      const theadHeight = theadEl ? Math.ceil(theadEl.getBoundingClientRect().height || 0) : 0;

      const compactMode = shownCount <= 10;
      const rowsForWindow = compactMode ? Math.max(shownCount, 1) : 10;

      let bodyRowsHeight = 0;
      for (let i = 0; i < rowsForWindow; i++) {
        bodyRowsHeight += Math.ceil(rowHeights[i] || fallbackRowHeight);
      }

      const horizontalScrollbarAllowance = compactMode ? 0 : 12;
      const bottomFadeAllowance = 0;
      const safetyBuffer = compactMode ? 2 : 2;
      const finalScrollHeight = Math.ceil(
        theadHeight + bodyRowsHeight + horizontalScrollbarAllowance + bottomFadeAllowance + safetyBuffer
      );

      scroller.classList.toggle('compact-fit', compactMode);
      scroller.style.height = `${finalScrollHeight}px`;
      scroller.style.maxHeight = `${finalScrollHeight}px`;
      scroller.style.overflowX = 'auto';
      scroller.style.overflowY = compactMode ? 'hidden' : 'auto';
    }

    const onScrollShadow = ()=> scroller.classList.toggle('scrolled', scroller.scrollTop > 0);
    scroller.addEventListener('scroll', onScrollShadow); onScrollShadow();

    const heads = Array.from(table.tHead.rows[0].cells);

    function normalizeHeaderText(raw){
      return String(raw || '')
        .replace(/_/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
    }

    function buildBalancedHeaderHTML(raw, maxLines = 3, targetLineLen = 16){
      const txt = normalizeHeaderText(raw);
      if (!txt) return '';

      const words = txt.split(' ').filter(Boolean);
      if (words.length <= 1) return txt;

      let best = null;

      function scoreLines(lines){
        const lengths = lines.map(line => line.length);
        const longest = Math.max(...lengths);
        const shortest = Math.min(...lengths);
        const total = lengths.reduce((a,b) => a + b, 0);
        const avg = total / lengths.length;

        let score = 0;
        score += (lines.length - 1) * 6;
        score += Math.abs(longest - targetLineLen) * 1.8;
        score += (longest - shortest) * 2.4;
        score += lengths.reduce((acc, len) => acc + Math.abs(len - avg) * 0.9, 0);
        score += lengths.reduce((acc, len) => acc + (len > targetLineLen ? (len - targetLineLen) * 4.5 : 0), 0);
        score += lengths.reduce((acc, len) => acc + (len < 4 ? 12 : 0), 0);
        if (lines.length >= 2 && lengths[lines.length - 1] <= 4) score += 10;
        if (lines.length === 3 && lengths[2] < lengths[1] * 0.45) score += 8;
        return score;
      }

      function explore(startIdx, linesLeft, currentLines){
        const remainingWords = words.length - startIdx;
        if (remainingWords <= 0) {
          const score = scoreLines(currentLines);
          if (!best || score < best.score) best = {score, lines: currentLines.slice()};
          return;
        }

        if (linesLeft <= 0) return;

        const minTake = 1;
        const maxTake = remainingWords - Math.max(0, linesLeft - 1);

        for (let take = minTake; take <= maxTake; take++) {
          const line = words.slice(startIdx, startIdx + take).join(' ');
          currentLines.push(line);
          explore(startIdx + take, linesLeft - 1, currentLines);
          currentLines.pop();
        }
      }

      for (let lines = 1; lines <= Math.min(maxLines, words.length); lines++) {
        explore(0, lines, []);
      }

      return best && best.lines && best.lines.length ? best.lines.join('<br>') : txt;
    }

    function buildFixedWordsHeaderHTML(raw, wordsPerLine = 2){
      const txt = normalizeHeaderText(raw);
      const take = Math.max(1, parseInt(wordsPerLine || 0, 10) || 1);
      if (!txt) return '';

      const words = txt.split(' ').filter(Boolean);
      if (!words.length) return txt;

      const lines = [];
      for (let i = 0; i < words.length; i += take) {
        lines.push(words.slice(i, i + take).join(' '));
      }
      return lines.join('<br>');
    }

    function applyBalancedHeaderWrap(rootEl){
      const scope = rootEl || table;
      const ths = Array.from(scope.querySelectorAll('#bt-block thead th, thead th'));
      ths.forEach((th) => {
        let label = th.querySelector('.dw-th-label');
        if (!label) {
          const txt = (th.textContent || '').trim();
          th.textContent = '';
          label = document.createElement('span');
          label.className = 'dw-th-label';
          th.appendChild(label);
          label.textContent = txt;
        }

        const raw = th.getAttribute('data-header-original')
          || (label.innerHTML || '').replace(/<br\s*\/?>/gi, ' ')
          || label.textContent
          || th.textContent
          || '';
        th.setAttribute('data-header-original', raw);

        const fixedWords = parseInt(th.getAttribute('data-header-wrap-words') || '0', 10) || 0;
        if (fixedWords > 0) {
          label.innerHTML = buildFixedWordsHeaderHTML(raw, fixedWords);
        } else {
          label.innerHTML = buildBalancedHeaderHTML(raw, 3, 16);
        }
      });
    }

    function applySmartHeaderWidths(rootEl){
      const scope = rootEl || table;
      const ths = Array.from(scope.querySelectorAll('#bt-block thead th, thead th'));
      ths.forEach((th) => {
        const label = th.querySelector('.dw-th-label');
        if (!label) return;

        const html = (label.innerHTML || '').trim();
        const hasManualWrap = (parseInt(th.getAttribute('data-header-wrap-words') || '0', 10) || 0) > 0;
        const hasLineBreaks = /<br\s*\/?>/i.test(html);
        if (!hasManualWrap && !hasLineBreaks) {
          th.style.minWidth = '';
          return;
        }

        const rawLines = html
          .split(/<br\s*\/?>/i)
          .map(s => s.replace(/<[^>]*>/g, '').trim())
          .filter(Boolean);

        if (!rawLines.length) return;

        const longest = rawLines.reduce((m, line) => Math.max(m, line.length), 0);
        const px = Math.max(92, Math.min(260, Math.round((longest * 9) + 34)));
        th.style.minWidth = px + 'px';
      });
    }

    // Wrap header text in span, then format into balanced 1–3 lines using whole words only
    applyBalancedHeaderWrap(table);
    applySmartHeaderWidths(table);

    heads.forEach((th,i)=>{
      th.classList.add('sortable'); th.setAttribute('aria-sort','none'); th.dataset.sort='none'; th.tabIndex=0;
      const type = th.dataset.type || 'text';
      const go = ()=> sortBy(i,type,th);
      th.addEventListener('click',go);
      th.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); go(); } });
    });

    function textOf(tr,i){ return (tr.children[i].innerText||'').trim(); }

    function sortBy(colIdx, type, th){
      // ✅ sort against FULL dataset (not current page only)
      const rows = ALL_ROWS.slice();
    
      const current = th.dataset.sort || 'none';
      const next = current === 'none' ? 'asc' : current === 'asc' ? 'desc' : 'none';
    
      heads.forEach(h=>{
        h.dataset.sort = 'none';
        h.setAttribute('aria-sort','none');
        h.classList.remove('is-sorted');
      });
    
      // reset to original order
      if(next === 'none'){
        rows.sort((a,b)=>(+a.dataset.idx)-(+b.dataset.idx));
        rows.forEach(r=>tb.insertBefore(r, emptyRow));
        page = 1;
        renderPage();
        return;
      }
    
      th.dataset.sort = next;
      th.setAttribute('aria-sort', next === 'asc' ? 'ascending' : 'descending');
      th.classList.add('is-sorted');
    
      const mul = next === 'asc' ? 1 : -1;
    
      rows.sort((a,b)=>{
        let v1 = textOf(a,colIdx);
        let v2 = textOf(b,colIdx);
    
        // force numeric on rank-like columns too
        const isNum = (type || 'text') === 'num';
    
        if(isNum){
          v1 = parseFloat(String(v1).replace(/[^0-9.\-]/g,''));
          v2 = parseFloat(String(v2).replace(/[^0-9.\-]/g,''));
          if(Number.isNaN(v1)) v1 = -Infinity;
          if(Number.isNaN(v2)) v2 = -Infinity;
        }else{
          v1 = String(v1).toLowerCase();
          v2 = String(v2).toLowerCase();
        }
    
        if(v1 > v2) return 1 * mul;
        if(v1 < v2) return -1 * mul;
        return 0;
      });
    
      // write sorted order back to tbody
      rows.forEach(r=>tb.insertBefore(r, emptyRow));
    
      // ✅ always go to page 1 after sort
      page = 1;
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

    function applyVisibleZebra() {
      const rows = Array.from(tb.rows)
        .filter(tr => !tr.classList.contains('dw-empty') && tr.style.display !== 'none');
    
      rows.forEach((tr, i) => {
        tr.classList.remove('dw-zebra-even', 'dw-zebra-odd');
        tr.classList.add(i % 2 === 0 ? 'dw-zebra-odd' : 'dw-zebra-even');
      });
    }

    function renderPage(){
      // Always operate on CURRENT DOM order (after sortBy re-inserts rows)
      const ordered = Array.from(tb.rows).filter(r => !r.classList.contains('dw-empty'));
      const visible = ordered.filter(matchesFilter);
      const total = visible.length;
    
      // hide all real rows first
      ALL_ROWS.forEach(r => { r.style.display = 'none'; });
    
      let shown = [];
      if (total === 0){
        if (emptyRow){
          emptyRow.style.display = 'table-row';
          if (emptyRow.firstElementChild) emptyRow.firstElementChild.colSpan = heads.length;
        }
        if (hasPager){
          prevBtn.disabled = true;
          nextBtn.disabled = true;
        }
        setPageStatus(0, 0);
        applyVisibleZebra();
        syncMenuOptions();
        syncMeasuredScrollerHeight();
        return;
      }
    
      if (emptyRow) emptyRow.style.display = 'none';
    
      if (!hasPager || pageSize === 0){
        // show all filtered rows
        shown = visible;
        shown.forEach(r => { r.style.display = 'table-row'; });
        if (hasPager){
          prevBtn.disabled = true;
          nextBtn.disabled = true;
        }
        setPageStatus(total, 1);
      } else {
        const pages = Math.max(1, Math.ceil(total / pageSize));
        if (page > pages) page = pages;
        if (page < 1) page = 1;
    
        const start = (page - 1) * pageSize;
        const end = start + pageSize;
        shown = visible.slice(start, end);
    
        shown.forEach(r => { r.style.display = 'table-row'; });
    
        prevBtn.disabled = page <= 1;
        nextBtn.disabled = page >= pages;
        setPageStatus(total, pages);
      }
    
      applyVisibleZebra();
      syncMenuOptions();
      syncMeasuredScrollerHeight();
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
          syncMenuOptions();
        },120);
      });
    
      clearBtn.addEventListener('click', ()=>{
        searchInput.value='';
        syncClearBtn();
        filter='';
        page=1;
        renderPage();
        syncMenuOptions();
        searchInput.focus();
      });
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

    let lastTrigger = null;

    function positionMenu(anchor){
      if(!modal || !anchor || !widgetRoot) return;
      const panel = modal.querySelector('.dw-modal');
      if(!panel) return;

      const widgetRect = widgetRoot.getBoundingClientRect();
      const rect = anchor.getBoundingClientRect();
      const sidePad = 12;
      const gap = 10;

      const availableWidth = Math.max(220, widgetRect.width - (sidePad * 2));
      const panelWidth = Math.min(320, availableWidth);
      panel.style.width = `${panelWidth}px`;
      panel.style.maxWidth = `${availableWidth}px`;

      const panelHeight = panel.offsetHeight || 0;
      const anchorLeft = rect.left - widgetRect.left;
      const anchorRight = rect.right - widgetRect.left;
      const anchorTop = rect.top - widgetRect.top;
      const anchorBottom = rect.bottom - widgetRect.top;

      let left = anchorRight - panelWidth;
      left = Math.max(sidePad, Math.min(left, widgetRect.width - panelWidth - sidePad));

      const spaceBelow = widgetRect.height - anchorBottom - gap - sidePad;
      const spaceAbove = anchorTop - gap - sidePad;

      let top;
      if (spaceBelow >= panelHeight || spaceBelow >= spaceAbove) {
        top = anchorBottom + gap;
      } else {
        top = anchorTop - panelHeight - gap;
      }

      top = Math.max(sidePad, Math.min(top, widgetRect.height - panelHeight - sidePad));

      panel.style.left = `${left}px`;
      panel.style.top = `${top}px`;
      panel.style.right = 'auto';
      panel.style.bottom = 'auto';
      panel.style.transform = 'none';
    }

    function hideMenu(){
      if(modal){
        modal.classList.add('vi-hide');
        modal.setAttribute('aria-hidden','true');
      }
    }

    function showMenu(anchor){
      if(!modal) return;
      lastTrigger = anchor || lastTrigger;
      modal.classList.remove('vi-hide');
      modal.setAttribute('aria-hidden','false');
      requestAnimationFrame(()=> positionMenu(lastTrigger));
    }

    function toggleMenu(anchor){
      if(!modal) return;
      const willShow = modal.classList.contains('vi-hide');
      if (willShow) showMenu(anchor);
      else hideMenu();
    }

    if(hasEmbed){
      triggerButtons.forEach((btn)=>{
        btn.addEventListener('click', (e)=>{
          e.preventDefault();
          e.stopPropagation();
          toggleMenu(btn);
        });
      });
      if(modalClose){
        modalClose.addEventListener('click', (e)=>{
          e.preventDefault();
          hideMenu();
        });
      }
      if(modal){
        modal.addEventListener('click', (e)=>{
          if(e.target === modal) hideMenu();
        });
      }
      document.addEventListener('click', (e)=>{
        if(!modal || modal.classList.contains('vi-hide')) return;
        const panel = modal.querySelector('.dw-modal');
        const clickedTrigger = triggerButtons.some((btn)=> btn.contains(e.target));
        if (clickedTrigger) return;
        if (panel && !panel.contains(e.target)) hideMenu();
      });
      document.addEventListener('keydown', (e)=>{
        if(e.key === 'Escape') hideMenu();
      });
      window.addEventListener('resize', ()=> {
        if(modal && !modal.classList.contains('vi-hide')) positionMenu(lastTrigger);
      });
      window.addEventListener('scroll', ()=> {
        if(modal && !modal.classList.contains('vi-hide')) positionMenu(lastTrigger);
      }, true);
    }

    /* ===== PNG EXPORT (unchanged) ===== */
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

    function escapeCsvCell(value){
      const s = (value ?? "").toString().replace(/\r?\n/g, " ").trim();
      if (/[",\n]/.test(s)) {
        return '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    }

    function downloadCsv(){
      try{
        hideMenu();

        const headsText = heads.map(th => escapeCsvCell(th.innerText || th.textContent || ""));
        const headerLine = headsText.join(",");

        const ordered = PREVIEW_ROWS.slice();
        const filteredRows = ordered.filter(matchesFilter);

        const lines = [headerLine];

        filteredRows.forEach(tr => {
          const cells = Array.from(tr.cells).map(td => {
            const txt = td.innerText || td.textContent || "";
            return escapeCsvCell(txt);
          });
          lines.push(cells.join(","));
        });

        const csv = lines.join("\n");
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);

        const base = getFilenameBase(document.querySelector("section.vi-table-embed") || document.body);
        const filename = (base || "table").slice(0, 70) + ".csv";

        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();

        setTimeout(() => URL.revokeObjectURL(url), 1500);
      }catch(err){
        console.error("CSV export failed:", err);
      }
    }
    function downloadCurrentViewCsv(){
      hideMenu();
    
      const headers = heads.map(th => escapeCsvCell(th.innerText || th.textContent || ""));
      const lines = [headers.join(",")];
    
      const rows = Array.from(tb.rows).filter(r => !r.classList.contains('dw-empty'));
      const visibleRows = rows.filter(r => matchesFilter(r) && r.style.display !== 'none');
    
      visibleRows.forEach(tr => {
        const cells = Array.from(tr.cells).map(td => escapeCsvCell(td.innerText || td.textContent || ""));
        lines.push(cells.join(","));
      });
    
      const csv = lines.join("\n");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
    
      const a = document.createElement("a");
      a.href = url;
      a.download = "current_view.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1200);
    }

    function showRowsInClone(clone, mode){
      const cloneTb = clone.querySelector('#bt-block tbody');
      if (!cloneTb) return;

      const cloneRows = Array.from(cloneTb.rows).filter(r => !r.classList.contains('dw-empty'));
      const keep = new Set();

      // ✅ Use CURRENT live DOM order (respects sorting), but never filter
      const liveRowsInOrder = Array.from(tb.rows).filter(r => !r.classList.contains('dw-empty'));
      const orderedIdx = liveRowsInOrder.map(r => String(r.dataset.idx));

      if (mode === 'top10'){
        orderedIdx.slice(0, 10).forEach(id => keep.add(id));
      } else if (mode === 'bottom10'){
        orderedIdx.slice(-10).forEach(id => keep.add(id));
      } else if (mode === 'current'){
        // only what is currently visible in preview (i.e., after search filter)
        PREVIEW_ROWS.forEach(r => {
          if (r.style.display !== 'none') keep.add(String(r.dataset.idx));
        });
      } else {
        // fallback: show all preview rows
        PREVIEW_ROWS.forEach(r => keep.add(String(r.dataset.idx)));
      }

      // Show/hide clone rows by idx
      cloneRows.forEach(r => {
        const on = keep.has(String(r.dataset.idx));
        r.style.display = on ? 'table-row' : 'none';
        r.classList.remove('dw-zebra-odd', 'dw-zebra-even');
      });

      // Re-zebra visible rows
      const vis = cloneRows.filter(r => r.style.display !== 'none');
      vis.forEach((r, i) => {
        r.classList.add(i % 2 === 0 ? 'dw-zebra-odd' : 'dw-zebra-even');
      });

      const empty = cloneTb.querySelector('.dw-empty');
      if (empty) empty.style.display = vis.length ? 'none' : 'table-row';
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

      // ✅ export width = widget width (consistent, legible)
    const w = Math.max(900, Math.min(1600, Math.ceil(targetWidth || 1200)));
    clone.style.maxWidth = "none";
    clone.style.width = w + "px";
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
        if(window.__viMenuTitleEl){
          window.__viMenuTitleEl.textContent = "Export too large — try Top 10 / Bottom 10";
          setTimeout(()=>{ window.__viMenuTitleEl.textContent = "Choose action"; }, 2200);
        }
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
        // ✅ Export-only CSS overrides (does NOT touch interactive table)
       const exportStyle = document.createElement("style");
        exportStyle.textContent = `
          /* ✅ Keep export image width consistent with the on-page widget (prevents tiny-looking text)
             and still allows header wrapping via wrapExportHeaders() */
          .vi-table-embed.export-mode #bt-block table.dw-table{
            table-layout: auto !important;
            width: max-content !important;
            min-width: 100% !important;
          }
        
         /* keep cell-level clamp rules in control */
        .vi-table-embed.export-mode #bt-block thead th,
        .vi-table-embed.export-mode #bt-block tbody td{
          vertical-align: middle !important;
        }

          .vi-table-embed.export-mode{
                      font-size: 16px !important;
                    }
                    .vi-table-embed.export-mode #bt-block thead th{
                      font-size: 16px !important;
                    }
                    .vi-table-embed.export-mode #bt-block tbody td{
                      font-size: 16px !important;
                    }
        
          /* ✅ REMOVE SORT ARROWS IN EXPORT MODE */
          .vi-table-embed.export-mode #bt-block thead th.sortable::after{
            content: "" !important;
          }
        
          \
/* ✅ Header: keep <th> as table-cell in export (prevents stacked header bug) */
        .vi-table-embed.export-mode #bt-block thead th{
          white-space: normal !important;
          line-height: 1.15 !important;
          padding-top: 10px !important;
          padding-bottom: 10px !important;

          /* no mid-word splitting */
          overflow-wrap: normal !important;
          word-break: normal !important;
          hyphens: none !important;

          /* IMPORTANT: do not change display on <th> */
          overflow: visible !important;
          text-overflow: clip !important;
        }

        /* ✅ Export: keep full wrapped labels visible */
        .vi-table-embed.export-mode #bt-block thead th .dw-th-label{
          display: inline-block !important;
          overflow: visible !important;
          text-overflow: clip !important;
          white-space: normal !important;
          overflow-wrap: normal !important;
          word-break: normal !important;
          hyphens: none !important;
          padding: 10px 14px !important;
          text-align: center !important;
          line-height: 1.15 !important;
        }

        .vi-table-embed.export-mode #bt-block thead th{
          padding: 0 !important;
          vertical-align: middle !important;

          /* override clamp props (flex can't clamp reliably) */
          -webkit-line-clamp: unset !important;
          line-clamp: unset !important;
          -webkit-box-orient: unset !important;
        }
        
          /* ✅ Keep SAME 3-line clamp behavior in export (match interactive table) */
        .vi-table-embed.export-mode #bt-block .dw-cell{
          white-space: normal !important;
          word-break: normal !important;      /* no mid-word split */
          overflow-wrap: normal !important;   /* wrap only at normal word boundaries */
          hyphens: none !important;
        
          line-height: 1.35 !important;
        
          display: -webkit-box !important;
          -webkit-box-orient: vertical !important;
          -webkit-line-clamp: 3 !important;
          line-clamp: 3 !important;
        
          overflow: hidden !important;
          text-overflow: ellipsis !important;
        }
        
          /* ✅ Export should never compress the bar columns */
          .vi-table-embed.export-mode #bt-block th.dw-bar-col,
          .vi-table-embed.export-mode #bt-block td.dw-bar-td{
            min-width: calc(var(--bar-fixed-w) + 70px) !important;
          }
        `;
        clone.appendChild(exportStyle);

        stage.appendChild(clone);
        document.body.appendChild(stage);
        function wrapExportHeaders(clone){
          const ths = clone.querySelectorAll('#bt-block thead th');
        
          ths.forEach(th => {
            let label = th.querySelector('.dw-th-label');
            if(!label){
              label = document.createElement('span');
              label.className = 'dw-th-label';
              label.textContent = (th.textContent || '').trim();
              th.textContent = '';
              th.appendChild(label);
            }
        
            const raw = th.getAttribute('data-header-original')
              || (label.innerHTML || '').replace(/<br\s*\/?>/gi, ' ')
              || label.textContent
              || '';
            th.setAttribute('data-header-original', raw);

            const fixedWords = parseInt(th.getAttribute('data-header-wrap-words') || '0', 10) || 0;
            if (fixedWords > 0) {
              label.innerHTML = buildFixedWordsHeaderHTML(raw, fixedWords);
            } else {
              label.innerHTML = buildBalancedHeaderHTML(raw, 3, 16);
            }
          });
        }
        function applySmartHeaderWidthsInClone(cloneRoot){
          const ths = cloneRoot.querySelectorAll('#bt-block thead th');
          ths.forEach(th => {
            const label = th.querySelector('.dw-th-label');
            if(!label) return;
            const html = (label.innerHTML || '').trim();
            const hasManualWrap = (parseInt(th.getAttribute('data-header-wrap-words') || '0', 10) || 0) > 0;
            const hasLineBreaks = /<br\s*\/?>/i.test(html);
            if (!hasManualWrap && !hasLineBreaks) {
              th.style.minWidth = '';
              return;
            }
            const rawLines = html
              .split(/<br\s*\/?>/i)
              .map(s => s.replace(/<[^>]*>/g, '').trim())
              .filter(Boolean);
            if (!rawLines.length) return;
            const longest = rawLines.reduce((m, line) => Math.max(m, line.length), 0);
            const px = Math.max(92, Math.min(260, Math.round((longest * 9) + 34)));
            th.style.minWidth = px + 'px';
          });
        }

        // ✅ Call before capture (export-only)
        wrapExportHeaders(clone);
        applySmartHeaderWidthsInClone(clone);

        showRowsInClone(clone, mode);

        const base = getFilenameBase(clone);
        const suffix = mode === 'bottom10' ? "_bottom10" : "_top10";
        const filename = (base + suffix).slice(0, 70);

        // ✅ Choose export width: match the on-page widget width (prevents tiny illegible PNGs)
        await new Promise(r => requestAnimationFrame(()=>requestAnimationFrame(r)));

        const widgetW = Math.ceil(widget.getBoundingClientRect().width || 1200);
        const fullTableWidth = Math.max(900, Math.min(1600, widgetW));

        await captureCloneToPng(clone, stage, filename, fullTableWidth);

      }catch(err){
        console.error("PNG export failed:", err);
      }
    }

    function getCurrentViewHtml(){
      const clone = document.documentElement.cloneNode(true);
    
      const cloneTb = clone.querySelector('#bt-block tbody');
      if (!cloneTb) return '<!doctype html>\n' + clone.outerHTML;
    
      const liveRows = Array.from(tb.rows).filter(r => !r.classList.contains('dw-empty'));
      const cloneRows = Array.from(cloneTb.rows).filter(r => !r.classList.contains('dw-empty'));
    
      cloneRows.forEach((r, i) => {
        const live = liveRows[i];
        const visible = !!live && matchesFilter(live) && live.style.display !== 'none';
        r.style.display = visible ? 'table-row' : 'none';
      });
    
      const empty = cloneTb.querySelector('.dw-empty');
      if (empty) empty.style.display = 'none';
    
      return '<!doctype html>\n' + clone.outerHTML;
    }
    
    async function onEmbedCurrentClick(){
      hideMenu();
      const code = getCurrentViewHtml();
      const ok = await copyToClipboard(code);
      if (menuTitle){
        menuTitle.textContent = ok ? 'Current view HTML copied!' : 'Copy failed (try again)';
        setTimeout(() => { menuTitle.textContent = 'Choose action'; }, 1800);
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

    function getCurrentViewHtml(){
      const clone = document.documentElement.cloneNode(true);
      const cloneTb = clone.querySelector('#bt-block table.dw-table tbody');
      if(!cloneTb) return '<!doctype html>\n' + clone.outerHTML;
    
      const liveRows = Array.from(tb.rows).filter(r => !r.classList.contains('dw-empty'));
      const cloneRows = Array.from(cloneTb.rows).filter(r => !r.classList.contains('dw-empty'));
    
      cloneRows.forEach((r, i)=>{
        const live = liveRows[i];
        const visible = !!live && matchesFilter(live) && live.style.display !== 'none';
        r.style.display = visible ? 'table-row' : 'none';
      });
    
      const empty = cloneTb.querySelector('.dw-empty');
      if(empty) empty.style.display = 'none';
    
      return '<!doctype html>\n' + clone.outerHTML;
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
    async function onEmbedCurrentClick(){
      hideMenu();
      const code = getCurrentViewHtml();
      const ok = await copyToClipboard(code);
    
      if (menuTitle){
        menuTitle.textContent = ok ? 'Current view HTML copied!' : 'Copy failed (try again)';
        setTimeout(() => { menuTitle.textContent = 'Choose action'; }, 1800);
      }
    }

    if(hasEmbed && btnTop10) btnTop10.addEventListener('click', ()=> downloadDomPng('top10'));
    if(hasEmbed && btnBottom10) btnBottom10.addEventListener('click', ()=> downloadDomPng('bottom10'));
    if(hasEmbed && btnCsv) btnCsv.addEventListener('click', downloadCsv);
    if(hasEmbed && btnEmbed) btnEmbed.addEventListener('click', onEmbedClick);
    if(hasEmbed && btnCsvCurrent) btnCsvCurrent.addEventListener('click', downloadCurrentViewCsv);
    if(hasEmbed && btnImgCurrent) btnImgCurrent.addEventListener('click', ()=> downloadDomPng('current'));
    if(hasEmbed && btnHtmlCurrent) btnHtmlCurrent.addEventListener('click', onEmbedCurrentClick);

    window.addEventListener('resize', syncMeasuredScrollerHeight);
    window.addEventListener('load', syncMeasuredScrollerHeight);
    renderPage();
    syncMenuOptions();
    syncMeasuredScrollerHeight();
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

def format_column_header(col_name: str, mode: str) -> str:
    s = str(col_name or "")
    mode = (mode or "").strip().lower()

    if mode.startswith("keep"):
        return s

    s2 = s.replace("_", " ").strip()
    s2 = re.sub(r"\s+", " ", s2)

    if not s2:
        return s

    if mode.startswith("sentence"):
        return s2[:1].upper() + s2[1:].lower()

    if mode.startswith("title"):
        return s2.title()

    if "caps" in mode:
        return s2.upper()

    return s



def remove_markdown_formatting(text: str) -> str:
    """Remove **bold** and *italic* markers while preserving the underlying text."""
    if not text:
        return ""
    s = str(text)

    # bold: **text**
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)

    # italic: *text*
    s = re.sub(r"\*(.+?)\*", r"\1", s)

    return s



def _bt_clear_formatting(state_key: str) -> None:
    """Clear formatting for a given session_state key (Ctrl+\ equivalent).
    Safe to use as an on_click callback for buttons tied to text inputs / text areas.
    """
    k = str(state_key or "").strip()
    if not k:
        return
    cleaned = remove_markdown_formatting(st.session_state.get(k, ""))
    st.session_state[k] = cleaned
    # keep any paired *_draft key in sync
    dk = f"{k}_draft"
    if dk in st.session_state:
        st.session_state[dk] = cleaned


# ======================================================
# Ultra-smooth live preview: commit-on-blur draft fields
# ======================================================
def _bt_commit_subtitle() -> None:
    # Commit draft subtitle to the canonical key used by config/preview/publish
    st.session_state["bt_widget_subtitle"] = st.session_state.get("bt_widget_subtitle_draft", "")

def _bt_commit_footer_notes() -> None:
    # Commit draft footer notes to the canonical key used by config/preview/publish
    st.session_state["bt_footer_notes"] = st.session_state.get("bt_footer_notes_draft", "")


def generate_table_html_from_df(
    df: pd.DataFrame,
    title: str,
    subtitle: str,
    brand_logo_url: str,
    brand_logo_alt: str,
    brand_class: str,
    title_style: str = "Keep original",
    subtitle_style: str = "Keep original",
    striped: bool = True,
    stripe_mode: str = "Odd",
    center_titles: bool = False,
    branded_title_color: bool = True,
    show_search: bool = True,
    show_pager: bool = True,
    show_embed: bool = True,
    embed_position: str = "Body",
    show_page_numbers: bool = True,
    show_header: bool = True,
    show_footer: bool = True,
    footer_logo_align: str = "Center",
    cell_align: str = "Center",
    footer_logo_h: int = 36,
    show_footer_notes: bool = False,
    footer_notes: str = "",
    show_heat_scale: bool = False,
    bar_columns: list[str] | None = None,
    bar_max_overrides: dict | None = None,
    bar_fixed_w: int = 200,
    heat_columns: list[str] | None = None,
    heat_overrides: dict | None = None,
    heat_strength: float = 0.55,
    heatmap_style: str = "Branded heatmap",
    header_style: str = "Keep original",
    col_header_overrides: dict | None = None,
    header_wrap_target: str = "Off",
    header_wrap_words: int = 2,
    col_format_rules: dict | None = None,
) -> str:

    df = df.copy()

    # Dynamic heights based on row count
    row_count = len(df.index)
    table_max_h = compute_widget_table_max_height(row_count)
    bar_columns_set = set(bar_columns or [])
    bar_max_overrides = bar_max_overrides or {}
    heat_columns_set = set(heat_columns or [])
    heat_overrides = heat_overrides or {}

    try:
        heat_strength = float(heat_strength)
    except Exception:
        heat_strength = 0.55
    heat_strength = max(0.10, min(0.85, heat_strength))

    # Safety clamp
    try:
        bar_fixed_w = int(bar_fixed_w)
    except Exception:
        bar_fixed_w = 200
    bar_fixed_w = max(120, min(360, bar_fixed_w))

    # Footer logo height clamp
    try:
        footer_logo_h = int(footer_logo_h)
    except Exception:
        footer_logo_h = 36
    footer_logo_h = max(16, min(90, footer_logo_h))
    try:
        header_wrap_words = int(header_wrap_words)
    except Exception:
        header_wrap_words = 2
    header_wrap_words = max(1, min(10, header_wrap_words))
    header_wrap_target = str(header_wrap_target or "Off").strip()

    # Footer notes (simple markdown: **bold** and *italic*)
    show_footer_notes = bool(show_footer_notes)
    footer_notes = (footer_notes or "").strip()
    footer_notes_html = ""
    if show_footer_notes and footer_notes:
        escaped = html_mod.escape(footer_notes)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
        escaped = escaped.replace("\n", "<br>")
        footer_notes_html = escaped
    # ✅ Heatmap scale (mutually exclusive with footer notes)
    show_heat_scale = bool(show_heat_scale)
    if show_footer_notes:
        show_heat_scale = False

    # Only show scale if user enabled it AND there is at least one heat column selected
    if show_heat_scale and not heat_columns_set:
        show_heat_scale = False

    footer_scale_html = ""
    if show_heat_scale:
        if (heatmap_style or "").strip().lower().startswith("standard"):
            bar_bg = "linear-gradient(90deg, #2ecc71, #3498db, #f1c40f, #e67e22, #e74c3c)"
        else:
            # branded gradient
            bar_bg = "linear-gradient(90deg, rgba(var(--brand-500-rgb), 0.05), rgba(var(--brand-500-rgb), 0.90))"

        footer_scale_html = f"""
          <div class="footer-scale" aria-label="Heatmap scale">
            <div class="scale-bar" style="background:{bar_bg};"></div>
            <div class="scale-labels"><span>Low</span><span>High</span></div>
          </div>
        """

    def parse_number(v) -> float:
        try:
            s = "" if pd.isna(v) else str(v)
            s = s.replace(",", "")
            s = re.sub(r"[^0-9.\-]", "", s)
            return float(s) if s else 0.0
        except Exception:
            return 0.0
    def format_numeric_for_display(raw_val, max_decimals: int = 2) -> str:
        """
        Limits numeric values to max 2 decimals (trim trailing zeros) and
        applies comma separators by default.
        Leaves integers as integers.
        Does NOT touch values that contain currency symbols, %, words, etc.
        """
        if pd.isna(raw_val):
            return ""

        s = str(raw_val).strip()

        # If it includes symbols/letters (%,$,etc) → do NOT reformat
        if re.search(r"[^\d\.\-\,\s]", s):
            return s

        # Normalize commas/spaces
        plain = re.sub(r"[,\s]", "", s)

        # Must be a plain number like -12 or 12.345
        if not re.fullmatch(r"-?\d+(\.\d+)?", plain):
            return s

        try:
            num = float(plain)
        except Exception:
            return s

        # Default display is comma-separated
        if abs(num - round(num)) < 1e-12:
            return f"{int(round(num)):,}"

        out = f"{num:,.{max_decimals}f}".rstrip("0").rstrip(".")
        return out
        # ✅ Column formatting rules (prefix/suffix/moneyline)
    col_format_rules = col_format_rules or {}

    def apply_column_formatting(col_name: str, display_val: str, raw_val) -> str:
        """
        Applies per-column formatting rules AFTER numeric formatting.

        Default numeric display uses comma separators.
        Supports combining multiple rules on the same column, e.g.:
          - plus_if_positive -> +1,234
          - prefix -> $1,234
          - plain_number + suffix -> 1234%
        """
        rules = col_format_rules.get(col_name) or {}

        raw_modes = rules.get("modes", None)
        if isinstance(raw_modes, (list, tuple, set)):
            modes = [str(m).strip().lower() for m in raw_modes if str(m).strip()]
        else:
            legacy_mode = str(rules.get("mode", "")).strip().lower()
            modes = [legacy_mode] if legacy_mode else []

        # Backward compatibility for legacy aliases
        modes = ["plus_if_positive" if m == "moneyline_plus" else m for m in modes]
        # Legacy comma_separator is now implicit default behaviour
        modes = [m for m in modes if m != "comma_separator"]

        # Preserve order but remove duplicates
        seen_modes = set()
        modes = [m for m in modes if not (m in seen_modes or seen_modes.add(m))]

        if display_val is None:
            return ""

        s = str(display_val).strip()
        if s == "":
            return s

        # Try to parse number from raw value (preferred), fallback to display string
        num = None
        try:
            num = parse_number(raw_val)
        except Exception:
            try:
                num = parse_number(s)
            except Exception:
                num = None

        # Legacy condition flags still supported for prefix/suffix
        only_pos = bool(rules.get("only_if_positive", False))
        only_neg = bool(rules.get("only_if_negative", False))
        only_nz = bool(rules.get("only_if_nonzero", False))

        if (only_pos or only_neg or only_nz) and num is None:
            return s
        if only_pos and not (num > 0):
            return s
        if only_neg and not (num < 0):
            return s
        if only_nz and not (num != 0):
            return s

        # Default numeric display is comma-separated; allow explicit override
        if "plain_number" in modes and num is not None:
            if abs(num - round(num)) < 1e-12:
                s = str(int(round(num)))
            else:
                s = f"{num:.2f}".rstrip("0").rstrip(".")

        if "plus_if_positive" in modes:
            if not s.startswith("+") and not s.startswith("-") and num is not None and num > 0:
                s = f"+{s}"

        # Then affixes
        if "prefix" in modes:
            pref = str(rules.get("prefix_value", rules.get("value", "")) or "")
            if pref:
                s = f"{pref}{s}"

        if "suffix" in modes:
            suf = str(rules.get("suffix_value", rules.get("value", "")) or "")
            if suf:
                s = f"{s}{suf}"

        return s

    def heat_background_css(pct_0_to_1: float, alpha: float) -> str:
        """
        Returns CSS for heat background based on selected style.
        - Branded: rgba overlay of brand color using alpha
        - Standard: 5-color scale (Green, Blue, Yellow, Orange, Red)
        """
        p = max(0.0, min(1.0, float(pct_0_to_1)))

        style = (heatmap_style or "").strip().lower()
        if "standard" in style:
            # 5 stops: green -> blue -> yellow -> orange -> red
            stops = ["#2ecc71", "#3498db", "#f1c40f", "#e67e22", "#e74c3c"]
            idx = int(round(p * (len(stops) - 1)))
            idx = max(0, min(len(stops) - 1, idx))
            color = stops[idx]

            # alpha controls opacity, same slider still works
            a = max(0.0, min(1.0, float(alpha)))
            return f"background-color: {color}; opacity: 1; background-image: linear-gradient(0deg, rgba(255,255,255, {1-a:.3f}), rgba(255,255,255, {1-a:.3f}));"

        # default branded
        return (
            f"background-image: linear-gradient(0deg, "
            f"rgba(var(--brand-500-rgb), {alpha:.3f}), "
            f"rgba(var(--brand-500-rgb), {alpha:.3f}));"
        )

    # ✅ Pre-compute max for each selected bar column (with optional override)
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
    
    # ✅ Pre-compute min/max for heat columns (with optional overrides)
    heat_minmax = {}
    for col in df.columns:
        if col in heat_columns_set and guess_column_type(df[col]) == "num":
            ov = heat_overrides.get(col, {}) or {}
            ov_min = ov.get("min", None)
            ov_max = ov.get("max", None)

            try:
                vals = df[col].apply(parse_number)
                auto_min = float(vals.min()) if len(vals) else 0.0
                auto_max = float(vals.max()) if len(vals) else 0.0
            except Exception:
                auto_min, auto_max = 0.0, 0.0

            mn = auto_min
            mx = auto_max

            if ov_min is not None:
                try:
                    mn = float(ov_min)
                except Exception:
                    pass
            if ov_max is not None:
                try:
                    mx = float(ov_max)
                except Exception:
                    pass

            if mx == mn:
                mx = mn + 1.0

            heat_minmax[col] = (mn, mx)

    # ✅ Detect text-heavy columns that should wrap at a fixed width
    text_wrap_columns = set()
    keyword_hints = {"name", "city", "team", "player", "school", "market", "county", "country", "region", "title"}
    for col in df.columns:
        if guess_column_type(df[col]) != "text":
            continue

        series = df[col].fillna("").astype(str).str.strip()
        lengths = series.str.len()
        max_len = int(lengths.max()) if len(lengths) else 0
        avg_len = float(lengths.mean()) if len(lengths) else 0.0
        col_key = str(col).strip().lower()

        if max_len > 18 or avg_len > 12 or any(hint in col_key for hint in keyword_hints):
            text_wrap_columns.add(col)

    # ✅ Header
    head_cells = []
    for col in df.columns:
        col_type = guess_column_type(df[col])
        _ov = (col_header_overrides or {})
        _base_label = _ov.get(col, col)
        if header_style == "Keep original":
            display_col = str(_base_label)
        else:
            display_col = format_column_header(str(_base_label), header_style)

        should_wrap_header = False
        wrap_words_for_col = header_wrap_words
        if header_wrap_target == "All columns":
            should_wrap_header = True
        elif header_wrap_target and header_wrap_target != "Off" and str(col) == header_wrap_target:
            should_wrap_header = True
        elif should_force_two_line_numeric_header(df[col], display_col):
            should_wrap_header = True
            wrap_words_for_col = 1

        if should_wrap_header:
            wrapped_lines = wrap_text_by_words(display_col, wrap_words_for_col).splitlines()
            safe_label = "<br>".join(html_mod.escape(line) for line in wrapped_lines if line.strip())
        else:
            safe_label = html_mod.escape(display_col)

        classes = []
        if col in bar_columns_set and col_type == "num":
            classes.append("dw-bar-col")
        if col in text_wrap_columns:
            classes.append("dw-text-col")
        class_attr = " ".join(classes)
        wrap_attr = f' data-header-wrap-words="{wrap_words_for_col}"' if should_wrap_header else ""
        original_attr = html_mod.escape(display_col, quote=True)

        head_cells.append(
            f'<th scope="col" data-type="{col_type}" data-header-original="{original_attr}" class="{class_attr}"{wrap_attr}>{safe_label}</th>'
        )

    table_head_html = "\n              ".join(head_cells)

    # ✅ Rows
    row_html_snippets = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            raw_val = row[col]
            display_val = format_numeric_for_display(raw_val, max_decimals=2)
            display_val = apply_column_formatting(col, display_val, raw_val)
            
            safe_val = html_mod.escape(display_val)
            safe_title = html_mod.escape(display_val, quote=True)

            if col in bar_columns_set and guess_column_type(df[col]) == "num":
                num_val = parse_number(row[col])
                denom = bar_max.get(col, 1.0) or 1.0
                pct_bar = max(0.0, min(100.0, (num_val / denom) * 100.0))

                # ✅ Heat behind bars (only if this col is also selected for heat)
                td_class = "dw-bar-td"
                td_style = ""

                if col in heat_columns_set and col in heat_minmax:
                    h_mn, h_mx = heat_minmax[col]
                    h_pct = (num_val - h_mn) / (h_mx - h_mn)
                    h_pct = max(0.0, min(1.0, h_pct))

                    # optional curve: makes low values more visible
                    h_pct = h_pct ** 0.8

                    min_alpha = 0.12
                    h_alpha = min_alpha + (h_pct * (heat_strength - min_alpha))

                    td_class = "dw-bar-td dw-heat-td"
                    td_style = f' style="{heat_background_css(h_pct, h_alpha)}"'

                cells.append(
                    f"""
                    <td class="{td_class}"{td_style}>
                      <div class="dw-bar-wrap" title="{safe_title}">
                        <div class="dw-bar-track">
                          <div class="dw-bar-fill" style="width:{pct_bar:.2f}%;"></div>
                          <div class="dw-bar-text">
                            <span class="dw-bar-pill">{safe_val}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    """
                )

            elif col in heat_columns_set and guess_column_type(df[col]) == "num" and col in heat_minmax:
                num_val = parse_number(row[col])
                mn, mx = heat_minmax[col]
                pct = (num_val - mn) / (mx - mn)
                pct = max(0.0, min(1.0, pct))

                # optional curve: makes low values more visible
                pct = pct ** 0.8

                min_alpha = 0.12
                alpha = min_alpha + (pct * (heat_strength - min_alpha))

                heat_style = heat_background_css(pct, alpha)

                cells.append(
                    f'<td class="dw-heat-td" style="{heat_style}"><div class="dw-cell" title="{safe_title}">{safe_val}</div></td>'
                )

            else:
                td_class = ' class="dw-text-col"' if col in text_wrap_columns else ""
                cells.append(f'<td{td_class}><div class="dw-cell" title="{safe_title}">{safe_val}</div></td>')

        row_html_snippets.append("            <tr>" + "".join(cells) + "</tr>")

    table_rows_html = "\n".join(row_html_snippets)
    colspan = str(len(df.columns))

    stripe_mode_norm = str(stripe_mode or "Odd").strip().lower()
    stripe_target_class = "dw-zebra-even" if stripe_mode_norm == "even" else "dw-zebra-odd"

    stripe_css = (
        f"""
    #bt-block tbody tr:not(.dw-empty) td{{ background:#ffffff; }} /* base */
    #bt-block tbody tr.{stripe_target_class} td{{ background:var(--stripe); }} /* striped */
    #bt-block tbody tr:not(.dw-empty):not(.{stripe_target_class}) td{{ background:#ffffff; }} /* plain */
    """
        if striped
        else """
    #bt-block tbody tr:not(.dw-empty) td{background:#ffffff;}
    """
    )

    header_class = "centered" if center_titles else ""
    title_class = "branded" if branded_title_color else ""

    # Apply optional casing rules to title/subtitle (same modes as header row)
    title_display = format_column_header(title, title_style)
    subtitle_display = format_column_header(subtitle, subtitle_style) if (subtitle or "").strip() else ""

    # Subtitle supports simple markdown (**bold** and *italic*) like footer notes
    subtitle_html = ""
    if (subtitle_display or "").strip():
        _s = html_mod.escape(subtitle_display)
        _s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _s)
        _s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", _s)
        subtitle_html = _s


    embed_position = (embed_position or "Body").strip().lower()
    if embed_position not in {"header", "footer", "body"}:
        embed_position = "body"

    if show_embed and embed_position == "footer":
        show_footer_notes = False
        footer_notes_html = ""

    header_vis = "" if show_header else "vi-hide"
    footer_vis = "" if show_footer else "vi-hide"

    body_embed_active = bool(show_embed and embed_position == "body")
    header_embed_active = bool(show_embed and embed_position == "header" and show_header)
    footer_embed_active = bool(show_embed and embed_position == "footer" and show_footer)

    controls_vis = "" if (show_search or show_pager or body_embed_active) else "vi-hide"
    search_vis = "" if show_search else "vi-hide"
    pager_vis = "" if show_pager else "vi-hide"
    embed_vis = "" if show_embed else "vi-hide"
    page_status_vis = "" if (show_page_numbers and show_pager) else "vi-hide"
    header_embed_target_vis = "" if header_embed_active else "vi-hide"
    body_embed_target_vis = "" if body_embed_active else "vi-hide"
    footer_embed_target_vis = "" if footer_embed_active else "vi-hide"

    footer_logo_align = (footer_logo_align or "Center").strip().lower()
    if footer_embed_active:
        footer_logo_align = "left"
    elif (show_footer_notes or show_heat_scale) and footer_logo_align == "center":
        footer_logo_align = "right"
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
        .replace("[[TITLE]]", html_mod.escape(title_display))
        .replace("[[SUBTITLE]]", subtitle_html)
        .replace("[[BRAND_LOGO_URL]]", brand_logo_url)
        .replace("[[BRAND_LOGO_ALT]]", html_mod.escape(brand_logo_alt))
        .replace("[[BRAND_CLASS]]", brand_class or "")
        .replace("[[STRIPE_CSS]]", stripe_css)
        .replace("[[HEADER_ALIGN_CLASS]]", header_class)
        .replace("[[TITLE_CLASS]]", title_class)
        .replace("[[HEADER_VIS_CLASS]]", header_vis)
        .replace("[[FOOTER_VIS_CLASS]]", footer_vis)
        .replace("[[EMBED_POSITION]]", embed_position)
        .replace("[[CONTROLS_VIS_CLASS]]", controls_vis)
        .replace("[[SEARCH_VIS_CLASS]]", search_vis)
        .replace("[[PAGER_VIS_CLASS]]", pager_vis)
        .replace("[[EMBED_VIS_CLASS]]", embed_vis)
        .replace("[[PAGE_STATUS_VIS_CLASS]]", page_status_vis)
        .replace("[[HEADER_EMBED_TARGET_VIS_CLASS]]", header_embed_target_vis)
        .replace("[[BODY_EMBED_TARGET_VIS_CLASS]]", body_embed_target_vis)
        .replace("[[FOOTER_EMBED_TARGET_VIS_CLASS]]", footer_embed_target_vis)
        .replace("[[FOOTER_ALIGN_CLASS]]", footer_align_class)
        .replace("[[FOOTER_EMBED_MODE_CLASS]]", "footer-with-embed" if footer_embed_active else "")
        .replace("[[CELL_ALIGN_CLASS]]", cell_align_class)
        .replace("[[BAR_FIXED_W]]", str(bar_fixed_w))
        .replace("[[TABLE_MAX_H]]", str(table_max_h))
        .replace("[[WIDGET_MAX_H]]", str(compute_preview_height(row_count)))
        .replace("[[FOOTER_LOGO_H]]", str(footer_logo_h))
        .replace("[[FOOTER_NOTES_VIS_CLASS]]", "" if (show_footer_notes and footer_notes_html) else "vi-hide")
        .replace("[[FOOTER_NOTES_HTML]]", footer_notes_html)
        .replace("[[FOOTER_SCALE_VIS_CLASS]]", "" if show_heat_scale else "vi-hide")
        .replace("[[FOOTER_SCALE_HTML]]", footer_scale_html)
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
        "title_style": st.session_state.get("bt_title_style", "Keep original"),
        "subtitle": st.session_state.get("bt_widget_subtitle", "Subheading"),
        "subtitle_style": st.session_state.get("bt_subtitle_style", "Keep original"),
        "striped": st.session_state.get("bt_striped_rows", True),
        "stripe_mode": st.session_state.get("bt_stripe_mode", "Odd"),
        "show_header": st.session_state.get("bt_show_header", True),
        "center_titles": st.session_state.get("bt_center_titles", False),
        "branded_title_color": st.session_state.get("bt_branded_title_color", True),
        "show_footer": st.session_state.get("bt_show_footer", True),
        "footer_logo_align": st.session_state.get("bt_footer_logo_align", "Center"),
        "footer_logo_h": st.session_state.get("bt_footer_logo_h", 36),
        "show_footer_notes": st.session_state.get("bt_show_footer_notes", False),
        "footer_notes": st.session_state.get("bt_footer_notes", ""),
        "show_heat_scale": st.session_state.get("bt_show_heat_scale", False),
        "cell_align": st.session_state.get("bt_cell_align", "Center"),
        "show_search": st.session_state.get("bt_show_search", True),
        "show_pager": st.session_state.get("bt_show_pager", True),
        "show_embed": st.session_state.get("bt_show_embed", True),
        "embed_position": st.session_state.get("bt_embed_position", "Body"),
        "show_page_numbers": st.session_state.get("bt_show_page_numbers", True),
        "bar_columns": st.session_state.get("bt_bar_columns", []),
        "bar_max_overrides": st.session_state.get("bt_bar_max_overrides", {}),
        "bar_fixed_w": st.session_state.get("bt_bar_fixed_w", 200),
        "heat_columns": st.session_state.get("bt_heat_columns", []),
        "heat_overrides": st.session_state.get("bt_heat_overrides", {}),
        "heat_strength": st.session_state.get("bt_heat_strength", 0.55),
        "heatmap_style": st.session_state.get("bt_heatmap_style", "Branded heatmap"),
        "header_style": st.session_state.get("bt_header_style", "Keep original"),
        "col_header_overrides": st.session_state.get("bt_col_header_overrides", {}) or {},
        "header_wrap_target": st.session_state.get("bt_header_wrap_target", "Off"),
        "header_wrap_words": st.session_state.get("bt_header_wrap_words", 2),
    }


def html_from_config(df: pd.DataFrame, cfg: dict, col_format_rules: dict | None = None) -> str:
    meta = get_brand_meta(cfg["brand"])
    return generate_table_html_from_df(
        df=df,
        title=cfg["title"],
        title_style=cfg.get("title_style", "Keep original"),
        subtitle=cfg["subtitle"],
        subtitle_style=cfg.get("subtitle_style", "Keep original"),
        brand_logo_url=meta["logo_url"],
        brand_logo_alt=meta["logo_alt"],
        brand_class=meta["brand_class"],
        striped=cfg["striped"],
        stripe_mode=cfg.get("stripe_mode", "Odd"),
        center_titles=cfg["center_titles"],
        branded_title_color=cfg["branded_title_color"],
        show_search=cfg["show_search"],
        show_pager=cfg["show_pager"],
        show_embed=cfg["show_embed"],
        embed_position=cfg.get("embed_position", "Body"),
        show_page_numbers=cfg["show_page_numbers"],
        show_header=cfg["show_header"],
        show_footer=cfg["show_footer"],
        footer_logo_align=cfg["footer_logo_align"],
        footer_logo_h=cfg.get("footer_logo_h", 36),
        show_footer_notes=cfg.get("show_footer_notes", False),
        footer_notes=cfg.get("footer_notes", ""),
        show_heat_scale=cfg.get("show_heat_scale", False),
        cell_align=cfg["cell_align"],
        bar_columns=cfg.get("bar_columns", []),
        bar_max_overrides=cfg.get("bar_max_overrides", {}),
        bar_fixed_w=cfg.get("bar_fixed_w", 200),
        heat_columns=cfg.get("heat_columns", []),
        heat_overrides=cfg.get("heat_overrides", {}),
        heat_strength=cfg.get("heat_strength", 0.55),
        heatmap_style=cfg.get("heatmap_style", "Branded heatmap"),
        header_style=cfg.get("header_style", "Keep original"),
        col_header_overrides=cfg.get("col_header_overrides", {}) or {},
        header_wrap_target=cfg.get("header_wrap_target", "Off"),
        header_wrap_words=cfg.get("header_wrap_words", 2),

        # ✅ LIVE-ONLY formatting rules
        col_format_rules=col_format_rules,
    )
    
def compute_pages_url(user: str, repo: str, filename: str) -> str:
    user = (user or "").strip()
    repo = (repo or "").strip()
    filename = (filename or "").lstrip("/").strip() or "branded_table.html"
    return f"https://{user}.github.io/{repo}/{filename}"
    
def build_publish_bundle(widget_file_name: str) -> dict:
    """
    Build the editable bundle that gets saved to GitHub (bundles/<file>.json).

    IMPORTANT:
    - If the user has clicked **Confirm & Save**, we prefer the CONFIRMED snapshot
      (bt_df_confirmed + bt_confirmed_cfg) so the bundle always matches the HTML
      that was actually published.
    - Otherwise we fall back to the current live draft state.
    """
    # Prefer CONFIRMED snapshot when available (keeps bundle aligned with published HTML)
    cfg = st.session_state.get("bt_confirmed_cfg")
    if not isinstance(cfg, dict) or not cfg:
        cfg = draft_config_from_state()

    # Live-only formatting rules are still saved so edits are retained when re-opening
    rules = st.session_state.get("bt_col_format_rules", {}) or {}

    # Prefer confirmed df (matches confirmed HTML); fallback to current upload
    df = st.session_state.get("bt_df_confirmed")
    if not isinstance(df, pd.DataFrame) or df.empty:
        df = st.session_state.get("bt_df_uploaded")

    if isinstance(df, pd.DataFrame) and not df.empty:
        csv_text = df.to_csv(index=False)
    else:
        csv_text = ""

    bundle = {
        "schema_version": 1,
        "widget_file_name": widget_file_name,

        # high-level metadata
        "brand": st.session_state.get("brand_table", ""),
        "created_by": (st.session_state.get("bt_created_by_user", "") or "").strip().lower(),
        "created_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),

        # naming + header text
        "table_name_words": st.session_state.get("bt_table_name_words", ""),
        "widget_title": st.session_state.get("bt_widget_title", ""),
        "widget_subtitle": st.session_state.get("bt_widget_subtitle", ""),

        # core state (everything needed to fully restore the editor)
        "config": cfg,
        "confirmed_total_height": int(st.session_state.get("bt_confirmed_total_height", 0) or 0),
        "col_format_rules": rules,
        "csv": csv_text,
        "hidden_cols": st.session_state.get("bt_hidden_cols", []) or [],

        # keep these for backward/forward compatibility (some older bundles used top-level keys)
        "bar_columns": st.session_state.get("bt_bar_columns", []) or [],
        "bar_max_overrides": st.session_state.get("bt_bar_max_overrides", {}) or {},
        "heat_columns": st.session_state.get("bt_heat_columns", []) or [],
        "heat_overrides": st.session_state.get("bt_heat_overrides", {}) or {},
    }
    return bundle

def load_bundle_into_editor(owner: str, repo: str, token: str, widget_file_name: str):
    bundle_path = f"bundles/{widget_file_name}.json"
    bundle = read_github_json(owner, repo, token, bundle_path, branch="main")

    if not isinstance(bundle, dict) or not bundle:
        st.error(f"Bundle not found at {bundle_path}. Cannot restore full table settings.")
        return

    st.session_state["bt_uploaded_name"] = f"bundle:{widget_file_name}"
    st.session_state["bt_editing_from_bundle"] = True
    st.session_state["bt_active_bundle_name"] = widget_file_name

    created_by = (bundle.get("created_by", "") or "").strip().lower()
    st.session_state["bt_created_by_user"] = created_by
    st.session_state["bt_user_select"] = created_by or "Select a user..."

    cfg = bundle.get("config") or {}

    # Clear editor keys to avoid stale mixes
    for k in [
        "bt_show_header","bt_widget_title","bt_widget_subtitle","bt_center_titles","bt_branded_title_color",
        "bt_show_footer","bt_footer_logo_align","bt_footer_logo_h","bt_show_footer_notes","bt_footer_notes","bt_show_heat_scale",
        "bt_striped_rows","bt_stripe_mode","bt_cell_align","bt_show_search","bt_show_pager","bt_show_embed","bt_show_page_numbers",
        "bt_bar_columns","bt_bar_max_overrides","bt_bar_fixed_w",
        "bt_heat_columns","bt_heat_overrides","bt_heat_strength","bt_heatmap_style","bt_header_style",
        "bt_header_wrap_target","bt_header_wrap_words","bt_col_format_rules","bt_hidden_cols"
    ]:
        st.session_state.pop(k, None)

    csv_text = (bundle.get("csv") or "")
    if csv_text.strip():
        df = pd.read_csv(io.StringIO(csv_text))
        st.session_state["bt_df_uploaded"] = df
        st.session_state["bt_df_source"] = df.copy(deep=True)
        st.session_state["bt_df_confirmed"] = df.copy(deep=True)

    st.session_state["bt_table_name_words"] = bundle.get("table_name_words", "")
    st.session_state["bt_confirmed_total_height"] = int(bundle.get("confirmed_total_height", 0) or 0)

    def _pick(*vals, default=None):
        for v in vals:
            if v is None:
                continue
            if isinstance(v, str):
                if v.strip() != "":
                    return v
            else:
                return v
        return default

    # Core config restore with safe defaults (supports legacy key variants)
    st.session_state["brand_table"]            = _pick(
        cfg.get("brand"), bundle.get("brand"), st.session_state.get("brand_table"), default="Action Network"
    )
    st.session_state["bt_widget_title"]        = _pick(
        cfg.get("title"), cfg.get("table_title"), bundle.get("widget_title"), bundle.get("table_title"), default="Table 1"
    )
    st.session_state["bt_title_style"]        = _pick(
        cfg.get("title_style"), cfg.get("table_title_style"), bundle.get("title_style"), default="Keep original"
    )
    st.session_state["bt_widget_subtitle"]     = _pick(
        cfg.get("subtitle"), cfg.get("table_subtitle"), bundle.get("widget_subtitle"), bundle.get("table_subtitle"), default="Subheading"
    )
    st.session_state["bt_subtitle_style"]     = _pick(
        cfg.get("subtitle_style"), cfg.get("table_subtitle_style"), bundle.get("subtitle_style"), default="Keep original"
    )

    st.session_state["bt_show_header"]         = cfg.get("show_header", True)
    st.session_state["bt_center_titles"]       = cfg.get("center_titles", False)
    st.session_state["bt_branded_title_color"] = cfg.get("branded_title_color", True)

    st.session_state["bt_show_footer"]         = cfg.get("show_footer", True)
    st.session_state["bt_footer_logo_align"]   = cfg.get("footer_logo_align", "Center")
    st.session_state["bt_footer_logo_h"]       = int(cfg.get("footer_logo_h", 36) or 36)
    st.session_state["bt_show_footer_notes"]   = cfg.get("show_footer_notes", False)
    st.session_state["bt_footer_notes"]        = cfg.get("footer_notes", "")
    st.session_state["bt_show_heat_scale"]     = cfg.get("show_heat_scale", False)

    st.session_state["bt_striped_rows"]        = cfg.get("striped", True)
    st.session_state["bt_stripe_mode"]         = cfg.get("stripe_mode", "Odd")
    st.session_state["bt_cell_align"]          = cfg.get("cell_align", "Center")
    st.session_state["bt_show_search"]         = cfg.get("show_search", True)
    st.session_state["bt_show_pager"]          = cfg.get("show_pager", True)
    st.session_state["bt_show_embed"]          = cfg.get("show_embed", True)
    st.session_state["bt_embed_position"]      = cfg.get("embed_position", "Body")
    st.session_state["bt_show_page_numbers"]   = cfg.get("show_page_numbers", True)

    st.session_state["bt_bar_columns"]         = cfg.get("bar_columns", bundle.get("bar_columns", [])) or []
    st.session_state["bt_bar_max_overrides"]   = cfg.get("bar_max_overrides", bundle.get("bar_max_overrides", {})) or {}
    st.session_state["bt_bar_fixed_w"]         = int(cfg.get("bar_fixed_w", 200) or 200)

    st.session_state["bt_heat_columns"]        = cfg.get("heat_columns", bundle.get("heat_columns", [])) or []
    st.session_state["bt_heat_overrides"]      = cfg.get("heat_overrides", bundle.get("heat_overrides", {})) or {}
    st.session_state["bt_heat_strength"]       = float(cfg.get("heat_strength", 0.55) or 0.55)
    st.session_state["bt_heatmap_style"]       = cfg.get("heatmap_style", "Branded heatmap")
    st.session_state["bt_header_style"]        = cfg.get("header_style", "Keep original")
    st.session_state["bt_header_wrap_target"]  = cfg.get("header_wrap_target", "Off")
    st.session_state["bt_header_wrap_words"]   = int(cfg.get("header_wrap_words", 2) or 2)

    st.session_state["bt_col_format_rules"]    = bundle.get("col_format_rules", {}) or {}
    st.session_state["bt_hidden_cols"]         = bundle.get("hidden_cols", []) or []

    # enforce mutual exclusivity
    if st.session_state["bt_show_footer_notes"]:
        st.session_state["bt_show_heat_scale"] = False
        if st.session_state["bt_footer_logo_align"] == "Center":
            st.session_state["bt_footer_logo_align"] = "Right"
    if st.session_state["bt_show_heat_scale"]:
        st.session_state["bt_show_footer_notes"] = False

    st.session_state["bt_editor_version"] = int(st.session_state.get("bt_editor_version", 0)) + 1
    st.session_state["bt_embed_tabs_visible"] = True
    st.session_state["bt_publish_in_progress"] = False
    st.session_state["bt_live_confirmed"] = True
    st.session_state["bt_confirm_flash"] = True
    st.rerun()

def is_page_live_with_hash(url: str, expected_hash: str) -> bool:
    try:
        r = http_session().get(url, timeout=5)
        if r.status_code != 200:
            return False
        return f"BT_PUBLISH_HASH:{expected_hash}" in r.text
    except Exception:
        return False

def build_iframe_snippet(url: str, height: int = 800, brand: str = "") -> str:
    url = (url or "").strip()
    if not url:
        return ""

    h = int(height) if height else 800
    brand_clean = (brand or "").strip().lower()

    # ✅ Canada Sports Betting → FULL width (no max-width wrapper)
    if brand_clean == "canada sports betting":
        return f"""<!-- ✅ Canada Sports Betting (FULL width, matches article text width) -->
<div style="width: 100%; margin: 0; padding: 0;">
  <iframe
    src="{html_mod.escape(url, quote=True)}"
    width="100%"
    height="{h}"
    style="border:0; border-radius:0; overflow:hidden; display:block;"
    loading="lazy"
    referrerpolicy="no-referrer-when-downgrade"
    allow="clipboard-write"
    sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-popups-to-escape-sandbox"
  ></iframe>
</div>"""

    # ✅ Everyone else → aligned article-width (720px centered)
    return f"""<!-- ✅ Standard embed (aligned to article text width) -->
<div style="max-width: 720px; margin: 0 auto; padding: 0 16px;">
  <iframe
    src="{html_mod.escape(url, quote=True)}"
    width="100%"
    height="{h}"
    style="border: 0; border-radius: 0; overflow: hidden; display: block;"
    loading="lazy"
    referrerpolicy="no-referrer-when-downgrade"
    allow="clipboard-write"
    sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-popups-to-escape-sandbox"
  ></iframe>
</div>"""



def read_github_text(owner: str, repo: str, token: str, path: str, branch: str = "main") -> str:
    """Read a text file from GitHub. Returns empty string if missing."""
    api_base = "https://api.github.com"
    headers = github_headers(token)
    path = (path or "").lstrip("/").strip()
    if not path:
        return ""

    url = f"{api_base}/repos/{owner}/{repo}/contents/{path}"
    r = http_session().get(url, headers=headers, params={"ref": branch}, timeout=20)

    if r.status_code == 404:
        return ""
    if r.status_code != 200:
        raise RuntimeError(f"Error reading text file: {r.status_code} {r.text}")

    data = r.json() or {}
    content_b64 = data.get("content", "")
    if not content_b64:
        return ""

    return base64.b64decode(content_b64).decode("utf-8", errors="ignore")


def build_published_iframe_snippet(
    owner: str,
    repo: str,
    token: str,
    widget_file_name: str,
    pages_url: str,
    brand: str = "",
    fallback_height: int = 800,
    bundle_path: str = "",
) -> str:
    """Rebuild iframe code for a published page from persisted metadata/bundle.

    This deliberately regenerates the snippet from canonical published metadata so the
    preview modal does not depend on transient session state.
    """
    widget_file_name = (widget_file_name or "").strip()
    pages_url = (pages_url or "").strip()
    if not pages_url and owner and repo and widget_file_name:
        pages_url = compute_pages_url(owner, repo, widget_file_name)
    if not pages_url:
        return ""

    resolved_brand = (brand or "").strip()
    try:
        resolved_height = int(fallback_height or 800)
    except Exception:
        resolved_height = 800

    candidate_bundle_paths = []
    bundle_path = (bundle_path or "").strip()
    if bundle_path:
        candidate_bundle_paths.append(bundle_path)
    if widget_file_name:
        candidate_bundle_paths.append(f"bundles/{widget_file_name}.json")
        base_name = re.sub(r"\.html?$", "", widget_file_name, flags=re.IGNORECASE)
        if base_name and base_name != widget_file_name:
            candidate_bundle_paths.append(f"bundles/{base_name}.json")

    seen = set()
    candidate_bundle_paths = [p for p in candidate_bundle_paths if p and not (p in seen or seen.add(p))]

    bundle = {}
    for candidate in candidate_bundle_paths:
        try:
            bundle = read_github_json(owner, repo, token, candidate, branch="main")
        except Exception:
            bundle = {}
        if isinstance(bundle, dict) and bundle:
            break

    if isinstance(bundle, dict) and bundle:
        try:
            resolved_height = int(bundle.get("confirmed_total_height", 0) or resolved_height)
        except Exception:
            resolved_height = max(320, resolved_height)
        cfg = bundle.get("config") or {}
        if not resolved_brand:
            resolved_brand = str(bundle.get("brand", "") or cfg.get("brand", "") or "").strip()

        if not int(bundle.get("confirmed_total_height", 0) or 0):
            csv_text = bundle.get("csv") or ""
            if csv_text:
                try:
                    bundle_df = pd.read_csv(io.StringIO(csv_text))
                except Exception:
                    bundle_df = None
                if isinstance(bundle_df, pd.DataFrame) and not bundle_df.empty:
                    hidden_cols = bundle.get("hidden_cols", []) or []
                    if hidden_cols:
                        bundle_df = bundle_df.drop(columns=hidden_cols, errors="ignore")
                    resolved_height = int(compute_preview_height(len(bundle_df.index), cfg=cfg, df=bundle_df))

    resolved_height = max(320, int(resolved_height or 800))
    return build_iframe_snippet(pages_url, height=resolved_height, brand=resolved_brand)

def wait_until_pages_live(url: str, timeout_sec: int = 60, interval_sec: float = 2.0) -> bool:
    """
    Returns True when the URL stops returning 404 and returns 200.
    """
    if not url:
        return False

    end_time = time.time() + timeout_sec
    while time.time() < end_time:
        try:
            r = http_session().get(url, timeout=10, headers={"Cache-Control": "no-cache"})
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
        "bt_gh_user",
        "bt_gh_repo",
        "bt_html_stale",
        "bt_confirm_flash",
        "bt_widget_exists_locked",
        "bt_widget_name_locked_value",
        "bt_df_uploaded",
        "bt_df_confirmed",
        "bt_df_source",              # ✅ NEW
        "bt_allow_swap",
        "bt_bar_columns",
        "bt_bar_max_overrides",
        "bt_bar_fixed_w",
        "bt_embed_started",
        "bt_embed_show_html",
        "bt_table_name_input",
        "bt_hidden_cols",            # ✅ NEW
        "bt_hidden_cols_draft",      # ✅ NEW
        "bt_enable_body_editor",     # ✅ NEW
        "bt_df_editor",              # ✅ NEW
        "bt_body_apply_flash",       # ✅ NEW
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
    st.session_state.setdefault("bt_confirmed_total_height", 0)
    st.session_state.setdefault("bt_preview_total_height", 0)
    st.session_state.setdefault("bt_last_published_repo", "")
    st.session_state.setdefault("bt_last_published_file", "")
    st.session_state.setdefault("bt_header_style", "Keep original")
    st.session_state.setdefault("bt_col_header_overrides", {})
    st.session_state.setdefault("bt_header_wrap_target", "Off")
    st.session_state.setdefault("bt_header_wrap_words", 2)
    st.session_state.setdefault("bt_embed_generated", False)  # show HTML/IFrame only after publish click
    st.session_state.setdefault("bt_embed_stale", False)      # becomes True after Confirm & Save post-publish
    st.session_state.setdefault("bt_published_hash", "")      # hash of last published HTML/config
    st.session_state.setdefault("bt_publish_in_progress", False)
    st.session_state.setdefault("bt_publish_started_at", None)
    st.session_state.setdefault("bt_expected_live_hash", "")
    st.session_state.setdefault("bt_live_confirmed", False)

    iframe_val = (st.session_state.get("bt_iframe_code") or "").strip()
    if iframe_val and ("data:text/html" in iframe_val or "about:srcdoc" in iframe_val):
        st.session_state["bt_iframe_code"] = ""

    st.session_state.setdefault("bt_footer_logo_align", "Center")
    st.session_state.setdefault("bt_footer_logo_h", 36)

    st.session_state.setdefault("bt_show_footer_notes", False)
    st.session_state.setdefault("bt_footer_notes", "")
    st.session_state.setdefault("bt_show_heat_scale", False)
    st.session_state.setdefault("bt_heat_scale_label_mode", "Low/High")
    st.session_state.setdefault("bt_gh_user", "Select a user...")
    st.session_state.setdefault("bt_widget_file_name", "table.html")

    st.session_state.setdefault("bt_confirm_flash", False)
    st.session_state.setdefault("bt_html_stale", False)

    st.session_state.setdefault("bt_widget_exists_locked", False)
    st.session_state.setdefault("bt_widget_name_locked_value", "")

    st.session_state.setdefault("bt_show_embed", True)
    st.session_state.setdefault("bt_embed_position", "Body")
    st.session_state.setdefault("bt_allow_swap", False)

    st.session_state.setdefault("bt_bar_columns", [])
    st.session_state.setdefault("bt_bar_max_overrides", {})
    st.session_state.setdefault("bt_bar_fixed_w", 200)

    # ✅ NEW: heatmap columns
    st.session_state.setdefault("bt_heat_columns", [])
    st.session_state.setdefault("bt_heat_overrides", {})   # { "Col": {"min": 0, "max": 100} }
    st.session_state.setdefault("bt_heat_strength", 0.55)  # 0.10–0.85 typical
    st.session_state.setdefault("bt_heatmap_style", "Branded heatmap")

    # ✅ NEW: body editing + hidden columns
    st.session_state.setdefault("bt_hidden_cols", [])
    st.session_state.setdefault("bt_hidden_cols_draft", [])
    st.session_state.setdefault("bt_enable_body_editor", False)
    st.session_state.setdefault("bt_body_apply_flash", False)
    st.session_state.setdefault("bt_editor_version", 0)


# =========================================================
# Header draft persistence across view switches
# (prevents title/subtitle resetting when navigating to Embed Script)
# =========================================================
def _cache_header_draft():
    st.session_state.setdefault("bt_header_cache", {})
    cache = st.session_state["bt_header_cache"]
    for k in [
        "bt_show_header",
        "bt_widget_title",
        "bt_title_style",
        "bt_widget_subtitle",
        "bt_subtitle_style",
        "bt_center_titles",
        "bt_branded_title_color",
    ]:
        if k in st.session_state:
            cache[k] = st.session_state.get(k)


def restore_draft_state_from_confirmed():
    """Keep the *editor* (draft) UI state in sync with the last Confirm & Save.

    Streamlit reruns wipe widget values that aren't rendered on a given run.
    When the user switches to 'Get Embed Script' and back, some draft keys can
    silently fall back to defaults (e.g., show_embed=True, show_footer_notes=False),
    even though the user already confirmed different settings.

    Strategy:
      - Restore when a key is missing
      - OR when it looks like it snapped back to a known default and confirmed differs
      - OR when a value is empty AND confirmed isn't
    """
    cfg = st.session_state.get("bt_confirmed_cfg") or {}
    if not isinstance(cfg, dict) or not cfg:
        return

    # Only run "snapback to defaults" restoration when returning from Embed tab.
    current_view = st.session_state.get("bt_left_view", "Edit table contents")
    prev_view = st.session_state.get("__bt_prev_left_view")
    coming_back_from_embed = (current_view == "Edit table contents" and prev_view == "Get Embed Script")

    # Confirmed cfg keys -> session_state keys used by the editor/preview
    mapping = {
        "brand": "brand_table",
        "title": "bt_widget_title",
        "title_style": "bt_title_style",
        "subtitle": "bt_widget_subtitle",
        "subtitle_style": "bt_subtitle_style",
        "striped": "bt_striped_rows",
        "stripe_mode": "bt_stripe_mode",
        "show_header": "bt_show_header",
        "center_titles": "bt_center_titles",
        "branded_title_color": "bt_branded_title_color",

        "show_footer": "bt_show_footer",
        "footer_logo_align": "bt_footer_logo_align",
        "footer_logo_h": "bt_footer_logo_h",

        "show_footer_notes": "bt_show_footer_notes",
        "footer_notes": "bt_footer_notes",

        "show_heat_scale": "bt_show_heat_scale",
        "heat_scale_label_mode": "bt_heat_scale_label_mode",

        "cell_align": "bt_cell_align",
        "show_search": "bt_show_search",
        "show_pager": "bt_show_pager",
        "show_embed": "bt_show_embed",
        "embed_position": "bt_embed_position",
        "show_page_numbers": "bt_show_page_numbers",

        "bar_columns": "bt_bar_columns",
        "bar_max_overrides": "bt_bar_max_overrides",
        "bar_fixed_w": "bt_bar_fixed_w",

        "heat_columns": "bt_heat_columns",
        "heat_overrides": "bt_heat_overrides",
        "heat_strength": "bt_heat_strength",
        "heatmap_style": "bt_heatmap_style",

        "header_style": "bt_header_style",
        "col_header_overrides": "bt_col_header_overrides",
        "header_wrap_target": "bt_header_wrap_target",
        "header_wrap_words": "bt_header_wrap_words",
    }

    # Known defaults that commonly re-appear after reruns (these are the ones we
    # want to override back to confirmed if confirmed differs)
    known_defaults = {
        "bt_widget_title": "Table 1",
        "bt_title_style": "Keep original",
        "bt_widget_subtitle": "Subheading",
        "bt_subtitle_style": "Keep original",
        "bt_header_style": "Keep original",
        "bt_col_header_overrides": {},
        "bt_header_wrap_target": "Off",
        "bt_header_wrap_words": 2,
        "bt_show_footer_notes": False,
        "bt_footer_notes": "",
        "bt_show_embed": True,
        "bt_embed_position": "Body",
        # These are set in ensure_confirm_state_exists:
        "bt_footer_logo_align": "Center",
        "bt_footer_logo_h": 36,
        "bt_show_heat_scale": False,
        "bt_heat_scale_label_mode": "Low/High",
        "bt_bar_columns": [],
        "bt_bar_max_overrides": {},
        "bt_bar_fixed_w": 200,
        "bt_heat_columns": [],
        "bt_heat_overrides": {},
        "bt_heat_strength": 0.55,
        "bt_heatmap_style": "Branded heatmap",
    }

    def is_empty(v):
        return v is None or v == "" or v == [] or v == {}  # noqa: E711

    for cfg_key, ss_key in mapping.items():
        if cfg_key not in cfg:
            continue
        confirmed_val = cfg.get(cfg_key)

        # If draft key is missing, restore immediately
        if ss_key not in st.session_state:
            st.session_state[ss_key] = confirmed_val
            continue

        current_val = st.session_state.get(ss_key)

        # 1) If current is empty but confirmed isn't, restore.
        # NOTE: Title/subtitle are allowed to be intentionally blank.
        if ss_key not in ("bt_widget_title", "bt_widget_subtitle"):
            if is_empty(current_val) and not is_empty(confirmed_val):
                st.session_state[ss_key] = confirmed_val
                continue

        # 2) If current snapped back to a known default (typically after tab switch),
        # but confirmed differs, restore.
        if coming_back_from_embed and ss_key in known_defaults:
            d = known_defaults[ss_key]
            if current_val == d and confirmed_val != d:
                st.session_state[ss_key] = confirmed_val
                continue

        # 3) For booleans: if confirmed differs and current equals False/True due to reset,
        # restore ONLY when it matches known default (handled above). Otherwise leave it.

    # Track view so we can detect when the user returns from Embed tab.
    st.session_state["__bt_prev_left_view"] = current_view

    # Restore dataframe snapshot if draft df disappeared
    if "bt_df_uploaded" not in st.session_state or st.session_state.get("bt_df_uploaded") is None:
        if isinstance(st.session_state.get("bt_df_confirmed"), pd.DataFrame):
            st.session_state["bt_df_uploaded"] = st.session_state["bt_df_confirmed"].copy()

    # Hidden columns: keep draft + confirmed aligned (if present)
    if "bt_hidden_cols" not in st.session_state and isinstance(st.session_state.get("bt_hidden_cols_draft"), list):
        st.session_state["bt_hidden_cols"] = list(st.session_state.get("bt_hidden_cols_draft") or [])

def _restore_header_draft():
    cache = st.session_state.get("bt_header_cache") or {}
    if not cache:
        return
    # Restore if key is missing or has fallen back to defaults
    defaults = {"bt_widget_title": "Table 1", "bt_widget_subtitle": "Subheading"}
    for k, v in cache.items():
        if k not in st.session_state:
            st.session_state[k] = v
            continue
        cur = st.session_state.get(k)
        # Allow users to intentionally clear title/subtitle (blank is valid).
        # Only restore when Streamlit snaps back to the explicit default label.
        if k in defaults and (cur is None or str(cur).strip() == defaults[k]) and str(v).strip() not in ("", defaults[k]):
            st.session_state[k] = v


def sync_bar_override(col: str):
    """
    Immediately sync a single override input into bt_bar_max_overrides.
    This makes the preview reflect the override instantly (no Confirm needed).
    """
    st.session_state.setdefault("bt_bar_max_overrides", {})

    # value typed in text_input for this column
    v = (st.session_state.get(f"bt_bar_override_{col}", "") or "").strip()

    # Blank → remove override
    if v == "":
        st.session_state["bt_bar_max_overrides"].pop(col, None)
        return

    # Try converting to float
    try:
        st.session_state["bt_bar_max_overrides"][col] = float(v)
    except Exception:
        # Ignore invalid mid-typing states like "1." or "-"
        pass


def prune_bar_overrides():
    """
    Remove overrides for columns that are no longer selected as bar columns.
    Keeps bt_bar_max_overrides clean and prevents "ghost overrides".
    """
    st.session_state.setdefault("bt_bar_max_overrides", {})
    selected = set(st.session_state.get("bt_bar_columns", []) or [])

    st.session_state["bt_bar_max_overrides"] = {
        k: v for k, v in st.session_state["bt_bar_max_overrides"].items()
        if k in selected
    }

def do_confirm_snapshot():
    # ✅ Always snapshot what user currently has in live table
    st.session_state["bt_df_confirmed"] = st.session_state["bt_df_uploaded"].copy()

    cfg = draft_config_from_state()
    st.session_state["bt_confirmed_cfg"] = cfg
    st.session_state["bt_confirmed_hash"] = stable_config_hash(cfg)

    # ✅ Apply hidden columns to the confirmed snapshot
    hidden_cols = st.session_state.get("bt_hidden_cols", []) or []
    df_confirm_for_html = st.session_state["bt_df_confirmed"].copy()
    if hidden_cols:
        df_confirm_for_html = df_confirm_for_html.drop(columns=hidden_cols, errors="ignore")

    live_rules = st.session_state.get("bt_col_format_rules", {})
    html = html_from_config(
        df_confirm_for_html,
        st.session_state["bt_confirmed_cfg"],
        col_format_rules=live_rules,
    )

    confirmed_total_height = compute_preview_height(
        len(df_confirm_for_html.index) if isinstance(df_confirm_for_html, pd.DataFrame) else 0,
        cfg=st.session_state["bt_confirmed_cfg"],
        df=df_confirm_for_html,
    )
    st.session_state["bt_confirmed_total_height"] = int(confirmed_total_height)

    st.session_state["bt_html_code"] = html
    st.session_state["bt_html_generated"] = True
    st.session_state["bt_html_hash"] = st.session_state["bt_confirmed_hash"]
    st.session_state["bt_html_stale"] = False

    st.session_state["bt_confirm_flash"] = True
    # ✅ If user already generated embed scripts once, a new Confirm makes them out-of-date
    if st.session_state.get("bt_embed_generated", False):
        st.session_state["bt_embed_stale"] = True

def reset_table_edits():
    # ✅ Restore original upload (true undo)
    src = st.session_state.get("bt_df_source")
    if isinstance(src, pd.DataFrame) and not src.empty:
        st.session_state["bt_df_uploaded"] = src.copy(deep=True)

    # ✅ Clear hidden columns (both live + draft)
    st.session_state["bt_hidden_cols"] = []
    st.session_state["bt_hidden_cols_draft"] = []

    # ✅ Clear header overrides
    st.session_state["bt_col_header_overrides"] = {}
    st.session_state["bt_col_header_overrides_draft"] = {}
    st.session_state["bt_header_wrap_target"] = "Off"
    st.session_state["bt_header_wrap_words"] = 2

    # ✅ Force data_editor to reset by changing its key
    st.session_state["bt_editor_version"] = int(st.session_state.get("bt_editor_version", 0)) + 1

    st.session_state["bt_body_apply_flash"] = True
def on_footer_notes_toggle():
    # if notes turned ON, force heat scale OFF
    if st.session_state.get("bt_show_footer_notes", False):
        st.session_state["bt_show_heat_scale"] = False
        if st.session_state.get("bt_embed_position", "Body") == "Footer":
            st.session_state["bt_embed_position"] = "Body"

        # if logo was centered, push it right (since notes take room)
        if st.session_state.get("bt_footer_logo_align") == "Center":
            st.session_state["bt_footer_logo_align"] = "Right"


def on_heat_scale_toggle():
    # if heat scale turned ON, force notes OFF
    if st.session_state.get("bt_show_heat_scale", False):
        st.session_state["bt_show_footer_notes"] = False

def on_embed_position_change():
    if st.session_state.get("bt_embed_position", "Body") == "Footer":
        st.session_state["bt_show_footer_notes"] = False
        st.session_state["bt_footer_logo_align"] = "Left"

# =========================================================
# Streamlit App
# =========================================================
st.set_page_config(page_title="Branded Table Generator", layout="wide")
st.markdown(
    """
    <style>
      [data-testid="stHeaderAnchor"] { display:none !important; }
      a.header-anchor { display:none !important; }

      /* ✅ Freeze the left settings panel (like "frozen columns") */
      div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child{
        position: sticky;
        top: 72px;
        align-self: flex-start;
        height: calc(100vh - 92px);
        overflow: auto;
        padding-bottom: 8px;
      }
      div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){
        align-self: flex-start;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Branded Table Generator")

# ✅ Global active-users banner (shared across browsers)
# NOTE: This is shared state stored in GitHub (active_users.json).
# Browsers will see updates on refresh/rerun (optionally auto-refresh below).
ACTIVE_USERS_AUTO_REFRESH_SECONDS = int(get_secret("ACTIVE_USERS_AUTO_REFRESH_SECONDS", 0) or 0)
if ACTIVE_USERS_AUTO_REFRESH_SECONDS > 0:
    # Simple full-page refresh (works reliably on Streamlit Cloud)
    st.markdown(
        f"<meta http-equiv='refresh' content='{ACTIVE_USERS_AUTO_REFRESH_SECONDS}'>",
        unsafe_allow_html=True,
    )


def _get_user_passcodes() -> dict:
    """Return a mapping of {username_lower: six_digit_code}.

    Supports:
      - secrets.USER_PASSCODES as a TOML table (preferred)
      - PASSCODE_<USER> flat secrets keys (fallback)
    """
    out = {}
    # Preferred: [USER_PASSCODES] table
    try:
        table = st.secrets.get("USER_PASSCODES", {})
    except Exception:
        table = {}

    if isinstance(table, Mapping):
        for k, v in table.items():
            u = str(k or "").strip().lower()
            code = str(v or "").strip()
            if u and re.fullmatch(r"\d{6}", code or ""):
                out[u] = code

    # Fallback: PASSCODE_<USER> keys
    try:
        all_keys = list(getattr(st.secrets, "_secrets", {}).keys())  # works on some runtimes
    except Exception:
        all_keys = []

    # Also try a small known list if we can't enumerate
    candidates = set(all_keys)

    for key in candidates:
        if not isinstance(key, str):
            continue
        if not key.startswith("PASSCODE_"):
            continue
        u = key.replace("PASSCODE_", "", 1).strip().lower()
        try:
            code = str(st.secrets.get(key, "") or "").strip()
        except Exception:
            code = ""
        if u and re.fullmatch(r"\d{6}", code or ""):
            out.setdefault(u, code)

    return out


# =========================================================
# Main tabs
# =========================================================
st.session_state.setdefault("main_tab", "Create New Table")

_main_tab_current = st.session_state.get("main_tab", "Create New Table")
_main_tab_col1, _main_tab_col2 = st.columns(2, gap="small")

with _main_tab_col1:
    if st.button(
        "Create New\nTable",
        key="main_tab_btn_create",
        use_container_width=True,
        type="primary" if _main_tab_current == "Create New Table" else "secondary",
    ):
        st.session_state["main_tab"] = "Create New Table"
        st.rerun()

with _main_tab_col2:
    if st.button(
        "Published Tables",
        key="main_tab_btn_published",
        use_container_width=True,
        type="primary" if _main_tab_current == "Published Tables" else "secondary",
    ):
        st.session_state["main_tab"] = "Published Tables"
        st.rerun()

main_tab = st.session_state.get("main_tab", "Create New Table")


# Options shown in dropdown
_user_passcodes = _get_user_passcodes()
created_by_options = ["Select a user..."] + sorted(_user_passcodes.keys())

def _validate_passcode(user: str, entered: str) -> bool:
    user = (user or "").strip().lower()
    entered = (entered or "").strip()
    codes = _get_user_passcodes()
    expected = codes.get(user, "")
    if not expected:
        return False
    # constant-time compare
    return hmac.compare_digest(entered, expected)

st.session_state.setdefault("bt_user_select", "Select a user...")
st.session_state.setdefault("bt_logged_in_user", "")
st.session_state.setdefault("bt_is_logged_in", False)

# user dropdown (login target)
created_by_choice = st.selectbox(
    "Created by (tracking only)",
    options=created_by_options,
    key="bt_user_select",
)

selected_user = ""
if created_by_choice and created_by_choice != "Select a user...":
    selected_user = created_by_choice.strip().lower()

# If dropdown changed away from the logged-in user, log out (prevents accidental cross-user edits)
if st.session_state.get("bt_is_logged_in") and selected_user and selected_user != st.session_state.get("bt_logged_in_user", ""):
    st.session_state["bt_is_logged_in"] = False
    st.session_state["bt_logged_in_user"] = ""
    st.session_state.pop("bt_user_passcode", None)

# passcode input + login/logout
pass_disabled = (not selected_user)
st.text_input(
    "6-digit passcode",
    type="password",
    max_chars=6,
    key="bt_user_passcode",
    disabled=pass_disabled,
    help="Enter your 6-digit passcode to enable publishing/editing as this user.",
)

c_login, c_logout = st.columns(2, gap="small")

with c_login:
    login_clicked = st.button(
        "Log in",
        disabled=pass_disabled or not (st.session_state.get("bt_user_passcode") or "").strip(),
        type="primary",
        use_container_width=True,
        key="bt_login_btn",
    )

with c_logout:
    logout_clicked = st.button(
        "Log out",
        disabled=not st.session_state.get("bt_is_logged_in", False),
        use_container_width=True,
        key="bt_logout_btn",
    )

if logout_clicked:
    _u = (st.session_state.get("bt_logged_in_user") or "").strip().lower()
    if _u:
        remove_active_user(PUBLISH_OWNER, github_token(PUBLISH_OWNER), _u)
    st.session_state["bt_is_logged_in"] = False
    st.session_state["bt_logged_in_user"] = ""
    st.session_state.pop("bt_user_passcode", None)
    st.rerun()

if login_clicked:
    entered = (st.session_state.get("bt_user_passcode") or "").strip()
    if not re.fullmatch(r"\d{6}", entered):
        st.error("Passcode must be exactly **6 digits**.")
    elif not _validate_passcode(selected_user, entered):
        st.error("Wrong passcode.")
    else:
        st.session_state["bt_is_logged_in"] = True
        st.session_state["bt_logged_in_user"] = selected_user
        st.success(f"Logged in as **{selected_user}**.")
        write_active_users_state(PUBLISH_OWNER, github_token(PUBLISH_OWNER), selected_user, action="login")
        st.rerun()

if st.session_state.get("bt_is_logged_in", False):
    st.markdown(f"✅ **Logged in as:** `{st.session_state.get('bt_logged_in_user','')}`")
else:
    st.caption("Not logged in. You can browse published tables, but publishing/editing requires login.")


try:
    render_active_users_banner(PUBLISH_OWNER, github_token(PUBLISH_OWNER))
except Exception:
    pass

# 🔄 Heartbeat: keep the active-users list fresh while you're logged in
if st.session_state.get("bt_is_logged_in") and st.session_state.get("bt_logged_in_user"):
    import time as _time
    _now = _time.time()
    _last = float(st.session_state.get("bt_last_active_heartbeat", 0) or 0)
    if (_now - _last) >= ACTIVE_USER_HEARTBEAT_SECONDS:
        try:
            write_active_users_state(
                PUBLISH_OWNER,
                github_token(PUBLISH_OWNER),
                st.session_state.get("bt_logged_in_user"),
                action="heartbeat",
            )
        except Exception:
            pass
        st.session_state["bt_last_active_heartbeat"] = _now

# ✅ This is the ONLY identity used for tracking + permissions
st.session_state.setdefault("bt_created_by_user", "")
st.session_state["bt_created_by_user"] = st.session_state.get("bt_logged_in_user", "") if st.session_state.get("bt_is_logged_in", False) else ""

# =========================================================
# ✅ TAB 2: Published Tables  (ONLY THIS VIEW)
# =========================================================
if main_tab == "Published Tables":
    st.markdown("### Published Tables")
    st.caption("All published tables found in GitHub Pages across repos.")
    # ✅ Current user (from the global selector above)
    current_user = (st.session_state.get("bt_created_by_user", "") or "").strip().lower()

    # ✅ Ensure filter keys exist (prevents weird state issues)
    st.session_state.setdefault("pub_brand_filter", "All")
    st.session_state.setdefault("pub_people_filter", "All")
    st.session_state.setdefault("pub_month_filter", "All")
    st.session_state.setdefault("pub_last_preview_url", "")

    # ✅ Refresh button MUST live inside this tab
    refresh_clicked = st.button(
        "🔄 Refresh Published Tables",
        key="pub_refresh_btn",
        use_container_width=False,
    )

    publish_owner = (PUBLISH_OWNER or "").strip().lower()

    token_to_use = ""
    if GITHUB_PAT:
        token_to_use = GITHUB_PAT
    else:
        try:
            token_to_use = get_installation_token_for_user(publish_owner)
        except Exception:
            token_to_use = ""

    if not publish_owner or not token_to_use:
        st.warning("No publishing token found. Add GITHUB_PAT in secrets to view published tables.")
    else:
        # ✅ Only refetch when needed
        if refresh_clicked or "df_pub_cache" not in st.session_state or "Has CSV" not in st.session_state["df_pub_cache"].columns:
            if refresh_clicked:
                st.cache_data.clear()
            st.session_state["df_pub_cache"] = get_all_published_widgets(publish_owner, token_to_use)

        df_pub = st.session_state.get("df_pub_cache")

        if df_pub is None or df_pub.empty:
            st.info("No published tables found yet.")
        else:
            # ✅ Normalize datetime once
            df_pub = df_pub.copy()
            df_pub["Created DT"] = pd.to_datetime(df_pub.get("Created UTC", ""), errors="coerce", utc=True)
            
            # ✅ Build filter options from FULL dataset
            all_brands = sorted([b for b in df_pub["Brand"].dropna().unique() if str(b).strip()])
            all_people = sorted([p for p in df_pub["Created By"].dropna().unique() if str(p).strip()])
            
            # ✅ Month filter keys + friendly labels
            df_pub["MonthKey"] = df_pub["Created DT"].dt.strftime("%Y-%m")     # ex: 2026-01
            df_pub["MonthLabel"] = df_pub["Created DT"].dt.strftime("%b %Y")   # ex: Jan 2026
            
            # ✅ map MonthKey -> MonthLabel (so selectbox can display friendly label)
            month_label_map = (
                df_pub.dropna(subset=["MonthKey"])
                .drop_duplicates("MonthKey")
                .set_index("MonthKey")["MonthLabel"]
                .to_dict()
            )
            
            all_month_keys = sorted([m for m in month_label_map.keys() if str(m).strip()], reverse=True)
            
            st.markdown("### Filters")
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 0.55])
            
            with col1:
                brand_filter = st.selectbox(
                    "Filter by brand",
                    ["All"] + all_brands,
                    key="pub_brand_filter",
                )
            
            with col2:
                people_filter = st.selectbox(
                    "Filter by people",
                    ["All"] + all_people,
                    key="pub_people_filter",
                )
            
            with col3:
                month_filter = st.selectbox(
                    "Filter by month",
                    ["All"] + all_month_keys,    # ✅ store MonthKey in session_state
                    key="pub_month_filter",
                    format_func=lambda k: "All" if k == "All" else month_label_map.get(k, k),
                )
            
            def reset_pub_filters():
                st.session_state["pub_brand_filter"] = "All"
                st.session_state["pub_people_filter"] = "All"
                st.session_state["pub_month_filter"] = "All"
                st.session_state["pub_last_preview_url"] = ""
                st.rerun()  # <- strongly recommended so the rest of this run doesn't use stale local vars
        
            with col4:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                st.button(
                    "Reset Filters",
                    key="pub_reset_filters",
                    use_container_width=True,
                    on_click=reset_pub_filters,
                )
            # ✅ Always initialize so tab blocks never crash
            df_view = pd.DataFrame()

            # ✅ Apply filters
            df_view = df_pub.copy()
            
            if brand_filter != "All":
                df_view = df_view[df_view["Brand"] == brand_filter]
            
            if people_filter != "All":
                df_view = df_view[df_view["Created By"] == people_filter]
            
            if month_filter != "All":
                df_view = df_view[df_view["MonthKey"] == month_filter]
            
            # ✅ Optional: hide helper columns from display
            df_view = df_view.drop(columns=["Created DT", "MonthKey", "MonthLabel"], errors="ignore")     

            # ✅ If no matches
            if df_view.empty:
                st.warning("No results match your filters.")
            else:
                # ✅ Clean up any helper cols safely (no-ops if they don't exist)
                df_view = df_view.drop(columns=["Created DT", "Month", "MonthKey", "MonthLabel"], errors="ignore")
            
                # ✅ Reset index once so selection rows map correctly everywhere
                df_view = df_view.reset_index(drop=True)

    # =========================================================
    # ✅ PREVIEW + DELETE in TABS (side-by-side)
    # =========================================================
    st.markdown(
        """
        <style>
          /* Full-width tab row */
          div[data-baseweb="tab-list"] {
            width: 100% !important;
            display: flex !important;
            gap: 0 !important;
            background: #dff5ea !important;          /* pale green bar */
            border-radius: 0 !important;
            overflow: hidden !important;
            border: 1px solid rgba(0,0,0,0.08) !important;
          }
    
          /* Each tab is 50/50 */
          button[data-baseweb="tab"] {
            flex: 1 1 0 !important;
            justify-content: center !important;
            padding: 14px 12px !important;
            font-weight: 700 !important;
            border: none !important;
            margin: 0 !important;
            background: transparent !important;
          }
    
          /* ACTIVE tab */
          button[data-baseweb="tab"][aria-selected="true"] {
            background: #00c853 !important;          /* strong green */
            color: #ffffff !important;
          }
          button[data-baseweb="tab"][aria-selected="true"] * {
            color: #ffffff !important;
          }
    
          /* INACTIVE tab */
          button[data-baseweb="tab"][aria-selected="false"] {
            color: #0b1f16 !important;
          }
          button[data-baseweb="tab"][aria-selected="false"]:hover {
            background: rgba(0, 200, 83, 0.12) !important;
          }
    
          /* Remove Streamlit's default underline/highlight if present */
          div[data-baseweb="tab-highlight"] { display: none !important; }
        

/* Explicitly kill ghost / outline / transparent variants */
.vi-table-embed .vi-header-actions button[class*="ghost"],
.vi-table-embed .vi-header-actions .dw-btn[class*="ghost"],
.vi-table-embed .footer-embed-wrap button[class*="ghost"],
.vi-table-embed .footer-embed-wrap .dw-btn[class*="ghost"],
.vi-table-embed .vi-header-actions button[class*="outline"],
.vi-table-embed .vi-header-actions .dw-btn[class*="outline"],
.vi-table-embed .footer-embed-wrap button[class*="outline"],
.vi-table-embed .footer-embed-wrap .dw-btn[class*="outline"] {
  background: linear-gradient(180deg, var(--accent-start), var(--accent-mid)) !important;
  background-color: var(--accent-mid) !important;
  color: #ffffff !important;
  border: none !important;
  outline: none !important;
  box-shadow:none !important;
}

/* Hover / focus / active must also match body button */
.vi-table-embed button.dw-btn.dw-download:hover,
.vi-table-embed .dw-btn.dw-download:hover,
.vi-table-embed .dw-download:hover,
.vi-table-embed .vi-header-actions button:hover,
.vi-table-embed .vi-header-actions .dw-btn:hover,
.vi-table-embed .vi-header-actions .dw-download:hover,
.vi-table-embed .footer-embed-wrap button:hover,
.vi-table-embed .footer-embed-wrap .dw-btn:hover,
.vi-table-embed .footer-embed-wrap .dw-download:hover,
.vi-table-embed button.dw-btn.dw-download:focus,
.vi-table-embed .dw-btn.dw-download:focus,
.vi-table-embed .dw-download:focus,
.vi-table-embed .vi-header-actions button:focus,
.vi-table-embed .vi-header-actions .dw-btn:focus,
.vi-table-embed .vi-header-actions .dw-download:focus,
.vi-table-embed .footer-embed-wrap button:focus,
.vi-table-embed .footer-embed-wrap .dw-btn:focus,
.vi-table-embed .footer-embed-wrap .dw-download:focus,
.vi-table-embed button.dw-btn.dw-download:active,
.vi-table-embed .dw-btn.dw-download:active,
.vi-table-embed .dw-download:active,
.vi-table-embed .vi-header-actions button:active,
.vi-table-embed .vi-header-actions .dw-btn:active,
.vi-table-embed .vi-header-actions .dw-download:active,
.vi-table-embed .footer-embed-wrap button:active,
.vi-table-embed .footer-embed-wrap .dw-btn:active,
.vi-table-embed .footer-embed-wrap .dw-download:active {
  background: linear-gradient(180deg, var(--accent-mid), var(--accent-end)) !important;
  background-color: var(--accent-end) !important;
  color: #ffffff !important;
  border: none !important;
  outline: none !important;
  box-shadow:none !important;
  text-decoration: none !important;
}

/* Prevent parent wrappers from dimming or flattening these buttons */
.vi-table-embed .vi-header-actions,
.vi-table-embed .footer-embed-wrap {
  opacity: 1 !important;
}

.vi-table-embed .vi-header-actions *,
.vi-table-embed .footer-embed-wrap * {
  text-decoration: none !important;
}

</style>
        """,
        unsafe_allow_html=True,
    )
    # ✅ Fallback safeguard before tabs
    if "df_view" not in locals():
        df_view = st.session_state.get("df_pub_cache", pd.DataFrame())
        if not isinstance(df_view, pd.DataFrame):
            df_view = pd.DataFrame()
        
    tab_preview_tables, tab_delete_tables = st.tabs(
        ["Preview tables", "Delete tables (admin)"]
    )
    
    # -----------------------------
    # TAB: DELETE TABLES (ADMIN)
    # -----------------------------
    with tab_delete_tables:
        st.markdown("#### Delete tables (admin)")
    
        delete_cols = ["Brand", "Table Name", "Has CSV", "Pages URL", "Repo", "File", "Created By", "Created UTC"]
        df_delete = df_view.copy() if isinstance(df_view, pd.DataFrame) else pd.DataFrame()

        # Make sure all required columns exist (prevents KeyError)
        for c in delete_cols:
            if c not in df_delete.columns:
                df_delete[c] = ""
    
        df_delete = df_delete[delete_cols].reset_index(drop=True)
    
        # Add checkbox column (multi-select)
        df_delete.insert(0, "Delete?", False)
    
        edited = st.data_editor(
            df_delete,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Delete?": st.column_config.CheckboxColumn("Delete?", help="Tick rows you want to delete"),
                "Pages URL": st.column_config.TextColumn("Pages URL"),
            },
            disabled=[c for c in df_delete.columns if c != "Delete?"],
            key="pub_delete_editor",
        )
    
        to_delete = edited[edited["Delete?"] == True].copy()
        st.session_state["pub_to_delete"] = to_delete.to_dict("records")  # ✅ snapshot for dialog
        delete_disabled = to_delete.empty
    
        c1, c2 = st.columns([1, 1])
        with c1:
            st.caption(f"Selected: **{len(to_delete)}**")
    
        with c2:
            delete_clicked = st.button(
                "🗑️ Delete selected",
                disabled=delete_disabled,
                use_container_width=True,
                type="secondary",
                key="pub_delete_btn",
            )
    
        if delete_clicked:
            if not hasattr(st, "dialog"):
                st.error("Your Streamlit version doesn’t support dialogs. Update Streamlit or use an inline confirmation block.")
            else:
                @st.dialog("Confirm delete", width="large")
                def confirm_delete_dialog():
                    rows = st.session_state.get("pub_to_delete", []) or []
                    df_del = pd.DataFrame(rows)
    
                    st.warning("This will permanently delete the selected HTML + bundle files from GitHub.")
                    st.markdown("**You are deleting:**")
    
                    if df_del.empty:
                        st.info("No rows selected.")
                        return
    
                    st.dataframe(
                        df_del[["Brand", "Table Name", "Repo", "File", "Created By", "Created UTC"]],
                        use_container_width=True,
                        hide_index=True,
                    )
    
                    passkey = st.text_input("Enter admin passkey", type="password", key="pub_delete_passkey")
                    i_understand = st.checkbox("I understand this cannot be undone", key="pub_delete_ack")
    
                    do_it = st.button(
                        "✅ Confirm delete",
                        disabled=not (passkey and i_understand),
                        type="primary",
                        key="pub_confirm_delete_btn",
                    )
    
                    if do_it:
                        expected = str(st.secrets.get("ADMIN_DELETE_CODE", "") or "")
                        if not expected or not hmac.compare_digest(passkey, expected):
                            st.error("Wrong passkey.")
                            return
    
                        errors = []
                        for _, r in df_del.iterrows():
                            repo = (r.get("Repo") or "").strip()
                            file = (r.get("File") or "").strip()
    
                            if not repo or not file:
                                errors.append(f"Missing Repo/File for row: {r.get('Pages URL')}")
                                continue
    
                            try:
                                # delete main HTML
                                delete_github_file(publish_owner, repo, token_to_use, file, branch="main")
    
                                # delete bundle written as bundles/{widget_file_name}.json (widget_file_name already ends with .html)
                                bundle_path = f"bundles/{file}.json"
                                delete_github_file(publish_owner, repo, token_to_use, bundle_path, branch="main")
    
                                # remove from widget_registry.json (recommended)
                                remove_from_widget_registry(publish_owner, repo, token_to_use, file, branch="main")
    
                            except Exception as e:
                                errors.append(f"{repo}/{file}: {e}")
    
                        if errors:
                            st.error("Some deletes failed:")
                            st.write(errors)
                        else:
                            st.success("Deleted successfully.")
    
                        # Refresh list after deletes
                        try:
                            st.cache_data.clear()
                        except Exception:
                            pass
                        st.session_state.pop("df_pub_cache", None)
                        st.session_state.pop("pub_to_delete", None)
                        st.rerun()
    
                confirm_delete_dialog()
    
    # -----------------------------
    # TAB: PREVIEW TABLES
    # -----------------------------
    with tab_preview_tables:
        st.markdown("#### Click a row to preview")
    
        df_display = df_view.copy()
        if "Pages URL" in df_display.columns:
            df_display["Pages URL"] = df_display["Pages URL"].astype(str)
        else:
            df_display["Pages URL"] = ""
    
        preview_cols = ["Brand", "Table Name", "Has CSV", "Pages URL", "Created By", "Created UTC"]
        for c in preview_cols:
            if c not in df_display.columns:
                df_display[c] = ""
    
        event = st.dataframe(
            df_display[preview_cols],
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="pub_table_click_df",
            column_config={
                "Pages URL": st.column_config.TextColumn("Pages URL"),
            },
        )
    
        # ✅ Extract selected row → auto-preview popup
        selected_rows = []
        try:
            selected_rows = event.selection.rows or []
        except Exception:
            selected_rows = []
    
        if selected_rows:
            selected_idx = selected_rows[0]
            selected_url = (df_display.loc[selected_idx, "Pages URL"] or "").strip()
    
            # ✅ row comes from df_display to ensure index alignment
            row = df_display.loc[selected_idx]
    
            selected_repo = (row.get("Repo") or "").strip()
            selected_file = (row.get("File") or "").strip()
    
            row_created_by = (row.get("Created By") or "").strip().lower()
            current_user = (st.session_state.get("bt_created_by_user", "") or "").strip().lower()
    
            # ✅ must pick a user in Published tab for editing
            can_edit = bool(current_user) and ((not row_created_by) or (row_created_by == current_user))
    
            # ✅ If we're about to open the delete-confirm dialog, do NOT open the preview dialog too
            if st.session_state.get("pub_open_single_delete_dialog"):
                pass
            else:
                if selected_url:
                    # ✅ Prevent re-opening popup every rerun if same row clicked again
                    last = st.session_state.get("pub_last_preview_url", "")
                    if selected_url != last:
                        st.session_state["pub_last_preview_url"] = selected_url
            
                    # ✅ Popup modal preview (if supported)
                    if hasattr(st, "dialog"):
            
                        @st.dialog("Table Preview", width="large")
                        def preview_dialog(url):
                            st.markdown(f"**Previewing:** {url}")

                            notice_html = ""

                            html_editor_key = f"pub_html_editor_{selected_repo}_{selected_file}"
                            html_pending_key = f"{html_editor_key}__pending"
                            html_status_key = f"{html_editor_key}__status"

                            iframe_editor_key = f"pub_iframe_editor_{selected_repo}_{selected_file}"
                            iframe_pending_key = f"{iframe_editor_key}__pending"

                            if html_pending_key in st.session_state:
                                st.session_state[html_editor_key] = st.session_state.pop(html_pending_key)

                            if iframe_pending_key in st.session_state:
                                st.session_state[iframe_editor_key] = st.session_state.pop(iframe_pending_key)

                            selected_pages_url = (row.get("Pages URL", "") or url or "").strip()
                            selected_bundle_path = f"bundles/{selected_file}.json"

                            initial_html = ""
                            try:
                                initial_html = read_github_text(
                                    publish_owner,
                                    selected_repo,
                                    token_to_use,
                                    selected_file,
                                    branch="main",
                                )
                            except Exception as e:
                                st.warning(f"Could not load HTML from GitHub: {e}")

                            if html_editor_key not in st.session_state:
                                st.session_state[html_editor_key] = initial_html or ""

                            iframe_snippet = build_published_iframe_snippet(
                                owner=publish_owner,
                                repo=selected_repo,
                                token=token_to_use,
                                widget_file_name=selected_file,
                                pages_url=selected_pages_url,
                                brand=row.get("Brand", ""),
                                fallback_height=st.session_state.get("bt_iframe_height", 800),
                                bundle_path=selected_bundle_path,
                            )
                            if iframe_snippet and iframe_snippet != str(st.session_state.get(iframe_editor_key) or ""):
                                st.session_state[iframe_editor_key] = iframe_snippet
                            elif iframe_editor_key not in st.session_state:
                                st.session_state[iframe_editor_key] = iframe_snippet or ""

                            c1, c2, c3 = st.columns(3)

                            with c1:
                                st.link_button("🔗 Open live page", url, use_container_width=True)

                            with c2:
                                if not can_edit:
                                    owner_name = row_created_by or "someone else"
                                    st.button(f"✏️ Edit {owner_name}'s table", disabled=True, use_container_width=True)

                                    notice_html = f"""
                                    <div style="
                                      margin-top: 10px;
                                      padding: 10px 12px;
                                      border-radius: 10px;
                                      background: rgba(255, 193, 7, 0.16);
                                      border: 1px solid rgba(255, 193, 7, 0.45);
                                      color: #7a4b00;
                                      font-size: 13px;
                                      line-height: 1.25;
                                      text-align: left;
                                    ">
                                      <strong>Note:</strong> Only <strong>{owner_name}</strong> can edit this table.
                                    </div>
                                    """
                                else:
                                    has_csv = (row.get("Has CSV") == "✅")

                                    if not has_csv:
                                        st.button("✏️ Edit this table", disabled=True, use_container_width=True)
                                        notice_html = """<div style="margin-top:10px;padding:10px 12px;border-radius:10px;background:rgba(59,130,246,0.10);border:1px solid rgba(59,130,246,0.25);color:#1f3a8a;font-size:13px;line-height:1.25;text-align:left;"><strong>Note:</strong> Legacy table (no editable bundle). Re-publish once from <strong>Create New Table</strong> to enable full edit restore.</div>"""
                                    else:
                                        if st.button(
                                            "✏️ Edit this table",
                                            key=f"pub_edit_{selected_repo}_{selected_file}",
                                            use_container_width=True,
                                        ):
                                            st.session_state["main_tab"] = "Create New Table"
                                            st.session_state["pub_last_preview_url"] = ""
                                            st.session_state.pop("pub_table_click_df", None)

                                            bundle_path = f"bundles/{selected_file}.json"
                                            bundle_probe = read_github_json(publish_owner, selected_repo, token_to_use, bundle_path, branch="main")
                                            if not bundle_probe:
                                                st.error(f"Bundle not found at {bundle_path}. Cannot restore full table settings.")
                                                st.stop()
                                            load_bundle_into_editor(publish_owner, selected_repo, token_to_use, selected_file)

                            with c3:
                                if st.button(
                                    "🗑️ Delete this table",
                                    key=f"pub_delete_single_btn_{selected_repo}_{selected_file}",
                                    use_container_width=True,
                                    type="secondary",
                                ):
                                    st.session_state["pub_single_delete_target"] = {
                                        "Repo": selected_repo,
                                        "File": selected_file,
                                        "Brand": row.get("Brand", ""),
                                        "Table Name": row.get("Table Name", ""),
                                        "Pages URL": url,
                                        "Created By": row_created_by,
                                        "Created UTC": row.get("Created UTC", ""),
                                    }
                                    st.session_state["pub_open_single_delete_dialog"] = True
                                    st.session_state["pub_last_preview_url"] = ""
                                    st.session_state.pop("pub_table_click_df", None)
                                    st.rerun()

                            if notice_html:
                                st.markdown(notice_html, unsafe_allow_html=True)

                            left_col, right_col = st.columns([1.35, 1.0], gap="large")

                            with left_col:
                                components.iframe(selected_pages_url or url, height=650, scrolling=True)

                            with right_col:
                                mode_key = f"pub_preview_editor_mode_{selected_repo}_{selected_file}"
                                style_radio_as_big_tabs(mode_key, height_px=42, font_px=16, radius_px=999)
                                editor_mode = st.radio(
                                    "Published asset editor",
                                    ["HTML", "IFrame"],
                                    horizontal=True,
                                    label_visibility="collapsed",
                                    key=mode_key,
                                )

                                status_msg = (st.session_state.get(html_status_key) or "").strip()
                                if status_msg:
                                    st.info(status_msg)
                                    st.session_state[html_status_key] = ""

                                if editor_mode == "HTML":
                                    st.caption("Edit the published HTML below. Saving here updates the actual GitHub file. GitHub Pages may take a few minutes to reflect changes.")
                                    st.text_area(
                                        "Published HTML",
                                        key=html_editor_key,
                                        height=420,
                                        label_visibility="collapsed",
                                    )

                                    h1, h2 = st.columns(2)
                                    with h1:
                                        if st.button(
                                            "↻ Reload HTML",
                                            key=f"pub_reload_html_{selected_repo}_{selected_file}",
                                            use_container_width=True,
                                        ):
                                            try:
                                                fresh_html = read_github_text(
                                                    publish_owner,
                                                    selected_repo,
                                                    token_to_use,
                                                    selected_file,
                                                    branch="main",
                                                )
                                                st.session_state[html_pending_key] = fresh_html or ""
                                                st.session_state[html_status_key] = "Reloaded latest HTML from GitHub."
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Could not reload HTML: {e}")
                                    with h2:
                                        save_disabled = not can_edit
                                        if st.button(
                                            "💾 Save HTML to GitHub",
                                            key=f"pub_save_html_{selected_repo}_{selected_file}",
                                            use_container_width=True,
                                            disabled=save_disabled,
                                        ):
                                            try:
                                                updated_html = st.session_state.get(html_editor_key, "") or ""
                                                upload_file_to_github(
                                                    publish_owner,
                                                    selected_repo,
                                                    token_to_use,
                                                    selected_file,
                                                    updated_html,
                                                    message=f"Update {selected_file} via preview editor",
                                                    branch="main",
                                                )
                                                try:
                                                    trigger_pages_build(publish_owner, selected_repo, token_to_use)
                                                except Exception:
                                                    pass
                                                refreshed_iframe = build_published_iframe_snippet(
                                                    owner=publish_owner,
                                                    repo=selected_repo,
                                                    token=token_to_use,
                                                    widget_file_name=selected_file,
                                                    pages_url=selected_pages_url,
                                                    brand=row.get("Brand", ""),
                                                    fallback_height=st.session_state.get("bt_iframe_height", 800),
                                                    bundle_path=selected_bundle_path,
                                                )
                                                st.session_state[iframe_pending_key] = refreshed_iframe or ""
                                                st.session_state[html_status_key] = "Saved HTML to GitHub. GitHub Pages may take a few minutes to reflect changes."
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Could not save HTML: {e}")

                                    st.download_button(
                                        "Download HTML file",
                                        data=st.session_state.get(html_editor_key, "") or "",
                                        file_name=selected_file,
                                        mime="text/html",
                                        use_container_width=True,
                                        key=f"pub_dl_html_{selected_repo}_{selected_file}",
                                    )
                                else:
                                    refreshed_iframe = build_published_iframe_snippet(
                                        owner=publish_owner,
                                        repo=selected_repo,
                                        token=token_to_use,
                                        widget_file_name=selected_file,
                                        pages_url=selected_pages_url,
                                        brand=row.get("Brand", ""),
                                        fallback_height=st.session_state.get("bt_iframe_height", 800),
                                        bundle_path=selected_bundle_path,
                                    )
                                    if refreshed_iframe and refreshed_iframe != str(st.session_state.get(iframe_editor_key, "") or ""):
                                        st.session_state[iframe_pending_key] = refreshed_iframe
                                        st.rerun()

                                    st.caption("This iframe snippet is rebuilt automatically from the published metadata and bundle. Editing it here is for copy/use only and does not change the GitHub page.")
                                    st.text_area(
                                        "Published iframe snippet",
                                        key=iframe_editor_key,
                                        height=420,
                                        label_visibility="collapsed",
                                    )
                                    st.download_button(
                                        "Download iframe snippet",
                                        data=st.session_state.get(iframe_editor_key, "") or "",
                                        file_name="iframe-snippet.html",
                                        mime="text/html",
                                        use_container_width=True,
                                        key=f"pub_dl_iframe_{selected_repo}_{selected_file}",
                                    )

                        preview_dialog(selected_url)

                    else:
                        st.info("Popup preview not supported in this Streamlit version — showing inline preview below.")
                        components.iframe(selected_url, height=820, scrolling=True)
                            
    if hasattr(st, "dialog") and st.session_state.get("pub_open_single_delete_dialog"):
    
        @st.dialog("Confirm delete", width="large")
        def confirm_single_delete_dialog():
            target = st.session_state.get("pub_single_delete_target") or {}
            repo = (target.get("Repo") or "").strip()
            file = (target.get("File") or "").strip()
    
            st.warning("This will permanently delete the selected HTML + bundle files from GitHub.")
            st.markdown("**You are deleting:**")
            st.write(
                {
                    "Brand": target.get("Brand", ""),
                    "Table Name": target.get("Table Name", ""),
                    "Repo": repo,
                    "File": file,
                    "Pages URL": target.get("Pages URL", ""),
                    "Created By": target.get("Created By", ""),
                    "Created UTC": target.get("Created UTC", ""),
                }
            )
    
            passkey = st.text_input("Enter admin passkey", type="password", key="pub_single_delete_passkey")
            i_understand = st.checkbox("I understand this cannot be undone", key="pub_single_delete_ack")
    
            do_it = st.button("✅ Confirm delete", disabled=not (passkey and i_understand), type="primary")
    
            if do_it:
                expected = str(st.secrets.get("ADMIN_DELETE_CODE", "") or "")
                if not expected or not hmac.compare_digest(passkey, expected):
                    st.error("Wrong passkey.")
                    return
    
                try:
                    # delete main HTML
                    delete_github_file(publish_owner, repo, token_to_use, file, branch="main")
    
                    # delete bundle at bundles/{file}.json
                    bundle_path = f"bundles/{file}.json"
                    delete_github_file(publish_owner, repo, token_to_use, bundle_path, branch="main")
    
                    # remove from registry (recommended)
                    remove_from_widget_registry(publish_owner, repo, token_to_use, file, branch="main")
    
                    st.success("Deleted successfully.")
    
                except Exception as e:
                    st.error(f"Delete failed: {e}")
                    return
    
                # Clean up + refresh
                st.session_state["pub_open_single_delete_dialog"] = False
                st.session_state.pop("pub_single_delete_target", None)
    
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
    
                st.session_state.pop("df_pub_cache", None)
                st.rerun()
    
        # reset the flag immediately so it doesn't reopen repeatedly unless set again
        st.session_state["pub_open_single_delete_dialog"] = False
        confirm_single_delete_dialog()           
# =========================================================
# ✅ TAB 1: Create New Table  (ALL CREATE UI HERE)
# =========================================================
if main_tab == "Create New Table":

    # =========================================================
    # ✅ "Created by" comes from the global selector above
    # =========================================================
    created_by_user_global = (st.session_state.get("bt_created_by_user", "") or "").strip().lower()

    # =========================================================
    # ✅ Upload CSV (disabled until "Created by" selected)
    # =========================================================
    uploaded_file = st.file_uploader(
        "Upload Your CSV File",
        type=["csv"],
        disabled=(not bool(created_by_user_global) and not st.session_state.get("bt_editing_from_bundle", False)),
    )

    if (not created_by_user_global) and (not st.session_state.get("bt_editing_from_bundle", False)):
        st.info("Select **Created by** to enable CSV upload.")
    else:
        # =========================================================
        # ✅ Brand selector
        # =========================================================
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

        # ✅ Allow Create tab to work for BOTH:
        # 1) normal uploaded CSV
        # 2) bundle-loaded df in session_state (Edit flow)
        
        df_loaded = st.session_state.get("bt_df_uploaded")
        has_loaded_df = isinstance(df_loaded, pd.DataFrame) and not df_loaded.empty
        
        if uploaded_file is None and not has_loaded_df:
            st.info("Upload A CSV To Start.")
        elif brand_selected_global == "Choose a brand...":
            st.info("Choose a **Brand** to load the table preview.")
        else:
            # ✅ Source of data: upload wins, otherwise use loaded bundle df
            if uploaded_file is not None:
                # New upload takes precedence over edit-bundle mode
                st.session_state["bt_editing_from_bundle"] = False
                st.session_state.pop("bt_active_bundle_name", None)
                try:
                    df_uploaded_now = pd.read_csv(uploaded_file)
                except Exception as e:
                    st.error(f"Error Reading CSV: {e}")
                    df_uploaded_now = pd.DataFrame()
        
                uploaded_name = getattr(uploaded_file, "name", "uploaded.csv")
        
            else:
                # bundle-loaded case
                df_uploaded_now = df_loaded.copy()
                uploaded_name = st.session_state.get("bt_uploaded_name", "loaded_bundle.csv")
        
            if df_uploaded_now.empty:
                st.error("Uploaded CSV Has No Rows.")
            else:
                prev_name = st.session_state.get("bt_uploaded_name")
        
                # ✅ Only reset/init when the "source" changes
                if prev_name != uploaded_name:
                    reset_widget_state_for_new_upload()
                    st.session_state["bt_uploaded_name"] = uploaded_name
                    st.session_state["bt_df_source"] = df_uploaded_now.copy(deep=True)     # original backup
                    st.session_state["bt_df_uploaded"] = df_uploaded_now.copy(deep=True)   # live editable version
                    st.session_state["bt_df_confirmed"] = df_uploaded_now.copy(deep=True)  # confirmed snapshot seed
        
                ensure_confirm_state_exists()
                restore_draft_state_from_confirmed()


        
                _restore_header_draft()

                # =====================================================
                # Full-width control rows above the editor/preview area
                # =====================================================
                st.session_state.setdefault("bt_left_view", "Edit table contents")
                st.session_state.setdefault("bt_right_view", "Preview")

                _left_btn_col1, _left_btn_col2 = st.columns(2, gap="small")
                with _left_btn_col1:
                    if st.button(
                        "Edit table contents",
                        key="bt_left_edit_btn",
                        use_container_width=True,
                        type="primary" if st.session_state.get("bt_left_view") == "Edit table contents" else "secondary",
                    ):
                        _cache_header_draft()
                        st.session_state["bt_left_view"] = "Edit table contents"
                        st.rerun()
                with _left_btn_col2:
                    if st.button(
                        "Get Embed Script",
                        key="bt_left_embed_btn",
                        use_container_width=True,
                        type="primary" if st.session_state.get("bt_left_view") == "Get Embed Script" else "secondary",
                    ):
                        _cache_header_draft()
                        st.session_state["bt_left_view"] = "Get Embed Script"
                        st.rerun()

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

                _right_btn_col1, _right_btn_col2 = st.columns(2, gap="small")
                with _right_btn_col1:
                    if st.button(
                        "Preview",
                        key="bt_right_preview_btn",
                        use_container_width=True,
                        type="primary" if st.session_state.get("bt_right_view") == "Preview" else "secondary",
                    ):
                        st.session_state["bt_right_view"] = "Preview"
                        st.rerun()
                with _right_btn_col2:
                    if st.button(
                        "Edit table content (Optional)",
                        key="bt_right_body_btn",
                        use_container_width=True,
                        type="primary" if st.session_state.get("bt_right_view") == "Edit table content (Optional)" else "secondary",
                    ):
                        st.session_state["bt_right_view"] = "Edit table content (Optional)"
                        st.rerun()

                left_view = st.session_state.get("bt_left_view", "Edit table contents")
                right_view = st.session_state.get("bt_right_view", "Preview")

                left_col, right_col = st.columns([1, 3], gap="large")

                # ✅ Right side: Preview + Body Editor tabs
                with right_col:
                    # Always create this so the preview renderer at the bottom can use it
                    preview_slot = st.container()

                    if right_view == "Preview":
                        # (Intentionally blank) — remove the extra big "Preview" heading.
                        pass
                
                    else:
                        st.markdown("### Edit table content (Optional)")
                        st.caption("Edit cells + hide columns here. Click **Apply changes to preview** to update the preview.")

                        # Quick header preview (updates instantly as you type in the left panel)
                        _t = apply_text_case(st.session_state.get("bt_widget_title", "Table 1"), st.session_state.get("bt_title_style", "Keep original"))
                        _s = apply_text_case(st.session_state.get("bt_widget_subtitle", ""), st.session_state.get("bt_subtitle_style", "Keep original"))
                        st.markdown(f"**{_t}**")
                        if (_s or "").strip():
                            st.markdown(_s)

                
                        df_live = st.session_state.get("bt_df_uploaded")
                
                        if not isinstance(df_live, pd.DataFrame) or df_live.empty:
                            st.info("Upload a CSV to enable editing.")
                        else:
                            all_cols = list(df_live.columns)

                            st.session_state.setdefault(
                                "bt_hidden_cols_draft",
                                st.session_state.get("bt_hidden_cols", []) or []
                            )

                            editor_version = st.session_state.get("bt_editor_version", 0)
                            editor_key_df = f"bt_df_editor_{editor_version}"
                            editor_key_hdr = f"bt_header_editor_{editor_version}"

                            def _apply_table_edits_to_preview():
                                df_now = st.session_state.get("bt_df_uploaded")
                                if not isinstance(df_now, pd.DataFrame) or df_now.empty:
                                    return

                                all_cols_now = list(df_now.columns)

                                # ✅ Save hidden columns
                                hidden_draft_now = st.session_state.get("bt_hidden_cols_draft", []) or []
                                st.session_state["bt_hidden_cols"] = hidden_draft_now

                                visible_cols_now = [c for c in all_cols_now if c not in set(hidden_draft_now)]

                                # ✅ Apply header label overrides (display only)
                                try:
                                    base_overrides = dict(st.session_state.get("bt_col_header_overrides_draft", {}) or {})
                                except Exception:
                                    base_overrides = {}

                                edited_hdr_df_now = st.session_state.get("bt_hdr_editor_df")
                                if not isinstance(edited_hdr_df_now, pd.DataFrame):
                                    edited_hdr_df_now = st.session_state.get(editor_key_hdr)
                                if isinstance(edited_hdr_df_now, pd.DataFrame):
                                    try:
                                        for _, rr in edited_hdr_df_now.iterrows():
                                            orig = str(rr.get("Column", "") or "")
                                            lbl = str(rr.get("Header label (optional)", "") or "").strip()
                                            if not orig:
                                                continue
                                            if lbl == "" or lbl == orig:
                                                base_overrides.pop(orig, None)
                                            else:
                                                base_overrides[orig] = lbl
                                    except Exception:
                                        pass

                                st.session_state["bt_col_header_overrides"] = base_overrides
                                st.session_state["bt_col_header_overrides_draft"] = dict(base_overrides)

                                # ✅ Apply edited visible cells back into the full live df
                                edited_df_visible_now = st.session_state.get("bt_body_editor_df")
                                if not isinstance(edited_df_visible_now, pd.DataFrame):
                                    edited_df_visible_now = st.session_state.get(editor_key_df)
                                if not isinstance(edited_df_visible_now, pd.DataFrame):
                                    edited_df_visible_now = df_now[visible_cols_now].copy()

                                base = df_now.copy()
                                for col in visible_cols_now:
                                    if col in edited_df_visible_now.columns and col in base.columns:
                                        try:
                                            base[col] = edited_df_visible_now[col].values
                                        except Exception:
                                            pass

                                st.session_state["bt_df_uploaded"] = base
                                st.session_state["bt_body_apply_flash"] = True

                            # ✅ Put the buttons ABOVE the dropdown so users don't miss them
                            b1, b2 = st.columns([1, 1])
                            b1.button(
                                "✅ Apply changes to preview",
                                use_container_width=True,
                                on_click=_apply_table_edits_to_preview,
                            )
                            b2.button(
                                "↩ Reset table edits",
                                use_container_width=True,
                                on_click=reset_table_edits,
                            )

                            if st.session_state.get("bt_body_apply_flash", False):
                                st.success("Preview updated ✅")
                                st.session_state["bt_body_apply_flash"] = False

                            st.multiselect(
                                "Hide columns",
                                options=all_cols,
                                default=st.session_state.get("bt_hidden_cols_draft", []),
                                key="bt_hidden_cols_draft",
                                help="Hidden columns will be removed from preview + final output after Apply.",
                            )

                            hidden_cols_draft = st.session_state.get("bt_hidden_cols_draft", []) or []
                            visible_cols = [c for c in all_cols if c not in set(hidden_cols_draft)]
                            df_visible = df_live[visible_cols].copy()

                            # ✅ Header row editing (display labels)
                            st.session_state.setdefault(
                                "bt_col_header_overrides_draft",
                                st.session_state.get("bt_col_header_overrides", {}) or {}
                            )

                            with st.expander("Edit header row (display labels)", expanded=False):
                                draft_overrides = st.session_state.get("bt_col_header_overrides_draft", {}) or {}
                                hdr_df = pd.DataFrame({
                                    "Column": visible_cols,
                                    "Header label (optional)": [draft_overrides.get(c, "") for c in visible_cols],
                                })

                                edited_hdr_df = st.data_editor(


                                    hdr_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    num_rows="fixed",
                                    column_config={
                                        "Column": st.column_config.TextColumn("Column", disabled=True),
                                        "Header label (optional)": st.column_config.TextColumn(
                                            "Header label (optional)",
                                            help="Leave blank to use the original column name. This only changes how the header is displayed (does not rename data columns).",
                                        ),
                                    },


                                    key=editor_key_hdr,


                                )


                                # store the edited header-label dataframe explicitly (Streamlit widget state isn't always a DataFrame)


                                st.session_state["bt_hdr_editor_df"] = edited_hdr_df

                            # Show header labels in the grid using draft overrides (or the original column name)


                            draft_overrides_for_grid = st.session_state.get("bt_col_header_overrides_draft", {}) or {}


                            hdr_style_for_grid = st.session_state.get("bt_header_style", "Keep original")


                            grid_col_config = {}


                            for _c in df_visible.columns:


                                _base = (draft_overrides_for_grid.get(_c) or "").strip() or _c


                                _lbl = str(_base) if hdr_style_for_grid == "Keep original" else format_column_header(str(_base), hdr_style_for_grid)


                                # Use TextColumn for label only (data types remain unchanged)


                                grid_col_config[_c] = st.column_config.Column(label=_lbl)


                            


                            edited_body_df = st.data_editor(


                                df_visible,
                                use_container_width=True,
                                hide_index=True,
                                num_rows="fixed",


                                column_config=grid_col_config,


                                key=editor_key_df,


                            )


                            # store edited body dataframe explicitly


                            st.session_state["bt_body_editor_df"] = edited_body_df

                # ===================== Left: Tabs =====================
                with left_col:
                    # ---------- EDIT TAB ----------
                    if left_view == "Edit table contents":
                        st.markdown("#### Edit table contents")

                        # ✅ Confirm & Save at the top
                        st.button(
                            "Confirm & Save",
                            key="bt_confirm_btn",
                            use_container_width=True,
                            type="primary",
                            on_click=do_confirm_snapshot,
                        )

                        if st.session_state.get("bt_confirm_flash", False):
                            st.success("Saved. Confirmed snapshot updated and HTML regenerated.")
                            st.session_state["bt_confirm_flash"] = False

                        SETTINGS_PANEL_HEIGHT = 590  # px

                        sub_head, sub_footer, sub_body, sub_bars, sub_heat = st.tabs(["Header", "Footer", "Body", "Bars", "Heat"])

                        with sub_head:
                            with st.container(height=SETTINGS_PANEL_HEIGHT):
                                show_header = st.checkbox(
                                    "Show Header Box",
                                    value=st.session_state.get("bt_show_header", True),
                                    key="bt_show_header",
                                )

                                st.text_input(
                                    "Table Title",
                                    key="bt_widget_title",
                                    placeholder="Table 1",
                                    disabled=not show_header,
                                )
                                _case_opts = ["Keep original", "Sentence case", "Title case", "ALL CAPS"]
                                st.selectbox(
                                    "Title text case",
                                    options=_case_opts,
                                    index=_case_opts.index(st.session_state.get("bt_title_style", "Keep original")),
                                    key="bt_title_style",
                                    disabled=not show_header,
                                )

                                
                                sub_c1, sub_c2 = st.columns([0.86, 0.14])
                                with sub_c1:
                                    st.session_state.setdefault("bt_widget_subtitle_draft", st.session_state.get("bt_widget_subtitle", ""))
                                    st.text_input(
                                        "Table Subtitle",
                                        key="bt_widget_subtitle_draft",
                                        placeholder="Subheading",
                                        disabled=not show_header,
                                        on_change=_bt_commit_subtitle,
                                    )
                                with sub_c2:
                                    st.write("")  # align with input
                                    st.write("")
                                    st.button(
                                        "↺",
                                        key="bt_reset_subtitle_format",
                                        help="Clear formatting (Ctrl+\\)",
                                        disabled=not show_header,
                                        use_container_width=True,
                                        on_click=_bt_clear_formatting,
                                        args=("bt_widget_subtitle",),
                                    )


                                st.caption("Shortcuts: **Ctrl/⌘+B** bold • **Ctrl/⌘+I** italic")

                                components.html(
                                    """
                                    <script>
                                    (function(){
                                      const doc = window.parent && window.parent.document;
                                      if(!doc) return;

                                      function findInput(){
                                        return doc.querySelector('input[aria-label="Table Subtitle"]');
                                      }

                                      function dispatchStreamlitInput(el){
                                        el.dispatchEvent(new Event('input', { bubbles:true }));
                                      }

                                      function applyEdit(inp, start, end, replacement, selectMode){
                                        inp.focus();
                                        if (typeof inp.setRangeText === 'function'){
                                          inp.setRangeText(replacement, start, end, selectMode || 'preserve');
                                          dispatchStreamlitInput(inp);
                                          return;
                                        }
                                        const v = inp.value ?? '';
                                        inp.value = v.slice(0, start) + replacement + v.slice(end);
                                        dispatchStreamlitInput(inp);
                                      }

                                      function getValue(el){ return el?.value ?? ''; }

                                      function hasWrapper(text, left, right){
                                        return text.startsWith(left) && text.endsWith(right);
                                      }

                                      function toggleWrapSelection(inp, left, right){
                                        const start = inp.selectionStart ?? 0;
                                        const end = inp.selectionEnd ?? 0;
                                        const v = getValue(inp);

                                        if (start === end){
                                          applyEdit(inp, start, end, left + right, 'end');
                                          const pos = start + left.length;
                                          try{ inp.setSelectionRange(pos, pos); }catch(e){}
                                          return;
                                        }

                                        const sel = v.slice(start, end);

                                        if (hasWrapper(sel, left, right)){
                                          const unwrapped = sel.slice(left.length, sel.length - right.length);
                                          applyEdit(inp, start, end, unwrapped, 'select');
                                          return;
                                        }

                                        applyEdit(inp, start, end, left + sel + right, 'select');
                                      }

                                      function mount(inp){
                                        if(!inp || inp.dataset.btSubtitleMounted === '1') return;
                                        inp.dataset.btSubtitleMounted = '1';

                                        const isMac = navigator.platform.toUpperCase().includes('MAC');

                                        inp.addEventListener('keydown', (e)=>{
                                          const mod = isMac ? e.metaKey : e.ctrlKey;
                                          if(!mod) return;

                                          const k = (e.key || '').toLowerCase();

                                          if (k === 'b'){
                                            e.preventDefault();
                                            toggleWrapSelection(inp, '**', '**');
                                          }

                                          if (k === 'i'){
                                            e.preventDefault();
                                            toggleWrapSelection(inp, '*', '*');
                                          }
                                        }, true);
                                      }

                                      const obs = new MutationObserver(()=>{
                                        const inp = findInput();
                                        if(inp) mount(inp);
                                      });

                                      obs.observe(doc.body, { childList:true, subtree:true });

                                      const i0 = findInput();
                                      if(i0) mount(i0);
                                    })();
                                    </script>
                                    """,
                                    height=0,
                                )

                                st.selectbox(
                                    "Subtitle text case",
                                    options=_case_opts,
                                    index=_case_opts.index(st.session_state.get("bt_subtitle_style", "Keep original")),
                                    key="bt_subtitle_style",
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

                                _df_for_header_wrap = st.session_state.get("bt_df_uploaded")
                                _header_wrap_column_options = ["Off", "All columns"]
                                if isinstance(_df_for_header_wrap, pd.DataFrame) and not _df_for_header_wrap.empty:
                                    _header_wrap_column_options.extend([str(c) for c in _df_for_header_wrap.columns])

                                _header_wrap_target = st.session_state.get("bt_header_wrap_target", "Off")
                                if _header_wrap_target not in _header_wrap_column_options:
                                    _header_wrap_target = "Off"
                                    st.session_state["bt_header_wrap_target"] = "Off"

                                st.selectbox(
                                    "Header wrap text",
                                    options=_header_wrap_column_options,
                                    index=_header_wrap_column_options.index(_header_wrap_target),
                                    key="bt_header_wrap_target",
                                    disabled=not show_header,
                                    help="Choose Off, All columns, or a single column to wrap header text by words per line.",
                                )

                                st.number_input(
                                    "Words per line",
                                    min_value=1,
                                    max_value=10,
                                    value=int(st.session_state.get("bt_header_wrap_words", 2)),
                                    step=1,
                                    key="bt_header_wrap_words",
                                    disabled=(not show_header) or (st.session_state.get("bt_header_wrap_target", "Off") == "Off"),
                                    help="1 = one word per line, 2 = two words per line, and so on.",
                                )

                        with sub_footer:
                            with st.container(height=SETTINGS_PANEL_HEIGHT):
                                show_footer = st.checkbox(
                                    "Show Footer (Logo)",
                                    value=st.session_state.get("bt_show_footer", True),
                                    key="bt_show_footer",
                                )

                                _footer_embed_active = st.session_state.get("bt_show_embed", True) and st.session_state.get("bt_embed_position", "Body") == "Footer"
                                _footer_align_options = ["Left"] if _footer_embed_active else (["Right", "Left"] if st.session_state.get("bt_show_footer_notes", False) else ["Right", "Center", "Left"])
                                _footer_align_value = st.session_state.get("bt_footer_logo_align", "Center")
                                if _footer_embed_active:
                                    _footer_align_value = "Left"
                                    st.session_state["bt_footer_logo_align"] = "Left"
                                elif st.session_state.get("bt_show_footer_notes", False):
                                    _footer_align_value = _footer_align_value if _footer_align_value in ["Right", "Left"] else "Right"

                                st.selectbox(
                                    "Footer Logo Alignment",
                                    options=_footer_align_options,
                                    index=_footer_align_options.index(_footer_align_value if _footer_align_value in _footer_align_options else _footer_align_options[0]),
                                    key="bt_footer_logo_align",
                                    disabled=(not show_footer) or _footer_embed_active,
                                )

                                st.number_input(
                                    "Logo height (px)",
                                    min_value=16,
                                    max_value=90,
                                    value=int(st.session_state.get("bt_footer_logo_h", 36)),
                                    step=2,
                                    key="bt_footer_logo_h",
                                    disabled=not show_footer,
                                    help="Adjust the logo height. Footer height stays fixed.",
                                )

                                st.divider()

                                show_footer_notes = st.checkbox(
                                    "Show Footer Notes",
                                    value=st.session_state.get("bt_show_footer_notes", False),
                                    key="bt_show_footer_notes",
                                    disabled=(not show_footer) or _footer_embed_active,
                                    on_change=on_footer_notes_toggle,
                                    help="Adds a notes area in the footer. When enabled, heat scale turns OFF automatically. Disabled when the embed button is placed in the footer.",
                                )

                                st.caption("Shortcuts: **Ctrl/⌘+B** toggle bold • **Ctrl/⌘+I** toggle italic")

                                
                                fn_c1, fn_c2 = st.columns([0.86, 0.14])
                                with fn_c1:
                                    st.session_state.setdefault("bt_footer_notes_draft", st.session_state.get("bt_footer_notes", ""))
                                    st.text_area(
                                        "Footer notes",
                                        key="bt_footer_notes_draft",
                                        height=140,
                                        disabled=not (show_footer and show_footer_notes),
                                        help="Bold: **text**  •  Italic: *text*",
                                        on_change=_bt_commit_footer_notes,
                                    )
                                with fn_c2:
                                    st.write("")  # align with textarea
                                    st.write("")
                                    st.write("")
                                    st.button(
                                        "↺",
                                        key="bt_reset_footer_notes_format",
                                        help="Clear formatting (Ctrl+\\)",
                                        disabled=not (show_footer and show_footer_notes),
                                        use_container_width=True,
                                        on_click=_bt_clear_formatting,
                                        args=("bt_footer_notes",),
                                    )


                                components.html(
                                    """
                                    <script>
                                    (function(){
                                      const doc = window.parent && window.parent.document;
                                      if(!doc) return;

                                      function findTextarea(){
                                        return doc.querySelector('textarea[aria-label="Footer notes"]');
                                      }

                                      function dispatchStreamlitInput(el){
                                        el.dispatchEvent(new Event('input', { bubbles:true }));
                                      }

                                      function applyEdit(ta, start, end, replacement, selectMode){
                                        ta.focus();
                                        if (typeof ta.setRangeText === 'function'){
                                          ta.setRangeText(replacement, start, end, selectMode || 'preserve');
                                          dispatchStreamlitInput(ta);
                                          return;
                                        }
                                        const v = ta.value ?? '';
                                        ta.value = v.slice(0, start) + replacement + v.slice(end);
                                        dispatchStreamlitInput(ta);
                                      }

                                      function getValue(el){ return el?.value ?? ''; }

                                      function hasWrapper(text, left, right){
                                        return text.startsWith(left) && text.endsWith(right);
                                      }

                                      function toggleWrapSelection(ta, left, right){
                                        const start = ta.selectionStart ?? 0;
                                        const end = ta.selectionEnd ?? 0;
                                        const v = getValue(ta);

                                        if (start === end){
                                          applyEdit(ta, start, end, left + right, 'end');
                                          const pos = start + left.length;
                                          try{ ta.setSelectionRange(pos, pos); }catch(e){}
                                          return;
                                        }

                                        const sel = v.slice(start, end);

                                        if (hasWrapper(sel, left, right)){
                                          const unwrapped = sel.slice(left.length, sel.length - right.length);
                                          applyEdit(ta, start, end, unwrapped, 'select');
                                          return;
                                        }

                                        applyEdit(ta, start, end, left + sel + right, 'select');
                                      }

                                      function stripFormatting(text){
                                        let t = text ?? "";
                                        t = t.replace(/\\*\\*/g, "");
                                        t = t.replace(/\\*/g, "");
                                        return t;
                                      }

                                      function stripAllFormatting(ta){
                                        const v = getValue(ta);
                                        const cleaned = stripFormatting(v);
                                        if (cleaned !== v){
                                          applyEdit(ta, 0, v.length, cleaned, 'preserve');
                                        }
                                      }

                                      function mount(ta){
                                        if(!ta || ta.dataset.btMounted === '1') return;
                                        ta.dataset.btMounted = '1';

                                        const isMac = navigator.platform.toUpperCase().includes('MAC');

                                        ta.addEventListener('keydown', (e)=>{
                                          const mod = isMac ? e.metaKey : e.ctrlKey;
                                          if(!mod) return;

                                          const k = (e.key || '').toLowerCase();

                                          if (k === 'b'){
                                            e.preventDefault();
                                            toggleWrapSelection(ta, '**', '**');
                                          }

                                          if (k === 'i'){
                                            e.preventDefault();
                                            toggleWrapSelection(ta, '*', '*');
                                          }

                                          if (k === 'x' && e.shiftKey){
                                            e.preventDefault();
                                            stripAllFormatting(ta);
                                          }
                                        }, true);
                                      }

                                      const obs = new MutationObserver(()=>{
                                        const ta = findTextarea();
                                        if(ta) mount(ta);
                                      });

                                      obs.observe(doc.body, { childList:true, subtree:true });

                                      const ta0 = findTextarea();
                                      if(ta0) mount(ta0);

                                      setTimeout(()=>{ try{ obs.disconnect(); }catch(e){} }, 120000);
                                    })();
                                    </script>
                                    """,
                                    height=1,
                                )

                        with sub_body:
                            with st.container(height=SETTINGS_PANEL_HEIGHT):
                                st.checkbox(
                                    "Striped Rows",
                                    value=st.session_state.get("bt_striped_rows", True),
                                    key="bt_striped_rows",
                                )

                                st.selectbox(
                                    "Stripe rows",
                                    options=["Odd", "Even"],
                                    index=["Odd", "Even"].index(st.session_state.get("bt_stripe_mode", "Odd") if st.session_state.get("bt_stripe_mode", "Odd") in ["Odd", "Even"] else "Odd"),
                                    key="bt_stripe_mode",
                                    disabled=not st.session_state.get("bt_striped_rows", True),
                                    help="Choose whether the striped background applies to odd rows or even rows.",
                                )
                        
                                st.selectbox(
                                    "Table Content Alignment",
                                    options=["Center", "Left", "Right"],
                                    index=["Center", "Left", "Right"].index(st.session_state.get("bt_cell_align", "Center")),
                                    key="bt_cell_align",
                                )
                        
                                st.selectbox(
                                    "Column header style",
                                    options=["Keep original", "Sentence case", "Title Case", "ALL CAPS"],
                                    index=["Keep original", "Sentence case", "Title Case", "ALL CAPS"].index(st.session_state.get("bt_header_style", "Keep original")),
                                    key="bt_header_style",
                                    help="Controls how column headers are displayed. This does not change your CSV data.",
                                )
                        
                                st.divider()
                                st.markdown("#### Table Controls")

                                df_for_controls = st.session_state.get("bt_df_uploaded")
                                _row_count_for_controls = sync_table_control_defaults_for_row_count(df_for_controls)
                                _compact_controls_default = _row_count_for_controls <= 10 and _row_count_for_controls > 0

                                st.checkbox(
                                    "Show Search",
                                    value=st.session_state.get("bt_show_search", not _compact_controls_default),
                                    key="bt_show_search",
                                    help="Defaults to off when the table has 10 rows or fewer, but you can enable it anytime.",
                                )
                                st.checkbox(
                                    "Show Pager",
                                    value=st.session_state.get("bt_show_pager", not _compact_controls_default),
                                    key="bt_show_pager",
                                    help="Defaults to off when the table has 10 rows or fewer, but you can enable it anytime.",
                                )

                                st.checkbox(
                                    "Show Page Numbers",
                                    value=st.session_state.get("bt_show_page_numbers", not _compact_controls_default),
                                    key="bt_show_page_numbers",
                                    disabled=not st.session_state.get("bt_show_pager", True),
                                    help="Only works when Pager is enabled.",
                                )
                        
                                st.checkbox(
                                    "Show Embed / Download Button",
                                    key="bt_show_embed",
                                )

                                st.selectbox(
                                    "Embed button position",
                                    options=["Body", "Header", "Footer"],
                                    index=["Body", "Header", "Footer"].index(st.session_state.get("bt_embed_position", "Body") if st.session_state.get("bt_embed_position", "Body") in ["Body", "Header", "Footer"] else "Body"),
                                    key="bt_embed_position",
                                    disabled=not st.session_state.get("bt_show_embed", True),
                                    on_change=on_embed_position_change,
                                    help="Choose where the Embed / Download button appears in the widget.",
                                )
                        
                                st.divider()
                                st.markdown("#### Column Formatting (Live Preview Only)")

                                st.session_state.setdefault("bt_col_format_rules", {})

                                df_for_cols = st.session_state.get("bt_df_uploaded")
                                all_cols = list(df_for_cols.columns) if isinstance(df_for_cols, pd.DataFrame) and not df_for_cols.empty else []

                                if not all_cols:
                                    st.info("Upload a CSV to enable column formatting.")
                                else:
                                    fmt_options = ["prefix", "suffix", "plus_if_positive", "plain_number"]

                                    def _normalize_fmt_rule_for_editor(rule: dict) -> tuple[list[str], str, str]:
                                        rule = rule or {}
                                        raw_modes = rule.get("modes", None)

                                        if isinstance(raw_modes, (list, tuple, set)):
                                            modes = [str(m).strip().lower() for m in raw_modes if str(m).strip()]
                                        else:
                                            legacy_mode = str(rule.get("mode", "")).strip().lower()
                                            modes = [legacy_mode] if legacy_mode else []

                                        modes = ["plus_if_positive" if m == "moneyline_plus" else m for m in modes]
                                        seen = set()
                                        modes = [m for m in modes if m in fmt_options and not (m in seen or seen.add(m))]

                                        prefix_value = str(rule.get("prefix_value", "") or "")
                                        suffix_value = str(rule.get("suffix_value", "") or "")

                                        legacy_value = str(rule.get("value", "") or "")
                                        if "prefix" in modes and not prefix_value:
                                            prefix_value = legacy_value
                                        if "suffix" in modes and not suffix_value:
                                            suffix_value = legacy_value

                                        return modes, prefix_value, suffix_value

                                    def sync_fmt_editor_from_selected_col():
                                        col = st.session_state.get("bt_fmt_selected_col")
                                        rule = st.session_state.get("bt_col_format_rules", {}).get(col, {}) or {}
                                        modes, prefix_value, suffix_value = _normalize_fmt_rule_for_editor(rule)
                                        st.session_state["bt_fmt_selected_modes"] = modes
                                        st.session_state["bt_fmt_prefix_value"] = prefix_value
                                        st.session_state["bt_fmt_suffix_value"] = suffix_value

                                    selected_col = st.session_state.get("bt_fmt_selected_col")
                                    if selected_col not in all_cols:
                                        st.session_state["bt_fmt_selected_col"] = all_cols[0]
                                        selected_col = all_cols[0]

                                    if "bt_fmt_editor_loaded_for_col" not in st.session_state:
                                        sync_fmt_editor_from_selected_col()
                                        st.session_state["bt_fmt_editor_loaded_for_col"] = selected_col
                                    elif st.session_state.get("bt_fmt_editor_loaded_for_col") != selected_col:
                                        sync_fmt_editor_from_selected_col()
                                        st.session_state["bt_fmt_editor_loaded_for_col"] = selected_col

                                    st.selectbox(
                                        "Column",
                                        options=all_cols,
                                        key="bt_fmt_selected_col",
                                        on_change=sync_fmt_editor_from_selected_col,
                                    )

                                    st.multiselect(
                                        "Format",
                                        options=fmt_options,
                                        key="bt_fmt_selected_modes",
                                        help="You can combine multiple formats on the same column.",
                                    )

                                    selected_modes = st.session_state.get("bt_fmt_selected_modes", []) or []

                                    if "prefix" in selected_modes:
                                        st.text_input("Prefix value", key="bt_fmt_prefix_value", placeholder="Enter a prefix")
                                    if "suffix" in selected_modes:
                                        st.text_input("Suffix value", key="bt_fmt_suffix_value", placeholder="Enter a suffix")
                                    if not {"prefix", "suffix"} & set(selected_modes):
                                        st.text_input("Value", value="(auto)", disabled=True, key="bt_fmt_value_disabled")

                                    def add_update_fmt():
                                        col = st.session_state.get("bt_fmt_selected_col")
                                        modes = st.session_state.get("bt_fmt_selected_modes", []) or []

                                        seen = set()
                                        modes = [str(m).strip().lower() for m in modes if str(m).strip()]
                                        modes = [m for m in modes if m in fmt_options and not (m in seen or seen.add(m))]

                                        if not modes:
                                            st.session_state["bt_col_format_rules"].pop(col, None)
                                            return

                                        rule = {"modes": modes}

                                        if "prefix" in modes:
                                            prefix_value = (st.session_state.get("bt_fmt_prefix_value", "") or "").strip()
                                            if not prefix_value:
                                                st.session_state["bt_col_format_rules"].pop(col, None)
                                                return
                                            rule["prefix_value"] = prefix_value

                                        if "suffix" in modes:
                                            suffix_value = (st.session_state.get("bt_fmt_suffix_value", "") or "").strip()
                                            if not suffix_value:
                                                st.session_state["bt_col_format_rules"].pop(col, None)
                                                return
                                            rule["suffix_value"] = suffix_value

                                        st.session_state["bt_col_format_rules"][col] = rule
                                        st.session_state["bt_fmt_editor_loaded_for_col"] = col

                                    st.button("✅ Add / Update", use_container_width=True, on_click=add_update_fmt)

                                    if st.session_state["bt_col_format_rules"]:
                                        st.caption("Current formatting rules:")
                                        st.json(st.session_state["bt_col_format_rules"])

                        with sub_bars:
                            with st.container(height=SETTINGS_PANEL_HEIGHT):
                                st.markdown("#### Bar Columns")

                                df_for_cols = st.session_state.get("bt_df_uploaded")
                                if not isinstance(df_for_cols, pd.DataFrame) or df_for_cols.empty:
                                    st.info("Upload a CSV to enable bars.")
                                else:
                                    numeric_cols = [c for c in df_for_cols.columns if guess_column_type(df_for_cols[c]) == "num"]

                                    if not numeric_cols:
                                        st.warning("No numeric columns found for bars.")
                                    else:
                                        # ✅ Prevent Streamlit crash if saved defaults include cols not in this CSV
                                        st.session_state["bt_bar_columns"] = [
                                            c for c in (st.session_state.get("bt_bar_columns") or [])
                                            if c in numeric_cols
                                        ]

                                        st.multiselect(
                                            "Choose columns to display as bars",
                                            options=numeric_cols,
                                            default=st.session_state.get("bt_bar_columns", []),
                                            key="bt_bar_columns",
                                            on_change=prune_bar_overrides,
                                            help="Only numeric columns can be converted into bar columns.",
                                        )

                                        st.number_input(
                                            "Bar width (px)",
                                            min_value=120,
                                            max_value=360,
                                            value=int(st.session_state.get("bt_bar_fixed_w", 200)),
                                            step=10,
                                            key="bt_bar_fixed_w",
                                            help="This controls the fixed bar track width for all bar columns.",
                                        )

                                        st.divider()
                                        st.markdown("#### Max Value Overrides (Optional)")

                                        st.session_state.setdefault("bt_bar_max_overrides", {})

                                        selected = st.session_state.get("bt_bar_columns", [])
                                        if not selected:
                                            st.caption("Select at least one bar column to set overrides.")
                                        else:
                                            for col in selected:
                                                current = st.session_state["bt_bar_max_overrides"].get(col, "")
                                                new_val = st.text_input(
                                                    f"Max override for: {col}",
                                                    value=str(current),
                                                    help="Leave blank to auto-scale based on max value in the column.",
                                                    key=f"bt_bar_override_{col}",
                                                ).strip()

                                                if new_val == "":
                                                    st.session_state["bt_bar_max_overrides"].pop(col, None)
                                                else:
                                                    try:
                                                        st.session_state["bt_bar_max_overrides"][col] = float(new_val)
                                                    except Exception:
                                                        st.warning(f"'{new_val}' is not a valid number for {col}.")
                        with sub_heat:
                            with st.container(height=SETTINGS_PANEL_HEIGHT):
                                st.markdown("#### Heatmap Columns")
    
                                df_for_cols = st.session_state.get("bt_df_uploaded")
                                if not isinstance(df_for_cols, pd.DataFrame) or df_for_cols.empty:
                                    st.info("Upload a CSV to enable heatmap.")
                                else:
                                    numeric_cols = [c for c in df_for_cols.columns if guess_column_type(df_for_cols[c]) == "num"]
    
                                    if not numeric_cols:
                                        st.warning("No numeric columns found for heatmap.")
                                    else:
                                        # ✅ Prevent Streamlit crash if saved defaults include cols not in this CSV
                                        st.session_state["bt_heat_columns"] = [
                                            c for c in (st.session_state.get("bt_heat_columns") or [])
                                            if c in numeric_cols
                                        ]

                                        st.multiselect(
                                            "Choose numeric columns to shade as a heatmap",
                                            options=numeric_cols,
                                            default=st.session_state.get("bt_heat_columns", []),
                                            key="bt_heat_columns",
                                            help="Applies background intensity based on value within each column.",
                                        )

                                        st.selectbox(
                                            "Heatmap style",
                                            options=["Branded heatmap", "Standard heatmap (5 colors)"],
                                            index=["Branded heatmap", "Standard heatmap (5 colors)"].index(
                                                st.session_state.get("bt_heatmap_style", "Branded heatmap")
                                            ),
                                            key="bt_heatmap_style",
                                            help="Branded = current brand color intensity. Standard = 5-color scale (Green → Blue → Yellow → Orange → Red).",
                                        )
    
                                        st.slider(
                                            "Heat strength",
                                            min_value=0.10,
                                            max_value=0.85,
                                            value=float(st.session_state.get("bt_heat_strength", 0.55)),
                                            step=0.05,
                                            key="bt_heat_strength",
                                            help="Controls max opacity of the heat shading.",
                                        )
                                        st.checkbox(
                                            "Show heatmap scale in footer",
                                            value=bool(st.session_state.get("bt_show_heat_scale", False)),
                                            key="bt_show_heat_scale",
                                            disabled=bool(st.session_state.get("bt_show_footer_notes", False)),
                                            on_change=on_heat_scale_toggle,   # ✅ ADD THIS
                                            help="Adds a compact legend bar in the footer. Cannot be used with Footer Notes.",
                                        )
    
                                        st.divider()
                                        st.markdown("#### Range Overrides (Optional)")
                                        st.session_state.setdefault("bt_heat_overrides", {})
    
                                        selected = st.session_state.get("bt_heat_columns", [])
                                        if not selected:
                                            st.caption("Select at least one heat column to set overrides.")
                                        else:
                                            for col in selected:
                                                cur = st.session_state["bt_heat_overrides"].get(col, {}) or {}
                                                c1, c2 = st.columns(2)
    
                                                vmin = c1.text_input(
                                                    f"Min override: {col}",
                                                    value="" if cur.get("min") is None else str(cur.get("min")),
                                                    key=f"bt_heat_min_{col}",
                                                    help="Leave blank to auto-use column min.",
                                                ).strip()
    
                                                vmax = c2.text_input(
                                                    f"Max override: {col}",
                                                    value="" if cur.get("max") is None else str(cur.get("max")),
                                                    key=f"bt_heat_max_{col}",
                                                    help="Leave blank to auto-use column max.",
                                                ).strip()
    
                                                st.session_state["bt_heat_overrides"].setdefault(col, {})
    
                                                if vmin == "":
                                                    st.session_state["bt_heat_overrides"][col].pop("min", None)
                                                else:
                                                    try:
                                                        st.session_state["bt_heat_overrides"][col]["min"] = float(vmin)
                                                    except Exception:
                                                        st.warning(f"'{vmin}' is not a valid min for {col}.")
    
                                                if vmax == "":
                                                    st.session_state["bt_heat_overrides"][col].pop("max", None)
                                                else:
                                                    try:
                                                        st.session_state["bt_heat_overrides"][col]["max"] = float(vmax)
                                                    except Exception:
                                                        st.warning(f"'{vmax}' is not a valid max for {col}.")                                   

                    # ---------- EMBED TAB ----------
                    else:
                        # Live publish status UI
                        if st.session_state.get("bt_publish_in_progress", False):
                            st.info("🚀 Publishing updates… This can take up to a minute.")
                        
                            pages_url = st.session_state.get("bt_last_published_url")
                            expected_hash = st.session_state.get("bt_expected_live_hash")
                        
                            if pages_url and expected_hash:
                                if st.button("Check if page is live"):
                                    if is_page_live_with_hash(pages_url, expected_hash):
                                        st.session_state["bt_publish_in_progress"] = False
                                        st.session_state["bt_live_confirmed"] = True
                                        st.success("✅ Page is live with the latest updates.")
                                    else:
                                        st.warning("⏳ Still updating. Please try again in a few seconds.")
                        st.markdown("#### Get Embed Script")

                        st.session_state.setdefault("bt_embed_started", False)
                        st.session_state.setdefault("bt_embed_show_html", False)
                        st.session_state.setdefault("bt_update_confirm_text", "")
                        st.session_state.setdefault("bt_existing_created_by", "")

                        html_generated = bool(st.session_state.get("bt_html_generated", False))
                        created_by_user = (st.session_state.get("bt_created_by_user", "") or "").strip().lower()

                        embed_done = bool((st.session_state.get("bt_last_published_url") or "").strip())

                        st.session_state["bt_embed_started"] = True
                        embed_generated = bool(st.session_state.get("bt_embed_generated", False))
                        embed_stale = bool(st.session_state.get("bt_embed_stale", False))
                    
                        if embed_generated and embed_stale:
                            st.warning("Your embed scripts are out of date. Click **Create embed script** to publish the latest confirmed version.")
                    
                        btn_label = "Create embed script"

                        if not html_generated:
                            st.warning("Click **Confirm & Save** first so the latest HTML is generated.")

                        st.caption("Give a table name in a few words (this creates your hosted page for the iframe).")
                        table_name_words = st.text_input(
                            "Give a table name in few words",
                            value=st.session_state.get("bt_table_name_words", ""),
                            key="bt_table_name_words",
                            placeholder="Example: Best Super Bowl Cities",
                        ).strip()

                        widget_file_name = ""
                        if table_name_words:
                            safe = re.sub(r"[^A-Za-z0-9\-\_\s]", "", table_name_words).strip()
                            safe = re.sub(r"\s+", "-", safe).strip("-")
                            safe = safe.lower() or "table"
                            widget_file_name = safe + ".html"

                        st.session_state["bt_widget_file_name"] = widget_file_name

                        publish_owner = (PUBLISH_OWNER or "").strip().lower()

                        token_to_use = ""
                        if GITHUB_PAT:
                            token_to_use = GITHUB_PAT
                        else:
                            try:
                                token_to_use = get_installation_token_for_user(publish_owner)
                            except Exception:
                                token_to_use = ""

                        installation_token = token_to_use
                        if not installation_token:
                            st.caption("❌ No publishing token found (PAT or GitHub App).")
                            if GITHUB_APP_SLUG:
                                st.caption(f"Install GitHub App: https://github.com/apps/{GITHUB_APP_SLUG}")

                        current_brand = st.session_state.get("brand_table", "")
                        repo_name = suggested_repo_name(current_brand)
                        st.session_state["bt_gh_repo"] = repo_name
                        
                        can_check = bool(publish_owner and installation_token and repo_name and widget_file_name)
                        
                        file_exists = False
                        existing_pages_url = ""
                        existing_meta = {}
                        can_overwrite_owner = False
                        existing_created_by = ""
                        
                        # Auto-check existence (no separate "Check name availability" button)
                        if can_check:
                            file_exists = github_file_exists_cached(
                                publish_owner,
                                repo_name,
                                installation_token,
                                widget_file_name,
                                branch="main",
                            )
                        
                            if file_exists:
                                existing_pages_url = compute_pages_url(publish_owner, repo_name, widget_file_name)
                                try:
                                    registry = read_github_json_cached(
                                        publish_owner,
                                        repo_name,
                                        installation_token,
                                        "widget_registry.json",
                                        branch="main",
                                    )
                                    existing_meta = registry.get(widget_file_name, {}) if isinstance(registry, dict) else {}
                                except Exception:
                                    existing_meta = {}
                        
                                existing_created_by = (existing_meta.get("created_by", "") or "").strip().lower()
                                can_overwrite_owner = (not existing_created_by) or (existing_created_by == created_by_user)
                        
                        # ✅ store results so the rest of the UI logic below can use them on reruns
                        st.session_state["bt_file_exists"] = file_exists
                        st.session_state["bt_existing_pages_url"] = existing_pages_url
                        st.session_state["bt_existing_meta"] = existing_meta
                        st.session_state["bt_can_overwrite_owner"] = can_overwrite_owner
                        st.session_state["bt_existing_created_by"] = existing_created_by
                        
                        file_exists = st.session_state.get("bt_file_exists", False)
                        existing_pages_url = st.session_state.get("bt_existing_pages_url", "")
                        existing_meta = st.session_state.get("bt_existing_meta", {})
                        can_overwrite_owner = st.session_state.get("bt_can_overwrite_owner", False)
                        existing_created_by = st.session_state.get("bt_existing_created_by", "")
                        embed_done = bool((st.session_state.get("bt_last_published_url") or "").strip())
                        
                        # ✅ If the user already published this exact repo+file in this session,
                        # allow updates WITHOUT needing the overwrite checkbox.
                        same_target_as_last_publish = bool(
                            st.session_state.get("bt_embed_generated", False)
                            and st.session_state.get("bt_last_published_file") == widget_file_name
                            and st.session_state.get("bt_last_published_repo") == repo_name
                        )
                        
                        if file_exists and not embed_done and not same_target_as_last_publish:
                            st.info("ℹ️ A page with this table name already exists.")
                            if existing_pages_url:
                                st.link_button("🔗 Open existing page", existing_pages_url, use_container_width=True)
                            if existing_meta:
                                st.caption(
                                    f"Existing info → Brand: {existing_meta.get('brand','?')} | "
                                    f"Created by: {existing_meta.get('created_by','?')} | "
                                    f"UTC: {existing_meta.get('created_at_utc','?')}"
                                )
                        
                            if can_overwrite_owner:
                                st.warning("This table already exists. To update it, type **UPDATE** below.")
                                st.text_input(
                                    "Type UPDATE to confirm overwrite",
                                    key="bt_update_confirm_text",
                                    placeholder="UPDATE",
                                )
                            else:
                                # non-owner can never overwrite
                                st.session_state["bt_update_confirm_text"] = ""
                                owner_label = f"{existing_created_by}'s" if existing_created_by else "another user's"
                                st.warning(f"⛔ This is **{owner_label} page**, so you can’t overwrite it.")
                        
                        # ✅ Read typed confirmation
                        update_text = (st.session_state.get("bt_update_confirm_text", "") or "").strip().upper()
                        update_confirmed = (update_text == "UPDATE")   
                        swap_confirmed = (not file_exists) or (update_confirmed and can_overwrite_owner) or same_target_as_last_publish
                        
                        can_publish = bool(
                            html_generated
                            and publish_owner
                            and repo_name
                            and widget_file_name
                            and installation_token
                            and created_by_user
                            and swap_confirmed
                        )
                        
                        publish_clicked = st.button(
                            btn_label,
                            use_container_width=True,
                            disabled=not can_publish,
                        )

                        if not can_publish:
                            missing = []
                            if not html_generated:
                                missing.append("Confirm & Save")
                            if not table_name_words:
                                missing.append("table name")
                            if publish_owner and not installation_token:
                                missing.append("publishing token")
                            if file_exists and not swap_confirmed:
                                if not can_overwrite_owner:
                                    missing.append("you can’t overwrite (different creator)")
                                else:
                                    missing.append("type UPDATE to confirm overwrite")
                            if missing:
                                st.caption("To enable publishing: " + ", ".join(missing) + ".")

                        if publish_clicked:
                            st.session_state["bt_embed_tabs_visible"] = True
                            # mark publish as in-progress
                            st.session_state["bt_publish_in_progress"] = True
                            st.session_state["bt_publish_started_at"] = time.time()
                            st.session_state["bt_expected_live_hash"] = st.session_state.get("bt_html_hash", "")
                            st.session_state["bt_live_confirmed"] = False
                        

                            try:
                                html_final = (
                                    f"<!-- BT_PUBLISH_HASH:{st.session_state.get('bt_html_hash','')} -->\n"
                                    + st.session_state.get("bt_html_code", "")
                                )
                                if not html_final:
                                    raise RuntimeError("No generated HTML found. Click Confirm & Save first.")

                                simulate_progress("Publishing to GitHub…", total_sleep=0.35)

                                ensure_repo_exists(publish_owner, repo_name, installation_token)

                                try:
                                    ensure_pages_enabled(publish_owner, repo_name, installation_token, branch="main")
                                except Exception:
                                    pass

                                upload_file_to_github(
                                    publish_owner,
                                    repo_name,
                                    installation_token,
                                    widget_file_name,
                                    html_final,
                                    f"Add/Update {widget_file_name} from Branded Table App",
                                    branch="main",
                                )
                                
                                # ✅ NEW: also publish the editable bundle (CSV + config + rules)
                                bundle = build_publish_bundle(widget_file_name)
                                bundle_path = f"bundles/{widget_file_name}.json"
                                
                                upload_file_to_github(
                                    publish_owner,
                                    repo_name,
                                    installation_token,
                                    bundle_path,
                                    json.dumps(bundle, indent=2),
                                    f"Add/Update bundle for {widget_file_name}",
                                    branch="main",
                                )
                                
                                pages_url = compute_pages_url(publish_owner, repo_name, widget_file_name)
                                
                                st.session_state["bt_last_published_url"] = pages_url
                                st.session_state["bt_published_hash"] = st.session_state.get("bt_html_hash", "")
                                st.session_state["bt_last_published_repo"] = repo_name
                                st.session_state["bt_last_published_file"] = widget_file_name        
                                created_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                                # ✅ mark embed scripts as generated + fresh
                                st.session_state["bt_embed_generated"] = True
                                st.session_state["bt_embed_stale"] = False

                                github_repo_url = f"https://github.com/{publish_owner}/{repo_name}"
                                table_title = st.session_state.get("bt_widget_title", "").strip() or table_name_words or widget_file_name

                                meta = {
                                    "brand": current_brand,
                                    "table_title": table_title,
                                    "file": widget_file_name,
                                    "pages_url": pages_url,
                                    "github_repo_url": github_repo_url,
                                    "created_by": created_by_user,
                                    "created_at_utc": created_utc,
                                    "bundle_path": f"bundles/{widget_file_name}.json",
                                    "has_bundle": True,
                                }

                                try:
                                    update_widget_registry(
                                        owner=publish_owner,
                                        repo=repo_name,
                                        token=installation_token,
                                        widget_file_name=widget_file_name,
                                        meta=meta,
                                        branch="main",
                                    )
                                except Exception:
                                    pass

                                with st.spinner("Waiting for GitHub Pages to go live (avoiding 404)…"):
                                    live = wait_until_pages_live(pages_url, timeout_sec=90, interval_sec=2)

                                if live:
                                    published_df = st.session_state.get("bt_df_confirmed")
                                    confirmed_cfg = st.session_state.get("bt_confirmed_cfg") or {}
                                    published_row_count = len(published_df.index) if isinstance(published_df, pd.DataFrame) else 0
                                    published_iframe_height = int(
                                        st.session_state.get("bt_confirmed_total_height", 0)
                                        or compute_preview_height(published_row_count, cfg=confirmed_cfg, df=published_df)
                                    )
                                    st.session_state["bt_iframe_height"] = published_iframe_height
                                    st.session_state["bt_iframe_code"] = build_iframe_snippet(
                                        pages_url,
                                        height=published_iframe_height,
                                        brand=current_brand,
                                    )
                                
                                    # ✅ IMPORTANT: mark the page live + stop "in progress" state
                                    st.session_state["bt_publish_in_progress"] = False
                                    st.session_state["bt_live_confirmed"] = True
                                
                                    st.success("✅ Page is live. IFrame is ready.")
                                else:
                                    st.session_state["bt_iframe_code"] = ""
                                
                                    # ✅ still deploying
                                    st.session_state["bt_live_confirmed"] = False
                                
                                    st.warning("⚠️ URL created but GitHub Pages is still deploying. Try again in ~30s.")

                            except Exception as e:
                                st.error(f"Publish / IFrame generation failed: {e}")

                        published_url_val = (st.session_state.get("bt_last_published_url") or "").strip()
                        show_tabs = bool(published_url_val and st.session_state.get("bt_live_confirmed", False))

                        if show_tabs:
                            published_url_val = (st.session_state.get("bt_last_published_url") or "").strip()
                            if published_url_val:
                                st.caption("Published Page")
                                st.link_button("🔗 Open published page", published_url_val, use_container_width=True)

                            # ✅ Faster than st.tabs(): only renders ONE view per rerun
                            style_radio_as_big_tabs("bt_embed_view", height_px=46, font_px=16, radius_px=12)
                            embed_view = st.radio(
                                "Embed view",
                                ["HTML Code", "IFrame"],
                                horizontal=True,
                                label_visibility="collapsed",
                                key="bt_embed_view",
                            )
                            
                            if embed_view == "HTML Code":
                                html_code_val = (st.session_state.get("bt_html_code") or "").strip()
                                if not html_code_val:
                                    st.info("Click **Confirm & Save** to generate HTML.")
                                else:
                                    st.caption("HTML Code")
                            
                                    # ✅ Rendering huge st.code blocks is slow — use text_area (faster) + optional code view
                                    st.text_area(
                                        "HTML Code",
                                        value=html_code_val,
                                        height=340,
                                        label_visibility="collapsed",
                                        key="bt_html_code_view",
                                    )
                            
                                    st.download_button(
                                        "Download HTML file",
                                        data=html_code_val,
                                        file_name="table.html",
                                        mime="text/html",
                                        use_container_width=True,
                                    )
                            
                            else:
                                iframe_val = (st.session_state.get("bt_iframe_code") or "").strip()
                                st.caption("IFrame Code")
                            
                                st.text_area(
                                    "IFrame Code",
                                    value=iframe_val or "",
                                    height=160,
                                    label_visibility="collapsed",
                                    key="bt_iframe_code_view",
                                )
                            
                                st.download_button(
                                    "Download iframe snippet",
                                    data=iframe_val or "",
                                    file_name="iframe-snippet.html",
                                    mime="text/html",
                                    use_container_width=True,
                                )

                # ✅ Render preview LAST (HARD-GATED: do NOT run on Get embed script)
                _left_view = st.session_state.get("bt_left_view", "Edit table contents")
                _right_view = st.session_state.get("bt_right_view", "Preview")
                
                # Only render preview when:
                # - Left view is "Edit table contents"
                # - Right view is "Preview"
                if _left_view == "Edit table contents" and _right_view == "Preview":
                    with preview_slot:
                        st.session_state.setdefault("bt_show_preview", False)

                        live_cfg = draft_config_from_state()
                        live_rules = st.session_state.get("bt_col_format_rules", {})

                        df_preview = st.session_state["bt_df_uploaded"].copy()
                        hidden_cols = st.session_state.get("bt_hidden_cols", []) or []
                        if hidden_cols:
                            df_preview = df_preview.drop(columns=hidden_cols, errors="ignore")

                        preview_rows = len(df_preview.index) if isinstance(df_preview, pd.DataFrame) else 0
                        preview_height = compute_preview_height(preview_rows, cfg=live_cfg, df=df_preview)
                        st.session_state["bt_preview_total_height"] = int(preview_height)

                        _preview_toggle_col, _preview_height_col = st.columns([1, 1])
                        with _preview_toggle_col:
                            st.checkbox("Show live preview", key="bt_show_preview")
                        with _preview_height_col:
                            st.caption(f"Estimated table height: **{int(preview_height)}px**")

                        if not st.session_state["bt_show_preview"]:
                            st.info("Preview hidden for performance.")
                        else:
                            cfg_hash = stable_config_hash(live_cfg)

                            try:
                                df_hash = int(pd.util.hash_pandas_object(df_preview, index=True).sum())
                            except Exception:
                                df_hash = hash((df_preview.shape, tuple(df_preview.columns)))

                            rules_hash = hash(json.dumps(live_rules, sort_keys=True, default=str))
                            preview_key = f"{cfg_hash}|{df_hash}|{rules_hash}"

                            if st.session_state.get("bt_preview_key") != preview_key:
                                st.session_state["bt_preview_key"] = preview_key
                                st.session_state["bt_preview_html"] = html_from_config(
                                    df_preview,
                                    live_cfg,
                                    col_format_rules=live_rules,
                                )

                            components.html(
                                st.session_state.get("bt_preview_html", ""),
                                height=preview_height,
                                scrolling=True,
                            )
                else:
                    # Clear any previously mounted preview so it does NOT persist visually
                    preview_slot.empty()

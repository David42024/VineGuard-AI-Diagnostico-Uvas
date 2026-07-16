"""Theme system for VineGuard AI - dark/light mode with agricultural palette."""

import streamlit as st


def get_css(dark_mode: bool) -> str:
    if dark_mode:
        return DARK_CSS
    return LIGHT_CSS


def render_theme():
    dark = st.session_state.get("dark_mode", False)
    st.markdown(get_css(dark), unsafe_allow_html=True)
    st.markdown(BASE_CSS, unsafe_allow_html=True)


LIGHT_CSS = """
<style>
:root {
    --bg-primary: #F8FAF9;
    --bg-secondary: #FFFFFF;
    --bg-card: #FFFFFF;
    --bg-surface: #F0F4F2;
    --bg-input: #FFFFFF;

    --border-color: #E2E8E4;
    --border-light: #E8EDEA;

    --text-primary: #17201B;
    --text-secondary: #647067;
    --text-muted: #94A39A;

    --green-primary: #166534;
    --green-secondary: #22C55E;
    --green-soft: #DCFCE7;
    --green-bg: #F0FDF4;

    --purple-primary: #7C3AED;
    --purple-soft: #F5F3FF;

    --amber: #F59E0B;
    --amber-soft: #FFFBEB;
    --red: #DC2626;
    --red-soft: #FEF2F2;
    --blue: #2563EB;
    --blue-soft: #EFF6FF;

    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.05);
    --shadow-lg: 0 8px 30px rgba(0,0,0,0.08);

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 18px;

    --sidebar-bg: #FFFFFF;
    --header-bg: #FFFFFF;
    --gradient-hero: linear-gradient(135deg, #166534 0%, #22C55E 100%);

    --chart-colors: #166534, #22C55E, #7C3AED, #F59E0B, #2563EB;
}
</style>
"""

DARK_CSS = """
<style>
:root {
    --bg-primary: #07120D;
    --bg-secondary: #0D1F16;
    --bg-card: #12291C;
    --bg-surface: #0F1F15;
    --bg-input: #1A3326;

    --border-color: #244331;
    --border-light: #1C3528;

    --text-primary: #F1F8F3;
    --text-secondary: #A8B9AE;
    --text-muted: #6B8273;

    --green-primary: #4ADE80;
    --green-secondary: #22C55E;
    --green-soft: #052E16;
    --green-bg: #0A3D20;

    --purple-primary: #A78BFA;
    --purple-soft: #1E1035;

    --amber: #FBBF24;
    --amber-soft: #2D2108;
    --red: #F87171;
    --red-soft: #2D0A0A;
    --blue: #60A5FA;
    --blue-soft: #0C1D35;

    --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
    --shadow-lg: 0 8px 30px rgba(0,0,0,0.4);

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 18px;

    --sidebar-bg: #0D1F16;
    --header-bg: #0D1F16;
    --gradient-hero: linear-gradient(135deg, #0A3D20 0%, #166534 100%);

    --chart-colors: #4ADE80, #22C55E, #A78BFA, #FBBF24, #60A5FA;
}
</style>
"""

BASE_CSS = """
<style>
/* ========== GLOBAL ========== */
html, body, .stApp {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.main .block-container {
    max-width: 1100px;
    padding: 1.5rem 1rem;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* Texto secundario sólo en contextos nativos de Streamlit, no en HTML personalizado */
.stMarkdown > div > p,
.stMarkdown > div > ul > li,
.stMarkdown > div > ol > li,
[data-testid="stSidebar"] label,
[data-testid="stForm"] label {
    color: var(--text-secondary) !important;
}

a { color: var(--green-primary) !important; }

/* ========== SIDEBAR ========== */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color) !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: var(--sidebar-bg) !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label {
    color: var(--text-secondary) !important;
}

[data-testid="stSidebar"] hr {
    border-color: var(--border-color) !important;
}

/* ========== HEADER ========== */
[data-testid="stHeader"] {
    background: var(--bg-secondary) !important;
}

[data-testid="stToolbar"] { background: transparent !important; }

/* ========== BUTTONS ========== */
.stButton > button {
    width: 100%;
    min-height: 44px;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    border: 1px solid transparent !important;
    transition: all 0.2s ease !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: var(--gradient-hero) !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    filter: brightness(1.08);
    box-shadow: 0 4px 14px rgba(22, 101, 52, 0.3);
    transform: translateY(-1px);
}

.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--green-primary) !important;
    border: 1px solid var(--green-primary) !important;
}

.stButton > button[kind="secondary"]:hover {
    background: var(--green-soft) !important;
}

/* ========== INPUTS ========== */
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: var(--green-primary) !important;
    box-shadow: 0 0 0 2px var(--green-soft) !important;
}

input, textarea, select {
    color: var(--text-primary) !important;
    caret-color: var(--green-primary) !important;
}

input::placeholder, textarea::placeholder {
    color: var(--text-muted) !important;
}

/* ========== METRICS ========== */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 1rem;
    box-shadow: var(--shadow-sm);
}

[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
    color: var(--green-primary) !important;
}

/* ========== EXPANDER ========== */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm);
}

[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ========== FILE UPLOADER ========== */
[data-testid="stFileUploaderDropzone"] {
    background: var(--bg-surface) !important;
    border: 2px dashed var(--border-color) !important;
    border-radius: var(--radius-md) !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--green-primary) !important;
}

[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    color: var(--text-secondary) !important;
}

/* ========== DATAFRAME ========== */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    overflow: hidden;
}

/* ========== TABS ========== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
}

.stTabs [aria-selected="true"] {
    color: var(--green-primary) !important;
    border-bottom: 2px solid var(--green-primary) !important;
}

/* ========== CHECKBOX / RADIO ========== */
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {
    color: var(--text-primary) !important;
}

[data-baseweb="checkbox"] > div,
[data-baseweb="radio"] > div {
    background: var(--bg-input) !important;
    border-color: var(--border-color) !important;
}

/* ========== PROGRESS ========== */
[data-testid="stProgress"] > div > div > div {
    background: var(--gradient-hero) !important;
}

/* ========== ALERTS ========== */
[data-testid="stAlert"] {
    border-radius: var(--radius-md);
    border: none !important;
}

.stAlert[data-baseweb="notification"] {
    border-radius: var(--radius-md);
}

/* ========== DIVIDER ========== */
hr {
    border: none !important;
    border-top: 1px solid var(--border-color) !important;
    margin: 1.5rem 0 !important;
}

/* ========== SIDEBAR COLLAPSE ========== */
[data-testid="collapsedControl"] {
    color: var(--green-primary) !important;
}

/* ========== RESPONSIVE ========== */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 0.75rem;
    }
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
"""


def toggle_theme():
    current = st.session_state.get("dark_mode", False)
    st.session_state.dark_mode = not current
    st.rerun()

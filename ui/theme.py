"""
ui/theme.py
ProQuant Apex Risk Terminal — Institutional Premium Theme v6.0
Ultra-professional glassmorphism design system with dynamic light/dark modes
"""
import streamlit as st
import os


def load_corporate_theme():
    """
    Kurumsal premium temayı yükler.
    Session state'deki 'theme' değerine göre aydınlık veya karanlık palet seçer.
    """
    current_theme = st.session_state.get("theme", "dark")

    if current_theme == "dark":
        t = {
            "bg":           "#060B18",
            "bg2":          "#0A1628",
            "sidebar_bg":   "#0D1F3C",
            "card_bg":      "rgba(13, 31, 60, 0.85)",
            "card_border":  "rgba(56, 189, 248, 0.15)",
            "primary":      "#38BDF8",
            "primary_rgb":  "56, 189, 248",
            "primary_hover":"#7DD3FC",
            "accent":       "#6366F1",
            "accent2":      "#8B5CF6",
            "text":         "#E2E8F0",
            "text_strong":  "#F8FAFC",
            "muted":        "#64748B",
            "muted2":       "#94A3B8",
            "border":       "rgba(51, 65, 85, 0.8)",
            "border2":      "rgba(56, 189, 248, 0.2)",
            "shadow":       "rgba(0, 0, 0, 0.5)",
            "shadow2":      "rgba(56, 189, 248, 0.1)",
            "success":      "#10B981",
            "danger":       "#F43F5E",
            "warning":      "#F59E0B",
            "nav_bg":       "rgba(6, 11, 24, 0.95)",
            "glass":        "rgba(13, 31, 60, 0.7)",
            "glass_border": "rgba(56, 189, 248, 0.12)",
            "gradient1":    "#38BDF8",
            "gradient2":    "#6366F1",
        }
    else:
        t = {
            "bg":           "#F0F4F8",
            "bg2":          "#E8EDF5",
            "sidebar_bg":   "#FFFFFF",
            "card_bg":      "rgba(255, 255, 255, 0.9)",
            "card_border":  "rgba(0, 76, 145, 0.12)",
            "primary":      "#004C91",
            "primary_rgb":  "0, 76, 145",
            "primary_hover":"#003366",
            "accent":       "#4F46E5",
            "accent2":      "#7C3AED",
            "text":         "#1E293B",
            "text_strong":  "#0F172A",
            "muted":        "#6B7280",
            "muted2":       "#9CA3AF",
            "border":       "rgba(229, 231, 235, 0.9)",
            "border2":      "rgba(0, 76, 145, 0.2)",
            "shadow":       "rgba(0, 0, 0, 0.08)",
            "shadow2":      "rgba(0, 76, 145, 0.08)",
            "success":      "#059669",
            "danger":       "#DC2626",
            "warning":      "#D97706",
            "nav_bg":       "rgba(255, 255, 255, 0.97)",
            "glass":        "rgba(255, 255, 255, 0.8)",
            "glass_border": "rgba(0, 76, 145, 0.1)",
            "gradient1":    "#004C91",
            "gradient2":    "#4F46E5",
        }

    st.session_state["theme_palette"] = t
    st.session_state["theme"] = current_theme

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* ─── RESET & BASE ─────────────────────────────────────────── */
    *, *::before, *::after {{
        box-sizing: border-box;
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: {t['bg']} !important;
        color: {t['text']} !important;
    }}

    /* Animated mesh background */
    .stApp {{
        background:
            radial-gradient(ellipse at 0% 0%, rgba({t['primary_rgb']}, 0.08) 0px, transparent 60%),
            radial-gradient(ellipse at 100% 0%, rgba(99, 102, 241, 0.06) 0px, transparent 60%),
            radial-gradient(ellipse at 50% 100%, rgba({t['primary_rgb']}, 0.04) 0px, transparent 60%),
            {t['bg']} !important;
        animation: appFadeIn 0.6s ease-out !important;
    }}

    @keyframes appFadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}

    /* ─── HIDE STREAMLIT CHROME ─────────────────────────────────── */
    header[data-testid="stHeader"]  {{ display: none !important; }}
    #MainMenu {{ visibility: hidden !important; }}
    footer    {{ visibility: hidden !important; }}
    .stDeployButton {{ display: none !important; }}

    /* ─── LAYOUT ────────────────────────────────────────────────── */
    .main .block-container {{
        padding: 5.5rem 2.5rem 3rem 2.5rem !important;
        max-width: 1440px !important;
    }}

    /* ─── CUSTOM SCROLLBAR ──────────────────────────────────────── */
    ::-webkit-scrollbar       {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {t['bg']}; }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, {t['gradient1']}, {t['gradient2']});
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ opacity: 0.8; }}

    /* ─── SIDEBAR ────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {{
        background: {t['sidebar_bg']} !important;
        border-right: 1px solid {t['border']} !important;
        width: 300px !important;
        box-shadow: 4px 0 24px {t['shadow']} !important;
        backdrop-filter: blur(20px) !important;
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 1rem !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: {t['text']} !important;
        font-size: 0.875rem !important;
    }}

    /* Sidebar logo area */
    .sidebar-brand {{
        background: linear-gradient(135deg, {t['gradient1']}22, {t['gradient2']}11);
        border-bottom: 1px solid {t['border']};
        padding: 1.25rem 1rem;
        margin-bottom: 0.5rem;
    }}
    .sidebar-brand-title {{
        font-size: 1.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, {t['gradient1']}, {t['gradient2']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }}
    .sidebar-brand-sub {{
        font-size: 0.7rem;
        color: {t['muted']};
        font-weight: 500;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-top: 2px;
    }}

    /* ─── TYPOGRAPHY ─────────────────────────────────────────────── */
    h1 {{
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        color: {t['text_strong']} !important;
        letter-spacing: -0.5px !important;
        line-height: 1.2 !important;
    }}
    h2 {{
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: {t['text_strong']} !important;
        letter-spacing: -0.3px !important;
    }}
    h3, h4, h5, h6 {{
        color: {t['text']} !important;
        font-weight: 600 !important;
    }}
    p, span, div, label {{
        color: {t['text']} !important;
    }}

    /* ─── METRIC CARDS ───────────────────────────────────────────── */
    div[data-testid="metric-container"] {{
        background: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 14px !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 4px 16px {t['shadow']}, 0 1px 0 {t['border2']} !important;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
        backdrop-filter: blur(20px) !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    div[data-testid="metric-container"]::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, {t['gradient1']}, {t['gradient2']});
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    div[data-testid="metric-container"]:hover::before {{
        opacity: 1;
    }}
    div[data-testid="metric-container"]:hover {{
        transform: translateY(-4px) !important;
        box-shadow: 0 16px 40px {t['shadow']}, 0 0 0 1px {t['border2']} !important;
        border-color: {t['primary']}44 !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, {t['gradient1']}, {t['gradient2']}) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        letter-spacing: -0.5px !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
        color: {t['muted']} !important;
        font-weight: 600 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }}
    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
        font-size: 0.8rem !important;
        font-weight: 600 !important;
    }}

    /* ─── BUTTONS ────────────────────────────────────────────────── */
    .stButton > button {{
        background: linear-gradient(135deg, {t['gradient1']}, {t['gradient2']}) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 2px 8px rgba({t['primary_rgb']}, 0.3) !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    .stButton > button::after {{
        content: '';
        position: absolute;
        top: 50%; left: 50%;
        width: 0; height: 0;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.4s ease, height 0.4s ease;
    }}
    .stButton > button:hover::after {{
        width: 300px; height: 300px;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba({t['primary_rgb']}, 0.4) !important;
    }}
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}

    /* Secondary buttons */
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        color: {t['primary']} !important;
        border: 1.5px solid {t['primary']} !important;
        box-shadow: none !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: rgba({t['primary_rgb']}, 0.08) !important;
        box-shadow: 0 4px 12px rgba({t['primary_rgb']}, 0.15) !important;
    }}

    /* ─── INPUTS ─────────────────────────────────────────────────── */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {{
        background: {t['card_bg']} !important;
        color: {t['text_strong']} !important;
        border: 1.5px solid {t['border']} !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.9rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
        backdrop-filter: blur(10px) !important;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: {t['primary']} !important;
        box-shadow: 0 0 0 3px rgba({t['primary_rgb']}, 0.15) !important;
        outline: none !important;
    }}

    .stSelectbox > div > div {{
        background: {t['card_bg']} !important;
        color: {t['text']} !important;
        border: 1.5px solid {t['border']} !important;
        border-radius: 10px !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.2s ease !important;
    }}
    .stSelectbox > div > div:focus-within {{
        border-color: {t['primary']} !important;
        box-shadow: 0 0 0 3px rgba({t['primary_rgb']}, 0.15) !important;
    }}

    .stSlider [data-testid="stSlider"] {{
        color: {t['primary']} !important;
    }}

    /* ─── TABS ───────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        background: transparent !important;
        border-bottom: 2px solid {t['border']} !important;
        gap: 0.5rem !important;
        padding-bottom: 0 !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {t['muted']} !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.75rem 1.25rem !important;
        border-radius: 8px 8px 0 0 !important;
        transition: all 0.2s ease !important;
        border: none !important;
        background: transparent !important;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {t['primary']} !important;
        background: rgba({t['primary_rgb']}, 0.06) !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {t['primary']} !important;
        background: rgba({t['primary_rgb']}, 0.08) !important;
        border-bottom: 3px solid {t['primary']} !important;
        font-weight: 700 !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 1.5rem !important;
    }}

    /* ─── DATAFRAME / TABLE ──────────────────────────────────────── */
    .stDataFrame, .stDataFrame [data-testid="stDataFrame"] {{
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid {t['border']} !important;
    }}
    .stDataFrame thead tr th {{
        background: linear-gradient(135deg, rgba({t['primary_rgb']}, 0.15), rgba(99, 102, 241, 0.1)) !important;
        color: {t['primary']} !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        border-bottom: 2px solid {t['border2']} !important;
        padding: 0.75rem 1rem !important;
    }}
    .stDataFrame tbody tr td {{
        color: {t['text']} !important;
        font-size: 0.875rem !important;
        padding: 0.6rem 1rem !important;
        border-bottom: 1px solid {t['border']} !important;
    }}
    .stDataFrame tbody tr:hover td {{
        background: rgba({t['primary_rgb']}, 0.04) !important;
    }}

    /* ─── EXPANDER ───────────────────────────────────────────────── */
    .streamlit-expanderHeader {{
        background: {t['card_bg']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }}
    .streamlit-expanderHeader:hover {{
        border-color: {t['primary']}44 !important;
        background: rgba({t['primary_rgb']}, 0.04) !important;
    }}

    /* ─── ALERTS / NOTIFICATIONS ─────────────────────────────────── */
    .stSuccess  {{ background: rgba(16, 185, 129, 0.1) !important; border-left: 4px solid #10B981 !important; border-radius: 10px !important; }}
    .stError    {{ background: rgba(244, 63, 94, 0.1) !important;  border-left: 4px solid #F43F5E !important; border-radius: 10px !important; }}
    .stWarning  {{ background: rgba(245, 158, 11, 0.1) !important; border-left: 4px solid #F59E0B !important; border-radius: 10px !important; }}
    .stInfo     {{ background: rgba({t['primary_rgb']}, 0.08) !important; border-left: 4px solid {t['primary']} !important; border-radius: 10px !important; }}

    /* ─── PROGRESS BAR ───────────────────────────────────────────── */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {t['gradient1']}, {t['gradient2']}) !important;
        border-radius: 100px !important;
    }}
    .stProgress > div {{
        background: {t['border']} !important;
        border-radius: 100px !important;
        height: 8px !important;
    }}

    /* ─── DIVIDER ────────────────────────────────────────────────── */
    hr {{
        border: none !important;
        border-top: 1px solid {t['border']} !important;
        opacity: 0.7 !important;
        margin: 1.5rem 0 !important;
    }}

    /* ─── SPINNER ────────────────────────────────────────────────── */
    .stSpinner > div {{
        border-top-color: {t['primary']} !important;
    }}

    /* ─── CODE BLOCKS ────────────────────────────────────────────── */
    code, pre {{
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
    }}
    .stCode {{
        background: {t['card_bg']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 10px !important;
    }}

    /* ─── TOOLTIP / POPOVER ──────────────────────────────────────── */
    [data-testid="stPopover"] > div {{
        background: {t['card_bg']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 12px !important;
        box-shadow: 0 20px 60px {t['shadow']} !important;
        backdrop-filter: blur(20px) !important;
    }}

    /* ─── HEADER BAR (Fixed) ──────────────────────────────────────── */
    .apex-header {{
        position: fixed; top: 0; left: 0; right: 0;
        height: 60px;
        background: {t['nav_bg']};
        border-bottom: 1px solid {t['border']};
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 2rem;
        z-index: 999999;
        box-shadow: 0 4px 20px {t['shadow']};
        backdrop-filter: blur(20px);
    }}

    /* ─── CARD COMPONENTS ────────────────────────────────────────── */
    .pq-card {{
        background: {t['card_bg']};
        border-radius: 14px;
        padding: 1.5rem;
        border: 1px solid {t['card_border']};
        box-shadow: 0 4px 16px {t['shadow']};
        margin-bottom: 1.25rem;
        backdrop-filter: blur(20px);
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }}
    .pq-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, {t['gradient1']}, {t['gradient2']});
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    .pq-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 32px {t['shadow']}, 0 0 0 1px {t['border2']};
        border-color: {t['primary']}33;
    }}
    .pq-card:hover::before {{
        opacity: 1;
    }}

    /* ─── STAT BADGE ─────────────────────────────────────────────── */
    .stat-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 100px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .stat-badge.success {{ background: rgba(16,185,129,0.15); color: #10B981; }}
    .stat-badge.danger  {{ background: rgba(244,63,94,0.15);  color: #F43F5E; }}
    .stat-badge.warning {{ background: rgba(245,158,11,0.15); color: #F59E0B; }}
    .stat-badge.info    {{ background: rgba({t['primary_rgb']}, 0.15); color: {t['primary']}; }}

    /* ─── GRADIENT TEXT UTILITY ──────────────────────────────────── */
    .gradient-text {{
        background: linear-gradient(135deg, {t['gradient1']}, {t['gradient2']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }}

    /* ─── SHIMMER LOADING ────────────────────────────────────────── */
    .shimmer {{
        background: linear-gradient(90deg,
            {t['card_bg']} 25%,
            rgba({t['primary_rgb']}, 0.05) 50%,
            {t['card_bg']} 75%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }}
    @keyframes shimmer {{
        0%   {{ background-position: 200% 0; }}
        100% {{ background-position: -200% 0; }}
    }}

    /* ─── PULSE ANIMATION ────────────────────────────────────────── */
    .pulse {{
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50%       {{ opacity: 0.5; }}
    }}

    /* ─── SIDEBAR NAV ITEM ───────────────────────────────────────── */
    section[data-testid="stSidebar"] .stSelectbox {{
        margin-top: 0.25rem !important;
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: {t['muted2']} !important;
        border: 1px solid {t['border']} !important;
        box-shadow: none !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
        margin-bottom: 0.2rem !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba({t['primary_rgb']}, 0.08) !important;
        color: {t['primary']} !important;
        border-color: {t['border2']} !important;
        transform: translateX(3px) !important;
        box-shadow: none !important;
    }}

    /* Logout button - keep it special */
    section[data-testid="stSidebar"] button[id*="logout"] {{
        background: rgba(244, 63, 94, 0.1) !important;
        color: #F43F5E !important;
        border-color: rgba(244, 63, 94, 0.3) !important;
    }}
    section[data-testid="stSidebar"] button[id*="logout"]:hover {{
        background: rgba(244, 63, 94, 0.2) !important;
        transform: none !important;
    }}

    /* ─── PLOTLY CHART CONTAINER ─────────────────────────────────── */
    .js-plotly-plot {{
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ─── POPOVER CONTENT ────────────────────────────────────────── */
    [data-testid="stPopover"] button {{
        background: transparent !important;
        color: {t['text']} !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0 0.5rem !important;
        min-height: auto !important;
        box-shadow: none !important;
        transition: color 0.2s ease !important;
    }}
    [data-testid="stPopover"] button:hover {{
        color: {t['primary']} !important;
        background: transparent !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* ─── LINK STYLE ─────────────────────────────────────────────── */
    a {{
        color: {t['primary']} !important;
        text-decoration: none !important;
        transition: opacity 0.2s ease !important;
    }}
    a:hover {{ opacity: 0.75 !important; }}

    /* ─── PAGE SECTION HEADER ────────────────────────────────────── */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid {t['border']};
    }}
    .section-header .icon-wrap {{
        width: 40px; height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, rgba({t['primary_rgb']}, 0.15), rgba(99,102,241,0.1));
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }}
    .section-header h2 {{
        margin: 0 !important;
        font-size: 1.25rem !important;
        color: {t['text_strong']} !important;
    }}
    .section-header p {{
        margin: 0 !important;
        font-size: 0.8rem !important;
        color: {t['muted']} !important;
    }}

    /* ─── TOP NAV TOP TIER ───────────────────────────────────────── */
    .findeks-top-tier {{
        background: {t['bg2']};
        border-bottom: 1px solid {t['border']};
        font-family: 'Inter', sans-serif;
    }}

    /* ─── FLOATING LANGUAGE SWITCHER ─────────────────────────────── */
    div[data-testid="stSelectbox"] > div > div {{
        background: transparent !important;
        border-color: {t['border']} !important;
        font-size: 0.8rem !important;
        color: {t['text']} !important;
    }}

    /* ─── STATUS INDICATOR DOT ───────────────────────────────────── */
    .status-dot {{
        width: 8px; height: 8px;
        border-radius: 50%;
        display: inline-block;
        position: relative;
    }}
    .status-dot.online {{
        background: #10B981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: statusPulse 2s infinite;
    }}
    @keyframes statusPulse {{
        0%   {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
        70%  {{ box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}

    /* ─── SMOOTH TRANSITIONS ─────────────────────────────────────── */
    * {{ transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1); }}
    
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
#  COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────

def score_gauge_html(score: float, color: str, label: str = "Kredi Skoru") -> str:
    """Premium animasyonlu skor göstergesi."""
    t = st.session_state.get("theme_palette", {
        "card_bg": "#1E293B", "text": "#F8FAFC",
        "muted": "#64748B", "border": "#334155"
    })
    bg_circle = "#1E3A5F" if st.session_state.get("theme", "dark") == "dark" else "#E5E7EB"

    pct    = (score - 300) / (850 - 300)
    r      = 52
    c      = 2 * 3.14159 * r
    offset = c * (1 - pct)

    risk   = get_risk_label(score)
    risk_colors = {
        "Mükemmel": "#10B981", "Çok İyi": "#38BDF8",
        "İyi": "#6366F1", "Orta": "#F59E0B", "Zayıf": "#F43F5E"
    }
    risk_color = risk_colors.get(risk, color)

    return f"""
    <div style="
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        padding: 1.5rem;
        background: {t['card_bg']};
        border-radius: 16px;
        border: 1px solid rgba({_hex_to_rgb(color)}, 0.2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2), 0 0 0 1px rgba({_hex_to_rgb(color)}, 0.1);
    ">
        <svg width="160" height="160" viewBox="0 0 120 120" style="filter: drop-shadow(0 4px 12px rgba({_hex_to_rgb(color)}, 0.3));">
            <circle cx="60" cy="60" r="{r}" stroke="{bg_circle}" stroke-width="8" fill="none"/>
            <circle cx="60" cy="60" r="{r}" stroke="{color}" stroke-width="10" fill="none"
                stroke-dasharray="{c}" stroke-dashoffset="{offset}"
                stroke-linecap="round" transform="rotate(-90 60 60)"
                style="transition: stroke-dashoffset 1.5s cubic-bezier(0.16, 1, 0.3, 1);" />
            <text x="60" y="54" text-anchor="middle" font-size="22" font-weight="900"
                fill="{t['text']}" font-family="Inter" letter-spacing="-1">{score:.0f}</text>
            <text x="60" y="70" text-anchor="middle" font-size="7.5" font-weight="600"
                fill="{t['muted']}" font-family="Inter" style="text-transform:uppercase; letter-spacing:1px;">{label}</text>
        </svg>
        <div style="
            margin-top: 0.75rem;
            font-weight: 800;
            color: {risk_color};
            font-size: 1rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        ">{risk}</div>
    </div>
    """


def _hex_to_rgb(hex_color: str) -> str:
    """Hex rengi RGB string'e çevirir (ör: #38BDF8 → 56, 189, 248)."""
    h = hex_color.lstrip('#')
    if len(h) != 6:
        return "56, 189, 248"
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r}, {g}, {b}"
    except Exception:
        return "56, 189, 248"


def get_risk_label(score: float) -> str:
    if score >= 800: return "Mükemmel"
    if score >= 740: return "Çok İyi"
    if score >= 670: return "İyi"
    if score >= 580: return "Orta"
    return "Zayıf"


def get_risk_color(score: float) -> str:
    if score >= 800: return "#10B981"
    if score >= 740: return "#38BDF8"
    if score >= 670: return "#6366F1"
    if score >= 580: return "#F59E0B"
    return "#F43F5E"


def kpi_card_html(title: str, value: str, subtitle: str = "",
                  color: str = "#38BDF8", icon: str = "📊",
                  trend: str = "", trend_positive: bool = True) -> str:
    """Kurumsal premium KPI kartı."""
    t = st.session_state.get("theme_palette", {
        "card_bg": "rgba(13,31,60,0.85)",
        "text": "#E2E8F0", "text_strong": "#F8FAFC",
        "muted": "#64748B", "shadow": "rgba(0,0,0,0.5)",
        "border": "rgba(51,65,85,0.8)"
    })
    rgb = _hex_to_rgb(color)
    trend_color = "#10B981" if trend_positive else "#F43F5E"
    trend_icon  = "↑" if trend_positive else "↓"
    trend_html  = f'<span style="color:{trend_color}; font-size:0.78rem; font-weight:700;">{trend_icon} {trend}</span>' if trend else ""
    shadow      = t['shadow']
    card_bg     = t['card_bg']
    muted       = t['muted']

    return (
        f'<div style="'
        f'background:{card_bg};border-radius:14px;padding:1.5rem;'
        f'border:1px solid rgba({rgb},0.2);border-top:3px solid {color};'
        f'box-shadow:0 4px 20px {shadow},0 0 0 1px rgba({rgb},0.05);'
        f'margin-bottom:0.75rem;backdrop-filter:blur(20px);'
        f'transition:all 0.35s cubic-bezier(0.16,1,0.3,1);'
        f'position:relative;overflow:hidden;" '
        f'onmouseover="this.style.transform=\'translateY(-4px)\';this.style.boxShadow=\'0 16px 40px rgba(0,0,0,0.3)\'" '
        f'onmouseout="this.style.transform=\'translateY(0)\';this.style.boxShadow=\'0 4px 20px rgba(0,0,0,0.4)\'">'
        f'<div style="position:absolute;top:0;right:0;width:80px;height:80px;'
        f'background:radial-gradient(circle,rgba({rgb},0.12) 0%,transparent 70%);border-radius:50%;"></div>'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;position:relative;">'
        f'<div style="flex:1;">'
        f'<div style="color:{muted};font-size:0.7rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:0.5rem;">{title}</div>'
        f'<div style="color:{color};font-size:2rem;font-weight:900;line-height:1;'
        f'letter-spacing:-1px;margin-bottom:0.4rem;">{value}</div>'
        f'<div style="color:{muted};font-size:0.78rem;font-weight:500;">{subtitle}</div>'
        + (f'<div style="margin-top:0.4rem;">{trend_html}</div>' if trend else '')
        + f'</div>'
        f'<div style="font-size:1.75rem;opacity:0.8;margin-left:1rem;margin-top:-0.25rem;">{icon}</div>'
        f'</div></div>'
    )


def decision_banner_html(approved: bool, probability: float) -> str:
    """Premium Onay/Red Bannerı."""
    if approved:
        color     = "#10B981"
        bg        = "rgba(16, 185, 129, 0.08)"
        border_c  = "rgba(16, 185, 129, 0.3)"
        text_c    = "#10B981"
        text      = "KREDİ ONAYLANDI"
        icon      = "✅"
        sub       = "Başvuru risk kriterlerini karşılamaktadır"
    else:
        color     = "#F43F5E"
        bg        = "rgba(244, 63, 94, 0.08)"
        border_c  = "rgba(244, 63, 94, 0.3)"
        text_c    = "#F43F5E"
        text      = "KREDİ REDDEDİLDİ"
        icon      = "❌"
        sub       = "Başvuru risk eşiğini aşmaktadır"

    rgb = _hex_to_rgb(color)
    return f"""
    <div style="
        background: {bg};
        border: 1px solid {border_c};
        border-left: 5px solid {color};
        border-radius: 16px;
        padding: 2rem 2.5rem;
        text-align: center;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute; inset: 0;
            background: radial-gradient(ellipse at center, rgba({rgb}, 0.05) 0%, transparent 70%);
        "></div>
        <div style="font-size: 3.5rem; margin-bottom: 0.75rem; position: relative;">{icon}</div>
        <div style="
            font-size: 1.75rem;
            font-weight: 900;
            color: {text_c};
            letter-spacing: 0.05em;
            position: relative;
        ">{text}</div>
        <div style="
            font-size: 0.9rem;
            color: {text_c};
            opacity: 0.7;
            margin-top: 0.5rem;
            position: relative;
        ">{sub}</div>
        <div style="
            margin-top: 1rem;
            font-size: 1.1rem;
            font-weight: 700;
            color: {text_c};
            position: relative;
        ">Başarı Olasılığı: <span style="font-size: 1.4rem;">{probability*100:.1f}%</span></div>
    </div>
    """


def section_header_html(icon: str, title: str, subtitle: str = "") -> str:
    """Bölüm başlığı komponenti."""
    t = st.session_state.get("theme_palette", {
        "text_strong": "#F8FAFC", "muted": "#64748B",
        "primary_rgb": "56, 189, 248", "border": "rgba(51,65,85,0.8)"
    })
    sub_html = f'<p style="margin:0; font-size:0.8rem; color:{t["muted"]}; margin-top:2px;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="
        display: flex; align-items: center; gap: 0.75rem;
        margin-bottom: 1.5rem; padding-bottom: 1rem;
        border-bottom: 1px solid {t['border']};
    ">
        <div style="
            width: 42px; height: 42px; border-radius: 11px;
            background: linear-gradient(135deg, rgba({t['primary_rgb']}, 0.2), rgba(99,102,241,0.12));
            display: flex; align-items: center; justify-content: center;
            font-size: 1.25rem; flex-shrink: 0;
        ">{icon}</div>
        <div>
            <h2 style="
                margin: 0; font-size: 1.2rem; font-weight: 800;
                color: {t['text_strong']} !important;
            ">{title}</h2>
            {sub_html}
        </div>
    </div>
    """

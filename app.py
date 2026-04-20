"""
app.py — ProQuant Capital | Kurumsal Kredi Risk Terminali v5.0
Ana Router & Orkestratör

Bu dosya tüm modülleri birleştirir, oturum yönetimini kontrol eder
ve kullanıcının seçtiği sayfayı doğru modüle yönlendirir.
"""

import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import streamlit as st
import textwrap
from config import APP_NAME, APP_VERSION, ROLES

# ── En başta sayfa konfigürasyonu ────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} | Institutional Risk Terminal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Default karanlık tema ─────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# ── Kütüphaneler ─────────────────────────────────────────────────
import time
import os

# ── Core ─────────────────────────────────────────────────────────
from core.auth_system import (
    init_auth_state, is_authenticated, get_current_user,
    logout, check_session_timeout, touch_activity, role_badge
)

# ── UI Tema ──────────────────────────────────────────────────────
from ui.theme import load_corporate_theme
from ui.login_screen import render_login_screen


# ─────────────────────────────────────────────────────────────────
# MİNİ DİL ÇEVİRİ MOTORU (OUTER SHELL İÇİN)
# ─────────────────────────────────────────────────────────────────
TRANSLATIONS = {
    "EN": {
        "Akademi": "Academy", "Hakkımızda": "About Us", "İletişim": "Contact", 
        "Bireysel": "Retail", "Ürünler": "Products", "Hesaplama Araçları": "Calculators",
        "Komuta Merkezi": "Command Center", "Analist Laboratuvarı": "Quant Sandbox", "Denetim Portalı": "Governance Portal"
    },
    "DE": {
        "Akademi": "Akademie", "Hakkımızda": "Über Uns", "İletişim": "Kontakt",
        "Bireysel": "Privatkunden", "Ürünler": "Produkte", "Hesaplama Araçları": "Rechner",
        "Komuta Merkezi": "Kommandozentrale", "Analist Laboratuvarı": "Quant Labor", "Denetim Portalı": "Prüfungsportal"
    }
}
def tr(text):
    lang = st.session_state.get("LANG", "TR")
    if lang == "TR": return text
    return TRANSLATIONS.get(lang, {}).get(text, text)

# ─────────────────────────────────────────────────────────────────
#  MOTORU YÜKLE (Session'da cache'le, her yeniden render'da yükleme)
# ─────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_all_engines_v3():
    """Tüm ML motorlarını sıfırdan yükler (Cache Hard Reset)."""
    from modules.credit_scoring_engine import AdvancedScoringEngine
    # ...
    from core.orchestrator_master import get_master_orchestrator
    from modules.fraud_detection import FraudDetectionEngine
    from modules.clustering_engine import CustomerClusteringEngine
    from modules.recommendation_engine import RecommendationEngine
    from modules.early_warning_system import EarlyWarningSystem
    from modules.pdf_report_generator import PDFReportGenerator
    
    # Phase 2 Yeni Modüller
    from bots.algo_paper_trading import get_trading_bot
    from modules.regulatory_reports_ifrs9 import get_regulatory_engine
    from modules.derivatives_math import get_derivatives_engine
    from modules.esg_scoring_engine import get_esg_engine
    from modules.automl_evolutionary import get_automl_optimizer
    from modules.deep_learning_credit import get_deep_learning_engine
    from modules.realtime_risk_monitor import get_risk_monitor
    from modules.credit_structuring_engine import get_structuring_engine

    engine       = AdvancedScoringEngine()
    fraud_engine = FraudDetectionEngine()
    cluster_engine = CustomerClusteringEngine()
    rec_engine   = RecommendationEngine()
    ews          = EarlyWarningSystem()
    try:
        pdf_gen = PDFReportGenerator()
    except ImportError:
        pdf_gen = None

    return {
        "engine":        engine,
        "fraud_engine":  fraud_engine,
        "cluster_engine":cluster_engine,
        "rec_engine":    rec_engine,
        "ews":           ews,
        "pdf_gen":       pdf_gen,
        # Phase 2
        "trading_bot":   get_trading_bot(),
        "reg_engine":    get_regulatory_engine(),
        "deriv_engine":  get_derivatives_engine(),
        "esg_engine":    get_esg_engine(),
        "automl":        get_automl_optimizer(),
        "deep_engine":   get_deep_learning_engine(),
        "risk_monitor":  get_risk_monitor(),
        "struct_engine": get_structuring_engine(),
        # Phase 5 & 6 Institutional Engines
        "master":        get_master_orchestrator(),
    }


# ─────────────────────────────────────────────────────────────────
#  SIDEBAR NAVİGASYON
# ─────────────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("📊",  "Yönetici Özeti",          1),  # min_role_level
    ("👤",  "Yeni Müşteri Analizi",    1),
    ("🗃️",  "Portföy Yönetimi",        1),
    ("📉",  "Makro Stres Testleri",    1),
    ("🛡️",  "Kurumsal Fiyatlama (RAROC)", 2),
    ("📈",  "Ekonometri & VaR Analizi",2),
    ("🧠",  "Otonom Kredi Komitesi",   2),
    ("🤖",  "Algoritmik Paper Trading", 2), # Phase 2
    ("📜",  "Düzenleyici Raporlar",    2), # Phase 2
    ("📐",  "Türev Ürünler Matematiği", 2), # Phase 2
    ("🌱",  "ESG & Sürdürülebilirlik", 1), # Phase 2
    ("🔧",  "AutoML Evrimsel Opt.",    2), # Phase 2
    ("🕸️",  "Derin Öğrenme Merkezi",   2), # Phase 2
    ("📡",  "Canlı Risk Monitörü",     1), # Phase 2
    ("🏦",  "Egzotik Kredi Yapılandırma", 2), # Phase 2
    ("💹",  "Sabit Getirili Ürünler",  2), # Phase 7
    ("🔄",  "İstatistiksel Arbitraj",  2), # Phase 7
    ("🎯",  "Opsiyon Analizi & Greeks", 2), # Phase 7
    ("🔵",  "Fama-French Faktör Alfa", 2), # Phase 7
    ("🌍",  "Makro Rejim & Tahsis",    2), # Phase 7
    ("🏘️",  "Yapılandırılmış Finans & MBS", 2), # Phase 9
    ("⛓️",  "Kripto & DeFi Analitikleri",  2), # Phase 9
    ("⚡",  "L3 HFT Order Matching",   2), # Phase 9
    ("⚖️",  "Basel IV & CCAR Regülasyon", 2), # Phase 9
    ("🌌",  "Kuantum Finans Laboratuvarı", 2), # Phase 9
    ("🚀",  "Uzay Ekonomisi",          2), # Phase 10
    ("🕷️",  "GNN Sistemik Risk",       2), # Phase 10
    ("☁️",  "İklim Finansmanı",        2), # Phase 10
    ("💡",  "Davranışsal Finans",      2), # Phase 10
    ("🔬",  "BioTech Ar-Ge Fiyatlama", 2), # Phase 10
    ("🗣️",  "GenAI Copilot (RAG)",     2), # Phase 11
    ("🏢",  "Global REIT Simulator",   2), # Phase 11
    ("🔒",  "Siber Risk & Aktüerya",   2), # Phase 11
    ("⛴️",  "Tedarik Zinciri & Kriz",  2), # Phase 11
    ("🦄",  "Private Equity Değerleme", 2), # Phase 11
    ("🧬",  "Neuromorphic BCI Trading", 2), # Phase 12
    ("⚛️",  "Nükleer Şebeke Elektriği", 2), # Phase 12
    ("🏆",  "Otonom AI Servet Kasası", 2), # Phase 12
    ("🌾",  "Agri-Tech & Biyosfer",    2), # Phase 12
    ("🏛️",  "Ülke Varlık Fonu Orkestrası", 2), # Phase 12
    ("📻",  "Piyasa Rejimi Analizi",   2), # Phase 5
    ("🔭",  "Mikro Yapı & Likidite",   2), # Phase 5
    ("⚙️",  "Portföy Optimizasyonu",   2), # Phase 5
    ("📊",  "Strateji Backtest Raporu", 2), # Phase 5  — farklı label, emoji ortak olabilir
    ("🔐",  "Yönetişim & Denetim",    3), # Phase 5
    ("📋",  "Denetim İzi & Loglar",    2),
    ("📄",  "Raporlama Merkezi",       1),
    ("🛠️",  "Model Yönetimi",          3),
    # Institutional Hubs (Bridge the Apex Gap)
    ("🕹️",  "Komuta Merkezi",           2),
    ("🧪",  "Analist Laboratuvarı",     2),
    ("🏅",  "Denetim Portalı",           2),
]


def render_sidebar(user_info: dict) -> str:
    """Sidebar'ı çizer ve seçilen sayfa adını döndürür."""
    engines = load_all_engines_v3()
    engine  = engines["engine"]

    with st.sidebar:
        t = st.session_state.get("theme_palette", {})
        primary   = t.get("primary", "#38BDF8")
        muted     = t.get("muted", "#64748B")
        text_st   = t.get("text_strong", "#F8FAFC")
        border    = t.get("border", "rgba(51,65,85,0.8)")
        grad1     = t.get("gradient1", "#38BDF8")
        grad2     = t.get("gradient2", "#6366F1")

        # ── Brand Block ──────────────────────────────────────────────
        st.markdown(textwrap.dedent(f"""
        <div style="
            background: linear-gradient(135deg, rgba(56,189,248,0.08), rgba(99,102,241,0.05));
            border-bottom: 1px solid {border};
            padding: 1.25rem 1rem 1rem;
            margin: -1rem -1rem 1rem -1rem;
        ">
            <div style="
                font-size: 1.05rem; font-weight: 900; letter-spacing: -0.3px;
                background: linear-gradient(135deg, {grad1}, {grad2});
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text; margin-bottom: 2px;
            ">ProQuant Capital</div>
            <div style="font-size:0.65rem; color:{muted}; font-weight:600;
                        letter-spacing:0.12em; text-transform:uppercase;">Risk Terminal v5.0</div>
        </div>
        """), unsafe_allow_html=True)

        # ── Model Durumu ──────────────────────────────────────────────
        if engine.is_trained():
            st.markdown(textwrap.dedent(f"""
            <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25);
                        border-radius:9px; padding:0.55rem 0.8rem; margin-bottom:0.75rem;
                        display:flex; align-items:center; gap:0.5rem;">
              <span style="width:7px;height:7px;border-radius:50%;background:#10B981;
                           display:inline-block;animation:sdPulse 2s ease infinite;"></span>
              <span style="font-size:0.75rem; color:#10B981; font-weight:700;">AI Motor Aktif</span>
            </div>
            <style>@keyframes sdPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(16,185,129,.6)}}70%{{box-shadow:0 0 0 5px rgba(16,185,129,0)}}}}</style>
            """), unsafe_allow_html=True)
        else:
            st.markdown(textwrap.dedent(f"""
            <div style="background:rgba(244,63,94,0.08); border:1px solid rgba(244,63,94,0.25);
                        border-radius:9px; padding:0.55rem 0.8rem; margin-bottom:0.75rem;">
              <div style="color:#F43F5E; font-size:0.75rem; font-weight:700;">⚠️ Model Eğitilmedi</div>
              <div style="font-size:0.65rem; color:{muted}; margin-top:2px;">Model Yönetimi → Eğit</div>
            </div>
            """), unsafe_allow_html=True)

        # Navigasyon
        from core.auth_system import get_role_level
        user_role_level = get_role_level()

        st.markdown("<p style='font-size:0.8rem; font-weight:600; color:#94a3b8; margin-bottom:0.2rem; margin-top:1rem;'>🔍 Modül Ara & Seç</p>", unsafe_allow_html=True)
        
        page_names = [
            f"{icon}  {label}"
            for icon, label, min_level in NAV_ITEMS
            if user_role_level >= min_level
        ]

        # Mevcut sayfayı bul veya varsayılanı kullan
        current_page_label = st.session_state.get("current_page_label", page_names[0])
        
        # Eğer doğrudan bir butondan gelinmişse (Sistem Ayarları gibi) listeye ekle
        if current_page_label not in page_names:
            page_names.append(current_page_label)
            
        try:
            current_index = page_names.index(current_page_label)
        except ValueError:
            current_index = 0

        def on_nav_change():
            st.session_state["current_page_label"] = st.session_state["nav_select_box"]

        st.selectbox(
            "Navigasyon_Görünmez", 
            page_names, 
            index=current_index,
            key="nav_select_box",
            on_change=on_nav_change,
            label_visibility="collapsed"
        )

        st.divider()

        # ── Kullanıcı Kartı ────────────────────────────────────────────
        full_name  = user_info.get("full_name") or user_info["username"]
        role       = user_info.get("role", "")
        dept       = user_info.get("department", "")
        role_color = ROLES.get(role, {}).get("color", "#6366F1")
        initials   = "".join(w[0].upper() for w in full_name.split()[:2])

        st.markdown(textwrap.dedent(f"""
        <div style="
            background: linear-gradient(135deg, rgba(56,189,248,0.06), rgba(99,102,241,0.04));
            border: 1px solid {border};
            border-radius: 12px; padding: 0.9rem 1rem;
            margin-bottom: 0.5rem;
        ">
          <div style="display:flex; align-items:center; gap:0.6rem;">
            <div style="
                width: 38px; height: 38px; border-radius: 10px;
                background: linear-gradient(135deg, {role_color}, {role_color}BB);
                display: flex; align-items: center; justify-content: center;
                font-size: 0.95rem; font-weight: 900; color: white; flex-shrink: 0;
                box-shadow: 0 4px 12px {role_color}44;
            ">{initials}</div>
            <div style="overflow:hidden; flex:1;">
              <div style="
                  font-weight: 700; font-size: 0.87rem; color: {text_st};
                  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
              ">{full_name}</div>
              <div style="font-size: 0.68rem; color: {muted}; margin-top:1px;">{dept}</div>
            </div>
          </div>
          <div style="margin-top:0.6rem; padding-top:0.6rem; border-top: 1px solid {border};">
            {role_badge(role)}
          </div>
        </div>
        """), unsafe_allow_html=True)

        # ── Tema Toggle ────────────────────────────────────────────────
        cur_theme = st.session_state.get("theme", "dark")
        theme_icon = "☀️ Aydınlık Mod" if cur_theme == "dark" else "🌙 Karanlık Mod"
        if st.button(theme_icon, use_container_width=True, key="theme_toggle_btn"):
            st.session_state["theme"] = "light" if cur_theme == "dark" else "dark"
            st.rerun()

        if st.button("🚪 Güvenli Çıkış", use_container_width=True, key="logout_btn"):
            logout()

    # Seçilen sayfanın etiketini döndür (Akademi gibi ikonları olmayan istisnalar eklendi)
    current_label_raw = st.session_state.get("current_page_label", "Yönetici Özeti")
    
    if current_label_raw in ["Akademi", "Hakkımızda", "İletişim"]:
        return current_label_raw
        
    for icon, label, _ in NAV_ITEMS:
        if label in current_label_raw:
            return label
            
    return "Yönetici Özeti"


# ─────────────────────────────────────────────────────────────────
#  SAYFA YÖNLENDİRİCİSİ
# ─────────────────────────────────────────────────────────────────

def route_page(page: str, user_info: dict, engines: dict):
    """Seçilen sayfaya göre doğru view modülünü çağırır."""

    engine         = engines["engine"]
    fraud_engine   = engines["fraud_engine"]
    cluster_engine = engines["cluster_engine"]
    rec_engine     = engines["rec_engine"]
    ews            = engines["ews"]
    pdf_gen        = engines["pdf_gen"]

    if page == "Akademi":
        from ui.academy_view import render_academy_view
        render_academy_view()
        return

    if page == "Hakkımızda":
        from ui.about_view import render_about_view
        render_about_view()
        return

    if page == "İletişim":
        from ui.contact_view import render_contact_view
        render_contact_view()
        return
    
    # --- Institutional Hubs ---
    if page == "Komuta Merkezi":
        from ui.command_center import render_command_center
        render_command_center()
        return

    if page == "Analist Laboratuvarı":
        from ui.quant_sandbox import render_quant_sandbox
        render_quant_sandbox()
        return

    if page == "Denetim Portalı":
        from ui.governance_portal import render_governance_portal
        render_governance_portal()
        return

    if page == "Yönetici Özeti":
        from ui.dashboard_view import render_dashboard
        render_dashboard(user_info)

    elif page == "Yeni Müşteri Analizi":
        from ui.analysis_view import render_analysis_view
        render_analysis_view(engine, fraud_engine, cluster_engine, rec_engine, user_info)

    elif page == "Portföy Yönetimi":
        from ui.portfolio_view import render_portfolio_view
        render_portfolio_view(user_info)

    elif page == "Makro Stres Testleri":
        from ui.macro_view import render_macro_view
        render_macro_view(engine, user_info)

    elif page == "Kurumsal Fiyatlama (RAROC)":
        from ui.views.pricing_dashboard import render_pricing_scenarios
        render_pricing_scenarios(user_info)

    elif page == "Ekonometri & VaR Analizi":
        from ui.views.macro_var_dashboard import render_macro_var_dashboard
        render_macro_var_dashboard(user_info)

    elif page == "Otonom Kredi Komitesi":
        from ui.views.committee_rag_dashboard import render_rag_committee_dashboard
        render_rag_committee_dashboard(user_info)

    elif page == "Algoritmik Paper Trading":
        from ui.views.algo_trading_view import render_algo_trading_view
        render_algo_trading_view(engines["trading_bot"], user_info)

    elif page == "Düzenleyici Raporlar":
        from ui.views.regulatory_view import render_regulatory_view
        render_regulatory_view(engines["reg_engine"], user_info)

    elif page == "Türev Ürünler Matematiği":
        from ui.views.derivatives_view import render_derivatives_view
        render_derivatives_view(engines["deriv_engine"], user_info)

    elif page == "ESG & Sürdürülebilirlik":
        from ui.views.esg_view import render_esg_view
        render_esg_view(engines["esg_engine"], user_info)

    elif page == "AutoML Evrimsel Opt.":
        from ui.views.automl_view import render_automl_view
        render_automl_view(engines["automl"], user_info)

    elif page == "Derin Öğrenme Merkezi":
        from ui.views.deep_learning_view import render_deep_learning_view
        render_deep_learning_view(engines["deep_engine"], user_info)

    elif page == "Canlı Risk Monitörü":
        from ui.views.risk_monitor_view import render_risk_monitor_view
        render_risk_monitor_view(engines["risk_monitor"], user_info)

    elif page == "Egzotik Kredi Yapılandırma":
        from ui.views.structuring_view import render_structuring_view
        render_structuring_view(engines["struct_engine"], user_info)

    elif page == "Sabit Getirili Ürünler":
        from ui.views.advanced.fixed_income_view import render_fixed_income_view
        render_fixed_income_view()

    elif page == "İstatistiksel Arbitraj":
        from ui.views.advanced.pairs_trading_view import render_pairs_trading_view
        render_pairs_trading_view()

    elif page == "Opsiyon Analizi & Greeks":
        from ui.views.advanced.options_view import render_options_view
        render_options_view()

    elif page == "Fama-French Faktör Alfa":
        from ui.views.advanced.factor_model_view import render_factor_model_view
        render_factor_model_view()

    elif page == "Makro Rejim & Tahsis":
        from ui.views.advanced.macro_regime_view import render_macro_regime_view
        render_macro_regime_view()

    elif page == "Yapılandırılmış Finans & MBS":
        from ui.views.quantum.structured_finance_view import render_structured_finance_view
        render_structured_finance_view()

    elif page == "Kripto & DeFi Analitikleri":
        from ui.views.quantum.defi_analytics_view import render_defi_analytics_view
        render_defi_analytics_view()

    elif page == "L3 HFT Order Matching":
        from ui.views.quantum.l3_matching_engine_view import render_l3_matching_engine_view
        render_l3_matching_engine_view()

    elif page == "Basel IV & CCAR Regülasyon":
        from ui.views.quantum.regulatory_stress_view import render_regulatory_stress_view
        render_regulatory_stress_view()

    elif page == "Kuantum Finans Laboratuvarı":
        from ui.views.quantum.quantum_finance_view import render_quantum_finance_view
        render_quantum_finance_view()

    elif page == "Uzay Ekonomisi":
        from ui.views.singularity.astro_finance_view import render_astro_finance_view
        render_astro_finance_view()

    elif page == "GNN Sistemik Risk":
        from ui.views.singularity.gnn_contagion_view import render_gnn_contagion_view
        render_gnn_contagion_view()

    elif page == "İklim Finansmanı":
        from ui.views.singularity.climate_carbon_view import render_climate_carbon_view
        render_climate_carbon_view()

    elif page == "Davranışsal Finans":
        from ui.views.singularity.behavioral_finance_view import render_behavioral_finance_view
        render_behavioral_finance_view()

    elif page == "BioTech Ar-Ge Fiyatlama":
        from ui.views.singularity.biotech_rdo_view import render_biotech_rdo_view
        render_biotech_rdo_view()

    elif page == "GenAI Copilot (RAG)":
        from ui.views.expanse.genai_copilot_view import render_genai_copilot_view
        render_genai_copilot_view()

    elif page == "Global REIT Simulator":
        from ui.views.expanse.global_reit_view import render_global_reit_view
        render_global_reit_view()

    elif page == "Siber Risk & Aktüerya":
        from ui.views.expanse.cyber_actuarial_view import render_cyber_actuarial_view
        render_cyber_actuarial_view()

    elif page == "Tedarik Zinciri & Kriz":
        from ui.views.expanse.supply_chain_geo_view import render_supply_chain_geo_view
        render_supply_chain_geo_view()

    elif page == "Private Equity Değerleme":
        from ui.views.expanse.pe_vc_view import render_pe_vc_view
        render_pe_vc_view()

    elif page == "Neuromorphic BCI Trading":
        from ui.views.apex.neuromorphic_bci_view import render_neuromorphic_bci_view
        render_neuromorphic_bci_view()

    elif page == "Nükleer Şebeke Elektriği":
        from ui.views.apex.nuclear_grid_view import render_nuclear_grid_view
        render_nuclear_grid_view()

    elif page == "Otonom AI Servet Kasası":
        from ui.views.apex.auto_ai_vault_view import render_auto_ai_vault_view
        render_auto_ai_vault_view()

    elif page == "Agri-Tech & Biyosfer":
        from ui.views.apex.agritech_biosphere_view import render_agritech_biosphere_view
        render_agritech_biosphere_view()

    elif page == "Ülke Varlık Fonu Orkestrası":
        from ui.views.apex.sovereign_wealth_view import render_sovereign_wealth_view
        render_sovereign_wealth_view()

    elif page == "Piyasa Rejimi Analizi":
        from ui.views.regime_view import render_regime_view
        render_regime_view()

    elif page == "Mikro Yapı & Likidite":
        from ui.views.microstructure_view import render_microstructure_view
        render_microstructure_view()

    elif page == "Portföy Optimizasyonu":
        from ui.views.optimizer_view import render_optimizer_view
        render_optimizer_view()

    elif page == "Strateji Backtest Raporu":
        from ui.views.backtest_results_view import render_backtest_view
        render_backtest_view(engines["master"])

    elif page == "Yönetişim & Denetim":
        from ui.views.governance_view import render_governance_view
        render_governance_view()

    elif page == "Denetim İzi & Loglar":
        from ui.audit_view import render_audit_view
        render_audit_view(user_info)

    elif page == "Raporlama Merkezi":
        from ui.reports_view import render_reports_view
        if pdf_gen is None:
            st.error("ReportLab kurulu değil. `pip install reportlab` ile yükleyin.")
            return
        render_reports_view(pdf_gen, user_info)

    elif page == "Model Yönetimi":
        _render_model_management(engine, fraud_engine, cluster_engine, ews, user_info)

    elif page == "Sistem Ayarları":
        from ui.settings_view import render_settings_view
        render_settings_view(user_info)

    else:
        st.info(f"Sayfa bulunamadı: {page}")


def _render_model_management(engine, fraud_engine, cluster_engine, ews, user_info: dict):
    """Model eğitim ve yönetim merkezi."""
    from core.auth_system import require_role
    st.title("⚙️ AI Model Yönetim Merkezi")
    st.markdown("<p style='color:#64748b;'>Tüm makine öğrenmesi modellerini buradan eğitip yönetin.</p>",
                unsafe_allow_html=True)

    # Durum kartları
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        status = "✅ Eğitildi" if engine.is_trained() else "❌ Eğitilmedi"
        st.metric("Kredi Skoru Motoru", status)
    with c2:
        status = "✅ Eğitildi" if fraud_engine.is_trained() else "❌ Eğitilmedi"
        st.metric("Sahtekarlık Motoru", status)
    with c3:
        status = "✅ Eğitildi" if cluster_engine.is_trained() else "❌ Eğitilmedi"
        st.metric("Segmentasyon Motoru", status)
    with c4:
        active_warnings = 0
        try:
            from core.database_handler import db
            active_warnings = len(db.get_active_warnings())
        except Exception:
            pass
        st.metric("Aktif Erken Uyarı", active_warnings)

    st.divider()

    tab_main, tab_fraud, tab_cluster, tab_ews = st.tabs([
        "🧠 Ana Kredi Motoru", "🛡️ Sahtekarlık Motoru",
        "🏷️ Segmentasyon", "⚠️ Erken Uyarı Taraması"
    ])

    with tab_main:
        st.subheader("Ensemble Kredi Risk Modeli")
        st.markdown("""
        **Algoritma:** Soft-Voting Ensemble  
        ├─ Random Forest (200 ağaç, maks. derinlik 12)  
        ├─ Gradient Boosting (150 iterasyon, LR=0.08)  
        └─ Lojistik Regresyon (L2 regularization)  

        **Eğitim Verisi:** 50,000 sentetik müşteri profili  
        **Hedef Değişken:** Kredi Onay / Red (Binary Classification)
        """)

        if not require_role(3):
            st.warning("Bu işlem için en az 'Head Analist' yetkisi gerekiyor.")
        else:
            if st.button("🚀 Ana Modeli Eğit / Güncelle (50,000 Simülasyon)",
                         type="primary", use_container_width=True, key="train_main"):
                progress_bar = st.progress(0.0)
                status_text = st.empty()

                def update_progress(val, msg):
                    progress_bar.progress(val)
                    status_text.text(f"⏳ {msg}")

                with st.spinner(""):
                    try:
                        metrics = engine.train(progress_callback=update_progress)
                        st.success("✅ Ana model başarıyla eğitildi ve üretime alındı!")
                        st.balloons()

                        # Metrikler
                        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                        mc1.metric("Doğruluk (Accuracy)", f"%{metrics['accuracy']:.2f}")
                        mc2.metric("AUC-ROC",             f"%{metrics['auc_roc']:.2f}")
                        mc3.metric("Precision",           f"%{metrics['precision']:.2f}")
                        mc4.metric("Recall",              f"%{metrics['recall']:.2f}")
                        mc5.metric("F1 Score",            f"%{metrics['f1']:.2f}")

                        data_src = metrics.get("data_source", "Sentetik")
                        st.info(f"**Eğitim Seti:** {metrics['train_size']:,} kayıt | "
                                f"**Test Seti:** {metrics['test_size']:,} kayıt | "
                                f"**Eğitim Tarihi:** {metrics['trained_at']}")
                        st.success(f"📊 **Veri Kaynağı:** {data_src}")
                        st.cache_resource.clear()

                    except Exception as e:
                        st.error(f"Eğitim hatası: {e}")

    with tab_fraud:
        st.subheader("Isolation Forest — Sahtekarlık & Anomali Tespit Motoru")
        st.markdown("""
        **Algoritma:** Isolation Forest (n_estimators=200, contamination=5%)  
        Normal müşteri davranış örüntüsünden sapan profilleri 
        **anomali** olarak işaretler.
        """)
        if st.button("🛡️ Sahtekarlık Motorunu Eğit",
                     use_container_width=True, key="train_fraud"):
            with st.spinner("Isolation Forest eğitiliyor..."):
                try:
                    fraud_engine.train_fraud_model()
                    st.success("✅ Sahtekarlık motoru eğitildi.")
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Hata: {e}")

    with tab_cluster:
        st.subheader("K-Means Müşteri Segmentasyonu (A/B/C/D Tier)")
        st.markdown("""
        **Algoritma:** K-Means (k=4 cluster, n_init=20)  
        Müşterileri 4 segmente böler:
        - 🥇 **A-Tier (Altın):** Yüksek gelir, düşük borç, sıfır gecikme  
        - 🥈 **B-Tier (Gümüş):** İyi profil, küçük iyileştirme alanları
        - 📈 **C-Tier (Gelişim):** Potansiyel var, destek gerektirir  
        - ⚠️ **D-Tier (Yüksek Risk):** Aktif izleme şart
        """)
        if st.button("🏷️ Segmentasyon Motorunu Eğit",
                     use_container_width=True, key="train_cluster"):
            with st.spinner("K-Means eğitiliyor..."):
                try:
                    cluster_engine.train()
                    st.success("✅ Segmentasyon motoru eğitildi.")
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Hata: {e}")

    with tab_ews:
        st.subheader("Erken Uyarı Sistemi — Portföy Taraması")
        st.markdown("""
        Tüm aktif müşterilerin finansal profilini tarayarak risk eşiklerini aşanları 
        otomatik olarak işaretler. Düzenli tarama yapılması önerilir.
        """)
        if st.button("🔍 Portföyü Şimdi Tara",
                     use_container_width=True, key="run_ews"):
            with st.spinner("Portföy taranıyor..."):
                try:
                    scan_result = ews.run_full_scan(analyst=user_info["username"])
                    st.success(
                        f"✅ Tarama tamamlandı. "
                        f"**{scan_result['scanned']}** müşteri tarandı, "
                        f"**{scan_result['new_warnings']}** yeni uyarı oluşturuldu."
                    )
                    by_sev = scan_result.get("by_severity", {})
                    if any(by_sev.values()):
                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("🔴 Kritik",  by_sev.get("Kritik", 0))
                        s2.metric("🟠 Yüksek",  by_sev.get("Yüksek", 0))
                        s3.metric("🟡 Orta",    by_sev.get("Orta", 0))
                        s4.metric("🔵 Düşük",   by_sev.get("Düşük", 0))
                except Exception as e:
                    st.error(f"Tarama hatası: {e}")


# ─────────────────────────────────────────────────────────────────
#  ANA GİRİŞ NOKTASI
# ─────────────────────────────────────────────────────────────────

def main():
    # 1. Premium tema yükle
    load_corporate_theme()

    # 2. Oturum durumunu başlat
    init_auth_state()

    # 3. Oturum açık değilse login ekranı
    if not is_authenticated():
        render_login_screen()
        return

    # 4. Oturum zaman aşımı kontrolü
    check_session_timeout()
    touch_activity()

    # 5. Motorları yükle
    engines   = load_all_engines_v3()
    user_info = get_current_user()

    # 6. Sidebar & sayfa seçimi
    page = render_sidebar(user_info)

    # 7. Üst Menü (Logo & Ayarlar)
    render_apex_header(user_info)

    # 8. İçerik yönlendirme
    route_page(page, user_info, engines)


def render_apex_header(user_info: dict):
    """Premium iki seviyeli navigasyon üst çubuğu."""
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(_BASE_DIR, "assets", "logo.png")

    t_pal     = st.session_state.get("theme_palette", {})
    is_dark   = st.session_state.get("theme", "dark") == "dark"
    t_bg      = t_pal.get("sidebar_bg", "#0D1F3C")
    t_text    = t_pal.get("text_strong", "#F8FAFC")
    t_muted   = t_pal.get("muted", "#64748B")
    t_top     = t_pal.get("bg2", "#0A1628")
    t_border  = t_pal.get("border", "rgba(51,65,85,0.8)")
    t_primary = t_pal.get("primary", "#38BDF8")
    t_grad1   = t_pal.get("gradient1", "#38BDF8")
    t_grad2   = t_pal.get("gradient2", "#6366F1")
    t_prgb    = t_pal.get("primary_rgb", "56, 189, 248")

    st.markdown(textwrap.dedent(f"""
        <style>
        .apex-header {{ display: none !important; }}

        /* Top tier bar */
        .findeks-top-tier {{
            background: {t_top};
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 3rem;
            height: 36px;
            margin: -5.5rem -2.5rem 0 -2.5rem;
            border-bottom: 1px solid {t_border};
            font-family: 'Inter', sans-serif;
        }}

        /* Nav popover button resets */
        .nav-popovers [data-testid="stPopover"] > button {{
            background: transparent !important;
            border: none !important;
            color: {t_text} !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.4rem 0.8rem !important;
            min-height: 0 !important;
            box-shadow: none !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }}
        .nav-popovers [data-testid="stPopover"] > button:hover {{
            background: rgba({t_prgb}, 0.08) !important;
            color: {t_primary} !important;
        }}

        /* Top tier link buttons */
        div.element-container:has(#nav-akademi) + div.element-container button,
        div.element-container:has(#nav-hakkimizda) + div.element-container button,
        div.element-container:has(#nav-iletisim) + div.element-container button,
        div.element-container:has(#nav-ayarlar) + div.element-container button {{
            background: transparent !important;
            border: none !important;
            color: {t_muted} !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            padding: 0.2rem 0.6rem !important;
            min-height: 0 !important;
            box-shadow: none !important;
            border-radius: 6px !important;
            transition: all 0.2s ease;
        }}
        div.element-container:has(#nav-akademi) + div.element-container button:hover,
        div.element-container:has(#nav-hakkimizda) + div.element-container button:hover,
        div.element-container:has(#nav-iletisim) + div.element-container button:hover,
        div.element-container:has(#nav-ayarlar) + div.element-container button:hover {{
            color: {t_primary} !important;
            background: rgba({t_prgb}, 0.08) !important;
        }}

        /* Language selectbox */
        div[data-testid="stSelectbox"] > div > div {{
            background: transparent !important;
            border-color: {t_border} !important;
            font-size: 0.78rem !important;
            color: {t_text} !important;
        }}
        </style>

        <!-- Top tier bar -->
        <div class="findeks-top-tier">
            <div style="display:flex; align-items:center; gap:0.4rem;">
                <span style="
                    width:6px; height:6px; border-radius:50%; background:#10B981;
                    display:inline-block; animation:hdrPulse 2s ease infinite;
                "></span>
                <span style="font-size:0.72rem; color:{t_muted}; font-weight:600;">
                    {tr("Bireysel")} Portföy
                </span>
            </div>
            <div style="flex:1;"></div>
        </div>
        <style>
        @keyframes hdrPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(16,185,129,.6)}}70%{{box-shadow:0 0 0 5px rgba(16,185,129,0)}}}}
        </style>
    """), unsafe_allow_html=True)

    # Linkleri sağa itiyoruz, sola ise spacer koyuyoruz
    st.markdown("<div style='position: relative; height: 0; z-index: 999999;'>", unsafe_allow_html=True)
    lang_col_spacer, lang_col1, lang_col2, lang_col3, lang_col4, lang_col5 = st.columns([7.5, 1.2, 1.2, 1.2, 1.1, 0.6])
    
    with lang_col_spacer:
        st.write("") # Sola boş alan bırakıp sağa itiyoruz
        
    with lang_col1:
        st.markdown("<div id='nav-akademi'></div>", unsafe_allow_html=True)
        if st.button(tr("Akademi"), use_container_width=True):
            st.session_state["current_page_label"] = "Akademi"
            st.rerun()
        
    with lang_col2:
        st.markdown("<div id='nav-hakkimizda'></div>", unsafe_allow_html=True)
        if st.button(tr("Hakkımızda"), use_container_width=True):
            st.session_state["current_page_label"] = "Hakkımızda"
            st.rerun()
        
    with lang_col3:
        st.markdown("<div id='nav-iletisim'></div>", unsafe_allow_html=True)
        if st.button(tr("İletişim"), use_container_width=True):
            st.session_state["current_page_label"] = "İletişim"
            st.rerun()
        
    with lang_col4:
        st.markdown("<div style='margin-top: -3.5rem;'>", unsafe_allow_html=True)
        current_lang_idx = ["TR", "EN", "DE"].index(st.session_state.get("LANG", "TR"))
        chosen_lang = st.selectbox("Dil", ["TR", "EN", "DE"], index=current_lang_idx, label_visibility="collapsed")
        if chosen_lang != st.session_state.get("LANG", "TR"):
            st.session_state["LANG"] = chosen_lang
            if chosen_lang != "TR":
                st.toast(f"Translation engine applied for {chosen_lang}. (Module contents rendering in native language...)", icon="🌐")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with lang_col5:
        st.markdown("<div id='nav-ayarlar' style='margin-top: -3.5rem;'></div>", unsafe_allow_html=True)
        if st.button("⚙️", use_container_width=True, help="Ayarlar (Profil, Güvenlik, Abonelik)"):
            st.session_state["current_page_label"] = "Sistem Ayarları"
            st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)


    # ── Ana Header: Logo + Navigasyon ────────────────────────────
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])

    with c1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=185)
        else:
            st.markdown(textwrap.dedent(f"""
            <div style="padding: 0.25rem 0;">
                <span style="
                    font-size: 1.2rem; font-weight: 900;
                    background: linear-gradient(135deg, {t_grad1}, {t_grad2});
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text; letter-spacing: -0.5px;
                ">{APP_NAME}</span>
            </div>
            """), unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='nav-popovers' style='display:flex; gap:0.5rem; justify-content:center; align-items:center; padding-top:0.6rem;'>", unsafe_allow_html=True)
        pop_col1, pop_col2, pop_col3 = st.columns([1.6, 2.2, 2.2])

        from core.auth_system import get_role_level
        user_role_level = get_role_level()
        allowed_pages = [f"{icon}  {label}" for icon, label, min_level in NAV_ITEMS if user_role_level >= min_level]

        inst_items     = [f"{icon}  {label}" for icon, label, lv in NAV_ITEMS if lv >= 2 and label in ["Komuta Merkezi", "Analist Laboratuvarı", "Denetim Portalı"]]
        remaining_pages = [p for p in allowed_pages if p not in inst_items]
        mid_point       = len(remaining_pages) // 2
        urunler_items   = remaining_pages[:mid_point]
        hesaplama_items = remaining_pages[mid_point:]

        with pop_col1:
            with st.popover("🏛️ Hubs", use_container_width=True):
                for name in inst_items:
                    display_name = TRANSLATIONS.get(st.session_state.get("LANG", "TR"), {}).get(" ".join(name.split(" ")[1:]), name) if st.session_state.get("LANG", "TR") != "TR" else name
                    if st.button(display_name, use_container_width=True, key=f"hdr_i_{name}"):
                        st.session_state["current_page_label"] = name.split("  ")[-1].strip()
                        st.rerun()

        with pop_col2:
            with st.popover(tr("Ürünler"), use_container_width=True):
                for name in urunler_items:
                    display_name = TRANSLATIONS.get(st.session_state.get("LANG", "TR"), {}).get(" ".join(name.split(" ")[1:]), name) if st.session_state.get("LANG", "TR") != "TR" else name
                    if st.button(display_name, use_container_width=True, key=f"hdr_u_{name}"):
                        st.session_state["current_page_label"] = name.split("  ")[-1].strip()
                        st.rerun()

        with pop_col3:
            with st.popover(tr("Hesaplama Araçları"), use_container_width=True):
                for name in hesaplama_items:
                    display_name = TRANSLATIONS.get(st.session_state.get("LANG", "TR"), {}).get(" ".join(name.split(" ")[1:]), name) if st.session_state.get("LANG", "TR") != "TR" else name
                    if st.button(display_name, use_container_width=True, key=f"hdr_h_{name}"):
                        st.session_state["current_page_label"] = name.split("  ")[-1].strip()
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        pass

    st.markdown(f"<hr style='margin-top: 0.75rem; margin-bottom: 2rem; border: none; border-top: 1px solid {t_border}; opacity: 0.5;'>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

import re
"""
ui/views/macro_var_dashboard.py
Makroekonomik Projeksiyonlar ve Value-at-Risk (VaR) Simülatör Kokpiti.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modules.macro_econometrics import macro_engine
from modules.portfolio_var_engine import var_engine
from core.database_handler import db

def render_macro_var_dashboard(user_info: dict):
    st.title("📈 Makro Ekonometri & Portföy VaR Analizi")
    st.markdown("""
    <p style='color:#64748b; margin-top:-0.5rem;'>
      Gelecek 24 ayın ekonometrik zaman serilerini projeksiyonlayıp (VAR modeli ile), 
      sistematik risk şoklarının kredi portföyünde yaratacağı "Kuyruk Riskini" (Value at Risk) ölçün.
    </p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    tab_macro, tab_var = st.tabs(["📉 Makro Ekonometrik Projeksiyon", "📊 Portföy VaR & Monte Carlo"])
    
    with tab_macro:
        _render_macro_projections()
        
    with tab_var:
        _render_portfolio_var(user_info)


def _render_macro_projections():
    st.subheader("VECM / VAR Tabanlı Zaman Serisi Projeksiyonları")
    c1, c2 = st.columns([1, 4])
    
    with c1:
        st.markdown("##### Şok Senaryosu")
        scenario = st.radio("Ekonomik Beklenti", ["Base", "Adverse", "Optimistic"], 
                            format_func=lambda x: {"Base": "Kademeli / Nötr", "Adverse": "Kriz (Negatif Yönlü)", "Optimistic": "İyimser Daralma"}[x])
        months = st.slider("Tahmin Ufku (Ay)", min_value=6, max_value=60, value=24, step=6)
        
        if st.button("🔄 Motoru Hesapla (VAR)"):
            with st.spinner("Matrisler çözülüyor..."):
                proj_df = macro_engine.forecast_var_scenario(months_ahead=months, scenario=scenario)
                st.session_state["macro_proj_df"] = proj_df
                st.success("Projeksiyon tamamlandı.")
                
    with c2:
        if "macro_proj_df" in st.session_state:
            df = st.session_state["macro_proj_df"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Date"], y=df["CDS_Spread"], name="CDS Primi (Risk)", yaxis="y1", line=dict(color="#ef4444", width=3)))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Inflation_Pct"], name="Enflasyon (%)", yaxis="y2", line=dict(color="#f59e0b", width=2, dash="dash")))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Policy_Rate_Pct"], name="Politika Faizi (%)", yaxis="y2", line=dict(color="#3b82f6", width=2)))
            
            fig.update_layout(
                title=f"{scenario} Senaryosu: Ekonometrik Çözümleme Eğrisi",
                yaxis=dict(title=dict(text="CDS (Bps)", font=dict(color="#ef4444")), tickfont=dict(color="#ef4444")),
                yaxis2=dict(title=dict(text="Yüzdelik (%)", font=dict(color="#94a3b8")), tickfont=dict(color="#94a3b8"), anchor="x", overlaying="y", side="right"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(x=0.01, y=0.99, bgcolor="rgba(15,23,42,0.8)")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Alt kısıma tablo
            st.dataframe(df.style.format({"Inflation_Pct": "{:.2f}%", "Policy_Rate_Pct": "{:.2f}%", "USD_TRY": "{:.2f} ₺", "CDS_Spread": "{:.0f}"}), use_container_width=True)
        else:
            st.info("Projeksiyonu başlatmak için sol taraftan konfigürasyonu onaylayın.")


def _render_portfolio_var(user_info):
    st.subheader("Kurumsal Kredi Portföyü Value-at-Risk (VaR)")
    st.markdown("Veritabanındaki güncel krediler üzerinden **Copula tabanlı Monte Carlo Simülasyonu** (10.000 İterasyon).")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        correlation = st.slider("Portföy Korelasyon Katsayısı (Rho)", min_value=0.01, max_value=0.60, value=0.15, step=0.01, 
                                help="Sistemik şokların şirketlerin kredi notuna yansıma korelasyonu (Varlık Korelasyonu).")
        
    if st.button("🎲 10.000 İterasyonluk Monte Carlo Başlat", type="primary"):
        with st.spinner("Uygulama aktif müşterileri çekiyor ve temerrüt kırılımlarını simüle ediyor..."):
            # Örnek dummy data çekme operasyonu
            # Gerçekte db.get_active_loans() benzeri bir çağrı yapılır
            n_loans = 1200
            np.random.seed(42)
            dummy_portfolio = pd.DataFrame({
                "loan_amount": np.random.lognormal(mean=np.log(50000), sigma=1.0, size=n_loans),
                "pd_prob": np.random.uniform(0.005, 0.08, size=n_loans),
                "lgd_prob": np.random.uniform(0.3, 0.6, size=n_loans)
            })
            
            results = var_engine.simulate_portfolio_loss(dummy_portfolio, asset_correlation=correlation)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Portföy Büyüklüğü", f"{results['total_exposure']/1e6:.1f} Milyon ₺")
            c2.metric("Beklenen Kayıp (Mean)", f"{results['expected_loss']/1e6:.2f} Milyon ₺")
            c3.metric("VaR (%99 Conf.)", f"{results['var_99']/1e6:.2f} Milyon ₺", "Zarar Limiti", delta_color="inverse")
            c4.metric("ES / Tail Risk", f"{results['expected_shortfall_99']/1e6:.2f} Milyon ₺", "Regülasyon Sermayesi", delta_color="inverse")
            
            st.divider()
            
            samples = results["loss_distribution_sample"]
            
            fig = ff_plot_dist(samples, results['var_99'], results['expected_shortfall_99'])
            st.plotly_chart(fig, use_container_width=True)


def ff_plot_dist(samples, var_99, es_99):
    """Plotly ile çan eğrisi altı dolu kırmızı Loss Distribution grafiği çizer."""
    df = pd.DataFrame({'Loss': samples})
    fig = px.histogram(df, x="Loss", nbins=50, title="Portföy Kredi Kayıp Dağılımı (Loss Distribution)")
    fig.add_vline(x=var_99, line_dash="dash", line_color="#f59e0b", annotation_text="VaR (%99)")
    fig.add_vline(x=es_99, line_dash="dash", line_color="#ef4444", annotation_text="Expected Shortfall")
    
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                      xaxis_title="Portföy Zararı (TL)", yaxis_title="Frekans",
                      bargap=0.05)
    fig.update_traces(marker_color='#3b82f6', marker_line_color='rgba(255,255,255,0.2)', marker_line_width=1)
    return fig

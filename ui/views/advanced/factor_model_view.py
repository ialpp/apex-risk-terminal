"""
ui/views/advanced/factor_model_view.py — ProQuant Capital | Çok Faktörlü Model & Fama-French v7.0
===================================================================================================
Fama-French 5/6 Faktör modelini görselleştiren, varlıkların faktör maruziyetlerini (betalarını)
ve getiri atıflarını sunan Streamlit dashboard'u.
Author: ProQuant Capital Factor Engine UX | Version: 7.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def render_factor_model_view():
    st.header("🧬 Fama-French & Çok Faktörlü Alfa Analizi", divider="violet")

    with st.sidebar:
        st.subheader("⚙️ Portföy Seçimi")
        asset_list = st.multiselect("Varlıklar", ["AAPL", "MSFT", "GOOGL", "JPM", "XOM"], default=["AAPL", "JPM"])
        weights = {}
        for a in asset_list:
            weights[a] = st.slider(f"{a} Ağırlığı (%)", 0.0, 100.0, 100.0 / len(asset_list)) / 100.0

    if not asset_list:
        st.warning("Lütfen sidebar'dan varlık seçin.")
        return

    from modules.factor_model_engine import get_factor_model_engine
    eng = get_factor_model_engine()

    # Mock varlık getirileri
    np.random.seed(42)
    sample_returns = {a: np.random.normal(0.0005, 0.015, 252) for a in asset_list}

    # Bireysel Faktör Maruziyetleri
    st.subheader("📊 Bireysel Faktör Beta (Maruziyet) Matrisi")
    exposures = []
    for a in asset_list:
        exp = eng.reg.estimate_exposures(sample_returns[a], a)
        exposures.append(exp.__dict__)
    
    exp_df = pd.DataFrame(exposures)
    cols = ["symbol", "alpha", "beta_mkt", "beta_smb", "beta_hml", "beta_rmw", "beta_cma", "beta_mom", "r_squared"]
    st.dataframe(exp_df[cols].style.format({
        "alpha": "{:.6f}", "beta_mkt": "{:.3f}", "beta_smb": "{:.3f}", "beta_hml": "{:.3f}",
        "beta_rmw": "{:.3f}", "beta_cma": "{:.3f}", "beta_mom": "{:.3f}", "r_squared": "{:.4f}"
    }).background_gradient(cmap='RdBu', subset=["beta_mkt", "beta_smb", "beta_hml", "beta_rmw", "beta_cma", "beta_mom"]), use_container_width=True)

    # Portföy Getiri Atfı (Attribution)
    st.divider()
    st.subheader("🍰 Portföy Getiri Kaynakları (Attribution)")
    
    # Normalize weights
    total_w = sum(weights.values())
    w_norm = {k: v/total_w for k,v in weights.items()}
    attr = eng.decompose_portfolio_return(w_norm, sample_returns)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Yıllık Alfa (α)", f"%{attr['portfolio_alpha_annual']*100:.2f}")
    with c2: st.metric("Günlük Alfa", f"%{attr['portfolio_alpha_daily']*100:.4f}")
    with c3: st.metric("Baskın Faktör Risk", attr['dominant_factor'])

    # Bar chart
    factors = attr["factor_exposures"]
    fig = px.bar(
        x=list(factors.keys()), y=list(factors.values()),
        labels={'x': 'Faktör', 'y': 'Portföy Maruziyeti (Beta)'},
        color=list(factors.values()), color_continuous_scale="RdBu",
        title="Agrega Portföy Faktör Betaları"
    )
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.info("""
    **Faktör Açıklamaları:** 
    `MKT`: Piyasa Riski | `SMB`: Küçük Şirket Primi | `HML`: Değer (Value) Primi | 
    `RMW`: Karlılık Primi | `CMA`: Muhafazakar Yatırım | `MOM`: Momentum
    """)

if __name__ == "__main__":
    render_factor_model_view()

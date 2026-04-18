"""
ui/views/optimizer_view.py — ProQuant Capital | Portföy Optimizasyon Dashboard v6.0
===================================================================================

`PortfolioOptimizerPro` tarafından üretilen varlık tahsisi (Asset Allocation) 
stratejilerini görselleştiren ve analiz eden Streamlit arayüz modülü.
Bu sayfa, farklı modern portföy teorisi modellerinin (MVO, Risk Parity, BL)
karşılaştırmalı analizini sunar.

Görsel Bileşenler:
  1. Efficient Frontier Plot: Risk-getiri bazlı etkin sınır ve seçili portföyler.
  2. Allocation Pie Charts: Model bazlı varlık dağılımlarının karşılaştırması.
  3. Risk Contribution Bar Chart: Her varlığın portföy riskine olan katkısı.
  4. Optimization Metrics Table: Sharpe, Volatilite, Expected Return karşılaştırması.

Interaktivite:
  - Sembol havuzu seçimi (Universe selection).
  - Risk iştahı (Risk Aversion) kaydırıcısı.
  - Black-Litterman uzman görüşü (View) ekleme arayüzü.
  - Kısıt (Constraint) yönetimi: Long-only, Max weight vb.

Author  : ProQuant Capital Portfolio UX Design
Version : 6.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
from datetime import datetime
from typing import List, Tuple, Dict

# ProQuant Modülleri
from modules.portfolio_optimizer_pro import get_portfolio_optimizer

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: GÖRSELLEŞTİRME YARDIMCILARI
# ─────────────────────────────────────────────────────────────────────────────

def plot_efficient_frontier(frontier_points: List[Tuple[float, float]], selected: Dict[str, Tuple[float, float]]):
    """Etkin sınırı ve seçili strateji noktalarını çizer."""
    fig = go.Figure()
    
    # Frontier Line
    vols, rets = zip(*frontier_points)
    fig.add_trace(go.Scatter(x=vols, y=rets, mode='lines', name='Efficient Frontier', line=dict(color='#3b82f6', width=2)))
    
    # Selected Points (Max Sharpe, Min Vol etc)
    colors = ["#ef4444", "#22c55e", "#f59e0b"]
    for i, (name, coord) in enumerate(selected.items()):
        fig.add_trace(go.Scatter(
            x=[coord[0]], y=[coord[1]], 
            mode='markers+text', name=name,
            text=[name], textposition="top center",
            marker=dict(size=12, color=colors[i % 3], symbol='star')
        ))
        
    fig.update_layout(title="Modern Portföy Teorisi - Etkin Sınır", template="plotly_dark", xaxis_title="Yıllık Volatilite (%)", yaxis_title="Yıllık Beklenen Getiri (%)")
    return fig

def plot_allocation_pies(allocations: Dict[str, Dict[str, float]]):
    """Farklı model ağırlıklarını yan yana Pie Chart olarak gösterir."""
    # Streamlit tablarından daha iyi bir karşılaştırma için
    cols = st.columns(len(allocations))
    for i, (name, weights) in enumerate(allocations.items()):
        with cols[i]:
            fig = px.pie(values=list(weights.values()), names=list(weights.keys()), title=name, hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(template="plotly_dark", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: VIEW RENDERING (EKRAN ÇIKTISI)
# ─────────────────────────────────────────────────────────────────────────────

def render_optimizer_view():
    """Portföy optimizasyon sayfasını oluşturur."""
    st.header("⚖️ Portföy Optimizasyon & Strateji Paneli", divider="blue")
    
    # Sidebar: Universe & Constraints
    with st.sidebar:
        st.subheader("🛠️ Optimizasyon Ayarları")
        universe = st.multiselect("Varlık Havuzu", ["AAPL", "MSFT", "GOOGL", "AMZN", "BTC", "GOLD", "SPY"], default=["AAPL", "MSFT", "GOLD"])
        risk_aversion = st.slider("Risk İştahı (λ)", 1.0, 10.0, 3.0)
        
        st.divider()
        st.subheader("📐 Kısıtlar (Constraints)")
        st.checkbox("Long Only", value=True)
        st.slider("Max Varlık Ağırlığı", 0.05, 1.0, 0.40)
        
    # Başlangıç Analizi (Mock Data Simulation)
    n = len(universe) if universe else 3
    symbols = universe if universe else ["V1", "V2", "V3"]
    
    # 1. Grafik Alanı: Frontier
    frontier_data = [(0.1 + i*0.01, 0.05 + i*0.02) for i in range(20)]
    selected_points = {
        "Max Sharpe": (0.15, 0.18),
        "Min Volatility": (0.10, 0.06),
        "Risk Parity": (0.12, 0.10)
    }
    st.plotly_chart(plot_efficient_frontier(frontier_data, selected_points), use_container_width=True)

    # 2. Ağırlık Karşılaştırmaları
    st.subheader("🍕 Model bazlı Varlık Dağılımı (Weights)")
    mock_allocs = {
        "Max Sharpe": {s: random.random() for s in symbols},
        "Min Volatility": {s: random.random() for s in symbols},
        "Risk Parity": {s: 1.0/n for s in symbols}
    }
    # Normalizasyon
    for k in mock_allocs:
        total = sum(mock_allocs[k].values())
        mock_allocs[k] = {s: v/total for s, v in mock_allocs[k].items()}
        
    plot_allocation_pies(mock_allocs)

    # 3. Black-Litterman Views
    with st.expander("🔮 Black-Litterman Uzman Görüşleri (Subjective Views)"):
        col_bl1, col_bl2 = st.columns([2, 1])
        with col_bl1:
            st.info("💡 Burada belirli varlıklar için piyasa beklentinizi girebilirsiniz.")
            st.text_input("Görüş", placeholder="Örn: AAPL, SPY'dan %5 daha fazla getiri sağlayacaktır.")
        with col_bl2:
            st.slider("Güven Seviyesi (%)", 0, 100, 50)
            st.button("Görüşü Modele Ekle")

    # Sonuç Tablosu
    st.subheader("📋 Optimizasyon Sonuçları")
    results_df = pd.DataFrame({
        "Strateji": ["Max Sharpe", "Min Volatility", "Risk Parity"],
        "Beklenen Getiri (%)": ["%18.2", "%6.4", "%10.5"],
        "Volatilite (%)": ["%15.4", "%9.8", "%12.2"],
        "Sharpe Rasyosu": ["1.18", "0.65", "0.86"],
        "Max Drawdown (%)": ["-%14.2", "-%6.5", "-%9.0"]
    })
    st.table(results_df)

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    render_optimizer_view()

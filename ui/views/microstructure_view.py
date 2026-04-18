import time
"""
ui/views/microstructure_view.py — ProQuant Capital | Piyasa Mikro Yapı Görselleştirme v6.0
========================================================================================

Piyasa mikro yapısı, likidite dinamikleri ve emir akışı zekasını (Order Flow)
görselleştiren gelişmiş analiz sayfası. `MicrostructureEngine` çıktılarının
gerçek zamanlı (veya simüle) takibini sağlar.

Görsel Bileşenler:
  1. Order Book Depth Chart: Bid/Ask hacimlerinin fiyat seviyelerine göre dağılımı.
  2. Order Imbalance Trend: Alış/satış baskısının zaman içindeki değişimi.
  3. VPIN Toxicity Indicator: Piyasa toksisitesinin kritik eşik takibi.
  4. Bid-Ask Spread Analytics: Spread genişliğinin işlem maliyeti üzerindeki etkisi.
  5. Micro-Price vs Mid-Price: Fiyat yönü değişimleri için öncü gösterge takibi.

Interaktivite:
  - Ticket bazlı derinlik seviyesi (L1, L2, L3) seçimi.
  - VPIN pencere büyüklüğü ayarı.
  - Likidite şoku (Liquidity Shock) uyarı limitleri.

Author  : ProQuant Capital HFT UX Design
Version : 6.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import random
from datetime import datetime, timedelta
from typing import List, Dict

# ProQuant Modülleri
from modules.microstructure_engine import get_microstructure_engine

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: GÖRSELLEŞTİRME YARDIMCILARI (PLOTTERS)
# ─────────────────────────────────────────────────────────────────────────────

def plot_order_book_depth(bids: List[Dict], asks: List[Dict]):
    """Sipariş defteri derinliğini (Depth Chart) çizer."""
    fig = go.Figure()
    
    # Bids (Yeşil)
    fig.add_trace(go.Scatter(
        x=[b['price'] for b in bids], 
        y=[b['volume'] for b in bids],
        fill='tozeroy', mode='lines', name='Bids (Buy)', line_color='#22c55e'
    ))
    
    # Asks (Kırmızı)
    fig.add_trace(go.Scatter(
        x=[a['price'] for a in asks], 
        y=[a['volume'] for a in asks],
        fill='tozeroy', mode='lines', name='Asks (Sell)', line_color='#ef4444'
    ))
    
    fig.update_layout(title="Limit Order Book Depth", template="plotly_dark", height=400, xaxis_title="Fiyat", yaxis_title="Hacim")
    return fig

def plot_vpin_toxic_meter(vpin_value: float):
    """VPIN Toksisite göstergesini (Gauge) çizer."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = vpin_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "VPIN Market Toxicity Score", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [0, 1], 'tickwidth': 1},
            'bar': {'color': "#3b82f6"},
            'steps': [
                {'range': [0, 0.4], 'color': "green"},
                {'range': [0.4, 0.7], 'color': "yellow"},
                {'range': [0.7, 1.0], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 0.8
            }
        }
    ))
    fig.update_layout(template="plotly_dark", height=300)
    return fig

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: VIEW RENDERING (EKRAN ÇIKTISI)
# ─────────────────────────────────────────────────────────────────────────────

def render_microstructure_view():
    """Mikro-yapı sayfasını oluşturur."""
    st.header("🔬 Piyasa Mikro Yapı & Likidite Paneli", divider="blue")
    
    # Üst Bölüm: Canlı Metrikler
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Quoted Spread", "2.5 bps", "-0.2")
    with c2: st.metric("Order Imbalance", "%18.4", "BUY Pressure")
    with c3: st.metric("Amihud Liquidity", "0.0042", help="Yüksek değer = Düşük Likidite")
    with c4: st.metric("Tick Velocity", "145 t/sec")

    # Ana Alan: Defter ve Toksisite
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Mock LOB Verisi
        mid = 150.0
        bids = [{"price": mid - i*0.1, "volume": random.randint(100, 1000)} for i in range(1, 20)]
        asks = [{"price": mid + i*0.1, "volume": random.randint(100, 1000)} for i in range(1, 20)]
        st.plotly_chart(plot_order_book_depth(bids, asks), use_container_width=True)
        
        # Imbalance Grafik
        st.subheader("📊 Order Imbalance Trend")
        times = [datetime.now() - timedelta(minutes=i) for i in range(60)][::-1]
        imbalance_vals = np.sin(np.linspace(0, 10, 60)) * 0.5 + np.random.normal(0, 0.1, 60)
        st.line_chart(pd.DataFrame({"Imbalance": imbalance_vals}, index=times))

    with col_right:
        st.plotly_chart(plot_vpin_toxic_meter(0.55), use_container_width=True)
        
        st.subheader("🛡️ Risk Uyarıları")
        vpin_val = 0.55
        if vpin_val > 0.7:
            st.error("🚨 KRİTİK: Yüksek Piyasa Toksisitesi! Informed Trading baskısı artıyor.")
        elif vpin_val > 0.5:
            st.warning("⚠️ DİKKAT: Likidite daralması riski gözlemleniyor.")
        else:
            st.success("✅ Piyasa likiditesi sağlıklı seviyelerde.")

        with st.expander("📚 Metrik Açıklamaları"):
            st.write("""
            - **VPIN:** Informed trading olasılığını ölçer. Ani çöküşlerin habercisidir.
            - **Imbalance:** Defterdeki alış ve satış emirleri arasındaki oransal farktır.
            - **Spread:** En iyi alış ve satış fiyatları arasındaki farktır.
            """)

    # İşlem Akışı (Tick Stream)
    st.subheader("⚡ Gerçek Zamanlı Emir Akışı (Tick Feed)")
    ticks = pd.DataFrame([
        {"Zaman": (datetime.now() - timedelta(seconds=i)).strftime("%H:%M:%S"), 
         "Fiyat": 150.0 + random.uniform(-0.5, 0.5), 
         "Miktar": random.randint(1, 500), 
         "Yön": random.choice(["BUY", "SELL"])} 
        for i in range(20)
    ])
    st.table(ticks)

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    render_microstructure_view()

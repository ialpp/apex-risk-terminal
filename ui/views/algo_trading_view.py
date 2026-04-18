"""
ui/views/algo_trading_view.py — ProQuant Capital | Algoritmik Trading Dashboard v2.0
===================================================================================

Bu modül, algo_paper_trading.py motorunun arayüzünü sağlar.
Kullanıcılara canlı simülasyon, strateji performans analizi ve portföy takibi sunar.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time

def render_algo_trading_view(trading_bot, user_info):
    st.title("🤖 Algoritmik Paper Trading Dashboard")
    st.markdown("<p style='color:#64748b;'>Gerçek zamanlı emir defteri (LOB) simülasyonu ve strateji performans takibi.</p>",
                unsafe_allow_html=True)

    # Sidebar / Kontrol Paneli
    with st.sidebar:
        st.header("⚙️ Bot Ayarları")
        symbol = st.selectbox("Enstrüman Seçin", ["BTC/USDT", "ETH/USDT", "XAU/USD", "EUR/USD", "AAPL"])
        st.divider()
        strategy_name = st.selectbox("Aktif Strateji", ["RSI_Mean_Reversion", "EMA_Crossover", "Bollinger_Breakout", "ML_Trend_Follower"])
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ Botu Başlat", type="primary", use_container_width=True):
                st.session_state.trading_active = True
                st.toast("Algo Bot Başlatıldı!")
        with c2:
            if st.button("⏹️ Durdur", use_container_width=True):
                st.session_state.trading_active = False
                st.toast("Algo Bot Durduruldu.")

    # 1. Özet Metrikler
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Net Likidite", "$104,250.00", "+$4,250.00")
    with m2:
        st.metric("Açık Pozisyonlar", "3", "Long")
    with m3:
        st.metric("Günlük Kâr/Zarar", "$840.12", "+%0.81")
    with m4:
        st.metric("Sharpe Oranı", "2.14", "Kurumsal Seviye")

    st.divider()

    # 2. Canlı Emir Defteri (LOB) ve Fiyat Grafiği
    col_chart, col_lob = st.columns([2, 1])

    with col_chart:
        st.subheader("📈 Fiyat Aksiyonu & Sinyaller")
        # Simüle edilmiş fiyat verisi
        dates = pd.date_range(end=datetime.datetime.now(), periods=100, freq='H')
        prices = np.cumsum(np.random.normal(0, 5, 100)) + 1000
        df = pd.DataFrame({'Date': dates, 'Price': prices})
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Price'], mode='lines', name='Price',
                                 line=dict(color='#38bdf8', width=2)))
        
        # Sinyaller ekle
        buy_signals = df.sample(5)
        fig.add_trace(go.Scatter(x=buy_signals['Date'], y=buy_signals['Price'], mode='markers',
                                 name='Buy Signal', marker=dict(symbol='triangle-up', size=12, color='#10b981')))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=400,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_lob:
        st.subheader("📑 LOB Simulation")
        # Emir defteri simülasyonu
        bid_prices = np.sort(np.random.normal(1000, 2, 8))[::-1]
        ask_prices = np.sort(np.random.normal(1004, 2, 8))
        bid_sizes = np.random.uniform(0.1, 5, 8)
        ask_sizes = np.random.uniform(0.1, 5, 8)

        st.markdown("""
        <style>
        .lob-table { width:100%; border-collapse:collapse; font-family:monospace; font-size:0.8rem; }
        .lob-bid { color:#10b981; text-align:right; }
        .lob-ask { color:#ef4444; text-align:left; }
        .lob-size { color:#94a3b8; text-align:center; }
        </style>
        """, unsafe_allow_html=True)
        
        lob_html = "<table class='lob-table'><tr><th>Size</th><th>Bid</th><th>Ask</th><th>Size</th></tr>"
        for i in range(8):
            lob_html += f"<tr><td class='lob-size'>{bid_sizes[i]:.2f}</td><td class='lob-bid'>{bid_prices[i]:.2f}</td>"
            lob_html += f"<td class='lob-ask'>{ask_prices[i]:.2f}</td><td class='lob-size'>{ask_sizes[i]:.2f}</td></tr>"
        lob_html += "</table>"
        st.markdown(lob_html, unsafe_allow_html=True)
        
        spread = ask_prices[0] - bid_prices[0]
        st.info(f"Anlık Spread: **{spread:.2f}**")

    st.divider()

    # 3. Portföy ve İşlem Detayı
    tab_pos, tab_his, tab_risk = st.tabs(["💼 Açık Pozisyonlar", "📜 İşlem Geçmişi", "🛡️ Risk Yönetimi"])

    with tab_pos:
        st.dataframe(pd.DataFrame([
            {"Symbol": "BTC/USDT", "Type": "Long", "Qty": 0.5, "Entry": 65000, "Mark": 65250, "PnL": "+$125.00", "PnL%": "+0.38%"},
            {"Symbol": "ETH/USDT", "Type": "Short", "Qty": 2.0, "Entry": 3500, "Mark": 3480, "PnL": "+$40.00", "PnL%": "+0.57%"},
            {"Symbol": "XAU/USD", "Type": "Long", "Qty": 10, "Entry": 2350, "Mark": 2345, "PnL": "-$50.00", "PnL%": "-0.21%"},
        ]), use_container_width=True)

    with tab_his:
        st.write("Son 24 saatteki işlemler...")
        st.dataframe(pd.DataFrame([
            {"Time": "14:20:05", "Symbol": "BTC/USDT", "Side": "Buy", "Price": 65200, "Size": 0.1, "Status": "Filled"},
            {"Time": "12:15:22", "Symbol": "ETH/USDT", "Side": "Sell", "Price": 3510, "Size": 0.5, "Status": "Filled"},
            {"Time": "09:05:41", "Symbol": "SOL/USDT", "Side": "Buy", "Price": 145.2, "Size": 10, "Status": "Filled"},
        ]), use_container_width=True)

    with tab_risk:
        st.subheader("Otonom Risk Limiti Kontrolleri")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.slider("Max Drawdown Stop", 1.0, 15.0, 5.0, format="%%%.1f")
        with c2:
            st.slider("Max Leverage", 1.0, 50.0, 10.0, format="x%.1f")
        with c3:
            st.slider("Position Sizing (Kelly %)", 0.0, 1.0, 0.4)
        
        st.button("Risk Parametrelerini Güncelle", use_container_width=True)

    # Bot durumuna göre loop simülasyonu
    if st.session_state.get("trading_active", False):
        st.empty()
        # Not: Streamlit'te gerçek loop için fragment veya placeholder kullanılır.
        # Burada sadece statik gösteriyoruz fakat logic algo_paper_trading.py'de bağlı.

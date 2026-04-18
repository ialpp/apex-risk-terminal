"""
ui/views/advanced/pairs_trading_view.py — ProQuant Capital | Pairs Trading Dashboard v7.0
===========================================================================================
İstatistiksel arbitraj çiftlerini, Z-score sinyallerini ve açık pozisyonları
görselleştiren profesyonel pairs trading arayüzü.
Author: ProQuant Capital HFT UX | Version: 7.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime


def render_pairs_trading_view():
    st.header("🔄 İstatistiksel Arbitraj & Pairs Trading", divider="green")

    col_cfg, col_main = st.columns([1, 3])

    with col_cfg:
        st.subheader("⚙️ Çift Seçimi")
        leg1 = st.selectbox("Varlık 1 (Y)", ["AAPL","GOOGL","MSFT","AMZN"], index=0)
        leg2 = st.selectbox("Varlık 2 (X)", ["MSFT","META","TSLA","NVDA"], index=0)
        lookback= st.slider("Lookback (gün)", 30, 252, 60)
        entry_z = st.slider("Entry Z-Score", 1.0, 3.5, 2.0, 0.1)
        exit_z  = st.slider("Exit Z-Score", 0.1, 1.5, 0.5, 0.1)

    with col_main:
        from modules.pairs_trading_engine import CointegrationAnalyzer, ZScoreSignalGenerator
        np.random.seed(42)
        n     = lookback + 50
        x_p   = np.cumsum(np.random.normal(0.001, 0.015, n)) + 150
        y_p   = 1.8 * x_p + 10 + np.random.normal(0, 2, n)

        # Eşbütünleşim testi
        analyzer = CointegrationAnalyzer()
        result   = analyzer.test_cointegration(y_p, x_p, leg1, leg2)

        # Metrikler
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            color = "normal" if result.is_cointegrated else "inverse"
            st.metric("Eşbütünleşim", "✅ Evet" if result.is_cointegrated else "❌ Hayır")
        with m2: st.metric("p-değeri", f"{result.p_value:.4f}")
        with m3: st.metric("Hedge Rasyosu (β)", f"{result.hedge_ratio:.3f}")
        with m4: st.metric("Yarı Ömür", f"{result.half_life_days:.1f} gün")

        st.divider()

        # Spread ve Z-score grafikleri
        hedge  = result.hedge_ratio
        spread = y_p - hedge * x_p
        spread_sr = pd.Series(spread)
        z_scores  = (spread_sr - spread_sr.rolling(lookback).mean()) / spread_sr.rolling(lookback).std()

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=spread, name="Spread", line=dict(color="#3b82f6")))
        fig.add_hline(y=spread_sr.mean(), line_dash="dash", line_color="white", annotation_text="Ortalama")
        fig.update_layout(title=f"{leg1}-{leg2} Spread", template="plotly_dark", height=280)
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(y=z_scores.dropna(), name="Z-Score", line=dict(color="#f59e0b")))
        fig2.add_hline(y=entry_z,  line_color="#ef4444", line_dash="dash", annotation_text=f"+{entry_z}σ Entry")
        fig2.add_hline(y=-entry_z, line_color="#22c55e", line_dash="dash", annotation_text=f"-{entry_z}σ Entry")
        fig2.add_hline(y=0, line_color="white", line_dash="dot")
        fig2.update_layout(title="Z-Score & Giriş Seviyeleri", template="plotly_dark", height=280)
        st.plotly_chart(fig2, use_container_width=True)

        # Sinyal Üretimi
        gen = ZScoreSignalGenerator(entry_z=entry_z, exit_z=exit_z, lookback=lookback)
        for s in spread[-lookback:]:
            last_sig = gen.add_spread(float(s))

        sig_color = {"LONG_SPREAD": "🟢", "SHORT_SPREAD": "🔴", "HOLD": "🟡", "EXIT": "⚪"}
        current_z = gen.current_zscore
        st.info(f"**Güncel Sinyal:** {sig_color.get(last_sig.value, '❓')} `{last_sig.value}` "
                f"| Z-Score: `{current_z:.3f}` | Spread σ: `{result.spread_std:.4f}`")

    with st.expander("📝 Strateji Notları"):
        st.write("""
        - **Long Spread**: Y al, X sat → Spread'in ortalamasına dönmesini bekle.
        - **Short Spread**: Y sat, X al → Spread'in düşmesini bekle.
        - Yarı ömür **< 20 gün** olan çiftler daha aktif alım satım için uygundur.
        - **p < 0.05** kritik eşiği eşbütünleşim için zorunlu koşuldur.
        """)

if __name__ == "__main__":
    render_pairs_trading_view()

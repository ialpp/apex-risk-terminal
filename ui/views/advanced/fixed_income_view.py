"""
ui/views/advanced/fixed_income_view.py — ProQuant Capital | Sabit Getirili Ürünler Dashboard v7.0
===================================================================================================

Tahvil fiyatlama, getiri eğrisi ve kredi spread analizlerini görselleştiren
kurumsal sabit getirili menkul kıymet dashboard'u.

Author: ProQuant Capital Fixed Income UX | Version: 7.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def render_fixed_income_view():
    st.header("📉 Sabit Getirili Ürünler & Tahvil Analizi", divider="blue")

    with st.sidebar:
        st.subheader("⚙️ Tahvil Parametreleri")
        face_val   = st.number_input("Nominal Değer ($)", 100.0, 100000.0, 1000.0)
        coupon_pct = st.slider("Kupon Oranı (%)", 0.0, 15.0, 5.0, 0.25) / 100
        maturity   = st.slider("Vade (Yıl)", 1, 30, 5)
        mkt_price  = st.number_input("Piyasa Fiyatı ($)", 100.0, 2000.0, 980.0)

    # Analiz
    from modules.fixed_income_engine import get_fixed_income_engine
    fi = get_fixed_income_engine()
    result = fi.analyze_bond("USER_BOND", coupon_pct, maturity, mkt_price, face_val)

    # Üst Metrik Kartları
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("YTM (%)", f"{result['ytm_pct']:.3f}")
    with c2: st.metric("Mod. Duration", f"{result['modified_duration']:.2f} yıl")
    with c3: st.metric("Convexity", f"{result['convexity']:.4f}")
    with c4: st.metric("DV01 ($)", f"{result['dv01_usd']:.2f}")

    st.divider()

    # Getiri Eğrisi
    st.subheader("📈 Nelson-Siegel-Svensson Getiri Eğrisi")
    curve = fi.get_yield_curve()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=curve["maturities_yr"], y=[y*100 for y in curve["yields"]],
        mode="lines+markers", name="Spot Yield Curve",
        line=dict(color="#3b82f6", width=2.5)
    ))
    fig.update_layout(
        template="plotly_dark", height=380,
        xaxis_title="Vade (Yıl)", yaxis_title="Getiri (%)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Fiyat-Getiri İlişkisi
    st.subheader("🔄 Fiyat / Getiri İlişkisi (Convexity Etkisi)")
    from modules.fixed_income_engine import Bond, BondPricer
    bond   = Bond("PY_BOND", face_val, coupon_pct, maturity)
    pricer = BondPricer()
    ytm_range = np.linspace(0.01, 0.15, 80)
    prices    = [pricer.price_from_ytm(bond, y) for y in ytm_range]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=ytm_range*100, y=prices,
        mode="lines", name="Bond Price", line=dict(color="#22c55e", width=2)))
    fig2.add_vline(x=result["ytm_pct"], line_dash="dash",
                   line_color="#ef4444", annotation_text=f"YTM: {result['ytm_pct']:.2f}%")
    fig2.update_layout(template="plotly_dark", height=350,
        xaxis_title="YTM (%)", yaxis_title="Fiyat ($)")
    st.plotly_chart(fig2, use_container_width=True)

    # Risk Özeti
    with st.expander("📋 Risk Özeti & Yorumlama"):
        st.write(f"""
        - **Duration {result['modified_duration']:.2f} yıl**: Faiz %1 artarsa fiyat yaklaşık
          **%{result['modified_duration']:.2f}** düşer.
        - **DV01 ${result['dv01_usd']:.2f}**: Faiz 1 baz puan değişince ${result['dv01_usd']:.2f} değer değişimi olur.
        - **Convexity {result['convexity']:.4f}**: Yüksek convexity, büyük faiz
          dalgalanmalarında tahvili avantajlı kılar.
        """)

if __name__ == "__main__":
    render_fixed_income_view()

"""
ui/views/advanced/macro_regime_view.py — ProQuant Capital | Makro Ekonomi & Rejim Bağlantı Motoru v7.0
========================================================================================================
NBER resesyon indikatörü, Taylor Kuralı tahmini ve piyasa rejimine bağlı
varlık tahsis sinyallerini görselleştiren dashboard.
Author: ProQuant Capital Macro Engine UX | Version: 7.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def render_macro_regime_view():
    st.header("🌍 Makroekonomik Rejim & Varlık Tahsisi (NBER & Taylor Rule)", divider="red")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📊 Güncel Makro Veriler")
        gdp   = st.number_input("GDP Büyümesi (YoY %)", -5.0, 10.0, 2.5)
        cpi   = st.number_input("TÜFE Enflasyonu (YoY %)", -2.0, 15.0, 3.1)
        unem  = st.number_input("İşsizlik Oranı (%)", 1.0, 20.0, 4.0)
        pmi   = st.number_input("Makro PMI", 20.0, 80.0, 52.0)
        y10   = st.number_input("10Y Tahvil Getirisi (%)", -1.0, 15.0, 4.2)
        y2    = st.number_input("2Y Tahvil Getirisi (%)", -1.0, 15.0, 4.0)
        vix   = st.number_input("VIX Volatilite Endeksi", 5.0, 100.0, 18.0)
        policy= st.number_input("Mevcut Politika Faizi (%)", 0.0, 15.0, 5.25)

    with c2:
        from modules.macro_regime_engine import get_macro_regime_engine
        eng = get_macro_regime_engine()
        res = eng.generate_macro_report(gdp, cpi, unem, policy, pmi, y10, y2, vix)

        st.subheader("🔮 Makro Görünüm Raporu")
        m1, m2, m3 = st.columns(3)
        with m1: 
            st.metric("Tespit Edilen Rejim", res["regime"])
            st.metric("Rejim Güveni", f"%{res['confidence']*100:.1f}")
        with m2: 
            st.metric("Resesyon Olasılığı", f"%{res['recession_probability']*100:.1f}")
            st.metric("Getiri Eğrisi", res["yield_curve"])
        with m3: 
            st.metric("Taylor Hedef Faizi", f"%{res['taylor_recommendation']:.2f}")
            st.metric("Para Politikası Bias", res["policy_bias"])

        st.divider()
        st.subheader("💼 Rejim Bazlı Varlık Getiri Beklentileri")
        rec = res["asset_recommendations"]
        # OW: Overweight, UW: Underweight, N: Neutral
        color_map = {"OW": "#22c55e", "UW": "#ef4444", "N": "#64748b"}
        
        cols = st.columns(len(rec))
        for idx, (asset, signal) in enumerate(rec.items()):
            with cols[idx]:
                st.markdown(f"""
                <div style='background-color:{color_map[signal]}; padding:10px; border-radius:5px; text-align:center;'>
                    <b>{asset}</b><br>{signal}
                </div>
                """, unsafe_allow_html=True)
                
        st.info("📌 **Varlık Sinyalleri:** `OW`: Ağırlığı Artır (Overweight) | `UW`: Ağırlığı Azalt (Underweight) | `N`: Nötr (Neutral)")

        # Basit gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = res['recession_probability'] * 100,
            title = {'text': "Implied Recession Risk"},
            gauge = {'axis': {'range': [0, 100]},
                     'bar': {'color': "red"},
                     'steps': [
                         {'range': [0, 30], 'color': "green"},
                         {'range': [30, 70], 'color': "orange"},
                         {'range': [70, 100], 'color': "gray"}],
                     }
        ))
        fig.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render_macro_regime_view()

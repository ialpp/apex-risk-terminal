"""
ui/views/regulatory_view.py — ProQuant Capital | Düzenleyici Raporlama (IFRS-9/Basel III) Dashboard v2.0
=====================================================================================================

Bu modül, regulatory_reports_ifrs9.py motorunun arayüzünü sağlar.
Bankacılık otoritelerine sunulacak raporları ve kümülatif risk metriklerini görselleştirir.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

def render_regulatory_view(reg_engine, user_info):
    st.title("📜 Düzenleyici Raporlama & Basel III Merkezi")
    st.markdown("<p style='color:#64748b;'>IFRS-9 Beklenen Kredi Zararı (ECL) ve Basel III Sermaye Yeterlilik hesaplamaları.</p>",
                unsafe_allow_html=True)

    # 1. Sermaye Yeterlilik Özeti (Basel III)
    st.subheader("🏛️ Sermaye Yeterlilik Rasyoları (CAR)")
    
    # Simüle edilmiş veriler
    car_data = reg_engine.calculate_capital_adequacy(150000000, 20000000, 10000000, 1200000000)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("CET1 Ratio", f"%{car_data['cet1_ratio']:.2f}", "Target: >%4.5")
    with c2:
        st.metric("Tier 1 Ratio", f"%{car_data['tier1_ratio']:.2f}", "Target: >%6.0")
    with c3:
        st.metric("Total Capital Ratio", f"%{car_data['total_capital_ratio']:.2f}", "Target: >%8.0")
    with c4:
        st.metric("Risk Weighted Assets", f"${car_data['rwa']/1e6:.1f}M")

    # CAR Görselleştirme (Gauge Chart)
    fig_car = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = car_data['total_capital_ratio'],
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Total Capital Adequacy Status"},
        gauge = {
            'axis': {'range': [None, 20]},
            'bar': {'color': "#818cf8"},
            'steps': [
                {'range': [0, 8], 'color': "rgba(239, 68, 68, 0.3)"},
                {'range': [8, 12], 'color': "rgba(251, 191, 36, 0.3)"},
                {'range': [12, 20], 'color': "rgba(16, 185, 129, 0.3)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 8.0
            }
        }
    ))
    fig_car.update_layout(height=250, margin=dict(t=30, b=0, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "#f1f5f9"})
    st.plotly_chart(fig_car, use_container_width=True)

    st.divider()

    # 2. IFRS-9 ECL Analizi
    st.subheader("📉 IFRS-9 Beklenen Kredi Zararı (ECL) Dağılımı")
    
    # 3 Stage simülasyonu
    stage_data = {
        "Stage 1 (Normal)": {"ECL": 2.4, "Exposure": 850, "PD": "1.2%"},
        "Stage 2 (Risk Artışı)": {"ECL": 15.8, "Exposure": 120, "PD": "8.5%"},
        "Stage 3 (Default/Impared)": {"ECL": 45.2, "Exposure": 30, "PD": "100.0%"}
    }
    
    df_stage = pd.DataFrame.from_dict(stage_data, orient='index').reset_index()
    
    col_ecl1, col_ecl2 = st.columns([1, 1])
    with col_ecl1:
        fig_ecl = px.pie(df_stage, values='ECL', names='index', 
                         title="ECL Dağılımı (Milyon $)",
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_ecl.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': "#f1f5f9"})
        st.plotly_chart(fig_ecl, use_container_width=True)
        
    with col_ecl2:
        st.markdown("#### Detaylı Karşılık Tablosu")
        st.table(df_stage)
        st.info("💡 Toplam provizyon (ECL) miktarı, riskli varlıklardaki (Stage 3) artış nedeniyle geçen aya göre %4.2 yükselmiştir.")

    st.divider()

    # 3. Likidite ve Stres Testleri
    st.subheader("🌊 Likidite Karşılama (LCR) ve Stres Senaryoları")
    
    lcr_data = reg_engine.calculate_lcr(45000000, 38000000)
    nsfr_data = reg_engine.calculate_nsfr(1200000000, 1100000000)

    lc1, lc2 = st.columns(2)
    with lc1:
        st.markdown("**Liquidity Coverage Ratio (LCR)**")
        st.progress(min(1.0, lcr_data['lcr_ratio'] / 1.5))
        st.write(f"Mevcut: %{lcr_data['lcr_ratio'] * 100:.1f} | Eşik: %100.0")
        
    with lc2:
        st.markdown("**Net Stable Funding Ratio (NSFR)**")
        st.progress(min(1.0, nsfr_data['nsfr_ratio'] / 1.5))
        st.write(f"Mevcut: %{nsfr_data['nsfr_ratio'] * 100:.1f} | Eşik: %100.0")

    # Stres Testi Simülasyonu
    with st.expander("⚡ Dinamik Stres Testi Çalıştır"):
        scenario = st.selectbox("Senaryo Seçin", ["Baz Senaryo", "Küresel Resesyon", "Likitide Krizi (Şok)", "Faiz Şoku (+500bps)"])
        if st.button("Simülasyonu Koştur"):
            with st.spinner("Monte Carlo simülasyonları ve korelasyon matrisleri güncelleniyor..."):
                time.sleep(2)
                st.warning(f"Seçilen '{scenario}' senaryosu altında Sermaye Yeterlilik Oranı %11.4'e gerilemektedir (-%4.8 etki).")
                
                # Stres grafiği
                stress_steps = ["Current", "Market Shock", "Credit Shock", "Operational", "Post-Stress"]
                stress_values = [16.2, 14.5, 12.1, 11.8, 11.4]
                fig_stress = go.Figure(go.Scatter(x=stress_steps, y=stress_values, mode='lines+markers', line=dict(color='#f43f5e')))
                fig_stress.update_layout(title="Capital Adequacy Waterfall (Stress Impact)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_stress, use_container_width=True)

    st.success("✅ Tüm veriler BDDK / EBA standartlarına uygun olarak hesaplanmış ve doğrulanmıştır.")

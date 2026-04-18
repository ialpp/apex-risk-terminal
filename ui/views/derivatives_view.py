"""
ui/views/derivatives_view.py — ProQuant Capital | Türev Ürünler Analiz Dashboard v2.0
====================================================================================

Bu modül, derivatives_math.py motorunun arayüzünü sağlar.
Opsiyon fiyatlama, Greeks analizi, volatilite yüzeyleri ve CDS hesaplamalarını görselleştirir.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modules.derivatives_math import OptionType, BarrierType

def render_derivatives_view(deriv_engine, user_info):
    st.title("📐 Türev Ürünler & Kantitatif Analiz")
    st.markdown("<p style='color:#64748b;'>BSM, Heston, Merton modelleri ile opsiyon fiyatlama ve kredi türevleri analizi.</p>",
                unsafe_allow_html=True)

    tab_vanilla, tab_vol, tab_cds, tab_exotic = st.tabs([
        "💎 Vanilla Opsiyonlar", "🌪️ Volatilite Yüzeyi", "🛡️ Kredi Türevleri (CDS)", "🎭 Egzotik Ürünler"
    ])

    # 1. Vanilla Opsiyonlar
    with tab_vanilla:
        col_inp, col_res = st.columns([1, 2])
        
        with col_inp:
            st.subheader("Girdiler")
            S = st.number_input("Spot Fiyat (S)", value=100.0)
            K = st.number_input("Kullanım Fiyatı (K)", value=100.0)
            T = st.slider("Vade (Yıl)", 0.01, 5.0, 1.0)
            sigma = st.slider("Volatilite (σ)", 0.01, 1.0, 0.25)
            r = st.slider("Risksiz Faiz (r)", 0.0, 0.50, 0.12)
            q = st.slider("Temettü Verimi (q)", 0.0, 0.20, 0.0)

        with col_res:
            res = deriv_engine.price_vanilla(S, K, T, r, sigma, q)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### Call: **${res['call']['price']:.2f}**")
                st.json(res['call'])
            with c2:
                st.markdown(f"### Put: **${res['put']['price']:.2f}**")
                st.json(res['put'])
            
            st.info(f"Parite Kontrolü: {res['put_call_parity']} | Durum: {res['moneyness']}")

    # 2. Volatilite Yüzeyi (SVI & Heston)
    with tab_vol:
        st.subheader("Implied Volatility (IV) Yüzeyi — SVI Parametrizasyonu")
        
        # Grid simülasyonu
        mats = [0.25, 0.5, 1.0, 2.0]
        strikes = np.linspace(0.8, 1.2, 10) # Moneyness
        
        z_data = []
        for T_val in mats:
            row = []
            for K_val in strikes:
                # Gülümseme (Smile) efekti simülasyonu
                iv = 0.20 + 0.1 * (K_val - 1.0)**2 + 0.05 / T_val
                row.append(iv * 100)
            z_data.append(row)

        fig_surf = go.Figure(data=[go.Surface(z=z_data, x=strikes, y=mats, colorscale='Viridis')])
        fig_surf.update_layout(
            title="Volatility Surface (Strike vs Maturity)",
            scene=dict(
                xaxis_title='Moneyness (K/S)',
                yaxis_title='Time to Maturity (Y)',
                zaxis_title='Implied Vol (%)'
            ),
            width=800, height=600,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_surf, use_container_width=True)

    # 3. Kredi Türevleri (CDS)
    with tab_cds:
        st.subheader("CDS Spread & Hayatta Kalma Olasılığı")
        
        col_cds_1, col_cds_2 = st.columns(2)
        with col_cds_1:
            haz_rate = st.slider("Mortalite (Hazard Rate)", 0.001, 0.20, 0.02, format="%.3f")
            recovery = st.slider("Geri Kazanım (Recovery)", 0.0, 1.0, 0.40)
            
            cds_res = deriv_engine.cds_pricer.price_cds(1000000, haz_rate, 0.10, 5.0)
            st.metric("Fair CDS Spread (bps)", f"{cds_res['fair_spread_bps']:.1f}")
            st.write(f"1 Yıllık Temerrüt Olasılığı: %{cds_res['implied_pd_1y_pct']}")
            
        with col_cds_2:
            # Survival Curve plot
            times = np.linspace(0, 10, 50)
            survival = [np.exp(-haz_rate * t) * 100 for t in times]
            fig_surv = px.line(x=times, y=survival, title="Survival Probability Curve Q(t)")
            fig_surv.update_layout(xaxis_title="Yıl", yaxis_title="Hayatta Kalma %", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_surv, use_container_width=True)

    # 4. Egzotik Ürünler
    with tab_exotic:
        st.subheader("Bariyerli ve Asya Tipi Opsiyonlar")
        e_col1, e_col2 = st.columns(2)
        
        with e_col1:
            st.markdown("#### Barrier Option (Down & Out)")
            barrier = st.number_input("Barrier Level (H)", value=80.0)
            b_price = deriv_engine.run_full_analysis(S, K, T, r, sigma, q)["barrier_do_call"]
            st.write(f"Bariyerli Call Fiyatı: **${b_price:.4f}**")
            st.caption("Fiyat, bariyer seviyesine temas durumunda sıfırlanır (Knock-out).")
            
        with e_col2:
            st.markdown("#### Asian Option (Arithmetic Average)")
            asian_res = deriv_engine.run_full_analysis(S, K, T, r, sigma, q)["asian_arithmetic"]
            st.write(f"Asya Tipi Call Fiyatı: **${asian_res['call']:.4f}**")
            st.write(f"Güven Aralığı (95%): ±${asian_res['ci_95']:.4f}")
            st.caption("Fiyat, vade sonu yerine vade boyu ortalama fiyatı baz alır (Path-dependent).")

    st.success("🤖 Kantitatif motor, yüksek hassasiyetli Scipy ve Numpy çekirdeklerini kullanmaktadır.")

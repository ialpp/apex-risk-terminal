"""
ui/views/advanced/options_view.py — ProQuant Capital | Opsiyon Analiz Dashboard v7.0
======================================================================================
Greeks hesaplama, volatility surface ve option chain tarama özelliklerini sunan
kurumsal opsiyon analiz dashboard'u. BSM motoru üzerine inşa edilmiştir.
Author: ProQuant Capital Derivatives UX | Version: 7.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def render_options_view():
    st.header("📐 Opsiyon Fiyatlama & Greeks Analizi", divider="orange")

    with st.sidebar:
        st.subheader("⚙️ Opsiyon Parametreleri")
        underlying = st.text_input("Dayanak Varlık", "AAPL")
        opt_type   = st.selectbox("Tip", ["call", "put"])
        spot       = st.number_input("Spot Fiyat (S)", 10.0, 5000.0, 150.0)
        strike     = st.number_input("Kullanım Fiyatı (K)", 10.0, 5000.0, 150.0)
        tte_days   = st.slider("Vadeye Kalan Gün", 1, 730, 90)
        vol_pct    = st.slider("Implied Vol (%)", 5.0, 150.0, 25.0) / 100
        rfr        = st.slider("Risksiz Oran (%)", 0.0, 10.0, 4.0) / 100

    tte = tte_days / 365.0
    from modules.options_greeks_engine import get_options_greeks_engine
    eng  = get_options_greeks_engine()
    res  = eng.analyze_option(underlying, opt_type, spot, strike, tte, rfr, vol_pct)

    # ── Üst kartlar ──────────────────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("Opsiyon Primi ($)", f"{res['price']:.4f}")
    with c2: st.metric("Delta (Δ)", f"{res['delta']:.5f}")
    with c3: st.metric("Gamma (Γ)", f"{res['gamma']:.6f}")
    with c4: st.metric("Theta/Gün ($)", f"{res['theta_daily']:.4f}")
    with c5: st.metric("Vega (1% vol)", f"{res['vega_1pct']:.4f}")

    st.divider()
    tabs = st.tabs(["Greeks Özeti", "Option Chain", "Volatility Surface"])

    with tabs[0]:
        c_left, c_right = st.columns(2)
        with c_left:
            greeks_df = pd.DataFrame({
                "Greek": ["Delta Δ","Gamma Γ","Theta Θ/day","Vega ν (1%)","Rho ρ (100bps)","Vanna","Charm","Volga"],
                "Değer": [res['delta'], res['gamma'], res['theta_daily'],
                           res['vega_1pct'], res['rho_100bps'],
                           res['vanna'], res['charm'], res['volga']],
                "Yorum": ["Fiyat duyarlılığı","Eğrilik","Zaman erimesi","Vol duyarlılığı",
                           "Faiz duyarlılığı","∂Δ/∂σ","∂Δ/∂t","∂ν/∂σ"]
            })
            st.dataframe(greeks_df, use_container_width=True, hide_index=True)

        with c_right:
            mon = res.get('moneyness','ATM')
            itr = res.get('intrinsic_value', 0)
            tval= res.get('time_value', 0)
            st.metric("Para Durumu", mon)
            st.metric("İç Değer ($)", f"{itr:.4f}")
            st.metric("Zaman Değeri ($)", f"{tval:.4f}")
            st.metric("d1", f"{res.get('d1',0):.4f}")
            st.metric("d2", f"{res.get('d2',0):.4f}")

        # Delta profili grafiği
        spot_range = np.linspace(spot*0.7, spot*1.3, 100)
        from modules.options_greeks_engine import BSMCore, OptionContract
        bsm = BSMCore()
        deltas = []
        prices_arr = []
        for s in spot_range:
            opt_tmp = OptionContract(underlying, opt_type, float(s), strike, tte, rfr, vol_pct)
            g = bsm.full_greeks(opt_tmp)
            deltas.append(g.delta)
            prices_arr.append(g.price)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spot_range, y=prices_arr, mode='lines',
                                  name='Opsiyon Fiyatı', line=dict(color='#3b82f6', width=2)))
        fig.add_trace(go.Scatter(x=spot_range, y=deltas, mode='lines',
                                  name='Delta', line=dict(color='#f59e0b', width=2),
                                  yaxis='y2'))
        fig.add_vline(x=spot, line_dash='dash', line_color='#22c55e',
                      annotation_text=f"Spot: {spot}")
        fig.add_vline(x=strike, line_dash='dot', line_color='#ef4444',
                      annotation_text=f"Strike: {strike}")
        fig.update_layout(
            title="Fiyat ve Delta Profili",
            template="plotly_dark", height=380,
            yaxis2=dict(title="Delta", overlaying='y', side='right'),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("📋 Option Chain")
        strikes_chain = [round(spot * k/100, 1) for k in range(80, 125, 5)]
        chain = eng.scan_option_chain(spot, strikes_chain, tte, rfr, vol_pct)
        chain_df = pd.DataFrame(chain)[
            ["strike","type","price","delta","gamma","theta_daily","vega_1pct","moneyness"]
        ]
        chain_df.columns = ["Strike","Tip","Fiyat","Delta","Gamma","Theta/Gün","Vega","Para Durumu"]
        st.dataframe(chain_df.style.format(
            {"Fiyat":"{:.4f}","Delta":"{:.5f}","Gamma":"{:.6f}",
             "Theta/Gün":"{:.4f}","Vega":"{:.4f}"}),
            use_container_width=True, hide_index=True
        )

    with tabs[2]:
        st.subheader("🌋 Volatility Surface (Skew & Term Structure)")
        surface_data = eng.surface.build_surface(spot, rfr)
        ttm_keys = list(surface_data.keys())
        strike_keys = [k for k in surface_data[ttm_keys[0]].keys()]

        z_matrix = [[surface_data[t][k]*100 for k in strike_keys] for t in ttm_keys]
        fig3 = go.Figure(data=[go.Surface(
            z=z_matrix, x=strike_keys, y=ttm_keys,
            colorscale='Viridis',
            colorbar=dict(title="IV (%)")
        )])
        fig3.update_layout(
            title="Implied Volatility Surface",
            scene=dict(xaxis_title="Strike %", yaxis_title="TTM", zaxis_title="IV (%)"),
            template="plotly_dark", height=500
        )
        st.plotly_chart(fig3, use_container_width=True)

if __name__ == "__main__":
    render_options_view()

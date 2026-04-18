"""
ui/views/structuring_view.py — ProQuant Capital | Egzotik Kredi Yapılandırma Dashboard v2.0
==========================================================================================

Bu modül, credit_structuring_engine.py motorunun arayüzünü sağlar.
CDO/CLO yapılarının tasarlanması, dilim bazlı risk analizi ve waterfall simülasyonlarını içerir.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def render_structuring_view(struct_engine, user_info):
    st.title("🏦 Egzotik Kredi Yapılandırma & Tranche Analizi")
    st.markdown("<p style='color:#64748b;'>Karmaşık kredi türevleri (CDO/CLO) modelleme, Waterfall simülasyonu ve dilim bazlı risk transferi.</p>",
                unsafe_allow_html=True)

    # 1. Havuz Özeti ve Yapılandırma Ayarları
    with st.sidebar:
        st.header("⚙️ Havuz Parametreleri")
        pool_size = st.number_input("Havuzdaki Varlık Sayısı", 10, 1000, 100)
        total_notional = st.number_input("Toplam Havuz Notional ($)", 1e8, 1e10, 1e9, format="%.0e")
        st.divider()
        st.header("🧪 Simülasyon Ayarları")
        correlation = st.slider("Varlık Korelasyonu (ρ)", 0.0, 1.0, 0.30)
        iterations = st.slider("Monte Carlo İterasyon", 100, 5000, 1000)

    # 2. Tranche Mimarisi Görselleştirme
    st.subheader("🏗️ CDO Dilim Mimarisi (Tranches)")
    
    tranches = struct_engine.tranches
    
    # Waterfall/Stack Chart için veri hazırla
    fig_arch = go.Figure()
    
    # En alttan en üste: Equity -> Mezzanine -> Senior
    colors = ["#f43f5e", "#fbbf24", "#818cf8"] # Equity, Mezzanine, Senior
    for i, t in enumerate(reversed(tranches)):
        fig_arch.add_trace(go.Bar(
            name=t.name,
            x=[t.thickness * 100],
            y=["CDO Structure"],
            orientation='h',
            marker=dict(color=colors[i]),
            text=f"{t.name} (%{t.thickness*100:.0f})",
            textposition='inside'
        ))

    fig_arch.update_layout(
        barmode='stack',
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(title="Thickness (%)", range=[0, 100]),
        yaxis=dict(visible=False),
        showlegend=True
    )
    st.plotly_chart(fig_arch, use_container_width=True)

    # 3. Simülasyon Çalıştırma
    st.divider()
    col_sim1, col_sim2 = st.columns([1, 1])

    with col_sim1:
        st.subheader("🎲 Monte Carlo Stres Testi")
        if st.button("🚀 Simülasyonu Koştur", type="primary", use_container_width=True):
            with st.spinner("Gaussian Copula ve Waterfall algoritmaları işletiliyor..."):
                results = struct_engine.run_monte_carlo(iterations=iterations, correlation=correlation)
                st.session_state.struct_results = results
                st.success("✅ Simülasyon Tamamlandı.")

    if "struct_results" in st.session_state:
        res = st.session_state.struct_results
        
        with col_sim2:
            st.subheader("📊 Havuz Bazlı Sonuçlar")
            st.metric("Beklenen Havuz Zararı (EL)", f"%{res['avg_pool_loss_pct']:.2f}")
            st.metric("Max Gözlenen Zarar", f"%{res['max_pool_loss_pct']:.2f}")

        st.divider()
        
        # 4. Dilim Bazlı Beklenen Zarar (EL)
        st.subheader("📉 Dilim (Tranche) Bazlı Risk Analizi")
        
        names = list(res['tranche_expected_losses'].keys())
        el_values = list(res['tranche_expected_losses'].values())
        
        fig_el = px.bar(x=names, y=el_values, color=names, 
                        labels={'x': 'Tranche', 'y': 'Expected Loss (%)'},
                        title="Dilim Bazlı Beklenen Zarar Oranları",
                        color_discrete_sequence=["#818cf8", "#fbbf24", "#f43f5e"])
        
        fig_el.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', 
                             plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_el, use_container_width=True)

        # 5. Waterfall Detayları
        with st.expander("📝 Waterfall Detaylı Hesaplama Tablosu"):
            st.markdown("""
            Waterfall (Şelale) modeli, nakit akışlarının ve zararların kıdem sırasına göre dağıtılmasını sağlar:
            1. **Equity (Junior):** İlk zararı karşılar. Tamamen tükenene kadar diğer dilimler korunur.
            2. **Mezzanine:** Equity tükendikten sonraki zararı karşılar.
            3. **Senior:** En son koruma kalkanıdır. AAA reytingine sahip olması hedeflenir.
            """)
            
            w_data = []
            for name, el in res['tranche_expected_losses'].items():
                # Bul tranche object
                t_obj = next(t for t in tranches if t.name == name)
                w_data.append({
                    "Dilim Adı": name,
                    "Rank": t_obj.rank.value,
                    "Thickness": f"%{t_obj.thickness*100:.0f}",
                    "Attachment": f"%{t_obj.attachment_point*100:.0f}",
                    "Detachment": f"%{t_obj.detachment_point*100:.0f}",
                    "Expected Loss": f"%{el:.2f}",
                    "Coupon (bps)": t_obj.coupon_rate
                })
            st.table(pd.DataFrame(w_data))

    else:
        st.info("👈 Simülasyonu başlatmak için 'Simülasyonu Koştur' düğmesine basın.")

    st.divider()
    
    # Kredi Notu Dağılımı Simülasyonu
    st.subheader("🏷️ Sentetik Kredi Notu Dağılımı")
    ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "Default"]
    counts = [65, 15, 8, 5, 3, 2, 1, 1]
    fig_rat = px.pie(values=counts, names=ratings, hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu_r)
    fig_rat.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
    st.plotly_chart(fig_rat, use_container_width=True)

    st.caption("🚨 Bu modül eğitim ve analiz amaçlıdır. Yatırım tavsiyesi içermez.")

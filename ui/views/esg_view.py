"""
ui/views/esg_view.py — ProQuant Capital | ESG & Sürdürülebilirlik Dashboard v2.0
==============================================================================

Bu modül, esg_scoring_engine.py motorunun arayüzünü sağlar.
Kurumsal ESG skorlarını, itibar yönetimi verilerini ve sürdürülebilirlik trendlerini sunar.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.esg_scoring_engine import ESGRating, ESGCategory, get_esg_simulation_data

def render_esg_view(esg_engine, user_info):
    st.title("🌱 ESG & Sürdürülebilirlik Analiz Merkezi")
    st.markdown("<p style='color:#64748b;'>Çevresel, Sosyal ve Yönetişim (ESG) risk puanlaması ve kurumsal itibar izleme.</p>",
                unsafe_allow_html=True)

    # 1. Şirket Seçimi ve Veri Yükleme
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        entity = st.text_input("Analiz Edilecek Kurum", value="ProQuant Global Holdings")
    with col_sel2:
        sector = st.selectbox("Sektör", ["Enerji", "Teknoloji", "Finans", "Sağlık", "İnşaat", "Kamu Hizmetleri"])

    raw_data = get_esg_simulation_data(entity, sector)
    scorecard = esg_engine.perform_full_scoring(entity, sector, raw_data)

    # 2. Özet Bilgi Kartları
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    
    rating_colors = {
        "AAA": "#10b981", "AA": "#34d399", "A": "#6ee7b7",
        "BBB": "#f59e0b", "BB": "#fbbf24", "B": "#f87171",
        "CCC": "#ef4444", "D": "#ef4444"
    }
    
    with m1:
        st.markdown(f"""
        <div style="background:{rating_colors.get(scorecard.rating.name, '#64748b')}; padding:1rem; border-radius:10px; text-align:center;">
          <div style="font-size:0.7rem; color:rgba(0,0,0,0.6); font-weight:700;">ESG RATING</div>
          <div style="font-size:2rem; font-weight:900; color:white;">{scorecard.rating.value}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m2:
        st.metric("Toplam Skor", f"{scorecard.total_score:.1f}/100", f"{scorecard.ranking_in_sector:.1f}% Rank")
    with m3:
        st.metric("Çevresel (E)", f"{scorecard.e_score:.1f}")
    with m4:
        st.metric("Sosyal (S)", f"{scorecard.s_score:.1f}")
    with m5:
        st.metric("Yönetişim (G)", f"{scorecard.g_score:.1f}")

    # 3. Görsel Analiz (Radar Chart & Trend)
    st.divider()
    gc1, gc2 = st.columns([1, 1])
    
    with gc1:
        st.subheader("🕸️ ESG Risk Profili")
        # Radar Chart
        categories = ['Environmental', 'Social', 'Governance']
        values = [scorecard.e_score, scorecard.s_score, scorecard.g_score]
        
        fig_radar = go.Figure(data=go.Scatterpolar(
          r=values + [values[0]],
          theta=categories + [categories[0]],
          fill='toself',
          line_color=rating_colors.get(scorecard.rating.name, '#10b981'),
          marker=dict(size=10)
        ))
        
        fig_radar.update_layout(
          polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)")
          ),
          showlegend=False,
          template="plotly_dark",
          paper_bgcolor='rgba(0,0,0,0)',
          margin=dict(t=40, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with gc2:
        st.subheader("📈 Tarihsel ESG Trendi")
        trend_data = esg_engine.get_esg_trend(entity)
        months = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        fig_trend = px.line(x=months, y=trend_data, markers=True)
        fig_trend.update_layout(xaxis_title="Ay", yaxis_title="Skor", template="plotly_dark", 
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig_trend.update_traces(line_color="#818cf8", line_width=3)
        st.plotly_chart(fig_trend, use_container_width=True)

    # 4. Haber Akışı ve İtibar (NLP Simulation)
    st.divider()
    st.subheader("📰 Kurumsal İtibar & Haber Analizi (NLP)")
    
    from modules.esg_scoring_engine import get_reputation_engine
    rep_engine = get_reputation_engine()
    news = rep_engine.generate_news(entity)
    
    for n in news:
        icon = "🟢" if n.impact > 0 else "🔴"
        color = "#10b981" if n.impact > 0 else "#ef4444"
        with st.container():
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border-left:4px solid {color}; padding:0.8rem; border-radius:4px; margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b;">
                    <span>{n.source} | {n.category.value}</span>
                    <span>{n.timestamp.strftime("%Y-%m-%d %H:%M")}</span>
                </div>
                <div style="font-weight:600; font-size:0.9rem; margin:0.3rem 0;">{icon} {n.title}</div>
                <div style="font-size:0.8rem; color:{color}; font-weight:700;">Etki Skoru: {n.impact:+.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    # 5. Detaylı Metrik Listesi
    with st.expander("🔍 Tüm ESG Metriklerini İncele"):
        m_data = []
        for m in scorecard.metrics:
            m_data.append({
                "Kategori": m.category.value,
                "Metrik Adı": m.name,
                "Normal Skor": f"{m.value:.1f}",
                "Ham Değer": f"{m.raw_value} {m.unit}",
                "Ağırlık": f"%{m.weight*100:.0f}"
            })
        st.table(pd.DataFrame(m_data))

    st.info("ℹ️ Bu rapor SASB (Sustainability Accounting Standards Board) ve TCFD kılavuzlarına dayanmaktadır.")

"""
ui/views/risk_monitor_view.py — ProQuant Capital | Canlı Risk Monitörü Dashboard v2.0
====================================================================================

Bu modül, realtime_risk_monitor.py motorunun arayüzünü sağlar.
Anlık risk uyarılarını, eşik aşımlarını ve portföy sağlığını canlı olarak izler.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import datetime
from modules.realtime_risk_monitor import AlertSeverity, get_risk_monitor, get_risk_simulator

def render_risk_monitor_view(risk_monitor, user_info):
    st.title("📡 Canlı Risk Monitörü & Alert Engine")
    st.markdown("<p style='color:#64748b;'>Anlık eşik kontrolleri, multivariate alert üretimi ve portföy 'Pulse' analizi.</p>",
                unsafe_allow_html=True)

    # Simulator Kontrolü
    simulator = get_risk_simulator()
    
    with st.sidebar:
        st.subheader("📡 Monitör Kontrolü")
        if not simulator.is_running:
            if st.button("🔴 Canlı İzlemeyi Başlat", type="primary", use_container_width=True):
                simulator.start()
                st.rerun()
        else:
            if st.button("⏹️ İzlemeyi Durdur", use_container_width=True):
                simulator.stop()
                st.rerun()
        
        st.divider()
        st.info("💡 İzleme başladığında sistem saniyede binlerce işlemi tarar ve tanımlı risk kurallarını işletir.")

    # 1. Risk Pulse (Anlık Durum Özeti)
    pulse = risk_monitor.get_risk_pulse()
    
    st.subheader("💓 Portfolio Risk Pulse")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    counts = pulse["counts"]
    with c1:
        st.metric("Kritik", counts["Kritik"], delta=None, delta_color="inverse")
    with c2:
        st.metric("Yüksek", counts["Yüksek"], delta=None, delta_color="inverse")
    with c3:
        st.metric("Orta", counts["Orta"])
    with c4:
        st.metric("Düşük", counts["Düşük"])
    with c5:
        status = pulse["system_status"]
        color = "#ef4444" if status == "TEHLİKEDE" else "#f59e0b" if status == "RİSKLİ" else "#10b981"
        st.markdown(f"""
        <div style="background:{color}; padding:0.5rem; border-radius:8px; text-align:center; color:white; font-weight:800; font-size:0.8rem;">
            DURUM: {status}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 2. Aktif Uyarılar Listesi
    st.subheader("🔔 Aktif Risk Uyarıları")
    
    alerts = pulse["recent_alerts"]
    if not alerts:
        st.info("Şu an için aktif bir risk uyarısı bulunmamaktadır. Canlı izlemeyi başlatmayı unutmayın.")
    else:
        # Alert Tablosu (Manuel Render)
        st.markdown("""
        <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
            <tr style="background:rgba(255,255,255,0.05); border-bottom:1px solid rgba(255,255,255,0.1);">
                <th style="padding:0.5rem; text-align:left;">Zaman</th>
                <th style="padding:0.5rem; text-align:left;">Önem</th>
                <th style="padding:0.5rem; text-align:left;">Kategori</th>
                <th style="padding:0.5rem; text-align:left;">Entity</th>
                <th style="padding:0.5rem; text-align:left;">Mesaj</th>
                <th style="padding:0.5rem; text-align:right;">Değer</th>
                <th style="padding:0.5rem; text-align:center;">İşlem</th>
            </tr>
        """, unsafe_allow_html=True)
        
        for a in alerts:
            sev_color = "#ef4444" if a["severity"] == "Kritik" else "#f97316" if a["severity"] == "Yüksek" else "#f59e0b" if a["severity"] == "Orta" else "#3b82f6"
            res_style = "opacity:0.3;" if a["is_resolved"] else ""
            
            st.markdown(f"""
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05); {res_style}">
                <td style="padding:0.4rem;">{a['timestamp']}</td>
                <td style="padding:0.4rem; color:{sev_color}; font-weight:700;">{a['severity']}</td>
                <td style="padding:0.4rem;">{a['category']}</td>
                <td style="padding:0.4rem; font-family:monospace;">{a['entity']}</td>
                <td style="padding:0.4rem;">{a['message']}</td>
                <td style="padding:0.4rem; text-align:right; font-weight:600;">{a['value']}</td>
                <td style="padding:0.4rem; text-align:center;">
                    {'✅ Çözüldü' if a['is_resolved'] else '⚠️ Bekliyor'}
                </td>
            </tr>
            """, unsafe_allow_html=True)
            
        st.markdown("</table>", unsafe_allow_html=True)

    # 3. İstatistikler & Drifts
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📊 Kategori Bazlı Risk Dağılımı")
        # Simüle edilmiş dağılım
        cat_data = pd.DataFrame({
            "Kategori": ["Kredi", "Sahtekarlık", "Likidite", "Makro", "ESG"],
            "Alert Sayısı": [42, 12, 5, 18, 9]
        })
        import plotly.express as px
        fig_cat = px.bar(cat_data, x="Kategori", y="Alert Sayısı", color="Kategori", 
                        color_discrete_sequence=px.colors.sequential.Agsunset)
        fig_cat.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)

    with g2:
        st.subheader("📉 Risk Drift (Son 60 Dakika)")
        # Simüle edilmiş drift
        minutes = list(range(60))
        risk_score = np.cumsum(np.random.normal(0, 1, 60)) + 50
        fig_drift = px.line(x=minutes, y=risk_score, title="Kümülatif Portföy Risk Skoru")
        fig_drift.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig_drift.update_traces(line_color="#f43f5e", fill='tozeroy')
        st.plotly_chart(fig_drift, use_container_width=True)

    # 4. Kural Yönetimi (Özet)
    with st.expander("📝 Aktif İzleme Kuralları (Thresholds)"):
        rules_df = pd.DataFrame([
            {"Kural ID": r.rule_id, "Kategori": r.category.value, "Metrik": r.metric_name, 
             "Eşik": f"{r.operator} {r.target_value}", "Önem": r.severity.value}
            for r in risk_monitor.rules
        ])
        st.table(rules_df)

    # Auto-refresh simülasyonu
    if simulator.is_running:
        time.sleep(1)
        st.rerun()

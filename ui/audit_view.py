"""
ui/audit_view.py
Denetim İzi (Audit Trail) & Sistem Log Monitörü
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from core.database_handler import db
from core.auth_system import require_role


def render_audit_view(user_info: dict):
    st.title("🔍 Denetim İzi & Sistem Log Monitörü")
    st.markdown("<p style='color:#64748b;'>Tüm risk analizleri, kullanıcı işlemleri ve sistem olaylarının şeffaf kaydı.</p>", unsafe_allow_html=True)

    tab_analysis, tab_warnings, tab_system = st.tabs([
        "📋 Analiz Logları", "⚠️ Erken Uyarılar", "🖥️ Sistem Logları"
    ])

    with tab_analysis:
        _render_analysis_logs()

    with tab_warnings:
        _render_warnings_panel(user_info)

    with tab_system:
        _render_system_logs(user_info)


def _render_analysis_logs():
    st.subheader("Tüm Risk Analiz Geçmişi")

    col_filter, col_analyst = st.columns(2)
    with col_filter:
        result_filter = st.selectbox("Karar Filtresi", ["Tümü", "✅ Onaylananlar", "❌ Reddedilenler"])
    with col_analyst:
        limit = st.slider("Gösterilecek Satır Sayısı", 10, 500, 100, step=10)

    logs = db.get_recent_logs(limit=limit)
    if logs.empty:
        st.info("Henüz analiz logu bulunamadı.")
        return

    if result_filter == "✅ Onaylananlar" and "ml_result" in logs.columns:
        logs = logs[logs["ml_result"] == 1]
    elif result_filter == "❌ Reddedilenler" and "ml_result" in logs.columns:
        logs = logs[logs["ml_result"] == 0]

    # Özet metrikler
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Sorgu", len(logs))
    if "ml_result" in logs.columns:
        approved_count = (logs["ml_result"] == 1).sum()
        m2.metric("Onaylanan", approved_count)
        m3.metric("Reddedilen", len(logs) - approved_count)
    if "credit_score" in logs.columns:
        m4.metric("Ort. Skor", f"{logs['credit_score'].mean():.0f}")

    st.divider()

    # Analist bazlı aktivite grafiği
    if "analyst_name" in logs.columns and not logs["analyst_name"].isna().all():
        analyst_counts = logs["analyst_name"].value_counts().reset_index()
        analyst_counts.columns = ["Analist", "Sorgu Sayısı"]
        fig = px.bar(
            analyst_counts, x="Analist", y="Sorgu Sayısı",
            color="Sorgu Sayısı",
            color_continuous_scale=["#4f46e5","#818cf8"],
            title="Analist Bazlı Sorgu Dağılımı",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            xaxis=dict(showgrid=False, color="#475569"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#475569"),
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=40, b=0),
            height=220,
            title_font=dict(size=13, color="#94a3b8"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Log tablosu
    show_cols = [
        "timestamp", "analyst_name", "customer_name", "age",
        "income", "credit_score", "ml_result", "fraud_score", "risk_category"
    ]
    show_cols = [c for c in show_cols if c in logs.columns]
    logs_show = logs[show_cols].copy()
    if "ml_result" in logs_show.columns:
        logs_show["ml_result"] = logs_show["ml_result"].map({1: "✅ Onay", 0: "❌ Red"})
    if "income" in logs_show.columns:
        logs_show["income"] = logs_show["income"].map("₺{:,.0f}".format)
    if "credit_score" in logs_show.columns:
        logs_show["credit_score"] = logs_show["credit_score"].map(
            lambda x: f"{x:.0f}" if pd.notna(x) else "—"
        )

    st.dataframe(logs_show, use_container_width=True, hide_index=True, height=400)

    # CSV
    csv_bytes = logs.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Analiz Loglarını CSV Olarak İndir",
        data=csv_bytes,
        file_name="analiz_loglari.csv",
        mime="text/csv",
    )


def _render_warnings_panel(user_info: dict):
    st.subheader("Erken Uyarı Yönetim Paneli")

    warnings = db.get_active_warnings()
    if warnings.empty:
        st.success("✅ Tüm uyarılar çözümlendi. Portföy temiz.")
        return

    # Önem dağılımı
    if "severity" in warnings.columns:
        sev_counts = warnings["severity"].value_counts()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Kritik",  sev_counts.get("Kritik", 0))
        c2.metric("🟠 Yüksek",  sev_counts.get("Yüksek", 0))
        c3.metric("🟡 Orta",    sev_counts.get("Orta", 0))
        c4.metric("🔵 Düşük",   sev_counts.get("Düşük", 0))
        st.divider()

    for _, w in warnings.iterrows():
        sev   = w.get("severity", "Orta")
        icon  = {"Kritik": "🔴", "Yüksek": "🟠", "Orta": "🟡", "Düşük": "🔵"}.get(sev, "⚪")
        color = {"Kritik": "#ef4444","Yüksek":"#f97316","Orta":"#f59e0b","Düşük":"#3b82f6"}.get(sev,"#64748b")
        name  = w.get("full_name") or w.get("customer_code", "?")

        with st.expander(f"{icon} **{sev}** — {name} | {w.get('warning_type','')}"):
            st.markdown(f"<span style='color:{color};'>{w.get('message','')}</span>",
                        unsafe_allow_html=True)
            st.caption(f"Oluşturulma: {w.get('created_at','')} | Müşteri Kodu: {w.get('customer_code','')}")
            if st.button(f"✅ Çözümlendi Olarak İşaretle",
                         key=f"resolve_{w.get('id','')}"):
                db.resolve_warning(int(w["id"]), user_info["username"])
                st.success("Uyarı çözümlendi.")
                st.rerun()


def _render_system_logs(user_info: dict):
    if not require_role(2):
        return
    st.subheader("Sistem Olay Logları")
    sys_logs = db.get_system_logs(limit=200)
    if sys_logs.empty:
        st.info("Sistem logu bulunamadı.")
        return

    level_filter = st.multiselect("Log Seviyesi", ["INFO", "WARNING", "ERROR"],
                                   default=["INFO", "WARNING", "ERROR"])
    if "level" in sys_logs.columns:
        sys_logs = sys_logs[sys_logs["level"].isin(level_filter)]

    show = ["created_at","level","module","message","user"]
    show = [c for c in show if c in sys_logs.columns]
    st.dataframe(sys_logs[show], use_container_width=True, hide_index=True, height=400)

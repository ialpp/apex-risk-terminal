"""
ui/dashboard_view.py
ProQuant Apex Risk Terminal — Executive Dashboard v6.0
Ultra-premium institutional analytics dashboard
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import textwrap
from core.database_handler import db
from ui.theme import kpi_card_html, get_risk_label, get_risk_color, section_header_html
from config import SCORE_BANDS


def _get_theme():
    """Aktif tema paletini döndürür."""
    return st.session_state.get("theme_palette", {
        "bg": "#060B18",
        "card_bg": "rgba(13,31,60,0.85)",
        "card_border": "rgba(56,189,248,0.15)",
        "text": "#E2E8F0",
        "text_strong": "#F8FAFC",
        "muted": "#64748B",
        "muted2": "#94A3B8",
        "border": "rgba(51,65,85,0.8)",
        "primary": "#38BDF8",
        "primary_rgb": "56, 189, 248",
        "gradient1": "#38BDF8",
        "gradient2": "#6366F1",
        "success": "#10B981",
        "danger": "#F43F5E",
        "warning": "#F59E0B",
        "shadow": "rgba(0,0,0,0.5)",
    })


def _plotly_layout(t: dict, height: int = 320) -> dict:
    """Plotly grafikleri için tutarlı kurumsal layout."""
    is_dark = st.session_state.get("theme", "dark") == "dark"
    paper_bg = "rgba(0,0,0,0)" 
    grid_color = "rgba(51,65,85,0.4)" if is_dark else "rgba(229,231,235,0.8)"
    tick_color = t["muted"]

    return dict(
        paper_bgcolor=paper_bg,
        plot_bgcolor=paper_bg,
        font=dict(color=t["muted"], family="Inter", size=12),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=tick_color, size=11),
            linecolor="rgba(0,0,0,0)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            gridwidth=1,
            tickfont=dict(color=tick_color, size=11),
            linecolor="rgba(0,0,0,0)",
            zeroline=False,
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11, color=t["muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(13,31,60,0.95)" if is_dark else "rgba(255,255,255,0.97)",
            bordercolor=t["border"],
            font=dict(color=t["text"], family="Inter", size=12),
        ),
    )


def render_dashboard(user_info: dict):
    t = _get_theme()
    is_dark = st.session_state.get("theme", "dark") == "dark"

    # ── Page Header ────────────────────────────────────────────────
    full_name = user_info.get("full_name", "—")
    role      = user_info.get("role", "—")
    dept      = user_info.get("department", "—")

    import datetime
    hour = datetime.datetime.now().hour
    greeting = "Günaydın" if hour < 12 else "İyi Öğlenler" if hour < 17 else "İyi Akşamlar"

    st.markdown(textwrap.dedent(f"""
    <div style="margin-bottom: 2rem;">
        <div style="
            display: flex; align-items: flex-start;
            justify-content: space-between;
            flex-wrap: wrap; gap: 1rem;
        ">
            <div>
                <div style="font-size:0.78rem; font-weight:600; color:{t['muted']};
                            text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.35rem;">
                    📊 Yönetici Kontrol Paneli
                </div>
                <h1 style="
                    margin: 0; font-size: 1.8rem; font-weight: 900;
                    background: linear-gradient(135deg, {t['gradient1']}, {t['gradient2']});
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text; letter-spacing: -0.5px; line-height: 1.1;
                ">{greeting}, {full_name.split()[0]}.</h1>
                <p style="margin: 0.4rem 0 0; color: {t['muted']}; font-size: 0.875rem; font-weight: 500;">
                    {role} &nbsp;·&nbsp; {dept}
                </p>
            </div>
            <div style="
                display: flex; gap: 0.75rem; align-items: center;
                flex-wrap: wrap;
            ">
                <div style="
                    padding: 0.4rem 0.9rem;
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.25);
                    border-radius: 100px;
                    display: flex; align-items: center; gap: 0.4rem;
                    font-size: 0.75rem; font-weight: 700; color: #10B981;
                ">
                    <span style="
                        width: 7px; height: 7px; border-radius: 50%;
                        background: #10B981;
                        animation: fdhPulse 2s ease infinite;
                        display: inline-block;
                    "></span>
                    Sistemler Aktif
                </div>
                <div style="
                    padding: 0.4rem 0.9rem;
                    background: rgba({t['primary_rgb']}, 0.08);
                    border: 1px solid rgba({t['primary_rgb']}, 0.2);
                    border-radius: 100px;
                    font-size: 0.75rem; font-weight: 600; color: {t['primary']};
                ">
                    🔄 Gerçek Zamanlı
                </div>
            </div>
        </div>
    </div>
    <style>
    @keyframes fdhPulse {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(16,185,129,0.6); }}
        70%       {{ box-shadow: 0 0 0 6px rgba(16,185,129,0); }}
    }}
    </style>
    """), unsafe_allow_html=True)

    # ── KPI Stats ─────────────────────────────────────────────────
    stats = db.get_portfolio_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_data = [
        (c1, "Aktif Portföy",   f"{stats['total_customers']:,}", "Toplam Müşteri",      t['gradient1'],  "🏦", "+5.2%", True),
        (c2, "Ort. Kredi Skoru", f"{stats['avg_score']:.0f}",   get_risk_label(stats['avg_score']), get_risk_color(stats['avg_score']), "⭐", "+2.1%", True),
        (c3, "Onay Oranı",      f"{stats['approval_rate']:.1f}%", "Sistem Ortalaması",  "#10B981",        "✅", "-0.3%", False),
        (c4, "Bekleyen Onay",   str(stats['pending_applications']), "Analiz Bekliyor",  t['warning'],     "⏳", "", False),
        (c5, "Kritik Uyarı",    str(stats['active_warnings']),   "Acil Müdahale",       "#F43F5E",        "🚨", "", False),
    ]
    for col, title, val, sub, color, icon, trend, tp in kpi_data:
        with col:
            st.markdown(
                kpi_card_html(title, val, sub, color, icon, trend, tp),
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Chart Row ─────────────────────────────────────────────────
    col_left, col_right = st.columns([1.65, 1])

    with col_left:
        st.markdown(section_header_html("📈", "Kurumsal Başvuru Trend Analizi",
                                        "Son 12 aylık başvuru & onay eğilimi"), unsafe_allow_html=True)

        trend_df = db.get_monthly_application_trend()
        if not trend_df.empty:
            fig = go.Figure()

            # Bar: Toplam başvuru
            fig.add_trace(go.Bar(
                x=trend_df["month"],
                y=trend_df["applications"],
                name="Toplam Başvuru",
                marker=dict(
                    color=f"rgba({t['primary_rgb']}, 0.12)",
                    line=dict(color=f"rgba({t['primary_rgb']}, 0.3)", width=1),
                ),
                hovertemplate="<b>%{x}</b><br>Başvuru: %{y:,}<extra></extra>"
            ))

            # Area fill
            fig.add_trace(go.Scatter(
                x=trend_df["month"],
                y=trend_df["approved"],
                name="Onaylanan",
                mode="lines",
                fill="tozeroy",
                fillcolor=f"rgba({t['primary_rgb']}, 0.06)",
                line=dict(color=t["gradient1"], width=0),
                hovertemplate="<b>%{x}</b><br>Onaylanan: %{y:,}<extra></extra>"
            ))

            # Line: Onaylanan
            fig.add_trace(go.Scatter(
                x=trend_df["month"],
                y=trend_df["approved"],
                name="",
                mode="lines+markers",
                line=dict(color=t["gradient1"], width=2.5, shape="spline"),
                marker=dict(size=7, color=t["gradient1"],
                            line=dict(color=t["bg"], width=2)),
                showlegend=False,
                hoverinfo="skip"
            ))

            layout = _plotly_layout(t, height=300)
            layout["barmode"] = "group"
            fig.update_layout(**layout)

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Trend verisi bulunamadı.")

    with col_right:
        st.markdown(section_header_html("🎯", "Risk Dağılım Matrisi",
                                        "Portföy kalite segmentasyonu"), unsafe_allow_html=True)

        risk_dist = stats.get("risk_distribution", {})
        if risk_dist:
            labels = list(risk_dist.keys())
            values = list(risk_dist.values())
            colors = {
                "Mükemmel": "#10B981",
                "Çok İyi":  "#38BDF8",
                "İyi":      "#6366F1",
                "Orta":     "#F59E0B",
                "Zayıf":    "#F43F5E",
            }
            clrs = [colors.get(l, "#64748B") for l in labels]

            fig2 = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.65,
                marker=dict(
                    colors=clrs,
                    line=dict(color=t["bg"], width=3)
                ),
                textinfo="percent",
                textfont=dict(size=11, family="Inter", color="white"),
                hovertemplate="<b>%{label}</b><br>%{value} müşteri<br>%{percent}<extra></extra>",
            )])

            # Donut center text
            fig2.add_annotation(
                text=f"<b>{sum(values):,}</b><br><span style='font-size:10px'>Müşteri</span>",
                x=0.5, y=0.5,
                font=dict(size=18, color=t["text_strong"], family="Inter"),
                showarrow=False,
                align="center"
            )

            layout2 = _plotly_layout(t, height=300)
            layout2.update({"showlegend": True,
                            "legend": {
                                "orientation": "v",
                                "x": 1.02, "y": 0.5,
                                "font": {"size": 11, "color": t["muted"]},
                                "bgcolor": "rgba(0,0,0,0)",
                            }})
            fig2.update_layout(**layout2)

            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Risk dağılım verisi bulunamadı.")

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"<hr style='border-top: 1px solid {t['border']}; opacity:0.5;'>", unsafe_allow_html=True)
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Bottom Row ────────────────────────────────────────────────
    col_warn, col_log = st.columns([1, 1.5])

    with col_warn:
        st.markdown(section_header_html("⚠️", "Kritik Uyarılar",
                                        "Aktif risk bildirimleri"), unsafe_allow_html=True)

        warnings = db.get_active_warnings()
        if warnings.empty:
            st.markdown(f"""
            <div style="
                background: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.2);
                border-radius: 12px; padding: 1.5rem;
                text-align: center;
            ">
                <div style="font-size:1.75rem; margin-bottom:0.5rem;">🛡️</div>
                <div style="color: #10B981; font-weight:700; font-size:0.9rem;">Portföy Güvende</div>
                <div style="color:{t['muted']}; font-size:0.78rem; margin-top:0.25rem;">Aktif uyarı bulunmuyor</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sev_colors = {
                "Kritik": "#F43F5E",
                "Yüksek": "#F59E0B",
                "Orta":   "#38BDF8",
                "Düşük":  "#64748B"
            }
            sev_icons = {
                "Kritik": "🔴",
                "Yüksek": "🟠",
                "Orta":   "🔵",
                "Düşük":  "⚪"
            }
            for _, w in warnings.head(5).iterrows():
                sev   = w.get("severity", "Orta")
                color = sev_colors.get(sev, "#64748B")
                icon  = sev_icons.get(sev, "○")
                name  = w.get("full_name") or w.get("customer_code", "?")
                rgb   = "244,63,94" if sev=="Kritik" else "245,158,11" if sev=="Yüksek" else "56,189,248" if sev=="Orta" else "100,116,139"
                st.markdown(textwrap.dedent(f"""
                <div style="
                    background: rgba({rgb}, 0.06);
                    border: 1px solid rgba({rgb}, 0.2);
                    border-left: 3px solid {color};
                    padding: 0.85rem 1rem;
                    border-radius: 10px;
                    margin-bottom: 0.6rem;
                    transition: all 0.2s ease;
                ">
                    <div style="
                        display: flex; align-items: center;
                        justify-content: space-between; margin-bottom: 0.2rem;
                    ">
                        <span style="
                            font-size: 0.68rem; font-weight: 800;
                            color: {color}; text-transform: uppercase;
                            letter-spacing: 0.08em;
                        ">{icon} {sev}</span>
                        <span style="font-size: 0.68rem; color: {t['muted']};">
                            {str(w.get('created_at',''))[:10]}
                        </span>
                    </div>
                    <div style="font-weight: 700; color: {t['text_strong']}; font-size: 0.875rem;">{name}</div>
                    <div style="color: {t['muted']}; font-size: 0.75rem; margin-top: 0.15rem;">
                        {w.get('warning_type', '')}
                    </div>
                </div>
                """), unsafe_allow_html=True)

    with col_log:
        st.markdown(section_header_html("📋", "Son İşlem Kayıtları",
                                        "Gerçek zamanlı aktivite akışı"), unsafe_allow_html=True)

        logs = db.get_recent_logs(limit=10)
        if logs.empty:
            st.info("İşlem kaydı bulunmuyor.")
        else:
            final_df = logs[["timestamp", "customer_name", "credit_score", "ml_result"]].copy()
            final_df.columns = ["Tarih", "Müşteri", "Skor", "Karar"]
            final_df["Karar"] = final_df["Karar"].map({1: "✅ ONAY", 0: "❌ RED"})

            st.dataframe(
                final_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Tarih":   st.column_config.TextColumn("📅 Tarih", width="medium"),
                    "Müşteri": st.column_config.TextColumn("👤 Müşteri", width="large"),
                    "Skor":    st.column_config.NumberColumn("📊 Skor", format="%d", width="small"),
                    "Karar":   st.column_config.TextColumn("⚡ Karar", width="small"),
                }
            )

    # ── Quick Action Bar ──────────────────────────────────────────
    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
    
    # Butonları ayrı oluşturup sızıntıları önleyelim
    quick_items = ["👤 Yeni Analiz", "📊 Portföy", "🛡️ Risk Monitör", "📄 Rapor Oluştur"]
    btns_html = ""
    for item in quick_items:
        btns_html += f"""
        <div style="
            padding: 0.45rem 0.95rem;
            background: rgba({t['primary_rgb']}, 0.08);
            border: 1px solid rgba({t['primary_rgb']}, 0.2);
            border-radius: 8px;
            font-size: 0.78rem; font-weight: 700;
            color: {t['primary']};
            cursor: pointer;
            transition: all 0.2s ease;
        ">{item}</div>
        """

    st.markdown(textwrap.dedent(f"""
    <div style="
        background: {t['card_bg']};
        border: 1px solid {t['card_border']};
        border-radius: 14px; padding: 1.25rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 1rem;
        backdrop-filter: blur(20px);
    ">
        <div>
            <div style="font-weight:800; color:{t['text_strong']}; font-size:0.9rem;">
                ⚡ Hızlı İşlemler
            </div>
            <div style="font-size:0.75rem; color:{t['muted']}; margin-top:2px;">
                En çok kullanılan modüllere hızlı erişim
            </div>
        </div>
        <div style="display:flex; gap:0.65rem; flex-wrap:wrap;">
            {btns_html}
        </div>
    </div>
    """), unsafe_allow_html=True)

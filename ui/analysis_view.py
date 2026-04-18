"""
ui/analysis_view.py
Apex Risk Terminal - Customer Analysis Engine
Findeks-Style Interactive Analytics
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from ui.theme import score_gauge_html, decision_banner_html
from core.database_handler import db
from config import SCORE_BANDS


def render_analysis_view(engine, fraud_engine, cluster_engine, rec_engine, user_info: dict):
    # Header Section
    st.markdown(f"""
        <div style="margin-bottom: 2rem;">
            <h1 style="margin:0; color:#004C91;">👤 Yeni Müşteri Risk Analizi</h1>
            <p style="color:#6B7280; font-size:1rem;">
                Gerçek zamanlı kredi skoru, temerrüt ihtimali ve kurumsal AI karar motoru.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if not engine.is_trained():
        st.error("⚙️ Model henüz eğitilmedi. Lütfen Model Yönetimi sekmesinde modeli eğitin.")
        return

    # ── Veri Giriş Formu (Clean White Card) ───────────────────────
    with st.container():
        with st.form("main_analysis_form", clear_on_submit=False):
            st.markdown("<h4 style='color:#1E293B;'>📋 Finansal Veri Girişi</h4>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                full_name = st.text_input("Ad Soyad", placeholder="Örn: Mehmet Öz")
                age = st.number_input("Yaş", 18, 85, 35)
                occupation = st.text_input("Meslek / Sektör", placeholder="Bankacı")
            with c2:
                monthly_income = st.number_input("Aylık Net Gelir (TL)", 5500, 500000, 35000, step=1000)
                total_debt = st.number_input("Mevcut Borç Yükü (TL)", 0, 5000000, 15000, step=1000)
                late_payment_count = st.number_input("Gecikmiş Ödeme (Son 12 Ay)", 0, 24, 0)
            with c3:
                credit_card_count = st.number_input("Aktif Kart Sayısı", 0, 15, 2)
                credit_history_years = st.number_input("Kredi Geçmişi (Yıl)", 0.0, 40.0, 5.0, step=0.5)
                employment_years = st.number_input("Çalışma Yılı", 0.0, 45.0, 4.0, step=0.5)

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 Analizi Başlat", use_container_width=True, type="primary")

    if not submitted:
        return

    # ── Analiz Süreci ───────────────────────────────────────────
    raw = {
        "Yas": int(age),
        "Aylik_Gelir": float(monthly_income),
        "Mevcut_Borc": float(total_debt),
        "Gecikmis_Odeme_Sayisi": int(late_payment_count),
        "Kredi_Karti_Sayisi": int(credit_card_count),
        "Kredi_Gecmisi_Yili": float(credit_history_years),
        "Calisma_Yili": float(employment_years),
        "Ek_Gelir": 0,
        "Bagli_Kisi_Sayisi": 0,
    }

    with st.spinner("Motor hesaplaması yapılıyor..."):
        try:
            ml_result = engine.predict(raw)
            fraud_result = fraud_engine.score(raw)
            segment = cluster_engine.predict_segment(raw)
            recs = rec_engine.generate(raw, ml_result["credit_score"], ml_result["risk_category"])
            fico_bd = ml_result.get("fico_breakdown", {})
        except Exception as e:
            st.error(f"Sistem Hatası: {e}")
            return

    # Log Kaydı
    db.log_analysis(
        analyst=user_info["username"],
        customer_code=f"TR-{int(age)}-{int(monthly_income/1000)}k",
        customer_name=full_name or "Müşteri",
        age=int(age), income=float(monthly_income),
        debt=float(total_debt),
        dti=(total_debt / monthly_income) if monthly_income > 0 else 0,
        late_payments=int(late_payment_count),
        card_count=int(credit_card_count),
        credit_score=ml_result["credit_score"],
        ml_result=int(ml_result["approved"]),
        ml_prob=ml_result["approval_prob"],
        fraud_score=fraud_result["fraud_score"],
        risk_category=ml_result["risk_category"],
    )

    st.markdown("<hr style='margin:2rem 0;'>", unsafe_allow_html=True)

    # ── Sonuç Paneli ───────────────────────────────────────────
    res_c1, res_c2, res_c3 = st.columns([1, 1.3, 1])

    with res_c1:
        score = ml_result["credit_score"]
        score_color = engine.get_score_color(score)
        st.markdown(score_gauge_html(score, score_color, "Analiz Skoru"), unsafe_allow_html=True)
        st.markdown(f"""
            <div style="text-align:center; margin-top:1rem;">
                <div style="font-weight:800; color:{score_color}; font-size:1.4rem;">{ml_result['risk_category']}</div>
                <div style="color:#64748B; font-size:0.85rem;">Ürün Grubu Bazlı Risk Sınıfı</div>
            </div>
        """, unsafe_allow_html=True)

    with res_c2:
        st.markdown(decision_banner_html(ml_result["approved"], ml_result["approval_prob"]), unsafe_allow_html=True)
        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 12px; margin-top: 1rem; text-align: center;">
                <div style="color:#64748B; font-size:0.85rem; margin-bottom:0.3rem;">Müşteri Davranışı Segmenti</div>
                <div style="font-size:1.2rem; font-weight:700; color:{segment['color']};">
                    {segment['icon']} {segment['segment']}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with res_c3:
        f_score = fraud_result["fraud_score"]
        f_color = "#10B981" if f_score < 30 else "#F59E0B" if f_score < 60 else "#EF4444"
        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; padding: 2rem; border-radius: 12px; text-align: center;">
                <div style="color:#64748B; font-size:0.75rem; text-transform:uppercase; font-weight:700;">GÜVENLİK ANALİZİ</div>
                <div style="font-size:3.5rem; font-weight:900; color:{f_color}; margin: 0.5rem 0;">{f_score}</div>
                <div style="font-weight:700; color:{f_color};">{fraud_result['risk_level']} Risk</div>
                <div style="font-size:0.75rem; color:#94A3B8; margin-top:0.5rem; border-top: 1px solid #F1F5F9; padding-top: 0.5rem;">
                    {len(fraud_result.get('flags',[]))} Kırmızı Bayrak Tespiti
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:2.5rem;'></div>", unsafe_allow_html=True)

    # ── Detaylı Analiz Tabları ──────────────────────────────────
    tabs = st.tabs(["📊 Skor Kırılımı", "🔍 Karar Gerekçesi (XAI)", "📉 Stres Analizi", "💡 AI Pro-Aktif Öneriler"])

    with tabs[0]:
        _render_fico_tab(fico_bd)
    with tabs[1]:
        _render_xai_tab(engine)
    with tabs[2]:
        _render_stress_tab(engine, raw)
    with tabs[3]:
        _render_recs_tab(recs)


def _render_fico_tab(fico_bd: dict):
    st.subheader("Bileşen Bazlı Puan Analizi")
    if not fico_bd: return
    
    cats = list(fico_bd.keys())
    vals = [v["score"] for v in fico_bd.values()]
    maxs = [v["max"] for v in fico_bd.values()]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cats, y=vals, name="Kazanılan",
        marker_color="#004C91",
        text=[f"{v:.0f}" for v in vals], textposition="auto"
    ))
    fig.add_trace(go.Bar(
        x=cats, y=[m - v for m, v in zip(maxs, vals)], name="Potansiyel Kayıp",
        marker_color="#E2E8F0"
    ))
    fig.update_layout(
        barmode="stack", paper_bgcolor="white", plot_bgcolor="white",
        height=350, margin=dict(t=20, b=20),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
    )
    st.plotly_chart(fig, use_container_width=True)

def _render_xai_tab(engine):
    st.subheader("Model Karar Gerekçeleri (XAI)")
    imp_df = engine.get_feature_importances()
    if imp_df.empty: return
    
    fig = px.bar(imp_df, x="Önem", y="Özellik", orientation="h",
                 color="Önem", color_continuous_scale=["#E2E8F0", "#004C91"])
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", height=380,
                      coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

def _render_stress_tab(engine, raw):
    st.subheader("Makro Ekonomik Şok Analizi")
    scen = engine.run_all_stress_scenarios(raw)
    lbls = ["Baz", "Hafif Şok", "Orta Şok", "Kriz Senaryosu"]
    scores = [s["credit_score"] for s in scen]
    
    fig = go.Figure(go.Scatter(x=lbls, y=scores, mode="lines+markers+text",
                               text=[f"{s:.0f}" for s in scores], textposition="top center",
                               line=dict(color="#004C91", width=3)))
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", height=320,
                      xaxis=dict(showgrid=False), yaxis=dict(range=[200, 1000], showgrid=True))
    st.plotly_chart(fig, use_container_width=True)

def _render_recs_tab(recs):
    st.subheader("Pro-Aktif Skor İyileştirme Planı")
    for r in recs:
        with st.expander(f"{r.get('icon','•')} {r.get('category','')} - {r.get('title','')} (Etki: {r.get('impact_score','')})"):
            st.write(r.get("desc",""))
            st.markdown(f"**Öneri:** {r.get('impact','')}")

"""
ui/macro_view.py
Makro Ekonomik Analiz & Portföy Stres Testi Paneli
Monte Carlo simülasyonu, senaryo karşılaştırması, bölgesel risk haritası placeholder
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from config import MONTE_CARLO_RUNS


def render_macro_view(engine, user_info: dict):
    st.title("📉 Makro Ekonomik Analiz & Stres Testleri")
    st.markdown("<p style='color:#64748b;'>Basel III uyumlu makro şok simülasyonları, Monte Carlo analizleri ve senaryo karşılaştırmaları.</p>",
                unsafe_allow_html=True)

    tab_scenario, tab_mc, tab_what_if = st.tabs([
        "📊 Senaryo Karşılaştırması", "🎲 Monte Carlo Simülasyonu", "🔮 'Ya Olursa?' Analizörü"
    ])

    with tab_scenario:
        _render_scenario_comparison(engine)

    with tab_mc:
        _render_monte_carlo(engine)

    with tab_what_if:
        _render_what_if(engine)


def _render_scenario_comparison(engine):
    st.subheader("4 Makro Senaryo Altında Kredi Risk Analizi")
    st.info("Türkiye ekonomik koşullarına göre özelleştirilmiş senaryo parametreleri kullanılmaktadır.")

    if not engine.is_trained():
        st.error("Model eğitilmedi. Lütfen önce Model Yönetimi sekmesinden modeli eğitin.")
        return

    # Baz müşteri profili
    st.markdown("#### Baz Profil (Temsili Orta Segment Müşteri)")
    c1, c2, c3 = st.columns(3)
    with c1:
        age    = st.number_input("Yaş", 20, 70, 38, key="macro_age")
        income = st.number_input("Aylık Gelir (TL)", 5500, 200000, 28000, step=500, key="macro_inc")
    with c2:
        debt  = st.number_input("Toplam Borç (TL)", 0, 2000000, 35000, step=1000, key="macro_dbt")
        late  = st.number_input("Gecikmiş Ödeme", 0, 15, 1, key="macro_late")
    with c3:
        cards   = st.number_input("Kredi Kartı", 0, 10, 2, key="macro_cards")
        history = st.number_input("Kredi Geçmişi (Yıl)", 0.0, 30.0, 4.0, key="macro_hist")

    raw = {
        "Yas": int(age), "Aylik_Gelir": float(income),
        "Mevcut_Borc": float(debt), "Gecikmis_Odeme_Sayisi": int(late),
        "Kredi_Karti_Sayisi": int(cards), "Kredi_Gecmisi_Yili": float(history),
        "Calisma_Yili": 5.0, "Ek_Gelir": 0, "Bagli_Kisi_Sayisi": 1,
    }

    if st.button("🚀 Tüm Senaryoları Çalıştır", type="primary"):
        with st.spinner("4 senaryo analiz ediliyor..."):
            results = engine.run_all_stress_scenarios(raw)

        labels   = ["🟢 Temel", "🟡 Hafif Şok\n(%10 Enf.)", "🟠 Orta Şok\n(%20 Enf.)", "🔴 Ağır Şok\n(%40 Enf.)"]
        scores   = [r["credit_score"] for r in results]
        defaults = [r["default_risk"] * 100 for r in results]
        decisions = [r["approved"] for r in results]
        bar_colors = ["#10b981" if d else "#ef4444" for d in decisions]

        # Ana karşılaştırma grafiği
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=labels, y=scores,
            name="Kredi Skoru",
            marker_color=bar_colors,
            marker_line_color="rgba(255,255,255,0.2)",
            marker_line_width=1,
            text=[f"<b>{s:.0f}</b>" for s in scores],
            textposition="outside",
            textfont=dict(color="#e2e8f0", size=12),
            yaxis="y",
        ))
        fig.add_trace(go.Scatter(
            x=labels, y=defaults,
            mode="lines+markers+text",
            name="Temerrüt Riski (%)",
            line=dict(color="#f59e0b", width=2.5),
            marker=dict(size=10, color="#f59e0b",
                        line=dict(color="#fff", width=2)),
            text=[f"%{d:.1f}" for d in defaults],
            textposition="top center",
            textfont=dict(color="#f59e0b", size=11),
            yaxis="y2",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            xaxis=dict(showgrid=False, color="#475569", tickfont=dict(size=11)),
            yaxis=dict(title="Kredi Skoru", showgrid=True,
                       gridcolor="rgba(255,255,255,0.06)", color="#475569"),
            yaxis2=dict(title="Temerrüt Riski (%)", overlaying="y",
                        side="right", color="#f59e0b", showgrid=False),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.08),
            margin=dict(l=0, r=0, t=20, b=0),
            height=380,
            bargap=0.3,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detay tablosu
        table_rows = []
        scenario_names = ["Temel Senaryo", "Hafif Şok (+%10 Enflasyon)",
                           "Orta Şok (+%20 Enflasyon)", "Ağır Şok (+%40 Enflasyon)"]
        for r, name in zip(results, scenario_names):
            params = r.get("scenario_params", {})
            table_rows.append({
                "Senaryo":          name,
                "Enflasyon Şoku":   f"%{params.get('inflation',0)*100:.0f}",
                "Faiz Şoku":        f"%{params.get('interest',0)*100:.0f}",
                "Kredi Skoru":      f"{r['credit_score']:.0f}",
                "Temerrüt Riski":   f"%{r['default_risk']*100:.1f}",
                "Onay Olasılığı":   f"%{r['approval_prob']*100:.1f}",
                "Karar":            "✅" if r["approved"] else "❌",
                "Risk Kategorisi":  r.get("risk_category", "—"),
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        # Skor düşüşü analizi
        st.markdown("#### 📊 Şok Etkisi — Baz Senaryoya Göre Skor Kaybı")
        base_score = scores[0]
        drops = [0] + [base_score - s for s in scores[1:]]
        fig2 = go.Figure(go.Waterfall(
            x=["Temel", "Hafif Şok", "Orta Şok", "Ağır Şok"],
            y=[base_score] + [-d for d in drops[1:]],
            measure=["absolute"] + ["relative"] * 3,
            base=0,
            connector=dict(line=dict(color="rgba(255,255,255,0.2)")),
            increasing=dict(marker_color="#10b981"),
            decreasing=dict(marker_color="#ef4444"),
            totals=dict(marker_color="#4f46e5"),
            text=[f"{v:.0f}" for v in [base_score] + [-d for d in drops[1:]]],
            textposition="outside",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            xaxis=dict(showgrid=False, color="#475569"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", color="#475569"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=280,
        )
        st.plotly_chart(fig2, use_container_width=True)


def _render_monte_carlo(engine):
    st.subheader(f"🎲 Monte Carlo Simülasyonu ({MONTE_CARLO_RUNS:,} Tekrar)")
    st.info("Gelir ve borç belirsizliği altında temerrüt olasılığı dağılımı simüle edilir.")

    if not engine.is_trained():
        st.error("Model eğitilmedi.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        mc_income = st.number_input("Baz Aylık Gelir (TL)", 5500, 200000, 25000, key="mc_inc")
    with c2:
        mc_debt   = st.number_input("Baz Toplam Borç (TL)", 0, 1000000, 20000, key="mc_dbt")
    with c3:
        mc_late   = st.number_input("Gecikmiş Ödeme", 0, 15, 1, key="mc_late")

    if st.button("🎲 Simülasyonu Başlat", type="primary", key="btn_mc"):
        raw_mc = {
            "Yas": 38, "Aylik_Gelir": float(mc_income),
            "Mevcut_Borc": float(mc_debt),
            "Gecikmis_Odeme_Sayisi": int(mc_late),
            "Kredi_Karti_Sayisi": 2, "Kredi_Gecmisi_Yili": 4.0,
            "Calisma_Yili": 5.0, "Ek_Gelir": 0, "Bagli_Kisi_Sayisi": 1,
        }

        with st.spinner(f"{MONTE_CARLO_RUNS:,} simülasyon çalışıyor..."):
            mc_result = engine.monte_carlo_simulation(raw_mc, n=MONTE_CARLO_RUNS)

        # Metrikler
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ortalama Temerrüt Riski", f"%{mc_result['mean_default']*100:.1f}")
        m2.metric("%5 Güven Aralığı (İyimser)", f"%{mc_result['p5']*100:.1f}")
        m3.metric("%95 Güven Aralığı (Kötümser)", f"%{mc_result['p95']*100:.1f}")
        m4.metric(">%50 Risk Yoğunluğu", f"%{mc_result['prob_above_50']*100:.1f}")

        # Histogram
        dist = np.array(mc_result["distribution"]) * 100
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=dist,
            nbinsx=60,
            name="Temerrüt Dağılımı",
            marker_color="rgba(79,70,229,0.7)",
            marker_line_color="#4f46e5",
            marker_line_width=0.5,
        ))
        # %95 VaR çizgisi
        p95_val = mc_result["p95"] * 100
        fig.add_vline(
            x=p95_val, line_dash="dash", line_color="#ef4444",
            annotation_text=f"VaR 95%: %{p95_val:.1f}",
            annotation_font_color="#ef4444"
        )
        # Ortalama çizgisi
        mean_val = mc_result["mean_default"] * 100
        fig.add_vline(
            x=mean_val, line_dash="dash", line_color="#10b981",
            annotation_text=f"Ortalama: %{mean_val:.1f}",
            annotation_font_color="#10b981",
            annotation_position="top left"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Inter"),
            xaxis=dict(title="Temerrüt Olasılığı (%)", showgrid=False, color="#475569"),
            yaxis=dict(title="Frekans", showgrid=True,
                       gridcolor="rgba(255,255,255,0.06)", color="#475569"),
            margin=dict(l=0, r=0, t=20, b=0),
            height=350,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Standart Sapma: %{mc_result['std']*100:.2f} — Simülasyon {mc_result['runs']:,} senaryodan oluşmaktadır.")


def _render_what_if(engine):
    st.subheader("🔮 'Ya Olursa?' Skor Simülatörü")
    st.info("Müşterinin belirli finansal değerlerini değiştirdiğinde skoru nasıl değişecek?")

    if not engine.is_trained():
        st.error("Model eğitilmedi.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Mevcut Durum")
        wi_income = st.number_input("Aylık Gelir (TL)", 5500, 300000, 22000, key="wi_inc")
        wi_debt   = st.number_input("Toplam Borç (TL)", 0, 2000000, 40000, key="wi_dbt")
        wi_late   = st.number_input("Gecikmiş Ödeme", 0, 20, 3, key="wi_late")
        wi_cards  = st.number_input("Kredi Kartı Sayısı", 0, 15, 3, key="wi_cards")
    with c2:
        st.markdown("##### Planlanan Değişiklikler (Delta)")
        delta_debt  = st.number_input("Borç Değişimi (- azaltma / + artış)", -200000, 200000, -10000, step=1000, key="wi_delta_dbt")
        delta_late  = st.number_input("Gecikme Değişimi", -10, 5, -2, key="wi_delta_late")
        delta_income = st.number_input("Gelir Değişimi (TL)", -50000, 100000, 5000, step=500, key="wi_delta_inc")
        delta_cards  = st.number_input("Kart Değişimi", -10, 5, -1, key="wi_delta_cards")

    raw_wi = {
        "Yas": 36, "Aylik_Gelir": float(wi_income),
        "Mevcut_Borc": float(wi_debt),
        "Gecikmis_Odeme_Sayisi": int(wi_late),
        "Kredi_Karti_Sayisi": int(wi_cards),
        "Kredi_Gecmisi_Yili": 4.0, "Calisma_Yili": 5.0,
        "Ek_Gelir": 0, "Bagli_Kisi_Sayisi": 1,
    }
    changes = {
        "Mevcut_Borc":            float(delta_debt),
        "Gecikmis_Odeme_Sayisi":  int(delta_late),
        "Aylik_Gelir":            float(delta_income),
        "Kredi_Karti_Sayisi":     int(delta_cards),
    }

    if st.button("🔮 Değişim Etkisini Hesapla", type="primary"):
        sim = engine.what_if_simulator(raw_wi, changes)
        orig  = sim["original_score"]
        mod   = sim["modified_score"]
        delta = sim["score_change"]

        c_orig, c_arrow, c_new = st.columns([1, 0.3, 1])
        with c_orig:
            color_o = engine.get_score_color(orig)
            st.markdown(f"""
            <div style='text-align:center; padding:1.5rem;
                        background:rgba(15,23,42,0.5); border-radius:12px;
                        border:2px solid {color_o};'>
              <div style='font-size:0.75rem; color:#64748b; text-transform:uppercase;'>MEVCUT SKOR</div>
              <div style='font-size:3rem; font-weight:900; color:{color_o};'>{orig:.0f}</div>
              <div style='font-size:0.85rem; color:{color_o};'>
                {"✅ Onay" if sim["original_predict"]["approved"] else "❌ Red"}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with c_arrow:
            arrow_color = "#10b981" if delta > 0 else "#ef4444" if delta < 0 else "#94a3b8"
            arrow = "→" 
            st.markdown(f"""
            <div style='text-align:center; padding:2rem 0; font-size:2rem; color:{arrow_color};'>
              {arrow}<br>
              <span style='font-size:1rem; font-weight:700;'>
                {'+' if delta >= 0 else ''}{delta:.0f}
              </span>
            </div>
            """, unsafe_allow_html=True)
        with c_new:
            color_m = engine.get_score_color(mod)
            st.markdown(f"""
            <div style='text-align:center; padding:1.5rem;
                        background:rgba(15,23,42,0.5); border-radius:12px;
                        border:2px solid {color_m};'>
              <div style='font-size:0.75rem; color:#64748b; text-transform:uppercase;'>YENİ SKOR</div>
              <div style='font-size:3rem; font-weight:900; color:{color_m};'>{mod:.0f}</div>
              <div style='font-size:0.85rem; color:{color_m};'>
                {"✅ Onay" if sim["modified_predict"]["approved"] else "❌ Red"}
              </div>
            </div>
            """, unsafe_allow_html=True)

        if delta > 20:
            st.success(f"🎉 Planlanan değişiklikler kredi skorunuzu **+{delta:.0f} puan** artıracak!")
        elif delta > 0:
            st.info(f"📈 Skorda **+{delta:.0f} puanlık** iyileşme bekleniyor.")
        elif delta < -20:
            st.error(f"⚠️ Bu değişiklikler skoru **{delta:.0f} puan** düşürecek!")
        else:
            st.warning(f"↔️ Skorda minimal değişim: {delta:+.0f} puan.")

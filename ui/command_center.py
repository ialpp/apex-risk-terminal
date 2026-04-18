import streamlit as st
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_command_center():
    st.markdown("""
        <p style='color: #004C91; font-weight: 800; font-size: 0.9rem; letter-spacing: 2px; text-transform: uppercase;'>INSTITUTIONAL COMMAND CENTER</p>
        <h1 style='font-weight: 900; font-size: 3rem; margin-bottom: 0.2rem;'>Komuta & Operasyon Merkezi</h1>
        <p style='color: #64748b; font-size: 1.1rem; margin-bottom: 2rem;'>Kredi iş akışlarını, otonom onayları ve komite kararlarını yönetin.</p>
    """, unsafe_allow_html=True)

    t_war, t_flow, t_dark, t_strat = st.tabs([
        "🛡️ Risk War Room", 
        "⛓️ İş Akışı (BPM)", 
        "🤖 Dark Decisioning", 
        "📊 Strateji Simülatörü"
    ])

    # 1. RISK WAR ROOM (Collaboration)
    with t_war:
        st.subheader("Kurumsal Karar Odası & Analitik Tartışma")
        col_chat, col_poll = st.columns([2, 1])
        
        with col_chat:
            # ÜST BÖLÜM: KARAR DESTEK GRAFİĞİ
            st.markdown("<p style='font-size:0.85rem; color:#64748b; margin-bottom:1rem;'>Hedef Kurum: <b>XYZ-992 (Strategic Partner)</b> - Karar Destek Matrisi</p>", unsafe_allow_html=True)
            
            radar_data = pd.DataFrame(dict(
                r=[80, 45, 90, 60, 70],
                theta=['Nakit Akışı', 'Teminat Gücü', 'Sektör Trendi', 'Müşteri Skoru', 'Piyasa Duyarlılığı']
            ))
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=radar_data['r'],
                theta=radar_data['theta'],
                fill='toself',
                line_color='#004C91',
                fillcolor='rgba(0, 76, 145, 0.2)'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                height=250,
                margin=dict(l=40, r=40, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            messages = [
                {"user": "Müdür_Can", "time": "14:20", "msg": "XYZ-992 nakit akışı rasyosu biraz düşük, görüşü olan?"},
                {"user": "Analist_Elif", "time": "14:22", "msg": "Alternatif verilerde (nakliye trafiği) %20 büyüme var, olumlu."},
                {"user": "Yönetici_Sarp", "time": "14:25", "msg": "Piyasa riski tablosuna göre likidite şoku bekliyoruz."},
                {"user": "Sistem_AI", "time": "14:26", "msg": "ANALİZ: Sektör trendi rasyoyu %15 yukarı çekebilir."}
            ]
            
            chat_html = "<div style='background:#f8fafc; padding:1.2rem; border-radius:10px; height:200px; overflow-y:auto; border:1px solid #e2e8f0; font-family:Inter, sans-serif; font-size:0.9rem;'>"
            for m in messages:
                color = "#004C91" if "Müdür" in m['user'] else "#10b981" if "AI" in m['user'] else "#475569"
                chat_html += f"<div style='margin-bottom:0.8rem;'><b style='color:{color};'>{m['user']}</b> <span style='font-size:0.75rem; color:#94a3b8;'>[{m['time']}]</span><br>{m['msg']}</div>"
            chat_html += "</div>"
            
            st.markdown(chat_html, unsafe_allow_html=True)
            
            c_inp, c_btn = st.columns([4, 1])
            with c_inp:
                st.text_input("Görüşünüzü bildirin...", key="war_room_msg", label_visibility="collapsed")
            with c_btn:
                if st.button("Paylaş", type="primary", use_container_width=True):
                    st.toast("Görüşünüz komiteye iletildi.", icon="💬")

        with col_poll:
            st.markdown("<div style='background:#f1f5f9; padding:1rem; border-radius:10px; border:1px solid #cbd5e1;'>", unsafe_allow_html=True)
            st.write("🗳️ **Komite Oylaması**")
            st.write("Konu: XYZ-992 Kredi Limit Artışı")
            vote = st.radio("Kararınız", ["Onayla", "Reddet", "Ek Teminat İste"], label_visibility="collapsed")
            if st.button("Oy Kullan", use_container_width=True):
                st.session_state["last_vote"] = vote
                st.success(f"Oyunuz ({vote}) kaydedildi.")
                st.balloons()
            st.markdown("</div>", unsafe_allow_html=True)

    # 2. WORKFLOW BPM (Interactive)
    if "workflow_df" not in st.session_state:
        st.session_state["workflow_df"] = pd.DataFrame({
            "ID": ["L-9102", "L-9105", "L-9108"],
            "Müşteri": ["Penta Corp", "Gözde Gıda", "Mavi Lojistik"],
            "Durum": ["Onayda", "Analiz", "Hukuk İnceleme"],
            "Sorumlu": ["Caner B.", "Ayşe K.", "Mert Ş."],
            "Süre": ["2 Gün", "4 Saat", "1 Hafta"]
        })

    with t_flow:
        st.subheader("Kredi Yaşam Döngüsü Takibi")
        st.table(st.session_state["workflow_df"])
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Bir Sonraki Aşamaya Taşı ➔", use_container_width=True):
                # İlk sıradaki kaydı bi sonraki aşamaya taşıma mantığı
                idx = 0
                current_status = st.session_state["workflow_df"].at[idx, "Durum"]
                new_status = "TAMAMLANDI" if current_status == "Hukuk İnceleme" else "SÖZLEŞME" if current_status == "Onayda" else "HUKUK"
                st.session_state["workflow_df"].at[idx, "Durum"] = new_status
                st.toast(f"{st.session_state['workflow_df'].at[idx, 'Müşteri']} durumu güncellendi: {new_status}")
                st.rerun()
                
        with c2:
            if st.button("Süreci Durdur 🛑", use_container_width=True, type="secondary"):
                st.session_state["workflow_df"].at[0, "Durum"] = "DURDURULDU"
                st.error("Proses manuel olarak durduruldu.")
                st.rerun()

        with c3:
            if st.button("Revizyon İste ↩️", use_container_width=True):
                st.session_state["workflow_df"].at[0, "Durum"] = "REVİZYON Bekliyor"
                st.warning("Eksik evrak/bilgi talebi gönderildi.")
                st.rerun()

    # 3. DARK DECISIONING (Autonomous)
    with t_dark:
        st.subheader("Otonom (Dark) Onay Motoru")
        st.markdown("<div style='background:#0f172a; padding:1.5rem; border-radius:12px; border:1px solid #1e293b; color:white;'>", unsafe_allow_html=True)
        is_autopilot = st.toggle("🤖 Otonom Mod (Auto-Pilot) Aktif", value=True)
        st.write("---")
        st.markdown(f"**Durum:** {'SİSTEM OTO-PLİOTTA' if is_autopilot else 'MANUEL KONTROL'}")
        st.slider("Otonom Onay Eşik Skoru (Min)", 300, 850, 750)
        st.write("Bu skorun üzerindeki krediler insan kontrolü olmadan onaylanır.")
        st.info("Bugün otonom olarak 14 kredi onaylandı, 22 milyon TL risk tahsis edildi.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. STRATEGY SIMULATOR
    with t_strat:
        st.subheader("Strateji ve Limit Optimizasyonu")
        st.markdown("<p style='font-size:0.9rem;'>Limit artış politikalarını test edin.</p>", unsafe_allow_html=True)
        increase_pct = st.slider("Limit Artış Yüzdesi (%)", 0, 50, 15)
        
        # Mock Impact Analysis
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.metric("Tahmini Yeni NPL (Takipteki Krediler)", f"%{2.1 + (increase_pct/20):.2f}", delta="+0.05%")
        with c_i2:
            st.metric("Beklenen Gelir Artışı", f"${12 + (increase_pct * 0.8):.1f}M", delta="+$2.4M")
        
        st.markdown("<div style='padding:1rem; border:1px dashed #cbd5e1; border-radius:8px;'>Bu simülasyon, Monte Carlo yöntemleri ile 10.000 farklı senaryo üzerinde koşturulmuştur.</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

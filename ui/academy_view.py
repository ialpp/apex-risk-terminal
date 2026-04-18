import streamlit as st
import os
from ui.academy_data import get_articles

def render_academy_view():
    view_mode = st.session_state.get("academy_view_mode", "grid")
    articles = get_articles()
    
    # Check if we are viewing an article
    if view_mode.startswith("article_"):
        art_id = view_mode.replace("article_", "")
        current_article = next((a for a in articles if a["id"] == art_id), None)
        
        if current_article:
            st.button("← Geri Dön", on_click=lambda: st.session_state.update({"academy_view_mode": "grid"}))
            st.markdown(f"<h2 style='color: #004C91; padding-top: 1rem;'>{current_article['title']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #6B7280; font-size: 0.9rem;'>Yazan: Baş Veri Bilimcisi | Okuma Süresi: {current_article['read_time']} | Kategori: {current_article['category']}</p>", unsafe_allow_html=True)
            st.divider()
            
            art_col1, art_col2 = st.columns([1, 2.5])
            with art_col1:
                img_paths = [
                    r"C:\Users\İsmail Alp\.gemini\antigravity\brain\3cf74ef8-7e97-44b0-8874-3a17ff69aa5b\blog_ai_risk_1776425120095.png",
                    r"C:\Users\İsmail Alp\.gemini\antigravity\brain\3cf74ef8-7e97-44b0-8874-3a17ff69aa5b\blog_macro_finance_1776425135253.png",
                    r"C:\Users\İsmail Alp\.gemini\antigravity\brain\3cf74ef8-7e97-44b0-8874-3a17ff69aa5b\blog_fraud_sec_1776425150452.png"
                ]
                idx = (current_article["image_idx"] - 1) % 3
                selected_img = img_paths[idx]
                
                if os.path.exists(selected_img):
                    st.image(selected_img, use_container_width=True)
                st.markdown(f"<p style='font-size: 0.75rem; color: #9CA3AF; text-align: center;'>Fig: {current_article['category']} Görseli.</p>", unsafe_allow_html=True)
                
            with art_col2:
                # Convert bold text from string to clean markdown, keeping spacing
                # Content has markdown already
                st.markdown(current_article['content'])
            return

    st.markdown("""
        <div style="margin-bottom: 2rem;">
            <h1 style="color: #004C91; font-weight: 800; font-size: 2.5rem; margin-bottom: 0.5rem;">Akademi & Araştırma Merkezi</h1>
            <p style="color: #6B7280; font-size: 1.1rem; max-width: 800px;">
                Kurumsal finansal risk yönetimi, gelişmiş algoritmalar ve makine öğrenimi modellerine dair en güncel teknik notlar, eğitim videoları ve araştırma makaleleri.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    img_paths = [
        r"C:\Users\İsmail Alp\.gemini\antigravity\brain\3cf74ef8-7e97-44b0-8874-3a17ff69aa5b\blog_ai_risk_1776425120095.png",
        r"C:\Users\İsmail Alp\.gemini\antigravity\brain\3cf74ef8-7e97-44b0-8874-3a17ff69aa5b\blog_macro_finance_1776425135253.png",
        r"C:\Users\İsmail Alp\.gemini\antigravity\brain\3cf74ef8-7e97-44b0-8874-3a17ff69aa5b\blog_fraud_sec_1776425150452.png"
    ]
    
    # Daha küçük görseller ve daha yoğun liste için 4 kolon
    cols_per_row = 4
    for i in range(0, len(articles), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(articles):
                art = articles[i + j]
                idx = (art["image_idx"] - 1) % 3
                img = img_paths[idx]
                
                with col:
                    st.markdown("<div class='pq-card' style='height: 100%; min-height: 400px; margin-bottom: 1rem;'>", unsafe_allow_html=True)
                    if os.path.exists(img): 
                        st.image(img, use_container_width=True)
                    st.markdown(f"<h4 style='font-size: 1.05rem; min-height: 40px;'>{art['title']}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #004C91; font-size: 0.75rem; font-weight: 700;'>{art['category']}</span> <br><span style='color: #6B7280; font-size: 0.75rem;'>• {art['read_time']}</span>", unsafe_allow_html=True)
                    st.write(art['short_desc'][:120] + "...")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    button_label = "Eğitimi İzle ▶" if "Video" in art['read_time'] else "Makaleyi Oku ➔"
                    btn_type = "secondary" if "Video" in art['read_time'] else "primary"
                    
                    if st.button(button_label, key=f"read_{art['id']}", type=btn_type, use_container_width=True):
                        st.session_state["academy_view_mode"] = f"article_{art['id']}"
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### 📋 Diğer Araştırma Bültenleri")
    
    # Liste tarzı görünüm
    cols = st.columns([1, 4])
    with cols[0]:
        st.markdown("**14 Nisan 2026**<br><span style='color: #6B7280; font-size: 0.8rem;'>Teknik Döküman</span>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("**AutoML ile Kredi Tahsis Optimizasyonu**")
        st.write("Algoritmik optimizasyon paketlerimizin yeni sürüm notları ve entegrasyon rehberi.")
        
    st.markdown("<hr style='margin: 1rem 0; border-color: #E5E7EB;'>", unsafe_allow_html=True)
    
    cols2 = st.columns([1, 4])
    with cols2[0]:
        st.markdown("**02 Nisan 2026**<br><span style='color: #6B7280; font-size: 0.8rem;'>Güncelleme</span>", unsafe_allow_html=True)
    with cols2[1]:
        st.markdown("**Piyasa Rejimi (Market Regime) Analizlerinde Markov Zincirleri**")
        st.write("Yeni geliştirilen HMM modülünün, volatilite tahminlerindeki %15'lik başarı artışının arka planı.")

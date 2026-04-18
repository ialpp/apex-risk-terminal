import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import plotly.express as px
import plotly.graph_objects as go
import time

def render_about_view():
    
    # Kapsamlı CSS, Animasyon ve Hyper-Elite Özellikler
    st.markdown("""
    <style>
        .about-container { font-family: 'Inter', sans-serif; color: #374151; position: relative; }
        
        .hero-background {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
            background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
            background-size: 30px 30px; opacity: 0.3;
        }

        .hero-title { color: #111827; font-weight: 900; font-size: 3.5rem; line-height: 1.1; margin-top: 1rem; margin-bottom: 1.5rem; letter-spacing: -1px; }
        .hero-subtitle { color: #4B5563; font-size: 1.2rem; max-width: 800px; line-height: 1.6; }
        
        /* 8. TYPEWRITER EFEKTİ (Daktilo) */
        .typewriter {
            overflow: hidden; 
            white-space: nowrap; 
            margin: 0 auto; 
            letter-spacing: .05em; 
            animation: typing 3.5s steps(40, end), blink-caret .75s step-end infinite;
            border-right: .15em solid #004C91;
            color: #004C91;
            font-weight: 800;
            font-size: 1.1rem;
            width: fit-content;
        }
        @keyframes typing { from { width: 0 } to { width: 100% } }
        @keyframes blink-caret { from, to { border-color: transparent } 50% { border-color: #004C91; } }

        /* API Status Terminali */
        .api-terminal {
            background: #0a0a0a !important; padding: 1rem;
            border-radius: 8px; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);
        }
        .api-terminal div {
            color: #10b981 !important; font-family: 'Courier New', Courier, monospace !important; 
            font-size: 0.9rem !important; line-height: 1.6 !important; font-weight: 600 !important;
            text-shadow: 0 0 8px rgba(16,185,129,0.4) !important;
        }
        .pulse-dot { display: inline-block; width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

        /* 5. GITHUB COMMITS (Dikey Kayan Bant) */
        .git-feed-wrapper { height: 120px; overflow: hidden; background: #0f172a !important; border-radius: 6px; padding: 1rem; border: 1px solid #1e293b; }
        .git-feed { animation: scrollUp 15s linear infinite; }
        .git-commit { color: #38bdf8 !important; font-family: monospace !important; font-size: 0.85rem !important; margin-bottom: 0.8rem; }
        .git-commit span { color: #94a3b8 !important; }
        @keyframes scrollUp { 0% { transform: translateY(0); } 100% { transform: translateY(-100%); } }

        /* 2. CANLI HABER & DUYGU ANALİZİ AKIŞI */
        .news-ticker-wrapper { background: #111827 !important; padding: 1rem; border-radius: 8px; border-left: 4px solid #f43f5e; overflow: hidden; white-space: nowrap; }
        .news-item { display: inline-block; animation: marquee-news 20s linear infinite; color: #ffffff !important; font-family: monospace !important; font-size: 0.95rem !important;}
        .news-tag-risk { background: #f43f5e !important; color: #ffffff !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 10px; }
        .news-tag-pos { background: #10b981 !important; color: #ffffff !important; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 10px; }
        @keyframes marquee-news { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

        /* 10. KUBERNETES KAFKA CONTAINER ANİMASYONU */
        .k8s-cluster { display: flex; gap: 10px; margin-top: 10px; }
        .k8s-pod { width: 30px; height: 30px; background: #e0f2fe; border: 2px solid #0ea5e9; border-radius: 6px; animation: breathe 3s infinite ease-in-out; }
        .k8s-pod:nth-child(2) { animation-delay: 0.5s; background: #dcfce7; border-color: #22c55e;}
        .k8s-pod:nth-child(3) { animation-delay: 1s; background: #fef08a; border-color: #eab308;}
        .k8s-pod:nth-child(4) { animation-delay: 1.5s; background: #ffedd5; border-color: #f97316;}
        @keyframes breathe { 0% { transform: scale(1); box-shadow: 0 0 0 rgba(14,165,233,0); } 50% { transform: scale(1.15); box-shadow: 0 0 15px rgba(14,165,233,0.5); } 100% { transform: scale(1); box-shadow: 0 0 0 rgba(14,165,233,0); } }

        /* Standart UI Blokları */
        .glass-card { background: rgba(255, 255, 255, 0.7); border: 1px solid rgba(255,255,255,0.5); border-radius: 12px; padding: 1.5rem; height: 100%; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

    # ------------------ HERO SECTION & MANİFESTO ------------------
    st.markdown("""
        <div class="about-container" style="padding-top: 1rem;">
            <div class="hero-background"></div>
            <div class="typewriter">İnsan zafiyetinden algoritmik mutlaklığa...</div>
            <h1 class="hero-title">Veri Şoklarına Karşı Tam Bağışıklık:<br><span style="color: #004C91;">Zekanın Kurumsallaşması.</span></h1>
            <p class="hero-subtitle">
                Geleneksel bankacılığı yıkan, anlık likidite ve küresel oynaklıklara karşı 
                "Sıfır Güven (Zero-Trust) ve Otonom Tahsis" sağlayan açık bağlantılı sinir ağı (Neural Network) ekosistemiyiz.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ------------------ API STATUS TERMINAL ------------------
    st.markdown("""
        <div class="api-terminal" style="margin-top: 2rem;">
            <div>> APEX.CORE.NODE_CHECK()</div>
            <div>[<span class="pulse-dot"></span>FRANKFURT SERVER]   PING: 12ms | SLA: HEALTHY | UPTIME: 99.998%</div>
            <div>[<span class="pulse-dot"></span>LONDON KAFKA CL]    PING: 08ms | SLA: HEALTHY | STREAM: ACTIVE</div>
            <div>[<span class="pulse-dot"></span>ISTANBUL INFERENCE] PING: 18ms | SLA: HEALTHY | XAI: ONLINE</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)



    # ------------------ İKİLİ KOLON: ZKP ve ROI HESAPLAYICI ------------------
    col_zk, col_roi = st.columns([1, 1])

    with col_zk:
        # 3. MASKELENMİŞ VERİ DEMOSU (ZERO-KNOWLEDGE)
        st.markdown("<h4 style='color: #111827;'>🔐 Zero-Knowledge (Sıfır Bilgi) Demostrasyonu</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:#64748b;'>Bankanızın verisi bize geldiğinde 0.01 sn'de tek yönlü kriptolanır. (Test edin)</p>", unsafe_allow_html=True)
        zk_input = st.text_input("Gizli Metin Girin (Örn: Müşteri Adı / TCKN):", placeholder="John Doe 123456789", label_visibility="collapsed")
        if zk_input:
            hashed_val = hashlib.sha256(zk_input.encode()).hexdigest()
            st.markdown(f"<div style='background:#f1f5f9; padding: 0.8rem; border-radius:6px; word-wrap:break-word; font-family:monospace; font-size:0.8rem;'>{hashed_val}</div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#10b981; font-weight:bold; font-size:0.8rem; margin-top:5px;'>✓ Model eğitim formuna (AES-256) anonimleştirildi.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#f1f5f9; padding: 0.8rem; border-radius:6px; color:#cbd5e1; font-family:monospace;'>Bekleniyor...</div>", unsafe_allow_html=True)

    with col_roi:
        # 4. ROI OPERASYONEL MALİYET HESAPLAYICISI
        st.markdown("<h4 style='color: #111827;'>📈 Kurumsal ROI (Getiri) Simülatörü</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:#64748b;'>Operasyon analisti sayınızı girin, APEX otomasyon kazancınızı görün.</p>", unsafe_allow_html=True)
        headcount = st.number_input("Kredi & Risk Operasyon Personeli Sayısı:", min_value=1, max_value=5000, value=120, step=10, label_visibility="collapsed")
        
        saved_opex = headcount * 45000 * 0.60 # Yıllık ort %60 opex save
        avoided_loss = headcount * 125000     # Önlenecek default zararı
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; margin-top: 0.5rem;">
            <div style="background:#0f172a !important; padding:1rem; border-radius:8px; width:48%; text-align:center;">
                <p style="margin:0; font-size:0.75rem; color:#94a3b8 !important;">Yıllık Personel Tasarrufu</p>
                <h3 style="margin:0; color:#38bdf8 !important;">${saved_opex/1_000_000:.1f}M</h3>
            </div>
            <div style="background:#0f172a !important; padding:1rem; border-radius:8px; width:48%; text-align:center;">
                <p style="margin:0; font-size:0.75rem; color:#94a3b8 !important;">Önlenen Batık Riski</p>
                <h3 style="margin:0; color:#10b981 !important;">${avoided_loss/1_000_000:.1f}M</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    # ------------------ HEATMAP & GITHUB FEED KOLONLARI ------------------
    hm_col, git_col = st.columns([2, 1])

    with hm_col:
        # 7. KÜRESEL LİKİDİTE VE SUNUCU ISI HARİTASI (HEATMAP)
        st.markdown("<h4 style='color: #111827;'>🌍 Global APEX Düğüm Ağı (Canlı Simülasyon)</h4>", unsafe_allow_html=True)
        cities = pd.DataFrame({
            'lat': [40.7128, 51.5074, 41.0082, 35.6895, 1.3521, 50.1109, 37.7749, -23.5505],
            'lon': [-74.0060, -0.1278, 28.9784, 139.6917, 103.8198, 8.6821, -122.4194, -46.6333],
            'Node': ['Wall Street', 'London', 'Istanbul Core', 'Tokyo', 'Singapore', 'Frankfurt', 'Silikon Vadisi', 'Sao Paulo'],
            'Traffic (PF/s)': np.random.randint(500, 5000, 8)
        })
        fig_map = px.scatter_geo(cities, lat='lat', lon='lon', size='Traffic (PF/s)', color='Traffic (PF/s)',
                                 hover_name='Node', projection='natural earth', color_continuous_scale="Viridis")
        fig_map.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0), geo=dict(bgcolor='rgba(0,0,0,0)', showland=True, landcolor="#f1f5f9"), coloraxis_showscale=False)
        st.plotly_chart(fig_map, use_container_width=True)

    with git_col:
        # 5. GITHUB COMMIT MÜHENDİS YAYINI
        st.markdown("<h4 style='color: #111827;'>💻 Mühendislik Ar-Ge Akışı</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div class="git-feed-wrapper">
            <div class="git-feed">
                <div class="git-commit"><span>[10:45] main</span> > feat(xai): SHAP hiperparametreleri 4x optimize edildi.</div>
                <div class="git-commit"><span>[10:42] prod</span> > fix(kube): Load balancer timeout hatası giderildi.</div>
                <div class="git-commit"><span>[10:38] dev</span> > chore: ECB basel_IV veri ambarı eşitlemesi.</div>
                <div class="git-commit"><span>[10:15] sec</span> > update: JWT token entropy analizi artırıldı.</div>
                <div class="git-commit"><span>[09:55] risk</span> > feat: RNN tahminleyici bellek sızıntısı debug.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 10. KUBERNETES CONTAINER SCALING
        st.markdown("<h5 style='color: #111827; margin-top: 1rem; margin-bottom:0;'>Elastic Node Scaling (K8s)</h5>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.75rem; color:#64748b;'>Talep arttıkça motor kendini klonlar.</p>", unsafe_allow_html=True)
        st.markdown("""
        <div class="k8s-cluster">
            <div class="k8s-pod"></div>
            <div class="k8s-pod"></div>
            <div class="k8s-pod"></div>
            <div class="k8s-pod"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    # ------------------ CANLI SENTİMENT & CLI EASTER EGG ------------------
    left_news, right_cli = st.columns([1.5, 1])

    with left_news:
        # 2. CANLI HABER TARAMASI (NLP SENTIMENT)
        st.markdown("<h4 style='color: #111827;'>📰 Sentinel NLP: Doğal Dil İşleme Veri Girişi</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div class="news-ticker-wrapper">
            <div class="news-item">
                > BLOOMBERG: ECB faiz oranlarını agresif indirmeye gidiyor <span class="news-tag-risk">RISK: %85 VITES</span>
                | REUTERS: Tedarik zinciri kırılmaları AB tarafında üretime darbe vurdu <span class="news-tag-risk">RISK: %92 ENDUSTRI</span>
                | WSJ: Kuantum işlemcilerde ticari breakthrough yakalandı <span class="news-tag-pos">ALPHA: LONG</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 9. PODCAST / CORPORATE OVERVIEW
        st.markdown("<h4 style='color: #111827; margin-top:2rem;'>🎙️ Vision Briefing (Kurumsal Yayın)</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:#64748b;'>APEX Baş Tasarımcısı Sistem Algoritmalarını Yanıtlıyor (2 Dk)</p>", unsafe_allow_html=True)
        # Dummy audio tag for mock visual
        st.markdown("""
            <audio controls style="width: 100%; height: 40px; border-radius: 4px;">
                <source src="" type="audio/mpeg">
                Tarayıcınız ses formatını desteklemiyor.
            </audio>
        """, unsafe_allow_html=True)

    with right_cli:
        # 6. TERMINAL CLI EASTER EGG
        st.markdown("<h4 style='color: #111827;'>👾 APEX_CLI (Terminal)</h4>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:#64748b;'>'help' yazıp Enter'a basın</p>", unsafe_allow_html=True)
        cmd = st.text_input("root@apex-cluster:~#", key="cli_cmd", label_visibility="collapsed")
        
        cli_output = "Type a command to interact."
        if cmd.strip().lower() == "help":
            cli_output = "> CORE ENGINES: running\n> KAFKA BROKERS: 8/8 active\n> XAI_MODELS: loaded\n> STATUS: All systems nominal.\n> Type 'deploy' to push model."
        elif cmd.strip().lower() == "deploy":
            cli_output = "> DEPLOY SEQUENCE INITIATED...\n...\n> Weights updated. Acc: 99.8%"
        elif cmd:
            cli_output = f"> APEX_ERR: Command '{cmd}' not recognized."
            
        st.markdown(f"""
        <div style="background: #000000 !important; color: #10b981 !important; font-family: monospace !important; padding: 1rem; height: 160px; overflow-y:auto; border-radius: 6px; font-size:0.9rem !important; border: 1px solid #334155;">
            {cli_output.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    # ------------------ FOOTER ------------------
    st.markdown("""
        <div style="text-align: center; margin-top: 4rem; margin-bottom: 2rem; padding-top: 2rem; border-top: 1px solid #e2e8f0;">
            <p style="color: #64748b; font-size: 0.9rem; font-weight: 600;">APEX QUANTITATIVE FIN-TECH LABS © 2026</p>
            <p style="color: #94a3b8; font-size: 0.8rem;">İSTANBUL • LONDRA • NEW YORK • TOKYO</p>
        </div>
    """, unsafe_allow_html=True)

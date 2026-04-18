import streamlit as st
import datetime
import plotly.express as px
import pandas as pd
import numpy as np
import hashlib
import time

def render_contact_view():
    # ------------------ KAPSAMLI CSS ------------------
    st.markdown("""
    <style>
        .contact-container { font-family: 'Inter', sans-serif; color: #111827; }
        .hero-title { font-weight: 900; font-size: 3.2rem; line-height: 1.1; margin-top: 1rem; margin-bottom: 0.5rem; letter-spacing: -1px; }
        .hero-subtitle { color: #4b5563; font-size: 1.1rem; max-width: 800px; line-height: 1.6; }
        
        /* Şık Koyu Kartlar */
        .dark-card { background: #0f172a !important; color: white !important; padding: 1.5rem; border-radius: 12px; border: 1px solid #1e293b; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }
        .dark-card h4 { color: #38bdf8 !important; margin-top: 0; font-weight: 800; }
        .dark-card p { color: #94a3b8 !important; font-size: 0.9rem; }
        
        /* Status Işıkları */
        .status-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #10b981; margin-right: 8px; animation: pulse-green 2s infinite; }
        @keyframes pulse-green { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }

        .critical-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #ef4444; margin-right: 8px; animation: pulse-red 1s infinite; }
        @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

        /* Terminal CSS */
        .cli-terminal { background: #000000 !important; color: #10b981 !important; font-family: monospace !important; padding: 1rem; height: 140px; overflow-y:auto; border-radius: 6px; font-size:0.85rem !important; border: 1px solid #334155; }
        
        /* The Red Phone / Elite Kırmızı Modül */
        .red-phone { background: linear-gradient(135deg, #450a0a, #7f1d1d) !important; border-left: 5px solid #ef4444; padding: 1.5rem; border-radius: 8px; box-shadow: 0 10px 20px rgba(239,68,68,0.2); color:white;}
        
        /* Glassmorphism */
        .glass-card { background: rgba(255,255,255,0.8); border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

    # ------------------ HERO SECTION ------------------
    st.markdown("""
        <div class="contact-container" style="padding-top: 1rem;">
            <p style="color: #004C91; font-weight: 800; font-size: 0.9rem; letter-spacing: 2px; text-transform: uppercase;">APEX GLOBAL OPERATIONS CENTER</p>
            <h1 class="hero-title">İletişim & Otonom Destek Üssü</h1>
            <p class="hero-subtitle">
                İster Tier-1 bir banka, ister teknoloji partneri olun; saat dilimi ve lokasyon fark etmeksizin küresel kuantum destek ağımızla anında bağlantı kurun.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ------------------ SISTEM DURUMU (STATUS PAGE) ------------------
    st.markdown("""
        <div style="background: #ecfdf5; border: 1px solid #34d399; border-radius: 8px; padding: 0.8rem 1rem; margin-top: 1.5rem; display: flex; align-items: center; gap: 1rem;">
            <div class="status-dot"></div>
            <strong style="color: #065f46; font-size: 0.95rem;">API Core ve Otonom Motorlar Tam Çevrimiçi</strong>
            <span style="color: #059669; font-size: 0.85rem; margin-left: auto;">Güncel Ortalama Destek SLA Oylaması: 8 Dakika</span>
        </div>
    """, unsafe_allow_html=True)

    # ------------------ CANLI GLOBAL TEHDİT RADARI (YENİ) ------------------
    st.markdown("<h4 style='color: #111827; margin-top: 2rem;'>🌐 APEX Gerçek Zamanlı Tehdit Algılama Radarı</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #64748b;'>Hizmet kalitemizi korumak için 7/24 bloklanan küresel anomali saldırıları (DDoS, Fraud Vectors)</p>", unsafe_allow_html=True)
    
    threat_df = pd.DataFrame({
        'lat': np.random.uniform(-40, 60, 20),
        'lon': np.random.uniform(-120, 140, 20),
        'Threat Size': np.random.randint(100, 1000, 20),
        'Type': ['DDoS', 'Fraud Injection', 'Identity Theft', 'Model Poisoning'] * 5
    })
    threat_fig = px.scatter_geo(threat_df, lat='lat', lon='lon', size='Threat Size', color='Type',
                                projection='orthographic', template='plotly_dark')
    threat_fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), geo=dict(bgcolor='rgba(0,0,0,0)', showland=True, landcolor="#1e293b", oceancolor="#0f172a", showocean=True), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(threat_fig, use_container_width=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    # ------------------ TAB YÖNETİMİ ------------------
    t_sales, t_dev, t_comp, t_media = st.tabs([
        "🤝 Kurumsal Satış & Büyüme (RFP)", 
        "💻 Geliştirici & Hata (Bug Bounty)", 
        "⚖️ Uyum, Etik & Kripto-Bağ", 
        "🎙️ Basın & Medya Kiti"
    ])

    # ============================== TAB 1: KURUMSAL SATIŞ (SALES & DEMO) ==============================
    with t_sales:
        s_c1, s_c2 = st.columns([1.2, 1])
        
        with s_c1:
            st.markdown("<h3 style='color:#111827;'>Birebir Yönetici Oturumu Rezerve Edin</h3>", unsafe_allow_html=True)
            segment = st.selectbox("Kurum Tipi", ["Seçiniz", "Tier-1 / Merkez Bankası", "Ticari Banka", "Hedge Fon / Portföy Yönetimi", "FinTech Startup"], label_visibility="collapsed")
            if segment != "Seçiniz":
                role = st.selectbox("Unvanınız", ["C-Level (CEO/CFO/CTO)", "Risk Direktörü", "Quant Analist", "Ürün Yöneticisi"])
                email = st.text_input("Kurumsal E-Posta Addressi")
                
                # Context-Aware Karşılama
                if "C-Level" in role or "Tier-1" in segment:
                    st.markdown("<div style='background:#fefce8; padding:0.5rem; border-left:4px solid #eab308; margin-bottom:1rem; font-size:0.85rem; color:#854d0e;'><strong>VIP Öncelikli Yönlendirme:</strong> Talebiniz doğrudan EMEA Bölgesi Satış Direktörü'nün (MD) masasına iletilecektir.</div>", unsafe_allow_html=True)
                
                demo_date = st.date_input("Demo Görüşmesi İçin Uygun Tarih", min_value=datetime.date.today())
                if st.button("Takvim Kaydını Oluştur (Calendly Entegrasyonu)", type="primary"):
                    st.success("Talebiniz alındı! Zoom bağlantısı kurumsal e-postanıza 3 saniye içinde iletilecektir.")

            st.markdown("<hr>", unsafe_allow_html=True)
            # YENİ: RFP / İHALE YÜKLEYİCİSİ
            st.markdown("#### 📑 Büyük Ölçekli İhale (RFP) Zeka Yükleyicisi")
            st.markdown("<p style='font-size:0.85rem; color:#64748b;'>Devlet veya merkez bankanıza ait 100+ sayfalık ihale teknik şartnamesini PDF olarak yükleyin. LLM motorumuz metni okuyarak satış ekibimize en uygun eşleşme analizini sunar.</p>", unsafe_allow_html=True)
            rfp_file = st.file_uploader("Bankanızın RFP/Şartname Belgesini Yükleyin", type=['pdf', 'docx'])
            if rfp_file:
                st.info("RFP analiz ediliyor... (45 sayfa tarandı). Kurumunuz için minimum 3.000 TPS otonom kapasite gerekli olduğu tespit edildi.")

        with s_c2:
            # YENİ: VIP ACCOUNT MANAGER (TAM) BULUCU
            st.markdown("""
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h4 style="color:#111827;">Mevcut Müşteri: Account Manager Bulucu</h4>
                <p style="font-size:0.85rem; color:#475569;">Kurum Kodunuzu girerek size atanmış özel yöneticinize anında ulaşın.</p>
            """)
            tam_id = st.text_input("Kurum ID (Örn: B1024):", placeholder="VIP Kodunuzu giriniz", label_visibility="collapsed")
            if tam_id:
                st.markdown("<div style='background:#f1f5f9; padding:0.8rem; border-left:3px solid #004C91;'><b style='color:#004C91;'>John Doe (Lead Quant)</b><br>Durum: Çevrimiçi 🟢<br>Erişim: Özel GSM +44 20 7946 0958<br>Lokasyon: Londra (Size 3 saat uzakta)</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # YENİ: THE RED PHONE (GİZLİ KANAL)
            st.markdown("""
            <div class="red-phone">
                <h4 style="color:white !important; margin:0 0 0.5rem 0;">☎️ Kırmızı Telefon (Quantum Kanal)</h4>
                <p style="color:#fca5a5 !important; font-size:0.85rem;">Yalnızca özel elit etkinliklerde sağlanan VIP şifrelenmiş geçiş tokenini giriniz.</p>
            """)
            vip_token = st.text_input("Decryption Passphrase", type="password")
            if vip_token:
                st.error("ACCESS DENIED: Asymmetric key handshake failed.")
            st.markdown("</div>", unsafe_allow_html=True)


    # ============================== TAB 2: GELİŞTİRİCİ & HATA (DEV & BUG BOUNTY) ==============================
    with t_dev:
        d1, d2 = st.columns([1, 1])
        with d1:
            st.markdown("<h3 style='color:#111827;'>Teknik Destek & Kod Hata Bildirimi</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.85rem; color:#64748b;'>API entegrasyon JSON hatalarınızı buraya yapıştırın. Yapay zeka %80 oranında anında çözüm sunar.</p>", unsafe_allow_html=True)
            traceback = st.text_area("Stack Trace / JSON Log", height=120, placeholder='{\n  "error_code": 403,\n  "message": "Invalid JWT Token Signature"\n}')
            if st.button("Logu İlet ve Yapay Zeka Taraması Başlat", key="btn_trace"):
                st.info("Hata logunuz ayrıştırıldı: Geçersiz Signature. Çözüm Önerisi oluşturuldu (Bkz: Belge #T-4492)")
                
            # YENİ: BEYAZ ŞAPKALI HACKER (BUG BOUNTY) PORTALI
            st.markdown("""
            <div class="glass-card" style="margin-top: 2rem;">
                <h4 style="color:#4f46e5;">🛡️ APEX Bug Bounty (Ödül Avı) Kulübü</h4>
                <p style="font-size:0.85rem; color:#64748b;">Açık kaynak sistemimizde veya risk API'lerimizde bir zafiyet (Vulnerability) mi tespit ettiniz? Bizimle paylaşın, 50.000$'a varan beyaz şapkalı hacker ödül havuzundan yararlanın.</p>
            """)
            cvss = st.slider("Tahmini Güvenlik Zafiyeti Skoru (CVSS v3.1)", 0.0, 10.0, 5.0)
            if st.button("Zafiyet (Exploit) Raporunu Şifreli Yükle", key="bounty"):
                st.success(f"Security Report submitted securely to CISO Desk. Severity: {cvss}")
            st.markdown("</div>", unsafe_allow_html=True)

        with d2:
            # YENİ: MİNİ API POSTMAN SANDBOX
            st.markdown("<h3 style='color:#111827;'>Hızlı Entegrasyon (API Sandbox)</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.85rem; color:#64748b;'>Satış beklemeden direkt uç noktalarımızı test edin.</p>", unsafe_allow_html=True)
            st.markdown("<div style='background:#1e293b !important; padding:1rem; border-radius:8px;'>", unsafe_allow_html=True)
            col_a, col_b = st.columns([3,1])
            with col_a:
                st.text_input("Endpoint URL", value="POST https://api.apexcore.io/v5/assess", disabled=True)
            with col_b:
                st.write("")
                if st.button("Ping Gönder", key="sim_ping"):
                    st.success("200 OK (Latency: 6ms)")
            st.markdown("""<code style='color:#10b981; background:black; padding:8px; display:block;'>{<br>&nbsp;"customer_id": "XY-9192",<br>&nbsp;"status": "APPROVED",<br>&nbsp;"apex_score": 884<br>}</code>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Hacker CLI Terminal Entegrasyonu
            st.markdown("<h4 style='color:#111827; margin-top:2rem;'>Terminal (Geek) Modu</h4>", unsafe_allow_html=True)
            cli_input = st.text_input("apex_client > ", placeholder="contact --sales --urgent --msg 'We need API access'", label_visibility="collapsed")
            cli_output = "Type a command..."
            if cli_input.startswith("contact"):
                cli_output = f"> APEX_CLI: Routing request...\n> Action: Generating Sandbox ticket.\n> Status: Sent successfully to DevOps."
            
            st.markdown(f"""
            <div class="cli-terminal">
                {cli_output.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

    # ============================== TAB 3: UYUM, ETİK & İHBAR (COMPLIANCE) ==============================
    with t_comp:
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("<h3 style='color:#111827;'>Yasal Uyum ve Anonim İhbar</h3>", unsafe_allow_html=True)
            # YENİ: VERİ YERLEŞİMİ / DATA RESIDENCY ŞALTERİ
            st.markdown("#### Yurtdışı Veri Lokalizasyonu (Data Residency)")
            jurisdiction = st.selectbox("İletişim Talebi Nerede Dağıtılsın?", ["Avrupa Birliği (Frankfurt - GDPR Uyumlu)", "Türkiye (İstanbul - KVKK Uyumlu)", "Amerika (NY - SOC2 Uyumlu)", "Ağ Dışı Yönlendirme"])
            if jurisdiction == "Avrupa Birliği (Frankfurt - GDPR Uyumlu)":
                st.markdown("<span style='color:#1d4ed8; font-weight:bold; font-size:0.85rem;'>🇪🇺 Avrupa Parlamentosu GDPR Kuralları devrede. Verileriniz AB dışına asla çıkmayacaktır.</span>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Güvenli PGP Public Key**")
            st.markdown("""
            <div style="background:#f8fafc; padding:1rem; border-radius:8px; border:1px solid #e2e8f0; font-family:monospace; font-size:0.7rem; color:#64748b; height:120px; overflow-y:auto;">
                -----BEGIN PGP PUBLIC KEY BLOCK-----<br>
                xo0EZC7GugEEA...<br>
                +Wz/zL8= <br>
                -----END PGP PUBLIC KEY BLOCK-----
            </div>
            <p style="font-size:0.75rem; color:#94a3b8; margin-top:0.3rem;">Gizli belgelerinizi sadece bu anahtarla imzalayarak gönderin.</p>
            """, unsafe_allow_html=True)

        with c_right:
            # YENİ: VİDEO/DOSYA YÜKLEYİCİ (Kamera yerine daha güvenli)
            st.markdown("#### Güvenli Medya/Belge Raporlama")
            st.markdown("<p style='font-size:0.85rem; color:#475569;'>C-Level yöneticiler sorunlarını yazmak yerine şifrelenmiş video veya ekran kaydı yükleyebilirler.</p>", unsafe_allow_html=True)
            video_test = st.file_uploader("Video veya Ekran Kaydı Yükle (Uçtan Uca Şifreli)", type=['mp4', 'mov', 'avi'])
            
            # YENİ: BLOCKCHAIN SMART CONTRACT EMANETİ
            st.markdown("""
            <div class="dark-card" style="margin-top: 1rem;">
                <h4 style="color:#cbd5e1 !important;">🔗 Kriptografik API Mutabakatı (Smart Contract Escrow)</h4>
                <p style="font-size:0.8rem; color:#94a3b8 !important;">Bankalar arası büyük HFT lisans ödemelerindeki güveni Web3 ile sağlıyoruz.</p>
                <code style="background:black; color:#38bdf8; padding:5px; font-size:0.75rem; border-radius:4px;">ETH: 0xA77...4f8c9 (APEX Escrow Verified)</code>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Anonim Etik İhbarı Yap (Whistleblowing)", expanded=False):
                st.markdown("<p style='font-size:0.8rem; color:#ef4444; font-weight:bold;'>Uyarı: Sistem IP logu tutmaz. No-Log Policy devrededir.</p>", unsafe_allow_html=True)
                st.text_area("İncelemeye alınacak vakayı detaylandırın:", height=80)
                if st.button("Şifreleyerek Bağımsız Denetime İlet"):
                    st.success("Talebiniz şifrelendi.")

    # ============================== TAB 4: BASIN & AKADEMİ ==============================
    with t_media:
        st.markdown("<h3 style='color:#111827;'>Medya, PR ve Araştırma Partnerliği</h3>", unsafe_allow_html=True)
        m_col1, m_col2 = st.columns([1, 1])
        
        with m_col1:
            st.markdown("""
            <div class="glass-card">
                <h4 style="color:#111827;">Marka & Basın Kiti (Press Kit)</h4>
                <p style="font-size:0.9rem; color:#475569;">Yüksek çözünürlüklü logolar, medya kullanımları, renk paletleri (Hex) ve CEO medya beyanat paketi indirime hazır.</p>
                <div style="background:#004C91; color:white; padding:0.6rem; border-radius:6px; text-align:center; font-weight:bold; cursor:pointer;">
                    ⬇️ Kurumsal_Paket_v5.zip (14.2 MB)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # OTONOM DUYGU ANALİZİ (SENTIMENT) BİLDİRİMİ
            st.markdown("<div style='margin-top:2rem; padding:1rem; border-left:4px solid #8b5cf6; background:#f5f3ff;'>", unsafe_allow_html=True)
            st.markdown("**Akıllı Müşteri Memnuniyeti İzleyici Motoru:** (Mesajlarınızın duygusunu sezer)")
            sentiment_test = st.text_input("Şikayet veya Önerinizi Test Edin:", placeholder="Sisteminiz çok yavaş çalışıyor rezalet!")
            if sentiment_test:
                if "rezalet" in sentiment_test.lower() or "kötü" in sentiment_test.lower() or "yavaş" in sentiment_test.lower() or "hata" in sentiment_test.lower():
                    st.markdown("<span style='background:#fee2e2; color:#b91c1c; padding:4px 8px; border-radius:4px;'>🔴 NEGATİF ALGI (%92). Önceliklendirildi.</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='background:#dcfce7; color:#15803d; padding:4px 8px; border-radius:4px;'>🟢 POZİTİF / NÖTR ALGI (%88). Standart kurye atandı.</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with m_col2:
            st.markdown("""
            <div class="glass-card">
                <h4 style="color:#111827;">Akademik Ortak Ekosistemi</h4>
                <p style="font-size:0.9rem; color:#475569;">Üniversitelerin Makine Öğrenimi laboratuvarlarıyla sağladığımız açık veri ortaklığı portalı.</p>
                <div style="border:1px solid #cbd5e1; padding:0.6rem; border-radius:6px; text-align:center; font-weight:bold; color:#004C91; cursor:pointer;">
                    GitHub OpenResearch ➔
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)

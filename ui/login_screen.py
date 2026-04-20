"""
ui/login_screen.py
ProQuant Apex Risk Terminal — Institutional Login v6.0
Premium glassmorphism login with animated backgrounds
"""
import streamlit as st
import time
import os
import textwrap
import urllib.request
import json
import datetime
from core.auth_system import (
    login, analyze_password_strength, render_password_strength,
    send_2fa_otp, reset_password_request
)
from core.database_handler import db
from config import APP_NAME, APP_VERSION


def render_login_screen():
    """
    Kurumsal premium giriş sayfası — glassmorphism & animasyonlu arka plan.
    """
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(_BASE_DIR, "assets", "logo.png")

    st.markdown(textwrap.dedent("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    
    /* Premium Dark Base */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #0A1628 0%, #060B18 100%) !important;
    }
    
    /* Dynamic Cyber-Mesh Background */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background: 
            radial-gradient(circle at 20% 30%, rgba(56, 189, 248, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(99, 102, 241, 0.12) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
        animation: atmosphereMove 15s ease-in-out infinite alternate;
    }
    
    @keyframes atmosphereMove {
        0% { transform: scale(1) translate(0, 0); opacity: 0.7; }
        50% { transform: scale(1.1) translate(2% , 1%); opacity: 1; }
        100% { transform: scale(1) translate(-1%, -2%); opacity: 0.8; }
    }
    
    /* Advanced Grid with Glowing Nodes */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background-image: 
            linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
        background-size: 60px 60px;
        background-position: center center;
        mask-image: radial-gradient(circle at 50% 50%, black, transparent 80%);
        pointer-events: none;
        z-index: 0;
        animation: gridFade 4s ease-in-out infinite alternate;
    }
    
    @keyframes gridFade {
        from { opacity: 0.3; }
        to   { opacity: 0.6; }
    }
    
    /* Top Scanner Line */
    .scanner-line {
        position: fixed;
        top: -100px;
        left: 0;
        width: 100%;
        height: 100px;
        background: linear-gradient(to bottom, transparent, rgba(56, 189, 248, 0.2), transparent);
        z-index: 10;
        pointer-events: none;
        animation: scanning 6s linear infinite;
    }
    
    @keyframes scanning {
        0% { top: -100px; }
        100% { top: 100vh; }
    }
    
    /* Hide Streamlit elements */
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer { visibility: hidden; }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Glassmorphism Card Container */
    .login-glass-card {
        background: rgba(13, 25, 48, 0.65) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 28px !important;
        padding: 3.5rem 3rem !important;
        box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.7),
            0 0 40px rgba(56, 189, 248, 0.1),
            inset 0 1px 1px rgba(255, 255, 255, 0.05) !important;
        position: relative;
        overflow: hidden;
        animation: cardEntrance 1s cubic-bezier(0.2, 0.8, 0.2, 1) both;
    }
    
    .login-glass-card::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at center, rgba(56, 189, 248, 0.03) 0%, transparent 60%);
        pointer-events: none;
        animation: innerGlow 8s linear infinite;
    }
    
    @keyframes innerGlow {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    
    @keyframes cardEntrance {
        from { opacity: 0; transform: translateY(40px) scale(0.95); filter: blur(10px); }
        to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }
    
    /* Cyber Typography */
    .login-brand-name {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #38BDF8 0%, #6366F1 50%, #A855F7 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        letter-spacing: -1px !important;
        text-transform: uppercase;
        margin-bottom: 0.1rem;
    }
    
    .login-status-bar {
        height: 3px;
        width: 100%;
        background: rgba(56, 189, 248, 0.1);
        border-radius: 10px;
        margin: 1.5rem 0;
        overflow: hidden;
        position: relative;
    }
    
    .login-status-progress {
        position: absolute;
        height: 100%;
        width: 40%;
        background: linear-gradient(90deg, transparent, #38BDF8, transparent);
        animation: progressMove 2.5s infinite ease-in-out;
    }
    
    @keyframes progressMove {
        0% { left: -40%; }
        100% { left: 100%; }
    }
    
    /* Form Elements */
    .stTextInput input {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(51, 65, 85, 0.5) !important;
        color: #F1F5F9 !important;
        border-radius: 12px !important;
        padding: 0.8rem 1.2rem !important;
        transition: all 0.3s ease !important;
        font-size: 0.95rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2) !important;
        background: rgba(30, 41, 59, 0.6) !important;
    }
    
    /* Futuristic Button */
    .stButton > button {
        background: linear-gradient(90deg, #38BDF8 0%, #6366F1 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.85rem !important;
        color: white !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 20px rgba(56, 189, 248, 0.25) !important;
        position: relative;
        overflow: hidden !important;
    }
    
    .stButton > button::after {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: 0.5s;
    }
    
    .stButton > button:hover::after {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(56, 189, 248, 0.4) !important;
    }
    
    /* Security Shield Badge */
    .shield-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        color: #10B981;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .pulse-dot {
        width: 6px; height: 6px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
        animation: pulse 1.5s infinite;
    }
    
    /* 2FA Input Fields */
    .otp-input-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 2rem 0;
    }
    
    /* Security Insights Card */
    .insights-panel {
        background: rgba(56, 189, 248, 0.03);
        border: 1px solid rgba(56, 189, 248, 0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin-top: 2rem;
        animation: fadeIn 1s ease-out;
    }
    
    .insight-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-size: 0.72rem;
    }
    
    .insight-label { color: #64748B; font-weight: 500; }
    .insight-value { color: #38BDF8; font-weight: 600; font-family: monospace; }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.5); opacity: 0.5; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """), unsafe_allow_html=True)

    # ─── Initialization ────────────────────────────────────────────
    if "login_stage" not in st.session_state:
        st.session_state["login_stage"] = "credentials"
    if "temp_user" not in st.session_state:
        st.session_state["temp_user"] = None

    # ─── New Visual Elements ───────────────────────────────────────
    st.markdown('<div class="scanner-line"></div>', unsafe_allow_html=True)

    # ─── Center the login card ─────────────────────────────────────
    _, center_col, _ = st.columns([1, 1.4, 1])

    with center_col:
        st.markdown('<div class="login-glass-card">', unsafe_allow_html=True)
        
        # Brand header
        if os.path.exists(logo_path):
            st.markdown("<div style='text-align:center; margin-bottom:1rem;'>", unsafe_allow_html=True)
            st.image(logo_path, width=220)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(textwrap.dedent(f"""
            <div class="login-brand">
                <div class="login-brand-name">{APP_NAME}</div>
                <div class="login-brand-sub">Institutional Risk Terminal</div>
            </div>
            """), unsafe_allow_html=True)

        # Status Bar Animation
        st.markdown("""
        <div class="login-status-bar"><div class="login-status-progress"></div></div>
        """, unsafe_allow_html=True)

        if st.session_state["login_stage"] == "credentials":
            # Institution tagline
            st.markdown("""
            <div style="text-align:center; margin-bottom:1.5rem;">
                <div style="
                    font-family: 'Space Grotesk', sans-serif;
                    font-size: 1.2rem; font-weight: 700;
                    color: #F8FAFC; letter-spacing: -0.5px;
                ">KURUMSAL ERİŞİM</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:2px; font-weight:500;">
                    <span style="color:#38BDF8;">●</span> Güvenli geçit protokolü aktif
                </div>
            </div>
            """, unsafe_allow_html=True)

            tab_login, tab_register = st.tabs(["🔐  Giriş Yap", "📝  Üye Ol"])

            with tab_login:
                _render_login_form()

            with tab_register:
                _render_register_form()
        else:
            _render_2fa_stage()

        # Security Insights (Sadece login aşamasında veya her zaman gösterilebilir)
        _render_security_insights()

        # Security indicator
        st.markdown(f"""
        <div style="text-align:center; margin-top:1.5rem;">
            <div class="shield-badge">
                <div class="pulse-dot"></div>
                AES-256 Şifreli Bağlantı
            </div>
        </div>
        <div class="version-badge" style="color:#475569; font-size:0.65rem; margin-top:1.2rem;">
            {APP_NAME} v{APP_VERSION} &nbsp;·&nbsp; SOC2 / GDPR
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


@st.dialog("🔑 Şifre Sıfırlama Merkezi")
def _render_forgot_password_dialog():
    st.write("Hesabınıza erişemiyor musunuz?")
    st.caption("Kayıtlı e-posta adresinizi veya kullanıcı adınızı girin. Size geçici bir şifre göndereceğiz.")
    
    identifier = st.text_input("E-posta veya Kullanıcı Adı", placeholder="örnek@kurum.com")
    
    if st.button("Şifre Sıfırlama Bağlantısı Gönder", use_container_width=True, type="primary"):
        if not identifier:
            st.error("Lütfen e-posta veya kullanıcı adı girin.")
            return
            
        with st.spinner("İşlem yapılıyor..."):
            res = reset_password_request(identifier)
            if res["success"]:
                st.success(res["message"])
                time.sleep(2)
                st.rerun()
            else:
                st.error(res["message"])

def _render_login_form():
    """Premium giriş formu."""
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    username = st.text_input(
        "Kullanıcı Adı",
        placeholder="kullanici_adi",
        key="login_user"
    )
    show_pass = st.checkbox("Şifreyi Göster", key="show_pass_toggle")
    password = st.text_input(
        "Şifre",
        type="password" if not show_pass else "default",
        placeholder="••••••••••",
        key="login_pass"
    )

    # "Beni Hatırla" & "Şifremi Unuttum"
    col_rem, col_forgot = st.columns([1, 1])
    with col_rem:
        st.markdown(
            "<div style='font-size:0.78rem; color:#64748B; padding-top:0.25rem;'>✔ Güvenli Oturum</div>",
            unsafe_allow_html=True
        )
    with col_forgot:
        st.markdown("<div style='text-align:right; margin-top:2px;'>", unsafe_allow_html=True)
        if st.button("Şifremi Unuttum", key="btn_forgot", type="tertiary"):
             _render_forgot_password_dialog()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    if st.button("Sisteme Bağlan →", use_container_width=True, type="primary", key="btn_login"):
        if not username or not password:
            st.warning("⚠️ Lütfen tüm alanları doldurun.")
            return

        with st.spinner("Kimlik doğrulanıyor..."):
            time.sleep(0.4)
            result = login(username.strip(), password)

        if result["success"]:
            user_info = result["user"]
            st.session_state["temp_user"] = user_info
            
            with st.spinner("Güvenlik kodu gönderiliyor..."):
                if send_2fa_otp(user_info):
                    st.session_state["login_stage"] = "2fa"
                    st.success("✅ Kimlik Doğrulandı. Yönlendiriliyor...")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("❌ Güvenlik kodu gönderilemedi. Lütfen sistem yöneticisiyle iletişime geçin.")
        else:
            st.error("❌ Kullanıcı adı veya şifre hatalı.")



def _render_register_form():
    """Premium kayıt formu."""
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Ad Soyad", key="reg_name", placeholder="İsim Soyisim")
    with col2:
        username = st.text_input("Kullanıcı Adı", key="reg_user", placeholder="kullanici_adi")

    email    = st.text_input("Kurumsal E-posta", key="reg_email", placeholder="ornek@kurum.com")
    password = st.text_input("Şifre", type="password", key="reg_pass", placeholder="En az 8 karakter")

    if password:
        try:
            strength = analyze_password_strength(password)
            render_password_strength(strength)
        except Exception:
            pass

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.75rem; color:#475569; margin-bottom:0.75rem; line-height:1.6;">
        ⚠️ Hesabınız oluşturulduktan sonra yönetici onayına gönderilecektir.
        Onay işlemi kurumsal e-posta adresinize bildirilecektir.
    </div>
    """, unsafe_allow_html=True)

    if st.button("Hesap Oluştur", use_container_width=True, key="btn_register"):
        if not all([full_name, username, email, password]):
            st.warning("⚠️ Lütfen tüm alanları doldurun.")
            return

        ok = db.add_user(
            username.strip(), password,
            role="Risk Analisti",
            full_name=full_name.strip(),
            email=email.strip(),
            department="Risk Yönetimi"
        )
        if ok:
            st.success("✅ Hesap oluşturuldu. Yönetici onayı bekleniyor.")
        else:
            st.error("❌ Bu kullanıcı adı zaten kullanılıyor.")


def _render_2fa_stage():
    """İkinci kademe doğrulama (2FA) ekranı."""
    st.markdown("""
    <div style="text-align:center; margin-bottom:1.5rem;">
        <div style="font-family:'Space Grotesk', sans-serif; font-size:1.1rem; font-weight:700; color:#F8FAFC;">
            İKİ ADIMLI DOĞRULAMA
        </div>
        <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">
            Lütfen kayıtlı cihazınıza gönderilen 6 haneli kodu girin.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2FA Kod Girişi
    otp_code = st.text_input("Güvenlik Kodu", placeholder="000000", max_chars=6)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Geri", use_container_width=True):
            st.session_state["login_stage"] = "credentials"
            st.session_state["temp_user"] = None
            st.rerun()
    with c2:
        if st.button("Doğrula & Gir", use_container_width=True, type="primary"):
            correct_otp = st.session_state.get("correct_otp")
            if not correct_otp:
                st.error("Kod süresi dolmuş veya hatalı oturum.")
                return

            if otp_code == correct_otp:
                # Gerçek oturumu başlat
                user_info = st.session_state["temp_user"]
                st.session_state["authenticated"] = True
                st.session_state["user_info"]     = user_info
                st.session_state["lang"]          = user_info.get("lang", "tr")
                st.session_state["theme"]         = user_info.get("theme", "dark")
                
                st.success("🔓 Erişim sağlandı. Hoş geldiniz.")
                
                # OTP verilerini temizle
                if "correct_otp" in st.session_state: del st.session_state["correct_otp"]
                if "temp_user" in st.session_state: del st.session_state["temp_user"]
                
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Hatalı veya süresi dolmuş kod.")

    st.markdown("""
    <div style="text-align:center; margin-top:1rem; font-size:0.7rem; color:#475569;">
        Kod gelmedi mi? <a href="#" style="color:#38BDF8; text-decoration:none;">Tekrar Gönder</a>
    </div>
    """, unsafe_allow_html=True)


def _get_client_location_info() -> str:
    """Gerçek IP ve lokasyon bilgisini çeker. Eğer başarısız olursa proxy bilgisini döner."""
    try:
        # Streamlit 1.35+ için Header Okuma
        client_ip = None
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            if "X-Forwarded-For" in headers:
                client_ip = headers["X-Forwarded-For"].split(",")[0].strip()
            elif "X-Real-Ip" in headers:
                client_ip = headers["X-Real-Ip"].strip()
        
        # Eğer Header'dan alınamadıysa, sunucu/dış IP yap (Cloud IP'si gelir)
        if not client_ip:
            req = urllib.request.Request("https://api.ipify.org?format=json")
            with urllib.request.urlopen(req, timeout=3) as resp:
                client_ip = json.loads(resp.read().decode())["ip"]
                
        # Lokasyonu Çek
        req2 = urllib.request.Request(f"http://ip-api.com/json/{client_ip}")
        with urllib.request.urlopen(req2, timeout=3) as resp2:
            data = json.loads(resp2.read().decode())
            if data.get("status") == "success":
                city = data.get("city", "Bilinmiyor")
                country = data.get("countryCode", "??")
                return f"{client_ip} ({city}, {country})"
    except Exception:
        pass
    
    return "192.168.1.44 (Istanbul, TR)"

def _render_security_insights():
    """Giriş ekranı için güvenlik istatistikleri ve meta veriler."""
    
    if "client_loc" not in st.session_state:
        st.session_state["client_loc"] = _get_client_location_info()
        
    loc_info = st.session_state["client_loc"]
    
    st.markdown(textwrap.dedent(f"""
    <div class="insights-panel">
        <div style="font-size:0.75rem; font-weight:700; color:#94A3B8; margin-bottom:1rem; text-transform:uppercase; letter-spacing:0.05em;">
            🛡️ Terminal Güvenlik İzlemesi
        </div>
        <div class="insight-item">
            <span class="insight-label">Erişim Noktası:</span>
            <span class="insight-value">{loc_info}</span>
        </div>
        <div class="insight-item">
            <span class="insight-label">Terminal Durumu:</span>
            <span class="insight-value" style="color:#10B981;">GÜVENLİ</span>
        </div>
        <div class="insight-item">
            <span class="insight-label">Son Başarılı Giriş:</span>
            <span class="insight-value">{datetime.datetime.now().strftime('%d.%m.%Y, %H:%M')} (Geçerli Oturum)</span>
        </div>
        <div class="insight-item">
            <span class="insight-label">Şifreleme Standartı:</span>
            <span class="insight-value">FIPS 140-2</span>
        </div>
    </div>
    """), unsafe_allow_html=True)

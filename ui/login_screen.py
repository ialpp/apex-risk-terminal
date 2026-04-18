"""
ui/login_screen.py
ProQuant Apex Risk Terminal — Institutional Login v6.0
Premium glassmorphism login with animated backgrounds
"""
import streamlit as st
import time
import os
from core.auth_system import login, analyze_password_strength, render_password_strength
from core.database_handler import db
from config import APP_NAME, APP_VERSION


def render_login_screen():
    """
    Kurumsal premium giriş sayfası — glassmorphism & animasyonlu arka plan.
    """
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(_BASE_DIR, "assets", "logo.png")

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Login page specific dark background */
    .stApp {
        background: #060B18 !important;
    }


    /* Animated gradient orbs */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse 60% 50% at 20% 20%, rgba(56, 189, 248, 0.12) 0%, transparent 60%),
            radial-gradient(ellipse 50% 60% at 80% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 60%),
            radial-gradient(ellipse 40% 40% at 50% 50%, rgba(139, 92, 246, 0.05) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
        animation: orbFloat 8s ease-in-out infinite alternate;
    }
    @keyframes orbFloat {
        from { opacity: 0.7; transform: scale(1); }
        to   { opacity: 1;   transform: scale(1.05); }
    }

    /* Grid pattern overlay */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(56, 189, 248, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56, 189, 248, 0.04) 1px, transparent 1px);
        background-size: 48px 48px;
        pointer-events: none;
        z-index: 0;
    }

    /* Hide streamlit chrome */
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer { visibility: hidden; }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Login wrapper */
    .login-page-wrapper {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        position: relative;
        z-index: 1;
    }

    /* Glass card */
    .login-glass-card {
        width: 100%;
        max-width: 440px;
        background: rgba(13, 31, 60, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 24px;
        padding: 3rem 2.5rem;
        box-shadow:
            0 32px 80px rgba(0, 0, 0, 0.6),
            0 0 0 1px rgba(56, 189, 248, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(32px);
        animation: cardIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    @keyframes cardIn {
        from { opacity: 0; transform: translateY(24px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0)   scale(1); }
    }

    /* Brand area */
    .login-brand {
        text-align: center;
        margin-bottom: 2.5rem;
    }
    .login-brand-name {
        font-size: 1.6rem;
        font-weight: 900;
        background: linear-gradient(135deg, #38BDF8, #6366F1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
    }
    .login-brand-sub {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 500;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }
    .login-divider {
        width: 40px;
        height: 2px;
        background: linear-gradient(90deg, #38BDF8, #6366F1);
        border-radius: 2px;
        margin: 0.75rem auto;
    }

    /* Tabs overrides for login */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: 1px solid rgba(56,189,248,0.1) !important;
        margin-bottom: 1.5rem !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.55rem 1.25rem !important;
        border-radius: 7px !important;
        border: none !important;
        background: transparent !important;
        flex: 1 !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38BDF8 !important;
        font-weight: 700 !important;
        border-bottom: none !important;
        box-shadow: 0 2px 8px rgba(56, 189, 248, 0.2) !important;
    }

    /* Input fields */
    .stTextInput input {
        background: rgba(255,255,255,0.05) !important;
        color: #E2E8F0 !important;
        border: 1.5px solid rgba(51, 65, 85, 0.8) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.9rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.25s ease !important;
    }
    .stTextInput input:focus {
        border-color: #38BDF8 !important;
        background: rgba(56, 189, 248, 0.05) !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.12) !important;
        outline: none !important;
    }
    .stTextInput input::placeholder {
        color: #475569 !important;
    }
    .stTextInput label {
        color: #94A3B8 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.03em !important;
    }

    /* Login button */
    .stButton > button {
        background: linear-gradient(135deg, #38BDF8 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 16px rgba(56, 189, 248, 0.3) !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 28px rgba(56, 189, 248, 0.45) !important;
        filter: brightness(1.05) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Alert overrides */
    .stSuccess  { background: rgba(16,185,129,0.1) !important; border-left: 4px solid #10B981 !important; border-radius: 10px !important; color: #D1FAE5 !important; }
    .stError    { background: rgba(244,63,94,0.1)  !important; border-left: 4px solid #F43F5E !important; border-radius: 10px !important; color: #FFE4E6 !important; }
    .stWarning  { background: rgba(245,158,11,0.1) !important; border-left: 4px solid #F59E0B !important; border-radius: 10px !important; color: #FEF3C7 !important; }

    /* Security badge */
    .security-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        margin-top: 2rem;
        color: #475569;
        font-size: 0.73rem;
        font-weight: 500;
        letter-spacing: 0.05em;
    }
    .security-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #10B981;
        animation: secPulse 2s ease infinite;
    }
    @keyframes secPulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.5; transform: scale(0.8); }
    }

    /* Version badge */
    .version-badge {
        text-align: center;
        margin-top: 1.5rem;
        color: #334155;
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 0.08em;
    }
    </style>
    """, unsafe_allow_html=True)

    # ─── Center the login card ─────────────────────────────────────
    _, center_col, _ = st.columns([1, 1.6, 1])

    with center_col:
        # Brand header
        if os.path.exists(logo_path):
            st.markdown("<div style='text-align:center; margin-bottom:1.5rem;'>", unsafe_allow_html=True)
            st.image(logo_path, width=240)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="login-brand">
                <div class="login-brand-name">{APP_NAME}</div>
                <div class="login-divider"></div>
                <div class="login-brand-sub">Institutional Risk Terminal</div>
            </div>
            """, unsafe_allow_html=True)

        # Institution tagline
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="
                font-size: 1.1rem; font-weight: 800;
                background: linear-gradient(135deg, #38BDF8, #6366F1);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text; letter-spacing: -0.3px;
            ">Kurumsal Erişim Paneli</div>
            <div style="font-size:0.78rem; color:#475569; margin-top:4px; font-weight:500;">
                Yetkili personel girişi — Tüm işlemler denetlenmektedir
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐  Giriş Yap", "📝  Üye Ol"])

        with tab_login:
            _render_login_form()

        with tab_register:
            _render_register_form()

        # Security indicator
        st.markdown(f"""
        <div class="security-badge">
            <span class="security-dot"></span>
            TLS 1.3 Şifrelemesi &nbsp;·&nbsp; 256-bit AES &nbsp;·&nbsp; SOC 2 Uyumlu
        </div>
        <div class="version-badge">
            {APP_NAME} &nbsp;v{APP_VERSION} &nbsp;·&nbsp; KVKK &amp; GDPR Compliant
        </div>
        """, unsafe_allow_html=True)


def _render_login_form():
    """Premium giriş formu."""
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    username = st.text_input(
        "Kullanıcı Adı",
        placeholder="kullanici_adi",
        key="login_user"
    )
    password = st.text_input(
        "Şifre",
        type="password",
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
        st.markdown(
            "<div style='text-align:right; font-size:0.78rem;'><a href='#' style='color:#38BDF8; text-decoration:none;'>Şifremi Unuttum</a></div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    if st.button("Sisteme Bağlan →", use_container_width=True, type="primary", key="btn_login"):
        if not username or not password:
            st.warning("⚠️ Lütfen tüm alanları doldurun.")
            return

        with st.spinner("Kimlik doğrulanıyor..."):
            time.sleep(0.4)
            result = login(username.strip(), password)

        if result["success"]:
            st.success("✅ Giriş başarılı — Yönlendiriliyor...")
            time.sleep(0.3)
            st.rerun()
        else:
            st.error("❌ Kullanıcı adı veya şifre hatalı.")

    st.markdown("""
    <div style="margin-top:1.5rem; padding:0.9rem 1rem;
                background: rgba(56,189,248,0.05);
                border: 1px solid rgba(56,189,248,0.12);
                border-radius: 10px;">
        <div style="font-size:0.73rem; color:#475569; font-weight:600; margin-bottom:0.4rem;">
            🔑 Demo Hesapları
        </div>
        <div style="font-size:0.72rem; color:#64748B; line-height:1.7;">
            <code style="color:#38BDF8;">admin</code> / <code style="color:#38BDF8;">admin123</code>
            &nbsp;&nbsp;&nbsp;
            <code style="color:#94A3B8;">analist</code> / <code style="color:#94A3B8;">analist123</code>
        </div>
    </div>
    """, unsafe_allow_html=True)


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

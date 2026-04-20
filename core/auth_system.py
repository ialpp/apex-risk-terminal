"""
core/auth_system.py
Kimlik Doğrulama & Oturum Yönetimi Sistemi
2FA, hesap kilitleme, şifre gücü kontrolü, rol bazlı erişim
"""

import streamlit as st
import time
import re
import random
import string
from datetime import datetime, timedelta
from core.database_handler import db
from core.email_service import send_otp_email, send_password_reset_email
from config import SESSION_TIMEOUT_MINS, PASSWORD_MIN_LENGTH, ROLES


# ─────────────────────────────────────────────
#  OTURUM BAŞLATMA
# ─────────────────────────────────────────────

def init_auth_state():
    """Tüm oturum değişkenlerini başlatır."""
    defaults = {
        "authenticated":    False,
        "user_info":        None,
        "login_attempts":   0,
        "last_activity":    datetime.now(),
        "lang":             "tr",
        "theme":            "dark",
        "current_page":     "dashboard",
        "onboarding_done":  False,
        "notifications":    [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ─────────────────────────────────────────────
#  GİRİŞ / ÇIKIŞ
# ─────────────────────────────────────────────

def login(username: str, password: str) -> dict:
    """
    Kullanıcı doğrulama.
    Dönüş:
      {"success": True, "user": {...}}
      {"success": False, "reason": "locked" | "invalid" | "inactive"}
    """
    result = db.verify_user(username, password)

    if result is None:
        return {"success": False, "reason": "invalid"}

    if isinstance(result, dict) and result.get("error") == "locked":
        return {"success": False, "reason": "locked", "until": result.get("until")}

    # Başarılı giriş
    st.session_state["authenticated"]  = True
    st.session_state["user_info"]      = result
    st.session_state["lang"]           = result.get("lang", "tr")
    st.session_state["theme"]          = result.get("theme", "dark")
    st.session_state["last_activity"]  = datetime.now()
    st.session_state["login_attempts"] = 0

    db.sys_log("INFO", f"Kullanıcı giriş yaptı: {username}", "auth_system", username)
    return {"success": True, "user": result}


def logout():
    """Tüm oturum verilerini temizler ve sayfayı yeniler."""
    user = st.session_state.get("user_info", {})
    uname = user.get("username", "?") if user else "?"
    db.sys_log("INFO", f"Kullanıcı çıkış yaptı: {uname}", "auth_system", uname)

    keys_to_clear = [
        "authenticated", "user_info", "login_attempts",
        "last_activity", "current_page"
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


# ─────────────────────────────────────────────
#  OTURUM ZAMAN AŞIMI
# ─────────────────────────────────────────────

def check_session_timeout():
    """Son aktiviteden bu yana SESSION_TIMEOUT_MINS geçtiyse oturumu kapatır."""
    if not is_authenticated():
        return
    last = st.session_state.get("last_activity", datetime.now())
    if (datetime.now() - last).seconds > SESSION_TIMEOUT_MINS * 60:
        st.warning("⏱️ Oturum zaman aşımına uğradı. Lütfen tekrar giriş yapın.")
        time.sleep(2)
        logout()


def touch_activity():
    """Her kullanıcı etkileşiminde son aktivite zamanını günceller."""
    st.session_state["last_activity"] = datetime.now()


# ─────────────────────────────────────────────
#  YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict | None:
    return st.session_state.get("user_info", None)


def get_user_role() -> str:
    user = get_current_user()
    return user["role"] if user else ""


def get_role_level() -> int:
    role = get_user_role()
    return ROLES.get(role, {}).get("level", 0)


def require_role(min_level: int) -> bool:
    """
    Belirli bir yetki seviyesi gerektirir.
    Yetki yoksa Streamlit'te hata mesajı gösterir ve False döner.
    """
    if get_role_level() < min_level:
        st.error("🚫 Bu işlem için yetkiniz bulunmamaktadır.")
        return False
    return True


# ─────────────────────────────────────────────
#  ŞİFRE GÜCÜ ANALİZİ
# ─────────────────────────────────────────────

def analyze_password_strength(password: str) -> dict:
    """
    Şifre gücünü 5 kritere göre analiz eder.
    Dönüş: {"score": 0-5, "label": str, "color": str, "tips": [str]}
    """
    score = 0
    tips = []

    if len(password) >= 8:
        score += 1
    else:
        tips.append("En az 8 karakter kullanın.")

    if re.search(r"[A-Z]", password):
        score += 1
    else:
        tips.append("En az 1 büyük harf ekleyin.")

    if re.search(r"[a-z]", password):
        score += 1
    else:
        tips.append("En az 1 küçük harf ekleyin.")

    if re.search(r"\d", password):
        score += 1
    else:
        tips.append("En az 1 rakam ekleyin.")

    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    else:
        tips.append("En az 1 özel karakter (@, !, # vb.) ekleyin.")

    labels = {
        0: ("Çok Zayıf", "#ef4444"),
        1: ("Zayıf",     "#f97316"),
        2: ("Orta",      "#f59e0b"),
        3: ("İyi",       "#84cc16"),
        4: ("Güçlü",     "#22c55e"),
        5: ("Mükemmel",  "#10b981"),
    }
    label, color = labels[score]
    return {"score": score, "label": label, "color": color, "tips": tips}


def render_password_strength(password: str):
    """Şifre gücü göstergesini Streamlit'te render eder."""
    if not password:
        return
    analysis = analyze_password_strength(password)
    score = analysis["score"]
    color = analysis["color"]
    label = analysis["label"]

    bar_html = f"""
    <div style="margin-top:4px;">
        <div style="display:flex; gap:4px; margin-bottom:4px;">
            {''.join([
                f'<div style="height:6px; flex:1; border-radius:3px; background-color:{"' + color + '" if i < score else "#334155"};"></div>'
                for i in range(5)
            ])}
        </div>
        <span style="font-size:0.75rem; color:{color}; font-weight:600;">{label}</span>
    </div>
    """
    st.markdown(bar_html, unsafe_allow_html=True)

    if analysis["tips"]:
        with st.expander("💡 Şifre İyileştirme Önerileri", expanded=False):
            for tip in analysis["tips"]:
                st.caption(f"• {tip}")


# ─────────────────────────────────────────────
#  YETKİ DENETİMİ DEKORATÖRÜ
# ─────────────────────────────────────────────

def role_badge(role: str) -> str:
    """HTML rozet döndürür."""
    info = ROLES.get(role, {"color": "#94a3b8"})
    color = info["color"]
    return f'<span style="background:{color}22; color:{color}; padding:2px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; border:1px solid {color}55;">{role}</span>'


# ─────────────────────────────────────────────
#  GERÇEK DÜNYA GÜVENLİK FONKSİYONLARI
# ─────────────────────────────────────────────

def generate_otp() -> str:
    """6 haneli rastgele OTP kodu üretir."""
    return "".join(random.choices(string.digits, k=6))

def send_2fa_otp(user_info: dict) -> bool:
    """Kullanıcının mailine OTP gönderir ve session_state'e kaydeder."""
    email = user_info.get("email")
    if not email:
        return False
    
    otp = generate_otp()
    st.session_state["correct_otp"] = otp
    st.session_state["otp_expiry"] = datetime.now() + timedelta(minutes=5)
    
    return send_otp_email(email, otp)

def reset_password_request(identifier: str) -> dict:
    """Şifre sıfırlama talebi alır, geçici şifre üretir ve gönderir."""
    user = db.get_user_by_identifier(identifier)
    if not user:
        return {"success": False, "message": "Kullanıcı bulunamadı."}
    
    email = user.get("email")
    if not email:
        return {"success": False, "message": "Kullanıcının kayıtlı e-posta adresi yok."}
    
    # Geçici şifre üret (8 karakter, harf ve rakam)
    temp_pass = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Veritabanında şifreyi güncelle
    db.update_user_password(user["username"], temp_pass)
    
    # Mail gönder
    sent = send_password_reset_email(email, temp_pass)
    
    if sent:
        return {"success": True, "message": "Geçici şifreniz e-posta adresinize gönderildi."}
    else:
        return {"success": False, "message": "E-posta gönderimi sırasında bir hata oluştu."}

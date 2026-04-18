"""
ui/settings_view.py
Apex Risk Terminal - Settings & Profile
Compact Popover Design
"""
import streamlit as st
from core.database_handler import db
from core.auth_system import (
    require_role, role_badge, logout
)
from config import ROLES, APP_NAME, APP_VERSION

def render_settings_view(user_info: dict):
    # Compact Header inside popover
    st.markdown(f"""
        <div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 0.5rem; margin-bottom: 1rem;">
            <h4 style="margin:0; color:#004C91;">🔧 Sistem & Profil</h4>
        </div>
    """, unsafe_allow_html=True)

    tab_profile, tab_system, tab_admin = st.tabs(["👤 Profil", "💻 Sistem", "🛡️ Admin"])

    with tab_profile:
        _render_profile_compact(user_info)

    with tab_system:
        _render_system_compact()

    with tab_admin:
        _render_admin_compact(user_info)

def _render_profile_compact(user_info: dict):
    initials = "".join(w[0].upper() for w in (user_info.get("full_name") or user_info["username"]).split()[:2])
    role = user_info.get('role','')
    role_color = ROLES.get(role, {}).get("color", "#004C91")
    
    st.markdown(f"""
        <div style="text-align:center; margin-bottom: 1rem;">
            <div style="width:50px; height:50px; border-radius:50%; background:{role_color}; 
                        color:white; display:flex; align-items:center; justify-content:center; 
                        font-weight:900; margin: 0 auto 0.5rem auto;">{initials}</div>
            <div style="font-weight:700; color:#1E293B;">{user_info.get('full_name','')}</div>
            <div style="font-size:0.75rem; color:#64748B;">{user_info.get('department','')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Simple Theme Switcher
    st.markdown("**Görünüm Karakteristiği**")
    theme_opt = {"Karanlık": "dark", "Aydınlık": "light"}
    curr_theme = st.session_state.get("theme", "light")
    new_theme_label = st.radio("Tema", ["Karanlık", "Aydınlık"], 
                               index=1 if curr_theme == "light" else 0, 
                               horizontal=True, label_visibility="collapsed")
    new_theme = theme_opt[new_theme_label]
    
    if new_theme != curr_theme:
        st.session_state["theme"] = new_theme
        st.rerun()

    st.markdown("---")
    if st.button("🚪 Oturumu Kapat", use_container_width=True, type="secondary"):
        logout()

def _render_system_compact():
    st.markdown(f"""
        <div style="font-size:0.85rem; color:#475569;">
            <p><b>Uygulama:</b> {APP_NAME}</p>
            <p><b>Versiyon:</b> v{APP_VERSION}</p>
            <p><b>Motor:</b> Ensemble v5.2 AI</p>
            <p><b>Sunucu:</b> Yerel / Kurumsal</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Önbelleği Temizle", use_container_width=True):
        st.cache_resource.clear()
        st.success("Sistem cache sıfırlandı.")

def _render_admin_compact(user_info: dict):
    if not require_role(3):
        st.warning("Erişim yetkiniz sınırlı.")
        return
    
    st.markdown("**Kullanıcı Kontrolü**")
    users = db.get_all_users()
    if not users.empty:
        target = st.selectbox("Analist Seç", users["username"].tolist())
        if st.button("Durumu Değiştir (Aktif/Pasif)", use_container_width=True):
            db.toggle_user_status(target)
            st.success(f"{target} güncellendi.")

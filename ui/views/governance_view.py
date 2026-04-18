import re
import time
"""
ui/views/governance_view.py — ProQuant Capital | Kurumsal Yönetişim & Denetim Paneli v6.0
====================================================================================

`GovernanceEngine` tarafından yönetilen yetkilendirme (RBAC), uyumluluk (Compliance) 
ve denetim (Audit) süreçlerini görselleştiren Streamlit arayüz modülü.
Sistem yöneticileri ve uyumluluk görevlileri (Compliance Officers) için tasarlanmıştır.

Görsel Bileşenler:
  1. System Health & Kill Switch: Platformun genel durum kontrolü ve acil müdahale.
  2. Audit Trail Explorer: Tüm kullanıcı eylemlerinin aranabilir ve filtrelenebilir listesi.
  3. Compliance Rule Monitor: Aktif limitler ve son ihlallerin özeti.
  4. Role/Permission Matrix: Mevcut kullanıcı rollerinin yetki dağılımı.

Interaktivite:
  - Kullanıcı bazlı denetim geçmişi arama.
  - Limit (Position Limit, Sector Limit) güncelleme arayüzü.
  - Acil durum 'Kill Switch' tetikleme ve geri çekme.

Author  : ProQuant Capital Governance UX
Version : 6.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ProQuant Modülleri
from core.governance_engine import get_governance_engine, UserRole, Permission

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: GÖRSELLEŞTİRME YARDIMCILARI
# ─────────────────────────────────────────────────────────────────────────────

def plot_compliance_radar():
    """Sistem uyumluluk metriklerini radar grafikte gösterir."""
    fig = go.Figure(data=go.Scatterpolar(
        r=[90, 85, 95, 80, 100],
        theta=["Data Privacy", "Model Risk", "Execution Integrity", "Access Control", "Audit Logging"],
        fill='toself',
        name='Compliance Score',
        line_color='#fbbf24'
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                      template="plotly_dark", title="Sistem Güvenlik & Uyumluluk Skoru")
    return fig

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: VIEW RENDERING (EKRAN ÇIKTISI)
# ─────────────────────────────────────────────────────────────────────────────

def render_governance_view():
    """Yönetişim ve denetim sayfasını oluşturur."""
    st.header("🔐 Kurumsal Yönetişim & Denetim Merkezi", divider="orange")
    
    # Üst Bölüm: Sistem Durumu & Kill Switch
    st.subheader("🛡️ Sistem Durumu & Acil Müdahale")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        st.success("✅ Sistem Aktif")
        st.info("Uptime: %99.98")
    with col2:
        st.warning("⚠️ 2 Kısıt İhlali")
        st.info("Last Audit: 12 dk önce")
    with col3:
        if st.button("🚨 GLOBAL KILL SWITCH (ACİL DURDURMA)", type="primary", use_container_width=True):
            st.error("DİKKAT: Sistem tüm işlemler için askıya alınacaktır! Şifre doğrulaması gerekli.")
            
    st.divider()

    # Orta Bölüm: Uyumluluk ve Yetki
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(plot_compliance_radar(), use_container_width=True)
    with c2:
        st.subheader("👥 Aktif Kullanıcı Rolleri")
        roles_df = pd.DataFrame({
            "Rol": ["ADMIN", "QUANT", "COMPLIANCE", "VIEWER"],
            "Kullanıcı Sayısı": [2, 14, 3, 5],
            "Erişim Seviyesi": ["Full", "Extended", "Secured", "Basic"]
        })
        st.table(roles_df)

    # Alt Bölüm: Audit Trail Explorer
    st.subheader("📜 Denetim İzi (Audit Trail Explorer)")
    
    # Filtreler
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1: user_search = st.text_input("Kullanıcı ID Ara", "")
    with f_col2: action_type = st.selectbox("Eylem Tipi", ["Hepsi", "AUTH_CHECK", "TRADE_EXECUTE", "MODEL_UPDATE"])
    with f_col3: date_range = st.date_input("Tarih Aralığı", [datetime.now() - timedelta(days=7), datetime.now()])

    # Mock Audit Verisi
    audit_data = pd.DataFrame([
        {"Zaman": (datetime.now() - timedelta(minutes=i*15)).strftime("%Y-%m-%d %H:%M"), 
         "Kullanıcı": f"USER_{random.randint(100, 200)}", 
         "Eylem": random.choice(["AUTH_CHECK", "TRADE_EXECUTE", "MODEL_UPDATE"]), 
         "Kaynak": random.choice(["Portfolio", "RiskEngine", "OrderGate"]), 
         "Durum": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "REJECTED"])}
        for i in range(20)
    ])
    
    # Filtreleme (Basit simülasyon)
    st.dataframe(audit_data, use_container_width=True)

    # Uyumluluk Limitleri
    with st.expander("⚙️ Aktif Uyumluluk Limitlerini Düzenle"):
        st.number_input("Maximum Pos. Size (% of Portfolio)", 1, 20, 10)
        st.number_input("Max. Order Value (USD)", 100000, 100000000, 10000000)
        st.multiselect("Banned Sectors", ["Defense", "Gambling", "Tobacco"], default=[])
        st.button("Limitleri Güncelle ve Duyur")

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    render_governance_view()

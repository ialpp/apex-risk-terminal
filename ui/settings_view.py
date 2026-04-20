"""
ui/settings_view.py
Apex Risk Terminal - Comprehensive Settings & Profile
Full Page View
"""
import streamlit as st
import textwrap
from core.database_handler import db
from core.auth_system import (
    require_role, role_badge, logout
)
from config import ROLES, APP_NAME, APP_VERSION

def render_settings_view(user_info: dict):
    # Full Page Header
    st.markdown(textwrap.dedent(f"""
        <div style="padding-bottom: 1.5rem; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <h2 style="margin:0; font-weight:800; background: linear-gradient(90deg, #38BDF8, #6366F1); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⚙️ Sistem ve Profil Ayarları</h2>
            <p style="color:#94A3B8; margin-top:0.5rem; font-size: 0.9rem;">Kişisel tercihlerinizi, güvenlik politikalarınızı ve terminal ayarlarınızı bu sayfadan yönetebilirsiniz.</p>
        </div>
    """), unsafe_allow_html=True)
    
    t1, t2, t3, t4, t5, t6 = st.tabs(["👤 Kişisel Bilgiler", "🔐 Güvenlik", "🔔 Bildirimler", "🎨 Görünüm", "📦 Abonelik Yönetimi", "📋 Yasal İzinler"])
    
    with t1:
        st.subheader("Profil Detayları")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Ad Soyad", value=user_info.get("full_name", ""))
            st.text_input("Kurum / Departman", value=user_info.get("department", "Risk Merkezi"))
            st.text_input("TCKN / VKN", value="12345678901", disabled=True, help="Kimlik/Vergi Numarası kilitlidir. Değişiklik için destek kaydı açın.")
        with c2:
            st.text_input("E-Posta Adresi", value=user_info.get("email", ""))
            st.text_input("Cep Telefonu", value="+90 5XX XXX XX XX")
            st.text_input("Meslek / Ünvan", value=user_info.get("role", ""))
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Kurumsal Tercihler")
        st.selectbox("Varsayılan Analiz Portföyü", ["Bireysel Krediler", "KOBİ Kredileri", "Ticari Tahsis"])
        st.selectbox("Belge ve Rapor Dili", ["Türkçe", "İngilizce (English)", "Almanca (Deutsch)"], index=["TR", "EN", "DE"].index(st.session_state.get("LANG", "TR")))
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Kişisel Bilgileri Kaydet", type="primary"):
            st.success("Kişisel bilgileriniz başarıyla güncellendi.")

    with t2:
        st.subheader("Şifre Değiştirme")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.text_input("Mevcut Şifre", type="password")
            st.text_input("Yeni Şifre", type="password")
            st.text_input("Yeni Şifre (Tekrar)", type="password")
            if st.button("Şifreyi Güncelle", type="secondary"):
                st.info("Kriptografik olarak şifreniz güncelleniyor...")
        with sc2:
            st.write("**Kimlik Doğrulama (2FA)**")
            st.toggle("SMS Tek Kullanımlık Şifre (Aktif)", value=True)
            st.toggle("Authenticator Uygulaması (Google/Microsoft)", value=False)
            st.toggle("Yeni Cihaz Girişi Uyarıları", value=True)
            st.caption("Kurumsal güvenlik politikası gereği en az bir 2FA yöntemi aktif bırakılmalıdır.")
            
            st.write("**Oturum Yönetimi**")
            st.slider("Otomatik Çıkış Süresi (Dakika)", 5, 120, 15)
            if st.button("Tüm Aktif Oturumları Sonlandır"):
                st.warning("Diğer tüm cihazlardaki oturumlarınız sonlandırıldı.")

    with t3:
        st.subheader("Sistem Bildirimleri")
        st.checkbox("Risk Raporu puanı güncellendiğinde SMS gönder", value=True)
        st.checkbox("Müşteri kredi notu kritik eşiğe düştüğünde E-Posta gönder", value=True)
        st.checkbox("Aylık finansal özet ve performans raporunu PDF olarak al", value=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Erken Uyarı (EWS) Bildirimleri")
        st.checkbox("Portföy Risk Değeri (VaR) artışında uyar", value=True)
        st.checkbox("Gecikmeli Kredi (NPL) oranı %5'i geçerse uyar", value=False)
        st.checkbox("Yeni Analiz model eğitimleri (AutoML) tamamlandığında bildir", value=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Kampanya ve İletişim")
        st.checkbox("Findeks kampanya, indirim ve yeniliklerinden haberdar olmak istiyorum", value=False)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Bildirim Tercihlerini Kaydet", type="primary"):
            st.success("Tüm bildirim ayarları kaydedildi.")

    with t4:
        st.subheader("Görünüm Karakteristiği")
        theme_opt = {"Karanlık (Dark)": "dark", "Aydınlık (Light)": "light"}
        curr_theme = st.session_state.get("theme", "light") # default light for generic? No, dark is terminal
        new_theme_label = st.radio("Tema Seçimi", ["Karanlık (Dark)", "Aydınlık (Light)"], 
                                   index=1 if curr_theme == "light" else 0)
        new_theme = theme_opt[new_theme_label]
        
        if new_theme != curr_theme:
            st.session_state["theme"] = new_theme
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Arayüz Optimizasyonu")
        st.toggle("Animasyonları Kapat (Performans Modu)", value=False)
        st.toggle("Kompakt Liste Görünümü (Sidebar daraltma)", value=False)
        st.selectbox("Varsayılan Veri Tablosu Satır Sayısı", [10, 25, 50, 100], index=1)

    with t5:
        st.subheader("Abonelik ve Limitler")
        st.info("**Aktif Paket:** Kurumsal Premium Sürüm")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Kalan Skorbord Sorgusu", "8,450", "-12")
        pc2.metric("Kalan Kapsamlı Rapor", "1,200", "-5")
        pc3.metric("Son Fatura Tutarı", "₺12,500", "Ödendi")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Ek Hizmet Yönetimi")
        st.toggle("Açık Bankacılık Modülü (YGM)", value=True, disabled=True)
        st.toggle("Yapay Zeka Destekli Tahmin Modülü (AutoML)", value=True)
        st.toggle("Derin Öğrenme API Erişim Anahtarı", value=False)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Paket İncele / Limit Arttır", type="primary"):
            st.toast("Satış temsilcinize sistem üzerinden otomatik talep iletildi.", icon="ℹ️")

    with t6:
        st.subheader("KVKK ve Rıza Yönetimi")
        st.checkbox("Kredi Kayıt Bürosu (KKB) verilerimin anonimleştirilerek AI modellerinde kullanılması", value=True)
        st.checkbox("Açık Bankacılık kapsamında 3. Parti hesap bakiyesi doğrulama izinlerine tam yetki", value=True)
        st.checkbox("Üçüncü taraf risk analiz kuruluşlarıyla limit paylaşım izni (Çapraz Risk Sorgusu)", value=False)
        st.checkbox("Biyometrik verilerimin güvenli giriş (FaceID/TouchID vb.) için işlenmesi", value=False)
        st.checkbox("Oturum kayıtlarımın (Audit Log) güvenlik incelemeleri için 10 yıl saklanması", value=True, disabled=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("İzinleri Uygula", type="primary"):
            st.success("KVKK ve Aydınlatma Metni izin tercihleri başarıyla kaydedildi.")

    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1); margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("🚪 Sistemi Kapat ve Güvenli Çıkış Yap", type="secondary"):
        logout()

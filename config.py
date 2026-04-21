"""
config.py — Kurumsal Kredi Risk Terminali Global Konfigürasyonu
Tüm sabitler, eşik değerleri ve sistem parametreleri burada merkezi olarak tanımlanır.
"""
import os
import sys

# SSL Karakter Seti Fix (özellikle Türkçe kullanıcı isimleri için)
try:
    import certifi
    import shutil
    original_ca = certifi.where()
    # Eğer yolda ASCII olmayan karakter varsa ceritifa dosyasını güvenli bir yere kopyala
    if any(ord(c) > 127 for c in original_ca):
        temp_dir = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'antigravity_ssl')
        os.makedirs(temp_dir, exist_ok=True)
        safe_ca_path = os.path.join(temp_dir, 'cacert.pem')
        if not os.path.exists(safe_ca_path):
            shutil.copy(original_ca, safe_ca_path)
        os.environ['CURL_CA_BUNDLE'] = safe_ca_path
        os.environ['SSL_CERT_FILE'] = safe_ca_path
        os.environ['REQUESTS_CA_BUNDLE'] = safe_ca_path
    else:
        os.environ['CURL_CA_BUNDLE'] = original_ca
except Exception:
    os.environ['CURL_CA_BUNDLE'] = ""
    os.environ['SSL_CERT_FILE'] = ""

# ─────────────────────────────────────────────
#  UYGULAMA METAVERİSİ
# ─────────────────────────────────────────────
APP_NAME        = "Apex Risk Terminal"
APP_SUBTITLE    = "Kurumsal Kredi Risk & Onay Terminali"
APP_VERSION     = "5.0.0"
APP_ICON        = "🏛️"
APP_LANG_DEFAULT = "tr"   # "tr" | "en"
LIVE_DATA_MODE   = True   # True: Gerçek piyasa verilerini çek | False: Simülasyon
DEFAULT_TICKERS  = ["AAPL", "TRY=X", "GC=F", "^VIX", "BTC-USD", "NVDA", "THYAO.IS"]

# ─────────────────────────────────────────────
#  GÜVENLİK PARAMETRELERİ
# ─────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS   = 5          # Kaç başarısız girişten sonra kilitlensin
LOCKOUT_MINUTES      = 15         # Kilitleme süresi (dakika)
SESSION_TIMEOUT_MINS = 30         # Oturum zaman aşımı (dakika)
PASSWORD_MIN_LENGTH  = 8          # Minimum şifre uzunluğu

# ─────────────────────────────────────────────
#  KREDİ SKORU EŞİK DEĞERLERİ (FICO benzeri)
# ─────────────────────────────────────────────
SCORE_BANDS = {
    "Mükemmel": (850, 1000, "#10b981"),   # Yeşil
    "Çok İyi":  (740, 849,  "#3b82f6"),   # Mavi
    "İyi":      (670, 739,  "#8b5cf6"),   # Mor
    "Orta":     (580, 669,  "#f59e0b"),   # Sarı
    "Zayıf":    (300, 579,  "#ef4444"),   # Kırmızı
}
SCORE_MIN = 300
SCORE_MAX = 850

# ─────────────────────────────────────────────
#  BORÇ / GELİR ORANI EŞİKLERİ
# ─────────────────────────────────────────────
DTI_LOW    = 0.35   # %35 altı — DÜŞÜK RİSK
DTI_MEDIUM = 0.50   # %50 altı — ORTA RİSK
DTI_HIGH   = 0.65   # %65 altı — YÜKSEK RİSK
# %65 ve üzeri — KRİTİK RİSK

# ─────────────────────────────────────────────
#  MAKRO / STRES TEST DEĞERLERİ
# ─────────────────────────────────────────────
INFLATION_SHOCKS     = [0.05, 0.10, 0.20, 0.40]   # %5, 10, 20, 40 enflasyon şoku
INTEREST_RATE_SHOCKS = [0.02, 0.05, 0.10, 0.15]   # Faiz şokları
MONTE_CARLO_RUNS     = 10000                        # Monte Carlo simülasyon sayısı

# ─────────────────────────────────────────────
#  MAKİNE ÖĞRENMESİ PARAMETRELERİ
# ─────────────────────────────────────────────
ML_TRAINING_SAMPLES  = 50000   # Sentetik veri seti boyutu
RF_N_ESTIMATORS      = 200
GB_N_ESTIMATORS      = 150
GB_LEARNING_RATE     = 0.08
RANDOM_STATE         = 42

# Model'in saklacağı dizin ve isim
MODELS_DIR   = "models"
MODEL_FILE   = "institutional_ensemble_v5.pkl"
SCALER_FILE  = "feature_scaler_v5.pkl"

# ─────────────────────────────────────────────
#  VERİTABANI
# ─────────────────────────────────────────────
DB_FILE = "kurumsal_veritabani.db"

# ─────────────────────────────────────────────
#  PDF RAPORLAMA
# ─────────────────────────────────────────────
PDF_COMPANY_NAME   = "ProQuant Capital Risk Services"
PDF_COMPANY_ADDR   = "Maslak Mahallesi, Büyükdere Cd. No:123, İstanbul"
PDF_REPORT_FOOTER  = "Bu rapor yapay zeka destekli risk analiz sistemi tarafından otomatik üretilmiştir."

# ─────────────────────────────────────────────
#  KULLANICI ROLLERİ
# ─────────────────────────────────────────────
ROLES = {
    "Genel Müdür":      {"level": 4, "color": "#f59e0b"},
    "Head Analist":     {"level": 3, "color": "#3b82f6"},
    "Risk Analisti":    {"level": 2, "color": "#8b5cf6"},
    "Stajyer Analist":  {"level": 1, "color": "#94a3b8"},
}

# ─────────────────────────────────────────────
#  DİL DESTEK TABLOSU (i18n)
# ─────────────────────────────────────────────
TRANSLATIONS = {
    "tr": {
        "app_title":       "Kurumsal Kredi Risk Terminali",
        "login":           "Sisteme Bağlan",
        "logout":          "Güvenli Çıkış",
        "dashboard":       "Yönetici Özeti",
        "new_analysis":    "Yeni Müşteri Analizi",
        "portfolio":       "Portföy Yönetimi",
        "macro":           "Makro Analiz",
        "reports":         "Raporlama Merkezi",
        "audit":           "Denetim İzi",
        "settings":        "Sistem Ayarları",
        "approved":        "ONAYLANDI",
        "rejected":        "REDDEDİLDİ",
        "score":           "Kredi Skoru",
        "risk":            "Risk Seviyesi",
        "income":          "Aylık Gelir",
        "debt":            "Mevcut Borç",
        "age":             "Yaş",
        "dti":             "Borç/Gelir Oranı",
        "late_payments":   "Gecikmiş Ödeme",
        "cards":           "Kredi Kartı Sayısı",
        "submit":          "Analizi Başlat",
        "loading":         "Kurumsal motor çalışıyor...",
        "no_model":        "Model henüz eğitilmedi. Lütfen Model Eğitimi sekmesine gidin.",
    },
    "en": {
        "app_title":       "Institutional Credit Risk Terminal",
        "login":           "Connect to System",
        "logout":          "Secure Logout",
        "dashboard":       "Executive Dashboard",
        "new_analysis":    "New Customer Analysis",
        "portfolio":       "Portfolio Management",
        "macro":           "Macro Analysis",
        "reports":         "Reporting Center",
        "audit":           "Audit Trail",
        "settings":        "System Settings",
        "approved":        "APPROVED",
        "rejected":        "REJECTED",
        "score":           "Credit Score",
        "risk":            "Risk Level",
        "income":          "Monthly Income",
        "debt":            "Current Debt",
        "age":             "Age",
        "dti":             "Debt/Income Ratio",
        "late_payments":   "Late Payments",
        "cards":           "Card Count",
        "submit":          "Run Analysis",
        "loading":         "Institutional engine processing...",
        "no_model":        "Model not trained yet. Please go to the Model Training tab.",
    }
}

def t(key: str, lang: str = APP_LANG_DEFAULT) -> str:
    """Çeviri fonksiyonu. Verilen key'in dile göre karşılığını döndürür."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["tr"]).get(key, key)

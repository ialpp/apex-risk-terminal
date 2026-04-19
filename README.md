# 🏦 Apex Risk Terminal
### Kurumsal Kredi Riski & Finansal Analiz Platformu

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
[![CI](https://github.com/ialpp/apex-risk-terminal/actions/workflows/ci.yml/badge.svg)](https://github.com/ialpp/apex-risk-terminal/actions/workflows/ci.yml)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://apex-risk-terminal-as5vrwswtre8zwrhosgurp.streamlit.app)

**Makine öğrenmesi destekli, kurumsal düzeyde kredi riski analiz ve karar destek sistemi.**

> 🚀 **Canlı Demo:** Streamlit Cloud'a deploy ettiğinizde badge URL'sini güncelleyin.

</div>

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Özellikler](#-özellikler)
- [Teknoloji Yığını](#-teknoloji-yığını)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Veri Seti](#-veri-seti)
- [Model Mimarisi](#-model-mimarisi)
- [Ekran Görüntüleri](#-ekran-görüntüleri)
- [Proje Yapısı](#-proje-yapısı)
- [İletişim](#-iletişim)

---

## 🎯 Proje Hakkında

Apex Risk Terminal, finansal kurumların kredi kararlarını desteklemek için geliştirilmiş kurumsal düzeyde bir analiz platformudur. Sistem:

- **Makine öğrenmesi** ile bireysel müşteri kredi riski tahmini
- **FICO benzeri** 5 kategorili kredi skoru hesaplama (300–850 aralığı)
- **Monte Carlo simülasyonu** ile olasılıksal risk modelleme
- **Basel III / IFRS 9** uyumlu stres test senaryoları
- **Black-Scholes** opsiyon fiyatlama ve Greeks hesaplama
- **Portföy optimizasyonu** (Markowitz Mean-Variance)
- **ESG skorlaması** ve sürdürülebilirlik analizi

gibi karmaşık finansal hesaplamaları tek bir web arayüzünde sunar.

---

## ✨ Özellikler

### 🧠 Yapay Zeka & Makine Öğrenmesi
| Modül | Algoritma | Açıklama |
|---|---|---|
| Kredi Skoru Motoru | Random Forest + GBM + Logistic Regression (Soft Voting Ensemble) | Temerrüt olasılığı (PD) tahmini |
| Sahtekarlık Tespiti | Isolation Forest | Anomali bazlı fraud detection |
| Müşteri Segmentasyonu | K-Means (k=4) | A/B/C/D Tier sınıflandırma |
| Erken Uyarı Sistemi | Eşik tabanlı kural motoru | Portföy sağlık taraması |
| AutoML Optimizer | Evrimsel algoritmalar | Hiperparametre optimizasyonu |
| Derin Öğrenme | Neural Network | İleri seviye örüntü tanıma |

### 📊 Kantitatif Finans
- **Black-Scholes** — Call/Put opsiyon fiyatlaması, Put-Call Parity doğrulaması
- **Greeks** — Delta, Gamma, Vega, Theta, Rho hesaplama
- **Monte Carlo** — 10.000 simülasyon ile temerrüt olasılığı dağılımı
- **Value at Risk (VaR)** — Parametrik ve Tarihsel Simülasyon yöntemleri
- **Markowitz Portföy Optimizasyonu** — Etkin sınır (Efficient Frontier)
- **Kalman Filtresi** — Dinamik fiyat ve sinyal tahmini
- **İstatistiksel Arbitraj** — Pairs Trading sinyalleri

### 🏛️ Düzenleyici Uyum
- **IFRS 9** — Stage 1/2/3 ECL (Expected Credit Loss) hesaplama
- **Basel III** — PD/LGD/EAD parametre modelleme
- **Stres Testi** — 4 senaryo: Temel / Hafif / Orta / Şiddetli makro şok
- **RAROC** — Risk-Adjusted Return on Capital fiyatlama

---

## 🛠 Teknoloji Yığını

```
Backend & ML
├── Python 3.11+
├── scikit-learn   — Ensemble modeller, preprocessing
├── scipy          — İstatistiksel hesaplamalar, Black-Scholes
├── numpy / pandas — Veri manipülasyonu
└── joblib         — Model serializasyon

Frontend
├── Streamlit 1.32+  — Web arayüzü
├── Plotly           — İnteraktif finansal grafikler
└── Custom CSS       — Glassmorphism dark-mode tema

Veri & Raporlama
├── SQLite           — Kurumsal veritabanı
├── ReportLab        — PDF rapor üretimi
└── openpyxl         — Excel export
```

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- pip

### Adım Adım

```bash
# 1. Depoyu klonlayın
git clone https://github.com/ialpp/apex-risk-terminal.git
cd apex-risk-terminal

# 2. Sanal ortam oluşturun (önerilen)
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Uygulamayı başlatın
streamlit run app.py
```

**Windows için kolay başlatma:** `başlat.bat` dosyasına çift tıklayın.

### Giriş Bilgileri (Demo)

| Kullanıcı | Şifre | Rol |
|---|---|---|
| `admin` | `admin123` | Genel Müdür |
| `analyst` | `analyst123` | Risk Analisti |

---

## 📖 Kullanım

### 1. Model Eğitimi
İlk kurulumda sol menüden **⚙️ Model Yönetimi** → **"Ana Modeli Eğit"** butonuna tıklayın.

Model eğitimi sırasında:
- **UCI German Credit** gerçek veri seti otomatik indirilir (~100KB)
- 1.000 gerçek kayıt + 9.000 augmented kayıt birleştirilerek eğitilir
- Eğitim ~30-60 saniye sürer
- AUC-ROC, F1, Precision/Recall metrikleri gösterilir

### 2. Müşteri Analizi
**👤 Yeni Müşteri Analizi** sayfasından müşteri bilgilerini girin:
- Yaş, Aylık Gelir, Mevcut Borç
- Gecikmiş Ödeme Sayısı, Çalışma Yılı
- Kredi Kartı Sayısı, Kredi Geçmişi

Sistem anlık olarak:
- Kredi Skoru (300-850)
- Temerrüt Olasılığı (%)
- FICO 5-kategori dağılımı
- Risk Kategorisi (Mükemmel / Çok İyi / İyi / Orta / Zayıf)
- Öneri & aksiyon planı hesaplar

### 3. Stres Testi
**📉 Makro Stres Testleri** sayfasından 4 farklı makroekonomik senaryo altında müşteri profilini test edin:

| Senaryo | Enflasyon Şoku | Faiz Şoku | İşsizlik Şoku |
|---|---|---|---|
| Temel | — | — | — |
| Hafif Şok | +%10 | +%2 | +%2 |
| Orta Şok | +%20 | +%5 | +%5 |
| Şiddetli Şok | +%40 | +%10 | +%10 |

---

## 📦 Veri Seti

### UCI Statlog (German Credit Data)
> Hofmann, H. (1994). *Statlog (German Credit Data).* UCI Machine Learning Repository.  
> 🔗 https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)

| Özellik | Değer |
|---|---|
| Kaynak | UCI Machine Learning Repository |
| Kayıt sayısı (gerçek) | 1.000 |
| Kayıt sayısı (augmented) | +9.000 (SMOTE benzeri) |
| Hedef değişken | Kredi Onay/Red (binary) |
| Lisans | Academic Use |

**Feature Mapping:** UCI'nın 20 özelliği projenin 10 özelliğine dönüştürülür:
- `age` → Yaş
- `credit_amount` → Mevcut Borç
- `duration_months` → Kredi Geçmişi (ay→yıl)
- `employment_years` → Çalışma Yılı
- `checking_account` → Gecikmiş Ödeme proxy
- vb.

---

## 🧮 Model Mimarisi

```
Input Features (10 boyut)
├── Yaş, Aylık Gelir, Mevcut Borç
├── Gecikmiş Ödeme Sayısı, Kredi Kartı Sayısı
├── Borç/Gelir Oranı (DTI), Çalışma Yılı
├── Ek Gelir, Bakmakla Yükümlü Kişi, Kredi Geçmişi
│
↓  StandardScaler normalizasyonu
│
Soft Voting Ensemble
├── Random Forest        (200 ağaç, max_depth=12)  ← ağırlık: 3
├── Gradient Boosting    (150 iter, lr=0.08)        ← ağırlık: 3
└── Logistic Regression  (L2, max_iter=1000)        ← ağırlık: 1
│
Output
├── approved: bool          # Onay/Red kararı
├── approval_prob: float    # Onay olasılığı (0-1)
├── default_risk: float     # Temerrüt riski (0-1)
├── credit_score: float     # FICO benzeri skor (300-850)
└── fico_breakdown: dict    # 5 kategori dağılımı
```

**Model Performansı (Test Seti, UCI + Augmented):**

| Metrik | Değer |
|---|---|
| Accuracy | ~%82-86 |
| AUC-ROC | ~%87-91 |
| Precision | ~%83-88 |
| Recall | ~%80-85 |
| F1 Score | ~%81-86 |

---

## 🗂 Proje Yapısı

```
apex-risk-terminal/
│
├── app.py                    # Ana Streamlit uygulaması & router
├── config.py                 # Global konfigürasyon & parametreler
├── requirements.txt          # Python bağımlılıkları
│
├── core/                     # Altyapı katmanı
│   ├── auth_system.py        # JWT tabanlı RBAC yetkilendirme
│   ├── database_handler.py   # SQLite ORM katmanı
│   ├── backtester_pro.py     # Strateji geri-test motoru
│   ├── data_orchestrator.py  # Veri akışı yönetimi
│   └── governance_engine.py  # Kurumsal yönetişim
│
├── modules/                  # İş mantığı & analiz motorları
│   ├── credit_scoring_engine.py    # Ana ML motoru (Ensemble)
│   ├── fraud_detection.py          # Isolation Forest anomali tespiti
│   ├── clustering_engine.py        # K-Means müşteri segmentasyonu
│   ├── deep_learning_credit.py     # Neural Network kredi analizi
│   ├── derivatives_math.py         # Black-Scholes, Greeks (46KB)
│   ├── esg_scoring_engine.py       # ESG & sürdürülebilirlik skoru
│   ├── portfolio_optimizer_pro.py  # Markowitz optimizasyonu
│   ├── portfolio_var_engine.py     # Value at Risk hesaplama
│   ├── regulatory_reports_ifrs9.py # IFRS 9 / ECL raporlama
│   ├── econometrics_engine.py      # VAR, ARIMA, GARCH
│   ├── kalman_filter_engine.py     # Kalman filtresi
│   ├── pairs_trading_engine.py     # İstatistiksel arbitraj
│   ├── options_greeks_engine.py    # Opsiyon Greeks motoru
│   ├── macro_regime_engine.py      # HMM rejim tespiti
│   └── automl_evolutionary.py     # Evrimsel hiperparametre opt.
│
├── ui/                       # Kullanıcı arayüzü katmanı
│   ├── theme.py              # Glassmorphism dark-mode CSS sistemi
│   ├── dashboard_view.py     # Yönetici özet dashboard
│   ├── analysis_view.py      # Müşteri analiz formu
│   ├── portfolio_view.py     # Portföy yönetim ekranı
│   └── login_screen.py       # Giriş ekranı
│
├── data/                     # Veri katmanı
│   ├── real_dataset_loader.py      # UCI veri seti yükleyici
│   └── credit_data/                # İndirilen gerçek veriler
│
├── tests/                    # Test süitleri
│   ├── automated_suite.py    # Birim & entegrasyon testleri
│   └── unit/                 # Modül bazlı testler
│
├── assets/                   # Statik dosyalar
│   └── logo.png              # Uygulama logosu
│
└── .streamlit/
    └── config.toml           # Streamlit tema konfigürasyonu
```

---

## 🚢 Deployment

### Streamlit Community Cloud (Ücretsiz)

1. Bu repoyu **fork** edin
2. [share.streamlit.io](https://share.streamlit.io) adresine gidin
3. GitHub hesabınızı bağlayın
4. **"New app"** → repoyu seçin → `app.py` → **Deploy**

> ⚠️ `.streamlit/config.toml` dosyası zaten yapılandırılmıştır.

---

## 📄 Lisans

Bu proje **MIT Lisansı** ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 📸 Ekran Görüntüleri

> 📌 Ekran görüntüleri Streamlit Cloud deploy sonrası eklenecektir.  
> Uygulamayı çalıştırarak canlı demo için yukarıdaki **Open in Streamlit** badge'ine tıklayın.

| Ekran | Açıklama |
|---|---|
| Executive Dashboard | Yönetici özet ekranı, KPI kartları, portföy dağılımı |
| Müşteri Analizi | Kredi skoru motoru, FICO dağılımı, risk kategorisi |
| Stres Testi | 4 makroekonomik senaryo karşılaştırması |
| ESG Analizi | Sürdürülebilirlik skoru ve çevre risk metrikleri |
| Portföy Optimizasyonu | Markowitz etkin sınır görselizasyonu |

---

## 📬 İletişim

Proje ile ilgili sorularınız için GitHub Issues kullanabilirsiniz.

---

<div align="center">
<sub>Built with ❤️ using Python & Streamlit</sub>
</div>

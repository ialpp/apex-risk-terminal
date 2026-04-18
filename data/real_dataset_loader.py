"""
data/real_dataset_loader.py
============================
Gerçek Kredi Veri Seti Yükleyici

Desteklenen veri setleri:
  1. UCI Statlog (German Credit Data) — 1000 kayıt, ücretsiz
     https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)
  
  2. Give Me Some Credit (Kaggle) — 150K kayıt
     Kaggle API key gerektirir.

Veri setleri projenin feature formatına (Yas, Aylik_Gelir, vb.) dönüştürülür.
"""

import os
import urllib.request
import numpy as np
import pandas as pd

# Proje kök dizini
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data", "credit_data")


# ──────────────────────────────────────────────────────────────────────────────
#  UCI GERMAN CREDIT DATASET
# ──────────────────────────────────────────────────────────────────────────────

UCI_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"
UCI_LOCAL = os.path.join(_DATA_DIR, "german_credit.data")

UCI_COLUMNS = [
    "checking_account", "duration_months", "credit_history", "purpose",
    "credit_amount", "savings_account", "employment_years", "installment_rate",
    "personal_status", "other_debtors", "residence_since", "property",
    "age", "other_installment", "housing", "existing_credits", "job",
    "dependents", "telephone", "foreign_worker", "target"  # 1=Good, 2=Bad
]


def download_uci_dataset(force: bool = False) -> bool:
    """
    UCI German Credit veri setini indirir.
    Dönüş: True = başarılı, False = hata
    """
    os.makedirs(_DATA_DIR, exist_ok=True)
    
    if os.path.exists(UCI_LOCAL) and not force:
        return True  # Zaten indirilmiş
    
    try:
        print(f"[INFO] UCI German Credit dataset indiriliyor: {UCI_URL}")
        urllib.request.urlretrieve(UCI_URL, UCI_LOCAL)
        print(f"[OK] Indirildi: {UCI_LOCAL}")
        return True
    except Exception as e:
        print(f"[HATA] Indirme hatasi: {e}")
        return False


def load_uci_german_credit() -> pd.DataFrame | None:
    """
    UCI German Credit veri setini yükler ve projenin feature formatına çevirir.
    
    Feature Mapping:
      age              → Yas
      credit_amount    → Mevcut_Borc  (kredi miktarı borç olarak)
      duration_months  → Kredi_Gecmisi_Yili (ay → yıl)
      employment_years → Calisma_Yili
      dependents       → Bagli_Kisi_Sayisi
      existing_credits → Kredi_Karti_Sayisi
      target           → Onay_Durumu (1=Good→1, 2=Bad→0)
    
    Eksik feature'lar (Aylik_Gelir, Ek_Gelir) makul tahminlerle doldurulur.
    """
    if not os.path.exists(UCI_LOCAL):
        success = download_uci_dataset()
        if not success:
            return None
    
    try:
        df_raw = pd.read_csv(UCI_LOCAL, sep=" ", header=None, names=UCI_COLUMNS)
    except Exception as e:
        print(f"❌ Veri okuma hatası: {e}")
        return None

    rng = np.random.default_rng(42)

    # Employment years → numeric mapping
    emp_map = {
        "A71": 0,    # unemployed
        "A72": 1,    # < 1 year
        "A73": 3,    # 1..4 years
        "A74": 7,    # 4..7 years
        "A75": 12,   # >= 7 years
    }

    # Checking account → proxy for gecikmiş ödeme
    check_map = {
        "A11": 4,   # < 0 DM → yüksek gecikme
        "A12": 1,   # 0..200 DM → düşük
        "A13": 0,   # >= 200 DM → sıfır
        "A14": 2,   # no checking → 2
    }

    df = pd.DataFrame()
    df["Yas"]                   = df_raw["age"].clip(18, 80)
    df["Mevcut_Borc"]           = df_raw["credit_amount"].astype(float)
    df["Kredi_Gecmisi_Yili"]    = (df_raw["duration_months"] / 12).round(1)
    df["Calisma_Yili"]          = df_raw["employment_years"].map(emp_map).fillna(2)
    df["Bagli_Kisi_Sayisi"]     = df_raw["dependents"].clip(0, 5)
    df["Kredi_Karti_Sayisi"]    = df_raw["existing_credits"].clip(0, 8)
    df["Gecikmis_Odeme_Sayisi"] = df_raw["checking_account"].map(check_map).fillna(1)
    
    # Aylik_Gelir: credit_amount ve duration'dan geri türet (makul tahmin)
    # Gerçek veri setinde aylık gelir yok — kredi/süre oranından proxy
    df["Aylik_Gelir"] = (df_raw["credit_amount"] / df_raw["duration_months"]).clip(1000, 50000) * rng.uniform(3, 6, len(df_raw))
    df["Aylik_Gelir"] = df["Aylik_Gelir"].clip(3000, 150000)
    
    # Ek_Gelir: gelirin %5-25'i
    df["Ek_Gelir"] = df["Aylik_Gelir"] * rng.uniform(0.05, 0.25, len(df_raw))
    
    # Borç/Gelir Oranı
    df["Borc_Gelir_Orani"] = (df["Mevcut_Borc"] / df["Aylik_Gelir"]).clip(0, 5)
    
    # Target: 1=Good Credit (onay) | 2=Bad Credit (red)
    df["Onay_Durumu"] = (df_raw["target"] == 1).astype(int)

    # Tipler
    df = df.astype({
        "Yas": int,
        "Bagli_Kisi_Sayisi": int,
        "Kredi_Karti_Sayisi": int,
        "Gecikmis_Odeme_Sayisi": int,
        "Onay_Durumu": int,
    })

    print(f"[OK] UCI German Credit yuklendi: {len(df)} kayit, {df['Onay_Durumu'].mean()*100:.1f}% onay orani")
    return df


# ──────────────────────────────────────────────────────────────────────────────
#  KARMA VERİ SETİ (UCI + Sentetik Genişletme)
# ──────────────────────────────────────────────────────────────────────────────

def load_combined_dataset(n_synthetic: int = 9000) -> pd.DataFrame:
    """
    Gerçek UCI verisi + genişletilmiş sentetik veri birleştirme.
    
    Toplam: ~10,000 kayıt (1,000 gerçek + 9,000 augmented)
    Bu yaklaşım gerçek veri dağılımını koruyarak model eğitimi için yeterli boyut sağlar.
    
    Returns:
        DataFrame: Birleşik veri seti, 'source' sütunu ile kaynak etiketlenmiş
    """
    real_df = load_uci_german_credit()
    
    if real_df is None:
        print("[WARN] UCI verisi alinamadi, sentetik veri kullaniliyor.")
        return _generate_synthetic(n_synthetic)

    real_df["source"] = "uci_real"
    
    # Gerçek veriden istatistik al, augmente et
    synth_df = _augment_from_real(real_df, n=n_synthetic)
    synth_df["source"] = "augmented"
    
    combined = pd.concat([real_df, synth_df], ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"[INFO] Karma veri seti hazir:")
    print(f"   Gercek (UCI): {len(real_df):,} kayit")
    print(f"   Augmented:    {len(synth_df):,} kayit")
    print(f"   Toplam:       {len(combined):,} kayit")
    print(f"   Onay orani:   {combined['Onay_Durumu'].mean()*100:.1f}%")
    
    return combined


def _augment_from_real(df: pd.DataFrame, n: int = 9000) -> pd.DataFrame:
    """
    Gerçek verinin dağılımını koruyarak augmente sentetik veri üretir.
    SMOTE benzeri yaklaşım — mevcut kayıtlara Gaussian gürültü ekler.
    """
    rng = np.random.default_rng(42)
    
    feature_cols = [
        "Yas", "Aylik_Gelir", "Mevcut_Borc", "Gecikmis_Odeme_Sayisi",
        "Kredi_Karti_Sayisi", "Borc_Gelir_Orani", "Calisma_Yili",
        "Ek_Gelir", "Bagli_Kisi_Sayisi", "Kredi_Gecmisi_Yili"
    ]
    
    samples = []
    for _ in range(n):
        # Rastgele gerçek bir kayıt seç
        base = df.sample(1, random_state=rng.integers(1e9)).iloc[0]
        new_row = {}
        
        for col in feature_cols:
            val = base[col]
            if col in ["Yas", "Bagli_Kisi_Sayisi", "Kredi_Karti_Sayisi", "Gecikmis_Odeme_Sayisi"]:
                # Integer kolonlar — küçük integer pertürbasyon
                noise = rng.integers(-1, 2)
                new_row[col] = int(max(0, val + noise))
            else:
                # Float kolonlar — %±15 Gaussian gürültü
                noise_fac = rng.normal(1.0, 0.15)
                new_row[col] = max(0.0, val * noise_fac)
        
        # DTI yeniden hesapla
        new_row["Borc_Gelir_Orani"] = new_row["Mevcut_Borc"] / max(new_row["Aylik_Gelir"], 1)
        new_row["Onay_Durumu"] = int(base["Onay_Durumu"])
        samples.append(new_row)
    
    return pd.DataFrame(samples)


def _generate_synthetic(n: int = 10000) -> pd.DataFrame:
    """Fallback: UCI erişilemezse tamamen sentetik veri üretir."""
    rng = np.random.default_rng(42)
    yas          = rng.integers(18, 75, n)
    aylik_gelir  = np.clip(rng.lognormal(9.9, 0.6, n), 5500, 200000)
    mevcut_borc  = aylik_gelir * rng.uniform(0.1, 4.0, n)
    calisma_yili = np.clip(rng.exponential(5, n), 0, 45)
    ek_gelir     = aylik_gelir * rng.uniform(0, 0.3, n)
    bagli_kisi   = rng.integers(0, 6, n)
    gecikmis     = rng.integers(0, 12, n)
    kredi_karti  = rng.integers(0, 8, n)
    kredi_gecm   = np.clip(rng.exponential(4, n), 0.5, 30)
    dti          = mevcut_borc / aylik_gelir
    
    from scipy.special import expit
    raw_score = (
        (aylik_gelir**0.4) * 3
        + calisma_yili * 20
        + kredi_gecm * 15
        - gecikmis**2 * 120
        - dti * 800
        - bagli_kisi * 40
        + ek_gelir * 0.01
        + rng.normal(0, 200, n)
    )
    prob = expit((raw_score - np.median(raw_score)) / np.std(raw_score) * 2)
    onay = (rng.random(n) < prob).astype(int)
    
    return pd.DataFrame({
        "Yas": yas, "Aylik_Gelir": aylik_gelir, "Mevcut_Borc": mevcut_borc,
        "Gecikmis_Odeme_Sayisi": gecikmis, "Kredi_Karti_Sayisi": kredi_karti,
        "Borc_Gelir_Orani": dti, "Calisma_Yili": calisma_yili,
        "Ek_Gelir": ek_gelir, "Bagli_Kisi_Sayisi": bagli_kisi,
        "Kredi_Gecmisi_Yili": kredi_gecm, "Onay_Durumu": onay,
        "source": "synthetic"
    })


def get_dataset_info() -> dict:
    """Veri seti hakkında metadata döndürür."""
    return {
        "name": "UCI Statlog (German Credit Data) + Augmented",
        "source_url": "https://archive.ics.uci.edu/ml/datasets/statlog+(german+credit+data)",
        "real_records": 1000,
        "augmented_records": 9000,
        "total_records": 10000,
        "features": 10,
        "target": "Onay_Durumu (1=Onaylı, 0=Reddedildi)",
        "license": "UCI Machine Learning Repository — Academic Use",
        "citation": "Hofmann, H. (1994). Statlog (German Credit Data). UCI Machine Learning Repository.",
        "local_path": UCI_LOCAL,
        "downloaded": os.path.exists(UCI_LOCAL),
    }


# ──────────────────────────────────────────────────────────────────────────────
#  TEST
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Veri Seti Yükleyici Test ===\n")
    info = get_dataset_info()
    print(f"Veri Seti  : {info['name']}")
    print(f"Kaynak     : {info['source_url']}")
    print(f"İndirildi  : {'Evet' if info['downloaded'] else 'Hayır'}\n")
    
    df = load_combined_dataset(n_synthetic=9000)
    if df is not None:
        print(f"\nSütunlar: {list(df.columns)}")
        print(f"\nİlk 3 kayıt:")
        print(df.head(3).to_string())

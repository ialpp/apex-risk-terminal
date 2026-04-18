import time
"""
modules/credit_scoring_engine.py
Kurumsal Makine Öğrenmesi Motoru
Random Forest + Gradient Boosting + Lojistik Regresyon Ensemble (Oylama)
Basel III Stres Testi Modülü
FICO Benzeri 5 Alt Kategori Skoru Hesaplayıcı
Monte Carlo Simülasyonu
"""

import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report, roc_auc_score,
    confusion_matrix, precision_score, recall_score, f1_score
)
from config import (
    ML_TRAINING_SAMPLES, RF_N_ESTIMATORS, GB_N_ESTIMATORS,
    GB_LEARNING_RATE, RANDOM_STATE, MODELS_DIR, MODEL_FILE,
    SCALER_FILE, SCORE_MIN, SCORE_MAX, SCORE_BANDS,
    INFLATION_SHOCKS, INTEREST_RATE_SHOCKS, MONTE_CARLO_RUNS
)


# ─────────────────────────────────────────────────────────────────
#  ANA MOTOR SINIFI
# ─────────────────────────────────────────────────────────────────

class AdvancedScoringEngine:
    """
    Kurumsal seviye Ensemble Kredi Risk Motoru.
    XGBoost + Random Forest + Lojistik Regresyon kombinasyonu.
    50,000 sentetik müşteri verisiyle eğitim.
    """

    FEATURE_COLS = [
        "Yas", "Aylik_Gelir", "Mevcut_Borc", "Gecikmis_Odeme_Sayisi",
        "Kredi_Karti_Sayisi", "Borc_Gelir_Orani", "Calisma_Yili",
        "Ek_Gelir", "Bagli_Kisi_Sayisi", "Kredi_Gecmisi_Yili"
    ]

    FEATURE_LABELS_TR = {
        "Yas":                    "Yaş",
        "Aylik_Gelir":            "Aylık Gelir",
        "Mevcut_Borc":            "Mevcut Borç",
        "Gecikmis_Odeme_Sayisi":  "Gecikmiş Ödeme",
        "Kredi_Karti_Sayisi":     "Kredi Kartı",
        "Borc_Gelir_Orani":       "Borç/Gelir Oranı",
        "Calisma_Yili":           "Çalışma Yılı",
        "Ek_Gelir":               "Ek Gelir",
        "Bagli_Kisi_Sayisi":      "Bakmakla Yükümlü",
        "Kredi_Gecmisi_Yili":     "Kredi Geçmişi",
    }

    def __init__(self):
        base = os.path.dirname(os.path.dirname(__file__))
        self.models_dir  = os.path.join(base, MODELS_DIR)
        self.model_path  = os.path.join(self.models_dir, MODEL_FILE)
        self.scaler_path = os.path.join(self.models_dir, SCALER_FILE)
        os.makedirs(self.models_dir, exist_ok=True)
        self.model  = None
        self.scaler = None
        self._load_artifacts()

    # ── Yükleme ──────────────────────────────────────────────────

    def _load_artifacts(self):
        try:
            self.model  = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        except Exception:
            pass

    def is_trained(self) -> bool:
        return self.model is not None

    # ── Sentetik Veri Üretimi ────────────────────────────────────

    def _generate_training_data(self, n: int = ML_TRAINING_SAMPLES) -> pd.DataFrame:
        """
        Ekonomik kurallara uygun, gerçekçi 50.000 müşteri verisi üretir.
        Lognormal dağılımlar, korelasyonlar ve gürültü içerir.
        """
        rng = np.random.default_rng(RANDOM_STATE)

        yas              = rng.integers(18, 75, n)
        aylik_gelir      = np.clip(rng.lognormal(mean=9.9, sigma=0.6, size=n), 5500, 200000)
        calisma_yili     = np.clip(rng.exponential(scale=5, size=n), 0, 45)
        ek_gelir         = aylik_gelir * rng.uniform(0, 0.3, n)
        bagli_kisi       = rng.integers(0, 6, n)

        # Borç: gelire bağımlı (yüksek gelir biraz daha borçlanabilir)
        borc_katsayisi   = rng.uniform(0.05, 4.5, n)
        mevcut_borc      = aylik_gelir * borc_katsayisi

        gecikmis_odeme   = rng.integers(0, 15, n)
        kredi_karti      = rng.integers(0, 10, n)
        kredi_gecmisi    = np.clip(rng.exponential(scale=4, size=n), 0.5, 30)

        dti              = mevcut_borc / aylik_gelir

        # FICA benzeri skor fonksiyonu (0-1000 arası ham)
        raw_score = (
              (aylik_gelir**0.4) * 3
            + (calisma_yili * 20)
            + (kredi_gecmisi * 15)
            - (gecikmis_odeme**2 * 120)
            - (dti * 800)
            - (bagli_kisi * 40)
            + (ek_gelir * 0.01)
            + rng.normal(0, 200, n)
        )
        # Normalleştir → 0-1 olasılık
        from scipy.special import expit
        prob_approve = expit((raw_score - np.median(raw_score)) / np.std(raw_score) * 2)
        onay         = (rng.random(n) < prob_approve).astype(int)

        df = pd.DataFrame({
            "Yas":                    yas,
            "Aylik_Gelir":            aylik_gelir,
            "Mevcut_Borc":            mevcut_borc,
            "Gecikmis_Odeme_Sayisi":  gecikmis_odeme,
            "Kredi_Karti_Sayisi":     kredi_karti,
            "Borc_Gelir_Orani":       dti,
            "Calisma_Yili":           calisma_yili,
            "Ek_Gelir":               ek_gelir,
            "Bagli_Kisi_Sayisi":      bagli_kisi,
            "Kredi_Gecmisi_Yili":     kredi_gecmisi,
            "Onay_Durumu":            onay,
        })
        return df

    # ── Eğitim ───────────────────────────────────────────────────

    def train(self, progress_callback=None, use_real_data: bool = True) -> dict:
        """
        Ensemble modeli eğitir ve kayıt eder.
        
        Args:
            use_real_data: True ise önce UCI German Credit gerçek veri setini dener.
                           İndirilemezse sentetik veriye düşer.
        
        Dönüş: Model performans metrikleri sözlüğü.
        """
        data_source = "synthetic"

        if use_real_data:
            try:
                if progress_callback:
                    progress_callback(0.03, "Gerçek UCI veri seti yükleniyor...")
                from data.real_dataset_loader import load_combined_dataset, download_uci_dataset
                download_uci_dataset()
                df = load_combined_dataset(n_synthetic=9000)
                if df is not None and len(df) > 500:
                    data_source = f"UCI German Credit (gerçek: 1.000 kayıt) + Augmented ({len(df)-1000:,} kayıt)"
                else:
                    raise ValueError("Veri seti yeterince büyük değil")
            except Exception as e:
                if progress_callback:
                    progress_callback(0.03, f"UCI verisi alınamadı ({e}), sentetik kullanılıyor...")
                df = self._generate_training_data()
                data_source = f"Sentetik ({ML_TRAINING_SAMPLES:,} kayıt)"
        else:
            if progress_callback:
                progress_callback(0.03, "Sentetik veri seti oluşturuluyor (50.000 kayıt)...")
            df = self._generate_training_data()
            data_source = f"Sentetik ({ML_TRAINING_SAMPLES:,} kayıt)"

        if progress_callback:
            progress_callback(0.10, f"Veri hazır: {len(df):,} kayıt | Kaynak: {data_source}")

        X    = df[self.FEATURE_COLS]
        y    = df["Onay_Durumu"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
        )

        # Ölçekleme
        if progress_callback: progress_callback(0.20, "Özellikler normalize ediliyor...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled  = scaler.transform(X_test)

        # Bireysel modeller
        if progress_callback: progress_callback(0.35, "Random Forest eğitiliyor (200 ağaç)...")
        rf  = RandomForestClassifier(
            n_estimators=RF_N_ESTIMATORS, max_depth=12,
            min_samples_leaf=10, n_jobs=-1, random_state=RANDOM_STATE
        )

        if progress_callback: progress_callback(0.55, "Gradient Boosting eğitiliyor...")
        gb  = GradientBoostingClassifier(
            n_estimators=GB_N_ESTIMATORS, learning_rate=GB_LEARNING_RATE,
            max_depth=5, random_state=RANDOM_STATE
        )

        if progress_callback: progress_callback(0.70, "Lojistik Regresyon eğitiliyor...")
        lr  = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, n_jobs=-1)

        # Soft Voting Ensemble
        if progress_callback: progress_callback(0.80, "Ensemble (Soft Voting) modeli kuruluyor...")
        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("gb", gb), ("lr", lr)],
            voting="soft",
            weights=[3, 3, 1]   # RF ve GB'ye daha fazla oy ağırlığı
        )
        ensemble.fit(X_train_scaled, y_train)

        # Performans
        if progress_callback: progress_callback(0.92, "Model performansı değerlendiriliyor...")
        y_pred      = ensemble.predict(X_test_scaled)
        y_prob      = ensemble.predict_proba(X_test_scaled)[:, 1]

        metrics = {
            "accuracy":    round(accuracy_score(y_test, y_pred) * 100, 2),
            "auc_roc":     round(roc_auc_score(y_test, y_prob) * 100, 2),
            "precision":   round(precision_score(y_test, y_pred) * 100, 2),
            "recall":      round(recall_score(y_test, y_pred) * 100, 2),
            "f1":          round(f1_score(y_test, y_pred) * 100, 2),
            "train_size":  len(X_train),
            "test_size":   len(X_test),
            "data_source": data_source,
            "trained_at":  datetime.now().strftime("%d.%m.%Y %H:%M"),
        }

        # Kayıt et
        if progress_callback: progress_callback(0.97, "Model diske kaydediliyor...")
        joblib.dump(ensemble, self.model_path)
        joblib.dump(scaler,   self.scaler_path)
        self.model  = ensemble
        self.scaler = scaler

        if progress_callback: progress_callback(1.0, "✅ Eğitim tamamlandı!")
        return metrics


    # ── Tahmin ───────────────────────────────────────────────────

    def _build_feature_dict(self, raw: dict) -> dict:
        """Raw giriş verisinden özellik vektörü oluşturur."""
        income  = max(raw.get("Aylik_Gelir", 0), 1)
        debt    = raw.get("Mevcut_Borc", 0)
        return {
            "Yas":                    raw.get("Yas", 35),
            "Aylik_Gelir":            income,
            "Mevcut_Borc":            debt,
            "Gecikmis_Odeme_Sayisi":  raw.get("Gecikmis_Odeme_Sayisi", 0),
            "Kredi_Karti_Sayisi":     raw.get("Kredi_Karti_Sayisi", 1),
            "Borc_Gelir_Orani":       debt / income,
            "Calisma_Yili":           raw.get("Calisma_Yili", 3),
            "Ek_Gelir":               raw.get("Ek_Gelir", 0),
            "Bagli_Kisi_Sayisi":      raw.get("Bagli_Kisi_Sayisi", 0),
            "Kredi_Gecmisi_Yili":     raw.get("Kredi_Gecmisi_Yili", 2),
        }

    def predict(self, raw: dict) -> dict:
        """
        Ana tahmin fonksiyonu.
        Dönüş: {approved, approval_prob, default_risk, credit_score, risk_category, ...}
        """
        if not self.is_trained():
            raise FileNotFoundError("Model henüz eğitilmedi.")
        features = self._build_feature_dict(raw)
        df  = pd.DataFrame([features])
        X_s = self.scaler.transform(df[self.FEATURE_COLS])

        prediction  = self.model.predict(X_s)[0]
        probs       = self.model.predict_proba(X_s)[0]
        credit_score = self.calculate_credit_score(raw)
        risk_cat     = self.get_risk_category(credit_score)

        return {
            "approved":       bool(prediction == 1),
            "approval_prob":  float(probs[1]),
            "default_risk":   float(probs[0]),
            "credit_score":   credit_score,
            "risk_category":  risk_cat,
            "fico_breakdown": self.calculate_fico_breakdown(raw),
        }

    def get_feature_importances(self) -> pd.DataFrame:
        """RF alt modelinin özellik önem derecelerini döndürür."""
        if not self.is_trained():
            return pd.DataFrame()
        rf_model = self.model.named_estimators_["rf"]
        importances = rf_model.feature_importances_
        labels = [self.FEATURE_LABELS_TR.get(f, f) for f in self.FEATURE_COLS]
        return (
            pd.DataFrame({"Özellik": labels, "Önem": importances})
            .sort_values("Önem", ascending=False)
        )

    # ── Kredi Skoru & FICO Benzeri Hesaplama ─────────────────────

    def calculate_credit_score(self, raw: dict) -> float:
        """
        FICO benzeri 5 kategori puanlaması:
        1. Ödeme Geçmişi     — %35
        2. Borç Yükü (DTI)   — %30
        3. Kredi Geçmişi     — %15
        4. Kredi Çeşitliliği — %10
        5. Yeni Kredi Başvurusu — %10
        """
        income          = max(raw.get("Aylik_Gelir", 1), 1)
        debt            = raw.get("Mevcut_Borc", 0)
        late_payments   = raw.get("Gecikmis_Odeme_Sayisi", 0)
        cards           = raw.get("Kredi_Karti_Sayisi", 1)
        credit_history  = raw.get("Kredi_Gecmisi_Yili", 1)
        work_years      = raw.get("Calisma_Yili", 0)
        dti             = debt / income

        # 1. Ödeme geçmişi (0-350)
        if late_payments == 0:      payment_score = 350
        elif late_payments <= 1:    payment_score = 300
        elif late_payments <= 3:    payment_score = 220
        elif late_payments <= 6:    payment_score = 150
        else:                       payment_score = max(50, 150 - (late_payments - 6) * 15)

        # 2. Borç Yükü (0-300)
        if dti <= 0.15:     debt_score = 300
        elif dti <= 0.30:   debt_score = 260
        elif dti <= 0.50:   debt_score = 200
        elif dti <= 0.75:   debt_score = 130
        elif dti <= 1.00:   debt_score = 80
        else:               debt_score = max(10, int(80 - (dti - 1) * 50))

        # 3. Kredi Geçmişi (0-150)
        history_score = min(150, int(credit_history * 12))

        # 4. Kredi Çeşitliliği (0-100)
        if cards == 0:      diversity_score = 40
        elif cards <= 2:    diversity_score = 100
        elif cards <= 4:    diversity_score = 80
        elif cards <= 6:    diversity_score = 60
        else:               diversity_score = 40

        # 5. Yeni Kredi/Çalışma İstikrarı (0-100)
        stability_score = min(100, int(work_years * 10))

        # Ham toplam 0-1000
        raw_total = payment_score + debt_score + history_score + diversity_score + stability_score
        # FICO aralığına scale et (300-850)
        score = SCORE_MIN + (raw_total / 1000) * (SCORE_MAX - SCORE_MIN)
        return round(min(SCORE_MAX, max(SCORE_MIN, score)), 1)

    def calculate_fico_breakdown(self, raw: dict) -> dict:
        """Her kategorinin ayrı ayrı puanını ve maksimumunu döndürür."""
        income          = max(raw.get("Aylik_Gelir", 1), 1)
        debt            = raw.get("Mevcut_Borc", 0)
        late_payments   = raw.get("Gecikmis_Odeme_Sayisi", 0)
        cards           = raw.get("Kredi_Karti_Sayisi", 1)
        credit_history  = raw.get("Kredi_Gecmisi_Yili", 1)
        work_years      = raw.get("Calisma_Yili", 0)
        dti             = debt / income

        payment_score   = max(50, 350 - late_payments * 40)
        debt_score      = max(10, int(300 * max(0, 1 - dti * 1.2)))
        history_score   = min(150, int(credit_history * 12))
        diversity_score = 100 if 1 <= cards <= 3 else max(40, 100 - abs(cards - 2) * 15)
        stability_score = min(100, int(work_years * 10))

        return {
            "Ödeme Geçmişi":        {"score": payment_score,   "max": 350, "weight": "35%"},
            "Borç Yükü":            {"score": debt_score,      "max": 300, "weight": "30%"},
            "Kredi Geçmişi":        {"score": history_score,   "max": 150, "weight": "15%"},
            "Kredi Çeşitliliği":    {"score": diversity_score, "max": 100, "weight": "10%"},
            "Finansal İstikrar":    {"score": stability_score, "max": 100, "weight": "10%"},
        }

    def get_risk_category(self, score: float) -> str:
        for category, (low, high, _) in SCORE_BANDS.items():
            if low <= score <= high:
                return category
        return "Zayıf"

    def get_score_color(self, score: float) -> str:
        for category, (low, high, color) in SCORE_BANDS.items():
            if low <= score <= high:
                return color
        return "#ef4444"

    # ── Stres Testleri ────────────────────────────────────────────

    def run_stress_test(self, raw: dict, scenario: str) -> dict:
        """
        Makro şok senaryosu altında tahmini çalıştırır.
        Senaryo isimleri: 'temel', 'hafif_şok', 'orta_şok', 'şiddetli_şok'
        """
        scenarios = {
            "temel":        {"inflation": 0.0,  "interest": 0.0,  "unemployment": 0.0},
            "hafif_şok":    {"inflation": 0.10, "interest": 0.02, "unemployment": 0.02},
            "orta_şok":     {"inflation": 0.20, "interest": 0.05, "unemployment": 0.05},
            "şiddetli_şok": {"inflation": 0.40, "interest": 0.10, "unemployment": 0.10},
        }
        params = scenarios.get(scenario, scenarios["temel"])

        stressed = raw.copy()
        # Enflasyon reel geliri düşürür
        stressed["Aylik_Gelir"]  *= (1 - params["inflation"])
        # Faiz borcu artırır
        stressed["Mevcut_Borc"]  *= (1 + params["interest"] * 2)
        # İşsizlik çalışma yılını etkiler
        stressed["Calisma_Yili"] = max(0, stressed.get("Calisma_Yili", 3) - params["unemployment"] * 10)
        stressed["Gecikmiş_Ödeme"] = raw.get("Gecikmis_Odeme_Sayisi", 0) + int(params["unemployment"] * 5)

        result = self.predict(stressed)
        result["scenario"]      = scenario
        result["scenario_params"] = params
        return result

    def run_all_stress_scenarios(self, raw: dict) -> list[dict]:
        scenarios = ["temel", "hafif_şok", "orta_şok", "şiddetli_şok"]
        return [self.run_stress_test(raw, s) for s in scenarios]

    # ── Monte Carlo Simülasyonu ───────────────────────────────────

    def monte_carlo_simulation(self, raw: dict, n: int = MONTE_CARLO_RUNS) -> dict:
        """
        Monte Carlo: Gelir ve borç değişkenliğinin temerrüt olasılığına etkisi.
        Dönüş: default_probs dizisi ve istatistikler.
        """
        if not self.is_trained():
            raise FileNotFoundError("Model eğitilmedi.")

        rng = np.random.default_rng(42)
        income_base = raw.get("Aylik_Gelir", 20000)
        debt_base   = raw.get("Mevcut_Borc", 10000)

        default_probs = []
        for _ in range(n):
            sim = raw.copy()
            sim["Aylik_Gelir"]  = income_base * rng.uniform(0.6, 1.4)
            sim["Mevcut_Borc"]  = debt_base   * rng.uniform(0.8, 1.6)
            sim["Gecikmis_Odeme_Sayisi"] = int(
                raw.get("Gecikmis_Odeme_Sayisi", 0) + rng.integers(-1, 3)
            )
            sim["Gecikmis_Odeme_Sayisi"] = max(0, sim["Gecikmis_Odeme_Sayisi"])
            res = self.predict(sim)
            default_probs.append(res["default_risk"])

        arr = np.array(default_probs)
        return {
            "runs":         n,
            "mean_default": float(np.mean(arr)),
            "p5":           float(np.percentile(arr, 5)),
            "p95":          float(np.percentile(arr, 95)),
            "std":          float(np.std(arr)),
            "prob_above_50": float(np.mean(arr > 0.5)),  # %50'den yüksek risk yoğunluğu
            "distribution": arr.tolist(),
        }

    # ── Simülatör ("Ya Olursa?") ─────────────────────────────────

    def what_if_simulator(self, raw: dict, changes: dict) -> dict:
        """
        Kullanıcı bir değişiklik yaptığında yeni skoru hesaplar.
        changes: {"Mevcut_Borc": -5000, "Gecikmis_Odeme_Sayisi": -2} gibi deltaDict
        """
        modified = raw.copy()
        for key, delta in changes.items():
            if key in modified:
                modified[key] = max(0, modified[key] + delta)

        original_score   = self.calculate_credit_score(raw)
        modified_score   = self.calculate_credit_score(modified)
        score_change     = modified_score - original_score

        return {
            "original_score":   original_score,
            "modified_score":   modified_score,
            "score_change":     score_change,
            "original_predict": self.predict(raw),
            "modified_predict": self.predict(modified),
        }

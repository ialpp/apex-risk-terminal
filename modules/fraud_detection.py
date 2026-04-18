"""
modules/fraud_detection.py
Anomali Tespiti & Sahtekarlık Skorlama Motoru
Isolation Forest + Kural Tabanlı Hibrit Sistem
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config import RANDOM_STATE, MODELS_DIR


class FraudDetectionEngine:
    """
    İki katmanlı sahtekarlık tespit sistemi:
    1. Kural tabanlı hızlı kontrol (anlık)
    2. Isolation Forest anomali tespiti (istatistiksel)
    """

    FRAUD_FEATURES = [
        "Yas", "Aylik_Gelir", "Mevcut_Borc", "Borc_Gelir_Orani",
        "Gecikmis_Odeme_Sayisi", "Kredi_Karti_Sayisi", "Kredi_Gecmisi_Yili"
    ]

    def __init__(self):
        base = os.path.dirname(os.path.dirname(__file__))
        self.model_path  = os.path.join(base, MODELS_DIR, "fraud_model.pkl")
        self.scaler_path = os.path.join(base, MODELS_DIR, "fraud_scaler.pkl")
        self.model  = None
        self.scaler = None
        self._load()

    def _load(self):
        try:
            self.model  = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        except Exception:
            pass

    def train_fraud_model(self, df: pd.DataFrame = None):
        """
        Normal veri üzerinde Isolation Forest eğitir.
        Anormal profiller yüksek anomali skoruyla işaretlenir.
        """
        if df is None:
            # Sentetik normal veri üret
            rng = np.random.default_rng(RANDOM_STATE)
            n   = 30000
            income  = np.clip(rng.lognormal(9.9, 0.5, n), 5500, 150000)
            df = pd.DataFrame({
                "Yas":                   rng.integers(20, 65, n),
                "Aylik_Gelir":           income,
                "Mevcut_Borc":           income * rng.uniform(0.1, 2.0, n),
                "Borc_Gelir_Orani":      rng.uniform(0.05, 1.5, n),
                "Gecikmis_Odeme_Sayisi": rng.integers(0, 8, n),
                "Kredi_Karti_Sayisi":    rng.integers(0, 6, n),
                "Kredi_Gecmisi_Yili":    rng.uniform(0.5, 20, n),
            })

        X = df[self.FRAUD_FEATURES]
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)

        model = IsolationForest(
            n_estimators=200, contamination=0.05,
            random_state=RANDOM_STATE, n_jobs=-1
        )
        model.fit(X_s)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model,  self.model_path)
        joblib.dump(scaler, self.scaler_path)
        self.model  = model
        self.scaler = scaler

    def is_trained(self) -> bool:
        return self.model is not None

    def score(self, raw: dict) -> dict:
        """
        Sahtekarlık / anomali riski hesaplar.
        Dönüş: {"fraud_score": 0-100, "risk_level": str, "flags": [str], "anomaly": bool}
        """
        flags = self._rule_based_check(raw)
        rule_score = min(100, len(flags) * 20)

        # İstatistiksel anomali
        anomaly_score = 0.0
        is_anomaly    = False
        if self.is_trained():
            income  = max(raw.get("Aylik_Gelir", 1), 1)
            debt    = raw.get("Mevcut_Borc", 0)
            feat = pd.DataFrame([{
                "Yas":                   raw.get("Yas", 35),
                "Aylik_Gelir":           income,
                "Mevcut_Borc":           debt,
                "Borc_Gelir_Orani":      debt / income,
                "Gecikmis_Odeme_Sayisi": raw.get("Gecikmis_Odeme_Sayisi", 0),
                "Kredi_Karti_Sayisi":    raw.get("Kredi_Karti_Sayisi", 1),
                "Kredi_Gecmisi_Yili":    raw.get("Kredi_Gecmisi_Yili", 2),
            }])
            X_s           = self.scaler.transform(feat[self.FRAUD_FEATURES])
            pred          = self.model.predict(X_s)[0]       # -1 = anomali
            decision      = self.model.decision_function(X_s)[0]
            anomaly_score = max(0, min(100, int((0 - decision) * 100)))
            is_anomaly    = (pred == -1)

        final_score = int(0.4 * rule_score + 0.6 * anomaly_score)
        return {
            "fraud_score":     final_score,
            "risk_level":      self._risk_label(final_score),
            "flags":           flags,
            "anomaly":         is_anomaly,
            "rule_score":      rule_score,
            "anomaly_score":   anomaly_score,
        }

    def _rule_based_check(self, raw: dict) -> list[str]:
        """Hızlı kural tabanlı bayrak kontrolü."""
        flags = []
        income  = max(raw.get("Aylik_Gelir", 1), 1)
        debt    = raw.get("Mevcut_Borc", 0)
        dti     = debt / income
        late    = raw.get("Gecikmis_Odeme_Sayisi", 0)
        cards   = raw.get("Kredi_Karti_Sayisi", 0)
        age     = raw.get("Yas", 30)
        history = raw.get("Kredi_Gecmisi_Yili", 0)

        if income > 100000 and history < 1:
            flags.append("⚠️ Çok yüksek gelir beyanı — kredi geçmişiyle uyuşmuyor")
        if dti > 4.0:
            flags.append("⚠️ Aşırı yüksek Borç/Gelir oranı (>400%)")
        if late > 10:
            flags.append("⚠️ Aşırı gecikmiş ödeme — sistematik temerrüt riski")
        if cards > 8:
            flags.append("⚠️ Olağandışı yüksek kredi kartı sayısı (>8)")
        if age < 21 and income > 50000:
            flags.append("⚠️ Çok genç yaş için yüksek gelir beyanı")
        if history < 0.5 and debt > 100000:
            flags.append("⚠️ Yeni profil — yüksek borç miktarı şüpheli")
        if income < 6000 and debt > 500000:
            flags.append("⚠️ Minimum gelir — aşırı borç miktarı")

        return flags

    def _risk_label(self, score: int) -> str:
        if score < 20:  return "Düşük"
        if score < 40:  return "Orta"
        if score < 65:  return "Yüksek"
        return "Kritik"

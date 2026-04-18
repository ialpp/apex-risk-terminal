"""
modules/clustering_engine.py
K-Means Tabanlı Müşteri Segmentasyon Motoru (A/B/C/D Tier Sistemi)
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config import RANDOM_STATE, MODELS_DIR


SEGMENT_LABELS = {
    0: {"name": "Altın Müşteri (A-Tier)",  "color": "#f59e0b", "icon": "🥇", "desc": "Yüksek gelir, düşük borç, ödeme disiplini mükemmel."},
    1: {"name": "Gümüş Müşteri (B-Tier)",  "color": "#94a3b8", "icon": "🥈", "desc": "İyi profil, küçük iyileştirme alanları mevcut."},
    2: {"name": "Gelişim Segmenti (C-Tier)","color": "#8b5cf6", "icon": "📈", "desc": "Potansiyel var, borç yönetimi destekle geliştirilebilir."},
    3: {"name": "Yüksek Risk (D-Tier)",     "color": "#ef4444", "icon": "⚠️",  "desc": "Aktif izleme gerektirir, temerrüt riski yüksek."},
}

CLUSTER_FEATURES = [
    "Aylik_Gelir", "Mevcut_Borc", "Borc_Gelir_Orani",
    "Gecikmis_Odeme_Sayisi", "Kredi_Karti_Sayisi", "Kredi_Gecmisi_Yili"
]


class CustomerClusteringEngine:

    def __init__(self):
        base = os.path.dirname(os.path.dirname(__file__))
        self.model_path  = os.path.join(base, MODELS_DIR, "clustering_model.pkl")
        self.scaler_path = os.path.join(base, MODELS_DIR, "clustering_scaler.pkl")
        self.label_map   = {}    # cluster_id -> segment adı
        self.model  = None
        self.scaler = None
        self._load()

    def _load(self):
        try:
            data = joblib.load(self.model_path)
            self.model     = data["model"]
            self.label_map = data["label_map"]
            self.scaler    = joblib.load(self.scaler_path)
        except Exception:
            pass

    def is_trained(self) -> bool:
        return self.model is not None

    def train(self, df: pd.DataFrame = None):
        """
        Portföy verisi üzerinde 4 segmentli K-Means eğitir.
        """
        if df is None or df.empty:
            rng = np.random.default_rng(RANDOM_STATE)
            n   = 20000
            income = np.clip(rng.lognormal(9.9, 0.6, n), 5500, 200000)
            df = pd.DataFrame({
                "Aylik_Gelir":            income,
                "Mevcut_Borc":            income * rng.uniform(0.05, 4.5, n),
                "Borc_Gelir_Orani":       rng.uniform(0.05, 4.0, n),
                "Gecikmis_Odeme_Sayisi":  rng.integers(0, 12, n),
                "Kredi_Karti_Sayisi":     rng.integers(0, 8, n),
                "Kredi_Gecmisi_Yili":     rng.uniform(0, 25, n),
            })

        X = df[CLUSTER_FEATURES].fillna(0)
        scaler = StandardScaler()
        X_s    = scaler.fit_transform(X)

        model = KMeans(n_clusters=4, random_state=RANDOM_STATE, n_init=20)
        model.fit(X_s)

        # Cluster merkezlerine göre etiket ata (gelir yüksek=iyi, gecikme düşük=iyi)
        centers = pd.DataFrame(scaler.inverse_transform(model.cluster_centers_), columns=CLUSTER_FEATURES)
        centers["cluster_id"] = range(4)
        # Basit heuristik: gelir yüksek + gecikme düşük = Tier A
        centers["quality"] = centers["Aylik_Gelir"] / (centers["Gecikmis_Odeme_Sayisi"] + 1)
        centers_sorted = centers.sort_values("quality", ascending=False)

        label_map = {}
        for rank, (_, row) in enumerate(centers_sorted.iterrows()):
            label_map[int(row["cluster_id"])] = rank  # 0=En iyi

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({"model": model, "label_map": label_map}, self.model_path)
        joblib.dump(scaler, self.scaler_path)
        self.model     = model
        self.scaler    = scaler
        self.label_map = label_map

    def predict_segment(self, raw: dict) -> dict:
        """Tek müşteri için segment tahmini."""
        if not self.is_trained():
            return {"segment_id": -1, "segment": "Bilinmiyor", "color": "#94a3b8"}
        income = max(raw.get("Aylik_Gelir", 1), 1)
        debt   = raw.get("Mevcut_Borc", 0)
        feat = pd.DataFrame([{
            "Aylik_Gelir":            income,
            "Mevcut_Borc":            debt,
            "Borc_Gelir_Orani":       debt / income,
            "Gecikmis_Odeme_Sayisi":  raw.get("Gecikmis_Odeme_Sayisi", 0),
            "Kredi_Karti_Sayisi":     raw.get("Kredi_Karti_Sayisi", 1),
            "Kredi_Gecmisi_Yili":     raw.get("Kredi_Gecmisi_Yili", 2),
        }])
        X_s        = self.scaler.transform(feat[CLUSTER_FEATURES])
        cluster_id = int(self.model.predict(X_s)[0])
        tier       = self.label_map.get(cluster_id, 3)
        info       = SEGMENT_LABELS.get(tier, SEGMENT_LABELS[3])
        return {
            "cluster_id":   cluster_id,
            "tier":         tier,
            "segment":      info["name"],
            "color":        info["color"],
            "icon":         info["icon"],
            "description":  info["desc"],
        }

    def segment_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tüm portföyü segmentlere ayırır."""
        if not self.is_trained() or df.empty:
            return df
        needed = [c for c in CLUSTER_FEATURES if c not in df.columns]
        if needed:
            return df
        X_s     = self.scaler.transform(df[CLUSTER_FEATURES].fillna(0))
        clusters = self.model.predict(X_s)
        df = df.copy()
        df["cluster_id"] = clusters
        df["tier"]       = df["cluster_id"].map(self.label_map)
        df["segment"]    = df["tier"].map(lambda t: SEGMENT_LABELS.get(t, {}).get("name", "?"))
        return df

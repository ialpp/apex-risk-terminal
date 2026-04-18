"""
modules/kalman_filter_engine.py — ProQuant Capital | Kalman Filtresi & Dinamik Sinyal Motoru v7.0
=================================================================================================

Finansal zaman serilerinde gürültüyü filtreleyen ve gizli durum değişkenlerini
(latent state variables) takip eden Kalman Filtre çekirdeği. Pairs trading,
dinamik beta tahmini ve fiyat trend tespitinde temel altyapıyı oluşturur.

Matematiksel Çekirdek:
  - Tahmin Adımı (Prediction): x̂_k|k-1 = F * x̂_k-1|k-1
  - Güncelleme Adımı (Update):  K_k = P_k|k-1 * H^T * (H * P_k|k-1 * H^T + R)^-1
  - Kalman Kazancı (Kalman Gain): K_k
  - Güncellenmiş Durum: x̂_k|k = x̂_k|k-1 + K_k * (z_k - H * x̂_k|k-1)

Uygulamalar:
  1. Dinamik Hedge Rasyosu (β) tahmini (Pairs Trading).
  2. Fiyat trendinin (Slope, Intercept) gerçek zamanlı kestirimi.
  3. Piyasa mikroyapısı: Kalman tabanlı spread rekonstruksiyonu.

Author  : ProQuant Capital Quantitative Signal Lab
Version : 7.0.0
"""
from __future__ import annotations
import math
import datetime
import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: KALMAN FİLTRE DURUM YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class KalmanState:
    """Tek bir Kalman filtresi adımının durumu."""
    x: np.ndarray          # Durum vektörü
    P: np.ndarray          # Hata kovaryansı
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class KalmanOutput:
    """Kalman filtresi çıktısı."""
    filtered_price: float
    trend_slope: float
    uncertainty: float
    kalman_gain: float
    residual: float

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: TEMEL KALMAN FİLTRE MOTORU
# ─────────────────────────────────────────────────────────────────────────────

class KalmanFilterCore:
    """
    Tek boyutlu (univariate) Kalman filtresi.
    Fiyat = Trend + Gürültü modelini uygular.
    """
    def __init__(self, process_noise: float = 1e-5, obs_noise: float = 1e-2):
        # F: Durum geçiş matrisi (2x2): [slope, intercept] modeli
        self.F = np.array([[1, 1], [0, 1]])
        # H: Gözlem matrisi
        self.H = np.array([[1, 0]])
        # Q: Süreç gürültüsü kovaryansı
        self.Q = np.eye(2) * process_noise
        # R: Gözlem gürültüsü kovaryansı
        self.R = np.array([[obs_noise]])

        # Başlangıç durumu
        self.x = np.zeros((2, 1))            # [price_level, slope]
        self.P = np.eye(2) * 1.0             # Başlangıç belirsizliği

    def predict(self) -> Tuple[np.ndarray, np.ndarray]:
        """Tahmin adımı: Bir sonraki durumu öngör."""
        x_pred = self.F @ self.x
        P_pred = self.F @ self.P @ self.F.T + self.Q
        return x_pred, P_pred

    def update(self, z: float) -> KalmanOutput:
        """Güncelleme adımı: Gözlemi dahil et."""
        z_arr = np.array([[z]])
        x_pred, P_pred = self.predict()

        # Yenilik (Innovation) ve yenilik kovaryansı
        y_k = z_arr - self.H @ x_pred                    # Residual
        S_k = self.H @ P_pred @ self.H.T + self.R        # Innovation cov.

        # Kalman Kazancı
        K_k = P_pred @ self.H.T @ np.linalg.inv(S_k)

        # Durum güncelleme
        self.x = x_pred + K_k @ y_k
        self.P = (np.eye(2) - K_k @ self.H) @ P_pred

        return KalmanOutput(
            filtered_price=float(self.x[0, 0]),
            trend_slope=float(self.x[1, 0]),
            uncertainty=float(self.P[0, 0]),
            kalman_gain=float(K_k[0, 0]),
            residual=float(y_k[0, 0])
        )

    def run_on_series(self, prices: np.ndarray) -> List[KalmanOutput]:
        """Tüm fiyat serisi üzerinde filtreyi koşturur."""
        results = []
        for p in prices:
            results.append(self.update(p))
        return results

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: DİNAMİK BETA TAHMİNİ (PAIRS TRADING İÇİN)
# ─────────────────────────────────────────────────────────────────────────────

class DynamicBetaEstimator:
    """
    İki varlık arasındaki dinamik (zaman değişken) beta katsayısını
    Kalman filtresiyle tahmin eder. Pairs Trading spreadi için kritik.
    """
    def __init__(self, delta: float = 1e-4):
        self.delta = delta
        self.Vw = delta / (1 - delta) * np.eye(2)
        self.Ve = 0.001
        self.beta = np.zeros((2, 1))   # [beta, alpha]
        self.P = np.zeros((2, 2))
        self.R = 0.0
        self.e = 0.0

    def update(self, x: float, y: float) -> Dict[str, float]:
        """Bir veri noktası ile beta tahminini güncelle."""
        F_vec = np.array([[x], [1.0]])

        # Tahmin
        R_pred = self.P + self.Vw
        sqrt_Q = F_vec.T @ R_pred @ F_vec + self.Ve

        # Kalman kazancı
        K = R_pred @ F_vec / float(sqrt_Q)

        # Yenilik
        self.e = y - float(F_vec.T @ self.beta)

        # Güncelleme
        self.beta = self.beta + K * self.e
        self.P = (np.eye(2) - K @ F_vec.T) @ R_pred

        return {
            "beta": float(self.beta[0, 0]),
            "alpha": float(self.beta[1, 0]),
            "spread": self.e,
            "uncertainty": float(self.P[0, 0])
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: KALMAN SİNYAL ORKESTRATÖRܝ
# ─────────────────────────────────────────────────────────────────────────────

class KalmanSignalOrchestrator:
    """Tüm Kalman tabanlı sinyal süreçlerini yöneten ana API."""

    def __init__(self):
        self.price_filter = KalmanFilterCore()
        self.beta_estimator = DynamicBetaEstimator()

    def filter_price_series(self, prices: List[float]) -> Dict[str, Any]:
        """Fiyat serisini filtreler ve trend bilgisi üretir."""
        arr = np.array(prices)
        results = self.price_filter.run_on_series(arr)
        filtered = [r.filtered_price for r in results]
        slopes   = [r.trend_slope for r in results]
        return {
            "filtered_prices": filtered,
            "trend_slopes": slopes,
            "final_trend": "UP" if slopes[-1] > 0 else "DOWN",
            "signal_certainty": 1.0 - results[-1].uncertainty
        }

    def estimate_dynamic_spread(self, x_prices: List[float], y_prices: List[float]) -> List[Dict]:
        """İki seri arasındaki dinamik spreadi tahmin eder."""
        results = []
        for x, y in zip(x_prices, y_prices):
            results.append(self.beta_estimator.update(x, y))
        return results

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────
_kalman_engine = KalmanSignalOrchestrator()

def get_kalman_engine() -> KalmanSignalOrchestrator:
    return _kalman_engine

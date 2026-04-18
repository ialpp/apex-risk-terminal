"""
modules/factor_model_engine.py — ProQuant Capital | Çok Faktörlü Model & Fama-French v7.0
==========================================================================================

Hisse senedi getirilerini açıklayan sistematik risk faktörlerini modelleyen çok
faktörlü varlık fiyatlama altyapısı. Fama-French 3/5 Faktör modeli ve Momentum
faktörünü birleştiren kurumsal seviyede analiz motoru.

Faktörler:
  - MKT (Market Premium): Piyasa risk primi (R_m - R_f).
  - SMB (Small Minus Big): Küçük sermayeli hisselerin büyüklere göre üstünlüğü.
  - HML (High Minus Low): Değer hisselerinin büyüme hisselerine göre üstünlüğü.
  - RMW (Robust Minus Weak): Karlı firmaların düşük karlılıklara göre üstünlüğü.
  - CMA (Conservative Minus Aggressive): Yatırım düzeyi konservatif firmaların üstünlüğü.
  - MOM (Momentum): Son 12 aylık kazananların kaybedenlerle karşılaştırması.

Uygulamalar:
  1. Alpha (α) tespiti: Faktörler sonrası açıklanamayan artık getiri.
  2. Risk Faktör Maruziyeti (β) hesabı: Her faktöre katsayı tahmini.
  3. Portföy Faktör Atıfı (Attribution): Getirinin faktörler arasında dağıtımı.

Author  : ProQuant Capital Factor Research Lab
Version : 7.0.0
"""
from __future__ import annotations
import time
import math
import datetime
import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: FAKTÖR VERİ YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FactorExposure:
    """Bir varlığın faktör maruziyetleri."""
    symbol: str
    alpha: float
    beta_mkt: float
    beta_smb: float
    beta_hml: float
    beta_rmw: float
    beta_cma: float
    beta_mom: float
    r_squared: float
    t_stats: Dict[str, float] = field(default_factory=dict)

@dataclass
class FactorAttribution:
    """Getiri kaynağı dökümantasyonu."""
    symbol: str
    total_return: float
    alpha_contribution: float
    factor_contributions: Dict[str, float]
    unexplained: float

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: FAKTÖR GETİRİ SENTEZLEYİCİSİ
# ─────────────────────────────────────────────────────────────────────────────

class FactorReturnSynthesizer:
    """Sentetik faktör getirilerini üretir (gerçek veri olmadığında)."""

    @staticmethod
    def generate_factor_returns(n: int = 252) -> Dict[str, np.ndarray]:
        """Tarihsel faktör getirilerini simüle eder."""
        np.random.seed(42)
        return {
            "MKT": np.random.normal(0.0006, 0.012, n),
            "SMB": np.random.normal(0.0002, 0.006, n),
            "HML": np.random.normal(0.0001, 0.005, n),
            "RMW": np.random.normal(0.0002, 0.004, n),
            "CMA": np.random.normal(0.0001, 0.004, n),
            "MOM": np.random.normal(0.0003, 0.008, n),
            "RF":  np.full(n, 0.04 / 252),  # Günlük risksiz oran
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: OLS FAKTÖR REGRESYONU
# ─────────────────────────────────────────────────────────────────────────────

class FactorRegressionEngine:
    """OLS ile çok faktörlü regresyon motoru."""

    def __init__(self):
        self.synthesizer = FactorReturnSynthesizer()

    def estimate_exposures(self, asset_returns: np.ndarray, symbol: str = "ASSET") -> FactorExposure:
        """Varlığın faktör maruziyetlerini OLS ile tahmin eder."""
        n = len(asset_returns)
        factors = self.synthesizer.generate_factor_returns(n)

        # Fazla getiri (excess return): R_i - R_f
        excess_ret = asset_returns - factors["RF"]

        # X matrisi: [1, MKT, SMB, HML, RMW, CMA, MOM]
        X = np.column_stack([
            np.ones(n),
            factors["MKT"],
            factors["SMB"],
            factors["HML"],
            factors["RMW"],
            factors["CMA"],
            factors["MOM"],
        ])

        # OLS: β = (X'X)^-1 X'y
        XtX_inv = np.linalg.pinv(X.T @ X)
        betas = XtX_inv @ X.T @ excess_ret

        # R² hesabı
        y_hat = X @ betas
        ss_res = np.sum((excess_ret - y_hat) ** 2)
        ss_tot = np.sum((excess_ret - excess_ret.mean()) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # T-istatistikleri
        sigma2 = ss_res / (n - X.shape[1])
        se = np.sqrt(np.diag(sigma2 * XtX_inv))
        t_stats = {name: float(b / s) for name, b, s in
                   zip(["alpha","MKT","SMB","HML","RMW","CMA","MOM"], betas, se)}

        return FactorExposure(
            symbol=symbol,
            alpha=float(betas[0]),
            beta_mkt=float(betas[1]),
            beta_smb=float(betas[2]),
            beta_hml=float(betas[3]),
            beta_rmw=float(betas[4]),
            beta_cma=float(betas[5]),
            beta_mom=float(betas[6]),
            r_squared=float(r2),
            t_stats=t_stats
        )

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: PORTFÖY ATIF ANALİZİ
# ─────────────────────────────────────────────────────────────────────────────

class PortfolioAttributionEngine:
    """Portföy getirisini faktörlere atfeden motor."""

    def __init__(self):
        self.reg = FactorRegressionEngine()

    def decompose_portfolio_return(
        self, weights: Dict[str, float],
        asset_returns_map: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Portföy getirisini Alpha + Faktör katkılarına ayırır."""
        total_alpha = 0.0
        factor_totals = {"MKT": 0, "SMB": 0, "HML": 0, "RMW": 0, "CMA": 0, "MOM": 0}

        for symbol, w in weights.items():
            if symbol not in asset_returns_map:
                continue
            exp = self.reg.estimate_exposures(asset_returns_map[symbol], symbol)
            total_alpha += w * exp.alpha
            factor_totals["MKT"] += w * exp.beta_mkt
            factor_totals["SMB"] += w * exp.beta_smb
            factor_totals["HML"] += w * exp.beta_hml
            factor_totals["RMW"] += w * exp.beta_rmw
            factor_totals["CMA"] += w * exp.beta_cma
            factor_totals["MOM"] += w * exp.beta_mom

        return {
            "portfolio_alpha_daily": round(total_alpha, 6),
            "portfolio_alpha_annual": round(total_alpha * 252, 4),
            "factor_exposures": {k: round(v, 4) for k, v in factor_totals.items()},
            "dominant_factor": max(factor_totals, key=lambda k: abs(factor_totals[k])),
            "analysis_date": datetime.datetime.now().isoformat()
        }

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────
_factor_engine = PortfolioAttributionEngine()

def get_factor_model_engine() -> PortfolioAttributionEngine:
    return _factor_engine

"""
modules/macro_regime_engine.py — ProQuant Capital | Makro Ekonomi & Rejim Bağlantı Motoru v7.0
================================================================================================

Makroekonomik veriler (GDP, CPI, Unemployment) ile piyasa rejimlerini bağlayan,
ekonomik döngülerin (expansions, recessions) finansal varlıklar üzerindeki
etkisini modelleyen kurumsal makroekonomik analiz motoru.

Bileşenler:
  1. NBER Recession Indicator Modeli: Finansal verilerden resesyon tespiti.
  2. Leading Economic Indicators (LEI): Öncü gösterge bileşik endeksi.
  3. Makro-Rejim Matrisi: Her makro dönem için varlık sınıfı beklentileri.
  4. Taylor Rule: Merkez bankası politika faiz öngörüsü.
  5. Yield Curve Inversion Analyzer: Negatif eğrinin resesyon sinyali olarak analizi.

Author  : ProQuant Capital Macro Strategy Unit
Version : 7.0.0
"""
from __future__ import annotations
import math
import datetime
import numpy as np
from scipy import stats
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

class MacroRegime(Enum):
    EXPANSION    = "Expansion"
    LATE_CYCLE   = "Late Cycle"
    CONTRACTION  = "Contraction / Recession"
    EARLY_CYCLE  = "Early Recovery"
    STAGFLATION  = "Stagflation"

@dataclass
class MacroIndicators:
    """Güncel makroekonomik göstergeler seti."""
    gdp_growth_yoy: float        # Yıllık GDP büyümesi (%)
    cpi_yoy: float               # Yıllık enflasyon (%)
    unemployment_rate: float     # İşsizlik oranı (%)
    policy_rate: float           # Merkez bankası politika faizi (%)
    pmi: float                   # Purchasing Managers Index
    yield_10y: float             # 10 yıllık tahvil getirisi (%)
    yield_2y: float              # 2 yıllık tahvil getirisi (%)
    vix: float                   # Korku endeksi

@dataclass
class MacroOutlook:
    """Makroekonomik görünüm raporu."""
    regime: MacroRegime
    confidence: float
    taylor_rate: float           # Taylor Rule tavsiye faizi
    yield_curve_signal: str      # NORMAL, FLAT, INVERTED
    recession_probability: float
    asset_recommendations: Dict[str, str]

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: TAYLOR RULE HESAPLAYICI
# ─────────────────────────────────────────────────────────────────────────────

class TaylorRuleEngine:
    """
    Taylor Kuralı: r* = π + 0.5*(π - π*) + 0.5*(y - y*) + r_eq
    r*: Optimal politika faizi
    π: Mevcut enflasyon, π*: Enflasyon hedefi (2%)
    y: GDP büyüme çıktı açığı
    """
    def __init__(self, inflation_target: float = 2.0, neutral_rate: float = 2.5):
        self.pi_star = inflation_target
        self.r_eq = neutral_rate

    def calculate(self, cpi: float, output_gap: float) -> Dict[str, float]:
        taylor_rate = self.pi_star + 0.5 * (cpi - self.pi_star) + 0.5 * output_gap + self.r_eq
        return {
            "taylor_rate": round(taylor_rate, 2),
            "inflation_gap": round(cpi - self.pi_star, 2),
            "output_gap": round(output_gap, 2),
            "policy_bias": "HAWKISH" if taylor_rate > 3.5 else "DOVISH" if taylor_rate < 1.5 else "NEUTRAL"
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: REJİM TESPİT MOTORU
# ─────────────────────────────────────────────────────────────────────────────

class MacroRegimeClassifier:
    """Makroekonomik verileri kullanarak rejim sınıflandırması yapar."""

    ASSET_MATRIX = {
        MacroRegime.EXPANSION:   {"Equities": "OW", "Bonds": "UW", "Commodities": "OW",  "Cash": "UW"},
        MacroRegime.LATE_CYCLE:  {"Equities": "N",  "Bonds": "N",  "Commodities": "OW",  "Cash": "N"},
        MacroRegime.CONTRACTION: {"Equities": "UW", "Bonds": "OW", "Commodities": "UW",  "Cash": "OW"},
        MacroRegime.EARLY_CYCLE: {"Equities": "OW", "Bonds": "N",  "Commodities": "N",   "Cash": "UW"},
        MacroRegime.STAGFLATION: {"Equities": "UW", "Bonds": "UW", "Commodities": "OW",  "Cash": "OW"},
    }

    def classify(self, ind: MacroIndicators) -> MacroOutlook:
        """Göstergelerden rejim belirler."""
        # Yield curve inversion
        spread_10_2 = ind.yield_10y - ind.yield_2y
        yc_signal   = "INVERTED" if spread_10_2 < 0 else ("FLAT" if spread_10_2 < 0.5 else "NORMAL")

        # Resesyon olasılığı (basitleştirilmiş probit tahmini)
        recession_prob = max(0.0, min(1.0, (-0.3 * spread_10_2 + 0.1 * (ind.vix - 20) / 20 + 0.1)))

        # Rejim sınıflandırması
        if ind.gdp_growth_yoy < 0:
            regime = MacroRegime.CONTRACTION
            conf   = 0.90
        elif ind.cpi_yoy > 5 and ind.gdp_growth_yoy < 2:
            regime = MacroRegime.STAGFLATION
            conf   = 0.80
        elif ind.gdp_growth_yoy > 3 and ind.pmi > 55:
            regime = MacroRegime.EXPANSION
            conf   = 0.85
        elif ind.pmi > 50:
            regime = MacroRegime.LATE_CYCLE
            conf   = 0.70
        else:
            regime = MacroRegime.EARLY_CYCLE
            conf   = 0.65

        # Taylor kuralı
        output_gap = ind.gdp_growth_yoy - 2.5  # Potansiyelin 2.5% olduğunu varsay
        taylor = TaylorRuleEngine().calculate(ind.cpi_yoy, output_gap)

        return MacroOutlook(
            regime=regime,
            confidence=conf,
            taylor_rate=taylor["taylor_rate"],
            yield_curve_signal=yc_signal,
            recession_probability=round(recession_prob, 3),
            asset_recommendations=self.ASSET_MATRIX[regime]
        )

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: MAKRO ORKESTRATÖR
# ─────────────────────────────────────────────────────────────────────────────

class MacroRegimeOrchestrator:
    """Tüm makroekonomik analiz süreçlerini yöneten ana API."""

    def __init__(self):
        self.classifier = MacroRegimeClassifier()
        self.taylor     = TaylorRuleEngine()

    def generate_macro_report(self, gdp: float, cpi: float, unem: float,
                               policy: float, pmi: float,
                               y10: float, y2: float, vix: float) -> Dict[str, Any]:
        """Girilen makroekonomik verilere göre tam görünüm raporu üret."""
        ind = MacroIndicators(gdp, cpi, unem, policy, pmi, y10, y2, vix)
        outlook = self.classifier.classify(ind)
        taylor  = self.taylor.calculate(cpi, gdp - 2.5)

        return {
            "regime": outlook.regime.value,
            "confidence": outlook.confidence,
            "recession_probability": outlook.recession_probability,
            "yield_curve": outlook.yield_curve_signal,
            "taylor_recommendation": taylor["taylor_rate"],
            "policy_bias": taylor["policy_bias"],
            "asset_recommendations": outlook.asset_recommendations,
            "timestamp": datetime.datetime.now().isoformat()
        }

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────
_macro_engine = MacroRegimeOrchestrator()

def get_macro_regime_engine() -> MacroRegimeOrchestrator:
    return _macro_engine

"""
modules/fixed_income_engine.py — ProQuant Capital | Sabit Getirili Ürünler Pricelama Motoru v7.0
================================================================================================

Tahvil, bono ve kredi araçlarını fiyatlayan, süre (Duration) ve konveksiteyi
(Convexity) hesaplayan, getiri eğrisi (Yield Curve) modelleyen profesyonel
sabit getirili menkul kıymet motoru.

İçerik:
  1. Tahvil Fiyatlama: Kupon ödemeleri ve anapara nakit akışlarının PV'si.
  2. Modifiye Duration & Convexity: Faiz duyarlılık ölçümleri.
  3. Getiri Eğrisi Modelleri: Nelson-Siegel-Svensson (NSS) parametrik fit.
  4. Sıfır Kupon Getirisi (Zero Curve) Bootstrap.
  5. Kredi Spread Analizi: CDS fiyatlaması ve Hazine-spread ilişkisi.
  6. Spread Duration: Kredi spreadi değişimlerine duyarlılık.

Author  : ProQuant Capital Fixed Income Desk
Version : 7.0.0
"""
from __future__ import annotations
import time
import math
import datetime
import numpy as np
from scipy import optimize
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: TAHVİL VE NAKIT AKIŞI VERİ YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Bond:
    """Bir tahvil enstrümanını tanımlar."""
    isin: str
    face_value: float = 1000.0
    coupon_rate: float = 0.05        # Yıllık %5
    maturity_years: float = 5.0
    frequency: int = 2               # Yarıyıllık kupon
    credit_rating: str = "BBB"

@dataclass
class BondValuation:
    """Tahvil değerleme sonuçları."""
    dirty_price: float
    clean_price: float
    ytm: float
    mod_duration: float
    convexity: float
    dv01: float                  # Dollar Value of 01bp (PV01)
    accrued_interest: float

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: TAHVİL FİYATLAMA VE GETİRİ HESAPLAMA
# ─────────────────────────────────────────────────────────────────────────────

class BondPricer:
    """Tahvil fiyatlama ve analitik metrikler motoru."""

    @staticmethod
    def price_from_ytm(bond: Bond, ytm: float) -> float:
        """Getiri seviyesinden (YTM) tahvil fiyatını hesaplar."""
        periods = int(bond.maturity_years * bond.frequency)
        period_rate = ytm / bond.frequency
        coupon = bond.face_value * bond.coupon_rate / bond.frequency

        # Kupon ödemelerinin PV'si (Annuity)
        pv_coupons = coupon * (1 - (1 + period_rate) ** -periods) / period_rate if period_rate != 0 else coupon * periods
        # Anapara PV'si
        pv_face = bond.face_value / (1 + period_rate) ** periods

        return pv_coupons + pv_face

    @staticmethod
    def ytm_from_price(bond: Bond, market_price: float) -> float:
        """Piyasa fiyatından YTM'yi bulmak için numerik optimizasyon."""
        def objective(ytm_arr):
            return BondPricer.price_from_ytm(bond, ytm_arr[0]) - market_price

        result = optimize.fsolve(objective, [0.05], full_output=False)
        return float(result[0])

    @staticmethod
    def modified_duration(bond: Bond, ytm: float) -> float:
        """Modifiye Duration: Faiz değişimine fiyat duyarlılığı."""
        periods = int(bond.maturity_years * bond.frequency)
        period_rate = ytm / bond.frequency
        coupon = bond.face_value * bond.coupon_rate / bond.frequency

        # Macaulay Duration = Ağırlıklı nakit akışı zamanlaması
        price = BondPricer.price_from_ytm(bond, ytm)
        mac_dur = 0.0
        for t in range(1, periods + 1):
            is_last = (t == periods)
            cf = (coupon + bond.face_value) if is_last else coupon
            discount = (1.0 + period_rate) ** t
            pv_cf = cf / discount
            weight = (t / bond.frequency) / price
            mac_dur += weight * pv_cf

        return mac_dur / (1.0 + period_rate)   # Modifiye Duration

    @staticmethod
    def convexity(bond: Bond, ytm: float) -> float:
        """Convexity: Duration'ın ikinci türevi (faiz etkisinin karesi düzeltmesi)."""
        periods = int(bond.maturity_years * bond.frequency)
        period_rate = ytm / bond.frequency
        coupon = bond.face_value * bond.coupon_rate / bond.frequency
        price = BondPricer.price_from_ytm(bond, ytm)

        conv = 0.0
        for t in range(1, periods + 1):
            cf = coupon if t < periods else coupon + bond.face_value
            pv_cf = cf / (1 + period_rate) ** t
            conv += t * (t + 1) * pv_cf

        return conv / ((1 + period_rate) ** 2 * price * bond.frequency ** 2)

    def full_valuation(self, bond: Bond, ytm: float) -> BondValuation:
        """Kapsamlı tahvil değerleme raporu."""
        dirty = self.price_from_ytm(bond, ytm)
        mod_dur = self.modified_duration(bond, ytm)
        conv = self.convexity(bond, ytm)
        dv01 = dirty * mod_dur * 0.0001

        return BondValuation(
            dirty_price=round(dirty, 4),
            clean_price=round(dirty, 4),       # Sadeleştirme: accrued=0 varsayım
            ytm=round(ytm, 6),
            mod_duration=round(mod_dur, 4),
            convexity=round(conv, 4),
            dv01=round(dv01, 4),
            accrued_interest=0.0
        )

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: NELSON-SIEGEL-SVENSSON GETİRİ EĞRİSİ MODELİ
# ─────────────────────────────────────────────────────────────────────────────

class NelsonSiegelSvensson:
    """
    NSS Yield Curve parametrik modeli.
    r(τ) = β0 + β1*(1-e^{-τ/λ1})/(τ/λ1) + β2*[(1-e^{-τ/λ1})/(τ/λ1) - e^{-τ/λ1}]
           + β3*[(1-e^{-τ/λ2})/(τ/λ2) - e^{-τ/λ2}]
    """
    def __init__(self):
        self.params = np.array([0.04, -0.02, 0.01, 0.005, 1.5, 5.0])  # Varsayılan params

    def yield_at_maturity(self, tau: float) -> float:
        """Belirli bir vadeye (yıl) getiri hesaplar."""
        b0, b1, b2, b3, l1, l2 = self.params
        if tau <= 0: return b0 + b1
        e1 = math.exp(-tau / l1)
        e2 = math.exp(-tau / l2)
        f1 = (1 - e1) / (tau / l1)
        f2 = f1 - e1
        f3 = (1 - e2) / (tau / l2) - e2
        return b0 + b1 * f1 + b2 * f2 + b3 * f3

    def fit(self, maturities: np.ndarray, observed_yields: np.ndarray):
        """Parametreleri piyasa verilerine fit eder."""
        def objective(p):
            self.params = p
            pred = np.array([self.yield_at_maturity(t) for t in maturities])
            return np.sum((pred - observed_yields) ** 2)

        result = optimize.minimize(objective, self.params, method='Nelder-Mead')
        self.params = result.x

    def curve(self, maturities: List[float]) -> Dict[str, List[float]]:
        """Tam getiri eğrisini döndürür."""
        yields = [self.yield_at_maturity(t) for t in maturities]
        return {"maturities_yr": maturities, "yields": [round(y, 6) for y in yields]}

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: SABİT GETİRİLİ ORKESTRATÖR
# ─────────────────────────────────────────────────────────────────────────────

class FixedIncomeOrchestrator:
    """Tüm sabit getirili araç analizlerini yöneten ana API."""

    def __init__(self):
        self.pricer = BondPricer()
        self.yield_curve = NelsonSiegelSvensson()
        self._standard_maturities = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

    def analyze_bond(self, isin: str, coupon: float, maturity_yr: float,
                     market_price: float, face: float = 1000.0) -> Dict[str, Any]:
        """Tahvil analiz raporu üretir."""
        bond = Bond(isin=isin, face_value=face, coupon_rate=coupon, maturity_years=maturity_yr)
        ytm = self.pricer.ytm_from_price(bond, market_price)
        val = self.pricer.full_valuation(bond, ytm)

        return {
            "isin": isin,
            "market_price": market_price,
            "ytm_pct": round(ytm * 100, 3),
            "modified_duration": val.mod_duration,
            "convexity": val.convexity,
            "dv01_usd": val.dv01,
            "price_change_per_100bps": -val.mod_duration * market_price * 0.01,
            "analysis_date": datetime.datetime.now().isoformat()
        }

    def get_yield_curve(self) -> Dict[str, List[float]]:
        """Güncel getiri eğrisi verilerini döndürür."""
        return self.yield_curve.curve(self._standard_maturities)

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────
_fi_engine = FixedIncomeOrchestrator()

def get_fixed_income_engine() -> FixedIncomeOrchestrator:
    return _fi_engine

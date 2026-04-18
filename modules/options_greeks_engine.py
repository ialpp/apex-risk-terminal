"""
modules/options_greeks_engine.py — ProQuant Capital | Opsiyon Fiyatlama & Greeks Hesaplama v7.0
================================================================================================

Black-Scholes-Merton modeli üzerine inşa edilmiş, tüm opsiyon Yunanlarını
(Delta, Gamma, Theta, Vega, Rho ve Yüksek-Dereceli Greeks) matematiksel
olarak sıfırdan hesaplayan profesyonel opsiyon analiz motoru.

Greeks:
  - Delta  (Δ): Fiyat değişimine birinci türev duyarlılığı.
  - Gamma  (Γ): Delta'nın fiyata göre türevi (eğrilik).
  - Theta  (Θ): Zaman erimesi (günlük).
  - Vega   (ν): Volatiliteye duyarlılık (1% volat. için).
  - Rho    (ρ): Faiz oranına duyarlılık.
  - Vanna    : Delta'nın volatiliteye karşı türevi (∂Δ/∂σ).
  - Charm    : Delta'nın zamana karşı türevi (∂Δ/∂t).
  - Volga    : Vega'nın volatiliteye karşı türevi.

Author  : ProQuant Capital Derivatives Desk
Version : 7.0.0
"""
from __future__ import annotations
import math
import datetime
import numpy as np
from scipy.stats import norm
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: OPSİYON VERİ YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OptionContract:
    """Bir opsiyon sözleşmesini tanımlar."""
    underlying: str
    option_type: Literal["call", "put"]
    spot: float                  # Dayanak varlık fiyatı (S)
    strike: float                # Kullanım fiyatı (K)
    time_to_expiry: float        # Vadeye kalan süre (yıl)
    risk_free_rate: float        # Risksiz oran (r)
    volatility: float            # İmplied/Historical vol (σ)
    dividend_yield: float = 0.0  # Temettü getirisi (q)

@dataclass
class GreeksResult:
    """Hesaplanan Greeks toplu sonucu."""
    price: float
    delta: float
    gamma: float
    theta_daily: float
    vega_1pct: float
    rho_100bps: float
    vanna: float
    charm: float
    volga: float
    intrinsic_value: float
    time_value: float
    d1: float
    d2: float

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: BSM ÇEKIRDEĞI VE GREEKS HESAPLAMA
# ─────────────────────────────────────────────────────────────────────────────

class BSMCore:
    """Black-Scholes-Merton formülü ve tam Greeks çekirdeği."""

    @staticmethod
    def _d1_d2(S: float, K: float, T: float, r: float, sigma: float,
               q: float = 0.0) -> tuple[float, float]:
        """d1 ve d2 parametrelerini hesaplar."""
        if T <= 0 or sigma <= 0:
            return 0.0, 0.0
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return d1, d2

    def price(self, opt: OptionContract) -> float:
        """BSM opsiyon primi."""
        S, K, T = opt.spot, opt.strike, opt.time_to_expiry
        r, sigma, q = opt.risk_free_rate, opt.volatility, opt.dividend_yield
        d1, d2 = self._d1_d2(S, K, T, r, sigma, q)

        if opt.option_type == "call":
            return S * math.exp(-q * T) * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            return K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)

    def full_greeks(self, opt: OptionContract) -> GreeksResult:
        """Tüm first ve second-order Greeks'i hesaplar."""
        S, K, T = opt.spot, opt.strike, opt.time_to_expiry
        r, sigma, q = opt.risk_free_rate, opt.volatility, opt.dividend_yield
        d1, d2 = self._d1_d2(S, K, T, r, sigma, q)
        sqrt_T = math.sqrt(T) if T > 0 else 1e-8

        N_d1  = norm.cdf(d1 if opt.option_type == "call" else -d1)
        N_d2  = norm.cdf(d2 if opt.option_type == "call" else -d2)
        n_d1  = norm.pdf(d1)    # Standard normal PDF at d1

        # Fiyat
        price = self.price(opt)

        # Delta
        if opt.option_type == "call":
            delta = math.exp(-q * T) * norm.cdf(d1)
        else:
            delta = -math.exp(-q * T) * norm.cdf(-d1)

        # Gamma (Call ve Put için eşit)
        gamma = math.exp(-q * T) * n_d1 / (S * sigma * sqrt_T)

        # Theta (günlük, yılı 365'e böl)
        if opt.option_type == "call":
            theta = (
                -S * math.exp(-q * T) * n_d1 * sigma / (2 * sqrt_T)
                - r * K * math.exp(-r * T) * norm.cdf(d2)
                + q * S * math.exp(-q * T) * norm.cdf(d1)
            ) / 365
        else:
            theta = (
                -S * math.exp(-q * T) * n_d1 * sigma / (2 * sqrt_T)
                + r * K * math.exp(-r * T) * norm.cdf(-d2)
                - q * S * math.exp(-q * T) * norm.cdf(-d1)
            ) / 365

        # Vega (σ'nın 1%-lik değişimi için)
        vega = S * math.exp(-q * T) * n_d1 * sqrt_T * 0.01

        # Rho (100bps için)
        if opt.option_type == "call":
            rho = K * T * math.exp(-r * T) * norm.cdf(d2) * 0.01
        else:
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2) * 0.01

        # İkinci dereceden Greeks
        vanna  = -math.exp(-q * T) * n_d1 * d2 / sigma
        charm  = -math.exp(-q * T) * (n_d1 * (2*(r-q)*T - d2*sigma*sqrt_T) / (2*T*sigma*sqrt_T))
        volga  = S * math.exp(-q * T) * n_d1 * sqrt_T * d1 * d2 / sigma

        # Intrinsic & Time Value
        if opt.option_type == "call":
            intrinsic = max(0, S - K)
        else:
            intrinsic = max(0, K - S)
        time_val = price - intrinsic

        return GreeksResult(
            price=round(price, 4), delta=round(delta, 5),
            gamma=round(gamma, 6), theta_daily=round(theta, 4),
            vega_1pct=round(vega, 4), rho_100bps=round(rho, 4),
            vanna=round(vanna, 6), charm=round(charm, 6), volga=round(volga, 6),
            intrinsic_value=round(intrinsic, 4), time_value=round(time_val, 4),
            d1=round(d1, 4), d2=round(d2, 4)
        )

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: VOLATİLİTE YÜZEYİ OLUŞTURUCU
# ─────────────────────────────────────────────────────────────────────────────

class VolatilitySurface:
    """İmplied Volatility yüzeyini oluşturur ve interpolasyon yapar."""

    def __init__(self):
        self.bsm = BSMCore()
        # Varsayılan yüzey: Strike % (80-120), TTM yıl (0.1-2.0)
        self._strikes_pct = [80, 85, 90, 95, 100, 105, 110, 115, 120]
        self._ttm_years   = [0.1, 0.25, 0.5, 1.0, 1.5, 2.0]

    def build_surface(self, spot: float, r: float = 0.04) -> Dict[str, Any]:
        """Tipik volatility smile/skew içeren yüzey üretir."""
        surface = {}
        for ttm in self._ttm_years:
            row = {}
            for k_pct in self._strikes_pct:
                K = spot * k_pct / 100
                # Tipik volatility skew: OTM put'lar daha yüksek vol
                atm_vol = 0.20
                skew = 0.003 * (100 - k_pct)   # Negatif skew (put tarafı daha yüksek)
                term = -0.02 * ttm              # Vade ile hafif düşüş
                iv = max(0.05, atm_vol + skew + term)
                row[f"K{k_pct}"] = round(iv, 4)
            surface[f"TTM{ttm}Y"] = row
        return surface

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: OPSİYON POZİSYON TARAYICI
# ─────────────────────────────────────────────────────────────────────────────

class OptionsGreeksOrchestrator:
    """Tüm opsiyon analizlerini yöneten ana API."""

    def __init__(self):
        self.bsm     = BSMCore()
        self.surface = VolatilitySurface()

    def analyze_option(self, underlying: str, option_type: str, spot: float,
                       strike: float, tte: float, r: float, vol: float,
                       q: float = 0.0) -> Dict[str, Any]:
        """Tek opsiyon için tam analiz raporu."""
        opt = OptionContract(underlying, option_type, spot, strike, tte, r, vol, q)
        greeks = self.bsm.full_greeks(opt)
        moneyness = "ATM" if abs(spot - strike) / spot < 0.02 \
                    else ("ITM" if (option_type == "call" and spot > strike) or
                                   (option_type == "put" and spot < strike) else "OTM")
        return {
            "underlying": underlying, "option_type": option_type.upper(),
            "moneyness": moneyness, **greeks.__dict__,
            "analysis_date": datetime.datetime.now().isoformat()
        }

    def scan_option_chain(self, spot: float, strikes: List[float],
                           ttm: float, r: float, vol: float) -> List[Dict]:
        """Tüm strike zincirini tarayıp hem call hem put Greeks döndürür."""
        chain = []
        for K in strikes:
            for ot in ["call", "put"]:
                opt = OptionContract("CHAIN", ot, spot, K, ttm, r, vol)
                g = self.bsm.full_greeks(opt)
                chain.append({"strike": K, "type": ot.upper(), **g.__dict__})
        return chain

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────
_greeks_engine = OptionsGreeksOrchestrator()

def get_options_greeks_engine() -> OptionsGreeksOrchestrator:
    return _greeks_engine

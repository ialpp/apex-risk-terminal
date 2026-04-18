"""
modules/derivatives_math.py — ProQuant Capital | Türev Ürünler Matematik Kütüphanesi v2.0
============================================================================================

Kurumsal sınıf türev ürün fiyatlama ve risk ölçüm kütüphanesi.

Desteklenen modeller:
  - Black-Scholes-Merton (BSM) vanilla opsiyon fiyatlama
  - Greeks: Delta, Gamma, Vega, Theta, Rho, Charm, Vanna, Volga
  - Heston Stokastik Volatilite Modeli (karakteristik fonksiyon yöntemi)
  - Merton Jump-Diffusion (Poisson atlamalı log-normal)
  - Variance Gamma Süreci
  - Egzotik Opsiyonlar: Bariyerli, Asya tipi, Lookback, İkili
  - Faiz Türevleri: Vasicek, CIR (Cox-Ingersoll-Ross)
  - CDS (Kredi Temerrüt Swapı) fiyatlama — reduced-form
  - Implied Volatility (Newton-Raphson + Brent)
  - Volatilite Yüzeyi İnterpolasyonu (SVI parameterizasyonu)

Author  : ProQuant Capital Quant Research
Version : 2.0.0
"""

from __future__ import annotations
import time

import math
import cmath
import statistics
import random
import itertools
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from scipy import stats as scipy_stats
from scipy import integrate as scipy_integrate
from scipy import optimize as scipy_optimize

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: SABİTLER & ENUM
# ─────────────────────────────────────────────────────────────────────────────

class OptionType(Enum):
    CALL = "call"
    PUT  = "put"

class ExerciseStyle(Enum):
    EUROPEAN = "european"
    AMERICAN = "american"

class BarrierType(Enum):
    DOWN_AND_OUT = "down_and_out"
    DOWN_AND_IN  = "down_and_in"
    UP_AND_OUT   = "up_and_out"
    UP_AND_IN    = "up_and_in"

# Sabitler
SQRT_2PI    = math.sqrt(2 * math.pi)
LN2         = math.log(2)
TRADING_DAYS= 252


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: TEMEL İSTATİSTİK YARDIMCILAR
# ─────────────────────────────────────────────────────────────────────────────

def norm_pdf(x: float) -> float:
    """Standart normal PDF."""
    return math.exp(-0.5 * x * x) / SQRT_2PI

def norm_cdf(x: float) -> float:
    """Standart normal CDF — hassas polinom yaklaşımı."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def norm_cdf_inv(p: float) -> float:
    """Normal CDF tersmatik (quantile)."""
    return scipy_stats.norm.ppf(p)

def bivariate_norm_cdf(x: float, y: float, rho: float) -> float:
    """İki boyutlu normal CDF — Drezner yaklaşımı."""
    return scipy_stats.multivariate_normal.cdf(
        [x, y], mean=[0, 0],
        cov=[[1, rho], [rho, 1]]
    )


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: BLACK-SCHOLES-MERTON
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BSMInputs:
    """BSM model girdileri."""
    S    : float   # Spot fiyat
    K    : float   # Strike
    T    : float   # Vadeye kalan süre (yıl)
    r    : float   # Risksiz faiz oranı (yıllık, sürekli)
    sigma: float   # Volatilite (yıllık)
    q    : float = 0.0   # Temettü verimi

    def _d1(self) -> float:
        if self.sigma <= 0 or self.T <= 0:
            return 0.0
        return (math.log(self.S / self.K) + (self.r - self.q + 0.5 * self.sigma**2) * self.T) / \
               (self.sigma * math.sqrt(self.T))

    def _d2(self) -> float:
        return self._d1() - self.sigma * math.sqrt(self.T)

    @property
    def d1(self) -> float:
        return self._d1()

    @property
    def d2(self) -> float:
        return self._d2()


class BlackScholesMerton:
    """
    Black-Scholes-Merton Opsiyon Fiyatlama Motoru.
    Hem call hem put fiyatı ve tüm Greeks dahil.
    """

    @staticmethod
    def price(inputs: BSMInputs, opt_type: OptionType) -> float:
        """Opsiyon fiyatı."""
        d1 = inputs.d1
        d2 = inputs.d2
        S, K, T, r, q = inputs.S, inputs.K, inputs.T, inputs.r, inputs.q

        if opt_type == OptionType.CALL:
            return (S * math.exp(-q * T) * norm_cdf(d1)
                    - K * math.exp(-r * T) * norm_cdf(d2))
        else:
            return (K * math.exp(-r * T) * norm_cdf(-d2)
                    - S * math.exp(-q * T) * norm_cdf(-d1))

    @staticmethod
    def delta(inputs: BSMInputs, opt_type: OptionType) -> float:
        """Delta: dOption/dS"""
        d1 = inputs.d1
        if opt_type == OptionType.CALL:
            return math.exp(-inputs.q * inputs.T) * norm_cdf(d1)
        else:
            return math.exp(-inputs.q * inputs.T) * (norm_cdf(d1) - 1)

    @staticmethod
    def gamma(inputs: BSMInputs) -> float:
        """Gamma: d²Option/dS²"""
        if inputs.sigma <= 0 or inputs.T <= 0:
            return 0.0
        d1   = inputs.d1
        return (math.exp(-inputs.q * inputs.T) * norm_pdf(d1)) / \
               (inputs.S * inputs.sigma * math.sqrt(inputs.T))

    @staticmethod
    def vega(inputs: BSMInputs) -> float:
        """Vega: dOption/dσ (1% değişim için)"""
        if inputs.T <= 0:
            return 0.0
        d1 = inputs.d1
        return inputs.S * math.exp(-inputs.q * inputs.T) * norm_pdf(d1) * math.sqrt(inputs.T) * 0.01

    @staticmethod
    def theta(inputs: BSMInputs, opt_type: OptionType) -> float:
        """Theta: dOption/dT (günlük)"""
        d1, d2 = inputs.d1, inputs.d2
        S, K, T, r, q, sigma = inputs.S, inputs.K, inputs.T, inputs.r, inputs.q, inputs.sigma

        if T <= 0:
            return 0.0

        term1 = -(S * math.exp(-q * T) * norm_pdf(d1) * sigma) / (2 * math.sqrt(T))

        if opt_type == OptionType.CALL:
            term2 = q * S * math.exp(-q * T) * norm_cdf(d1)
            term3 = r * K * math.exp(-r * T) * norm_cdf(d2)
            return (term1 + term2 - term3) / TRADING_DAYS
        else:
            term2 = q * S * math.exp(-q * T) * norm_cdf(-d1)
            term3 = r * K * math.exp(-r * T) * norm_cdf(-d2)
            return (term1 - term2 + term3) / TRADING_DAYS

    @staticmethod
    def rho(inputs: BSMInputs, opt_type: OptionType) -> float:
        """Rho: dOption/dr (1% değişim için)"""
        d2 = inputs.d2
        K, T, r = inputs.K, inputs.T, inputs.r
        if opt_type == OptionType.CALL:
            return K * T * math.exp(-r * T) * norm_cdf(d2) * 0.01
        else:
            return -K * T * math.exp(-r * T) * norm_cdf(-d2) * 0.01

    @staticmethod
    def vanna(inputs: BSMInputs) -> float:
        """Vanna: d²Option/(dS × dσ)"""
        d1, d2 = inputs.d1, inputs.d2
        if inputs.sigma <= 0:
            return 0.0
        return -math.exp(-inputs.q * inputs.T) * norm_pdf(d1) * d2 / inputs.sigma

    @staticmethod
    def volga(inputs: BSMInputs) -> float:
        """Volga (Vomma): d²Option/dσ²"""
        d1, d2 = inputs.d1, inputs.d2
        if inputs.sigma <= 0 or inputs.T <= 0:
            return 0.0
        return (inputs.S * math.exp(-inputs.q * inputs.T) *
                norm_pdf(d1) * math.sqrt(inputs.T) * d1 * d2 / inputs.sigma)

    @staticmethod
    def charm(inputs: BSMInputs, opt_type: OptionType) -> float:
        """Charm (Delta bleed): dDelta/dT"""
        d1, d2 = inputs.d1, inputs.d2
        T, r, q, sigma = inputs.T, inputs.r, inputs.q, inputs.sigma
        if T <= 0 or sigma <= 0:
            return 0.0

        pdf_d1 = norm_pdf(d1)
        if opt_type == OptionType.CALL:
            return (-math.exp(-q * T) *
                    (pdf_d1 * (2 * (r - q) * T - d2 * sigma * math.sqrt(T)) /
                     (2 * T * sigma * math.sqrt(T))))
        else:
            return (-math.exp(-q * T) *
                    (pdf_d1 * (2 * (r - q) * T - d2 * sigma * math.sqrt(T)) /
                     (2 * T * sigma * math.sqrt(T)) - q * norm_cdf(-d1)))

    @staticmethod
    def speed(inputs: BSMInputs) -> float:
        """Speed: dGamma/dS (3. dereceden türev)"""
        gamma = BlackScholesMerton.gamma(inputs)
        d1    = inputs.d1
        if inputs.S == 0:
            return 0.0
        return -gamma * (1 + d1 / (inputs.sigma * math.sqrt(inputs.T))) / inputs.S

    @classmethod
    def full_greeks(cls, inputs: BSMInputs, opt_type: OptionType) -> Dict[str, float]:
        """Tüm Greeks'i tek sözlükte ver."""
        price = cls.price(inputs, opt_type)
        return {
            "price" : round(price, 6),
            "delta" : round(cls.delta(inputs, opt_type), 6),
            "gamma" : round(cls.gamma(inputs), 6),
            "vega"  : round(cls.vega(inputs), 6),
            "theta" : round(cls.theta(inputs, opt_type), 6),
            "rho"   : round(cls.rho(inputs, opt_type), 6),
            "vanna" : round(cls.vanna(inputs), 6),
            "volga" : round(cls.volga(inputs), 6),
            "charm" : round(cls.charm(inputs, opt_type), 6),
            "speed" : round(cls.speed(inputs), 6),
        }

    @staticmethod
    def put_call_parity_check(call_price: float, put_price: float,
                               inputs: BSMInputs, tol: float = 0.01) -> bool:
        """Put-Call parite kontrolü."""
        lhs = call_price - put_price
        rhs = inputs.S * math.exp(-inputs.q * inputs.T) - \
              inputs.K * math.exp(-inputs.r * inputs.T)
        return abs(lhs - rhs) < tol


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: IMPLIED VOLATILITY SOLVER
# ─────────────────────────────────────────────────────────────────────────────

class ImpliedVolatilitySolver:
    """
    Piyasa fiyatlarından Implied Volatility (IV) çıkarma.
    Newton-Raphson + Brent yöntemi hibrit solver.
    """

    MAX_ITER = 200
    TOL      = 1e-7

    @classmethod
    def solve_newton_raphson(cls, market_price: float, inputs: BSMInputs,
                              opt_type: OptionType,
                              sigma0: float = 0.20) -> Optional[float]:
        """Newton-Raphson IV solver."""
        sigma = sigma0
        bsm   = BlackScholesMerton()

        for _  in range(cls.MAX_ITER):
            inp    = BSMInputs(inputs.S, inputs.K, inputs.T, inputs.r, sigma, inputs.q)
            price  = bsm.price(inp, opt_type)
            vega   = bsm.vega(inp) * 100   # vega() 1% versiyonu, burada ham vega

            diff   = price - market_price
            if abs(diff) < cls.TOL:
                return sigma

            if abs(vega) < 1e-8:
                break

            sigma -= diff / vega
            if sigma <= 0 or sigma > 10:
                break

        # Newton başarısız → Brent
        return cls.solve_brent(market_price, inputs, opt_type)

    @classmethod
    def solve_brent(cls, market_price: float, inputs: BSMInputs,
                     opt_type: OptionType,
                     lo: float = 1e-5, hi: float = 5.0) -> Optional[float]:
        """Brent yöntemi IV solver."""
        bsm = BlackScholesMerton()

        def objective(sigma):
            inp = BSMInputs(inputs.S, inputs.K, inputs.T, inputs.r, sigma, inputs.q)
            return bsm.price(inp, opt_type) - market_price

        try:
            f_lo = objective(lo)
            f_hi = objective(hi)
            if f_lo * f_hi > 0:
                return None
            result = scipy_optimize.brentq(objective, lo, hi, xtol=cls.TOL, maxiter=cls.MAX_ITER)
            return result
        except Exception:
            return None

    @classmethod
    def solve(cls, market_price: float, inputs: BSMInputs,
               opt_type: OptionType) -> Optional[float]:
        """Ana çözücü — Newton ile başla, Brent ile bitir."""
        return cls.solve_newton_raphson(market_price, inputs, opt_type)


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 5: HESTON STOKASTİK VOLATİLİTE MODELİ
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HestonParams:
    """Heston model parametreleri."""
    kappa : float   # Ortalamaya dönüş hızı
    theta : float   # Uzun vadeli volatilite (variance)
    sigma_v: float  # Volatilite of Volatility (vol-of-vol)
    rho   : float   # Spot-vol korelasyon
    v0    : float   # Başlangıç varyansı


class HestonModel:
    """
    Heston (1993) Stokastik Volatilite Modeli.
    Karakteristik Fonksiyon + Gil-Pelaez inversiyon yöntemi.

    dS = μS dt + √V S dW₁
    dV = κ(θ-V) dt + σᵥ √V dW₂
    Corr(dW₁, dW₂) = ρ dt
    """

    def __init__(self, params: HestonParams):
        self.params = params

    def characteristic_function(self, u: complex,
                                  S: float, K: float, T: float,
                                  r: float) -> complex:
        """Heston modeli karakteristik fonksiyonu."""
        p   = self.params
        kappa, theta, sigma_v, rho, v0 = p.kappa, p.theta, p.sigma_v, p.rho, p.v0

        x  = math.log(S / K)
        xi = kappa - sigma_v * rho * u * 1j
        d  = cmath.sqrt(xi**2 + sigma_v**2 * u * (u + 1j))

        g2 = (xi - d) / (xi + d)

        phi_1 = cmath.exp(1j * u * x)
        phi_2 = cmath.exp(r * T * 1j * u)
        phi_3 = ((xi - d) / sigma_v**2 *
                 ((xi - d) * T - 2 * cmath.log((1 - g2 * cmath.exp(-d * T)) / (1 - g2))))
        phi_4 = cmath.exp(kappa * theta / sigma_v**2 * phi_3)
        phi_5 = cmath.exp(v0 * (xi - d) / sigma_v**2 *
                          (1 - cmath.exp(-d * T)) / (1 - g2 * cmath.exp(-d * T)))

        return phi_1 * phi_2 * phi_4 * phi_5

    def price(self, S: float, K: float, T: float, r: float,
               opt_type: OptionType = OptionType.CALL,
               n_quad: int = 64) -> float:
        """Heston opsiyon fiyatı (Fourier inversiyon)."""
        if T <= 0:
            if opt_type == OptionType.CALL:
                return max(S - K, 0)
            return max(K - S, 0)

        discount = math.exp(-r * T)

        def integrand(u: float, j: int) -> float:
            if j == 1:
                phi = self.characteristic_function(u - 1j, S, K, T, r)
                cf_z= self.characteristic_function(-1j, S, K, T, r)
                return (phi / (cf_z * 1j * u)).real * math.cos(-u * math.log(K))
            else:
                phi = self.characteristic_function(u, S, K, T, r)
                return (phi / (1j * u)).real * math.cos(-u * math.log(K))

        nodes, weights = np.polynomial.legendre.leggauss(n_quad)
        # [0, ∞) → [-1, 1] dönüşümü: u = (1+t)/(1-t), t ∈ (-1,1)
        a, b = 1e-5, 200.0
        hmid  = (b - a) / 2
        hcent = (b + a) / 2

        I1 = hmid * sum(w * integrand(hmid * xi + hcent, 1) for xi, w in zip(nodes, weights))
        I2 = hmid * sum(w * integrand(hmid * xi + hcent, 2) for xi, w in zip(nodes, weights))

        P1 = 0.5 + I1 / math.pi
        P2 = 0.5 + I2 / math.pi

        call_price = S * P1 - K * discount * P2
        call_price = max(call_price, 0)

        if opt_type == OptionType.CALL:
            return call_price
        else:
            # Put-call parite
            return call_price - S + K * discount

    def implied_vol_surface(self, S: float, r: float,
                             strikes: List[float],
                             maturities: List[float],
                             iv_solver: ImpliedVolatilitySolver = None) -> Dict:
        """IV Yüzeyi üret."""
        if iv_solver is None:
            iv_solver = ImpliedVolatilitySolver()

        surface = {}
        for T in maturities:
            surface[T] = {}
            for K in strikes:
                heston_price = self.price(S, K, T, r, OptionType.CALL)
                base_inputs  = BSMInputs(S=S, K=K, T=T, r=r, sigma=0.20)
                iv = iv_solver.solve(heston_price, base_inputs, OptionType.CALL)
                surface[T][K] = round(iv * 100, 2) if iv else None
        return surface


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 6: MERTON JUMP-DIFFUSION MODELİ
# ─────────────────────────────────────────────────────────────────────────────

class MertonJumpDiffusion:
    """
    Merton (1976) Jump-Diffusion Modeli.
    GBM + Poisson atlama bileşeni.

    dS/S = (μ - λk̄) dt + σ dW + (J-1) dN
    J ~ LogNormal(γ, δ²), N ~ Poisson(λ)
    """

    def __init__(self, lamda: float = 0.5, gamma: float = -0.05,
                 delta: float = 0.10):
        """
        lamda: Atlama yoğunluğu (yılda ortalama atlama sayısı)
        gamma: Ortalama log-atlama büyüklüğü
        delta: Log-atlama standart sapması
        """
        self.lamda = lamda
        self.gamma = gamma
        self.delta = delta
        self.kbar  = math.exp(gamma + 0.5 * delta**2) - 1

    def price(self, S: float, K: float, T: float, r: float,
               sigma: float, opt_type: OptionType = OptionType.CALL,
               n_terms: int = 50) -> float:
        """
        Merton fiyatlama formülü — Poisson serileri toplamı.
        """
        total = 0.0
        lamda_prime = self.lamda * (1 + self.kbar)
        for n in range(n_terms):
            # n atlama için BS fiyatı
            sigma_n = math.sqrt(sigma**2 + n * self.delta**2 / T) if T > 0 else sigma
            r_n     = r - self.lamda * self.kbar + n * (self.gamma + 0.5 * self.delta**2) / T

            weight  = (math.exp(-lamda_prime * T) *
                       (lamda_prime * T) ** n /
                       math.factorial(min(n, 170)))  # overflow önlemi

            inp   = BSMInputs(S=S, K=K, T=T, r=r_n, sigma=sigma_n)
            price = BlackScholesMerton.price(inp, opt_type)
            total += weight * price

        return total

    def monte_carlo_paths(self, S0: float, T: float,
                           mu: float, sigma: float,
                           n_paths: int = 5000, n_steps: int = 252) -> np.ndarray:
        """Monte Carlo yol simülasyonu."""
        dt      = T / n_steps
        paths   = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = S0

        for t in range(1, n_steps + 1):
            # GBM
            Z     = np.random.standard_normal(n_paths)
            gbm   = ((mu - self.lamda * self.kbar - 0.5 * sigma**2) * dt
                     + sigma * math.sqrt(dt) * Z)
            # Atlamalar
            N     = np.random.poisson(self.lamda * dt, n_paths)
            jumps = np.random.normal(self.gamma, self.delta, n_paths) * N
            paths[:, t] = paths[:, t-1] * np.exp(gbm + jumps)

        return paths


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 7: EGZOTİK OPSİYONLAR
# ─────────────────────────────────────────────────────────────────────────────

class BarrierOption:
    """
    Bariyerli Opsiyonlar (Analytical — Rubinstein & Reiner 1991).
    """

    @staticmethod
    def price(S: float, K: float, H: float, T: float, r: float,
               sigma: float, q: float, rebate: float,
               barrier_type: BarrierType,
               opt_type: OptionType) -> float:
        """Bariyerli opsiyon fiyatı."""
        _phi    = 1 if opt_type == OptionType.CALL else -1
        _eta    = (-1 if barrier_type in (BarrierType.DOWN_AND_OUT,
                                          BarrierType.DOWN_AND_IN) else 1)

        mu      = (r - q - 0.5 * sigma**2) / sigma**2
        lam     = math.sqrt(mu**2 + 2 * r / sigma**2)

        x1   = math.log(S / K) / (sigma * math.sqrt(T)) + (1 + mu) * sigma * math.sqrt(T)
        x2   = math.log(S / H) / (sigma * math.sqrt(T)) + (1 + mu) * sigma * math.sqrt(T)
        y1   = math.log(H**2 / (S * K)) / (sigma * math.sqrt(T)) + (1 + mu) * sigma * math.sqrt(T)
        y2   = math.log(H / S) / (sigma * math.sqrt(T)) + (1 + mu) * sigma * math.sqrt(T)
        z    = math.log(H / S) / (sigma * math.sqrt(T)) + lam * sigma * math.sqrt(T)

        A    = _phi * S * math.exp(-q * T) * norm_cdf(_phi * x1) - \
               _phi * K * math.exp(-r * T) * norm_cdf(_phi * x1 - _phi * sigma * math.sqrt(T))
        B    = _phi * S * math.exp(-q * T) * norm_cdf(_phi * x2) - \
               _phi * K * math.exp(-r * T) * norm_cdf(_phi * x2 - _phi * sigma * math.sqrt(T))
        C    = _phi * S * (H/S)**(2*(mu+1)) * math.exp(-q * T) * norm_cdf(_eta * y1) - \
               _phi * K * math.exp(-r * T) * (H/S)**(2*mu) * norm_cdf(_eta * y1 - _eta * sigma * math.sqrt(T))
        D    = _phi * S * (H/S)**(2*(mu+1)) * math.exp(-q * T) * norm_cdf(_eta * y2) - \
               _phi * K * math.exp(-r * T) * (H/S)**(2*mu) * norm_cdf(_eta * y2 - _eta * sigma * math.sqrt(T))

        barrier_above_spot = H > S

        if barrier_type == BarrierType.DOWN_AND_OUT:
            return A - C if K >= H else B - D
        elif barrier_type == BarrierType.DOWN_AND_IN:
            vanilla = BlackScholesMerton.price(
                BSMInputs(S=S, K=K, T=T, r=r, sigma=sigma, q=q), opt_type)
            return vanilla - BarrierOption.price(S, K, H, T, r, sigma, q, rebate,
                                                 BarrierType.DOWN_AND_OUT, opt_type)
        elif barrier_type == BarrierType.UP_AND_OUT:
            return A - B + C - D if K <= H else 0.0
        elif barrier_type == BarrierType.UP_AND_IN:
            vanilla = BlackScholesMerton.price(
                BSMInputs(S=S, K=K, T=T, r=r, sigma=sigma, q=q), opt_type)
            return vanilla - BarrierOption.price(S, K, H, T, r, sigma, q, rebate,
                                                 BarrierType.UP_AND_OUT, opt_type)
        return 0.0


class AsianOption:
    """
    Asya Tipi Opsiyonlar — Monte Carlo fiyatlama.
    Ortalama fiyat (Average Price) ve Ortalama Strike varyantları.
    """

    def __init__(self, n_paths: int = 10000, n_steps: int = 100):
        self.n_paths = n_paths
        self.n_steps = n_steps

    def price_average_price(self, S: float, K: float, T: float,
                             r: float, sigma: float,
                             opt_type: OptionType = OptionType.CALL) -> Tuple[float, float]:
        """Average Price Asian opsiyon."""
        dt    = T / self.n_steps
        payoffs = []

        for _ in range(self.n_paths):
            path  = [S]
            for _ in range(self.n_steps):
                z   = random.gauss(0, 1)
                s   = path[-1] * math.exp((r - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z)
                path.append(s)

            avg = sum(path) / len(path)

            if opt_type == OptionType.CALL:
                payoffs.append(max(avg - K, 0))
            else:
                payoffs.append(max(K - avg, 0))

        mean_payoff = sum(payoffs) / self.n_paths
        std_payoff  = statistics.stdev(payoffs) if len(payoffs) > 1 else 0
        se          = std_payoff / math.sqrt(self.n_paths)

        price = mean_payoff * math.exp(-r * T)
        ci    = se * 1.96 * math.exp(-r * T)   # %95 güven aralığı
        return price, ci

    def price_average_strike(self, S: float, T: float, r: float,
                              sigma: float, opt_type: OptionType = OptionType.CALL) -> float:
        """Average Strike Asian opsiyon."""
        dt     = T / self.n_steps
        payoffs= []

        for _ in range(self.n_paths):
            path = [S]
            for _ in range(self.n_steps):
                z = random.gauss(0, 1)
                s = path[-1] * math.exp((r - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z)
                path.append(s)

            avg_K  = sum(path) / len(path)
            final  = path[-1]

            if opt_type == OptionType.CALL:
                payoffs.append(max(final - avg_K, 0))
            else:
                payoffs.append(max(avg_K - final, 0))

        return sum(payoffs) / self.n_paths * math.exp(-r * T)


class LookbackOption:
    """Lookback Opsiyonlar — Analitik fiyatlama."""

    @staticmethod
    def price_floating_strike(S: float, T: float, r: float, q: float,
                               sigma: float, S_min: float,
                               opt_type: OptionType = OptionType.CALL) -> float:
        """
        Floating Strike Lookback Call: max(Smax - Sfinal, 0)
        """
        a1 = (math.log(S / S_min) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        a2 = a1 - sigma * math.sqrt(T)
        a3 = (math.log(S / S_min) + (-r + q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))

        if opt_type == OptionType.CALL:
            price = (S * math.exp(-q * T) * norm_cdf(a1)
                     - S_min * math.exp(-r * T) * norm_cdf(a2)
                     - S * math.exp(-q * T) * sigma**2 / (2 * (r - q)) *
                     (norm_cdf(-a1) - math.exp((r - q) * T) * (S_min / S)**(2 * (r - q) / sigma**2) * norm_cdf(-a3)))
        else:
            price = (S_min * math.exp(-r * T) * norm_cdf(-a2)
                     - S * math.exp(-q * T) * norm_cdf(-a1))
        return max(price, 0)


class BinaryOption:
    """
    Digital / İkili Opsiyonlar.
    - Cash-or-Nothing: Vade anında S>K ise 1 TL ödeme
    - Asset-or-Nothing: Vade anında S>K ise S kadar ödeme
    """

    @staticmethod
    def cash_or_nothing(S: float, K: float, T: float, r: float,
                         sigma: float, cash: float = 1.0,
                         opt_type: OptionType = OptionType.CALL) -> float:
        d2 = BSMInputs(S, K, T, r, sigma).d2
        if opt_type == OptionType.CALL:
            return cash * math.exp(-r * T) * norm_cdf(d2)
        else:
            return cash * math.exp(-r * T) * norm_cdf(-d2)

    @staticmethod
    def asset_or_nothing(S: float, K: float, T: float, r: float,
                          sigma: float, q: float = 0.0,
                          opt_type: OptionType = OptionType.CALL) -> float:
        d1 = BSMInputs(S, K, T, r, sigma, q).d1
        if opt_type == OptionType.CALL:
            return S * math.exp(-q * T) * norm_cdf(d1)
        else:
            return S * math.exp(-q * T) * norm_cdf(-d1)


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 8: FAİZ TÜREV MODELLERİ
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VasicekParams:
    """Vasicek modeli parametreleri."""
    kappa: float   # Ortalamaya dönüş hızı
    theta: float   # Uzun vadeli ortalama faiz
    sigma: float   # Volatilite
    r0   : float   # Başlangıç faiz oranı


class VasicekModel:
    """
    Vasicek (1977) Faiz Oranı Modeli.
    dr = κ(θ - r) dt + σ dW

    Özellikleri:
    - Negatif faize izin verir (dezavantaj)
    - Kapalı form tahvil + opsiyon fiyatlama
    - Tek faktörlü ortalamaya dönüş
    """

    def __init__(self, params: VasicekParams):
        self.p = params

    def _B(self, T: float) -> float:
        kappa = self.p.kappa
        if kappa == 0:
            return T
        return (1 - math.exp(-kappa * T)) / kappa

    def _A(self, T: float) -> float:
        kappa, theta, sigma = self.p.kappa, self.p.theta, self.p.sigma
        B = self._B(T)
        if kappa == 0:
            return -(sigma**2 * T**3 / 6)
        term = (theta - sigma**2 / (2 * kappa**2)) * (B - T) - sigma**2 / (4 * kappa) * B**2
        return term

    def zero_coupon_bond_price(self, T: float) -> float:
        """Sıfır tahvil fiyatı: P(0,T) = exp(A(T) - B(T)r₀)"""
        return math.exp(self._A(T) - self._B(T) * self.p.r0)

    def yield_curve(self, maturities: List[float]) -> List[Tuple[float, float]]:
        """Getiri eğrisi: (vade, getiri)"""
        curve = []
        for T in maturities:
            if T <= 0:
                curve.append((T, self.p.r0))
                continue
            P   = self.zero_coupon_bond_price(T)
            y   = -math.log(P) / T
            curve.append((T, round(y * 100, 4)))
        return curve

    def simulate_path(self, T: float, n_steps: int = 252,
                       n_paths: int = 1000) -> np.ndarray:
        """Vasicek faiz yolu simülasyonu."""
        dt     = T / n_steps
        kappa, theta, sigma = self.p.kappa, self.p.theta, self.p.sigma
        paths  = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = self.p.r0

        for t in range(1, n_steps + 1):
            Z   = np.random.standard_normal(n_paths)
            dr  = kappa * (theta - paths[:, t-1]) * dt + sigma * math.sqrt(dt) * Z
            paths[:, t] = paths[:, t-1] + dr
        return paths


@dataclass
class CIRParams:
    """Cox-Ingersoll-Ross modeli parametreleri."""
    kappa: float
    theta: float
    sigma: float
    r0   : float


class CIRModel:
    """
    Cox-Ingersoll-Ross (1985) Faiz Oranı Modeli.
    dr = κ(θ - r) dt + σ√r dW

    Feller koşulu: 2κθ > σ² (negatif faize izin vermez)
    """

    def __init__(self, params: CIRParams):
        self.p = params
        self._check_feller()

    def _check_feller(self) -> bool:
        return 2 * self.p.kappa * self.p.theta > self.p.sigma**2

    def _psi(self, T: float) -> float:
        kappa, sigma = self.p.kappa, self.p.sigma
        gamma = math.sqrt(kappa**2 + 2 * sigma**2)
        return 2 * gamma * math.exp((kappa + gamma) * T / 2) / \
               (2 * gamma + (kappa + gamma) * (math.exp(gamma * T) - 1))

    def _phi(self, T: float) -> float:
        kappa, theta, sigma = self.p.kappa, self.p.theta, self.p.sigma
        gamma = math.sqrt(kappa**2 + 2 * sigma**2)
        num   = 2 * kappa * theta / sigma**2
        den_log = (2 * math.log(2 * gamma * math.exp((kappa + gamma) * T / 2) /
                                 (2 * gamma + (kappa + gamma) * (math.exp(gamma * T) - 1))))
        return num * den_log

    def zero_coupon_bond_price(self, T: float) -> float:
        r0 = self.p.r0
        return math.exp(-self._psi(T) * r0) * math.exp(self._phi(T))

    def yield_curve(self, maturities: List[float]) -> List[Tuple[float, float]]:
        curve = []
        for T in maturities:
            if T <= 0:
                curve.append((T, self.p.r0 * 100))
                continue
            P = self.zero_coupon_bond_price(T)
            y = -math.log(P) / T
            curve.append((T, round(y * 100, 4)))
        return curve


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 9: KREDİ TEMERRÜT SWAPI (CDS) FİYATLAMA
# ─────────────────────────────────────────────────────────────────────────────

class CDSPricer:
    """
    Kredi Temerrüt Swapı (CDS) Fiyatlama Motoru.
    Reduced-Form Hazard Rate modeli — J. Hull yöntemi.

    CDS Spread = (Koruma Bacağı NPV) / (Prim Bacağı BPS01)
    """

    def __init__(self, recovery_rate: float = 0.40):
        self.rr = recovery_rate

    def _survival_probability(self, t: float, hazard_rate: float) -> float:
        """Hayatta kalma olasılığı Q(t) = exp(-λt)."""
        return math.exp(-hazard_rate * t)

    def _default_probability(self, t: float, hazard_rate: float) -> float:
        """Temerrüt olasılığı F(t) = 1 - Q(t)."""
        return 1 - self._survival_probability(t, hazard_rate)

    def price_cds(self, notional: float,
                   hazard_rate: float,
                   risk_free_rate: float,
                   maturity: float,
                   payment_freq: int = 4,   # Çeyreklik
                   running_coupon: float = None) -> Dict[str, float]:
        """
        CDS fiyatlama.
        Eşit aralıklı ödemeleri kümülatif iskonto eder.
        """
        dt        = 1 / payment_freq
        n_periods = int(maturity * payment_freq)
        recovery  = self.rr

        protection_leg = 0.0
        premium_leg_bps01 = 0.0

        for i in range(1, n_periods + 1):
            t     = i * dt
            t_mid = (i - 0.5) * dt   # koruma bölümünde ara dönem kullan

            q_t   = self._survival_probability(t, hazard_rate)
            q_mid = self._survival_probability(t_mid, hazard_rate)
            df    = math.exp(-risk_free_rate * t)
            df_mid= math.exp(-risk_free_rate * t_mid)

            # Koruma bacağı katkısı (temerrüt anı: t-1 ile t arası)
            q_prev = self._survival_probability((i-1) * dt, hazard_rate)
            dp     = q_prev - q_t   # [t-1, t] arası default prob
            protection_leg    += (1 - recovery) * df_mid * dp

            # Prim bacağı (BPS01): 1 bp = 0.0001
            premium_leg_bps01 += q_t * df * dt

        fair_spread = protection_leg / max(premium_leg_bps01, 1e-10) * 10000   # baz puan

        # Çalışan bir CDS'in değerini hesapla
        if running_coupon is not None:
            model_spread  = fair_spread / 10000
            running_coupon_rate = running_coupon / 10000
            mtm = (model_spread - running_coupon_rate) * premium_leg_bps01 * notional
        else:
            mtm = 0.0

        return {
            "notional"            : notional,
            "hazard_rate_pct"     : round(hazard_rate * 100, 4),
            "fair_spread_bps"     : round(fair_spread, 2),
            "running_coupon_bps"  : running_coupon,
            "protection_leg_pct"  : round(protection_leg * 100, 4),
            "premium_bps01"       : round(premium_leg_bps01 * 10000, 4),
            "mtm_value"           : round(mtm, 2),
            "survival_t1"         : round(self._survival_probability(1, hazard_rate) * 100, 2),
            "survival_t3"         : round(self._survival_probability(3, hazard_rate) * 100, 2),
            "survival_tmat"       : round(self._survival_probability(maturity, hazard_rate) * 100, 2),
            "implied_pd_1y_pct"   : round(self._default_probability(1, hazard_rate) * 100, 2),
            "recovery_rate"       : round(recovery * 100, 1),
        }

    def cds_curve(self, hazard_rates: Dict[float, float],
                   risk_free_rate: float,
                   notional: float = 1_000_000,
                   maturities: List[float] = None) -> List[Dict]:
        """CDS spread eğrisi."""
        mats = maturities or [0.5, 1, 2, 3, 5, 7, 10]
        results = []
        for mat in mats:
            # Segmente göre hazard rate (basit lineer interpolasyon)
            sorted_tenors = sorted(hazard_rates.keys())
            if mat <= sorted_tenors[0]:
                hr = hazard_rates[sorted_tenors[0]]
            elif mat >= sorted_tenors[-1]:
                hr = hazard_rates[sorted_tenors[-1]]
            else:
                for i in range(len(sorted_tenors) - 1):
                    if sorted_tenors[i] <= mat <= sorted_tenors[i+1]:
                        t1, t2 = sorted_tenors[i], sorted_tenors[i+1]
                        w      = (mat - t1) / (t2 - t1)
                        hr     = hazard_rates[t1] + w * (hazard_rates[t2] - hazard_rates[t1])
                        break
                else:
                    hr = list(hazard_rates.values())[-1]

            cds = self.price_cds(notional, hr, risk_free_rate, mat)
            cds["maturity"] = mat
            results.append(cds)
        return results


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 10: VOLATİLİTE YÜZEYİ — SVI PARAMETRİZASYONU
# ─────────────────────────────────────────────────────────────────────────────

class SVIVolatilitySurface:
    """
    SVI (Stochastic Volatility Inspired) Volatilite Yüzeyi.
    Gatheral (2004) parametrik model.

    w(k) = a + b(ρ(k-m) + √((k-m)² + σ²))
    k = log-moneyness = ln(K/F)
    """

    def __init__(self, a: float = 0.04, b: float = 0.8,
                 rho: float = -0.3, m: float = 0.0, sigma: float = 0.1):
        self.a     = a
        self.b     = b
        self.rho   = rho
        self.m     = m
        self.sigma = sigma

    def total_variance(self, k: float) -> float:
        """Toplam varyans w(k)."""
        inner = math.sqrt((k - self.m)**2 + self.sigma**2)
        return self.a + self.b * (self.rho * (k - self.m) + inner)

    def implied_vol(self, k: float, T: float) -> float:
        """Implied volatilite."""
        w = self.total_variance(k)
        if w < 0 or T <= 0:
            return 0.20
        return math.sqrt(max(w / T, 0))

    def surface_grid(self, log_moneyness: List[float],
                      maturities    : List[float]) -> Dict[str, Any]:
        """Vol yüzeyi grid hesaplama."""
        grid = {}
        for T in maturities:
            row = {}
            for k in log_moneyness:
                iv = self.implied_vol(k, T)
                row[round(k, 3)] = round(iv * 100, 2)
            grid[T] = row

        # Arb-free kontroller
        min_iv = min(v for row in grid.values() for v in row.values() if v > 0)
        max_iv = max(v for row in grid.values() for v in row.values() if v > 0)

        return {
            "grid"       : grid,
            "min_iv_pct" : min_iv,
            "max_iv_pct" : max_iv,
            "atm_term_structure": {T: round(self.implied_vol(0.0, T) * 100, 2) for T in maturities},
            "skew_1y"    : round((self.implied_vol(-0.10, 1.0) - self.implied_vol(0.10, 1.0)) * 100, 2),
        }

    @classmethod
    def fit_to_market(cls, log_moneyness: List[float],
                       market_ivs     : List[float],
                       T              : float) -> "SVIVolatilitySurface":
        """Piyasa datası ile SVI kalibrasyon (basit LS)."""
        market_variances = [iv**2 * T for iv in market_ivs]

        def objective(params):
            a, b, rho, m, sigma = params
            if b < 0 or sigma < 0 or abs(rho) >= 1:
                return 1e10
            svi = cls(a, b, rho, m, sigma)
            return sum((svi.total_variance(k) - w)**2
                       for k, w in zip(log_moneyness, market_variances))

        x0     = [0.04, 0.8, -0.3, 0.0, 0.1]
        bounds = [(0, 1), (0, 5), (-0.999, 0.999), (-2, 2), (0.001, 2)]
        try:
            result = scipy_optimize.minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
            a, b, rho, m, sigma = result.x
            return cls(a, b, rho, m, sigma)
        except Exception:
            return cls()   # Varsayılan parametreler


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 11: TÜREV ÜRÜN ANALYZ ORKESTRATÖRÜ
# ─────────────────────────────────────────────────────────────────────────────

class DerivativesPricingEngine:
    """
    Türev Ürün Fiyatlama Orkestratörü.
    Streamlit UI'ından tek noktadan erişim.
    """

    def __init__(self):
        self.bsm         = BlackScholesMerton()
        self.iv_solver   = ImpliedVolatilitySolver()
        self.asian       = AsianOption()
        self.cds_pricer  = CDSPricer()

    def price_vanilla(self, S: float, K: float, T: float, r: float,
                       sigma: float, q: float = 0.0) -> Dict[str, Any]:
        """Vanilla call ve put fiyatları + Greeks."""
        inp   = BSMInputs(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
        call  = self.bsm.full_greeks(inp, OptionType.CALL)
        put   = self.bsm.full_greeks(inp, OptionType.PUT)
        parity= self.bsm.put_call_parity_check(call["price"], put["price"], inp)

        return {
            "call"          : call,
            "put"           : put,
            "put_call_parity": "✅ Geçerli" if parity else "❌ İhlal",
            "moneyness"     : "ITM" if S > K else "OTM" if S < K else "ATM",
            "intrinsic_call": max(S - K, 0),
            "intrinsic_put" : max(K - S, 0),
            "time_value_call": max(call["price"] - max(S - K, 0), 0),
            "inputs"        : {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "q": q}
        }

    def price_heston(self, S: float, K: float, T: float, r: float,
                      heston_params: HestonParams) -> Dict[str, float]:
        """Heston fiyat + IV karşılaştırması."""
        model      = HestonModel(heston_params)
        call_price = model.price(S, K, T, r, OptionType.CALL)
        put_price  = model.price(S, K, T, r, OptionType.PUT)

        # BSM implied vol
        inp   = BSMInputs(S=S, K=K, T=T, r=r, sigma=0.20)
        iv    = self.iv_solver.solve(call_price, inp, OptionType.CALL)

        return {
            "call_price"     : round(call_price, 6),
            "put_price"      : round(put_price, 6),
            "heston_iv_pct"  : round((iv or 0) * 100, 2),
        }

    def run_full_analysis(self, S: float = 100.0, K: float = 100.0,
                           T: float = 1.0, r: float = 0.12,
                           sigma: float = 0.25, q: float = 0.0) -> Dict[str, Any]:
        """Türev ürün tam analiz paketi."""
        # Vanilla
        vanilla = self.price_vanilla(S, K, T, r, sigma, q)

        # Merton Jump
        mjd     = MertonJumpDiffusion()
        mjd_call= mjd.price(S, K, T, r, sigma, OptionType.CALL)
        mjd_put = mjd.price(S, K, T, r, sigma, OptionType.PUT)

        # Asian
        asian_c, asian_ci = self.asian.price_average_price(S, K, T, r, sigma, OptionType.CALL)

        # Barrier — Down & Out
        barrier_do = BarrierOption.price(
            S, K, S * 0.85, T, r, sigma, q, 0.0,
            BarrierType.DOWN_AND_OUT, OptionType.CALL
        )

        # CDS
        cds = self.cds_pricer.price_cds(1_000_000, 0.015, r, T)

        # SVI Vol Surface
        svi  = SVIVolatilitySurface()
        surf = svi.surface_grid(
            log_moneyness=[-0.20, -0.10, 0.0, 0.10, 0.20],
            maturities=[0.25, 0.5, 1.0, 2.0]
        )

        return {
            "vanilla"         : vanilla,
            "merton_jump"     : {"call": round(mjd_call, 4), "put": round(mjd_put, 4)},
            "asian_arithmetic": {"call": round(asian_c, 4), "ci_95": round(asian_ci, 4)},
            "barrier_do_call" : round(barrier_do, 4),
            "cds"             : cds,
            "vol_surface"     : surf,
            "analysis_ts"     : datetime.datetime.now().isoformat(),
        }


def get_derivatives_engine() -> DerivativesPricingEngine:
    return DerivativesPricingEngine()

"""
modules/credit_structuring_engine.py — ProQuant Capital | Egzotik Kredi Yapılandırma & Tranche Motoru v2.0
=====================================================================================================

Karmaşık kredi türevleri ve yapılandırılmış finansman (Structured Finance) ürünleri için analiz motoru.
CDO, CLO ve sentetik risk transferi (SRT) işlemlerinin modellenmesi.

Kapsam:
  - Tranche Mimarisi: Senior, Mezzanine ve Equity dilimlerinin oluşturulması.
  - Attachment/Detachment Points: Zarar eşiklerinin ve koruma katmanlarının belirlenmesi.
  - Waterfall Simulation: Nakit akışlarının (Faiz ve Anapara) dilimler arası dağılımı.
  - Default Correlation: Gaussian Copula modeli ile temerrüt kümelenmesi (clustering) simülasyonu.
  - Credit Enhancement: Over-collateralization ve Spread Account mekanizmaları.
  - Sensitivity Analysis: Korelasyon şoklarına karşı tranche değer değişimi (Delto/Gamma).
  - Rating Distribution: Moody's/S&P ölçeğinde dilim bazlı kredi notu atama.

Author  : ProQuant Capital Structured Finance Desk
Version : 2.0.0
"""

from __future__ import annotations

import math
import enum
import uuid
import random
import datetime
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.stats import norm

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: TRANCHE (DİLİM) TANIMI
# ─────────────────────────────────────────────────────────────────────────────

class TrancheRank(enum.Enum):
    SENIOR    = "Senior"
    MEZZANINE = "Mezzanine"
    EQUITY    = "Equity / First Loss"

@dataclass
class Tranche:
    """Yapılandırılmış bir kredi ürününün tek bir dilimi."""
    name: str
    rank: TrancheRank
    notional: float
    attachment_point: float  # Zararın başladığı % eşik
    detachment_point: float  # Dilimin tamamen tükendiği % eşik
    coupon_rate: float       # Dilim sahiplerine ödenen faiz (bps/year)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    current_loss: float = 0.0
    
    @property
    def thickness(self) -> float:
        """Dilimin toplam havuz içindeki % büyüklüğü."""
        return self.detachment_point - self.attachment_point

    def calculate_loss(self, pool_loss_pct: float) -> float:
        """Havuzdaki toplam zarar oranına göre bu dilimin zararını hesapla."""
        # Zarar attachment point'in altındaysa 0
        effective_loss = max(0, min(pool_loss_pct - self.attachment_point, self.thickness))
        self.current_loss = (effective_loss / self.thickness) * self.notional if self.thickness > 0 else 0
        return self.current_loss

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: KREDİ HAVUZU (COLLATERAL POOL)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CollateralAsset:
    """Havuzdaki tek bir kredi varlığı."""
    id: str
    notional: float
    pd: float         # Temerrüt olasılığı
    lgd: float        # Zarar oranı
    sector: str
    is_defaulted: bool = False

class CreditPool:
    """Yapılandırma için kullanılan kredi havuzu."""
    def __init__(self, size: int = 100, total_notional: float = 1_000_000_000):
        self.assets: List[CollateralAsset] = []
        self._generate_random_pool(size, total_notional)

    def _generate_random_pool(self, size: int, total_notional: float):
        asset_val = total_notional / size
        sectors = ["Havacılık", "Enerji", "Teknoloji", "İnşaat", "Finans"]
        for i in range(size):
            self.assets.append(CollateralAsset(
                id=f"A-{i+1:03d}",
                notional=asset_val,
                pd=random.uniform(0.01, 0.08),
                lgd=0.45,
                sector=random.choice(sectors)
            ))

    @property
    def total_notional(self) -> float:
        return sum(a.notional for a in self.assets)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: YAPILANDIRMA MOTORU (STRUCTURING ENGINE)
# ─────────────────────────────────────────────────────────────────────────────

class StructuringEngine:
    """CDO/CLO yapısını kuran ve stres testi yapan motor."""

    def __init__(self, pool: CreditPool):
        self.pool = pool
        self.tranches: List[Tranche] = []

    def create_standard_structure(self):
        """Klasik bir CDO yapısı oluştur."""
        total = self.pool.total_notional
        
        self.tranches = [
            Tranche("Class A (Senior)", TrancheRank.SENIOR, total * 0.80, 0.20, 1.00, 150),
            Tranche("Class B (Mezzanine)", TrancheRank.MEZZANINE, total * 0.15, 0.05, 0.20, 450),
            Tranche("Equity (Residual)", TrancheRank.EQUITY, total * 0.05, 0.00, 0.05, 1200)
        ]

    def simulate_default_scenario(self, correlation: float = 0.3) -> Dict[str, Any]:
        """
        Gaussian Copula Simülasyonu.
        Varlıklar arası korelasyonu (Asset Correlation) hesaba katarak temerrütleri simüle eder.
        """
        n_assets = len(self.pool.assets)
        U = np.random.normal(0, 1, n_assets)
        M = np.random.normal(0, 1)  # Piyasa faktörü (Common Factor)
        
        # Latent variables (Varlık getirileri simülasyonu)
        Z = math.sqrt(correlation) * M + math.sqrt(1 - correlation) * U
        
        pool_loss = 0.0
        defaults_count = 0
        
        for i, asset in enumerate(self.pool.assets):
            # Temerrüt eşiği: norm.ppf(asset.pd)
            threshold = norm.ppf(asset.pd)
            if Z[i] < threshold:
                pool_loss += asset.notional * asset.lgd
                defaults_count += 1
        
        pool_loss_pct = pool_loss / self.pool.total_notional
        
        # Dilim bazlı zarar dağıtımı (Waterfall)
        tranche_results = []
        for t in self.tranches:
            loss = t.calculate_loss(pool_loss_pct)
            tranche_results.append({
                "name": t.name,
                "loss_amount": round(loss, 2),
                "loss_pct": round(loss / t.notional * 100, 2) if t.notional > 0 else 0,
                "remaining_notional": round(t.notional - loss, 2)
            })
            
        return {
            "pool_loss_total": round(pool_loss, 2),
            "pool_loss_pct": round(pool_loss_pct * 100, 2),
            "defaults_count": defaults_count,
            "correlation_used": correlation,
            "tranche_impacts": tranche_results
        }

    def run_monte_carlo(self, iterations: int = 1000, correlation: float = 0.3) -> Dict[str, Any]:
        """Binlerce senaryo çalıştırıp Expected Loss (EL) hesapla."""
        results = []
        for _ in range(iterations):
            results.append(self.simulate_default_scenario(correlation))
            
        avg_loss = sum(r["pool_loss_pct"] for r in results) / iterations
        tranche_el = collections.defaultdict(float)
        
        for r in results:
            for t_res in r["tranche_impacts"]:
                tranche_el[t_res["name"]] += t_res["loss_pct"]
        
        summary = {
            "avg_pool_loss_pct": round(avg_loss, 2),
            "max_pool_loss_pct": round(max(r["pool_loss_pct"] for r in results), 2),
            "tranche_expected_losses": {name: round(total / iterations, 2) for name, total in tranche_el.items()}
        }
        
        return summary

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def get_structuring_engine(size: int = 100) -> StructuringEngine:
    pool = CreditPool(size=size)
    engine = StructuringEngine(pool)
    engine.create_standard_structure()
    return engine

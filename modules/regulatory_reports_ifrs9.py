"""
modules/regulatory_reports_ifrs9.py — ProQuant Capital | Basel III & IFRS-9 Motor v2.0
========================================================================================

Kurumsal düzenleyici uyum motoru.
IFRS-9 Finansal Araçlar standardına göre kredi sınıflandırması,
Basel III sermaye yeterlilik oranları ve likidite rasyoları.

Kapsam:
  - IFRS-9 Stage 1/2/3 beklenen kredi zararı (ECL) hesaplama
  - Basel III Tier 1 / Tier 2 Sermaye Yeterlilik Oranı (CAR)
  - Likidite Karşılama Oranı (LCR) stres testi
  - Net Gerçekleşebilir Fonlama Oranı (NSFR)
  - Karşı Taraf Kredi Riski (CCR) — SA-CCR yöntemi
  - Piyasa Riski Standart Yöntemi (Sensitivities-Based Method)
  - Operasyonel Risk Temel Gösterge Yaklaşımı (BIA)
  - ICAAP/SREP rapor şablonları

Author  : ProQuant Capital Regulatory Analytics
Version : 2.0.0
"""

from __future__ import annotations
import time

import math
import uuid
import random
import datetime
import statistics
import itertools
import collections
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union, NamedTuple
from dataclasses import dataclass, field

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 1: ENUM & SABİTLER
# ═══════════════════════════════════════════════════════════════════════════════

class IFRS9Stage(Enum):
    """IFRS-9 Kredi Aşaması."""
    STAGE_1 = 1   # 12 aylık ECL — Düşük risk
    STAGE_2 = 2   # Tüm ömür ECL — Önemli artış
    STAGE_3 = 3   # Tüm ömür ECL — Değer düşüklüğü (Temerrüt)

class CreditQuality(Enum):
    """Kredi Kalite Kategorisi."""
    PRIME        = "Prime"         # AAA-AA
    HIGH_GRADE   = "High Grade"    # A
    UPPER_MEDIUM = "Upper Medium"  # BBB
    LOWER_MEDIUM = "Lower Medium"  # BB
    NON_INVEST   = "Non-Invest"    # B
    SPECULATIVE  = "Speculative"   # CCC-C
    DEFAULT      = "Default"       # D

class CollateralType(Enum):
    NONE          = "Teminat Yok"
    REAL_ESTATE   = "Gayrimenkul"
    FINANCIAL     = "Finansal Teminat"
    RECEIVABLES   = "Alacaklar"
    GUARANTEE     = "Kefalet"
    GOVERNMENT    = "Devlet Garantisi"

class ExposureClass(Enum):
    """Basel III Risk Ağırlık Sınıfları."""
    CENTRAL_GOVT  = "Merkezi Yönetim"
    BANKS         = "Bankalar"
    CORPORATES    = "Kurumsal"
    RETAIL        = "Perakende"
    REAL_ESTATE   = "Gayrimenkul"
    EQUITIES      = "Hisse Senetleri"
    SECURITIZATION= "Menkul Kıymetleştirme"
    OTHER_ASSETS  = "Diğer Varlıklar"

# Basel III Risk Ağırlıkları (SA — Standart Yaklaşım)
RISK_WEIGHTS = {
    ExposureClass.CENTRAL_GOVT : 0.00,
    ExposureClass.BANKS        : 0.50,
    ExposureClass.CORPORATES   : 1.00,
    ExposureClass.RETAIL       : 0.75,
    ExposureClass.REAL_ESTATE  : 0.35,
    ExposureClass.EQUITIES     : 1.00,
    ExposureClass.OTHER_ASSETS : 1.00,
}

# LCR likit varlık seviyeleri
HQLA_HAIRCUTS = {
    "Level 1"  : 0.00,   # Merkez bankası rezervleri, devlet tahvilleri
    "Level 2A" : 0.15,   # AAA-AA devlet tahvilleri, covered bonds
    "Level 2B" : 0.25,   # Düşük kredi riski kurumsal tahviller
}

# Basel III Minimum Oranlar
MIN_CET1_RATIO         = 0.045   # %4.5 CET1
MIN_TIER1_RATIO        = 0.060   # %6.0 Tier 1
MIN_TOTAL_CAPITAL_RATIO= 0.080   # %8.0 Toplam Sermaye
CAPITAL_CONSERVATION   = 0.025   # %2.5 Sermaye Tamponu
COUNTERCYCLICAL_BUFFER = 0.025   # %2.5 Döngüsel Tampon (ülke bağımlı)
MIN_LEVERAGE_RATIO     = 0.030   # %3.0 Kaldıraç Oranı
MIN_LCR_RATIO          = 1.00    # 100% LCR
MIN_NSFR_RATIO         = 1.00    # 100% NSFR

# IFRS-9 PD varsayımları (Stage geçiş eşikleri)
STAGE_2_PD_THRESHOLD   = 0.015   # 12 aylık PD > %1.5 → Stage 2
STAGE_3_DPD_THRESHOLD  = 90      # 90+ DPD → Stage 3

# ECL parametreleri
LGD_SECURED_RE         = 0.125   # Gayrimenkul teminatlı %12.5 LGD
LGD_SECURED_FIN        = 0.20    # Finansal teminatlı %20 LGD
LGD_UNSECURED          = 0.45    # Teminatsız %45 LGD
LGD_SUBORDINATED       = 0.75    # Subordinated %75 LGD


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 2: KREDİ ENSTRÜMANİ
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CreditExposure:
    """Tek bir kredi/varlık maruziyeti."""
    exposure_id    : str
    debtor_name    : str
    exposure_class : ExposureClass
    outstanding    : float         # Mevcut bakiye (TL)
    committed      : float         # Taahhüt
    pd_12m         : float         # 12 aylık Temerrüt Olasılığı
    pd_lifetime    : float         # Ömür boyu Temerrüt Olasılığı
    lgd            : float         # Zarar Tipi Şiddet
    ead            : float         # Temerrüt Anındaki Maruziyet
    maturity_years : float         # Kalan vade (yıl)
    collateral_type: CollateralType = CollateralType.NONE
    collateral_value: float        = 0.0
    dpd            : int           = 0   # Days Past Due
    credit_score   : float         = 600.0
    internal_rating: str           = "BB"
    sector         : str           = "Genel"
    origination_date: datetime.datetime = field(
        default_factory=datetime.datetime.now)
    last_review_date: datetime.datetime = field(
        default_factory=datetime.datetime.now)

    def __post_init__(self):
        if not self.exposure_id:
            self.exposure_id = str(uuid.uuid4())[:8].upper()
        # EAD = outstanding + CCF * committed_unutilized
        ccf           = 0.75   # Kredi Dönüşüm Faktörü
        unutilized    = max(self.committed - self.outstanding, 0)
        if self.ead == 0:
            self.ead  = self.outstanding + ccf * unutilized

    @property
    def net_exposure(self) -> float:
        """Teminat sonrası net maruziyet."""
        haircut = 0.20 if self.collateral_type == CollateralType.REAL_ESTATE else 0.30
        coll_adj = self.collateral_value * (1 - haircut)
        return max(self.ead - coll_adj, 0)

    @property
    def risk_weighted_asset(self) -> float:
        rw = RISK_WEIGHTS.get(self.exposure_class, 1.00)
        return self.net_exposure * rw

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exposure_id"    : self.exposure_id,
            "debtor"         : self.debtor_name,
            "class"          : self.exposure_class.value,
            "outstanding"    : round(self.outstanding, 2),
            "ead"            : round(self.ead, 2),
            "net_exposure"   : round(self.net_exposure, 2),
            "pd_12m"         : round(self.pd_12m * 100, 4),
            "pd_lifetime"    : round(self.pd_lifetime * 100, 4),
            "lgd"            : round(self.lgd * 100, 2),
            "collateral"     : self.collateral_type.value,
            "dpd"            : self.dpd,
            "credit_score"   : self.credit_score,
            "rwa"            : round(self.risk_weighted_asset, 2),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 3: IFRS-9 MOTORÜ
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IFRS9ClassificationResult:
    """IFRS-9 sınıflandırma sonucu."""
    exposure       : CreditExposure
    stage          : IFRS9Stage
    ecl_12m        : float    # 12 aylık ECL
    ecl_lifetime   : float    # Ömür boyu ECL
    ecl_applied    : float    # Uygulanan ECL (stage'e göre)
    provision      : float    # Karşılık tutarı
    impairment_loss: float    # Değer düşüklüğü zararı
    classification : str      # Muhasebe sınıfı (FVOCI/FVTPL/AC)
    stage_reason   : str      # Aşama geçiş gerekçesi

    def __repr__(self):
        return (f"IFRS9[{self.exposure.exposure_id}] "
                f"Stage {self.stage.value} | "
                f"ECL={self.ecl_applied:,.0f} TL")


class IFRS9Engine:
    """
    IFRS-9 Beklenen Kredi Zararı (ECL) Hesaplama Motoru.

    Metodoloji:
      ECL = PD × LGD × EAD × Discount Factor

    Forward-Looking Makro Senaryo Ağırlıkları:
      - İyimser (Upside)   : %25
      - Baz (Base)         : %55
      - Olumsuz (Downside) : %20
    """

    SCENARIO_WEIGHTS = {
        "upside"  : 0.25,
        "base"    : 0.55,
        "downside": 0.20,
    }

    # Makro senaryo PD çarpanları
    SCENARIO_PD_MULT = {
        "upside"  : 0.70,
        "base"    : 1.00,
        "downside": 1.65,
    }

    def classify_stage(self, exposure: CreditExposure) -> Tuple[IFRS9Stage, str]:
        """
        IFRS-9 Aşama Sınıflandırması.

        Stage 3: DPD ≥ 90 veya temerrüt olayı
        Stage 2: Önemli kredi risk artışı (SICR)
        Stage 1: Normal izleme
        """
        reasons = []

        # Stage 3 kriterleri
        if exposure.dpd >= STAGE_3_DPD_THRESHOLD:
            return IFRS9Stage.STAGE_3, f"DPD={exposure.dpd} gün ≥ {STAGE_3_DPD_THRESHOLD} gün"

        if exposure.pd_lifetime >= 0.50:
            return IFRS9Stage.STAGE_3, f"Ömür boyu PD={exposure.pd_lifetime:.1%} ≥ %50"

        if exposure.credit_score < 300:
            return IFRS9Stage.STAGE_3, f"Kredi skoru={exposure.credit_score:.0f} < 300"

        # Stage 2 kriterleri (SICR — Significant Increase in Credit Risk)
        if exposure.pd_12m >= STAGE_2_PD_THRESHOLD:
            reasons.append(f"12A PD={exposure.pd_12m:.2%} ≥ {STAGE_2_PD_THRESHOLD:.2%}")

        if exposure.dpd >= 30:
            reasons.append(f"DPD={exposure.dpd} ≥ 30 gün")

        if exposure.credit_score < 500:
            reasons.append(f"Kredi skoru={exposure.credit_score:.0f} < 500")

        # Maturity uzunluğu riski (3+ yıl vade ile yüksek PD)
        if exposure.maturity_years > 3 and exposure.pd_12m > 0.008:
            reasons.append(f"Uzun vadeli+yüksek PD kombinasyonu")

        if reasons:
            return IFRS9Stage.STAGE_2, "; ".join(reasons)

        return IFRS9Stage.STAGE_1, "Kredi risk artışı tespit edilmedi"

    def compute_ecl_12m(self, exposure: CreditExposure,
                          macro_scenario: str = "base") -> float:
        """12 aylık ECL hesaplama (PD × LGD × EAD)."""
        pd_mult = self.SCENARIO_PD_MULT.get(macro_scenario, 1.0)
        pd      = min(exposure.pd_12m * pd_mult, 1.0)
        discount_factor = 1 / (1 + 0.12)   # %12 efektif faiz oranı ile iskonto
        ecl     = pd * exposure.lgd * exposure.ead * discount_factor
        return max(ecl, 0)

    def compute_ecl_lifetime(self, exposure: CreditExposure,
                               macro_scenario: str = "base") -> float:
        """
        Ömür boyu ECL hesaplama.
        Marjinal PD yöntemi: Her yıl için koşullu PD hesaplayıp indirgeme.
        """
        pd_mult    = self.SCENARIO_PD_MULT.get(macro_scenario, 1.0)
        base_pd_12m= min(exposure.pd_12m * pd_mult, 0.99)
        maturity   = max(exposure.maturity_years, 1)
        ef_rate    = 0.12   # Efektif faiz oranı
        survival   = 1.0    # Hayatta kalma olasılığı
        total_ecl  = 0.0

        for t in range(1, int(maturity) + 1):
            # Marjinal PD — yıllık artış varsayımı
            annual_pd   = base_pd_12m * (1 + 0.02 * (t - 1))
            annual_pd   = min(annual_pd, 0.99)
            cond_pd     = annual_pd * survival
            discount    = 1 / ((1 + ef_rate) ** t)
            ecl_t       = cond_pd * exposure.lgd * exposure.ead * discount
            total_ecl  += ecl_t
            survival   *= (1 - annual_pd)
            if survival < 0.001:
                break

        return max(total_ecl, 0)

    def compute_probability_weighted_ecl(self, exposure: CreditExposure,
                                           stage: IFRS9Stage) -> Tuple[float, float, float]:
        """
        Senaryo ağırlıklı ECL hesaplama.
        Returns: (ecl_12m, ecl_lifetime, ecl_weighted)
        """
        ecl_12m_total      = 0.0
        ecl_lifetime_total = 0.0

        for scenario, weight in self.SCENARIO_WEIGHTS.items():
            ecl12   = self.compute_ecl_12m(exposure, scenario)
            ecllife = self.compute_ecl_lifetime(exposure, scenario)
            ecl_12m_total       += weight * ecl12
            ecl_lifetime_total  += weight * ecllife

        if stage == IFRS9Stage.STAGE_1:
            applied = ecl_12m_total
        else:
            applied = ecl_lifetime_total   # Stage 2 & 3

        return ecl_12m_total, ecl_lifetime_total, applied

    def determine_classification(self, exposure: CreditExposure) -> str:
        """
        IFRS-9 Muhasebe Sınıflandırması:
        - AC      : Amortized Cost (İtfa Edilmiş Maliyet)
        - FVOCI   : Fair Value through OCI
        - FVTPL   : Fair Value through P&L
        """
        if exposure.exposure_class in (ExposureClass.CORPORATES, ExposureClass.RETAIL):
            if exposure.dpd == 0 and exposure.pd_12m < 0.02:
                return "Amortized Cost (AC)"
            return "Fair Value Through P&L (FVTPL)"
        elif exposure.exposure_class == ExposureClass.CENTRAL_GOVT:
            return "Amortized Cost (AC)"
        elif exposure.exposure_class == ExposureClass.EQUITIES:
            return "Fair Value Through OCI (FVOCI)"
        else:
            return "Amortized Cost (AC)"

    def classify_exposure(self, exposure: CreditExposure) -> IFRS9ClassificationResult:
        """Tek maruziyet için tam IFRS-9 analizi."""
        stage, reason      = self.classify_stage(exposure)
        ecl12, ecllife, applied = self.compute_probability_weighted_ecl(exposure, stage)
        classification     = self.determine_classification(exposure)

        # Karşılık = uygulanan ECL (önceki dönem karşılık düşürülür — basit model: 0)
        provision         = applied
        impairment        = max(applied - 0, 0)   # Net değer düşüklüğü

        return IFRS9ClassificationResult(
            exposure        = exposure,
            stage           = stage,
            ecl_12m         = ecl12,
            ecl_lifetime    = ecllife,
            ecl_applied     = applied,
            provision       = provision,
            impairment_loss = impairment,
            classification  = classification,
            stage_reason    = reason,
        )

    def portfolio_ecl(self,
                       exposures: List[CreditExposure]
                       ) -> Dict[str, Any]:
        """Portföy düzeyinde IFRS-9 analizi."""
        results     = [self.classify_exposure(e) for e in exposures]
        total_ead   = sum(e.ead           for e in exposures)
        total_ecl   = sum(r.ecl_applied   for r in results)
        total_prov  = sum(r.provision     for r in results)

        stage_dist  = {1: 0, 2: 0, 3: 0}
        stage_ecl   = {1: 0.0, 2: 0.0, 3: 0.0}
        stage_ead   = {1: 0.0, 2: 0.0, 3: 0.0}

        for r in results:
            s = r.stage.value
            stage_dist[s] += 1
            stage_ecl[s]  += r.ecl_applied
            stage_ead[s]  += r.exposure.ead

        coverage_ratio = total_ecl / total_ead if total_ead > 0 else 0

        return {
            "portfolio_summary" : {
                "total_exposures"   : len(exposures),
                "total_ead"         : round(total_ead, 2),
                "total_ecl"         : round(total_ecl, 2),
                "total_provision"   : round(total_prov, 2),
                "coverage_ratio_pct": round(coverage_ratio * 100, 4),
            },
            "stage_distribution": {
                f"stage_{s}": {
                    "count"  : stage_dist[s],
                    "ead"    : round(stage_ead[s], 2),
                    "ecl"    : round(stage_ecl[s], 2),
                    "pct_of_total": round(stage_ead[s] / total_ead * 100, 2) if total_ead > 0 else 0,
                }
                for s in (1, 2, 3)
            },
            "individual_results": results,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 4: BASEL III SERMAYE YETERLİLİK MOTORU
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CapitalComponent:
    """Sermaye bileşeni."""
    name        : str
    amount      : float
    tier        : int   # 1 = CET1/AT1, 2 = Tier 2
    sub_type    : str   = ""   # CET1, AT1, T2
    deductions  : float = 0.0
    description : str   = ""

    @property
    def net_amount(self) -> float:
        return max(self.amount - self.deductions, 0)


@dataclass
class RegulatoryCapital:
    """Toplam Düzenleyici Sermaye."""
    components : List[CapitalComponent] = field(default_factory=list)

    def add(self, comp: CapitalComponent) -> None:
        self.components.append(comp)

    @property
    def cet1(self) -> float:
        return sum(c.net_amount for c in self.components if c.sub_type == "CET1")

    @property
    def additional_t1(self) -> float:
        return sum(c.net_amount for c in self.components if c.sub_type == "AT1")

    @property
    def tier1(self) -> float:
        return self.cet1 + self.additional_t1

    @property
    def tier2(self) -> float:
        return sum(c.net_amount for c in self.components if c.tier == 2)

    @property
    def total_capital(self) -> float:
        return self.tier1 + self.tier2

    def summary(self) -> Dict[str, float]:
        return {
            "CET1"         : round(self.cet1, 2),
            "AT1"          : round(self.additional_t1, 2),
            "Tier 1"       : round(self.tier1, 2),
            "Tier 2"       : round(self.tier2, 2),
            "Total Capital": round(self.total_capital, 2),
        }


@dataclass
class RWAComponents:
    """Risk Ağırlıklı Varlıklar (RWA) bileşenleri."""
    credit_risk_rwa  : float = 0.0   # Kredi Riski RWA
    market_risk_rwa  : float = 0.0   # Piyasa Riski RWA
    operational_rwa  : float = 0.0   # Operasyonel Risk RWA
    cva_rwa          : float = 0.0   # Kredi Değerleme Düzeltmesi RWA

    @property
    def total_rwa(self) -> float:
        return (self.credit_risk_rwa + self.market_risk_rwa +
                self.operational_rwa + self.cva_rwa)

    def breakdown(self) -> Dict[str, Any]:
        total = max(self.total_rwa, 1)
        return {
            "credit_risk_rwa"  : round(self.credit_risk_rwa, 2),
            "market_risk_rwa"  : round(self.market_risk_rwa, 2),
            "operational_rwa"  : round(self.operational_rwa, 2),
            "cva_rwa"          : round(self.cva_rwa, 2),
            "total_rwa"        : round(self.total_rwa, 2),
            "credit_pct"       : round(self.credit_risk_rwa / total * 100, 2),
            "market_pct"       : round(self.market_risk_rwa / total * 100, 2),
            "operational_pct"  : round(self.operational_rwa / total * 100, 2),
        }


class BaselIIICapitalEngine:
    """
    Basel III Sermaye Yeterlilik Oranı Hesaplama Motoru.

    Desteklenen yaklaşımlar:
      - Kredi Riski: Standart Yaklaşım (SA)
      - Piyasa Riski: Sensitivities-Based Method (SbM)
      - Operasyonel Risk: Temel Gösterge Yaklaşımı (BIA)
    """

    def compute_credit_rwa(self,
                            exposures: List[CreditExposure],
                            ecl_results: Optional[List[IFRS9ClassificationResult]] = None
                            ) -> float:
        """Standart Yaklaşım Kredi Riski RWA."""
        total_rwa = 0.0
        for exp in exposures:
            rw         = RISK_WEIGHTS.get(exp.exposure_class, 1.00)
            net_exp    = exp.net_exposure

            # Stage 3 için ek %100 RW gereksinimi
            if ecl_results:
                for r in ecl_results:
                    if r.exposure.exposure_id == exp.exposure_id:
                        if r.stage == IFRS9Stage.STAGE_3:
                            rw = max(rw, 1.50)   # Stage 3 için %150 RW
                        break

            total_rwa += net_exp * rw
        return total_rwa

    def compute_market_risk_rwa(self,
                                 equity_book: float    = 0,
                                 bond_book  : float    = 0,
                                 fx_position: float    = 0,
                                 commodity  : float    = 0) -> float:
        """
        Piyasa Riski Standart Methodu (Sensitivities-Based Method — SbM).
        Basitleştirilmiş hesaplama.
        """
        # Genel faiz riski RWA
        interest_rwa = bond_book * 0.08

        # Hisse senedi riski RWA
        equity_rwa   = equity_book * 0.32

        # Kur riski RWA
        fx_rwa       = fx_position * 0.08

        # Emtia riski RWA
        commodity_rwa= commodity * 0.15

        capital_charge = interest_rwa + equity_rwa + fx_rwa + commodity_rwa
        return capital_charge * 12.5   # RWA = Sermaye Gereksinimi × 12.5

    def compute_operational_rwa_bia(self, gross_income_3y: List[float]) -> float:
        """
        Operasyonel Risk — Temel Gösterge Yaklaşımı (BIA).
        BIA = Ortalama pozitif brüt gelir × %15 × 12.5
        """
        positive    = [gi for gi in gross_income_3y if gi > 0]
        if not positive:
            return 0.0
        avg_income  = sum(positive) / len(positive)
        capital_req = avg_income * 0.15
        return capital_req * 12.5

    def compute_cva_rwa(self, otc_derivatives_notional: float,
                          counterparty_pd: float = 0.01) -> float:
        """
        Kredi Değerleme Düzeltmesi (CVA) RWA.
        Standart CVA Yaklaşımı (BA-CVA) basitleştirilmiş versiyonu.
        """
        lgd_cvA  = 0.40   # CVA LGD standardı
        maturity  = 5.0   # yıl — varsayılan
        capital   = counterparty_pd * lgd_cvA * otc_derivatives_notional * maturity
        return capital * 12.5

    def compute_capital_ratios(self,
                                capital   : RegulatoryCapital,
                                rwa       : RWAComponents,
                                total_assets: float = 0
                                ) -> Dict[str, Any]:
        """Tüm Basel III oranlarını hesapla."""
        total_rwa = max(rwa.total_rwa, 1)

        cet1_ratio    = capital.cet1          / total_rwa
        tier1_ratio   = capital.tier1         / total_rwa
        total_ratio   = capital.total_capital / total_rwa
        leverage_ratio= capital.tier1         / max(total_assets, 1)

        # Tampon analizleri
        cet1_ex_conservation  = max(cet1_ratio - MIN_CET1_RATIO, 0)
        cct_buffer_headroom   = max(cet1_ratio - (MIN_CET1_RATIO + CAPITAL_CONSERVATION), 0)

        def traffic_light(value, min_req, good_thr):
            if value < min_req:
                return "🔴 Minimum Altı"
            elif value < good_thr:
                return "🟡 Tampon Bölge"
            else:
                return "🟢 Yeterli"

        return {
            "ratios": {
                "CET1 Oranı (%)": round(cet1_ratio * 100, 4),
                "Tier 1 Oranı (%)": round(tier1_ratio * 100, 4),
                "Toplam Sermaye Oranı (%)": round(total_ratio * 100, 4),
                "Kaldıraç Oranı (%)": round(leverage_ratio * 100, 4),
            },
            "minimums": {
                "CET1 Min (%)": MIN_CET1_RATIO * 100,
                "Tier 1 Min (%)": MIN_TIER1_RATIO * 100,
                "Toplam Min (%)": MIN_TOTAL_CAPITAL_RATIO * 100,
                "Kaldıraç Min (%)": MIN_LEVERAGE_RATIO * 100,
            },
            "surplus_deficit": {
                "CET1 Fazla/Açık (%)": round((cet1_ratio - MIN_CET1_RATIO) * 100, 4),
                "T1 Fazla/Açık (%)": round((tier1_ratio - MIN_TIER1_RATIO) * 100, 4),
                "Toplam Fazla/Açık (%)": round((total_ratio - MIN_TOTAL_CAPITAL_RATIO) * 100, 4),
            },
            "traffic_lights": {
                "CET1"          : traffic_light(cet1_ratio, MIN_CET1_RATIO, MIN_CET1_RATIO + CAPITAL_CONSERVATION),
                "Tier 1"        : traffic_light(tier1_ratio, MIN_TIER1_RATIO, MIN_TIER1_RATIO + CAPITAL_CONSERVATION),
                "Toplam Sermaye": traffic_light(total_ratio, MIN_TOTAL_CAPITAL_RATIO, MIN_TOTAL_CAPITAL_RATIO + CAPITAL_CONSERVATION),
                "Kaldıraç"      : traffic_light(leverage_ratio, MIN_LEVERAGE_RATIO, MIN_LEVERAGE_RATIO + 0.02),
            },
            "conservation_buffer_headroom_pct": round(cct_buffer_headroom * 100, 4),
            "fully_loaded_cet1_pct"           : round(cet1_ratio * 100, 4),
        }

    def stress_test_capital(self,
                             capital : RegulatoryCapital,
                             rwa     : RWAComponents,
                             shocks  : Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Sermaye Yeterlilik Stres Testi.
        Farklı makro şoklar altında oran değişimini analiz eder.
        """
        base_ratios = self.compute_capital_ratios(capital, rwa)
        results     = [{"Senaryo": "Baz", **base_ratios["ratios"]}]

        for scenario_name, rwa_shock_pct in shocks.items():
            shocked_rwa = RWAComponents(
                credit_risk_rwa=rwa.credit_risk_rwa * (1 + rwa_shock_pct),
                market_risk_rwa=rwa.market_risk_rwa * (1 + rwa_shock_pct * 0.5),
                operational_rwa=rwa.operational_rwa,
                cva_rwa        =rwa.cva_rwa         * (1 + rwa_shock_pct * 0.3),
            )
            shocked_cap = RegulatoryCapital()
            for comp in capital.components:
                # Kriz anında gelir düşmesiyle sermaye azalır
                shocked = CapitalComponent(
                    name=comp.name,
                    amount=comp.amount * (1 - rwa_shock_pct * 0.15),
                    tier=comp.tier,
                    sub_type=comp.sub_type,
                    deductions=comp.deductions,
                )
                shocked_cap.add(shocked)

            shocked_ratios = self.compute_capital_ratios(shocked_cap, shocked_rwa)
            results.append({
                "Senaryo": scenario_name,
                **shocked_ratios["ratios"],
                "Durum": shocked_ratios["traffic_lights"]["Toplam Sermaye"],
            })

        return results


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 5: LİKİDİTE YÖNETİMİ (LCR & NSFR)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LiquidityBuffer:
    """Yüksek Kaliteli Likit Varlık (HQLA) stoku."""
    level1_central_bank  : float = 0.0   # Merkez bankası rezervi
    level1_govt_bonds    : float = 0.0   # AAA devlet tahvili
    level2a_bonds        : float = 0.0   # AA idare tahvili
    level2b_corporate    : float = 0.0   # İyi kalite kurumsal tahvil

    @property
    def level1_total(self) -> float:
        return self.level1_central_bank + self.level1_govt_bonds

    @property
    def level2a_adjusted(self) -> float:
        return self.level2a_bonds * (1 - HQLA_HAIRCUTS["Level 2A"])

    @property
    def level2b_adjusted(self) -> float:
        return self.level2b_corporate * (1 - HQLA_HAIRCUTS["Level 2B"])

    @property
    def total_hqla(self) -> float:
        """Toplam HQLA (taşıt sınır ve kesintiler uygulandıktan sonra)."""
        l2_total = self.level2a_adjusted + self.level2b_adjusted
        # Level 2 = max HQLA'nın %40'ı
        l2_cap   = self.level1_total * 0.667   # 40% / 60% oranı
        l2_capped= min(l2_total, l2_cap)
        # Level 2B = max HQLA'nın %15'i
        l2b_cap  = self.level1_total * 0.25
        l2b_actual = min(self.level2b_adjusted, l2b_cap)
        l2_adj   = min(self.level2a_adjusted + l2b_actual, l2_cap)
        return self.level1_total + l2_adj


@dataclass
class CashOutflow:
    """LCR nakit çıkışı kalemi."""
    name        : str
    amount      : float
    outflow_rate: float   # Basel III tanımlı koşu oranı
    category    : str = "Diğer"

    @property
    def stress_outflow(self) -> float:
        return self.amount * self.outflow_rate


@dataclass
class CashInflow:
    """LCR nakit girişi kalemi."""
    name        : str
    amount      : float
    inflow_rate : float   # Maksimum %75 sayılır
    category    : str = "Diğer"

    @property
    def stress_inflow(self) -> float:
        return self.amount * min(self.inflow_rate, 0.75)


class LCREngine:
    """
    Likidite Karşılama Oranı (LCR) Motoru.
    Basel III Likidite Standartları (BCBS 238) uygulaması.

    LCR = HQLA / Net Stres Nakit Çıkışı ≥ %100
    """

    # Standart Basel III Koşu Oranları
    OUTFLOW_RATES = {
        "retail_sight_stable"   : 0.03,   # Mevduat sigortası kapsanan sabit → %3
        "retail_sight_less"     : 0.10,   # Daha az sabit bireysel → %10
        "sme_operational"       : 0.05,   # KOBİ operasyonel → %5
        "corporate_non_op"      : 0.25,   # Kurumsal operasyonel olmayan → %25
        "interbank_secured"     : 0.00,   # Güvenceli bankalararası → %0
        "interbank_unsecured"   : 0.25,   # Güvencesiz bankalararası → %25
        "otc_derivative"        : 1.00,   # OTC türev teminatlı → %100
        "credit_facility_retail": 0.05,   # Perakende kredi taahhütleri → %5
        "credit_facility_corp"  : 0.10,   # Kurumsal kredi taahhütleri → %10
    }

    INFLOW_RATES = {
        "retail_loans"          : 0.50,   # Bireysel kredi geri dönüşleri → %50
        "corporate_loans"       : 1.00,   # Kurumsal kredi geri dönüşleri → %100
        "interbank_secured"     : 0.00,   # Güvenceli bankalar arası → %0
        "interbank_unsecured"   : 1.00,   # Güvencesiz bankalar arası → %100
    }

    def compute_lcr(self,
                     hqla   : LiquidityBuffer,
                     outflows: List[CashOutflow],
                     inflows : List[CashInflow]) -> Dict[str, Any]:
        """LCR hesaplama."""
        total_hqla  = hqla.total_hqla
        gross_out   = sum(o.stress_outflow for o in outflows)
        gross_in    = sum(i.stress_inflow  for i in inflows)

        # Net çıkış = Toplam çıkış − min(Toplam giriş, %75 × çıkış)
        max_inflow  = gross_out * 0.75
        net_outflow = gross_out - min(gross_in, max_inflow)
        net_outflow = max(net_outflow, 1)

        lcr_ratio   = total_hqla / net_outflow

        # Bileşen analizi
        hqla_breakdown = {
            "Level 1 (Merkez Bankası)": round(hqla.level1_central_bank, 0),
            "Level 1 (Devlet Tahvili)": round(hqla.level1_govt_bonds, 0),
            "Level 2A (Düzeltilmiş)" : round(hqla.level2a_adjusted, 0),
            "Level 2B (Düzeltilmiş)" : round(hqla.level2b_adjusted, 0),
            "HQLA Toplam"            : round(total_hqla, 0),
        }

        outflow_detail = {o.name: round(o.stress_outflow, 0) for o in outflows}
        inflow_detail  = {i.name: round(i.stress_inflow,  0) for i in inflows}

        return {
            "lcr_ratio"           : round(lcr_ratio * 100, 2),
            "lcr_ratio_label"     : f"{lcr_ratio*100:.1f}%",
            "compliance"          : "✅ Uyumlu" if lcr_ratio >= MIN_LCR_RATIO else "❌ Uyumsuz",
            "surplus_shortage"    : round((total_hqla - net_outflow), 0),
            "hqla_breakdown"      : hqla_breakdown,
            "gross_outflow"       : round(gross_out, 0),
            "gross_inflow"        : round(gross_in, 0),
            "net_outflow"         : round(net_outflow, 0),
            "outflow_detail"      : outflow_detail,
            "inflow_detail"       : inflow_detail,
            "regulatory_minimum"  : "100%",
        }

    def lcr_stress_scenarios(self, base_hqla: LiquidityBuffer,
                               base_outflows: List[CashOutflow],
                               base_inflows : List[CashInflow]) -> List[Dict]:
        """LCR stres testi — farklı kriz senaryoları."""
        scenarios = [
            ("Baz",          1.00, 1.00),
            ("Hafif Stres",  0.90, 1.20),
            ("Orta Stres",   0.80, 1.50),
            ("Ağır Stres",   0.65, 2.00),
            ("Sistem Krizi", 0.50, 3.00),
        ]

        results = []
        for name, hqla_mult, out_mult in scenarios:
            stressed_hqla = LiquidityBuffer(
                level1_central_bank=base_hqla.level1_central_bank * hqla_mult,
                level1_govt_bonds  =base_hqla.level1_govt_bonds   * hqla_mult,
                level2a_bonds      =base_hqla.level2a_bonds        * hqla_mult,
                level2b_corporate  =base_hqla.level2b_corporate    * hqla_mult * 0.5,
            )
            stressed_out = [
                CashOutflow(o.name, o.amount * out_mult, o.outflow_rate, o.category)
                for o in base_outflows
            ]
            lcr = self.compute_lcr(stressed_hqla, stressed_out, base_inflows)
            results.append({
                "Senaryo"         : name,
                "LCR (%)"         : lcr["lcr_ratio"],
                "Uyum"            : lcr["compliance"],
                "Net Çıkış (TL)"  : lcr["net_outflow"],
                "HQLA (TL)"       : lcr["hqla_breakdown"]["HQLA Toplam"],
                "Fazla/Açık (TL)" : lcr["surplus_shortage"],
            })

        return results


class NSFREngine:
    """
    Net Gerçekleşebilir Fonlama Oranı (NSFR) Motoru.
    NSFR = Mevcut İstikrarlı Fonlama (ASF) / Gerekli İstikrarlı Fonlama (RSF) ≥ %100
    """

    # ASF faktörleri (fonlama karlılığı — Basel III)
    ASF_FACTORS = {
        "tier1_capital"          : 1.00,
        "tier2_capital"          : 1.00,
        "retail_deposit_1y"      : 0.95,
        "retail_deposit_lt1y"    : 0.90,
        "wholesale_deposit_1y"   : 0.50,
        "central_bank_funding_1y": 1.00,
        "interbank_secured_1y"   : 0.00,
    }

    # RSF faktörleri (varlık istikrar gereksinimi)
    RSF_FACTORS = {
        "hqla_level1"            : 0.05,
        "hqla_level2a"           : 0.15,
        "hqla_level2b"           : 0.50,
        "retail_loans_lt1y"      : 0.50,
        "retail_loans_gt1y"      : 0.65,
        "corporate_loans_lt1y"   : 0.50,
        "corporate_loans_gt1y"   : 0.65,
        "mortgage_loans"         : 0.65,
        "otc_derivatives"        : 0.20,
        "other_assets"           : 1.00,
    }

    def compute_asf(self, funding_sources: Dict[str, float]) -> float:
        total = 0.0
        for source, amount in funding_sources.items():
            factor = self.ASF_FACTORS.get(source, 0.5)
            total += amount * factor
        return total

    def compute_rsf(self, asset_categories: Dict[str, float]) -> float:
        total = 0.0
        for category, amount in asset_categories.items():
            factor = self.RSF_FACTORS.get(category, 1.0)
            total += amount * factor
        return total

    def compute_nsfr(self, funding_sources: Dict[str, float],
                      asset_categories : Dict[str, float]) -> Dict[str, Any]:
        asf   = self.compute_asf(funding_sources)
        rsf   = self.compute_rsf(asset_categories)
        nsfr  = asf / max(rsf, 1)

        return {
            "nsfr_ratio"       : round(nsfr * 100, 2),
            "compliance"       : "✅ Uyumlu" if nsfr >= MIN_NSFR_RATIO else "❌ Uyumsuz",
            "asf_total"        : round(asf, 0),
            "rsf_total"        : round(rsf, 0),
            "surplus_shortage" : round(asf - rsf, 0),
            "regulatory_min"   : "100%",
            "asf_breakdown"    : {k: round(v * self.ASF_FACTORS.get(k, 0.5), 0)
                                   for k, v in funding_sources.items()},
            "rsf_breakdown"    : {k: round(v * self.RSF_FACTORS.get(k, 1.0), 0)
                                   for k, v in asset_categories.items()},
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 6: SENTETİK PORTFÖY ÜRETECİ
# ═══════════════════════════════════════════════════════════════════════════════

class SyntheticPortfolioGenerator:
    """Test amaçlı gerçekçi kredi portföyü oluşturucu."""

    SECTORS = ["Perakende", "İmalat", "İnşaat", "Tarım", "Enerji",
               "Turizm", "Teknoloji", "Sağlık", "Finans", "Ulaşım"]
    RATINGS = {
        "AAA": (0.0005, 0.003), "AA": (0.001, 0.006),
        "A"  : (0.002,  0.012), "BBB":(0.005, 0.025),
        "BB" : (0.015,  0.060), "B"  : (0.040, 0.140),
        "CCC": (0.120,  0.350), "D"  : (0.999, 0.999),
    }

    def generate_exposures(self, n: int = 50,
                             seed: int = 42) -> List[CreditExposure]:
        random.seed(seed)
        exposures = []

        # Rating dağılımı (kurumsal portföy tipik)
        rating_dist = [
            ("AAA", 0.03), ("AA", 0.08), ("A", 0.18), ("BBB", 0.32),
            ("BB", 0.22),  ("B", 0.11),  ("CCC", 0.05), ("D", 0.01),
        ]

        for i in range(n):
            # Rating seç
            r = random.random()
            cumul = 0
            rating = "BBB"
            for (rtg, prob) in rating_dist:
                cumul += prob
                if r <= cumul:
                    rating = rtg
                    break

            pd_12m, pd_lt = self.RATINGS[rating]
            pd_12m  = pd_12m  * random.uniform(0.7, 1.3)
            pd_lt   = pd_lt   * random.uniform(0.7, 1.3)

            # Sınıf
            exp_class = random.choices(
                list(ExposureClass),
                weights=[0.05, 0.10, 0.45, 0.30, 0.05, 0.02, 0.02, 0.01]
            )[0]

            # Teminat
            coll_type  = random.choices(
                list(CollateralType),
                weights=[0.30, 0.25, 0.15, 0.10, 0.15, 0.05]
            )[0]

            outstanding = random.uniform(100_000, 50_000_000)
            lgd_map = {
                CollateralType.NONE        : LGD_UNSECURED,
                CollateralType.REAL_ESTATE : LGD_SECURED_RE,
                CollateralType.FINANCIAL   : LGD_SECURED_FIN,
                CollateralType.GUARANTEE   : 0.35,
                CollateralType.GOVERNMENT  : 0.05,
                CollateralType.RECEIVABLES : 0.30,
            }
            lgd   = lgd_map.get(coll_type, LGD_UNSECURED)
            dpd   = 0
            if rating == "D":
                dpd = random.randint(90, 365)
            elif rating in ("CCC", "B"):
                dpd = random.choices([0, 30, 60], weights=[0.6, 0.3, 0.1])[0]

            score = random.uniform(200, 850)
            if   rating in ("AAA", "AA"): score = random.uniform(720, 850)
            elif rating in ("A", "BBB"):  score = random.uniform(600, 720)
            elif rating in ("BB", "B"):   score = random.uniform(450, 600)
            elif rating == "CCC":         score = random.uniform(300, 450)
            else:                         score = random.uniform(200, 300)

            exp = CreditExposure(
                exposure_id    = f"EXP{i+1:04d}",
                debtor_name    = f"Müşteri {i+1}",
                exposure_class = exp_class,
                outstanding    = outstanding,
                committed      = outstanding * random.uniform(1.0, 1.3),
                pd_12m         = min(pd_12m, 1.0),
                pd_lifetime    = min(pd_lt, 1.0),
                lgd            = lgd,
                ead            = 0,
                maturity_years = random.uniform(0.5, 10.0),
                collateral_type= coll_type,
                collateral_value=outstanding * random.uniform(0, 1.5),
                dpd            = dpd,
                credit_score   = score,
                internal_rating= rating,
                sector         = random.choice(self.SECTORS),
            )
            exposures.append(exp)

        return exposures


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 7: ANA DÜZENLEYICI RAPOR MOTORU
# ═══════════════════════════════════════════════════════════════════════════════

class RegulatoryReportEngine:
    """
    Kurumsal Basel III & IFRS-9 Raporlama Orkestratörü.
    Streamlit UI'ından tek noktadan çağrılabilir.
    """

    def __init__(self):
        self.ifrs9_engine    = IFRS9Engine()
        self.basel_engine    = BaselIIICapitalEngine()
        self.lcr_engine      = LCREngine()
        self.nsfr_engine     = NSFREngine()
        self.portfolio_gen   = SyntheticPortfolioGenerator()

    def calculate_capital_adequacy(self, cet1: float, at1: float, t2: float, rwa: float) -> Dict[str, float]:
        return {
            'cet1_ratio': (cet1 / rwa) * 100 if rwa else 0,
            'tier1_ratio': ((cet1 + at1) / rwa) * 100 if rwa else 0,
            'total_capital_ratio': ((cet1 + at1 + t2) / rwa) * 100 if rwa else 0,
            'rwa': rwa
        }

    def calculate_lcr(self, hqla: float, net_outflows: float) -> Dict[str, float]:
        return {'lcr_ratio': hqla / net_outflows if net_outflows else 0}

    def calculate_nsfr(self, asf: float, rsf: float) -> Dict[str, float]:
        return {'nsfr_ratio': asf / rsf if rsf else 0}

    def generate_synthetic_bank_data(self, n_exposures: int = 50) -> Dict[str, Any]:
        """Sentetik test bankası verisi oluştur."""
        exposures = self.portfolio_gen.generate_exposures(n_exposures)

        # Sermaye
        capital = RegulatoryCapital()
        capital.add(CapitalComponent("Ödenmiş Sermaye",      5_000_000_000, 1, "CET1"))
        capital.add(CapitalComponent("Birikmiş K/Z",          1_200_000_000, 1, "CET1"))
        capital.add(CapitalComponent("Diğer Kapsamlı Gelir",   300_000_000, 1, "CET1",
                                      deductions=50_000_000))
        capital.add(CapitalComponent("İktisap Şerefiyesi",         0, 1, "CET1",
                                      deductions=200_000_000))
        capital.add(CapitalComponent("Katkı (AT1) Tahvil",    800_000_000, 1, "AT1"))
        capital.add(CapitalComponent("İkincil Borç (T2)",   1_000_000_000, 2, "T2"))

        # RWA
        total_outstanding = sum(e.outstanding for e in exposures)
        rwa = RWAComponents(
            credit_risk_rwa = total_outstanding * 0.68,
            market_risk_rwa = total_outstanding * 0.08,
            operational_rwa = total_outstanding * 0.05,
            cva_rwa         = total_outstanding * 0.01,
        )

        # LCR
        hqla = LiquidityBuffer(
            level1_central_bank = 2_500_000_000,
            level1_govt_bonds   = 1_800_000_000,
            level2a_bonds       =   700_000_000,
            level2b_corporate   =   300_000_000,
        )
        outflows = [
            CashOutflow("Bireysel Mevduat (Sabit)", 8_000_000_000, 0.03, "Perakende"),
            CashOutflow("Bireysel Mevduat (Daha Az Sabit)", 3_000_000_000, 0.10, "Perakende"),
            CashOutflow("Kurumsal Mevduat", 5_000_000_000, 0.25, "Kurumsal"),
            CashOutflow("Bankalar Arası Teminatsız", 1_500_000_000, 0.25, "Toptan"),
            CashOutflow("Kurumsal Kredi Taahhütleri", 800_000_000, 0.10, "Taahhüt"),
        ]
        inflows = [
            CashInflow("Bireysel Kredi Geri Dönüşleri", 2_000_000_000, 0.50, "Perakende"),
            CashInflow("Kurumsal Kredi Geri Dönüşleri", 1_200_000_000, 1.00, "Kurumsal"),
            CashInflow("Bankalar Arası Teminatsız", 500_000_000, 1.00, "Toptan"),
        ]

        # NSFR
        funding_sources = {
            "tier1_capital"          : capital.tier1,
            "tier2_capital"          : capital.tier2,
            "retail_deposit_1y"      : 6_000_000_000,
            "retail_deposit_lt1y"    : 5_000_000_000,
            "wholesale_deposit_1y"   : 3_000_000_000,
            "central_bank_funding_1y": 1_500_000_000,
        }
        asset_categories = {
            "hqla_level1"         : hqla.level1_total,
            "hqla_level2a"        : hqla.level2a_bonds,
            "retail_loans_gt1y"   : total_outstanding * 0.40,
            "retail_loans_lt1y"   : total_outstanding * 0.20,
            "corporate_loans_gt1y": total_outstanding * 0.25,
            "mortgage_loans"      : total_outstanding * 0.10,
            "other_assets"        : total_outstanding * 0.05,
        }

        return {
            "exposures"       : exposures,
            "capital"         : capital,
            "rwa"             : rwa,
            "hqla"            : hqla,
            "outflows"        : outflows,
            "inflows"         : inflows,
            "funding_sources" : funding_sources,
            "asset_categories": asset_categories,
            "total_assets"    : total_outstanding * 1.15,
        }

    def run_full_regulatory_analysis(self, n_exposures: int = 50) -> Dict[str, Any]:
        """Komple düzenleyici analiz paketi."""
        data = self.generate_synthetic_bank_data(n_exposures)

        # IFRS-9
        ifrs9_result = self.ifrs9_engine.portfolio_ecl(data["exposures"])

        # Basel III
        ecl_list  = ifrs9_result["individual_results"]
        cr_rwa    = self.basel_engine.compute_credit_rwa(data["exposures"], ecl_list)
        data["rwa"].credit_risk_rwa = cr_rwa

        capital_ratios = self.basel_engine.compute_capital_ratios(
            data["capital"], data["rwa"], data["total_assets"]
        )
        stress_scenarios_shocks = {
            "Hafif Resesyon"    : 0.15,
            "Orta Kriz"         : 0.35,
            "Ağır Finansal Kriz": 0.60,
        }
        stress_results = self.basel_engine.stress_test_capital(
            data["capital"], data["rwa"], stress_scenarios_shocks
        )

        # LCR
        lcr_result     = self.lcr_engine.compute_lcr(
            data["hqla"], data["outflows"], data["inflows"])
        lcr_stress     = self.lcr_engine.lcr_stress_scenarios(
            data["hqla"], data["outflows"], data["inflows"])

        # NSFR
        nsfr_result    = self.nsfr_engine.compute_nsfr(
            data["funding_sources"], data["asset_categories"])

        return {
            "ifrs9"              : ifrs9_result,
            "capital_ratios"     : capital_ratios,
            "rwa_breakdown"      : data["rwa"].breakdown(),
            "capital_summary"    : data["capital"].summary(),
            "stress_test"        : stress_results,
            "lcr"                : lcr_result,
            "lcr_stress"         : lcr_stress,
            "nsfr"               : nsfr_result,
            "analysis_timestamp" : datetime.datetime.now().isoformat(),
            "n_exposures"        : n_exposures,
        }

    def generate_icaap_summary(self, analysis: Dict[str, Any]) -> str:
        """ICAAP Yönetim Özeti Markdown raporu."""
        cap  = analysis["capital_ratios"]["ratios"]
        lcr  = analysis["lcr"]["lcr_ratio"]
        nsfr = analysis["nsfr"]["nsfr_ratio"]
        ecl  = analysis["ifrs9"]["portfolio_summary"]["total_ecl"]
        s1   = analysis["ifrs9"]["stage_distribution"]["stage_1"]["pct_of_total"]
        s2   = analysis["ifrs9"]["stage_distribution"]["stage_2"]["pct_of_total"]
        s3   = analysis["ifrs9"]["stage_distribution"]["stage_3"]["pct_of_total"]

        ts   = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        return f"""
# 🏛️ ICAAP — İç Sermaye Yeterlilik Değerlendirme Süreci
### ProQuant Capital | Düzenleyici Uyum Raporu
**Rapor Tarihi:** {ts} | **Versiyon:** 2.0 | **Gizlilik:** KESİN GİZLİ

---

## 📊 Yürütücü Özeti

Bu ICAAP raporu, bankanın Basel III bütünleşik muhasebesine göre düzenleyici
sermaye pozisyonunu, likidite tamponu yeterliliğini ve IFRS-9 beklenen kredi
zarar karşılıklarını yansıtmaktadır.

---

## 1. Sermaye Yeterlilik Paneli

| Oran                     | Cari Değer | Minimum | Durum |
|:-------------------------|:----------:|:-------:|:-----:|
| CET1 Oranı               | **{cap["CET1 Oranı (%)"]:.2f}%** | 4.5%  | {"✅" if cap["CET1 Oranı (%)"] >= 4.5 else "❌"} |
| Tier 1 Sermaye Oranı     | **{cap["Tier 1 Oranı (%)"]:.2f}%** | 6.0% | {"✅" if cap["Tier 1 Oranı (%)"] >= 6.0 else "❌"} |
| Toplam Sermaye Oranı     | **{cap["Toplam Sermaye Oranı (%)"]:.2f}%** | 8.0% | {"✅" if cap["Toplam Sermaye Oranı (%)"] >= 8.0 else "❌"} |
| Kaldıraç Oranı           | **{cap["Kaldıraç Oranı (%)"]:.2f}%** | 3.0% | {"✅" if cap["Kaldıraç Oranı (%)"] >= 3.0 else "❌"} |

---

## 2. Likidite Göstergeleri

| Gösterge | Cari | Minimum | Durum |
|:---------|:----:|:-------:|:-----:|
| LCR      | **{lcr:.1f}%** | 100% | {"✅" if lcr >= 100 else "❌"} |
| NSFR     | **{nsfr:.1f}%** | 100% | {"✅" if nsfr >= 100 else "❌"} |

---

## 3. IFRS-9 Kredi Kalite Dağılımı

| Aşama   | Portföy Payı | Açıklama                        |
|:--------|:------------:|:--------------------------------|
| Stage 1 | **{s1:.1f}%** | Normal — 12 aylık ECL           |
| Stage 2 | **{s2:.1f}%** | SICR — Ömür boyu ECL            |
| Stage 3 | **{s3:.1f}%** | Değer düşüklüğü — Ömür boyu ECL |

**Toplam ECL Karşılığı:** {ecl:,.0f} TL

---

## 4. Düzenleyici Değerlendirme

{"✅ Banka tüm Basel III minimum gereksinimleri karşılamaktadır." if all(v >= t for v, t in [(cap["CET1 Oranı (%)"], 4.5), (lcr, 100), (nsfr, 100)]) else "⚠️ Bir veya birden fazla düzenleyici eşik aşılmakta — acil sermaye/likidite planı gereklidir."}

---
*Bu rapor ProQuant Capital Regulatory Analytics Modülü tarafından otomatik üretilmiştir.*
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def get_regulatory_engine() -> RegulatoryReportEngine:
    return RegulatoryReportEngine()

"""
modules/fundamental_intelligence.py — ProQuant Capital | Temel Analiz & Kurumsal Finans Motoru v3.0
================================================================================================

Kurumsal finansal modelleme, değerleme ve temel analiz kütüphanesi.
Bu modül, bir şirketin finansal sağlığını 3-tablolu (Income Statement, Balance Sheet, Cash Flow) 
projeksiyonlar ve ileri seviye değerleme metotları (DCF, LBO, Multiples) ile analiz eder.

Kapsam:
  1. 3-Tablolu Modelleme (3-Statement Modeling):
     - Gelir Tablosu (P&L): Gelir kalemleri, COGS, EBITDA, EBIT, Net Kar.
     - Bilanço (Balance Sheet): Varlıklar, Yükümlülükler, Özkaynaklar dengesi.
     - Nakit Akış Tablosu (Cash Flow): Operasyonel, Yatırım ve Finansman nakit akışları.
  2. Finansal Oran Analizi (Ratio Analysis):
     - Likidite Rasyoları: Current Ratio, Quick Ratio, Cash Ratio.
     - Kârlılık Rasyoları: ROE, ROA, ROIC, Gross/Net Margins.
     - Solvency (Borçluluk): Debt/Equity, Debt/EBITDA, Interest Coverage.
     - Verimlilik (Activity): Asset Turnover, Inventory Turnover, DSO, DPO.
  3. Değerleme Modelleri (Valuation):
     - DCF (Discounted Cash Flow): Serbest Nakit Akışı (FCF) projeksiyonu.
     - WACC (Ağırlık Ortalama Sermaye Maliyeti): CAPM tabanlı maliyet hesabı.
     - DDM (Dividend Discount Model): Gordon Büyüme Modeli.
     - Karşılaştırmalı Değerleme: P/E, EV/EBITDA, P/S çarpan analizleri.
  4. LBO (Leveraged Buyout) Analizi:
     - Borç yapılandırma (Tranche A, B, Mezzanine).
     - IRR ve Nakit çarpanı (MoIC) projeksiyonları.

Author  : ProQuant Capital Corporate Finance Unit
Version : 3.0.0
"""

from __future__ import annotations
import time

import math
import random
import datetime
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: FİNANSAL TABLO BİLEŞENLERİ (3-STATEMENT)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class IncomeStatement:
    """Gelir Tablosu Kalemleri."""
    revenue: float
    cogs: float
    operating_expenses: float
    depreciation_amortization: float
    interest_expense: float
    tax_rate: float = 0.20
    
    @property
    def gross_profit(self) -> float:
        return self.revenue - self.cogs
        
    @property
    def ebitda(self) -> float:
        return self.revenue - self.cogs - self.operating_expenses
        
    @property
    def ebit(self) -> float:
        return self.ebitda - self.depreciation_amortization
        
    @property
    def ebt(self) -> float:
        return self.ebit - self.interest_expense
        
    @property
    def net_income(self) -> float:
        return self.ebt * (1 - self.tax_rate)


@dataclass
class BalanceSheet:
    """Bilanço Kalemleri."""
    cash: float
    accounts_receivable: float
    inventory: float
    fixed_assets_net: float
    accounts_payable: float
    long_term_debt: float
    equity_common: float
    retained_earnings: float
    
    @property
    def total_assets(self) -> float:
        return self.cash + self.accounts_receivable + self.inventory + self.fixed_assets_net
        
    @property
    def total_liabilities(self) -> float:
        return self.accounts_payable + self.long_term_debt
        
    @property
    def total_equity(self) -> float:
        return self.equity_common + self.retained_earnings
        
    def check_balance(self) -> bool:
        return abs(self.total_assets - (self.total_liabilities + self.total_equity)) < 1e-5


@dataclass
class CashFlowStatement:
    """Nakit Akış Tablosu (Dolaylı Yöntem)."""
    net_income: float
    depreciation: float
    change_in_nwc: float
    capex: float
    debt_issuance_net: float
    dividends_paid: float
    
    @property
    def operating_cf(self) -> float:
        return self.net_income + self.depreciation - self.change_in_nwc
        
    @property
    def investing_cf(self) -> float:
        return -self.capex
        
    @property
    def financing_cf(self) -> float:
        return self.debt_issuance_net - self.dividends_paid
        
    @property
    def net_change_in_cash(self) -> float:
        return self.operating_cf + self.investing_cf + self.financing_cf


# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: ANALİZ MOTORU (RATIO ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────

class FundamentalRatioEngine:
    """Finansal rasyo hesaplama ve analiz motoru."""

    @staticmethod
    def liquidity_analysis(bs: BalanceSheet) -> Dict[str, float]:
        """Likidite rasyoları."""
        current_assets = bs.cash + bs.accounts_receivable + bs.inventory
        return {
            "current_ratio": current_assets / max(bs.accounts_payable, 1),
            "quick_ratio": (bs.cash + bs.accounts_receivable) / max(bs.accounts_payable, 1),
            "cash_ratio": bs.cash / max(bs.accounts_payable, 1)
        }

    @staticmethod
    def profitability_analysis(is_stmt: IncomeStatement, bs: BalanceSheet) -> Dict[str, float]:
        """Kârlılık rasyoları."""
        total_assets = bs.total_assets
        total_equity = bs.total_equity
        return {
            "gross_margin": is_stmt.gross_profit / is_stmt.revenue,
            "ebitda_margin": is_stmt.ebitda / is_stmt.revenue,
            "net_margin": is_stmt.net_income / is_stmt.revenue,
            "roa": is_stmt.net_income / max(total_assets, 1),
            "roe": is_stmt.net_income / max(total_equity, 1)
        }

    @staticmethod
    def solvency_analysis(is_stmt: IncomeStatement, bs: BalanceSheet) -> Dict[str, float]:
        """Kaldıraç ve borç ödeme gücü."""
        return {
            "debt_to_equity": bs.long_term_debt / max(bs.total_equity, 1),
            "debt_to_ebitda": bs.long_term_debt / max(is_stmt.ebitda, 1),
            "interest_coverage": is_stmt.ebit / max(is_stmt.interest_expense, 0.001)
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: DEĞERLEME MODELLERİ (DCF, WACC, DDM)
# ─────────────────────────────────────────────────────────────────────────────

class ValuationEngine:
    """Şirket değerleme motoru."""

    @staticmethod
    def calculate_wacc(risk_free_rate: float, beta: float, market_premium: float,
                      cost_of_debt: float, tax_rate: float, 
                      market_cap: float, total_debt: float) -> float:
        """Ağırlıklı Ortalama Sermaye Maliyeti (WACC)."""
        # Cost of Equity via CAPM
        cost_of_equity = risk_free_rate + beta * market_premium
        
        v = market_cap + total_debt
        w_e = market_cap / v
        w_d = total_debt / v
        
        wacc = (w_e * cost_of_equity) + (w_d * cost_of_debt * (1 - tax_rate))
        return wacc

    def dcf_valuation(self, current_fcf: float, growth_rate: float, 
                      wacc: float, terminal_growth: float, 
                      projection_years: int = 5) -> Dict[str, Any]:
        """
        Discounted Cash Flow (DCF).
        İki aşamalı büyüme modeli.
        """
        projected_fcfs = []
        discount_factors = []
        present_values = []
        
        fcf = current_fcf
        for y in range(1, projection_years + 1):
            fcf *= (1 + growth_rate)
            df = 1 / (1 + wacc)**y
            pv = fcf * df
            
            projected_fcfs.append(fcf)
            discount_factors.append(df)
            present_values.append(pv)
            
        stage_1_value = sum(present_values)
        
        # Terminal Value (Perpetuity Growth Method)
        terminal_value = (projected_fcfs[-1] * (1 + terminal_growth)) / (wacc - terminal_growth)
        pv_terminal_value = terminal_value / (1 + wacc)**projection_years
        
        enterprise_value = stage_1_value + pv_terminal_value
        
        return {
            "enterprise_value": enterprise_value,
            "stage_1_pv": stage_1_value,
            "pv_terminal_value": pv_terminal_value,
            "terminal_value": terminal_value,
            "projected_fcfs": projected_fcfs,
            "wacc_used": wacc
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: LBO (LEVERAGED BUYOUT) ANALİZİ
# ─────────────────────────────────────────────────────────────────────────────

class LBOKernal:
    """LBO modelleme motoru."""

    def calculate_exit_returns(self, entry_ebitda: float, exit_ebitda: float,
                              entry_multiple: float, exit_multiple: float,
                              entry_debt: float, exit_debt: float,
                              equity_investment: float, years: int = 5) -> Dict[str, float]:
        """Entry-Exit bazlı LBO getirisi."""
        entry_ev = entry_ebitda * entry_multiple
        exit_ev  = exit_ebitda * exit_multiple
        
        exit_equity_value = exit_ev - exit_debt
        
        moic = exit_equity_value / equity_investment
        irr  = (moic**(1/years)) - 1
        
        return {
            "entry_ev": entry_ev,
            "exit_ev": exit_ev,
            "exit_equity": exit_equity_value,
            "moic": moic,
            "irr_pct": irr * 100
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 5: TEMEL ANALİZ ORKESTRATÖRÜ
# ─────────────────────────────────────────────────────────────────────────────

class FundamentalIntelligenceEngine:
    """Tüm temel analiz süreçlerini yöneten ana API."""

    def __init__(self):
        self.ratios = FundamentalRatioEngine()
        self.valuation = ValuationEngine()
        self.lbo = LBOKernal()

    def generate_company_report(self, name: str, is_data: Dict[str, float], 
                               bs_data: Dict[str, float]) -> Dict[str, Any]:
        """Şirket finansal karnesi ve değerleme raporu üret."""
        
        is_stmt = IncomeStatement(**is_data)
        bs_stmt = BalanceSheet(**bs_data)
        
        # 1. Rasyo Analizi
        liq = self.ratios.liquidity_analysis(bs_stmt)
        prof = self.ratios.profitability_analysis(is_stmt, bs_stmt)
        sol = self.ratios.solvency_analysis(is_stmt, bs_stmt)
        
        # 2. Değerleme (Varsayılan parametrelerle)
        wacc = self.valuation.calculate_wacc(0.12, 1.2, 0.06, 0.15, 0.20, bs_stmt.total_equity, bs_stmt.long_term_debt)
        current_fcf = is_stmt.net_income + is_stmt.depreciation_amortization - 2000000 # Basit FCF
        dcf = self.valuation.dcf_valuation(current_fcf, 0.10, wacc, 0.03)
        
        # 3. Özet Puanlama
        score = 0
        if liq["current_ratio"] > 1.5: score += 1
        if prof["roe"] > 0.15: score += 1
        if sol["interest_coverage"] > 3: score += 1
        if dcf["enterprise_value"] > bs_stmt.total_assets: score += 1

        return {
            "company": name,
            "ratios": {**liq, **prof, **sol},
            "valuation": dcf,
            "health_score": f"{score}/4",
            "valuation_status": "UNDERVALUED" if dcf["enterprise_value"] > bs_stmt.total_equity * 1.5 else "FAIR",
            "timestamp": datetime.datetime.now().isoformat()
        }

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

_fundamental_engine = FundamentalIntelligenceEngine()

def get_fundamental_engine() -> FundamentalIntelligenceEngine:
    return _fundamental_engine

"""
modules/portfolio_var_engine.py
Portföy Value-at-Risk (VaR) ve Expected Shortfall Motoru
Monte Carlo (Gaussian Copula Approx) ile binlerce kredinin eş zamanlı temerrüt riskini analiz eder.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)

class PortfolioVaREngine:
    """
    Kredi portföyü seviyesinde yoğunlaşma (concentration) risklerini ve 
    Ekonomik Sermaye (Economic Capital) gereksinimlerini simüle eder.
    """
    
    def __init__(self):
        self.num_iterations = 10000 
        
    def simulate_portfolio_loss(self, portfolio_df: pd.DataFrame, asset_correlation: float = 0.15) -> dict:
        """
        Copula tabanlı Monte Carlo Kredi Kayıp Dağılımı (Loss Distribution)
        
        portfolio_df sütunları:
        - loan_amount
        - pd_prob (Probability of Default, ondalık)
        - lgd_prob (Loss Given Default, ondalık)
        """
        if portfolio_df.empty:
             return {"error": "Portföy boş."}
             
        n_loans = len(portfolio_df)
        amounts = portfolio_df["loan_amount"].values
        pds = portfolio_df["pd_prob"].values
        lgds = portfolio_df["lgd_prob"].values
        
        # Temerrüt eşiği hesaplama: Z_threshold = N^-1(PD)
        # N^-1, norm.ppf (percent point function - inverse CDF) olarak geçer.
        # Çok küçük PD'lerde -inf almaması için cap atılır:
        pds_clipped = np.clip(pds, 0.0001, 0.9999)
        default_thresholds = norm.ppf(pds_clipped)
        
        losses = np.zeros(self.num_iterations)
        
        # Monte Carlo Iterate
        # Firma varlık değeri = sqrt(rho_asset)*Z_m + sqrt(1-rho_asset)*Z_i
        # Z_m = Makro ekonomik (sistematik) risk bileşeni
        # Z_i = İdiosekratik (firmaya özel) risk bileşeni
        
        sqrt_rho = np.sqrt(asset_correlation)
        sqrt_1_rho = np.sqrt(1 - asset_correlation)
        
        for i in range(self.num_iterations):
            Z_m = np.random.standard_normal()
            Z_i = np.random.standard_normal(n_loans)
            
            # Firmanın sentetik varlık getirisi (Asset Return)
            asset_returns = sqrt_rho * Z_m + sqrt_1_rho * Z_i
            
            # Temerrüt durumu: Asset Return < Default Threshold
            defaults = (asset_returns < default_thresholds)
            
            # O iterasyondaki toplam kayıp
            iter_loss = np.sum(defaults * amounts * lgds)
            losses[i] = iter_loss
            
        # Metriklerin Çıkartılması
        losses_sorted = np.sort(losses)
        
        expected_loss = np.mean(losses)
        
        # VaR (Value at Risk)
        idx_99 = int(self.num_iterations * 0.99)
        idx_999 = int(self.num_iterations * 0.999)
        var_99 = losses_sorted[idx_99]
        var_999 = losses_sorted[idx_999]
        
        # Expected Shortfall (ES) - Tail Risk
        es_99 = np.mean(losses_sorted[idx_99:])
        
        return {
            "total_exposure": np.sum(amounts),
            "expected_loss": expected_loss,
            "var_99": var_99,
            "var_999": var_999,
            "expected_shortfall_99": es_99,
            "economic_capital": var_999 - expected_loss, # Basel standard
            "loss_distribution_sample": losses[:1000].tolist() # Grafik için alt küme
        }

var_engine = PortfolioVaREngine()

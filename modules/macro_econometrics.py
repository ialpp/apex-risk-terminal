"""
modules/macro_econometrics.py
Kurumsal Ekonometri Motoru - Zaman Serisi (VAR / ARIMA) Projeksiyonları
Geçmiş makroekonomik verileri sentetik olarak üretir ve geleceğe yönelik kriz/baz senaryolarını tahmin eder.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MacroEconometricsEngine:
    """
    Ekonomik değişkeler arasındaki gecikmeli (lagged) etkileşimi VECM / VAR
    formatında simüle eden kurumsal sınıf makro-ekonometri modelleri.
    """
    
    def __init__(self):
        self.base_date = datetime.now().replace(day=1)
        self.var_history_cache = None

    def generate_historical_data(self, months_back: int = 120) -> pd.DataFrame:
        """Son 10 yılın (120 ay) temel ekonomik parametrelerini üretir."""
        if self.var_history_cache is not None and len(self.var_history_cache) >= months_back:
            return self.var_history_cache.tail(months_back).copy()

        np.random.seed(42)  # Tutarlı tarihçe için
        dates = [self.base_date - relativedelta(months=i) for i in reversed(range(months_back))]
        
        # O-U Süreçleri ile Mean Reverting Seri Üretimi
        dt = 1/12
        inflation = [0.08] # Yıllık baz
        policy_rate = [0.09]
        fx_usd_try = [2.50]
        cds_spread = [150]
        
        for i in range(1, months_back):
            # Enflasyon dalgalanması (son yıllarda yukarı şok)
            if i > 80: # Son 3-4 senede şok
                inf_shock = np.random.normal(0.005, 0.01)
                inf_theta = 0.45 
            else:
                inf_shock = np.random.normal(0, 0.002)
                inf_theta = 0.10
                
            inf_new = inflation[-1] + 0.1 * (inf_theta - inflation[-1]) * dt + inf_shock
            inflation.append(max(0.01, inf_new))
            
            # Politika faizi genelde enflasyonu gecikmeli takip eder (Taylor Rule approx)
            target_rate = max(0.05, inflation[-1] + 0.02)
            rate_new = policy_rate[-1] + 0.2 * (target_rate - policy_rate[-1]) * dt + np.random.normal(0, 0.005)
            policy_rate.append(max(0.01, rate_new))
            
            # FX Rate: ÜFE-TÜFE farkı ve faiz farkı PPP (Purchasing Power Parity) ile sürüklenir
            fx_drift = (inflation[-1] - 0.02) * dt
            fx_new = fx_usd_try[-1] * (1 + fx_drift + np.random.normal(0, 0.015))
            fx_usd_try.append(fx_new)
            
            # CDS Spread: Makro stabilite bozuldukça quadratik fırlar
            cds_target = 100 + (inflation[-1] * 1000) + max(0, (fx_new - fx_usd_try[-2])*1000 if i>1 else 0)
            cds_new = cds_spread[-1] + 0.3 * (cds_target - cds_spread[-1]) * dt + np.random.normal(0, 20)
            cds_spread.append(max(50, cds_new))

        df = pd.DataFrame({
            "Date": dates,
            "Inflation_Pct": np.array(inflation) * 100,
            "Policy_Rate_Pct": np.array(policy_rate) * 100,
            "USD_TRY": fx_usd_try,
            "CDS_Spread": cds_spread
        })
        self.var_history_cache = df
        return df

    def forecast_var_scenario(self, months_ahead: int = 24, scenario: str = "Base") -> pd.DataFrame:
        """
        Geçmişten alınan momentum ile Geleceğe Yönelik VAR Projeksiyonu.
        Senaryo tipleri: 'Base', 'Adverse' (Kötümser/Kriz), 'Optimistic' (İyimser)
        """
        history = self.generate_historical_data(12)
        last_inf = history["Inflation_Pct"].iloc[-1]
        last_rate = history["Policy_Rate_Pct"].iloc[-1]
        last_fx = history["USD_TRY"].iloc[-1]
        last_cds = history["CDS_Spread"].iloc[-1]
        
        dates = [self.base_date + relativedelta(months=i) for i in range(1, months_ahead + 1)]
        
        # Senaryo Şokları
        if scenario == "Adverse":
            inf_shock_mean, rate_target_add, fx_vol, cds_jump = 1.0, 5.0, 0.05, 300
        elif scenario == "Optimistic":
            inf_shock_mean, rate_target_add, fx_vol, cds_jump = -0.5, -2.0, 0.01, -100
        else: # Base
            inf_shock_mean, rate_target_add, fx_vol, cds_jump = 0.0, 0.0, 0.02, 0.0
            
        proj_inf, proj_rate, proj_fx, proj_cds = [last_inf], [last_rate], [last_fx], [last_cds + cds_jump]
        
        for _ in range(months_ahead):
            # Enflasyon momentumu
            new_inf = proj_inf[-1] * 0.95 + inf_shock_mean + np.random.normal(0, 0.5)
            proj_inf.append(max(2.0, new_inf))
            
            # Faiz
            new_rate = proj_rate[-1] + 0.1 * (proj_inf[-1] + rate_target_add - proj_rate[-1])
            proj_rate.append(max(1.0, new_rate))
            
            # FX
            fx_drift = (proj_inf[-1] / 1200) # Aylık enflasyon yansıması
            new_fx = proj_fx[-1] * (1 + fx_drift + np.random.normal(0, fx_vol))
            proj_fx.append(max(last_fx*0.8, new_fx))
            
            # CDS
            new_cds = proj_cds[-1] * 0.98 + (proj_inf[-1]*2) + np.random.normal(0, 10)
            proj_cds.append(max(50, new_cds))
            
        proj_df = pd.DataFrame({
            "Date": dates,
            "Inflation_Pct": proj_inf[1:],
            "Policy_Rate_Pct": proj_rate[1:],
            "USD_TRY": proj_fx[1:],
            "CDS_Spread": proj_cds[1:]
        })
        return proj_df

macro_engine = MacroEconometricsEngine()

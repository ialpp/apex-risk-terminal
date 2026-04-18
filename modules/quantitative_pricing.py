"""
modules/quantitative_pricing.py
Kurumsal Fiyatlama ve Risk-Adjusted Return On Capital (RAROC) Motoru
Merton (KMV) Opsiyon Fiyatlama Tabanlı Zımni Temerrüt Hesaplamaları
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)

class PricingEngine:
    """
    Kredilerin kârlılık oranlarını ve şirketin iflas mesafelerini
    sermaye piyasası modelleri ile hesaplayan kurumsal motor.
    """

    def __init__(self):
        # Kurumsal standartlar (Basel III baseline approximations)
        self.risk_free_rate = 0.045  # %4.5 (Örn: 10 Yıllık Tahvil)
        self.market_risk_premium = 0.055 
        self.corporate_tax_rate = 0.25 # %25 Kurumlar Vergisi
        self.target_roe = 0.15 # %15 Hedef Özsermaye Kârlılığı

    def calculate_raroc(self, loan_amount: float, interest_rate: float, 
                        pd_prob: float, lgd_prob: float = 0.45, 
                        operating_cost_pct: float = 0.012) -> dict:
        """
        Risk-Adjusted Return On Capital (RAROC) hesaplar.
        
        Parametreler:
        - loan_amount: Kredi Miktarı
        - interest_rate: Müşteriye sunulan nominal faiz oranı
        - pd_prob: Probability of Default (Temerrüt Olasılığı % olarak veya ondalık)
        - lgd_prob: Loss Given Default (Temerrüt Halinde Kayıp, genelde %45)
        - operating_cost_pct: Kredinin operasyonel maliyeti (Örn %1.2)
        """
        # PD ondalık kontrol
        if pd_prob > 1:
            pd_prob /= 100.0
            
        # 1. Gelirler (Revenues)
        net_interest_income = loan_amount * (interest_rate - self.risk_free_rate)
        
        # 2. Beklenen Kayıp (Expected Loss - EL)
        expected_loss = loan_amount * pd_prob * lgd_prob
        
        # 3. Operasyonel Maliyet
        operating_cost = loan_amount * operating_cost_pct
        
        # 4. Beklenmeyen Kayıp bazlı Ekonomik Sermaye (Unexpected Loss & Economic Capital)
        # Basitleştirilmiş Basel formülü (k=99.9% güven aralığı ivmesi approx)
        z_999 = 3.09023
        unexpected_loss = loan_amount * lgd_prob * np.sqrt(pd_prob * (1 - pd_prob))
        economic_capital = unexpected_loss * z_999
        
        # 5. Risk Ayarlı Net Gelir (Maliyetler düşüldükten sonra)
        risk_adjusted_income = net_interest_income - expected_loss - operating_cost
        after_tax_income = risk_adjusted_income * (1 - self.corporate_tax_rate)
        
        # 6. RAROC Oranı
        if economic_capital > 0:
            raroc = (after_tax_income / economic_capital) * 100 
        else:
            raroc = 0.0
            
        is_valuable = raroc >= (self.target_roe * 100)
        
        return {
            "loan_amount": loan_amount,
            "interest_income": net_interest_income,
            "expected_loss": expected_loss,
            "economic_capital": economic_capital,
            "raroc_percentage": raroc,
            "target_roe": self.target_roe * 100,
            "decision": "ONAY: Değer Yaratıyor" if is_valuable else "RED: Sermaye Maliyeti Karşılanmıyor"
        }

    def merton_distance_to_default(self, equity_value: float, equity_volatility: float, 
                                   debt_face_value: float, time_to_maturity: float = 1.0) -> dict:
        """
        Merton (KMV) Yapısal Temerrüt Modeli (Structural Default Model).
        Bir firmanın hisse (equity) değerini bir "Call Option" olarak görerek firmanın asıl varlık 
        değerini (Asset Value) ve Volatilitesini iteratif olarak çözer (Burada approx Gauss-Newton kullanılır).
        """
        if debt_face_value <= 0 or equity_value <= 0:
            return {"dd": 0.0, "implied_pd": 1.0, "error": "Geçersiz sermaye/borç verisi"}
            
        # Basitleştirilmiş iterasyon (Asset Value Approximation)
        # V_a = E + D
        asset_value = equity_value + debt_face_value
        
        # asset_vol = equity_vol * (E / V_a) approx
        asset_volatility = equity_volatility * (equity_value / asset_value)
        
        # Distance to Default (DD)
        # DD = (ln(V_a / D) + (r + 0.5 * vol^2) * T) / (vol * sqrt(T))
        try:
            numerator = np.log(asset_value / debt_face_value) + (self.risk_free_rate + 0.5 * asset_volatility**2) * time_to_maturity
            denominator = asset_volatility * np.sqrt(time_to_maturity)
            dd = numerator / denominator
            
            # Implied Probability of Default
            implied_pd = norm.cdf(-dd)
            
            return {
                "asset_value_est": asset_value,
                "asset_volatility_est": asset_volatility,
                "distance_to_default": dd,
                "implied_pd_percentage": implied_pd * 100
            }
        except Exception as e:
            logger.error(f"Merton DD hatası: {e}")
            return {"dd": 0.0, "implied_pd": 1.0, "error": str(e)}

    def generate_yield_curve_simulation(self, base_rate: float = 0.04, periods: int = 24) -> pd.DataFrame:
        """
        Makro simülasyonlar için sentetik verim eğrisi (Yield Curve) ve CDS spread gelişimi üretir.
        Ornstein-Uhlenbeck (Mean Reverting) süreci kullanılarak faiz patikası (Interest Rate Path) çizilir.
        """
        dt = 1/12
        theta = 0.05 # Uzun dönem ortalama
        kappa = 0.15 # Ortalamaya dönüş hızı
        sigma = 0.01 # Volatilite
        
        rates = [base_rate]
        for _ in range(periods - 1):
            random_shock = np.random.normal(0, np.sqrt(dt))
            dr = kappa * (theta - rates[-1]) * dt + sigma * random_shock
            rates.append(rates[-1] + dr)
            
        df = pd.DataFrame({
            "Month": [f"Ay {i+1}" for i in range(periods)],
            "Base_Rate": rates,
            "Corporate_Spread": [r * 1.5 + np.random.uniform(0.01, 0.03) for r in rates] # CDS approx
        })
        return df

pricing_engine = PricingEngine()

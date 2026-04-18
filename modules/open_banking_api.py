"""
modules/open_banking_api.py
Açık Bankacılık (Open Banking) Simülatörü ve NLP İşlem Sınıflandırıcı
Gerçek zamanlı banka müşteri işlem (transaction) dökümlerini çeker ve kategorize eder.
"""

import pandas as pd
import numpy as np
import uuid
import re
from datetime import datetime, timedelta

class OpenBankingAPI:
    """
    Kullanıcıların kredi kartı ve vadesiz hesap harcamalarını 
    çekip makine öğrenmesi / NLP modellerine hazırlayan API simülasyonu.
    """
    
    def __init__(self):
        # NLP Categorization Patterns (Regex based lookup mimicking text classifier)
        self.category_patterns = {
            "Gıda & Market": [r"MIGROS", r"CARREFOUR", r"BIM", r"A101", r"SOK", r"MARKET", r"FIRIN"],
            "E-Ticaret & Teknoloji": [r"AMAZON", r"TRENDYOL", r"HEPSIBURADA", r"N11", r"APPLE", r"MEDIAMARKT"],
            "Faturalar & Telekom": [r"TURKCELL", r"VODAFONE", r"TURK TELEKOM", r"ISKI", r"TEDAS", r"YEDAS", r"ENERA"],
            "Yüksek Risk (Nakit/Kripto)": [r"N_AVANS", r"BINANCE", r"BTC", r"PARIBU", r"BET", r"CASINO", r"KUMAR"],
            "Trafik & Ulaşım": [r"KGS", r"OGS", r"HGS", r"SHELL", r"OPET", r"PETROLOFISI", r"UBER", r"MARTI"],
            "Lüks & Eğlence": [r"ZARA", r"BEYMEN", r"MASSIMO", r"STARBUCKS", r"MACFIT", r"NETFLIX", r"SPOTIFY"]
        }

    def _classify_transaction(self, description: str) -> str:
        """
        Gelen metin bazlı işlem dökümünü sınıflandırır.
        Gerçek kurumsal yapılarda burada Transformer tabanlı FinBERT benzeri NLP modelleri çalışır.
        """
        desc_upper = str(description).upper()
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, desc_upper):
                    return category
        return "Diğer"

    def fetch_synthetic_transactions(self, customer_id: int, months_back: int = 3, num_transactions: int = 150) -> pd.DataFrame:
        """
        Belirtilen müşteri için son X aya ait rastgele sahte bankacılık ekstresi üretir.
        """
        np.random.seed(customer_id + int(datetime.now().timestamp() % 100)) # Pseudo-random
        
        merchants = [
            "MIGROS KADIKOY", "CARREFOURSA IST", "N_AVANS ÇEKİM", "APPLE STORE", "TRENDYOL.COM",
            "TURKCELL ILETISIM", "HEPSIBURADA", "SHELL AKARYAKIT", "STARBUCKS COFFEE", "ISKI SU FAT",
            "BEYMEN ZORLU", "BINANCE TR", "SPOTIFY ABONELIK", "KGS BAKIYE YUKLEME", "ECZANE",
            "ATM NAKIT CEKIM", "KIRA ODEMESI"
        ]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months_back)
        
        transactions = []
        
        for _ in range(num_transactions):
            random_days = np.random.randint(0, (end_date - start_date).days)
            tx_date = start_date + timedelta(days=random_days)
            merchant = np.random.choice(merchants)
            
            # Tutar üretimi (harcama tipine göre ağırlıklı)
            if "KIRA" in merchant:
                amount = np.random.uniform(8000, 25000)
                tx_type = "OUT"
            elif "NAKIT CEKIM" in merchant or "N_AVANS" in merchant:
                amount = np.random.uniform(2000, 15000)
                tx_type = "OUT"
            elif "BINANCE" in merchant:
                amount = np.random.uniform(1000, 50000)
                tx_type = "OUT"
            else:
                amount = np.random.exponential(scale=350) + 20
                tx_type = "OUT"
                
            # %5 olasılıkla para girişi (maaş veya transfer)
            if np.random.rand() < 0.05:
                merchant = "GELEN TRANSFER / MAAS"
                amount = np.random.uniform(15000, 80000)
                tx_type = "IN"
                
            tx = {
                "transaction_id": str(uuid.uuid4())[:8],
                "date": tx_date.strftime("%Y-%m-%d"),
                "merchant_description": merchant,
                "amount_try": round(amount, 2),
                "type": tx_type,
                "category": self._classify_transaction(merchant) if tx_type == "OUT" else "Gelir/Transfer"
            }
            transactions.append(tx)
            
        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date", ascending=False).reset_index(drop=True)
        return df

    def analyze_account_health(self, df: pd.DataFrame) -> dict:
        """
        NLP ile kategorize edilmiş hesap hareketlerinin risk analizini yapar.
        Aylık lüks oranı, riskli harcamalar, nakit çevrimi tespit edilir.
        """
        if df.empty:
            return {"status": "No Data"}
            
        out_df = df[df["type"] == "OUT"]
        in_df = df[df["type"] == "IN"]
        
        total_spent = out_df["amount_try"].sum()
        total_income = in_df["amount_try"].sum()
        
        # Yüksek riskli işlemler (Kripto, Bahis, Nakit Avans vs)
        high_risk_spent = out_df[out_df["category"] == "Yüksek Risk (Nakit/Kripto)"]["amount_try"].sum()
        high_risk_ratio = (high_risk_spent / total_spent) if total_spent > 0 else 0
        
        flags = []
        if high_risk_ratio > 0.15:
            flags.append("🚨 İşlemlerin %15'in den fazlası Yüksek Riskli/Kripto/Nakit Avans segmentinde!")
        if total_spent > total_income * 1.5 and total_income > 0:
            flags.append("⚠️ Son 3 ayda harcamalar, gelen net transferi %50 oranında aşıyor.")
            
        return {
            "total_income_3m": total_income,
            "total_spent_3m": total_spent,
            "high_risk_ratio": high_risk_ratio * 100,
            "net_flow": total_income - total_spent,
            "warning_flags": flags,
            "category_breakdown": out_df.groupby("category")["amount_try"].sum().to_dict()
        }

open_banking_api = OpenBankingAPI()

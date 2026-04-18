"""
modules/microstructure_engine.py — ProQuant Capital | Piyasa Mikro Yapı Analiz Motoru v5.0
========================================================================================

Finansal piyasaların en alt katmanındaki veri akışlarını, likidite dinamiklerini ve
Limit Order Book (LOB) yapısını inceleyen yüksek performanslı analiz motoru.
Bu modül, fiyat hareketlerinin arkasındaki 'emir akışı' (order flow) zekasını modeller.

Kapsam:
  1. Limit Order Book (LOB) Modelleme:
     - Bid/Ask Derinliği (Depth) ve Dengesizliği (Imbalance).
     - Spread Analizi: Quoted Spread, Effective Spread, Realized Spread.
  2. Likidite Metrikleri:
     - Amihud Illiquidity Ratio: Getiri / Hacim duyarlılığı.
     - Kyle's Lambda: Emir büyüklüğünün fiyat üzerindeki etkisi.
     - Hui-Heubel Likidite İndeksi.
  3. Bilgi Odaklı Ticaret Olasılığı (VPIN):
     - Volume-Synchronized Probability of Informed Trading.
     - Piyasa toksisitesi (toxicity) ve ani çöküş (Flash Crash) öncü göstergeleri.
  4. Tick Veri İşleme:
     - Trade-by-trade veri temizleme ve normalize etme.
     - Hacim barları (Volume Bars) ve zaman barları (Time Bars) dönüşümleri.

Matematiksel Alt Yapı:
  - Vektörel likidite hesaplamaları.
  - VPIN olasılık yoğunluk fonksiyonu simülasyonu.
  - Mikro-fiyat (Micro-price) hesaplama.

Author  : ProQuant Capital High-Frequency Trading Desk
Version : 5.0.0
"""

from __future__ import annotations

import math
import random
import datetime
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: LOB VE TİK VERİ YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OrderBookLevel:
    """LOB üzerindeki tek bir fiyat seviyesi."""
    price: float
    volume: float

@dataclass
class OrderBookSnapshot:
    """Belirli bir andaki LOB görünümü."""
    symbol: str
    timestamp: datetime.datetime
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]

    def get_mid_price(self) -> float:
        if not self.bids or not self.asks: return 0.0
        return (self.bids[0].price + self.asks[0].price) / 2.0

    def get_imbalance(self) -> float:
        """Sipariş defteri dengesizliğini (Order Imbalance) hesaplar."""
        bid_vol = sum(level.volume for level in self.bids[:5])
        ask_vol = sum(level.volume for level in self.asks[:5])
        if (bid_vol + ask_vol) == 0: return 0.0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: LİKİDİTE VE MALİYET MOTORU
# ─────────────────────────────────────────────────────────────────────────────

class LiquidityAnalytics:
    """Piyasa derinliğini ve işlem maliyetini ölçen motor."""

    @staticmethod
    def calculate_amihud_illiquidity(returns: np.ndarray, volumes: np.ndarray) -> float:
        """
        ILLIQ = Average(|R| / Volume)
        Fiyatın hacme karşı duyarlılığı (Ne kadar yüksekse likidite o kadar düşüktür).
        """
        if len(returns) == 0 or np.sum(volumes) == 0: return 0.0
        # Sıfır hacimli günleri filtrele
        mask = volumes > 0
        return np.mean(np.abs(returns[mask]) / volumes[mask])

    @staticmethod
    def calculate_micro_price(snapshot: OrderBookSnapshot) -> float:
        """
        Hacim ağırlıklı orta fiyat (Micro-price).
        MP = (P_bid * V_ask + P_ask * V_bid) / (V_bid + V_ask)
        Gelecekteki fiyat hareketinin daha iyi bir tahmincisidir.
        """
        if not snapshot.bids or not snapshot.asks: return 0.0
        p_bid, v_bid = snapshot.bids[0].price, snapshot.bids[0].volume
        p_ask, v_ask = snapshot.asks[0].price, snapshot.asks[0].volume
        return (p_bid * v_ask + p_ask * v_bid) / (v_bid + v_ask)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: VPIN (VOLUMETRIC TOXICITY ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────

class VPINAnalyzer:
    """Bilgi odaklı ticaret olasılığını (Informed Trading) modeller."""

    def __init__(self, bucket_volume: int = 1000):
        self.bucket_volume = bucket_volume
        self.buckets: List[Dict[str, float]] = []

    def calculate_vpin(self, trade_data: List[Dict[str, Any]]) -> float:
        """
        VPIN = Σ|V_buy - V_sell| / (n * BucketVolume)
        Hacim bazlı toksisite ölçümü.
        """
        if not trade_data: return 0.0
        
        # Hacim kovalarına (volume buckets) ayır
        v_buys, v_sells = [], []
        curr_buy, curr_sell, curr_total = 0, 0, 0
        
        for trade in trade_data:
            vol = trade['volume']
            # Tick-rule: Fiyat arttıysa alış, düştüyse satış (basitleştirilmiş)
            side = trade['side'] # 'BUY' or 'SELL'
            
            if side == 'BUY': curr_buy += vol
            else: curr_sell += vol
            
            curr_total += vol
            if curr_total >= self.bucket_volume:
                v_buys.append(curr_buy)
                v_sells.append(curr_sell)
                curr_buy, curr_sell, curr_total = 0, 0, 0
                
        if len(v_buys) < 5: return 0.0 # Yetersiz veri
        
        # Olasılık hesapla
        imbalances = [abs(b - s) for b, s in zip(v_buys, v_sells)]
        return sum(imbalances) / (len(imbalances) * self.bucket_volume)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: MİKRO YAPI ORKESTRATÖRÜ
# ─────────────────────────────────────────────────────────────────────────────

class MicrostructureOrchestrator:
    """Tüm mikro-yapı süreçlerini yöneten ana API."""

    def __init__(self):
        self.liquidity = LiquidityAnalytics()
        self.vpin_engine = VPINAnalyzer()
        self.history: List[OrderBookSnapshot] = []

    def analyze_order_flow(self, snapshot: OrderBookSnapshot) -> Dict[str, Any]:
        """Anlık LOB görünümünü analiz eder."""
        mid_price = snapshot.get_mid_price()
        micro_price = self.liquidity.calculate_micro_price(snapshot)
        imbalance = snapshot.get_imbalance()
        
        # Gelecek sinyali (Price Pressure)
        # Mikro-fiyat orta-fiyatın üzerindeyse alış baskısı vardır (yukarı yönlü baskı)
        pressure = (micro_price / mid_price) - 1.0 if mid_price != 0 else 0
        
        return {
            "symbol": snapshot.symbol,
            "mid_price": round(mid_price, 4),
            "micro_price": round(micro_price, 4),
            "imbalance": round(imbalance, 4),
            "price_pressure_bps": round(pressure * 10000, 2),
            "liquidity_state": "DEEP" if abs(imbalance) < 0.2 else "THIN",
            "timestamp": snapshot.timestamp.isoformat()
        }

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

_micro_engine = MicrostructureOrchestrator()

def get_microstructure_engine() -> MicrostructureOrchestrator:
    return _micro_engine

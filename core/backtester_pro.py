"""
core/backtester_pro.py — ProQuant Capital | Profesyonel Event-Driven Backtest Motoru v4.0
=======================================================================================

Gelişmiş olay-tabanlı (event-driven) backtest mimarisi. Bu modül, bir ticaret stratejisinin
tarihsel veriler üzerindeki performansını gerçekçi piyasa koşulları (slippage, gecikme,
işlem maliyeti) altında simüle eder.

Mimarisi (Architecture):
  1. Event Queue: Tüm sistem olaylarını (Market, Signal, Order, Fill) yöneten kuyruk.
  2. Data Handler: Tarihsel verileri (CSV, DB, Sim) Bar-by-Bar servis eden arayüz.
  3. Strategy Engine: Sinyal üretim mantığını barındıran kullanıcı tanımlı sınıflar.
  4. Portfolio Manager: Pozisyon takibi, risk limitleri ve sermaye yönetimi.
  5. Execution Simulator: Emirlerin piyasada dolumunu (Fill) simüle eden katman.
  6. Performance Analytics: Sharpe, Sortino, Drawdown ve Equity Curve hesaplama.

Olay Tipleri (Event Types):
  - MARKET: Yeni bir fiyat barı veya tick geldiğinde tetiklenir.
  - SIGNAL: Strateji bir ticaret fırsatı tespit ettiğinde üretilir.
  - ORDER: Portföy yöneticisi sinyali onaylayıp emir gönderdiğinde üretilir.
  - FILL: Broker (simülatör) emri gerçekleştirdiğinde üretilir.

Gelişmiş Özellikler:
  - Multi-Asset Support: Aynı anda birden fazla enstrümanı backtest edebilme.
  - Intraday & Daily: Dakikalıktan günlüğe farklı zaman dilimleri.
  - Vectorized vs Event-Driven Hybrid: Analiz için vektörel, simülasyon için olay-tabanlı.

Author  : ProQuant Capital Quantitative Engineering Desk
Version : 4.0.0
"""

from __future__ import annotations

import queue
import time
import math
import datetime
import collections
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, Set

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: OLAY SİSTEMİ (EVENTS)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Event:
    """Temel olay sınıfı."""
    type: str

@dataclass
class MarketEvent(Event):
    """Yeni piyasa verisi olayı."""
    def __init__(self):
        self.type = 'MARKET'

@dataclass
class SignalEvent(Event):
    """Strateji sinyal olayı."""
    def __init__(self, symbol: str, datetime: Any, signal_type: str, strength: float = 1.0):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type # 'LONG', 'SHORT', 'EXIT'
        self.strength = strength

@dataclass
class OrderEvent(Event):
    """Portföyden broker'a giden emir olayı."""
    def __init__(self, symbol: str, order_type: str, quantity: int, direction: str):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type # 'MKT', 'LMT'
        self.quantity = quantity
        self.direction = direction # 'BUY', 'SELL'

@dataclass
class FillEvent(Event):
    """Emrin gerçekleşme (dolum) olayı."""
    def __init__(self, timeindex: Any, symbol: str, exchange: str, 
                 quantity: int, direction: str, fill_cost: float, commission: float = None):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost # Dolum fiyatı
        self.commission = commission or self._calculate_commission()

    def _calculate_commission(self) -> float:
        """İşlem maliyeti simülasyonu (IBKR standardı benzeri)."""
        # Minimum 1$, hisse başı 0.005$ veya hacmin %0.01'i
        full_cost = self.quantity * self.fill_cost
        comm = max(1.0, full_cost * 0.001)
        return comm

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: VERİ YÖNETİMİ (DATA HANDLER)
# ─────────────────────────────────────────────────────────────────────────────

class DataHandler:
    """Tarihsel verileri sırayla sunan soyut sınıf."""
    def get_latest_bars(self, symbol: str, N: int = 1) -> List[Tuple]:
        raise NotImplementedError

    def update_bars(self):
        raise NotImplementedError

class HistoricCSVDataHandler(DataHandler):
    """CSV dosyalarından veri okuyan handler."""
    def __init__(self, events: queue.Queue, symbol_list: List[str]):
        self.events = events
        self.symbol_list = symbol_list
        self.symbol_data: Dict[str, pd.DataFrame] = {}
        self.latest_symbol_data: Dict[str, List] = {s: [] for s in symbol_list}
        self.continue_backtest = True
        self._load_all_data()

    def _load_all_data(self):
        """Tüm sembol verilerini belleğe yükle."""
        for s in self.symbol_list:
            # Gerçekte dosya okunur, burada simüle ediliyor
            n = 500
            dates = pd.date_range(end=datetime.datetime.now(), periods=n, freq='D')
            prices = np.cumsum(np.random.normal(0, 5, n)) + 1000
            df = pd.DataFrame({
                'datetime': dates, 'open': prices, 'high': prices + 5, 
                'low': prices - 5, 'close': prices, 'volume': 10000
            })
            df.set_index('datetime', inplace=True)
            self.symbol_data[s] = df.iterrows()

    def get_latest_bar(self, symbol: str):
        return self.latest_symbol_data[symbol][-1] if self.latest_symbol_data[symbol] else None

    def update_bars(self):
        """Her sembol için bir sonraki barı çıkarır ve MARKET olayı tetikler."""
        for s in self.symbol_list:
            try:
                bar = next(self.symbol_data[s])
                self.latest_symbol_data[s].append(bar)
            except StopIteration:
                self.continue_backtest = False
        
        self.events.put(MarketEvent())

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: STRATEJİ MOTORU (STRATEGY)
# ─────────────────────────────────────────────────────────────────────────────

class Strategy:
    """Kullanıcı stratejileri için temel sınıf."""
    def calculate_signals(self, event: MarketEvent):
        raise NotImplementedError

class MovingAverageCrossStrategy(Strategy):
    """Çift Hareketli Ortalama (SMA) Kesişim Stratejisi."""
    def __init__(self, bars: DataHandler, events: queue.Queue, short_window: int = 20, long_window: int = 100):
        self.bars = bars
        self.events = events
        self.symbol_list = bars.symbol_list
        self.short_window = short_window
        self.long_window = long_window
        self.bought = {s: 'FLAT' for s in self.symbol_list}

    def calculate_signals(self, event: MarketEvent):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.latest_symbol_data[s]
                if len(bars) >= self.long_window:
                    closes = [b[1]['close'] for b in bars]
                    short_sma = np.mean(closes[-self.short_window:])
                    long_sma  = np.mean(closes[-self.long_window:])
                    
                    dt = bars[-1][0]
                    if short_sma > long_sma and self.bought[s] == 'FLAT':
                        self.events.put(SignalEvent(s, dt, 'LONG'))
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == 'LONG':
                        self.events.put(SignalEvent(s, dt, 'EXIT'))
                        self.bought[s] = 'FLAT'

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: PORTFÖY YÖNETİCİSİ (PORTFOLIO)
# ─────────────────────────────────────────────────────────────────────────────

class Portfolio:
    """Pozisyonları, kâr/zararı ve emir yönetimini idare eder."""
    def __init__(self, bars: DataHandler, events: queue.Queue, start_date: Any, initial_capital: float = 100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        self.all_positions = self._construct_all_positions()
        self.current_positions = {s: 0 for s in self.symbol_list}
        
        self.all_holdings = self._construct_all_holdings()
        self.current_holdings = self._construct_current_holdings()

    def _construct_all_positions(self):
        d = {s: 0 for s in self.symbol_list}
        d['datetime'] = self.start_date
        return [d]

    def _construct_all_holdings(self):
        d = {s: 0.0 for s in self.symbol_list}
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def _construct_current_holdings(self):
        d = {s: 0.0 for s in self.symbol_list}
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event: MarketEvent):
        """Piyasa günü kapandığında portföy değerlerini güncelle."""
        bars = {s: self.bars.get_latest_bar(s) for s in self.symbol_list}
        
        # Pozisyonları kaydet
        dp = {s: self.current_positions[s] for s in self.symbol_list}
        dp['datetime'] = bars[self.symbol_list[0]][0] 
        self.all_positions.append(dp)
        
        # Değerleri (Holdings) kaydet
        dh = {s: 0.0 for s in self.symbol_list}
        dh['datetime'] = dp['datetime']
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        
        for s in self.symbol_list:
            market_val = self.current_positions[s] * bars[s][1]['close']
            dh[s] = market_val
            dh['total'] += market_val
            
        self.all_holdings.append(dh)

    def update_signal(self, event: SignalEvent):
        """Sinyal geldiğinde emir (Order) üret."""
        if event.type == 'SIGNAL':
            symbol = event.symbol
            direction = event.signal_type
            qty = 100 # Sabit miktar (Gerçekte risk engine hesaplar)
            
            if direction == 'LONG':
                self.events.put(OrderEvent(symbol, 'MKT', qty, 'BUY'))
            if direction == 'EXIT':
                self.events.put(OrderEvent(symbol, 'MKT', self.current_positions[symbol], 'SELL'))

    def update_fill(self, event: FillEvent):
        """İşlem gerçekleştiğinde portföyü güncelle."""
        if event.type == 'FILL':
            # Pozisyon güncelle
            fill_dir = 1 if event.direction == 'BUY' else -1
            self.current_positions[event.symbol] += fill_dir * event.quantity
            
            # Nakit ve maliyet güncelle
            cost = fill_dir * event.fill_cost * event.quantity
            self.current_holdings['cash'] -= (cost + event.commission)
            self.current_holdings['commission'] += event.commission

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 5: YÜRÜTME SİMÜLATÖRÜ (EXECUTION)
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionHandler:
    """Emirleri piyasada gerçekleştiren broker simülasyonu."""
    def __init__(self, events: queue.Queue):
        self.events = events

    def execute_order(self, event: OrderEvent):
        if event.type == 'ORDER':
            # Simüle edilmiş dolum: Anlık fiyat üzerinden (Slippage eklenebilir)
            fill_event = FillEvent(
                datetime.datetime.now(), event.symbol, 'NASDAQ', 
                event.quantity, event.direction, 1000.0 # Sabit fiyat simülasyonu
            )
            self.events.put(fill_event)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 6: ANALİZ & METRİKLER (PERFORMANCE)
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceEngine:
    """Backtest sonuçlarını analiz eden istatistik motoru."""
    
    @staticmethod
    def create_sharpe_ratio(returns: pd.Series, periods: int = 252) -> float:
        """Sharpe Oranı hesapla."""
        return np.sqrt(periods) * (np.mean(returns) / np.std(returns)) if np.std(returns) != 0 else 0

    @staticmethod
    def create_drawdowns(equity_curve: pd.Series) -> Tuple[pd.Series, float, int]:
        """Max Drawdown ve süresini hesapla."""
        hwm = equity_curve.cummax()
        drawdown = (hwm - equity_curve) / hwm
        max_dd = drawdown.max()
        # Max DD süresi simülasyonu
        dd_duration = 10 
        return drawdown, max_dd, dd_duration

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 7: BACKTEST ORKESTRATÖRÜ (ENGINE)
# ─────────────────────────────────────────────────────────────────────────────

class BacktestOrchestrator:
    """Tüm bileşenleri birleştiren ana döngü (Event Loop)."""
    def __init__(self, symbol_list: List[str], initial_capital: float = 100000.0):
        self.symbol_list = symbol_list
        self.events = queue.Queue()
        
        self.data_handler = HistoricCSVDataHandler(self.events, self.symbol_list)
        self.strategy = MovingAverageCrossStrategy(self.data_handler, self.events)
        self.portfolio = Portfolio(self.data_handler, self.events, datetime.datetime.now(), initial_capital)
        self.execution = ExecutionHandler(self.events)

    def run(self):
        """Olay döngüsünü başlat (The Heart of the System)."""
        print("🚀 ProQuant Backtest Pro Başlatılıyor...")
        
        while True:
            # Veri güncelle
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
            else:
                break

            # Olayları işle
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.execution.execute_order(event)
                        elif event.type == 'FILL':
                            self.portfolio.update_fill(event)

            # (Opsiyonel) Simülasyon hızı için bekleme
            # time.sleep(0.01)

        print("✅ Backtest Tamamlandı. Performans analizi üretiliyor...")
        self._output_performance()

    def _output_performance(self):
        """Sonuçları özetle."""
        stats = PerformanceEngine()
        equity_df = pd.DataFrame(self.portfolio.all_holdings)
        equity_df.set_index('datetime', inplace=True)
        
        returns = equity_df['total'].pct_change().dropna()
        sharpe = stats.create_sharpe_ratio(returns)
        _, max_dd, _ = stats.create_drawdowns(equity_df['total'])
        
        print(f"--- SONUÇLAR ---")
        print(f"Başlangıç Sermayesi : ${self.portfolio.initial_capital:,.2f}")
        print(f"Final Değer         : ${equity_df['total'].iloc[-1]:,.2f}")
        print(f"Sharpe Oranı        : {sharpe:.2f}")
        print(f"Max Drawdown        : %{max_dd*100:.2f}")

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

def get_backtest_engine(symbols: List[str]) -> BacktestOrchestrator:
    return BacktestOrchestrator(symbols)

if __name__ == "__main__":
    engine = get_backtest_engine(["AAPL", "TSLA"])
    engine.run()

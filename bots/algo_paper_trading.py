"""
bots/algo_paper_trading.py — ProQuant Capital | Algoritmik Kağıt Trading Botu v2.0
====================================================================================

Kurumsal sınıf, olay güdümlü (event-driven) algoritmik trading simülatörü.
Backtrader/Zipline mimarisine benzeyen profesyonel Order Book, Slipaj Modeli,
Komisyon Motoru ve Strateji Framework'ü içerir.

Desteklenen Stratejiler:
  - Momentum (RSI tabanlı)
  - Mean Reversion (Bollinger Bands)
  - Trend Following (EMA Crossover)
  - Arbitrage Simulation
  - ML-Guided Signals (credit risk feedback)

Author  : ProQuant Capital Quant Research Desk
Version : 2.0.0
"""

from __future__ import annotations

import math
import time
import uuid
import random
import logging
import hashlib
import datetime
import statistics
import itertools
import collections
from enum import Enum, auto
from typing import (
    Any, Dict, List, Optional, Tuple, Callable,
    Generator, Deque, NamedTuple, Union
)
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 1: ENUM TANIMLAMALARI & SABİTLER
# ═══════════════════════════════════════════════════════════════════════════════

class OrderSide(Enum):
    BUY  = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT  = "LIMIT"
    STOP   = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

class OrderStatus(Enum):
    PENDING   = "PENDING"
    PARTIAL   = "PARTIAL"
    FILLED    = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED  = "REJECTED"
    EXPIRED   = "EXPIRED"

class PositionSide(Enum):
    LONG  = "LONG"
    SHORT = "SHORT"
    FLAT  = "FLAT"

class AssetClass(Enum):
    EQUITY       = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    COMMODITY    = "COMMODITY"
    CRYPTO       = "CRYPTO"
    FX           = "FX"
    DERIVATIVE   = "DERIVATIVE"

class SignalType(Enum):
    STRONG_BUY  = 2
    BUY         = 1
    NEUTRAL     = 0
    SELL        = -1
    STRONG_SELL = -2

class RiskLevel(Enum):
    VERY_LOW  = "VERY_LOW"
    LOW       = "LOW"
    MEDIUM    = "MEDIUM"
    HIGH      = "HIGH"
    VERY_HIGH = "VERY_HIGH"

# Piyasa sabitleri
TRADING_DAYS_PER_YEAR   = 252
HOURS_PER_SESSION       = 8
MINUTES_PER_SESSION     = 480
TICK_SIZE_DEFAULT       = 0.01
LOT_SIZE_EQUITY         = 100
LOT_SIZE_BOND           = 1000
RISK_FREE_RATE_DEFAULT  = 0.045   # %4.5 — TCMB politika faizi
MAX_POSITION_PCT        = 0.20    # Tek pozisyon maks. %20 portföy
DEFAULT_LEVERAGE        = 1.0
MAX_LEVERAGE_EQUITY     = 3.0
MAX_LEVERAGE_FUTURES    = 10.0


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 2: VERİ YAPILARI
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Instrument:
    """İşlem gören enstrüman tanımı."""
    symbol      : str
    name        : str
    asset_class : AssetClass
    currency    : str = "TRY"
    tick_size   : float = TICK_SIZE_DEFAULT
    lot_size    : int   = LOT_SIZE_EQUITY
    margin_req  : float = 1.0      # 1.0 = leverage yok
    listing_exchange: str = "BIST"
    sector      : str  = "Genel"
    isin        : str  = ""
    metadata    : Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.isin:
            self.isin = f"TR{hashlib.md5(self.symbol.encode()).hexdigest()[:10].upper()}"

    @property
    def display_name(self) -> str:
        return f"{self.symbol} ({self.listing_exchange})"


@dataclass
class OHLCV:
    """Mum çubuğu verisi (Open/High/Low/Close/Volume)."""
    timestamp : datetime.datetime
    open      : float
    high      : float
    low       : float
    close     : float
    volume    : int
    vwap      : float = 0.0
    trades    : int   = 0

    def __post_init__(self):
        if self.vwap == 0.0:
            self.vwap = (self.open + self.high + self.low + self.close) / 4

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3

    @property
    def range_pct(self) -> float:
        if self.low == 0:
            return 0.0
        return (self.high - self.low) / self.low * 100


@dataclass
class Tick:
    """Anlık fiyat tick verisi."""
    timestamp  : datetime.datetime
    symbol     : str
    bid        : float
    ask        : float
    last       : float
    volume     : int
    bid_size   : int = 100
    ask_size   : int = 100

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    @property
    def spread_pct(self) -> float:
        if self.bid == 0:
            return 0.0
        return self.spread / self.bid * 100

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass
class Order:
    """Emir nesnesi."""
    order_id    : str
    symbol      : str
    side        : OrderSide
    order_type  : OrderType
    quantity    : int
    price       : Optional[float]   = None   # LIMIT için zorunlu
    stop_price  : Optional[float]   = None   # STOP için zorunlu
    status      : OrderStatus       = OrderStatus.PENDING
    filled_qty  : int               = 0
    avg_fill_price: float           = 0.0
    commission  : float             = 0.0
    slippage    : float             = 0.0
    created_at  : datetime.datetime = field(default_factory=datetime.datetime.now)
    filled_at   : Optional[datetime.datetime] = None
    strategy_tag: str               = ""
    notes       : str               = ""
    time_in_force: str              = "GTC"  # GTC, DAY, IOC, FOK

    def __post_init__(self):
        if not self.order_id:
            self.order_id = str(uuid.uuid4())[:8].upper()

    @property
    def is_open(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.PARTIAL)

    @property
    def remaining_qty(self) -> int:
        return self.quantity - self.filled_qty

    @property
    def total_value(self) -> float:
        return self.filled_qty * self.avg_fill_price

    @property
    def net_value(self) -> float:
        return self.total_value + self.commission


@dataclass
class Position:
    """Açık pozisyon nesnesi."""
    symbol      : str
    side        : PositionSide
    quantity    : int
    avg_cost    : float
    opened_at   : datetime.datetime = field(default_factory=datetime.datetime.now)
    unrealized_pnl: float           = 0.0
    realized_pnl  : float           = 0.0
    mark_price    : float           = 0.0
    stop_loss     : Optional[float] = None
    take_profit   : Optional[float] = None
    max_favorable : float           = 0.0   # MAE/MFE tracking
    max_adverse   : float           = 0.0
    strategy_tag  : str             = ""

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_cost

    @property
    def market_value(self) -> float:
        return self.quantity * self.mark_price

    @property
    def total_pnl(self) -> float:
        return self.unrealized_pnl + self.realized_pnl

    @property
    def pnl_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_basis * 100

    def update_mark(self, current_price: float) -> None:
        """Anlık fiyat ile pozisyonu güncelle."""
        self.mark_price = current_price
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (current_price - self.avg_cost) * self.quantity
        else:
            self.unrealized_pnl = (self.avg_cost - current_price) * self.quantity

        if self.unrealized_pnl > self.max_favorable:
            self.max_favorable = self.unrealized_pnl
        if self.unrealized_pnl < self.max_adverse:
            self.max_adverse = self.unrealized_pnl


@dataclass
class Trade:
    """Gerçekleşen işlem kaydı."""
    trade_id    : str
    order_id    : str
    symbol      : str
    side        : OrderSide
    quantity    : int
    price       : float
    commission  : float
    slippage    : float
    timestamp   : datetime.datetime
    strategy_tag: str   = ""
    pnl         : float = 0.0   # Kapanan pozisyonlarda dolu

    @property
    def gross_value(self) -> float:
        return self.quantity * self.price

    @property
    def net_value(self) -> float:
        return self.gross_value - self.commission

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id"   : self.trade_id,
            "order_id"   : self.order_id,
            "symbol"     : self.symbol,
            "side"       : self.side.value,
            "quantity"   : self.quantity,
            "price"      : round(self.price, 4),
            "commission" : round(self.commission, 4),
            "slippage"   : round(self.slippage, 4),
            "timestamp"  : self.timestamp.isoformat(),
            "strategy"   : self.strategy_tag,
            "pnl"        : round(self.pnl, 4),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 3: KOMİSYON & SLIPAJ MODELLERİ
# ═══════════════════════════════════════════════════════════════════════════════

class ICommissionModel:
    """Komisyon modeli arayüzü."""
    def calculate(self, order: Order, fill_price: float) -> float:
        raise NotImplementedError


class ISlippageModel:
    """Slipaj modeli arayüzü."""
    def calculate(self, order: Order, current_price: float, volume: int) -> float:
        raise NotImplementedError


class FixedCommissionModel(ICommissionModel):
    """Sabit TL komisyon."""
    def __init__(self, fixed_amount: float = 9.90):
        self.fixed_amount = fixed_amount

    def calculate(self, order: Order, fill_price: float) -> float:
        return self.fixed_amount


class PercentageCommissionModel(ICommissionModel):
    """İşlem hacmine göre yüzde komisyon."""
    def __init__(self,
                 rate_pct : float = 0.0015,
                 min_fee  : float = 1.0,
                 max_fee  : float = float("inf")):
        self.rate    = rate_pct   # örn. 0.0015 = %0.15
        self.min_fee = min_fee
        self.max_fee = max_fee

    def calculate(self, order: Order, fill_price: float) -> float:
        gross   = order.filled_qty * fill_price
        fee     = gross * self.rate
        return max(self.min_fee, min(self.max_fee, fee))


class TieredCommissionModel(ICommissionModel):
    """Kademeli komisyon (kurumsal brokerlar için)."""
    TIERS = [
        (0,         500_000,   0.0020),   # 0-500K → %0.20
        (500_000,   2_000_000, 0.0015),   # 500K-2M → %0.15
        (2_000_000, 10_000_000,0.0010),   # 2M-10M → %0.10
        (10_000_000,float("inf"),0.0007), # 10M+ → %0.07
    ]

    def calculate(self, order: Order, fill_price: float) -> float:
        gross = order.filled_qty * fill_price
        for lower, upper, rate in self.TIERS:
            if lower <= gross < upper:
                fee = gross * rate
                return max(5.0, fee)   # min 5 TL
        return gross * 0.0007


class FixedSlippageModel(ISlippageModel):
    """Sabit pip slipaj."""
    def __init__(self, pips: float = 0.0):
        self.pips = pips

    def calculate(self, order: Order, current_price: float, volume: int) -> float:
        direction = 1 if order.side == OrderSide.BUY else -1
        return current_price + (direction * self.pips)


class VolumeImpactSlippageModel(ISlippageModel):
    """
    Emir büyüklüğünün piyasaya etkisini modelleyen gerçekçi slipaj.
    Kyle Lambda modelinden ilham alınmıştır.
    """
    def __init__(self, impact_factor: float = 0.0001, spread_pct: float = 0.005):
        self.impact_factor = impact_factor
        self.spread_pct    = spread_pct

    def calculate(self, order: Order, current_price: float, volume: int) -> float:
        if volume == 0:
            volume = 1
        participation = order.quantity / volume
        impact        = self.impact_factor * math.sqrt(participation) * current_price
        half_spread   = current_price * self.spread_pct / 2

        if order.side == OrderSide.BUY:
            return current_price + half_spread + impact
        else:
            return current_price - half_spread - impact


class MarketImpactSlippageModel(ISlippageModel):
    """
    Almgren-Chriss piyasa etki modeli (kurumsal seviye).
    Büyük emirlerin fiyatı nasıl bozduğunu simüle eder.
    """
    def __init__(self, eta: float = 2.5e-7, sigma: float = 0.02):
        self.eta   = eta    # geçici etki katsayısı
        self.sigma = sigma  # yıllık volatilite

    def calculate(self, order: Order, current_price: float, volume: int) -> float:
        if volume == 0:
            volume = max(1, order.quantity)
        participation = order.quantity / volume
        temp_impact   = self.eta * current_price * (order.quantity ** 0.6)
        noise         = random.gauss(0, self.sigma * current_price * 0.01)

        if order.side == OrderSide.BUY:
            return current_price + temp_impact + abs(noise)
        else:
            return current_price - temp_impact - abs(noise)


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 4: ORDER BOOK (EMİR DEFTERİ)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BookLevel:
    """Order book seviyesi (fiyat + hacim)."""
    price  : float
    volume : int
    orders : int = 1


class OrderBook:
    """
    Limit Order Book (LOB) simülatörü.
    Gerçek borsalardaki emir defteri mekanizmasını taklit eder.
    """

    def __init__(self, symbol: str, depth: int = 10):
        self.symbol   = symbol
        self.depth    = depth
        self._bids    : List[BookLevel] = []   # Azalan sırada
        self._asks    : List[BookLevel] = []   # Artan sırada
        self._last    : float = 0.0
        self._volume  : int   = 0

    def _generate_symmetric_book(self, mid_price: float, spread_pct: float = 0.003,
                                  depth: int = 10) -> None:
        """Sentetik emir defteri oluştur (gerçekçi mimari)."""
        spread = mid_price * spread_pct
        half   = spread / 2

        self._bids = []
        self._asks = []

        for i in range(depth):
            decay   = 1.0 / (i + 1)
            vol_bid = int(random.lognormvariate(8, 1) * decay)
            vol_ask = int(random.lognormvariate(8, 1) * decay)

            bid_price = mid_price - half - (i * spread * 0.4)
            ask_price = mid_price + half + (i * spread * 0.4)

            if bid_price > 0:
                self._bids.append(BookLevel(
                    price=round(bid_price, 4),
                    volume=max(1, vol_bid),
                    orders=random.randint(1, 15)
                ))
            if ask_price > 0:
                self._asks.append(BookLevel(
                    price=round(ask_price, 4),
                    volume=max(1, vol_ask),
                    orders=random.randint(1, 15)
                ))

    def update(self, mid_price: float) -> None:
        """Anlık fiyata göre emir defterini güncelle."""
        self._last = mid_price
        self._generate_symmetric_book(mid_price)

    @property
    def best_bid(self) -> Optional[float]:
        return self._bids[0].price if self._bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self._asks[0].price if self._asks else None

    @property
    def spread(self) -> float:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return 0.0

    @property
    def mid_price(self) -> float:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return self._last

    def bid_depth(self, levels: int = 5) -> List[Dict]:
        return [{"price": b.price, "volume": b.volume, "orders": b.orders}
                for b in self._bids[:levels]]

    def ask_depth(self, levels: int = 5) -> List[Dict]:
        return [{"price": a.price, "volume": a.volume, "orders": a.orders}
                for a in self._asks[:levels]]

    def total_bid_volume(self, levels: int = 5) -> int:
        return sum(b.volume for b in self._bids[:levels])

    def total_ask_volume(self, levels: int = 5) -> int:
        return sum(a.volume for a in self._asks[:levels])

    @property
    def order_imbalance(self) -> float:
        """Emir dengesizliği: > 0 alıcı baskısı, < 0 satıcı baskısı."""
        bv = self.total_bid_volume()
        av = self.total_ask_volume()
        total = bv + av
        if total == 0:
            return 0.0
        return (bv - av) / total

    def simulate_fill(self, order: Order) -> Tuple[float, int]:
        """
        Emir defteri üzerinde emir dolum simülasyonu.
        Gerçek LOB sweep algoritması.
        Returns: (ortalama dolum fiyatı, doldurulan miktar)
        """
        remaining = order.quantity
        total_cost = 0.0
        filled = 0

        levels = self._asks if order.side == OrderSide.BUY else self._bids

        for level in levels:
            if remaining <= 0:
                break
            fill_at_level = min(remaining, level.volume)

            if order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and level.price > (order.price or float("inf")):
                    break
                if order.side == OrderSide.SELL and level.price < (order.price or 0):
                    break

            total_cost  += fill_at_level * level.price
            filled      += fill_at_level
            remaining   -= fill_at_level
            level.volume -= fill_at_level

        if filled == 0:
            return 0.0, 0

        avg_fill = total_cost / filled
        return avg_fill, filled


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 5: STRATEJİ FRAMEWORKÜ
# ═══════════════════════════════════════════════════════════════════════════════

class BaseStrategy:
    """Tüm stratejilerin türediği taban sınıf."""

    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name         = name
        self.params       = params or {}
        self._signals     : List[Dict] = []
        self._initialized = False

    def initialize(self, universe: List[str]) -> None:
        """Strateji başlangıç kurulumu."""
        self.universe     = universe
        self._initialized = True

    def generate_signal(self,
                        symbol: str,
                        bars  : List[OHLCV],
                        tick  : Optional[Tick] = None) -> SignalType:
        """Override edilmesi gereken sinyal üretici."""
        raise NotImplementedError

    def on_order_filled(self, order: Order) -> None:
        """Emir dolduğunda çağrılır — override opsiyonel."""
        pass

    def on_position_closed(self, position: Position, pnl: float) -> None:
        """Pozisyon kapandığında çağrılır — override opsiyonel."""
        pass

    @property
    def signal_history(self) -> List[Dict]:
        return self._signals.copy()

    def _record_signal(self, symbol: str, signal: SignalType,
                        reason: str = "", confidence: float = 0.5) -> None:
        self._signals.append({
            "timestamp"  : datetime.datetime.now().isoformat(),
            "symbol"     : symbol,
            "signal"     : signal.name,
            "reason"     : reason,
            "confidence" : confidence,
        })


class RSIMomentumStrategy(BaseStrategy):
    """
    RSI tabanlı Momentum Stratejisi.
    - RSI < oversold → BUY signal
    - RSI > overbought → SELL signal
    - RSI divergence ek filtre
    """

    def __init__(self,
                 rsi_period   : int   = 14,
                 oversold     : float = 30.0,
                 overbought   : float = 70.0,
                 extreme_os   : float = 20.0,
                 extreme_ob   : float = 80.0):
        super().__init__(
            name="RSI_Momentum",
            params={
                "rsi_period" : rsi_period,
                "oversold"   : oversold,
                "overbought" : overbought,
                "extreme_os" : extreme_os,
                "extreme_ob" : extreme_ob,
            }
        )

    @staticmethod
    def _compute_rsi(closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0

        gains  = []
        losses = []
        for i in range(1, period + 1):
            delta = closes[-i] - closes[-(i+1)]
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(delta))

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 1e-9

        rs  = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signal(self, symbol: str, bars: List[OHLCV],
                         tick: Optional[Tick] = None) -> SignalType:
        if len(bars) < self.params["rsi_period"] + 2:
            return SignalType.NEUTRAL

        closes    = [b.close for b in bars]
        rsi       = self._compute_rsi(closes, self.params["rsi_period"])
        prev_rsi  = self._compute_rsi(closes[:-1], self.params["rsi_period"])

        oversold  = self.params["oversold"]
        overbought= self.params["overbought"]
        ext_os    = self.params["extreme_os"]
        ext_ob    = self.params["extreme_ob"]

        if rsi < ext_os:
            signal = SignalType.STRONG_BUY
            reason = f"RSI aşırı satım bölgesi: {rsi:.1f} < {ext_os}"
            confidence = 0.85
        elif rsi < oversold and prev_rsi >= oversold:
            signal = SignalType.BUY
            reason = f"RSI satım bölgesine girdi: {rsi:.1f}"
            confidence = 0.65
        elif rsi > ext_ob:
            signal = SignalType.STRONG_SELL
            reason = f"RSI aşırı alım bölgesi: {rsi:.1f} > {ext_ob}"
            confidence = 0.85
        elif rsi > overbought and prev_rsi <= overbought:
            signal = SignalType.SELL
            reason = f"RSI alım bölgesine girdi: {rsi:.1f}"
            confidence = 0.65
        else:
            signal = SignalType.NEUTRAL
            reason = f"RSI nötr: {rsi:.1f}"
            confidence = 0.5

        self._record_signal(symbol, signal, reason, confidence)
        return signal


class BollingerBandsMeanReversionStrategy(BaseStrategy):
    """
    Bollinger Bantları ile Ortalamaya Dönüş Stratejisi.
    - Fiyat alt banda dokunursa BUY
    - Fiyat üst banda dokunursa SELL
    - Bandwidth sıkışması: volatilite patlaması öncesi filtre
    """

    def __init__(self, period: int = 20, num_std: float = 2.0,
                 squeeze_pct: float = 0.03):
        super().__init__(
            name="BB_MeanReversion",
            params={"period": period, "num_std": num_std, "squeeze_pct": squeeze_pct}
        )

    @staticmethod
    def _compute_bands(closes: List[float], period: int,
                        num_std: float) -> Tuple[float, float, float]:
        if len(closes) < period:
            last = closes[-1] if closes else 100.0
            return last, last * 1.02, last * 0.98

        window = closes[-period:]
        mid    = sum(window) / period
        std    = statistics.stdev(window)
        upper  = mid + num_std * std
        lower  = mid - num_std * std
        return mid, upper, lower

    def generate_signal(self, symbol: str, bars: List[OHLCV],
                         tick: Optional[Tick] = None) -> SignalType:
        if len(bars) < self.params["period"] + 1:
            return SignalType.NEUTRAL

        closes  = [b.close for b in bars]
        current = closes[-1]
        period  = self.params["period"]
        num_std = self.params["num_std"]

        mid, upper, lower = self._compute_bands(closes, period, num_std)
        bandwidth = (upper - lower) / mid if mid else 0

        # Squeeze: bantlar çok darsa sinyal verme
        if bandwidth < self.params["squeeze_pct"]:
            self._record_signal(symbol, SignalType.NEUTRAL,
                                f"BB squeeze: bandwidth={bandwidth:.3f}", 0.3)
            return SignalType.NEUTRAL

        if current <= lower:
            pct_below  = (lower - current) / lower * 100
            if pct_below > 1.5:
                signal = SignalType.STRONG_BUY
                conf   = 0.80
            else:
                signal = SignalType.BUY
                conf   = 0.60
            reason = f"Fiyat alt banda değdi: {current:.2f} ≤ {lower:.2f}"
        elif current >= upper:
            pct_above  = (current - upper) / upper * 100
            if pct_above > 1.5:
                signal = SignalType.STRONG_SELL
                conf   = 0.80
            else:
                signal = SignalType.SELL
                conf   = 0.60
            reason = f"Fiyat üst banda değdi: {current:.2f} ≥ {upper:.2f}"
        else:
            signal = SignalType.NEUTRAL
            reason = f"Fiyat bantlar içinde: {lower:.2f}–{upper:.2f}"
            conf   = 0.5

        self._record_signal(symbol, signal, reason, conf)
        return signal


class EMAcrossoverStrategy(BaseStrategy):
    """
    Üstel Hareketli Ortalama (EMA) Çapraz Geçiş Stratejisi.
    Hızlı EMA, yavaş EMA'yı yukarı keserse BUY ("Altın Haç").
    Aşağı keserse SELL ("Ölüm Haçı").
    """

    def __init__(self, fast_period: int = 9, slow_period: int = 21,
                 signal_period: int = 5):
        super().__init__(
            name="EMA_Crossover",
            params={
                "fast_period"  : fast_period,
                "slow_period"  : slow_period,
                "signal_period": signal_period,
            }
        )

    @staticmethod
    def _ema(prices: List[float], period: int) -> List[float]:
        if not prices:
            return []
        k     = 2 / (period + 1)
        emas  = [prices[0]]
        for p in prices[1:]:
            emas.append(p * k + emas[-1] * (1 - k))
        return emas

    def generate_signal(self, symbol: str, bars: List[OHLCV],
                         tick: Optional[Tick] = None) -> SignalType:
        slow_p = self.params["slow_period"]
        fast_p = self.params["fast_period"]

        if len(bars) < slow_p + 2:
            return SignalType.NEUTRAL

        closes     = [b.close for b in bars]
        fast_emas  = self._ema(closes, fast_p)
        slow_emas  = self._ema(closes, slow_p)

        fast_now   = fast_emas[-1]
        fast_prev  = fast_emas[-2]
        slow_now   = slow_emas[-1]
        slow_prev  = slow_emas[-2]

        cross_up   = fast_prev <= slow_prev and fast_now > slow_now
        cross_down = fast_prev >= slow_prev and fast_now < slow_now
        gap_pct    = abs(fast_now - slow_now) / slow_now * 100 if slow_now else 0

        if cross_up:
            if gap_pct > 0.5:
                signal = SignalType.STRONG_BUY
                conf   = 0.82
            else:
                signal = SignalType.BUY
                conf   = 0.62
            reason = f"Altın Haç: EMA{fast_p} ({fast_now:.2f}) > EMA{slow_p} ({slow_now:.2f})"
        elif cross_down:
            if gap_pct > 0.5:
                signal = SignalType.STRONG_SELL
                conf   = 0.82
            else:
                signal = SignalType.SELL
                conf   = 0.62
            reason = f"Ölüm Haçı: EMA{fast_p} ({fast_now:.2f}) < EMA{slow_p} ({slow_now:.2f})"
        elif fast_now > slow_now:
            signal = SignalType.NEUTRAL
            reason = f"Yükselen trend (EMA gap: {gap_pct:.2f}%)"
            conf   = 0.5
        else:
            signal = SignalType.NEUTRAL
            reason = f"Alçalan trend (EMA gap: {gap_pct:.2f}%)"
            conf   = 0.5

        self._record_signal(symbol, signal, reason, conf)
        return signal


class MACDStrategy(BaseStrategy):
    """
    Moving Average Convergence Divergence (MACD) Stratejisi.
    MACD hattı sinyal hattını geçince sinyal üretir.
    Histogram sıfır geçişleri ek onay verir.
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(
            name="MACD",
            params={"fast": fast, "slow": slow, "signal": signal}
        )

    @staticmethod
    def _ema(prices: List[float], period: int) -> List[float]:
        if not prices:
            return []
        k   = 2 / (period + 1)
        out = [prices[0]]
        for p in prices[1:]:
            out.append(p * k + out[-1] * (1 - k))
        return out

    def _compute_macd(self, closes: List[float]) -> Tuple[List[float], List[float], List[float]]:
        fast_p  = self.params["fast"]
        slow_p  = self.params["slow"]
        sig_p   = self.params["signal"]

        fast_ema   = self._ema(closes, fast_p)
        slow_ema   = self._ema(closes, slow_p)
        macd_line  = [f - s for f, s in zip(fast_ema, slow_ema)]
        signal_line= self._ema(macd_line, sig_p)
        histogram  = [m - s for m, s in zip(macd_line, signal_line)]
        return macd_line, signal_line, histogram

    def generate_signal(self, symbol: str, bars: List[OHLCV],
                         tick: Optional[Tick] = None) -> SignalType:
        if len(bars) < 40:
            return SignalType.NEUTRAL

        closes     = [b.close for b in bars]
        macd, sig, hist = self._compute_macd(closes)

        if len(macd) < 2:
            return SignalType.NEUTRAL

        macd_now  = macd[-1];  macd_prev  = macd[-2]
        sig_now   = sig[-1];   sig_prev   = sig[-2]
        hist_now  = hist[-1];  hist_prev  = hist[-2]

        # Çapraz geçiş + histogram onayı
        bull_cross = macd_prev < sig_prev and macd_now >= sig_now
        bear_cross = macd_prev > sig_prev and macd_now <= sig_now

        # Histogram ivmesi
        hist_accel = (hist_now - hist_prev) > 0

        if bull_cross and hist_accel:
            signal = SignalType.STRONG_BUY
            conf   = 0.80
            reason = f"MACD bullish crossover + histogram ivmesi"
        elif bull_cross:
            signal = SignalType.BUY
            conf   = 0.62
            reason = f"MACD bullish crossover"
        elif bear_cross and not hist_accel:
            signal = SignalType.STRONG_SELL
            conf   = 0.80
            reason = f"MACD bearish crossover + histogram ivmesi"
        elif bear_cross:
            signal = SignalType.SELL
            conf   = 0.62
            reason = f"MACD bearish crossover"
        else:
            signal = SignalType.NEUTRAL
            reason = f"MACD nötr: {macd_now:.4f}"
            conf   = 0.5

        self._record_signal(symbol, signal, reason, conf)
        return signal


class MLGuidedStrategy(BaseStrategy):
    """
    Kredi Risk Motoru'ndan gelen skorları trading sinyaline çeviren hibrit strateji.
    Müşteri kredi kalitesi bozulunca tahvil pozisyonu aç.
    """

    def __init__(self, credit_threshold_buy: float = 700,
                 credit_threshold_sell: float = 400):
        super().__init__(
            name="ML_Credit_Guided",
            params={
                "buy_threshold" : credit_threshold_buy,
                "sell_threshold": credit_threshold_sell,
            }
        )
        self._credit_scores: Dict[str, float] = {}

    def update_credit_score(self, symbol: str, score: float) -> None:
        """Kredi motor entegrasyonu: skoru güncelle."""
        self._credit_scores[symbol] = score

    def generate_signal(self, symbol: str, bars: List[OHLCV],
                         tick: Optional[Tick] = None) -> SignalType:
        if symbol not in self._credit_scores:
            # Sentetik skor
            score = random.uniform(300, 850)
            self._credit_scores[symbol] = score
        else:
            score = self._credit_scores[symbol]

        buy_thr  = self.params["buy_threshold"]
        sell_thr = self.params["sell_threshold"]

        if score >= buy_thr:
            signal = SignalType.BUY
            reason = f"Yüksek kredi skoru ({score:.0f} ≥ {buy_thr}): Tahvil AL"
            conf   = min(0.95, score / 850)
        elif score <= sell_thr:
            signal = SignalType.SELL
            reason = f"Düşük kredi skoru ({score:.0f} ≤ {sell_thr}): Tahvil SAT"
            conf   = min(0.95, 1 - score / 850)
        else:
            signal = SignalType.NEUTRAL
            reason = f"Nötr kredi skoru ({score:.0f})"
            conf   = 0.5

        self._record_signal(symbol, signal, reason, conf)
        return signal


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 6: RİSK YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════

class RiskManager:
    """
    Kurumsal risk yöneticisi.
    - Pozisyon büyüklüğü belirleme (Kelly/Fixed Fractional/Volatility Parity)
    - Stop-loss ve take-profit otomatik seviyeleri
    - Portföy konsantrasyonu limitleri
    - Drawdown kontrolleri
    - VaR tabanlı pozisyon kısıtları
    """

    def __init__(self,
                 max_position_pct     : float = MAX_POSITION_PCT,
                 max_drawdown_pct     : float = 0.20,
                 max_sector_exposure  : float = 0.35,
                 stop_loss_pct        : float = 0.05,
                 take_profit_pct      : float = 0.10,
                 daily_loss_limit_pct : float = 0.03):

        self.max_position_pct    = max_position_pct
        self.max_drawdown_pct    = max_drawdown_pct
        self.max_sector_exposure = max_sector_exposure
        self.stop_loss_pct       = stop_loss_pct
        self.take_profit_pct     = take_profit_pct
        self.daily_loss_limit    = daily_loss_limit_pct
        self._risk_events        : List[Dict] = []

    def calculate_position_size(self,
                                 portfolio_value : float,
                                 signal_strength : float,
                                 price           : float,
                                 volatility_daily: float = 0.015,
                                 method          : str   = "fixed_fractional"
                                 ) -> int:
        """
        Pozisyon büyüklüğü belirle.

        Methods:
          - fixed_fractional : Portföyün sabit bir yüzdesi
          - kelly             : Kelly Kriteri
          - vol_parity        : Volatilite Parite
        """
        if price <= 0 or portfolio_value <= 0:
            return 0

        if method == "fixed_fractional":
            max_capital  = portfolio_value * self.max_position_pct * signal_strength
            shares       = int(max_capital / price)

        elif method == "kelly":
            # Basit Kelly: f = (bp - q) / b
            b            = self.take_profit_pct / self.stop_loss_pct
            p            = 0.5 + signal_strength * 0.2   # tahmini win rate
            q            = 1 - p
            kelly_f      = max(0, (b * p - q) / b)
            half_kelly   = kelly_f * 0.5   # Half-Kelly daha güvenli
            max_capital  = portfolio_value * min(half_kelly, self.max_position_pct)
            shares       = int(max_capital / price)

        elif method == "vol_parity":
            # Volatilite paritesi: daha az riskli enstrümana daha fazla yer
            target_vol   = 0.01   # günlük %1 hedef
            if volatility_daily > 0:
                weight   = min(target_vol / volatility_daily, self.max_position_pct)
            else:
                weight   = self.max_position_pct
            max_capital  = portfolio_value * weight
            shares       = int(max_capital / price)

        else:
            shares = int((portfolio_value * 0.05) / price)

        return max(0, shares)

    def compute_stop_loss(self, entry_price: float, side: PositionSide,
                           atr: Optional[float] = None) -> float:
        if atr is not None:
            mult = 2.5   # ATR çarpanı
            if side == PositionSide.LONG:
                return entry_price - mult * atr
            else:
                return entry_price + mult * atr
        else:
            if side == PositionSide.LONG:
                return entry_price * (1 - self.stop_loss_pct)
            else:
                return entry_price * (1 + self.stop_loss_pct)

    def compute_take_profit(self, entry_price: float, side: PositionSide,
                             rr_ratio: float = 2.0) -> float:
        """Ödül/Risk oranına göre hedef fiyat."""
        tp_pct = self.stop_loss_pct * rr_ratio
        if side == PositionSide.LONG:
            return entry_price * (1 + tp_pct)
        else:
            return entry_price * (1 - tp_pct)

    def check_order(self, order: Order, portfolio) -> Tuple[bool, str]:
        """Emir risk kontrolü. True = geçerli, False = reddedildi."""
        # Portföy değeri kontrolü
        pv = portfolio.total_value
        if pv <= 0:
            return False, "Portföy değeri sıfır"

        # Likidite kontrolü
        required_cash = order.quantity * (order.price or portfolio.last_price(order.symbol))
        if required_cash > portfolio.cash * 1.05:   # %5 tolerans
            return False, f"Yetersiz nakit: {portfolio.cash:.0f} < {required_cash:.0f}"

        # Maksimum pozisyon kontrolü
        pos_value = required_cash
        if pos_value / pv > self.max_position_pct:
            return False, f"Pozisyon limiti aşıldı: {pos_value/pv:.1%} > {self.max_position_pct:.1%}"

        return True, "OK"

    def check_drawdown(self, portfolio) -> Tuple[bool, str]:
        """Maksimum drawdown kontrolü."""
        dd = portfolio.max_drawdown
        if dd > self.max_drawdown_pct:
            self._risk_events.append({
                "type"     : "MAX_DRAWDOWN_BREACHED",
                "timestamp": datetime.datetime.now().isoformat(),
                "value"    : dd,
                "limit"    : self.max_drawdown_pct,
            })
            return False, f"Maks. Drawdown aşıldı: {dd:.1%} > {self.max_drawdown_pct:.1%}"
        return True, "OK"

    @property
    def risk_event_count(self) -> int:
        return len(self._risk_events)


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 7: PORTFÖY YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════

class Portfolio:
    """
    Kağıt trading portföy yöneticisi.
    Gerçek zamanlı (simüle) PnL, pozisyon ve nakit takibi.
    """

    def __init__(self,
                 initial_cash  : float = 1_000_000.0,
                 currency      : str   = "TRY",
                 portfolio_name: str   = "ProQuant Kağıt Portföy"):

        self.initial_cash    = initial_cash
        self.cash            = initial_cash
        self.currency        = currency
        self.name            = portfolio_name
        self.created_at      = datetime.datetime.now()

        self._positions      : Dict[str, Position] = {}
        self._closed_positions: List[Dict]         = []
        self._trades         : List[Trade]          = []
        self._orders         : List[Order]          = []
        self._equity_curve   : List[Tuple[datetime.datetime, float]] = []
        self._peak_equity    : float                = initial_cash
        self._prices         : Dict[str, float]     = {}

        # Günlük P&L tracking
        self._daily_pnl      : List[float] = []
        self._session_start_value: float   = initial_cash

    # ── Temel Erişimciler ────────────────────────────────────────────

    def last_price(self, symbol: str) -> float:
        return self._prices.get(symbol, 0.0)

    def update_price(self, symbol: str, price: float) -> None:
        """Anlık fiyatı güncelle, pozisyon mark-to-market yap."""
        self._prices[symbol] = price
        if symbol in self._positions:
            self._positions[symbol].update_mark(price)

    @property
    def positions(self) -> Dict[str, Position]:
        return self._positions.copy()

    @property
    def open_positions(self) -> Dict[str, Position]:
        return {s: p for s, p in self._positions.items() if p.quantity > 0}

    @property
    def unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self._positions.values())

    @property
    def realized_pnl(self) -> float:
        return sum(t.pnl for t in self._trades if t.pnl != 0)

    @property
    def total_value(self) -> float:
        market_val = sum(p.market_value for p in self._positions.values())
        return self.cash + market_val

    @property
    def equity(self) -> float:
        return self.total_value

    @property
    def margin_used(self) -> float:
        return sum(p.cost_basis for p in self._positions.values())

    @property
    def free_margin(self) -> float:
        return self.equity - self.margin_used

    @property
    def total_return_pct(self) -> float:
        if self.initial_cash == 0:
            return 0.0
        return (self.equity - self.initial_cash) / self.initial_cash * 100

    @property
    def max_drawdown(self) -> float:
        if not self._equity_curve:
            return 0.0
        peak    = self._equity_curve[0][1]
        max_dd  = 0.0
        for _, equity in self._equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @property
    def sharpe_ratio(self) -> float:
        if len(self._daily_pnl) < 2:
            return 0.0
        mean_r = sum(self._daily_pnl) / len(self._daily_pnl)
        std_r  = statistics.stdev(self._daily_pnl) if len(self._daily_pnl) > 1 else 1e-9
        rf_day = RISK_FREE_RATE_DEFAULT / TRADING_DAYS_PER_YEAR
        return (mean_r - rf_day) / std_r * math.sqrt(TRADING_DAYS_PER_YEAR) if std_r > 0 else 0.0

    @property
    def win_rate(self) -> float:
        closed_pnls = [t.pnl for t in self._trades if t.pnl != 0]
        if not closed_pnls:
            return 0.0
        wins = sum(1 for p in closed_pnls if p > 0)
        return wins / len(closed_pnls)

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(p for p in (t.pnl for t in self._trades) if p > 0)
        gross_loss   = abs(sum(p for p in (t.pnl for t in self._trades) if p < 0))
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    def record_equity(self) -> None:
        """Equity curve'e nokta ekle."""
        ts = datetime.datetime.now()
        eq = self.equity
        self._equity_curve.append((ts, eq))
        if eq > self._peak_equity:
            self._peak_equity = eq

    def record_daily_return(self) -> None:
        curr_val      = self.equity
        prev_val      = self._session_start_value
        daily_return  = (curr_val - prev_val) / prev_val if prev_val > 0 else 0.0
        self._daily_pnl.append(daily_return)
        self._session_start_value = curr_val

    # ── İşlem Motorları ──────────────────────────────────────────────

    def open_position(self, order: Order, fill_price: float,
                       filled_qty: int) -> Optional[Trade]:
        """Yeni pozisyon aç veya mevcut pozisyonu artır."""

        trade = Trade(
            trade_id    = str(uuid.uuid4())[:8].upper(),
            order_id    = order.order_id,
            symbol      = order.symbol,
            side        = order.side,
            quantity    = filled_qty,
            price       = fill_price,
            commission  = order.commission,
            slippage    = fill_price - (order.price or fill_price),
            timestamp   = datetime.datetime.now(),
            strategy_tag= order.strategy_tag,
        )

        cost = filled_qty * fill_price + order.commission
        if self.cash < cost:
            logger.warning(f"Yetersiz nakit: {self.cash:.0f} < {cost:.0f}")
            return None

        self.cash -= cost

        if order.symbol in self._positions:
            pos = self._positions[order.symbol]
            if order.side == OrderSide.BUY and pos.side == PositionSide.LONG:
                # Ortalama maliyet güncelle
                total_cost = pos.avg_cost * pos.quantity + fill_price * filled_qty
                pos.quantity += filled_qty
                pos.avg_cost  = total_cost / pos.quantity
            elif order.side == OrderSide.SELL and pos.side == PositionSide.LONG:
                # Uzun pozisyonu kıs veya kapat
                closed = min(pos.quantity, filled_qty)
                trade.pnl = (fill_price - pos.avg_cost) * closed - order.commission
                pos.quantity -= closed
                pos.realized_pnl += trade.pnl
                if pos.quantity == 0:
                    self._closed_positions.append({
                        "symbol"     : pos.symbol,
                        "entry_price": pos.avg_cost,
                        "exit_price" : fill_price,
                        "quantity"   : closed,
                        "pnl"        : trade.pnl,
                        "duration"   : (datetime.datetime.now() - pos.opened_at).seconds,
                    })
                    del self._positions[order.symbol]
        else:
            side = PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT
            self._positions[order.symbol] = Position(
                symbol      = order.symbol,
                side        = side,
                quantity    = filled_qty,
                avg_cost    = fill_price,
                strategy_tag= order.strategy_tag,
            )

        self._trades.append(trade)
        self.cash += filled_qty * fill_price if order.side == OrderSide.SELL else 0
        self.record_equity()
        return trade

    def get_performance_summary(self) -> Dict[str, Any]:
        """Detaylı performans özeti."""
        closed_pnls = [t.pnl for t in self._trades if t.pnl != 0]

        return {
            "portfolio_name"     : self.name,
            "initial_cash"       : self.initial_cash,
            "current_equity"     : round(self.equity, 2),
            "cash"               : round(self.cash, 2),
            "unrealized_pnl"     : round(self.unrealized_pnl, 2),
            "realized_pnl"       : round(self.realized_pnl, 2),
            "total_return_pct"   : round(self.total_return_pct, 4),
            "max_drawdown"       : round(self.max_drawdown * 100, 4),
            "sharpe_ratio"       : round(self.sharpe_ratio, 4),
            "win_rate"           : round(self.win_rate * 100, 2),
            "profit_factor"      : round(self.profit_factor, 4),
            "total_trades"       : len(self._trades),
            "open_positions"     : len(self.open_positions),
            "avg_trade_pnl"      : round(sum(closed_pnls) / len(closed_pnls), 2) if closed_pnls else 0,
            "best_trade"         : round(max(closed_pnls), 2) if closed_pnls else 0,
            "worst_trade"        : round(min(closed_pnls), 2) if closed_pnls else 0,
            "equity_curve_points": len(self._equity_curve),
            "created_at"         : self.created_at.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 8: SENTETİK PİYASA VERİSİ ÜRETECİ
# ═══════════════════════════════════════════════════════════════════════════════

class SyntheticMarketEngine:
    """
    Gerçekçi sentetik fiyat serisi üreteci.
    Geometric Brownian Motion + Jump Diffusion + Mean Reversion süreçleri.
    """

    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        self._instruments: Dict[str, Instrument] = {}
        self._price_history: Dict[str, List[OHLCV]] = {}
        self._current_prices: Dict[str, float]      = {}
        self._order_books   : Dict[str, OrderBook]  = {}
        self._tick_buffers  : Dict[str, Deque[Tick]] = {}

    def register_instrument(self, instrument: Instrument,
                              initial_price: float) -> None:
        sym = instrument.symbol
        self._instruments[sym]    = instrument
        self._current_prices[sym] = initial_price
        self._price_history[sym]  = []
        self._order_books[sym]    = OrderBook(sym)
        self._tick_buffers[sym]   = collections.deque(maxlen=1000)

    def _gbm_step(self, price: float, mu: float = 0.0002,
                   sigma: float = 0.015, dt: float = 1.0) -> float:
        """Geometric Brownian Motion adımı."""
        z   = random.gauss(0, 1)
        new = price * math.exp((mu - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z)
        return max(new, 0.01)

    def _jump_diffusion_step(self, price: float,
                              mu: float = 0.0002, sigma: float = 0.015,
                              jump_intensity: float = 0.02,
                              jump_mean: float = -0.01,
                              jump_sigma: float = 0.05) -> float:
        """Merton Jump-Diffusion modeli."""
        gbm_component = self._gbm_step(price, mu, sigma)
        # Poisson atlama
        if random.random() < jump_intensity:
            jump_size = math.exp(random.gauss(jump_mean, jump_sigma)) - 1
            return gbm_component * (1 + jump_size)
        return gbm_component

    def _mean_reversion_step(self, price: float, long_run_mean: float,
                              kappa: float = 0.05, sigma: float = 0.012) -> float:
        """Ornstein-Uhlenbeck ortalamaya dönüş süreci."""
        drift    = kappa * (long_run_mean - price)
        diffusion= sigma * math.sqrt(price) * random.gauss(0, 1)
        return max(price + drift + diffusion, 0.01)

    def generate_ohlcv_bar(self, symbol: str, process: str = "gbm") -> Optional[OHLCV]:
        if symbol not in self._current_prices:
            return None

        price = self._current_prices[symbol]

        # İntrabar simülasyonu (1 günlük mum için ~20 tick)
        ticks = [price]
        for _ in range(20):
            if process == "jump_diffusion":
                t = self._jump_diffusion_step(ticks[-1])
            elif process == "mean_reversion":
                t = self._mean_reversion_step(ticks[-1], price)
            else:
                t = self._gbm_step(ticks[-1])
            ticks.append(t)

        o = ticks[0]
        h = max(ticks)
        l = min(ticks)
        c = ticks[-1]
        v = int(random.lognormvariate(10, 1))

        bar = OHLCV(
            timestamp = datetime.datetime.now(),
            open      = round(o, 4),
            high      = round(h, 4),
            low       = round(l, 4),
            close     = round(c, 4),
            volume    = v,
        )

        self._current_prices[symbol] = c
        self._price_history[symbol].append(bar)
        self._order_books[symbol].update(c)

        # Tick kayıt
        tick = Tick(
            timestamp = bar.timestamp,
            symbol    = symbol,
            bid       = round(c * 0.9995, 4),
            ask       = round(c * 1.0005, 4),
            last      = round(c, 4),
            volume    = v,
        )
        self._tick_buffers[symbol].append(tick)

        return bar

    def generate_history(self, symbol: str, days: int = 252,
                          process: str = "gbm") -> List[OHLCV]:
        """Geçmiş veri serisi üret."""
        bars = []
        for _ in range(days):
            bar = self.generate_ohlcv_bar(symbol, process)
            if bar:
                bars.append(bar)
        return bars

    def get_bars(self, symbol: str, count: int = 100) -> List[OHLCV]:
        history = self._price_history.get(symbol, [])
        return history[-count:] if len(history) >= count else history

    def get_current_tick(self, symbol: str) -> Optional[Tick]:
        buf = self._tick_buffers.get(symbol)
        if buf:
            return buf[-1]
        return None

    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        return self._order_books.get(symbol)


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 9: BACKTEST MOTORU
# ═══════════════════════════════════════════════════════════════════════════════

class BacktestResult(NamedTuple):
    """Backtest sonuç nesnesi."""
    strategy_name     : str
    symbol            : str
    start_date        : datetime.datetime
    end_date          : datetime.datetime
    initial_capital   : float
    final_equity      : float
    total_return_pct  : float
    annualized_return : float
    max_drawdown      : float
    sharpe_ratio      : float
    win_rate          : float
    profit_factor     : float
    total_trades      : int
    avg_hold_days     : float
    equity_curve      : List[float]
    trade_log         : List[Dict]


class EventDrivenBacktestEngine:
    """
    Olay Güdümlü Backtest Motoru.
    Her mum çubuğu bir "olay" olarak işlenir.
    Strateji → Sinyal → Risk Yönetimi → Emir → Dolum pipeline'ı.
    """

    def __init__(self,
                 portfolio       : Portfolio,
                 strategy        : BaseStrategy,
                 commission_model: ICommissionModel,
                 slippage_model  : ISlippageModel,
                 risk_manager    : RiskManager):

        self.portfolio        = portfolio
        self.strategy         = strategy
        self.commission_model = commission_model
        self.slippage_model   = slippage_model
        self.risk_manager     = risk_manager
        self._event_log       : List[Dict] = []

    def _create_market_order(self, symbol: str, side: OrderSide,
                              quantity: int, tag: str = "") -> Order:
        return Order(
            order_id     = str(uuid.uuid4())[:8].upper(),
            symbol       = symbol,
            side         = side,
            order_type   = OrderType.MARKET,
            quantity     = quantity,
            strategy_tag = tag,
        )

    def _process_signal(self, symbol: str, signal: SignalType,
                         bar: OHLCV) -> Optional[Order]:
        """Sinyali emirlerine çevir."""
        pv = self.portfolio.equity
        if pv <= 0:
            return None

        pos = self.portfolio.open_positions.get(symbol)

        # Güç katsayısı
        strength_map = {
            SignalType.STRONG_BUY : 1.0,
            SignalType.BUY        : 0.6,
            SignalType.NEUTRAL    : 0.0,
            SignalType.SELL       : 0.6,
            SignalType.STRONG_SELL: 1.0,
        }
        strength = strength_map.get(signal, 0.0)

        if signal in (SignalType.BUY, SignalType.STRONG_BUY):
            if pos and pos.side == PositionSide.LONG:
                return None   # Zaten uzun pozisyon

            qty = self.risk_manager.calculate_position_size(
                pv, strength, bar.close, method="fixed_fractional"
            )
            if qty <= 0:
                return None

            order = self._create_market_order(
                symbol, OrderSide.BUY, qty, self.strategy.name
            )
            return order

        elif signal in (SignalType.SELL, SignalType.STRONG_SELL):
            if not pos or pos.quantity == 0:
                return None   # Kapatılacak pozisyon yok

            close_qty = pos.quantity if signal == SignalType.STRONG_SELL else pos.quantity // 2
            if close_qty <= 0:
                return None

            order = self._create_market_order(
                symbol, OrderSide.SELL, close_qty, self.strategy.name
            )
            return order

        return None

    def _fill_order(self, order: Order, bar: OHLCV,
                     order_book: Optional[OrderBook] = None) -> bool:
        """Emiri doldur."""
        if order_book:
            fill_price, filled = order_book.simulate_fill(order)
            if filled == 0:
                order.status = OrderStatus.CANCELLED
                return False
        else:
            # Basit dolum: mum ortası fiyatı + slipaj
            base_price = (bar.open + bar.close) / 2
            fill_price = self.slippage_model.calculate(
                order, base_price, bar.volume
            )
            filled     = order.quantity

        commission = self.commission_model.calculate(order, fill_price)
        order.filled_qty      = filled
        order.avg_fill_price  = fill_price
        order.commission      = commission
        order.status          = OrderStatus.FILLED
        order.filled_at       = datetime.datetime.now()

        # Portföya uygula
        trade = self.portfolio.open_position(order, fill_price, filled)
        return trade is not None

    def run(self, symbol: str, bars: List[OHLCV],
             order_book: Optional[OrderBook] = None) -> BacktestResult:
        """
        Ana backtest döngüsü.
        Her mum için: Sinyal → Emir → Dolum → PnL → Equity kayıt
        """
        self.strategy.initialize([symbol])
        start_date   = bars[0].timestamp if bars else datetime.datetime.now()
        history      = []

        for i, bar in enumerate(bars):
            self.portfolio.update_price(symbol, bar.close)

            # Stop-loss / Take-profit kontrol (açık pozisyon varsa)
            pos = self.portfolio.open_positions.get(symbol)
            if pos and pos.stop_loss and pos.side == PositionSide.LONG:
                if bar.low <= pos.stop_loss:
                    sl_order = self._create_market_order(
                        symbol, OrderSide.SELL, pos.quantity, "STOP_LOSS"
                    )
                    sl_order.price = pos.stop_loss
                    self._fill_order(sl_order, bar, order_book)
                    self._event_log.append({
                        "type": "STOP_LOSS_HIT", "bar": i,
                        "price": pos.stop_loss, "symbol": symbol
                    })
                    continue

            # Sinyal üret (en az 30 mum gerekli)
            if i >= 30:
                recent_bars = bars[max(0, i-100):i+1]
                signal = self.strategy.generate_signal(symbol, recent_bars)

                # Emir oluştur
                order = self._process_signal(symbol, signal, bar)
                if order:
                    # Risk kontrolü
                    ok, reason = self.risk_manager.check_order(order, self.portfolio)
                    if ok:
                        filled = self._fill_order(order, bar, order_book)
                        if filled:
                            self._event_log.append({
                                "type"  : f"ORDER_{order.side.value}",
                                "bar"   : i,
                                "price" : bar.close,
                                "qty"   : order.filled_qty,
                                "signal": signal.name,
                            })
                    else:
                        self._event_log.append({
                            "type"  : "ORDER_REJECTED",
                            "bar"   : i,
                            "reason": reason,
                        })

            self.portfolio.record_equity()
            history.append(self.portfolio.equity)

        # Sonuç oluştur
        end_date  = bars[-1].timestamp if bars else datetime.datetime.now()
        n_years   = max((end_date - start_date).days / 365, 1/252)
        final_eq  = self.portfolio.equity
        init_cap  = self.portfolio.initial_cash
        total_ret = (final_eq - init_cap) / init_cap
        ann_ret   = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0

        return BacktestResult(
            strategy_name    = self.strategy.name,
            symbol           = symbol,
            start_date       = start_date,
            end_date         = end_date,
            initial_capital  = init_cap,
            final_equity     = round(final_eq, 2),
            total_return_pct = round(total_ret * 100, 4),
            annualized_return= round(ann_ret * 100, 4),
            max_drawdown     = round(self.portfolio.max_drawdown * 100, 4),
            sharpe_ratio     = round(self.portfolio.sharpe_ratio, 4),
            win_rate         = round(self.portfolio.win_rate * 100, 2),
            profit_factor    = round(self.portfolio.profit_factor, 4),
            total_trades     = len(self.portfolio._trades),
            avg_hold_days    = 0.0,
            equity_curve     = history,
            trade_log        = [t.to_dict() for t in self.portfolio._trades],
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 10: ÇOKLU STRATEJİ KARŞILAŞTIRICI
# ═══════════════════════════════════════════════════════════════════════════════

class StrategyBenchmark:
    """
    Birden fazla stratejiyi aynı veri setinde çalıştırıp
    karşılaştırmalı performans raporu çıkarır.
    """

    def __init__(self, initial_capital: float = 1_000_000.0):
        self.initial_capital = initial_capital
        self._results        : List[BacktestResult] = []

    def add_strategy(self, strategy: BaseStrategy) -> "StrategyBenchmark":
        self._strategies = getattr(self, "_strategies", [])
        self._strategies.append(strategy)
        return self

    def run_all(self, symbol: str, bars: List[OHLCV],
                 commission_model: ICommissionModel = None,
                 slippage_model  : ISlippageModel   = None) -> List[BacktestResult]:
        """Tüm stratejileri çalıştır."""
        strategies = getattr(self, "_strategies", [])
        if not strategies:
            return []

        commission = commission_model or PercentageCommissionModel()
        slippage   = slippage_model   or VolumeImpactSlippageModel()
        risk_mgr   = RiskManager()

        self._results = []
        for strat in strategies:
            port    = Portfolio(initial_cash=self.initial_capital,
                                portfolio_name=f"{strat.name} Portföy")
            engine  = EventDrivenBacktestEngine(port, strat, commission,
                                                 slippage, risk_mgr)
            result  = engine.run(symbol, bars.copy())
            self._results.append(result)

        return self._results

    def leaderboard(self) -> List[Dict[str, Any]]:
        """Performans sıralaması."""
        if not self._results:
            return []

        scored = []
        for r in self._results:
            # Bileşik skor: Sharpe ağırlıklı
            score = (
                r.sharpe_ratio * 0.35 +
                r.total_return_pct / 100 * 0.25 +
                r.win_rate / 100 * 0.20 +
                (1 / max(r.max_drawdown, 0.1)) * 0.10 +
                r.profit_factor * 0.10
            )
            scored.append({
                "strategy"        : r.strategy_name,
                "score"           : round(score, 4),
                "total_return"    : f"{r.total_return_pct:+.2f}%",
                "ann_return"      : f"{r.annualized_return:+.2f}%",
                "sharpe"          : round(r.sharpe_ratio, 3),
                "max_drawdown"    : f"{r.max_drawdown:.2f}%",
                "win_rate"        : f"{r.win_rate:.1f}%",
                "profit_factor"   : round(r.profit_factor, 3),
                "total_trades"    : r.total_trades,
                "final_equity"    : f"{r.final_equity:,.0f}",
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        for i, row in enumerate(scored):
            row["rank"] = i + 1
        return scored


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 11: ARAÇLAR & YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

class TechnicalIndicators:
    """Teknik indikatör kütüphanesi."""

    @staticmethod
    def sma(values: List[float], period: int) -> List[float]:
        out = []
        for i in range(len(values)):
            if i < period - 1:
                out.append(float("nan"))
            else:
                out.append(sum(values[i-period+1:i+1]) / period)
        return out

    @staticmethod
    def ema(values: List[float], period: int) -> List[float]:
        if not values:
            return []
        k   = 2 / (period + 1)
        out = [values[0]]
        for v in values[1:]:
            out.append(v * k + out[-1] * (1 - k))
        return out

    @staticmethod
    def rsi(values: List[float], period: int = 14) -> List[float]:
        out = [float("nan")] * period
        for i in range(period, len(values)):
            window = values[i-period:i]
            gains  = [max(window[j] - window[j-1], 0) for j in range(1, len(window))]
            losses = [max(window[j-1] - window[j], 0) for j in range(1, len(window))]
            ag = sum(gains) / (period - 1) if gains else 0
            al = sum(losses) / (period - 1)  if losses else 1e-9
            rs = ag / al
            out.append(100 - 100 / (1 + rs))
        return out

    @staticmethod
    def bollinger_bands(values: List[float], period: int = 20,
                         num_std: float = 2.0
                         ) -> Tuple[List[float], List[float], List[float]]:
        mid   = TechnicalIndicators.sma(values, period)
        upper = []
        lower = []
        for i, m in enumerate(mid):
            if math.isnan(m) or i < period - 1:
                upper.append(float("nan"))
                lower.append(float("nan"))
            else:
                window = values[i-period+1:i+1]
                std    = statistics.stdev(window)
                upper.append(m + num_std * std)
                lower.append(m - num_std * std)
        return mid, upper, lower

    @staticmethod
    def atr(bars: List[OHLCV], period: int = 14) -> List[float]:
        trs  = []
        for i, bar in enumerate(bars):
            if i == 0:
                trs.append(bar.high - bar.low)
            else:
                prev_close = bars[i-1].close
                tr = max(bar.high - bar.low,
                         abs(bar.high - prev_close),
                         abs(bar.low  - prev_close))
                trs.append(tr)
        # Wilder smoothing
        atrs  = [float("nan")] * (period - 1)
        if len(trs) >= period:
            atrs.append(sum(trs[:period]) / period)
            for i in range(period, len(trs)):
                atrs.append((atrs[-1] * (period - 1) + trs[i]) / period)
        return atrs

    @staticmethod
    def macd(values: List[float], fast: int = 12, slow: int = 26,
              signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        fast_e  = TechnicalIndicators.ema(values, fast)
        slow_e  = TechnicalIndicators.ema(values, slow)
        macd_l  = [f - s for f, s in zip(fast_e, slow_e)]
        sig_l   = TechnicalIndicators.ema(macd_l, signal)
        hist    = [m - s for m, s in zip(macd_l, sig_l)]
        return macd_l, sig_l, hist

    @staticmethod
    def vwap(bars: List[OHLCV]) -> List[float]:
        cum_vol = 0
        cum_pv  = 0
        out     = []
        for bar in bars:
            cum_pv  += bar.typical_price * bar.volume
            cum_vol += bar.volume
            out.append(cum_pv / cum_vol if cum_vol > 0 else bar.close)
        return out

    @staticmethod
    def stochastic(bars: List[OHLCV], k_period: int = 14,
                    d_period: int = 3) -> Tuple[List[float], List[float]]:
        k_vals = []
        for i in range(len(bars)):
            if i < k_period - 1:
                k_vals.append(float("nan"))
            else:
                window = bars[i-k_period+1:i+1]
                low14  = min(b.low  for b in window)
                high14 = max(b.high for b in window)
                if high14 - low14 == 0:
                    k_vals.append(50.0)
                else:
                    k = (bars[i].close - low14) / (high14 - low14) * 100
                    k_vals.append(k)
        d_vals = TechnicalIndicators.sma([v for v in k_vals if not math.isnan(v)], d_period)
        return k_vals, d_vals


class PerformanceMetrics:
    """Portföy performans metrik hesaplayıcı."""

    @staticmethod
    def calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        if max_drawdown == 0:
            return float("inf")
        return annualized_return / max_drawdown

    @staticmethod
    def sortino_ratio(returns: List[float], target: float = 0.0,
                       periods_per_year: int = 252) -> float:
        downside = [min(r - target, 0) for r in returns]
        ds_std   = math.sqrt(sum(d**2 for d in downside) / max(len(downside), 1))
        if ds_std == 0:
            return float("inf")
        avg_excess = sum(r - target for r in returns) / max(len(returns), 1)
        return avg_excess / ds_std * math.sqrt(periods_per_year)

    @staticmethod
    def var_historical(pnl_series: List[float], confidence: float = 0.99) -> float:
        sorted_pnl = sorted(pnl_series)
        idx = int((1 - confidence) * len(sorted_pnl))
        return -sorted_pnl[max(0, idx)]

    @staticmethod
    def cvar(pnl_series: List[float], confidence: float = 0.99) -> float:
        var = PerformanceMetrics.var_historical(pnl_series, confidence)
        tail = [p for p in pnl_series if p < -var]
        if not tail:
            return var
        return -sum(tail) / len(tail)

    @staticmethod
    def ulcer_index(equity_curve: List[float]) -> float:
        if not equity_curve:
            return 0.0
        peak    = equity_curve[0]
        drawdowns = []
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            drawdowns.append(dd)
        return math.sqrt(sum(d**2 for d in drawdowns) / len(drawdowns))

    @staticmethod
    def omega_ratio(returns: List[float], threshold: float = 0.0) -> float:
        gains  = sum(max(r - threshold, 0) for r in returns)
        losses = sum(max(threshold - r, 0) for r in returns)
        if losses == 0:
            return float("inf")
        return gains / losses


# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLÜM 12: ANA ARAÇ (AlgoTradingSimulator)
# ═══════════════════════════════════════════════════════════════════════════════

class AlgoTradingSimulator:
    """
    Üst düzey simülatör bağlama noktası.
    Streamlit UI'ından kolayca çağrılabilir.
    """

    ALL_INSTRUMENTS = [
        Instrument("THYAO", "Türk Hava Yolları", AssetClass.EQUITY,   sector="Havacılık"),
        Instrument("GARAN", "Garanti Bankası",   AssetClass.EQUITY,   sector="Bankacılık"),
        Instrument("SISE",  "Şişe Cam",          AssetClass.EQUITY,   sector="Sanayi"),
        Instrument("EREGL", "Ereğli Demir",      AssetClass.EQUITY,   sector="Demir Çelik"),
        Instrument("AKBNK", "Akbank",            AssetClass.EQUITY,   sector="Bankacılık"),
        Instrument("TUPRS", "Tüpraş",            AssetClass.EQUITY,   sector="Enerji"),
        Instrument("KCHOL", "Koç Holding",       AssetClass.EQUITY,   sector="Holding"),
        Instrument("BIMAS", "BİM Mağazaları",    AssetClass.EQUITY,   sector="Perakende"),
        Instrument("TCMB10Y","TCMB 10Y Tahvil",  AssetClass.FIXED_INCOME, lot_size=1000),
        Instrument("XAUUSD","Altın (USD)",        AssetClass.COMMODITY),
    ]

    STRATEGY_MAP = {
        "RSI Momentum"         : RSIMomentumStrategy,
        "Bollinger Mean Rev."  : BollingerBandsMeanReversionStrategy,
        "EMA Crossover"        : EMAcrossoverStrategy,
        "MACD"                 : MACDStrategy,
        "ML Kredi Güdümlü"     : MLGuidedStrategy,
    }

    def __init__(self, initial_capital: float = 1_000_000.0, seed: int = 42):
        self.initial_capital = initial_capital
        self.market_engine   = SyntheticMarketEngine(seed=seed)
        self._setup_market()

    def _setup_market(self) -> None:
        prices = {
            "THYAO": 285.0, "GARAN": 78.5,  "SISE": 45.2,
            "EREGL": 52.0,  "AKBNK": 65.0,  "TUPRS": 192.0,
            "KCHOL": 130.0, "BIMAS": 420.0, "TCMB10Y": 98.5,
            "XAUUSD": 1985.0,
        }
        for inst in self.ALL_INSTRUMENTS:
            self.market_engine.register_instrument(inst, prices.get(inst.symbol, 100.0))
            self.market_engine.generate_history(inst.symbol, days=300)

    def run_backtest(self, strategy_name: str, symbol: str,
                      initial_capital: float = None,
                      commission_type: str   = "percentage",
                      slippage_type  : str   = "volume") -> BacktestResult:

        cap      = initial_capital or self.initial_capital
        strategy = self._build_strategy(strategy_name)
        bars     = self.market_engine.get_bars(symbol, 250)

        commission = self._build_commission(commission_type)
        slippage   = self._build_slippage(slippage_type)
        risk_mgr   = RiskManager()
        portfolio  = Portfolio(initial_cash=cap,
                               portfolio_name=f"{strategy_name} — {symbol}")
        engine     = EventDrivenBacktestEngine(portfolio, strategy, commission,
                                               slippage, risk_mgr)
        return engine.run(symbol, bars)

    def run_benchmark(self, symbols: List[str] = None,
                       strategy_names: List[str] = None) -> Dict[str, List[Dict]]:
        syms  = symbols or ["THYAO", "GARAN"]
        strats= strategy_names or list(self.STRATEGY_MAP.keys())

        results = {}
        for sym in syms:
            bars      = self.market_engine.get_bars(sym, 250)
            benchmark = StrategyBenchmark(self.initial_capital)
            for sn in strats:
                benchmark.add_strategy(self._build_strategy(sn))
            benchmark.run_all(sym, bars)
            results[sym] = benchmark.leaderboard()
        return results

    def _build_strategy(self, name: str) -> BaseStrategy:
        cls = self.STRATEGY_MAP.get(name, RSIMomentumStrategy)
        return cls()

    def _build_commission(self, ctype: str) -> ICommissionModel:
        if ctype == "fixed":
            return FixedCommissionModel(9.90)
        elif ctype == "tiered":
            return TieredCommissionModel()
        return PercentageCommissionModel()

    def _build_slippage(self, stype: str) -> ISlippageModel:
        if stype == "fixed":
            return FixedSlippageModel(0.01)
        elif stype == "almgren":
            return MarketImpactSlippageModel()
        return VolumeImpactSlippageModel()

    def get_live_market_snapshot(self) -> List[Dict]:
        """Anlık piyasa fiyatları özeti."""
        snapshot = []
        for inst in self.ALL_INSTRUMENTS:
            sym  = inst.symbol
            # Yeni bir bar üret (fiyatı günceller)
            bar  = self.market_engine.generate_ohlcv_bar(sym)
            book = self.market_engine.get_order_book(sym)
            if bar and book:
                snapshot.append({
                    "symbol"     : sym,
                    "name"       : inst.name,
                    "sector"     : inst.sector,
                    "last"       : round(bar.close, 4),
                    "change_pct" : round((bar.close - bar.open) / bar.open * 100, 2),
                    "volume"     : bar.volume,
                    "bid"        : book.best_bid,
                    "ask"        : book.best_ask,
                    "spread_pct" : round(book.spread / book.mid_price * 100, 4) if book.mid_price else 0,
                    "imbalance"  : round(book.order_imbalance, 4),
                    "asset_class": inst.asset_class.value,
                })
        return snapshot

    def compute_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """Seçili sembol için teknik indikatörler."""
        bars   = self.market_engine.get_bars(symbol, 200)
        closes = [b.close for b in bars]
        ti     = TechnicalIndicators()

        rsi_vals = ti.rsi(closes, 14)
        macd_l, sig_l, hist = ti.macd(closes)
        mid_bb, up_bb, lo_bb = ti.bollinger_bands(closes)
        atr_vals = ti.atr(bars, 14)
        vwap_vals= ti.vwap(bars)

        # Son geçerli değerler
        def last_valid(lst):
            for v in reversed(lst):
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    return round(v, 4)
            return None

        return {
            "symbol"  : symbol,
            "rsi"     : last_valid(rsi_vals),
            "macd"    : last_valid(macd_l),
            "macd_sig": last_valid(sig_l),
            "macd_hist":last_valid(hist),
            "bb_upper": last_valid(up_bb),
            "bb_mid"  : last_valid(mid_bb),
            "bb_lower": last_valid(lo_bb),
            "atr"     : last_valid(atr_vals),
            "vwap"    : last_valid(vwap_vals),
            "close"   : closes[-1] if closes else None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def get_simulator(initial_capital: float = 1_000_000.0) -> AlgoTradingSimulator:
    """Singleton benzeri erişim noktası."""
    return AlgoTradingSimulator(initial_capital=initial_capital)

def get_trading_bot(initial_capital: float = 1_000_000.0) -> AlgoTradingSimulator:
    """app.py entegrasyonu için alias."""
    return get_simulator(initial_capital)

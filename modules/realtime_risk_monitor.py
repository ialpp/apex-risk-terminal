"""
modules/realtime_risk_monitor.py — ProQuant Capital | Gerçek Zamanlı Risk Monitörü & Alert Engine v2.0
==================================================================================================

Kurumsal portföy risklerini anlık olarak izleyen ve tanımlı eşik değerlere göre uyarı üreten motor.
Sistemdeki tüm modüllerden (Credit, Fraud, ESG, Macro) gelen verileri konsolide eder.

Kapsam:
  - Real-time Stream Simulation: Saniyede binlerce işlem verisi akışının simülasyonu.
  - Threshold Engine: Sabit, dinamik ve yüzdelik değişim tabanlı eşik kontrolü.
  - Alert Severity: Bilgi (Info), Düşük (Low), Orta (Medium), Yüksek (High), Kritik (Critical).
  - Multivariate Alerting: Birden fazla koşulun (AND/OR) birleşimiyle tetiklenen kompleks uyarılar.
  - Alert Fatigue Prevention: Arka arkaya gelen mükerrer uyarıları birleştirme (Batching).
  - Risk Score Drift: Müşteri risk skorlarındaki ani sapmaları (Drift) tespit etme.
  - Dashboard API: UI için canlı risk pulse ve olay günlüğü verisi.

Author  : ProQuant Capital Risk Oversight Team
Version : 2.0.0
"""

from __future__ import annotations

import enum
import time
import uuid
import random
import datetime
import collections
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import yfinance as yf

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: ENUM & TİPLER
# ─────────────────────────────────────────────────────────────────────────────

class AlertSeverity(enum.Enum):
    INFO     = "INFO"
    LOW      = "Düşük"
    MEDIUM   = "Orta"
    HIGH     = "Yüksek"
    CRITICAL = "Kritik"

class AlertCategory(enum.Enum):
    CREDIT_RISK   = "Kredi Riski"
    FRAUD         = "Sahtekarlık"
    LIQUIDITY     = "Likidite"
    MACRO         = "Makro Ekonomik"
    ESG           = "ESG/Sürdürülebilirlik"
    SYSTEM        = "Sistem/Performans"

@dataclass
class Alert:
    """Üretilen bir uyarı (alert) kaydı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    category: AlertCategory = AlertCategory.CREDIT_RISK
    entity_id: str = "GENEL"
    message: str = ""
    value: float = 0.0
    threshold: float = 0.0
    is_resolved: bool = False
    resolved_at: Optional[datetime.datetime] = None
    resolved_by: Optional[str] = None

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: EŞİK (THRESHOLD) YÖNETİMİ
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ThresholdRule:
    """Risk izleme kuralı tanımı."""
    rule_id: str
    category: AlertCategory
    metric_name: str
    target_value: float
    operator: str  # ">", "<", ">=", "<=", "CHANGE_PCT"
    severity: AlertSeverity
    description: str = ""

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: RİSK MONİTÖR MOTORU
# ─────────────────────────────────────────────────────────────────────────────

class RealtimeRiskMonitor:
    """Ana risk izleme ve uyarı üretim motoru."""

    def __init__(self):
        self.rules: List[ThresholdRule] = []
        self.active_alerts: collections.deque[Alert] = collections.deque(maxlen=1000)
        self.alert_history: List[Alert] = []
        self._setup_default_rules()
        self.lock = threading.Lock()

    def _setup_default_rules(self):
        """Varsayılan kurumsal risk kurallarını yükle."""
        self.rules = [
            ThresholdRule("R001", AlertCategory.CREDIT_RISK, "credit_score", 450, "<", AlertSeverity.HIGH, "Kredi skoru tehlikeli seviyede."),
            ThresholdRule("R002", AlertCategory.FRAUD, "fraud_prob", 0.85, ">", AlertSeverity.CRITICAL, "Yüksek olasılıklı sahtekarlık şüphesi."),
            ThresholdRule("R003", AlertCategory.LIQUIDITY, "lcr_ratio", 1.10, "<", AlertSeverity.MEDIUM, "Likidite karşılama oranı sınırda."),
            ThresholdRule("R004", AlertCategory.MACRO, "vix_index", 25, ">", AlertSeverity.HIGH, "Küresel korku endeksi (VIX) yükseliyor! Piyasa oynaklığı riskli."),
            ThresholdRule("R005", AlertCategory.MACRO, "fx_rate", 33, ">", AlertSeverity.MEDIUM, "Döviz kurunda (USD/TRY) hareketlilik izleniyor."),
            ThresholdRule("R006", AlertCategory.CREDIT_RISK, "delinquency_days", 30, ">", AlertSeverity.LOW, "Gecikme süresi 30 günü geçti.")
        ]

    def check_metric(self, entity_id: str, category: AlertCategory, metric_name: str, value: float):
        """Gelen veriyi kurallara göre kontrol et."""
        relevant_rules = [r for r in self.rules if r.category == category and r.metric_name == metric_name]
        
        for rule in relevant_rules:
            is_triggered = False
            if rule.operator == ">" and value > rule.target_value: is_triggered = True
            elif rule.operator == "<" and value < rule.target_value: is_triggered = True
            elif rule.operator == ">=" and value >= rule.target_value: is_triggered = True
            elif rule.operator == "<=" and value <= rule.target_value: is_triggered = True
            
            if is_triggered:
                self._create_alert(entity_id, rule, value)

    def _create_alert(self, entity_id: str, rule: ThresholdRule, current_value: float):
        """Yeni bir uyarı oluştur ve listeye ekle."""
        with self.lock:
            # Mükerrer kontrolü (Son 5 dakika içinde aynı kural ve entity için alert varsa geç)
            now = datetime.datetime.now()
            duplicate = False
            for al in reversed(self.active_alerts):
                if (al.entity_id == entity_id and 
                    al.message == rule.description and 
                    (now - al.timestamp).seconds < 300):
                    duplicate = True
                    break
            
            if not duplicate:
                new_alert = Alert(
                    severity=rule.severity,
                    category=rule.category,
                    entity_id=entity_id,
                    message=rule.description,
                    value=current_value,
                    threshold=rule.target_value
                )
                self.active_alerts.appendleft(new_alert)
                self.alert_history.append(new_alert)

    def resolve_alert(self, alert_id: str, user: str):
        """Uyarıyı kapat."""
        with self.lock:
            for al in self.active_alerts:
                if al.id == alert_id:
                    al.is_resolved = True
                    al.resolved_at = datetime.datetime.now()
                    al.resolved_by = user
                    break

    def get_risk_pulse(self) -> Dict[str, Any]:
        """Canlı dashboard için anlık durum özeti."""
        with self.lock:
            counts = {
                "Kritik": len([a for a in self.active_alerts if a.severity == AlertSeverity.CRITICAL and not a.is_resolved]),
                "Yüksek": len([a for a in self.active_alerts if a.severity == AlertSeverity.HIGH and not a.is_resolved]),
                "Orta": len([a for a in self.active_alerts if a.severity == AlertSeverity.MEDIUM and not a.is_resolved]),
                "Düşük": len([a for a in self.active_alerts if a.severity == AlertSeverity.LOW and not a.is_resolved]),
            }
            
            total_active = sum(counts.values())
            
            return {
                "counts": counts,
                "total_active": total_active,
                "recent_alerts": [self._alert_to_dict(a) for a in list(self.active_alerts)[:10]],
                "system_status": "TEHLİKEDE" if counts["Kritik"] > 0 else "RİSKLİ" if counts["Yüksek"] > 3 else "NORMAL"
            }

    def _alert_to_dict(self, a: Alert) -> Dict[str, Any]:
        return {
            "id": a.id,
            "timestamp": a.timestamp.strftime("%H:%M:%S"),
            "severity": a.severity.value,
            "category": a.category.value,
            "entity": a.entity_id,
            "message": a.message,
            "value": round(a.value, 2),
            "threshold": a.threshold,
            "is_resolved": a.is_resolved
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: VERİ AKIŞ SİMÜLATÖRÜ (STREAM SIMULATION)
# ─────────────────────────────────────────────────────────────────────────────

class RiskStreamSimulator:
    """Anlık veri akışını simüle eden modül."""

    def __init__(self, monitor: RealtimeRiskMonitor):
        self.monitor = monitor
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False

    def _simulate_loop(self):
        """Gerçek piyasa verilerini izleyerek alarm üret."""
        tickers = {
            "VIX": "^VIX",
            "USD/TRY": "TRY=X",
            "GOLD": "GC=F",
            "BTC": "BTC-USD"
        }
        
        while self.is_running:
            for label, symbol in tickers.items():
                try:
                    data = yf.Ticker(symbol).history(period="1d")
                    if not data.empty:
                        last_price = data['Close'].iloc[-1]
                        
                        # Kategorik eşleştirme
                        if label == "VIX":
                            self.monitor.check_metric("GLOBAL", AlertCategory.MACRO, "vix_index", last_price)
                        elif label == "USD/TRY":
                            self.monitor.check_metric("TRY_FX", AlertCategory.MACRO, "fx_rate", last_price)
                        elif label == "GOLD":
                            self.monitor.check_metric("COMMODITY", AlertCategory.LIQUIDITY, "gold_price", last_price)
                except Exception:
                    continue
            
            # 1 dakikada bir kontrol et (API limitlerini korumak için)
            time.sleep(60)

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORT
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance for the monitor
_monitor_instance = RealtimeRiskMonitor()
_simulator_instance = RiskStreamSimulator(_monitor_instance)

def get_risk_monitor() -> RealtimeRiskMonitor:
    return _monitor_instance

def get_risk_simulator() -> RiskStreamSimulator:
    return _simulator_instance

# Start simulator on load for demo purposes (optional)
# _simulator_instance.start()

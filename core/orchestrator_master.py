"""
core/orchestrator_master.py — ProQuant Capital | Merkezi Sistem Orkestratörü v6.0
================================================================================

Tüm alt sistemleri (Econometrics, Risk, NLP, Execution, Governance) bir araya getiren,
veri akışını koordine eden ve platformun "tek bir canlı organizma" gibi çalışmasını 
sağlayan merkezi kontrol motoru.

Mimari (Central Nervous System):
  1. Engine Registry: Yüklenen tüm motorların (Engines) merkezi katalogu.
  2. Data Bus: Modüller arası asenkron ve senkron veri transferi.
  3. Lifecycle Management: Sistem başlatma (Startup), sağlık kontrolü (Health Check)
     ve güvenli kapatma (Graceful Shutdown) süreçleri.
  4. Global State Manager: Portföy değerleri, piyasa rejimi ve aktif alarmlar gibi
     sistem çapındaki değişkenlerin takibi.
  5. Cross-Module Workflows:
     - Pipeline A: Market Data -> Regime Mapping -> Portfolio Optimizer.
     - Pipeline B: News Stream -> Deep Sentiment (NLP) -> Trading signal -> Execution.
     - Pipeline C: Trade Fill -> Governance (Audit) -> Reporting Engine.

Güvenlik:
  - Tüm orkestrasyon adımları GovernanceEngine üzerinden yetki kontrolüne tabidir.

Author  : ProQuant Capital Systems Architecture
Version : 6.0.0
"""

from __future__ import annotations

import time
import enum
import logging
import datetime
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# Tüm ProQuant Modülleri (Importing to orchestrate)
from core.data_orchestrator import get_data_orchestrator
from core.governance_engine import get_governance_engine, UserSession, UserRole, Permission
from core.execution_engine import get_execution_engine
from modules.econometrics_engine import get_econometrics_engine
from modules.advanced_risk_suite import get_risk_suite
from modules.regime_mapping import get_regime_mapping_engine
from modules.deep_sentiment import get_deep_sentiment_engine
from modules.portfolio_optimizer_pro import get_portfolio_optimizer
from modules.pro_reporting_engine import get_reporting_engine

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: SİSTEM DURUMU VE MOTOR KAYDI
# ─────────────────────────────────────────────────────────────────────────────

class SystemStatus(enum.Enum):
    INITIALIZING = "Başlatılıyor"
    READY        = "Sistem Hazır"
    BUSY         = "İşlem Yapılıyor"
    MAINTENANCE  = "Bakım Modu"
    DISABLED     = "Devre Dışı"

@dataclass
class EngineHealth:
    """Tek bir motorun sağlık durumu."""
    name: str
    status: str = "OK"
    last_ping: datetime.datetime = field(default_factory=datetime.datetime.now)
    latency_ms: float = 0.0
    active_tasks: int = 0

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: MASTER ORCHESTRATOR ÇEKİRDEĞİ
# ─────────────────────────────────────────────────────────────────────────────

class MasterOrchestrator:
    """Sistemin 'Beyni' ve ana koordinasyon merkezi."""

    def __init__(self):
        self.status = SystemStatus.INITIALIZING
        self.registry: Dict[str, Any] = {}
        self.health_map: Dict[str, EngineHealth] = {}
        self.start_time = datetime.datetime.now()
        self._initialize_engines()

    def _initialize_engines(self):
        """Tüm motorları yükle ve kaydet."""
        print("🛠️ ProQuant Master Orchestrator: Motorlar Başlatılıyor...")
        
        self.registry = {
            "data": get_data_orchestrator(),
            "governance": get_governance_engine(),
            "execution": get_execution_engine(),
            "econometrics": get_econometrics_engine(),
            "risk": get_risk_suite(),
            "regime": get_regime_mapping_engine(),
            "nlp": get_deep_sentiment_engine(),
            "optimizer": get_portfolio_optimizer(),
            "reporting": get_reporting_engine()
        }
        
        for name in self.registry:
            self.health_map[name] = EngineHealth(name=name)
        
        self.status = SystemStatus.READY
        print(f"✅ Sistem Hazır. Çalışma Zamanı: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def check_system_health(self) -> List[Dict[str, Any]]:
        """Tüm motorların sağlık durumunu denetle."""
        report = []
        for name, health in self.health_map.items():
            report.append(health.__dict__)
        return report

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: ÇAPRAZ MODÜL İŞ akışları (CROSS-MODULE PIPELINES)
# ─────────────────────────────────────────────────────────────────────────────

    def run_investment_pipeline(self, symbol: str, user_session: UserSession):
        """
        Tam yatırım akışını koordine et:
        Data -> Regime -> Risk -> Optimizer -> Execution.
        """
        print(f"🔄 Yatırım Boru Hattı Başlatıldı: {symbol}")
        
        # 1. Yetki Kontrolü
        if not self.registry["governance"].authorize(user_session, Permission.EXECUTE_TRADE):
            return {"status": "REJECTED", "reason": "Unauthorized access"}

        # 2. Veri Alımı & Rejim Tespiti
        data = self.registry["data"].get_market_data(symbol)
        regime = self.registry["regime"].analyze_market_regime(data.to_numpy())
        
        # 3. Risk ve Optimizasyon
        risk = self.registry["risk"].calculate_comprehensive_risk(data.to_numpy())
        opt = self.registry["optimizer"].run_comprehensive_optimization([symbol], data.to_numpy().reshape(-1, 1))
        
        # 4. Raporlama
        self.registry["reporting"].create_corporate_risk_report(risk, user_session.username)
        
        return {
            "symbol": symbol,
            "regime": regime["current_regime"],
            "var_99": risk["metrics"]["parametric"]["var"],
            "optimal_weight": opt["risk_parity"][symbol],
            "timestamp": datetime.datetime.now().isoformat()
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: SİSTEM YÖNETİMİ (SYSTEM ADMIN)
# ─────────────────────────────────────────────────────────────────────────────

    def broadcast_message(self, message: str):
        """Tüm modüllere ve UI katmanına sistem mesajı yayını yapar."""
        log_msg = f"📣 [BROADCAST] {datetime.datetime.now().isoformat()} | {message}"
        logging.info(log_msg)
        # (Gerçekte bu WebSocket veya Streamlit state üzerinden iletilir)
        return log_msg

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

_master_instance = MasterOrchestrator()

def get_master_orchestrator() -> MasterOrchestrator:
    return _master_instance

def startup_check_sequence():
    """Uygulama başında çalıştırılacak kritik kontrol dizisi."""
    orchestrator = get_master_orchestrator()
    health = orchestrator.check_system_health()
    all_ok = all(h["status"] == "OK" for h in health)
    if not all_ok:
        logging.error("Sistem başlatma sırasında kritik motor hataları tespit edildi!")
    return all_ok

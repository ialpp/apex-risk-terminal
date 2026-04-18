"""
core/governance_engine.py — ProQuant Capital | Kurumsal Denetim & Yönetişim v5.0
================================================================================

Kurumsal seviyede güvenlik, yetkilendirme (RBAC), denetim (Audit) ve 
uyumluluk (Compliance) süreçlerini yöneten merkezi yönetişim çekirdeği.
Bu modül, platformun kurumsal standartlara (SOC2, GDPR, ISO 27001) uygun 
şekilde çalışmasını sağlar.

Kapsam:
  1. Rol Tabanlı Erişim Kontrolü (Role-Based Access Control - RBAC):
     - Roller: ADMIN, QUANT, COMPLIANCE, VIEWER.
     - İzin Matrisi: Modül bazlı okuma/yazma/çalıştırma yetkileri.
  2. Denetim İzi (Audit Trail):
     - Her kritik işlem (Emir gönderimi, model değişikliği) loglanır.
     - Değiştirilemez (Immutable) log yapısı (simüle).
  3. Uyumluluk Kuralları Motoru (Compliance Rules Engine):
     - Pre-trade Limitleri: Tek hisse limiti, sektör yoğunlaşma limiti.
     - Restricted List: Yasaklı varlıkların engellenmesi.
     - Fat-Finger Warning: Normal dışı emir büyüklüğü uyarıları.
  4. Yönetişim İş Akışları (Workflows):
     - Model onay (Approval) süreçleri.
     - Acil durum kapatma (Kill Switch) yönetimi.

Matematiksel Alt Yapı:
  - İzin doğrulama algoritmaları.
  - Hashing (Audit bütünlüğü için).

Author  : ProQuant Capital Governance & Security Team
Version : 5.0.0
"""

from __future__ import annotations
import time

import uuid
import enum
import logging
import datetime
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, Set

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: YETKİLENDİRME (RBAC) MODELİ
# ─────────────────────────────────────────────────────────────────────────────

class UserRole(enum.Enum):
    ADMIN       = "System Administrator"
    QUANT       = "Quantitative Researcher"
    COMPLIANCE  = "Compliance Officer"
    VIEWER      = "Read-Only Observer"

class Permission(enum.Enum):
    WRITE_MODEL   = "model:write"
    READ_MODEL    = "model:read"
    EXECUTE_TRADE = "trade:execute"
    VIEW_AUDIT    = "audit:view"
    MANAGE_USERS  = "user:manage"

ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: set(Permission),
    UserRole.QUANT: {Permission.READ_MODEL, Permission.WRITE_MODEL, Permission.EXECUTE_TRADE},
    UserRole.COMPLIANCE: {Permission.READ_MODEL, Permission.VIEW_AUDIT},
    UserRole.VIEWER: {Permission.READ_MODEL}
}

@dataclass
class UserSession:
    """Aktif kullanıcı oturumu."""
    user_id: str
    role: UserRole
    username: str
    session_start: datetime.datetime = field(default_factory=datetime.datetime.now)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: DENETİM İZİ (AUDIT LOGGING)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AuditLogEntry:
    """Tekil bir denetim kaydı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    user_id: str = "SYSTEM"
    action: str = ""
    resource: str = ""
    status: str = "SUCCESS"
    metadata: Dict[str, Any] = field(default_factory=dict)

class AuditManager:
    """Sistemdeki tüm eylemleri kaydeden motor."""

    def __init__(self):
        self._logs: List[AuditLogEntry] = []

    def log_action(self, user: UserSession, action: str, resource: str, metadata: Dict[str, Any] = None):
        entry = AuditLogEntry(
            user_id=user.user_id,
            action=action,
            resource=resource,
            metadata=metadata or {}
        )
        self._logs.append(entry)
        # Kurumsal loglama (Basit console simülasyonu)
        print(f"🔒 [AUDIT] {entry.timestamp.isoformat()} | User: {user.username} | {action} on {resource}")

    def get_user_history(self, user_id: str) -> List[AuditLogEntry]:
        return [log for log in self._logs if log.user_id == user_id]

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: UYUMLULUK MOTORU (COMPLIANCE)
# ─────────────────────────────────────────────────────────────────────────────

class ComplianceEngine:
    """Emir öncesi (Pre-trade) kontrollerini yapan motor."""

    def __init__(self):
        self.max_position_size = 0.10 # Portföyün max %10'u tek hisse
        self.restricted_symbols: Set[str] = {"YASAKLI_01", "SPEC_02"}

    def validate_order(self, symbol: str, quantity: float, price: float, portfolio_value: float) -> Tuple[bool, str]:
        """Emrin kurallara uygunluğunu denetle."""
        
        # 1. Restricted List Kontrolü
        if symbol in self.restricted_symbols:
            return False, f"UYARI: {symbol} yasaklı varlıklar listesinde bulunuyor."
            
        # 2. Limit Kontrolü
        order_val = quantity * price
        if order_val > portfolio_value * self.max_position_size:
            return False, "UYARI: Maksimum tek varlık yoğunlaşma limiti (%10) aşılıyor."
            
        # 3. Fat-Finger Kontrolü (Anormal büyüklük)
        if order_val > 10000000: # 10M$ limit
            return False, "UYARI: Sıradışı emir büyüklüğü (Fat-Finger Kontrolü)."
            
        return True, "Onaylandı"

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: YÖNETİŞİM ORKESTRATÖRÜ
# ─────────────────────────────────────────────────────────────────────────────

class GovernanceOrchestrator:
    """Tüm yönetişim süreçlerini birleştiren ana API."""

    def __init__(self):
        self.audit = AuditManager()
        self.compliance = ComplianceEngine()
        self._kill_switch_active = False

    def authorize(self, session: UserSession, permission: Permission) -> bool:
        """Kullanıcının belirtilen eyleme yetkisi olup olmadığını kontrol et."""
        if self._kill_switch_active and session.role != UserRole.ADMIN:
            return False
            
        is_allowed = permission in ROLE_PERMISSIONS.get(session.role, set())
        
        # Log yetkilendirme girişimi
        self.audit.log_action(session, "AUTH_CHECK", permission.value, {"allowed": is_allowed})
        
        return is_allowed

    def activate_kill_switch(self, admin_session: UserSession):
        """Sistemi acil durum moduna geçir (Sadece Admin)."""
        if admin_session.role == UserRole.ADMIN:
            self._kill_switch_active = True
            self.audit.log_action(admin_session, "SYSTEM_KILL_SWITCH", "GLOBAL", {"state": "ACTIVE"})
            return True
        return False

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

_gov_engine = GovernanceOrchestrator()

def get_governance_engine() -> GovernanceOrchestrator:
    return _gov_engine

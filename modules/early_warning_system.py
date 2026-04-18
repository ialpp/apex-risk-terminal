"""
modules/early_warning_system.py
Temerrüt Erken Uyarı Sistemi
Portföydeki müşterileri tarayarak risk işaretlerini tespit eder.
"""

import pandas as pd
from core.database_handler import db
from config import DTI_HIGH, DTI_MEDIUM


class EarlyWarningSystem:
    """
    Portföy genelinde otomatik risk taraması yapar.
    Her müşteri için belirlenen eşikler aşılırsa veritabanına uyarı kaydeder.
    """

    SEVERITY_LEVELS = {
        "Kritik":  {"color": "#ef4444", "icon": "🔴"},
        "Yüksek":  {"color": "#f97316", "icon": "🟠"},
        "Orta":    {"color": "#f59e0b", "icon": "🟡"},
        "Düşük":   {"color": "#3b82f6", "icon": "🔵"},
    }

    def run_full_scan(self, analyst: str = "Sistem") -> dict:
        """
        Tüm aktif müşterileri tarar ve yeni uyarılar üretir.
        Dönüş: {"scanned": int, "new_warnings": int, "by_severity": dict}
        """
        customers = db.get_all_customers(active_only=True)
        if customers.empty:
            return {"scanned": 0, "new_warnings": 0, "by_severity": {}}

        scanned = 0
        new_count = 0
        severity_counts = {"Kritik": 0, "Yüksek": 0, "Orta": 0, "Düşük": 0}

        for _, row in customers.iterrows():
            scanned += 1
            warnings = self._analyze_customer(row)
            for warn in warnings:
                db.add_warning(
                    customer_id=int(row["id"]),
                    customer_code=str(row["customer_code"]),
                    warning_type=warn["type"],
                    severity=warn["severity"],
                    message=warn["message"]
                )
                new_count += 1
                severity_counts[warn["severity"]] = severity_counts.get(warn["severity"], 0) + 1

        return {
            "scanned":      scanned,
            "new_warnings": new_count,
            "by_severity":  severity_counts
        }

    def _analyze_customer(self, row: pd.Series) -> list[dict]:
        """Tek müşteri için uyarı listesi üretir."""
        warnings = []

        income = max(float(row.get("monthly_income", 0) or 0), 1)
        debt   = float(row.get("total_debt", 0) or 0)
        dti    = debt / income
        late   = int(row.get("late_payment_count", 0) or 0)
        score  = row.get("credit_score")

        # ── DTI Kritik Eşiği Aşıldı
        if dti > 2.5:
            warnings.append({
                "type":     "Aşırı Borçluluk",
                "severity": "Kritik",
                "message":  f"Borç/Gelir Oranı %{dti*100:.0f} ile kritik seviyede. Anlık müdahale gerekiyor."
            })
        elif dti > DTI_HIGH:
            warnings.append({
                "type":     "Yüksek DTI",
                "severity": "Yüksek",
                "message":  f"DTI oranı %{dti*100:.0f} — risk eşiği aşıldı (%65)."
            })

        # ── Gecikmiş Ödeme Artışı
        if late >= 6:
            warnings.append({
                "type":     "Çoklu Gecikme",
                "severity": "Kritik",
                "message":  f"{late} adet gecikmiş ödeme — tahsilat sürecine alınmalı."
            })
        elif late >= 3:
            warnings.append({
                "type":     "Gecikmiş Ödeme",
                "severity": "Yüksek",
                "message":  f"{late} adet gecikmiş ödeme tespit edildi. İzlemeye alındı."
            })

        # ── Düşük Kredi Skoru Uyarısı
        if score is not None:
            if score < 500:
                warnings.append({
                    "type":     "Çok Düşük Skor",
                    "severity": "Kritik",
                    "message":  f"Kredi skoru {score:.0f} — portföy kalitesi açısından kritik."
                })
            elif score < 580:
                warnings.append({
                    "type":     "Düşük Skor",
                    "severity": "Orta",
                    "message":  f"Kredi skoru {score:.0f} — yakından izlenmelidir."
                })

        return warnings

    def get_active_warnings_df(self) -> pd.DataFrame:
        """Aktif (çözülmemiş) uyarıları döndürür."""
        return db.get_active_warnings()

    def resolve(self, warning_id: int, resolved_by: str):
        db.resolve_warning(warning_id, resolved_by)

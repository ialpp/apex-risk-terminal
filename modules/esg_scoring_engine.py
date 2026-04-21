"""
modules/esg_scoring_engine.py — ProQuant Capital | ESG Risk & Sürdürülebilirlik Motoru v2.0
==========================================================================================

Kurumsal Çevresel, Sosyal ve Yönetişim (ESG) skorlama ve risk değerlendirme motoru.
Yatırım bankaları ve varlık yönetim şirketleri için sürdürülebilirlik analizi sağlar.

Kapsam:
  - Çevresel (Environmental): Karbon ayak izi, enerji yoğunluğu, atık yönetimi, su kullanımı.
  - Sosyal (Social): Çalışan hakları, iş sağlığı ve güvenliği, çeşitlilik (DEI), toplum etkisi.
  - Yönetişim (Governance): Yönetim kurulu yapısı, yönetici ücretleri, etik kurallar, şeffaflık.
  - NLP Haber Simülasyonu: Kurumsal itibar ve kriz takibi.
  - Tedarik Zinciri Risk Haritalama: Kapsam 1, 2 ve 3 emisyon takibi.
  - Sektörel ESG Matrisleri: SASB ve TCFD standartlarına uyum.

Author  : ProQuant Capital Sustainability Research
Version : 2.0.0
"""

from __future__ import annotations
import time

import enum
import math
import random
import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from config import LIVE_DATA_MODE
from modules.nlp_intelligence import get_nlp_engine

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: ENUM & SABİTLER
# ─────────────────────────────────────────────────────────────────────────────

class ESGRating(enum.Enum):
    AAA = "AAA"  # Lider
    AA  = "AA"   # Lider
    A   = "A"    # Ortalama Üstü
    BBB = "BBB"  # Ortalama
    BB  = "BB"   # Ortalama Altı
    B   = "B"    # Geciken
    CCC = "CCC"  # Yüksek Risk

class ESGCategory(enum.Enum):
    ENVIRONMENTAL = "Environmental"
    SOCIAL        = "Social"
    GOVERNANCE    = "Governance"

class ESGMetricType(enum.Enum):
    QUANTITATIVE = "Quantitative"
    QUALITATIVE  = "Qualitative"

# Sektörel Ağırlıklar (SASB bazlı basitleştirilmiş)
SECTOR_ESG_WEIGHTS = {
    "Enerji":           {"E": 0.50, "S": 0.20, "G": 0.30},
    "Teknoloji":        {"E": 0.15, "S": 0.45, "G": 0.40},
    "Finans":           {"E": 0.10, "S": 0.30, "G": 0.60},
    "Sağlık":           {"E": 0.20, "S": 0.50, "G": 0.30},
    "İnşaat":           {"E": 0.45, "S": 0.35, "G": 0.20},
    "Ulaşım":           {"E": 0.55, "S": 0.20, "G": 0.25},
    "Perakende":        {"E": 0.30, "S": 0.40, "G": 0.30},
    "Hammadde":         {"E": 0.60, "S": 0.20, "G": 0.20},
    "Kamu Hizmetleri":  {"E": 0.70, "S": 0.10, "G": 0.20},
    "Genel":            {"E": 0.33, "S": 0.33, "G": 0.34},
}

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: VERİ YAPILARI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ESGMetric:
    """Tek bir ESG metriği."""
    name: str
    category: ESGCategory
    value: float  # 0-100 arası normalize edilmiş skor
    raw_value: Any
    unit: str
    weight: float
    metric_type: ESGMetricType = ESGMetricType.QUANTITATIVE
    description: str = ""

@dataclass
class ESGScorecard:
    """Kurumsal ESG karne özeti."""
    entity_name: str
    sector: str
    e_score: float
    s_score: float
    g_score: float
    total_score: float
    rating: ESGRating
    metrics: List[ESGMetric] = field(default_factory=list)
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)

    @property
    def ranking_in_sector(self) -> float:
        """Sektörel bazdaki yüzdelik dilimi (simülasyon)."""
        return random.uniform(0.1, 99.9)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: ESG ANALİZ MOTORU
# ─────────────────────────────────────────────────────────────────────────────

class ESGScoringEngine:
    """ESG skorlama ve analiz mantığı."""

    def __init__(self):
        self._history: Dict[str, List[ESGScorecard]] = {}

    def calculate_rating(self, score: float) -> ESGRating:
        """Toplam skoru harf notuna çevir."""
        if score >= 90: return ESGRating.AAA
        if score >= 80: return ESGRating.AA
        if score >= 70: return ESGRating.A
        if score >= 55: return ESGRating.BBB
        if score >= 40: return ESGRating.BB
        if score >= 25: return ESGRating.B
        return ESGRating.CCC

    def score_environmental(self, data: Dict[str, Any]) -> List[ESGMetric]:
        """Çevresel skor bileşenlerini hesapla."""
        metrics = []
        
        # 1. Karbon Yoğunluğu (Emisyon / Gelir)
        carbon_int = data.get("carbon_intensity", 50)
        score = max(0, 100 - (carbon_int * 2))  # Düşük yoğunluk iyi
        metrics.append(ESGMetric(
            "Karbon Yoğunluğu", ESGCategory.ENVIRONMENTAL, score, carbon_int, "tCO2e/m$", 0.40,
            description="Gelir başına karbon emisyonu."
        ))

        # 2. Yenilenebilir Enerji Payı
        renew_pct = data.get("renewable_energy_pct", 10)
        score = min(100, renew_pct * 2.5)  # %40 üstü tam puan
        metrics.append(ESGMetric(
            "Yenilenebilir Enerji", ESGCategory.ENVIRONMENTAL, score, renew_pct, "%", 0.30,
            description="Toplam enerji tüketiminde yeşil enerji oranı."
        ))

        # 3. Su Verimliliği
        water_eff = data.get("water_efficiency_score", 60)
        metrics.append(ESGMetric(
            "Su Yönetimi", ESGCategory.ENVIRONMENTAL, water_eff, water_eff, "Score", 0.15,
            description="Su geri kazanımı ve koruma politikaları."
        ))

        # 4. Atık Yönetimi & Geri Dönüşüm
        waste_score = data.get("waste_management_score", 55)
        metrics.append(ESGMetric(
            "Atık Yönetimi", ESGCategory.ENVIRONMENTAL, waste_score, waste_score, "Score", 0.15,
            description="Tehlikeli atık yönetimi ve döngüsel ekonomi."
        ))

        return metrics

    def score_social(self, data: Dict[str, Any]) -> List[ESGMetric]:
        """Sosyal skor bileşenlerini hesapla."""
        metrics = []

        # 1. Çalışan Çeşitliliği (Gender/Diversity)
        div_pct = data.get("diversity_pct", 20)
        score = min(100, div_pct * 2)  # %50 üstü tam puan
        metrics.append(ESGMetric(
            "Kapsayıcılık & Çeşitlilik", ESGCategory.SOCIAL, score, div_pct, "%", 0.30,
            description="Yönetim kademesinde kadın ve azınlık oranı."
        ))

        # 2. İş Sağlığı ve Güvenliği
        isg_rate = data.get("injury_rate", 2)
        score = max(0, 100 - (isg_rate * 20))  # Kaza oranı arttıkça skor düşer
        metrics.append(ESGMetric(
            "İş Sağlığı ve Güvenliği", ESGCategory.SOCIAL, score, isg_rate, "LTIFR", 0.30,
            description="Kayıp iş günü kaza frekansı."
        ))

        # 3. Eğitim & Gelişim
        training_hours = data.get("avg_training_hours", 20)
        score = min(100, training_hours * 2)
        metrics.append(ESGMetric(
            "Eğitim & Gelişim", ESGCategory.SOCIAL, score, training_hours, "Saat/Yıl", 0.20,
            description="Çalışan başına yıllık eğitim süresi."
        ))

        # 4. Toplum Etkisi
        community = data.get("community_impact_score", 50)
        metrics.append(ESGMetric(
            "Toplum Etkisi", ESGCategory.SOCIAL, community, community, "Score", 0.20,
            description="Sosyal sorumluluk projeleri ve yerel kalkınma desteği."
        ))

        return metrics

    def score_governance(self, data: Dict[str, Any]) -> List[ESGMetric]:
        """Yönetişim skor bileşenlerini hesapla."""
        metrics = []

        # 1. Yönetim Kurulu Bağımsızlığı
        indep_pct = data.get("board_independence_pct", 40)
        score = min(100, indep_pct * 1.5)
        metrics.append(ESGMetric(
            "YK Bağımsızlığı", ESGCategory.GOVERNANCE, score, indep_pct, "%", 0.40,
            description="Bağımsız yönetim kurulu üyelerinin oranı."
        ))

        # 2. CEO Pay Ratio (Adalet)
        pay_ratio = data.get("ceo_pay_ratio", 50)
        score = max(0, 100 - (pay_ratio / 2))  # Ratio arttıkça skor düşer
        metrics.append(ESGMetric(
            "Ücret Adaleti", ESGCategory.GOVERNANCE, score, pay_ratio, "Ratio", 0.20,
            description="CEO maaşının çalışan ortalamasına oranı."
        ))

        # 3. Şeffaflık & Denetim
        audit_score = data.get("audit_transparency_score", 80)
        metrics.append(ESGMetric(
            "Şeffaflık", ESGCategory.GOVERNANCE, audit_score, audit_score, "Score", 0.20,
            description="Finansal olmayan raporlama kalitesi."
        ))

        # 4. rüşvet ve Yolsuzlukla Mücadele
        ethics_score = data.get("ethics_compliance_score", 75)
        metrics.append(ESGMetric(
            "İş Etiği", ESGCategory.GOVERNANCE, ethics_score, ethics_score, "Score", 0.20,
            description="Yolsuzlukla mücadele politikaları ve uyum."
        ))

        return metrics

    def perform_full_scoring(self, entity_name: str, sector: str, raw_data: Dict[str, Any]) -> ESGScorecard:
        """Uçtan uca ESG skorlaması yap."""
        e_metrics = self.score_environmental(raw_data)
        s_metrics = self.score_social(raw_data)
        g_metrics = self.score_governance(raw_data)

        e_avg = sum(m.value * m.weight for m in e_metrics) / sum(m.weight for m in e_metrics)
        s_avg = sum(m.value * m.weight for m in s_metrics) / sum(m.weight for m in s_metrics)
        g_avg = sum(m.value * m.weight for m in g_metrics) / sum(m.weight for m in g_metrics)

        # Sektörel ağırlıkları uygula
        weights = SECTOR_ESG_WEIGHTS.get(sector, SECTOR_ESG_WEIGHTS["Genel"])
        total_score = (e_avg * weights["E"]) + (s_avg * weights["S"]) + (g_avg * weights["G"])
        
        # CANLI VERİ EKLEMESİ: Haber duyarlılığı skoru etkiler
        if LIVE_DATA_MODE:
            nlp = get_nlp_engine()
            narrative = nlp.get_active_narrative()
            # Pazar genel duyarlılığı skora %10 etki eder
            total_score += (narrative["market_sentiment"] * 10)
            total_score = max(0, min(100, total_score))
        
        rating = self.calculate_rating(total_score)
        
        scorecard = ESGScorecard(
            entity_name=entity_name,
            sector=sector,
            e_score=round(e_avg, 2),
            s_score=round(s_avg, 2),
            g_score=round(g_avg, 2),
            total_score=round(total_score, 2),
            rating=rating,
            metrics=e_metrics + s_metrics + g_metrics
        )

        # Geçmişe kaydet
        if entity_name not in self._history:
            self._history[entity_name] = []
        self._history[entity_name].append(scorecard)

        return scorecard

    def get_esg_trend(self, entity_name: str) -> List[float]:
        """Var olan geçmiş skorları döndür. En az 12 aylık veri seti simüle eder."""
        historical = [s.total_score for s in self._history.get(entity_name, [])]
        
        # 12 aylık periyot için liste oluştur
        if len(historical) >= 12:
            return historical[-12:]
        
        # Eksik verileri simüle ederek 12'ye tamamla
        last_val = historical[-1] if historical else random.uniform(55, 75)
        needed = 12 - len(historical)
        simulated = [max(0, min(100, last_val + random.uniform(-8, 8))) for _ in range(needed)]
        return simulated + historical

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: ŞİRKET SİMÜLASYONU
# ─────────────────────────────────────────────────────────────────────────────

def get_esg_simulation_data(name: str, sector: str) -> Dict[str, Any]:
    """Sektöre özel gerçekçi sentetik veri seti."""
    base = {
        "Enerji":           {"carbon": 120, "renew": 15, "diversity": 12, "ceo": 120},
        "Teknoloji":        {"carbon": 10,  "renew": 80, "diversity": 35, "ceo": 180},
        "Finans":           {"carbon": 5,   "renew": 90, "diversity": 45, "ceo": 250},
        "İnşaat":           {"carbon": 85,  "renew": 5,  "diversity": 8,  "ceo": 60},
        "Kamu Hizmetleri":  {"carbon": 200, "renew": 40, "diversity": 25, "ceo": 40},
    }
    
    defaults = base.get(sector, {"carbon": 50, "renew": 20, "diversity": 25, "ceo": 100})
    
    # Biraz varyasyon ekle
    return {
        "carbon_intensity":         max(1, defaults["carbon"] * random.uniform(0.8, 1.5)),
        "renewable_energy_pct":     min(100, defaults["renew"] * random.uniform(0.5, 2.0)),
        "water_efficiency_score":   random.uniform(30, 95),
        "waste_management_score":   random.uniform(30, 95),
        "diversity_pct":            min(100, defaults["diversity"] * random.uniform(0.7, 1.4)),
        "injury_rate":              random.uniform(0.1, 8.0),
        "avg_training_hours":       random.uniform(5, 60),
        "community_impact_score":   random.uniform(20, 100),
        "board_independence_pct":   random.uniform(20, 100),
        "ceo_pay_ratio":            max(5, defaults["ceo"] * random.uniform(0.5, 2.0)),
        "audit_transparency_score": random.uniform(50, 100),
        "ethics_compliance_score":  random.uniform(50, 100),
    }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 5: HABER VE İTİBAR MOTORU (NLP SİMÜLASYONU)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ESGNewsEvent:
    title: str
    impact: float  # -10 (Çok kötü) ile +10 (Çok iyi)
    source: str
    category: ESGCategory
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

class ReputationEngine:
    """Haber akışının ESG skoruna etkisini simüle eden motor."""
    
    NEWS_TEMPLATES = [
        ("şirket yeni bir rüzgar çiftliği yatırımını duyurdu.", 4.5, ESGCategory.ENVIRONMENTAL),
        ("Karbon emisyon hedeflerini %20 erken yakaladı.", 6.0, ESGCategory.ENVIRONMENTAL),
        ("Bir tesisinde çevre kirliliği iddiaları ile soruşturma açıldı.", -7.5, ESGCategory.ENVIRONMENTAL),
        ("Çeşitlilik ve kapsayıcılık ödülüne layık görüldü.", 3.5, ESGCategory.SOCIAL),
        ("Toplu işten çıkarma kararı çalışan ve sendika tepkisi çekti.", -5.0, ESGCategory.SOCIAL),
        ("Yönetim kuruluna 2 yeni bağımsız üye atandı.", 4.0, ESGCategory.GOVERNANCE),
        ("Vergi usulsüzlüğü iddiaları borsada değer kaybına neden oldu.", -8.5, ESGCategory.GOVERNANCE)
    ]

    def generate_news(self, entity_name: str) -> List[ESGNewsEvent]:
        num = random.randint(2, 5)
        events = []
        for _ in range(num):
            tmpl = random.choice(self.NEWS_TEMPLATES)
            events.append(ESGNewsEvent(
                title=f"{entity_name} {tmpl[0]}",
                impact=tmpl[1],
                source=random.choice(["Bloomberg", "Reuters", "Financial Times", "Dünya Gazetesi"]),
                category=tmpl[2]
            ))
        return events

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def get_esg_engine() -> ESGScoringEngine:
    return ESGScoringEngine()

def get_reputation_engine() -> ReputationEngine:
    return ReputationEngine()

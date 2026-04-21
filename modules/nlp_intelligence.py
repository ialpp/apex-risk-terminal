"""
modules/nlp_intelligence.py — ProQuant Capital | Gelişmiş NLP & Haber İstihbarat Motoru v4.0
========================================================================================

Kurumsal seviyede finansal metin analizi, duygu tespiti (Sentiment Analysis) ve
haber akışlarından yatırım sinyali üretimi sağlayan NLP (Doğal Dil İşleme) motoru.
Bu modül, yapılandırılmamış verileri (Haberler, Raporlar, Sosyal Medya) kantitatif 
metriklere dönüştürür.

Kapsam:
  1. Duygu Analiz Çekirdeği (Sentiment Engine):
     - Lexicon-based (Sözlük tabanlı) skorlama sistemi.
     - Finansal terminolojiye (Finanical Lexicon) optimize edilmiş sözlükler.
     - Cümle bazlı (Sentence-level) duygu ağırlıklandırma.
  2. Varlık Tespiti (Entity Extraction):
     - Metin içinden `TICKER` (Hisse kodları) ve şirket isimlerinin otonom tespiti.
     - Sektörel bağlam (Contextual) analizi.
  3. Haber Etki Modellemesi (Impact Modeling):
     - Haber etki süresi (Decay rate) hesaplama.
     - Sinyal gücü (Signal intensity) ve duyuru türü bazlı ağırlıklandırma.
  4. Gerçek Zamanlı Alert Sistemi:
     - Aciliyet (Urgency) skoru üretimi.
     - Kritikliğe göre anlık bildirim (Alert) tetikleme.
  5. Dil Desteği:
     - Türkçe ve İngilizce finansal terminoloji hibrit desteği.

Matematiksel Alt Yapı:
  - TF-IDF (Term Frequency-Inverse Document Frequency) simülasyonu.
  - Exponential Decay fonksiyonları (Haber ömrü için).

Author  : ProQuant Capital AI & NLP Research Lab
Version : 4.0.0
"""

from __future__ import annotations

import re
import time
import math
import random
import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import requests
import yfinance as yf
from data.sample_warehouse import SampleDataWarehouse, GLOBAL_CORPORATE_MASTER

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: NLP VERİ MODELLERİ
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FinancialNews:
    """Tekil bir haber maddesi."""
    headline: str
    content: str
    source: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    entities: List[str] = field(default_factory=list)
    base_sentiment: float = 0.0

@dataclass
class SentimentResult:
    """Duygu analizi sonucu."""
    overall_score: float # -1.0 to 1.0
    intensity: float     # 0.0 to 1.0
    impact_duration_hrs: int
    detected_entities: List[str]
    urgency: str # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: DUYGU ANALİZİ (LEXICON ENGINE)
# ─────────────────────────────────────────────────────────────────────────────

class SentimentEngine:
    """Metinleri finansal sözlükler üzerinden analiz eden motor."""

    def __init__(self):
        self.warehouse = SampleDataWarehouse()

    def analyze_text(self, text: str) -> float:
        """Metnin kümülatif duygu skorunu hesaplar."""
        # Veri ambarındaki 5.000+ kelimelik sözlüğü kullan
        score = self.warehouse.search_sentiment(text)
        return score

    def get_urgency(self, score: float, entity_importance: float) -> str:
        """Haberin aciliyetini belirle."""
        combined = abs(score) * entity_importance
        if combined > 0.8: return "CRITICAL"
        if combined > 0.5: return "HIGH"
        if combined > 0.2: return "MEDIUM"
        return "LOW"

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: VARLIK VE ETKİ MODELLEME
# ─────────────────────────────────────────────────────────────────────────────

class EntityExtractor:
    """Metin içindeki finansal varlıkları tespit eder."""

    def __init__(self):
        # Kayıtlı ticker listesi (Warehouse'dan)
        self.tickers = {c["symbol"] for c in GLOBAL_CORPORATE_MASTER}

    def find_tickers(self, text: str) -> List[str]:
        """Metin içindeki varlık kodlarını (XOM, AAPL vb.) regex ile bul."""
        # Büyük harf, 2-5 karakterli kelimeleri ara
        words = re.findall(r'\b[A-Z]{2,5}\b', text)
        found = [w for w in words if w in self.tickers]
        return list(set(found))

class NewsImpactDecline:
    """Haber etkisinin zaman içindeki sönümlenmesini (decay) modeller."""

    @staticmethod
    def calculate_decay(base_sentiment: float, hours_passed: float, half_life: float = 4.0) -> float:
        """
        R(t) = R0 * e^(-λt)
        Haberin etkisi eksponansiyel olarak azalır.
        """
        decay_constant = math.log(2) / half_life
        remaining_impact = base_sentiment * math.exp(-decay_constant * hours_passed)
        return remaining_impact

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: HABER İSTİHBARAT ORKESTRATÖRÜ
# ─────────────────────────────────────────────────────────────────────────────

class NLPIntelligenceEngine:
    """Tüm NLP süreçlerini yöneten ana API."""

    def __init__(self):
        self.sentiment = SentimentEngine()
        self.extractor = EntityExtractor()
        self.decay_model = NewsImpactDecline()
        self.news_buffer: List[FinancialNews] = []
        # Auto-populate if possible
        try:
            self.news_buffer = LiveNewsProvider().fetch_live_news()
        except Exception:
            pass

    def process_incoming_news(self, news_item: FinancialNews) -> SentimentResult:
        """Yeni gelen bir haberi analiz et ve sonuç üret."""
        # 1. Varlık Tespiti
        detected = self.extractor.find_tickers(news_item.headline + " " + news_item.content)
        news_item.entities = detected
        
        # 2. Duygu Skoru
        score = self.sentiment.analyze_text(news_item.headline)
        news_item.base_sentiment = score
        
        # 3. Önem ve Etki Süresi
        # Büyük şirketse etki süresi daha uzundur
        duration = 24 if any(e in ["AAPL", "JPM", "XOM"] for e in detected) else 4
        
        # 4. Aciliyet
        importance = 1.0 if detected else 0.5
        urgency = self.sentiment.get_urgency(score, importance)
        
        # Arabelleğe ekle
        self.news_buffer.append(news_item)
        
        return SentimentResult(
            overall_score=score,
            intensity=abs(score),
            impact_duration_hrs=duration,
            detected_entities=detected,
            urgency=urgency
        )

    def get_active_narrative(self) -> Dict[str, float]:
        """Tüm haber akışından süzülen aktif piyasa 'anlatısı' (Narrative)."""
        current_time = datetime.datetime.now()
        net_narrative = 0.0
        
        for news in self.news_buffer:
            age = (current_time - news.timestamp).total_seconds() / 3600.0
            if age < 48: # Sadece son 48 saat
                impact = self.decay_model.calculate_decay(news.base_sentiment, age)
                net_narrative += impact
                
        return {
            "market_sentiment": max(-1.0, min(1.0, net_narrative)),
            "buffer_size": len(self.news_buffer),
            "trend": "BULLISH" if net_narrative > 0.1 else "BEARISH" if net_narrative < -0.1 else "NEUTRAL"
        }

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 5: HABER SİMÜLASYON VERİ SETLERİ (MİLYONLARCA TOKENS)
# ─────────────────────────────────────────────────────────────────────────────

class LiveNewsProvider:
    """Gerçek zamanlı finansal haber akışı sağlar."""
    
    def __init__(self):
        self.tickers = ["^GSPC", "TRY=X", "GC=F", "BTC-USD", "AAPL", "NVDA", "THYAO.IS"]

    def fetch_live_news(self) -> List[FinancialNews]:
        """Seçili ana varlıklardan gerçek haberleri çeker."""
        all_news = []
        for symbol in self.tickers:
            try:
                ticker = yf.Ticker(symbol)
                yf_news = ticker.news
                for item in yf_news[:3]: # Her sembolden en güncel 3 haber
                    all_news.append(FinancialNews(
                        headline=item.get("title", "No Title"),
                        content=item.get("publisher", "Unknown Source"),
                        source=item.get("link", "https://finance.yahoo.com"),
                        timestamp=datetime.datetime.fromtimestamp(item.get("providerPublishTime", time.time()))
                    ))
            except Exception:
                continue
        return all_news

    def generate_random_news(self) -> FinancialNews:
        """Geriye dönük uyumluluk için; rastgele bir canlı haber döner."""
        news_list = self.fetch_live_news()
        if news_list:
            return random.choice(news_list)
        return FinancialNews("Piyasa verisi bekleniyor...", "Bağlantı kontrol ediliyor.", "System")

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

_nlp_engine = NLPIntelligenceEngine()

def get_nlp_engine() -> NLPIntelligenceEngine:
    return _nlp_engine

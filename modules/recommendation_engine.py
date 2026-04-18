"""
modules/recommendation_engine.py
AI Tabanlı Kredi Skoru İyileştirme Tavsiye Motoru
Müşterinin profiline göre kişiselleştirilmiş öneriler üretir.
"""

from config import DTI_LOW, DTI_MEDIUM, DTI_HIGH


class RecommendationEngine:
    """
    Her müşterinin kredi profilini analiz ederek
    kişiselleştirilmiş, önceliklendirilmiş tavsiyeler üretir.
    Tıpkı Credit Karma veya Experian'ın Boost gibi.
    """

    def generate(self, raw: dict, credit_score: float, risk_category: str) -> list[dict]:
        """
        Dönüş: [
            {"priority": 1, "category": str, "title": str, "desc": str,
             "impact": str, "effort": str, "icon": str}
        ]
        """
        recs = []
        income = max(raw.get("Aylik_Gelir", 1), 1)
        debt   = raw.get("Mevcut_Borc", 0)
        dti    = debt / income
        late   = raw.get("Gecikmis_Odeme_Sayisi", 0)
        cards  = raw.get("Kredi_Karti_Sayisi", 1)
        history = raw.get("Kredi_Gecmisi_Yili", 1)
        work   = raw.get("Calisma_Yili", 0)
        extra  = raw.get("Ek_Gelir", 0)
        age    = raw.get("Yas", 30)

        # ── 1. Gecikmiş Ödeme (Ağırlık %35) ──────────────────────
        if late >= 6:
            recs.append({
                "priority": 1,
                "category": "Ödeme Geçmişi",
                "icon":     "🔴",
                "title":    "Gecikmiş Ödemeleri Hemen Kapatın",
                "desc":     f"Sistemde {late} adet gecikmiş ödeme kaydınız var. Ödeme geçmişi, toplam skorunuzun %35'ini oluşturur ve şu an en büyük skor katilinizdir.",
                "impact":   "Çok Yüksek",
                "impact_score": "+80 ila +120 puan",
                "effort":   "Orta",
            })
        elif late >= 3:
            recs.append({
                "priority": 1,
                "category": "Ödeme Geçmişi",
                "icon":     "🟠",
                "title":    "Bekleyen Ödemeleri Tasfiye Edin",
                "desc":     f"{late} adet gecikmiş ödemenizi kapatmak skorunuzu önemli ölçüde artıracaktır. Tahsilat aşamasına gelmeden çözüme kavuşturun.",
                "impact":   "Yüksek",
                "impact_score": "+40 ila +70 puan",
                "effort":   "Orta",
            })
        elif late == 1 or late == 2:
            recs.append({
                "priority": 2,
                "category": "Ödeme Geçmişi",
                "icon":     "🟡",
                "title":    "Otomatik Ödeme Talimatı Kurun",
                "desc":     f"Küçük gecikmelerinizi önlemek için banka hesabınıza otomatik ödeme talimatı verin. Sıfır gecikme en hızlı skor artış yöntemidir.",
                "impact":   "Orta",
                "impact_score": "+20 ila +40 puan",
                "effort":   "Düşük",
            })

        # ── 2. Borç/Gelir Oranı (%30) ────────────────────────────
        if dti > DTI_HIGH:
            monthly_save_needed = (debt - income * DTI_MEDIUM) / 12
            recs.append({
                "priority": 1,
                "category": "Borç Yönetimi",
                "icon":     "🔴",
                "title":    "Borç Konsolidasyonu Yapın",
                "desc":     f"DTI oranınız %{dti*100:.0f} ile kritik seviyede. Hedef: %50 altı. Yüksek faizli borçlarınızı tek düşük faizli krediye çevirin. Aylık {monthly_save_needed:,.0f} TL borç azaltımı gerekiyor.",
                "impact":   "Çok Yüksek",
                "impact_score": "+60 ila +100 puan",
                "effort":   "Yüksek",
            })
        elif dti > DTI_MEDIUM:
            recs.append({
                "priority": 2,
                "category": "Borç Yönetimi",
                "icon":     "🟠",
                "title":    "Borç Azaltımı Planı Oluşturun",
                "desc":     f"DTI oranınız %{dti*100:.0f}. Düşük risk eşiği %35'tir. 6 ay içinde borcunuzu %15 azaltırsanız skorunuz belirgin artış gösterir.",
                "impact":   "Yüksek",
                "impact_score": "+30 ila +60 puan",
                "effort":   "Orta",
            })
        elif dti > DTI_LOW:
            recs.append({
                "priority": 3,
                "category": "Borç Yönetimi",
                "icon":     "🟡",
                "title":    "Gereksiz Harcamaları Kısın",
                "desc":     "DTI oranınız iyi seviyede ama hâlâ iyileştirme payı var. Aylık 1.000-2.000 TL fazladan borç ödemesi skoru hızla artırır.",
                "impact":   "Orta",
                "impact_score": "+15 ila +30 puan",
                "effort":   "Düşük",
            })

        # ── 3. Kredi Kartı Yönetimi (%10) ────────────────────────
        if cards > 6:
            recs.append({
                "priority": 2,
                "category": "Kredi Çeşitliliği",
                "icon":     "💳",
                "title":    "Atıl Kredi Kartlarını Kapatın",
                "desc":     f"{cards} kredi kartı aşırıya kaçıyor. 2-3 adet kaliteli kart, kredi çeşitliliği puanınızı optimize eder.",
                "impact":   "Orta",
                "impact_score": "+15 ila +25 puan",
                "effort":   "Düşük",
            })
        elif cards == 0:
            recs.append({
                "priority": 3,
                "category": "Kredi Çeşitliliği",
                "icon":     "💳",
                "title":    "İlk Kredi Kartınızı Edinin",
                "desc":     "Kredi kartı yoksa kredi geçmişi oluşturmanız imkânsız. Düşük limitli bir kart alın, her ay tam ödeyin.",
                "impact":   "Orta",
                "impact_score": "+20 ila +35 puan",
                "effort":   "Düşük",
            })

        # ── 4. Kredi Geçmişi Uzunluğu (%15) ─────────────────────
        if history < 2:
            recs.append({
                "priority": 3,
                "category": "Kredi Geçmişi",
                "icon":     "📅",
                "title":    "Eski Hesaplarınızı Kapatmayın",
                "desc":     "Kredi geçmişiniz oldukça kısa. Eski kartlarınızı ve hesaplarınızı açık tutun — geçmiş ne kadar uzun, skor o kadar yüksek.",
                "impact":   "Orta",
                "impact_score": "+10 ila +30 puan",
                "effort":   "Çok Düşük",
            })

        # ── 5. Gelir Artışı ──────────────────────────────────────
        if extra < income * 0.1:
            recs.append({
                "priority": 4,
                "category": "Gelir Artışı",
                "icon":     "💰",
                "title":    "Ek Gelir Kaynağı Ekleyin",
                "desc":     "Ek gelir (kira, serbest çalışma, yatırım temettüsü) hem DTI oranınızı iyileştirir hem de model gözünde güvenilirliğinizi artırır.",
                "impact":   "Orta",
                "impact_score": "+20 ila +45 puan",
                "effort":   "Yüksek",
            })

        # ── 6. İstihdam İstikrarı ────────────────────────────────
        if work < 2:
            recs.append({
                "priority": 3,
                "category": "İstihdam",
                "icon":     "💼",
                "title":    "İş İstikrarınızı Belgeleyin",
                "desc":     "2 yılın altındaki çalışma süresi risk faktörüdür. Mümkünse iş sözleşmenizi, terfinizi veya sektör sertifikalarınızı belgeleyin.",
                "impact":   "Düşük-Orta",
                "impact_score": "+10 ila +20 puan",
                "effort":   "Orta",
            })

        # ── 7. Yeni Kredi Başvurusu Uyarısı ─────────────────────
        recs.append({
            "priority": 5,
            "category": "Başvuru Stratejisi",
            "icon":     "🎯",
            "title":    "Çoklu Kredi Başvurusundan Kaçının",
            "desc":     "Kısa sürede birden fazla kredi başvurusu yapmak (hard inquiry) skorunuzu 5-10 puan düşürür. Başvuruları 6 ay arayla yapın.",
            "impact":   "Düşük",
            "impact_score": "-5 ila -15 puan (kaçınılırsa önlenir)",
            "effort":   "Çok Düşük",
        })

        # Önceliğe göre sırala
        recs.sort(key=lambda x: x["priority"])
        return recs

    def get_quick_wins(self, recs: list[dict]) -> list[dict]:
        """Düşük efor, yüksek etki olan tavsiyeleri döndürür."""
        return [r for r in recs if r.get("effort") in ("Düşük", "Çok Düşük") and r.get("priority") <= 3]

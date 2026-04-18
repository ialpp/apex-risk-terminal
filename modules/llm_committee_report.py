"""
modules/llm_committee_report.py
Otonom Kredi Komite Raporlayıcısı (RAG & LLM Simülasyonu)
Müşteri kredi skorlarını, açık bankacılık verilerini ve makro risk faktörlerini 
birleştirerek doğal dilde yönetim kurulu (komite) onayı için rapor hazırlar.
"""

import time
import random
from datetime import datetime

class LLMCommitteeReporter:
    """
    RAG (Retrieval-Augmented Generation) altyapısını simüle ederek 
    nümerik makine öğrenmesi çıktılarını resmi kurumsal metne çevirir.
    """
    
    def __init__(self):
        self.system_prompt = """
        Sen üst düzey bir kurumsal kredi risk analistisin. Müşterinin nicel verilerini (Quantitative Data) 
        analiz ederek, objektif, profesyonel ve resmi bir bankacılık diliyle Kredi Komitesine sunulmak 
        üzere tavsiye kararı hazırlamakla görevlisin.
        """
        
    def _generate_synthetic_embeddings_process(self):
        """Vektör aramasını simüle eder."""
        time.sleep(0.5) # Simulating DB fetch
        
    def generate_report(self, customer_name: str, credit_score: float, 
                        pd_prob: float, macro_risk_level: str, 
                        open_banking_flags: list, requested_amount: float) -> str:
        """
        Gelen parametrelere göre bir C-Level Kredi Komite Raporu (Markdown) sentezler.
        """
        self._generate_synthetic_embeddings_process()
        
        # Karar ağacı logic'i (LLM text reasoning simülasyonu)
        is_risky = pd_prob > 0.05 or macro_risk_level == "Adverse" or len(open_banking_flags) > 0
        decision = "ŞARTLI ONAY (CONDITIONAL APPROVAL)" if not is_risky else "RED (DECLINE)"
        if credit_score > 750 and pd_prob < 0.02 and macro_risk_level == "Base":
            decision = "KESİN ONAY (STRONG APPROVAL)"
            
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Metin blokları (Templates)
        intro = f"**Kredi Risk Komitesi Dikkatine**\n\n**Tarih:** {date_str}\n**Firma İşlem Kodu:** TX-{random.randint(1000,9999)}\n**Konu:** {customer_name} - {requested_amount:,.0f} ₺ Limit Tahsis Talebi Değerlendirmesi\n\n"
        
        body_1 = f"**1. Makine Öğrenmesi & Skorlama Katmanı:**\nModelimiz tarafından {customer_name} için hesaplanan Kredi Skoru **{credit_score:.1f}/1000** olarak belirlenmiştir. Merton (KMV) Yapısal Modeline dayalı zımni temerrüt olasılığı (PD) %{pd_prob*100:.2f} seviyesindedir. "
        if pd_prob < 0.03:
            body_1 += "Bu oran sektör ortalamalarının altında olup güçlü bir bilanço yapısına işaret etmektedir.\n\n"
        else:
            body_1 += "Bu oran, firmanın kısa vadeli asimetrik şoklara karşı hassas (vulnerable) durumda olduğunu göstermektedir.\n\n"
            
        body_2 = f"**2. Açık Bankacılık (Nakit Akışı) & NLP İncelemesi:**\nMüşterinin son 3 aylık hesap hareketleri Vektör Uzayında taranmış ve harcama profili çıkarılmıştır. "
        if not open_banking_flags:
            body_2 += "Nakit akışlarında şüpheli bir fon transferi, kumar veya kripto borsalarına anormal çıkış tespit edilmemiştir (Sıfır Bulgu).\n\n"
        else:
            body_2 += "Bununla birlikte, algoritma aşağıdaki yüksek riskli (Red Flag) işlem döngülerini tespit etmiştir:\n"
            for flag in open_banking_flags:
                body_2 += f"- *{flag}*\n"
            body_2 += "\n"
            
        body_3 = f"**3. Makro Ekonometrik Stres Testi Projeksiyonu:**\nMevcut makroekonomik modelimiz (**{macro_risk_level} Senaryo**) altında CDS ve faiz projeksiyonları değerlendirildiğinde, portföy Var (Value-at-Risk) korelasyonunun kontrol edilebilir seviyede kaldığı " if macro_risk_level != "Adverse" else f"**3. Makro Ekonometrik Stres Testi Projeksiyonu:**\nGlobal piyasalardaki **{macro_risk_level} (Kriz Dönemi)** senaryosu baz alındığında, likidite daralmasının söz konusu krediye ciddi bir Default baskısı yaratacağı "
        body_3 += "nicel (quantitative) olarak saptanmıştır.\n\n"
        
        body_4 = f"**4. Nihai Komite Kararı ve Tavsiyesi:**\nYapay Zeka Karar Motorumuz ve Risk Katmanlarımızın ortak sonucuna göre tahsis talebi için sistem çıktısı: **{decision}**.\n\n"
        
        if "RED" in decision:
            footer = "Ekonomik Sermaye maliyetinin beklenen kârlılığı (RAROC) karşılamaması ve nakit akışındaki anomaliler sebebiyle, başvurunun şimdilik beklemeye alınması (Decline) tavsiye edilir."
        elif "KESİN" in decision:
            footer = "Sınıfının en iyi pörtföyleri arasında yer alan bu müşterinin sadakatini sağlamak adına, rekabetçi (indirimli) bir spread ile derhal işleme alınması önerilir."
        else:
            footer = "Önerilen kredi onaylanabilir; ancak teminat (collateral) rasyosunun %20 oranında artırılması ve covenants (kredi sözleşme şartları) eklenmesi komitenin takdirine sunulur."
            
        full_report = intro + body_1 + body_2 + body_3 + body_4 + footer
        return full_report
        
llm_reporter = LLMCommitteeReporter()

"""
modules/pdf_report_generator.py
Kurumsal PDF Rapor Üretici — ReportLab tabanlı
Müşteri başına tam analiz raporu, portföy özet raporu üretir.
"""

import io
from datetime import datetime
from config import PDF_COMPANY_NAME, PDF_COMPANY_ADDR, PDF_REPORT_FOOTER, SCORE_BANDS

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


class PDFReportGenerator:
    """Kurumsal bankacılık standartlarında PDF raporları üretir."""

    # Kurumsal renk paleti
    PRIMARY   = colors.HexColor("#1e3a5f")
    ACCENT    = colors.HexColor("#3b82f6")
    SUCCESS   = colors.HexColor("#10b981")
    DANGER    = colors.HexColor("#ef4444")
    WARNING   = colors.HexColor("#f59e0b")
    LIGHT_BG  = colors.HexColor("#f8fafc")
    BORDER    = colors.HexColor("#e2e8f0")
    TEXT_MAIN = colors.HexColor("#1e293b")
    TEXT_MUTE = colors.HexColor("#64748b")

    def __init__(self):
        if not REPORTLAB_OK:
            raise ImportError("ReportLab kurulu değil. `pip install reportlab` ile kurun.")

    def _get_styles(self):
        styles = getSampleStyleSheet()
        custom = {
            "h1": ParagraphStyle("h1", parent=styles["Heading1"],
                                  fontSize=22, textColor=self.PRIMARY,
                                  spaceAfter=6, fontName="Helvetica-Bold"),
            "h2": ParagraphStyle("h2", parent=styles["Heading2"],
                                  fontSize=14, textColor=self.PRIMARY,
                                  spaceAfter=4, fontName="Helvetica-Bold"),
            "h3": ParagraphStyle("h3", parent=styles["Heading3"],
                                  fontSize=11, textColor=self.ACCENT,
                                  spaceAfter=3, fontName="Helvetica-Bold"),
            "body": ParagraphStyle("body", parent=styles["Normal"],
                                    fontSize=9, textColor=self.TEXT_MAIN,
                                    spaceAfter=4, leading=13),
            "muted": ParagraphStyle("muted", parent=styles["Normal"],
                                     fontSize=8, textColor=self.TEXT_MUTE,
                                     spaceAfter=2),
            "center": ParagraphStyle("center", parent=styles["Normal"],
                                      fontSize=9, alignment=TA_CENTER),
            "right": ParagraphStyle("right", parent=styles["Normal"],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=self.TEXT_MUTE),
        }
        return custom

    def _header_section(self, styles, report_type: str, report_no: str) -> list:
        """Ortak başlık bloğu."""
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        elements = [
            Paragraph(PDF_COMPANY_NAME, styles["h1"]),
            Paragraph(PDF_COMPANY_ADDR, styles["muted"]),
            HRFlowable(width="100%", thickness=2, color=self.PRIMARY, spaceAfter=8),
            Paragraph(report_type, styles["h2"]),
            Paragraph(f"Rapor No: {report_no} &nbsp;&nbsp;&nbsp; Tarih: {now}", styles["muted"]),
            Spacer(1, 0.3*cm),
        ]
        return elements

    def _footer_text(self) -> str:
        return PDF_REPORT_FOOTER

    def _score_color_rl(self, score: float):
        """Kredi skoruna göre ReportLab rengi döndürür."""
        for _, (low, high, hex_col) in SCORE_BANDS.items():
            if low <= score <= high:
                return colors.HexColor(hex_col)
        return self.DANGER

    # ──────────────────────────────────────────────────────────────
    #  MÜŞTERİ ANALİZ RAPORU
    # ──────────────────────────────────────────────────────────────

    def generate_customer_report(
        self,
        customer: dict,
        ml_result: dict,
        fraud_result: dict,
        recommendations: list,
        fico_breakdown: dict,
        generated_by: str = "Sistem"
    ) -> bytes:
        """
        Tek bir müşteri için kapsamlı PDF analiz raporu üretir.
        Dönüş: PDF bytes (Streamlit download_button'a verilebilir).
        """
        buf    = io.BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4,
                                    topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=2*cm, rightMargin=2*cm)
        styles = self._get_styles()
        report_no = f"CR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elements  = self._header_section(styles, "BİREYSEL KREDİ RİSK ANALİZ RAPORU", report_no)

        # ── Müşteri Kimlik Bilgileri ──────────────────────────────
        elements.append(Paragraph("1. Müşteri Kimlik Bilgileri", styles["h3"]))
        id_data = [
            ["Müşteri Kodu",  customer.get("customer_code", "—"),
             "Adı Soyadı",    customer.get("full_name", "—")],
            ["T.C. Kimlik",   "•••••" + str(customer.get("national_id", ""))[-4:],
             "Doğum Tarihi",  customer.get("birth_date", "—")],
            ["Telefon",       customer.get("phone", "—"),
             "E-posta",       customer.get("email", "—")],
            ["Şehir",         customer.get("city", "—"),
             "Meslek",        customer.get("occupation", "—")],
        ]
        id_table = Table(id_data, colWidths=[3*cm, 5.5*cm, 3*cm, 5.5*cm])
        id_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), self.LIGHT_BG),
            ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",   (2,0), (2,-1), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("GRID",       (0,0), (-1,-1), 0.5, self.BORDER),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, self.LIGHT_BG]),
            ("PADDING",    (0,0), (-1,-1), 5),
        ]))
        elements += [id_table, Spacer(1, 0.4*cm)]

        # ── Finansal Durum Özeti ─────────────────────────────────
        elements.append(Paragraph("2. Finansal Durum Özeti", styles["h3"]))
        income    = customer.get("monthly_income", 0)
        debt      = customer.get("total_debt", 0)
        dti       = (debt / income * 100) if income > 0 else 0
        fin_data = [
            ["Metrik",                  "Değer",          "Değerlendirme"],
            ["Aylık Gelir",             f"₺{income:,.0f}", "—"],
            ["Toplam Borç",             f"₺{debt:,.0f}",  "—"],
            ["Borç/Gelir Oranı (DTI)",  f"%{dti:.1f}",    "Kritik" if dti > 65 else "Yüksek" if dti > 50 else "Normal"],
            ["Gecikmiş Ödeme",          str(customer.get("late_payment_count", 0)) + " adet", "—"],
            ["Kredi Kartı Sayısı",      str(customer.get("credit_card_count", 0)) + " adet", "—"],
        ]
        fin_table = Table(fin_data, colWidths=[6*cm, 4*cm, 7*cm])
        fin_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), self.PRIMARY),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("GRID",          (0,0), (-1,-1), 0.5, self.BORDER),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, self.LIGHT_BG]),
            ("PADDING",       (0,0), (-1,-1), 6),
        ]))
        elements += [fin_table, Spacer(1, 0.4*cm)]

        # ── Kredi Skoru & FICO ───────────────────────────────────
        credit_score = ml_result.get("credit_score", 0)
        risk_cat     = ml_result.get("risk_category", "—")
        score_color  = self._score_color_rl(credit_score)

        elements.append(Paragraph("3. Kredi Skoru & FICO Analizi", styles["h3"]))
        score_summary = [
            ["KREDİ SKORU", f"{credit_score:.0f} / 850", "RİSK KATEGORİSİ", risk_cat],
            ["Onay Olasılığı", f"%{ml_result.get('approval_prob', 0)*100:.1f}",
             "Temerrüt Riski", f"%{ml_result.get('default_risk', 0)*100:.1f}"],
        ]
        ss_table = Table(score_summary, colWidths=[4*cm, 4*cm, 4*cm, 5*cm])
        ss_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (1,0), score_color),
            ("TEXTCOLOR",   (0,0), (1,0), colors.white),
            ("BACKGROUND",  (2,0), (3,0), self.PRIMARY),
            ("TEXTCOLOR",   (2,0), (3,0), colors.white),
            ("FONTNAME",    (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("GRID",        (0,0), (-1,-1), 0.5, self.BORDER),
            ("PADDING",     (0,0), (-1,-1), 8),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ]))
        elements += [ss_table, Spacer(1, 0.3*cm)]

        # FICO Kategorileri
        if fico_breakdown:
            fico_data = [["Kategori", "Puan", "Maks. Puan", "Ağırlık", "Oran"]]
            for cat, vals in fico_breakdown.items():
                sc  = vals["score"]
                mx  = vals["max"]
                pct = f"%{sc/mx*100:.0f}"
                fico_data.append([cat, str(sc), str(mx), vals["weight"], pct])
            fico_table = Table(fico_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2*cm, 5*cm])
            fico_table.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), self.ACCENT),
                ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("GRID",          (0,0), (-1,-1), 0.5, self.BORDER),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, self.LIGHT_BG]),
                ("PADDING",       (0,0), (-1,-1), 5),
                ("ALIGN",         (1,0), (-1,-1), "CENTER"),
            ]))
            elements += [fico_table, Spacer(1, 0.4*cm)]

        # ── Karar ────────────────────────────────────────────────
        elements.append(Paragraph("4. Sistem Kararı", styles["h3"]))
        approved = ml_result.get("approved", False)
        decision_color = self.SUCCESS if approved else self.DANGER
        decision_text  = "✓  ONAYLANDI" if approved else "✗  REDDEDİLDİ"
        dec_table = Table([[decision_text]], colWidths=[17*cm])
        dec_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), decision_color),
            ("TEXTCOLOR",  (0,0), (-1,-1), colors.white),
            ("FONTNAME",   (0,0), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 16),
            ("ALIGN",      (0,0), (-1,-1), "CENTER"),
            ("PADDING",    (0,0), (-1,-1), 12),
        ]))
        elements += [dec_table, Spacer(1, 0.4*cm)]

        # ── Sahtekarlık / Anomali ────────────────────────────────
        if fraud_result:
            elements.append(Paragraph("5. Sahtekarlık & Anomali Değerlendirmesi", styles["h3"]))
            fraud_score = fraud_result.get("fraud_score", 0)
            fraud_level = fraud_result.get("risk_level", "—")
            fraud_color = self.SUCCESS if fraud_score < 30 else (self.WARNING if fraud_score < 60 else self.DANGER)
            fr_data = [
                ["Sahtekarlık Skoru", f"{fraud_score}/100"],
                ["Risk Seviyesi",     fraud_level],
                ["Anomali Tespit",    "Evet" if fraud_result.get("anomaly") else "Hayır"],
            ]
            fr_table = Table(fr_data, colWidths=[6*cm, 11*cm])
            fr_table.setStyle(TableStyle([
                ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
                ("BACKGROUND",    (1,0), (1,0), fraud_color),
                ("TEXTCOLOR",     (1,0), (1,0), colors.white),
                ("FONTSIZE",      (0,0), (-1,-1), 9),
                ("GRID",          (0,0), (-1,-1), 0.5, self.BORDER),
                ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, self.LIGHT_BG]),
                ("PADDING",       (0,0), (-1,-1), 6),
            ]))
            flags = fraud_result.get("flags", [])
            if flags:
                fr_flags = Table(
                    [[f] for f in flags],
                    colWidths=[17*cm]
                )
                fr_flags.setStyle(TableStyle([
                    ("BACKGROUND",  (0,0), (-1,-1), colors.HexColor("#fff7ed")),
                    ("FONTSIZE",    (0,0), (-1,-1), 8),
                    ("TEXTCOLOR",   (0,0), (-1,-1), self.TEXT_MAIN),
                    ("GRID",        (0,0), (-1,-1), 0.3, self.BORDER),
                    ("PADDING",     (0,0), (-1,-1), 5),
                ]))
                elements += [fr_table, Spacer(1, 0.2*cm), fr_flags, Spacer(1, 0.4*cm)]
            else:
                elements += [fr_table, Spacer(1, 0.4*cm)]

        # ── Tavsiyeler ───────────────────────────────────────────
        if recommendations:
            elements.append(Paragraph("6. AI Tabanlı İyileştirme Tavsiyeleri", styles["h3"]))
            for i, rec in enumerate(recommendations[:6], 1):
                rec_text = f"<b>{i}. {rec.get('icon','')} {rec.get('title','')}</b> — {rec.get('desc','')} [{rec.get('impact_score','')}]"
                elements.append(Paragraph(rec_text, styles["body"]))

        # ── Footer ───────────────────────────────────────────────
        elements += [
            Spacer(1, 0.6*cm),
            HRFlowable(width="100%", thickness=1, color=self.BORDER),
            Paragraph(f"Raporu Oluşturan: {generated_by} &nbsp;|&nbsp; {self._footer_text()}", styles["muted"]),
        ]

        doc.build(elements)
        buf.seek(0)
        return buf.read()

    # ──────────────────────────────────────────────────────────────
    #  PORTFÖY ÖZET RAPORU
    # ──────────────────────────────────────────────────────────────

    def generate_portfolio_report(self, stats: dict, generated_by: str = "Sistem") -> bytes:
        """Tüm portföy için özet istatistik raporu."""
        buf    = io.BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4,
                                    topMargin=2*cm, bottomMargin=2*cm,
                                    leftMargin=2*cm, rightMargin=2*cm)
        styles = self._get_styles()
        report_no = f"PR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        elements  = self._header_section(styles, "PORTFÖY ÖZET RAPORU", report_no)

        # KPI Tablosu
        kpi_data = [
            ["Toplam Aktif Müşteri",   str(stats.get("total_customers", 0))],
            ["Ortalama Kredi Skoru",   f"{stats.get('avg_score', 0):.1f}"],
            ["Genel Onay Oranı",       f"%{stats.get('approval_rate', 0):.1f}"],
            ["Toplam Onaylanan Tutar", f"₺{stats.get('total_portfolio', 0):,.0f}"],
            ["Bekleyen Başvurular",    str(stats.get("pending_applications", 0))],
            ["Aktif Uyarılar",         str(stats.get("active_warnings", 0))],
        ]
        kpi_table = Table(kpi_data, colWidths=[9*cm, 8*cm])
        kpi_table.setStyle(TableStyle([
            ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 10),
            ("GRID",          (0,0), (-1,-1), 0.5, self.BORDER),
            ("ROWBACKGROUNDS",(0,0), (-1,-1), [colors.white, self.LIGHT_BG]),
            ("PADDING",       (0,0), (-1,-1), 8),
            ("ALIGN",         (1,0), (1,-1), "CENTER"),
        ]))
        elements += [kpi_table, Spacer(1, 0.4*cm)]

        # Risk Dağılımı
        risk_dist = stats.get("risk_distribution", {})
        if risk_dist:
            elements.append(Paragraph("Risk Kategorisi Dağılımı", styles["h3"]))
            rd_data = [["Kategori", "Müşteri Sayısı"]]
            for cat, cnt in risk_dist.items():
                rd_data.append([cat, str(cnt)])
            rd_table = Table(rd_data, colWidths=[9*cm, 8*cm])
            rd_table.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), self.PRIMARY),
                ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 9),
                ("GRID",          (0,0), (-1,-1), 0.5, self.BORDER),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, self.LIGHT_BG]),
                ("PADDING",       (0,0), (-1,-1), 6),
            ]))
            elements += [rd_table, Spacer(1, 0.4*cm)]

        elements += [
            Spacer(1, 0.6*cm),
            HRFlowable(width="100%", thickness=1, color=self.BORDER),
            Paragraph(f"Raporu Oluşturan: {generated_by} &nbsp;|&nbsp; {self._footer_text()}", styles["muted"]),
        ]
        doc.build(elements)
        buf.seek(0)
        return buf.read()

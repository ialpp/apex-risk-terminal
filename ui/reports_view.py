import re
"""
ui/reports_view.py
Raporlama Merkezi — PDF, Excel, Portföy Özeti
"""

import streamlit as st
import pandas as pd
import io
from core.database_handler import db
from config import APP_NAME


def render_reports_view(pdf_gen, user_info: dict):
    st.title("📄 Raporlama Merkezi")
    st.markdown("<p style='color:#64748b;'>Kurumsal PDF raporları, Excel çıktıları ve portföy özetleri üretin.</p>", unsafe_allow_html=True)

    tab_pdf, tab_excel, tab_summary = st.tabs([
        "📋 Müşteri PDF Raporu", "📊 Excel Dışa Aktarım", "📈 Portföy Özeti"
    ])

    with tab_pdf:
        _render_pdf_section(pdf_gen, user_info)

    with tab_excel:
        _render_excel_section()

    with tab_summary:
        _render_summary_section(pdf_gen, user_info)


def _render_pdf_section(pdf_gen, user_info: dict):
    st.subheader("Bireysel Müşteri Analiz Raporu (PDF)")
    customers = db.get_all_customers()
    if customers.empty:
        st.info("Portföyde müşteri bulunmuyor.")
        return

    customer_options = {
        f"{row['customer_code']} — {row['full_name']}": row['customer_code']
        for _, row in customers.iterrows()
    }
    selected_label = st.selectbox("Müşteri Seç", list(customer_options.keys()))

    if st.button("📋 PDF Raporu Oluştur", type="primary"):
        code = customer_options[selected_label]
        customer = db.get_customer_by_code(code)
        if not customer:
            st.error("Müşteri bulunamadı.")
            return

        # Boş ML ve fraud sonuçları (Rapor için temel veriler kullanılır)
        ml_stub = {
            "approved": (customer.get("risk_category") not in ["Zayıf", "Orta"]),
            "approval_prob": 0.65,
            "default_risk": 0.35,
            "credit_score": customer.get("credit_score") or 580,
            "risk_category": customer.get("risk_category") or "Bilinmiyor",
        }
        fraud_stub = {"fraud_score": 15, "risk_level": "Düşük", "anomaly": False, "flags": []}

        try:
            with st.spinner("PDF üretiliyor..."):
                pdf_bytes = pdf_gen.generate_customer_report(
                    customer=customer,
                    ml_result=ml_stub,
                    fraud_result=fraud_stub,
                    recommendations=[],
                    fico_breakdown={},
                    generated_by=user_info["username"]
                )
            st.download_button(
                "⬇️ PDF'i İndir",
                data=pdf_bytes,
                file_name=f"kredi_raporu_{code}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("✅ PDF hazırlandı.")
        except ImportError as e:
            st.error(f"ReportLab kurulu değil: {e}\n\n`pip install reportlab` çalıştırın.")
        except Exception as e:
            st.error(f"PDF üretim hatası: {e}")


def _render_excel_section():
    st.subheader("Excel / CSV Dışa Aktarım")

    export_options = st.multiselect(
        "Hangi veriler dahil edilsin?",
        ["Müşteri Listesi", "Analiz Logları", "Aktif Uyarılar"],
        default=["Müşteri Listesi"]
    )

    if st.button("📊 Excel Dosyası Oluştur", type="primary"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            if "Müşteri Listesi" in export_options:
                df = db.get_all_customers()
                if not df.empty:
                    df.to_excel(writer, sheet_name="Müşteriler", index=False)

            if "Analiz Logları" in export_options:
                df = db.get_recent_logs(limit=500)
                if not df.empty:
                    df.to_excel(writer, sheet_name="Analiz Logları", index=False)

            if "Aktif Uyarılar" in export_options:
                df = db.get_active_warnings()
                if not df.empty:
                    df.to_excel(writer, sheet_name="Uyarılar", index=False)

        output.seek(0)
        st.download_button(
            "⬇️ Excel Dosyasını İndir",
            data=output.read(),
            file_name="portfoy_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.success("✅ Excel hazırlandı.")


def _render_summary_section(pdf_gen, user_info: dict):
    st.subheader("Portföy Özet Raporu")
    stats = db.get_portfolio_stats()

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Müşteri",    f"{stats['total_customers']:,}")
    c2.metric("Ort. Kredi Skoru",  f"{stats['avg_score']:.1f}")
    c3.metric("Onay Oranı",        f"%{stats['approval_rate']:.1f}")

    if st.button("📋 Portföy PDF Raporu Oluştur", type="primary"):
        try:
            with st.spinner("Portföy raporu üretiliyor..."):
                pdf_bytes = pdf_gen.generate_portfolio_report(stats, user_info["username"])
            st.download_button(
                "⬇️ PDF'i İndir",
                data=pdf_bytes,
                file_name="portfoy_ozet_raporu.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except ImportError as e:
            st.error(f"ReportLab kurulu değil: {e}")
        except Exception as e:
            st.error(f"PDF hatası: {e}")

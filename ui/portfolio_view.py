import re
"""
ui/portfolio_view.py
Portföy Yönetim Paneli
Müşteri arama, kart/tablo görünümü, toplu CSV import, etiketleme
"""

import streamlit as st
import pandas as pd
import io
from core.database_handler import db
from config import SCORE_BANDS


def render_portfolio_view(user_info: dict):
    st.title("🗃️ Portföy Yönetimi")
    st.markdown("<p style='color:#64748b;'>Tüm müşteri kayıtlarını görüntüleyin, arayın, filtreleyin veya toplu olarak içe aktarın.</p>", unsafe_allow_html=True)

    tab_list, tab_import, tab_add = st.tabs([
        "📋 Müşteri Listesi", "📥 Toplu İçe Aktar (CSV)", "➕ Tekil Müşteri Ekle"
    ])

    with tab_list:
        _render_customer_list(user_info)

    with tab_import:
        _render_bulk_import(user_info)

    with tab_add:
        _render_add_customer_form(user_info)


def _render_customer_list(user_info: dict):
    # Arama & Filtreler
    col_search, col_filter_risk, col_filter_seg = st.columns([2, 1, 1])
    with col_search:
        query = st.text_input("🔍 Ara (İsim, Kod, TC, E-posta)",
                               placeholder="Müşteri adı veya kodu...")
    with col_filter_risk:
        risk_filter = st.selectbox("Risk Kategorisi", ["Tümü"] + list(SCORE_BANDS.keys()))
    with col_filter_seg:
        view_mode = st.radio("Görünüm", ["📋 Tablo", "🃏 Kart"], horizontal=True)

    # Veri çek
    if query:
        df = db.search_customers(query)
    else:
        df = db.get_all_customers()

    if df.empty:
        st.info("Henüz portföyde müşteri bulunmuyor.")
        return

    # Risk filtresi
    if risk_filter != "Tümü" and "risk_category" in df.columns:
        df = df[df["risk_category"] == risk_filter]

    st.caption(f"**{len(df)} müşteri** listeleniyor.")

    if "Tablo" in view_mode:
        _render_table_view(df)
    else:
        _render_card_view(df)


def _render_table_view(df: pd.DataFrame):
    show_cols = [
        "customer_code", "full_name", "city", "occupation",
        "monthly_income", "total_debt", "credit_score",
        "risk_category", "segment", "late_payment_count"
    ]
    show_cols = [c for c in show_cols if c in df.columns]
    df_show   = df[show_cols].copy()

    rename_map = {
        "customer_code":     "Kod",
        "full_name":         "Ad Soyad",
        "city":              "Şehir",
        "occupation":        "Meslek",
        "monthly_income":    "Aylık Gelir ₺",
        "total_debt":        "Toplam Borç ₺",
        "credit_score":      "Kredi Skoru",
        "risk_category":     "Risk",
        "segment":           "Segment",
        "late_payment_count":"Gecikme",
    }
    df_show = df_show.rename(columns=rename_map)

    if "Aylık Gelir ₺" in df_show.columns:
        df_show["Aylık Gelir ₺"] = df_show["Aylık Gelir ₺"].map("₺{:,.0f}".format)
    if "Toplam Borç ₺" in df_show.columns:
        df_show["Toplam Borç ₺"] = df_show["Toplam Borç ₺"].map("₺{:,.0f}".format)
    if "Kredi Skoru" in df_show.columns:
        df_show["Kredi Skoru"] = df_show["Kredi Skoru"].map(
            lambda x: f"{x:.0f}" if pd.notna(x) else "—"
        )

    st.dataframe(df_show, use_container_width=True, hide_index=True, height=480)

    # CSV İndirme
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Portföyü CSV Olarak İndir",
        data=csv_bytes,
        file_name="portfoy_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


def _render_card_view(df: pd.DataFrame):
    # 3'lü grid kart görünümü
    cols = st.columns(3)
    for idx, (_, row) in enumerate(df.head(30).iterrows()):
        score = row.get("credit_score")
        risk  = row.get("risk_category", "—")
        seg   = row.get("segment", "—")

        # Renk
        score_color = "#64748b"
        if score:
            for cat, (lo, hi, col) in SCORE_BANDS.items():
                if lo <= float(score) <= hi:
                    score_color = col
                    break

        income = row.get("monthly_income", 0) or 0
        debt   = row.get("total_debt", 0) or 0
        late   = row.get("late_payment_count", 0) or 0

        with cols[idx % 3]:
            st.markdown(f"""
            <div class="pq-card" style="border-left:4px solid {score_color};">
              <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                  <div style="font-weight:800; font-size:1rem; color:#f8fafc;">
                    {row.get('full_name','—')}
                  </div>
                  <div style="font-size:0.75rem; color:#64748b;">
                    {row.get('customer_code','—')} · {row.get('city','—')}
                  </div>
                </div>
                <div style="font-size:1.5rem; font-weight:900; color:{score_color};">
                  {f"{score:.0f}" if score else "—"}
                </div>
              </div>
              <div style="margin-top:0.8rem; display:grid; grid-template-columns:1fr 1fr;
                          gap:0.4rem; font-size:0.78rem; color:#94a3b8;">
                <div>💰 ₺{income:,.0f}/ay</div>
                <div>💳 {row.get('credit_card_count',0)} kart</div>
                <div>🏦 ₺{debt:,.0f} borç</div>
                <div>⚠️ {late} gecikme</div>
              </div>
              <div style="margin-top:0.6rem; font-size:0.73rem;">
                <span style="background:{score_color}22; color:{score_color};
                             padding:2px 8px; border-radius:20px; font-weight:600;">
                  {risk}
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)


def _render_bulk_import(user_info: dict):
    st.subheader("📥 CSV/Excel ile Toplu Müşteri Yükleme")
    st.markdown("""
    Aşağıdaki kolon isimleriyle bir CSV veya Excel dosyası oluşturun ve yükleyin:

    | Zorunlu Kolonlar | Açıklama |
    |---|---|
    | `full_name` | Müşteri adı soyadı |
    | `monthly_income` | Aylık gelir (TL) |
    | `total_debt` | Toplam borç (TL) |
    | `late_payment_count` | Gecikmiş ödeme sayısı |
    | `credit_card_count` | Kredi kartı sayısı |

    **Opsiyonel:** `age`, `city`, `occupation`, `email`, `phone`, `credit_history_years`
    """)

    uploaded_file = st.file_uploader(
        "Dosyayı seçin (CSV veya Excel)",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                import_df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
            else:
                import_df = pd.read_excel(uploaded_file)

            st.success(f"✅ Dosya okundu: **{len(import_df)} satır** bulundu.")
            st.dataframe(import_df.head(10), use_container_width=True)

            if st.button("💾 Portföye Aktar", type="primary", use_container_width=True):
                with st.spinner("Müşteriler sisteme işleniyor..."):
                    count = db.import_customers_from_df(import_df, user_info["username"])
                st.success(f"✅ {count} müşteri başarıyla portföye eklendi.")
        except Exception as e:
            st.error(f"Dosya okuma hatası: {e}")

    # Şablon İndirme
    sample = pd.DataFrame({
        "full_name":           ["Ahmet Yılmaz", "Zeynep Kaya"],
        "age":                 [35, 28],
        "monthly_income":      [25000, 18000],
        "total_debt":          [10000, 5000],
        "late_payment_count":  [0, 1],
        "credit_card_count":   [2, 1],
        "credit_history_years":[5.0, 2.5],
        "city":                ["İstanbul", "Ankara"],
        "occupation":          ["Mühendis", "Öğretmen"],
    })
    csv_template = sample.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📄 CSV Şablonunu İndir",
        data=csv_template,
        file_name="musteri_sablonu.csv",
        mime="text/csv"
    )


def _render_add_customer_form(user_info: dict):
    st.subheader("➕ Yeni Müşteri Kaydı")
    with st.form("add_customer_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Ad Soyad *")
            national_id = st.text_input("TC Kimlik No")
            birth_date  = st.text_input("Doğum Tarihi (GG.AA.YYYY)")
            phone = st.text_input("Telefon")
            email = st.text_input("E-posta")
        with c2:
            city = st.selectbox("Şehir", ["İstanbul","Ankara","İzmir","Bursa","Diğer"])
            occupation = st.text_input("Meslek")
            employer   = st.text_input("İşveren / Şirket")
            monthly_income = st.number_input("Aylık Gelir (TL) *", 5500, 500000, 20000)
            total_debt     = st.number_input("Toplam Borç (TL)", 0, 5000000, 0)

        c3, c4, c5 = st.columns(3)
        with c3:
            late_payment_count   = st.number_input("Gecikmiş Ödeme", 0, 24, 0)
            credit_card_count    = st.number_input("Kredi Kartı Sayısı", 0, 15, 1)
        with c4:
            employment_years     = st.number_input("Çalışma Süresi (Yıl)", 0.0, 45.0, 2.0)
            credit_history_years = st.number_input("Kredi Geçmişi (Yıl)", 0.0, 40.0, 1.0)
        with c5:
            home_ownership = st.selectbox("Konut Durumu", ["Kiracı","Ev Sahibi","Aile Yanı"])
            education_level = st.selectbox("Eğitim", ["Lise","Ön Lisans","Lisans","Y.Lisans","Doktora"])

        notes = st.text_area("Notlar")
        submitted = st.form_submit_button("Müşteriyi Sisteme Kaydet", use_container_width=True)

    if submitted:
        if not full_name or not monthly_income:
            st.warning("Ad Soyad ve Aylık Gelir zorunludur.")
            return
        data = {
            "full_name":            full_name.strip(),
            "national_id":          national_id or None,
            "birth_date":           birth_date or None,
            "age":                  None,
            "phone":                phone or None,
            "email":                email or None,
            "address":              None,
            "city":                 city,
            "occupation":           occupation or None,
            "employer":             employer or None,
            "employment_years":     float(employment_years),
            "monthly_income":       float(monthly_income),
            "additional_income":    0,
            "total_debt":           float(total_debt),
            "credit_card_count":    int(credit_card_count),
            "late_payment_count":   int(late_payment_count),
            "credit_history_years": float(credit_history_years),
            "home_ownership":       home_ownership,
            "monthly_expenses":     0,
            "dependents":           0,
            "education_level":      education_level,
            "assigned_analyst":     user_info["username"],
            "notes":               notes or "",
        }
        try:
            code = db.add_customer(data)
            st.success(f"✅ Müşteri sisteme kaydedildi. Müşteri Kodu: **{code}**")
        except Exception as e:
            st.error(f"Kayıt hatası: {e}")

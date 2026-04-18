import re
"""
ui/views/pricing_dashboard.py
Yüksek Düzey Kârlılık (RAROC) ve Açık Bankacılık Risk Simülatörü Arayüzü
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from modules.quantitative_pricing import pricing_engine
from modules.open_banking_api import open_banking_api
from core.database_handler import db

def render_pricing_scenarios(user_info: dict):
    st.title("🛡️ Kurumsal Risk Fiyatlama & RAROC Kokpiti")
    st.markdown("""
    <p style='color:#64748b; margin-top:-0.5rem;'>
      Bu alanda Merton KMV Opsiyon Fiyatlama teorisi ve Open Banking NLP katmanı ile 
      kredi senaryolarının bankaya <b>net özsermaye kârlılığını (RAROC)</b> hesaplayabilirsiniz.
    </p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    tab_pricing, tab_open_banking = st.tabs(["📊 RAROC Fiyatlama Simülatörü", "🏦 Açık Bankacılık (NLP)"])
    
    with tab_pricing:
        _render_raroc_simulator(user_info)
        
    with tab_open_banking:
        _render_open_banking_layer(user_info)


def _render_raroc_simulator(user_info):
    c1, c2 = st.columns([1, 2])
    
    # Kredi Parametreleri
    with c1:
        st.subheader("Simülasyon Parametreleri")
        with st.form("raroc_form"):
            loan_amount = st.number_input("Kredi Tutarı (TL)", min_value=10000, max_value=50000000, value=250000, step=10000)
            interest_rate = st.slider("Müşteriye Sunulan Faiz Oranı (%)", min_value=2.0, max_value=40.0, value=12.0, step=0.5) / 100.0
            pd_prob = st.slider("Kurumsal Temerrüt Olasılığı (PD %)", min_value=0.1, max_value=100.0, value=3.5, step=0.1) / 100.0
            lgd_prob = st.slider("Kayıp Beklentisi (LGD %)", min_value=10.0, max_value=100.0, value=45.0) / 100.0
            
            submit = st.form_submit_button("Matematiksel Modeli Çalıştır 🚀")
            
    with c2:
        st.subheader("Risk-Adjusted Return On Capital (RAROC) Sonuçları")
        if submit:
            results = pricing_engine.calculate_raroc(
                loan_amount=loan_amount,
                interest_rate=interest_rate,
                pd_prob=pd_prob,
                lgd_prob=lgd_prob
            )
            
            r_col1, r_col2, r_col3 = st.columns(3)
            r_col1.metric("Beklenen Kayıp (EL)", f"{results['expected_loss']:,.0f} TL")
            r_col2.metric("Ekonomik Sermaye", f"{results['economic_capital']:,.0f} TL", 
                          help="Beklenmeyen zararlara karşı bankanın bloke etmesi gereken Basel sermayesi")
            r_col3.metric("RAROC Oranı", f"%{results['raroc_percentage']:.2f}",
                          delta=f"Hedef: %{results['target_roe']:.0f}",
                          delta_color="normal" if results["raroc_percentage"] >= results["target_roe"] else "inverse")
            
            theme = st.session_state.get('theme', 'dark')
            card_bg = "rgba(15,23,42,0.6)" if theme == "dark" else "rgba(255,255,255,0.85)"
            text_color = "#f8fafc" if theme == "dark" else "#1e293b"
            
            dec_color = "#10b981" if "ONAY" in results["decision"] else "#ef4444"
            st.markdown(f"""
            <div style="background:{card_bg}; padding:1rem; border-radius:10px; border-left:5px solid {dec_color}; margin-top:1rem;">
                <h4 style="color:{text_color}; margin:0;">Kurul Önerisi: {results['decision']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Grafikler
            st.markdown("##### Gelir Dağılımı")
            fig = px.pie(
                values=[results['expected_loss'], results['economic_capital'], max(0, results['interest_income']-results['expected_loss'])], 
                names=['Beklenen Kayıp', 'Bloke Edilen Sermaye', 'Net Kâr Katkısı'],
                hole=0.4,
                color_discrete_sequence=['#ef4444', '#f59e0b', '#10b981']
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sol taraftan parametreleri girip modeli çalıştırınız.")

def _render_open_banking_layer(user_info):
    st.subheader("NLP Destekli Nakit Akışı Haritalandırması")
    st.markdown("Veritabanına kayıtlı olmayan harcamalar banka API simülatörü üzerinden okunup yapay zeka tarafından parse edilir.")
    
    col1, col2 = st.columns([1, 1])
    sim_id = col1.number_input("Müşteri ID (Simülasyon Seed)", min_value=1, value=101)
    
    if col1.button("💳 Bankacılık Ekstresini Çek & Analiz Et"):
        with st.spinner("Bankalarla haberleşiliyor ve işlemler parse ediliyor..."):
            df_tx = open_banking_api.fetch_synthetic_transactions(customer_id=sim_id, months_back=3)
            analysis = open_banking_api.analyze_account_health(df_tx)
            
            if analysis.get("warning_flags"):
                for flag in analysis["warning_flags"]:
                    st.error(flag)
            else:
                st.success("✅ Riskli harcama deseni tespit edilmedi.")
                
            c_a, c_b, c_c = st.columns(3)
            c_a.metric("Toplam Nakit Girişi (3 Ay)", f"{analysis['total_income_3m']:,.0f} TL")
            c_b.metric("Toplam Nakit Çıkışı (3 Ay)", f"{analysis['total_spent_3m']:,.0f} TL")
            c_c.metric("Yüksek Riskli Oran", f"%{analysis['high_risk_ratio']:.1f}", delta_color="inverse")
            
            st.markdown("### Harcama Sınıflandırma Profili (NLP Sonucu)")
            
            cat_df = pd.DataFrame(list(analysis['category_breakdown'].items()), columns=['Kategori', 'Tutar'])
            fig = px.bar(cat_df, x='Kategori', y='Tutar', text_auto='.2s', title="Kategori Bazlı Tüketim")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Ham İşlem Geçmişi")
            st.dataframe(df_tx.head(20), use_container_width=True)

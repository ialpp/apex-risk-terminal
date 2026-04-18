import re
"""
ui/views/committee_rag_dashboard.py
Otonom Kredi Komite Raporlayıcısı (RAG) Arayüzü
"""

import streamlit as st
import time
from modules.llm_committee_report import llm_reporter
from modules.open_banking_api import open_banking_api
from core.database_handler import db

def render_rag_committee_dashboard(user_info: dict):
    st.title("🧠 Otonom Kredi Komitesi (GenAI & RAG)")
    st.markdown("""
    <p style='color:#64748b; margin-top:-0.5rem;'>
      Bu katman; veri tabanındaki makine öğrenmesi skorlarını, açık bankacılık loglarını ve 
      makroekonomik kriz beklentilerini okuyarak <b>Üretken Yapay Zeka (LLM)</b> altyapısıyla 
      yönetim kurulu onay metinleri hazırlar.
    </p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("RAG Prompt Parametreleri")
        with st.form("rag_form"):
            customer_name = st.text_input("Görüşülecek Firma/Müşteri Ünvanı", value="DemirÇelik San. A.Ş.")
            requested_amount = st.number_input("Talep Edilen Kredi (TL)", min_value=10000, value=1500000, step=50000)
            
            st.markdown("Veri Kaynakları Ağırlığı (Vector Search)")
            credit_score = st.slider("Firmaya Ait ML Skoru (1000 Üzerinden)", 300, 1000, 680)
            pd_prob = st.slider("Temerrüt Olasılığı (PD %)", 0.1, 20.0, 4.5) / 100.0
            
            macro_level = st.selectbox("Mevcut Makro Konjonktür", ["Optimistic", "Base", "Adverse"])
            
            simulate_flags = st.checkbox("Açık Bankacılıkta Kırmızı Bayraklar (Red Flags) Var mı?", value=False)
            
            submit = st.form_submit_button("🤖 Otonom Raporu Sentezle")
            
    with c2:
        st.subheader("Kurumsal Karar Metni (LLM Çıktısı)")
        
        if submit:
            with st.spinner("Vektör veri tabanı taranıyor... Rapor sentezleniyor..."):
                flags = []
                if simulate_flags:
                    from modules.open_banking_api import open_banking_api
                    # Sadece test etmek için dummy flags basıyoruz, open_banking modülünden çekmiyoruz çünkü spesifik format lazım
                    flags = [
                        "🚨 İşlemlerin %15'in den fazlası Yüksek Riskli/Kripto/Nakit Avans segmentinde!",
                        "⚠️ Son 3 ayda harcamalar, gelen net transferi %50 oranında aşıyor."
                    ]
                
                # Sentez fonksiyonuna yolla
                final_report_md = llm_reporter.generate_report(
                    customer_name=customer_name,
                    credit_score=credit_score,
                    pd_prob=pd_prob,
                    macro_risk_level=macro_level,
                    open_banking_flags=flags,
                    requested_amount=requested_amount
                )
                
                # Streaming effect simulator
                message_placeholder = st.empty()
                streamed_text = ""
                # Chunk size for streaming effect
                chunk_size = 4
                for i in range(0, len(final_report_md), chunk_size):
                    chunk = final_report_md[i:i+chunk_size]
                    streamed_text += chunk
                    message_placeholder.markdown(
                        f"""
                        <div style='background:rgba(15,23,42,0.5); padding:2rem; border-radius:10px; 
                        border: 1px solid rgba(255,255,255,0.1); 
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'>
                        {streamed_text}▌
                        </div>
                        """, unsafe_allow_html=True
                    )
                    time.sleep(0.01)
                    
                # Final text (remove cursor)
                message_placeholder.markdown(
                    f"""
                    <div style='background:rgba(15,23,42,0.5); padding:2rem; border-radius:10px; 
                    border: 1px solid rgba(255,255,255,0.1); 
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'>
                    {streamed_text}
                    </div>
                    """, unsafe_allow_html=True
                )
                
                st.download_button(
                    label="📄 Raporu Kaydet (MD)",
                    data=streamed_text,
                    file_name=f"Komite_Karari_{customer_name.replace(' ', '_')}.md",
                    mime="text/markdown"
                )
        else:
            st.info("Sol taraftan parametreleri ayarlayarak Yapay Zekaya rapor yazma komutu verebilirsiniz.")


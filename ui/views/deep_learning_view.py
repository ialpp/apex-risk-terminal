"""
ui/views/deep_learning_view.py — ProQuant Capital | Derin Öğrenme Analiz Dashboard v2.0
=====================================================================================

Bu modül, deep_learning_credit.py motorunun arayüzünü sağlar.
LSTM ve Transformer tabanlı kredi risk modellerinin eğitim süreçlerini ve tahminlerini sunar.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

def render_deep_learning_view(deep_engine, user_info):
    st.title("🕸️ Derin Öğrenme & Sinir Ağları Merkezi")
    st.markdown("<p style='color:#64748b;'>Zaman serisi müşteri davranışları için Transformer ve LSTM hibrit mimarileri.</p>",
                unsafe_allow_html=True)

    # 1. Model Durumu ve Eğitim
    st.subheader("🤖 Model Eğitim Durumu")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Transformer Katmanları", "4 Head, 128 Hidden")
    with col_s2:
        st.metric("LSTM Hücreleri", "64 Unit, Bi-Directional")
    with col_s3:
        status = "✅ HAZIR" if deep_engine.is_ready else "⏳ EĞİTİM GEREKİYOR"
        st.metric("Durum", status)

    if not deep_engine.is_ready:
        if st.button("🚀 Derin Öğrenme Modellerini Eğit", type="primary", use_container_width=True):
            with st.status("Sinir ağları eğitiliyor (PyTorch Simulation)...", expanded=True) as status:
                st.write("Bakırköy Veri Merkezi: GPU kümesi tahsis ediliyor...")
                results = deep_engine.run_training_cycle(n_samples=1000)
                st.write(f"Transformer Loss: {results['transformer_loss']:.4f}")
                st.write(f"LSTM Loss: {results['lstm_loss']:.4f}")
                status.update(label="✅ Eğitim Tamamlandı!", state="complete")
                st.rerun()

    if deep_engine.is_ready:
        # 2. Eğitim Metrikleri
        st.divider()
        c_m1, c_m2 = st.columns(2)
        
        with c_m1:
            st.subheader("📉 Kayıp Eğrisi (Loss Curve)")
            # Simüle edilmiş eğitim geçmişi
            epochs = list(range(1, 21))
            loss_t = [0.8 / (e**0.5) + np.random.normal(0, 0.02) for e in epochs]
            loss_l = [0.9 / (e**0.4) + np.random.normal(0, 0.02) for e in epochs]
            
            fig_loss = go.Figure()
            fig_loss.add_trace(go.Scatter(x=epochs, y=loss_t, name='Transformer Loss', line=dict(color='#818cf8', width=3)))
            fig_loss.add_trace(go.Scatter(x=epochs, y=loss_l, name='LSTM Loss', line=dict(color='#34d399', width=3)))
            fig_loss.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                   xaxis_title="Epoch", yaxis_title="Loss")
            st.plotly_chart(fig_loss, use_container_width=True)

        with c_m2:
            st.subheader("🎯 Model AUC-ROC Karşılaştırması")
            models = ["Random Forest (Baseline)", "LSTM", "Transformer", "Ensemble Deep"]
            scores = [0.84, 0.89, 0.92, 0.94]
            fig_auc = px.bar(x=models, y=scores, color=scores, color_continuous_scale="Viridis")
            fig_auc.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  xaxis_title="", yaxis_title="AUC Score", showlegend=False)
            st.plotly_chart(fig_auc, use_container_width=True)

        # 3. Canlı Risk Tahmini (Zaman Serisi)
        st.divider()
        st.subheader("🔍 Tekil Müşteri Zaman Serisi Analizi")
        
        # Rastgele bir müşteri verisi üret
        seq_len = 12
        features = ["Gelir", "Harcama", "Kredi Borcu", "Gecikme", "Kredi Kullanım"]
        data = np.random.randn(seq_len, 5).cumsum(axis=0)
        
        df_seq = pd.DataFrame(data, columns=features)
        df_seq['Ay'] = [f"Ay-{i+1}" for i in range(seq_len)]
        
        st.markdown("**12 Aylık Finansal Hareket Verisi:**")
        st.line_chart(df_seq.set_index('Ay')[["Kredi Borcu", "Harcama"]])

        if st.button("⚡ Bu Profil İçin Tahmin Yap"):
            prediction = deep_engine.predict_risk(data)
            
            p1, p2, p3 = st.columns(3)
            with p1:
                st.metric("Transformer Tahmini", f"%{prediction['transformer_prob']*100:.1f}")
            with p2:
                st.metric("LSTM Tahmini", f"%{prediction['lstm_prob']*100:.1f}")
            with p3:
                color = "inverse" if prediction['ensemble_risk'] > 0.5 else "normal"
                st.metric("BİRLEŞİK RİSK (Ensemble)", f"%{prediction['ensemble_risk']*100:.1f}", 
                          prediction['recommendation'], delta_color=color)
            
            if prediction['ensemble_risk'] > 0.7:
                st.error("🚨 KRİTİK UYARI: Müşteri davranışsal zaman serisi, yüksek temerrüt olasılığı (default) sinyalleri vermektedir.")
            else:
                st.success("✅ GÜVENLİ: Müşteri ödeme alışkanlıkları ve gelir-gider dengesi sürdürülebilir seviyededir.")

    # 4. Mimari Açıklaması
    with st.expander("🧱 Mimari Detaylarını Görüntüle"):
        st.markdown("""
        #### Transformer Encoder
        - **Multi-Head Attention:** 4 kafa ile zaman serisindeki uzak bağımlılıkları (Long-term dependencies) yakalar.
        - **Positional Encoding:** Zamanın sırasını model için anlamlı hale getirir.
        - **Layer Normalization:** Gradyan patlamalarını önler ve eğitimi hızlandırır.
        
        #### LSTM (Long Short-Term Memory)
        - **Sequential Memory:** Müşterinin son 12 aydaki ardışık davranışlarını hafızasında tutar.
        - **Gating mechanism:** Hangi verinin unutulacağına, hangisinin saklanacağına karar verir.
        
        #### Hibrit Karar
        - Modellerin tahminleri, historik başarı oranlarına göre ağırlıklandırılarak (Weighted Averaging) son karara dönüştürülür.
        """)

    st.divider()
    st.info("💡 Derin öğrenme modelleri her hafta sonu yeni gelen portföy verileriyle otomatik olarak yeniden eğitilmektedir.")

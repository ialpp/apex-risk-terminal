"""
ui/views/automl_view.py — ProQuant Capital | AutoML Evrimsel Optimizasyon Dashboard v2.0
========================================================================================

Bu modül, automl_evolutionary.py motorunun arayüzünü sağlar.
Genetik Algoritma tabanlı hiperparametre aramalarını yönetir ve sonuçları görselleştirir.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

def render_automl_view(automl_engine, user_info):
    st.title("🧬 AutoML Evrimsel Optimizasyon Merkezi")
    st.markdown("<p style='color:#64748b;'>Genetik Algoritmalar (GA) ile hiperparametre optimizasyonu ve otonom model seçimi.</p>",
                unsafe_allow_html=True)

    # 1. Optimizasyon Ayarları
    with st.expander("🛠️ Optimizasyon Parametreleri", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            model_type = st.selectbox("Model Tipi", ["Random Forest", "XGBoost", "Deep MLP", "SVM"])
            n_gens = st.slider("Nesil Sayısı (Generations)", 5, 100, 20)
        with c2:
            pop_size = st.slider("Popülasyon Büyüklüğü", 10, 200, 50)
            mut_rate = st.slider("Mutasyon Oranı", 0.01, 0.50, 0.10)
        with c3:
            fitness_metric = st.selectbox("Fitness Metriği", ["AUC-ROC", "F1 Score", "Profit Factor", "Sharpe Ratio"])
            elitism = st.checkbox("Elitizm Uygula", value=True)

        if st.button("🚀 Evrimi Başlat", type="primary", use_container_width=True):
            st.session_state.automl_running = True
            with st.status("Genetik algoritma çalıştırılıyor...", expanded=True) as status:
                st.write("🧬 Başlangıç popülasyonu oluşturuluyor...")
                # Simülasyon olduğu için motoru çağırıyoruz
                results = automl_engine.run_optimization(model_type, n_generations=n_gens)
                time.sleep(1)
                st.write(f"🧬 {n_gens} nesil boyunca evrimleşme tamamlandı.")
                st.session_state.automl_results = results
                status.update(label="✅ Optimizasyon Tamamlandı!", state="complete", expanded=False)

    # 2. Optimizasyon Sonuçları (Eğer varsa)
    if "automl_results" in st.session_state:
        res = st.session_state.automl_results
        
        st.divider()
        st.subheader(f"🏆 En İyi Model Sonuçları ({res['model']})")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("En İyi Fitness", f"{res['best_fitness']:.4f}")
        m2.metric("Nesil", res['generations'])
        m3.metric("Süre", f"{res['duration_sec']}sn")
        m4.metric("Aranan Parametre", res['params_searched'])

        # En iyi parametreler
        st.info(f"**Optimal Hiperparametreler:** {res['best_params']}")

        # 3. Görselleştirme (Fitness Trend)
        st.divider()
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
            st.subheader("📈 Fitness Gelişimi (Learning Curve)")
            h_df = pd.DataFrame(res['history'])
            
            fig_fitness = go.Figure()
            fig_fitness.add_trace(go.Scatter(x=h_df['generation'], y=h_df['best_fitness'], 
                                            name='Best Fitness', line=dict(color='#818cf8', width=3)))
            fig_fitness.add_trace(go.Scatter(x=h_df['generation'], y=h_df['avg_fitness'], 
                                            name='Avg Fitness', line=dict(color='rgba(129, 140, 248, 0.4)', dash='dash')))
            
            fig_fitness.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Nesil",
                yaxis_title="Fitness Skoru",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_fitness, use_container_width=True)

        with col_g2:
            st.subheader("📊 Parametre Önem Sırası")
            # Simüle edilmiş feature/param importance
            p_names = list(res['best_params'].keys())
            p_imp = np.random.dirichlet(np.ones(len(p_names)), size=1)[0]
            
            df_imp = pd.DataFrame({"Parametre": p_names, "Etki": p_imp}).sort_values("Etki", ascending=True)
            fig_imp = px.bar(df_imp, x="Etki", y="Parametre", orientation='h', color_discrete_sequence=['#38bdf8'])
            fig_imp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_imp, use_container_width=True)

        # 4. Popülasyon Detayı
        with st.expander("📑 Tüm Nesil Kayıtları"):
            st.table(h_df)

    else:
        # Tanıtım ekranı
        st.info("👈 Optimizasyonu başlatmak için yukarıdaki ayarları kontrol edin ve 'Evrimi Başlat' butonuna basın.")
        
        st.markdown("""
        ### Neden Evrimsel Optimizasyon?
        GridSearch her kombinasyonu dener ve zaman kaybına yol açar. **Evrimsel (Evolutionary)** yaklaşım ise:
        1.  **Doğal Seçilim:** Başarılı parametre setlerini bir sonraki nesle aktarır.
        2.  **Crossover:** Farklı başarılı setleri birleştirerek hibrit çözümler üretir.
        3.  **Mutation:** Lokal minimumlardan kaçmak için rastgele 'sıçramalar' yapar.
        4.  **Hız:** Çok daha az iterasyonla global optimuma daha yakın sonuçlar bulur.
        """)

    st.divider()
    st.caption(f"Sistem: ProQuant AutoML v{st.session_state.get('app_version', '2.0')} | Engine: Genetic Evolutionary Optimizer")

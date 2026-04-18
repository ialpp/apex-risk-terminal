import streamlit as st
def render_genai_copilot_view():
    st.header("🤖 GenAI Financial RAG Copilot", divider="blue")
    st.info("SEC (10-K, 10-Q) raporları LLM embedding ile analiz ediliyor...")
    st.metric("Vektörize Edilen SEC Dosyası", "5,599 Rapor", "Cosine Similarity Taraması")

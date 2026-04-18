@echo off
title ProQuant Capital
color 0A
echo.
echo  ProQuant Capital - Kurumsal Risk Terminali v5.0
echo  Gerekli paketler yukleniyor, lutfen bekleyin...
echo.
py -m pip install streamlit pandas numpy scikit-learn joblib matplotlib seaborn plotly reportlab openpyxl xlsxwriter Pillow scipy -q
echo.
echo  Uygulama baslatiliyor... Tarayici otomatik acilacak.
echo  Durdurmak icin CTRL+C basin.
echo.
py -m streamlit run app.py
pause

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

print("Sentetik veriler üretiliyor ve model eğitiliyor. Lütfen bekleyin...")

# 1. Sentetik Veri Oluşturma (İktisadi Kurallara Uygun)
np.random.seed(42)
num_samples = 2000

# Özellikler (Features)
yasi = np.random.randint(18, 70, size=num_samples)
aylik_gelir = np.random.normal(loc=15000, scale=8000, size=num_samples).clip(min=5500) # TL cinsi asgari ücret üstü
mevcut_borc = aylik_gelir * np.random.uniform(0.1, 4.0, size=num_samples) # Gelire oranla borç
gecikmis_odeme_sayisi = np.random.randint(0, 10, size=num_samples)
kredi_karti_sayisi = np.random.randint(0, 5, size=num_samples)

# Kredi Onay Mantığı (Hedef Değişken)
borc_gelir_orani = mevcut_borc / aylik_gelir

# Skorlama Sistemi: Düşük skor kötüdür
skor = (aylik_gelir * 0.05) - (mevcut_borc * 0.1) - (gecikmis_odeme_sayisi * 500) + (yasi * 10)

# Threshold ile Onay (1) / Ret (0) belirleme (Modelin tahmin edeceği etiket)
gurultu = np.random.normal(0, 1000, size=num_samples)
nihai_skor = skor + gurultu

# Medyanın üstü onay alır
kredi_onay = (nihai_skor > np.median(nihai_skor)).astype(int) 

df = pd.DataFrame({
    'Yas': yasi,
    'Aylik_Gelir': aylik_gelir,
    'Mevcut_Borc': mevcut_borc,
    'Gecikmis_Odeme_Sayisi': gecikmis_odeme_sayisi,
    'Kredi_Karti_Sayisi': kredi_karti_sayisi,
    'Borc_Gelir_Orani': borc_gelir_orani,
    'Onay_Durumu': kredi_onay
})

# 2. Model Eğitimi (Scikit-Learn)
X = df.drop('Onay_Durumu', axis=1)
y = df['Onay_Durumu']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Başarı oranı
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Eğitildi! Doğruluk Oranı (Accuracy): %{accuracy*100:.2f}")

# 3. Modeli Kaydetme
model_path = os.path.join(os.path.dirname(__file__), 'kredi_modeli.pkl')
joblib.dump(model, model_path)
print(f"Model başarıyla kaydedildi: {model_path}")

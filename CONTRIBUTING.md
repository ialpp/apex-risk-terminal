# Contributing to Apex Risk Terminal

Katkıda bulunmak istediğiniz için teşekkür ederiz! 🎉

Bu belge, projeye nasıl katkıda bulunabileceğinizi açıklar.

---

## 📋 Başlamadan Önce

### Gereksinimler

- Python 3.11+
- Git
- pip veya conda

### Geliştirme Ortamı Kurulumu

```bash
# Repoyu fork'layıp klonlayın
git clone https://github.com/YOUR_USERNAME/apex-risk-terminal.git
cd apex-risk-terminal

# Sanal ortam oluşturun
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
streamlit run app.py
```

---

## 🌿 Branch Stratejisi

| Branch | Amaç |
|---|---|
| `main` | Kararlı üretim sürümü |
| `develop` | Geliştirme dalı |
| `feature/xyz` | Yeni özellik geliştirme |
| `fix/xyz` | Hata düzeltme |
| `hotfix/xyz` | Acil üretim düzeltmesi |

```bash
# Yeni bir özellik dalı oluşturun
git checkout -b feature/my-new-module

# Değişikliklerinizi commit edin
git add .
git commit -m "feat(modules): add new risk scoring algorithm"

# Ana repoya push edin
git push origin feature/my-new-module
```

---

## ✅ Commit Mesajı Kuralları

[Conventional Commits](https://www.conventionalcommits.org/) standardını kullanıyoruz:

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

### Tipler

| Tip | Açıklama |
|---|---|
| `feat` | Yeni özellik |
| `fix` | Hata düzeltme |
| `docs` | Sadece dokümantasyon değişikliği |
| `refactor` | Ne özellik ne hata düzeltme — yeniden yapılandırma |
| `test` | Test ekleme veya düzeltme |
| `chore` | Build araçları, bağımlılık güncellemeleri |

### Örnekler

```
feat(modules): add IFRS9 ECL stage classification
fix(auth): resolve session timeout not clearing state
docs(readme): add deployment badge and screenshots
test(scoring): add unit tests for ensemble prediction
```

---

## 🏗️ Modül Geliştirme Standartları

### Yeni Modül Ekleme

1. `modules/` altına `my_module.py` oluşturun
2. Mutlaka bir `get_my_engine()` factory fonksiyonu ekleyin
3. `app.py`'deki `load_all_engines_v3()` fonksiyonuna import edin
4. `NAV_ITEMS` listesine navigasyon kaydı ekleyin
5. `ui/views/` altına karşılık gelen view dosyasını oluşturun

### Kod Standartları

```python
# ✅ Doğru
def get_my_engine() -> MyEngine:
    """Factory function — singleton pattern."""
    return MyEngine()

class MyEngine:
    """
    Modül açıklaması.
    
    Attributes:
        param: açıklaması
    """
    
    def analyze(self, data: dict) -> dict:
        """
        Analiz yapar.
        
        Args:
            data: Girdi verisi
            
        Returns:
            Analiz sonuçları dict'i
        """
        ...
```

### View Standartları

```python
# ui/views/my_module_view.py
import streamlit as st

def render_my_module_view(engine, user_info: dict):
    """View render fonksiyonu."""
    st.title("📊 Modül Başlığı")
    st.markdown("<p style='color:#64748b;'>Açıklama</p>", unsafe_allow_html=True)
    
    # Tab yapısını kullan
    tab1, tab2 = st.tabs(["📊 Ana Analiz", "⚙️ Ayarlar"])
    
    with tab1:
        ...
```

---

## 🧪 Test Yazma

```bash
# Testleri çalıştır
python -m pytest tests/ -v

# Belirli bir modülü test et
python -m pytest tests/unit/test_credit_scoring.py -v

# Coverage raporu
python -m pytest tests/ --cov=modules --cov-report=html
```

### Test Yapısı

```
tests/
├── unit/           # Bireysel modül testleri
├── integration/    # Modüller arası entegrasyon testleri
├── regulatory/     # Düzenleyici uyum testleri
└── stability/      # Stabilite ve yük testleri
```

---

## 🔍 Pull Request Süreci

1. **Fork** edin ve feature branch oluşturun
2. Değişikliklerinizi yapın ve commit edin (conventional commits)
3. `tests/` altına ilgili testleri yazın
4. `CHANGELOG.md`'yi güncelleyin
5. PR açın ve şablonu doldurun
6. Code review bekleyin

### PR Şablonu

```markdown
## Değişiklik Özeti
<!-- Ne değişti ve neden? -->

## Test Edildi mi?
- [ ] Birim testler geçiyor
- [ ] Manuel test yapıldı
- [ ] Yeni özellik için test yazıldı

## Bağlantılı Issue
Fixes #<issue_number>
```

---

## 📬 İletişim

Sorularınız için [GitHub Issues](https://github.com/YOUR_USERNAME/apex-risk-terminal/issues) kullanın.

---

<div align="center">
<sub>Built with ❤️ using Python & Streamlit</sub>
</div>

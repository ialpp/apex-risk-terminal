import sys
import codecs
from ui.academy_data import ARTICLES

specific_expansions = {
    "financial_graph_networks": """
**İlişkisel Veri Bağlarının Çok Katmanlı İncelemesi**  
Kurumların hesaplarına giren ve çıkan fonların basit lineer (doğrusal) analizleri uzun zamandır yetersiz kalmaktadır. Özellikle uluslararası kara para aklama şebekelerinin başvurduğu "Katmanlama" (Layering) yöntemi, paranın kaynağını kamufle etmek için paravan şirketler, yasal temsilciler ve dijital gölge cüzdanlar üzerinden dolambaçlı yollar çizer. Graph Nöral Ağları (GNN), tam olarak bu çok katmanlı, kokuşmuş ağları bir defada görüntülemek üzere veri tabanında (örneğin Neo4J altyapısıyla) saniyik bir düğüm eşleştirmesi yapar.

**Zaman ve Yön Vektörleri (Directed Graphs)**  
Geleneksel uyarı (alert) sistemlerindeki bir diğer eksiklik 'yön ve zaman' bağıntısının kurulamamasıdır. GNN modelleri ise sadece Ali'nin Veli'ye para göndermesini değil, Veli'nin aynı gün içinde hiç tanımadığı Ayşe, Fatma ve üç ayrı off-shore şirketine bu parayı parçalara bölerek ne kadar sürede dağıttığını ölçer. Zaman damgası (Timestamp) daraldıkça, Graph analizindeki risk skoru katlanarak artar. Merkezi düğümler (Hub Nodes) olarak nitelendirilen geçiş hesapları 'Kırmızı Bayrak' yerleştirilerek operasyonel inceleme departmanlarına (Compliance) sevk edilir. Bu denli organik ve canlı büyüyen bir algılayıcı yapı sayesinde finans devlerinin ceza ödeme riski (Regulatory Fines) bütünüyle sıfıra yaklaşmaktadır.
""",
    "nlp_credit_scoring": """
**Psikometrik Göstergeler Olarak Müşteri Talepleri**  
Bir müşterinin kredi başvurusu onaylandığında işlem bitmiş sayılmaz; asıl izleme (monitoring) aşaması başlar. Doğal Dil İşleme (NLP) algoritmaları, müşterinin kurum ile kurduğu yazılı, sözlü ve sosyal temasları "Sentiment (Duygu) Analizi" çerçevesinde değerlendirir. Müşteri kredi vadesi yaklaşırken müşteri hizmetleri temsilcilerine agresif tonlu sorular soruyor mu? Elektronik postalarda aciliyet belirten 'ödeme vadesini kaçırma', 'cezai işlem', 'nakit darlığı' gibi finansal stres jargonu (Financial Stress Lexicons) artıyor mu?  

**Transformer Modellerinin Otonom Kararları**  
Müşterinin yazışmaları, LLM tabanlı Transformer ağlarına aktarıldığında, kişinin potansiyel iflas (default) ihtimalini anlık olarak yükselten sinyaller üretilir. Örneğin, düzenli ödeme yapan müşterinin son bir ay içindeki çağrı merkezi görüşmelerinde yüksek dozda "işten çıkarılma", "piyasa durgunluğu" gibi meta-keywordlerin tespit edilmesi, bankanın proaktif davranarak yapılandırma teklifleri sunmasına zemin hazırlar. Bu sistem sayesinde kurum, müşteri henüz fiilen batmadan, yani sadece gecikme evresinde dahi değilken, davranışsal analizle erken müdahalede bulunabilmektedir.
""",
    "robo_advisor_hyper": """
**Black-Litterman Modellerinin Makine Öğrenimi İle Birleşimi**  
Standart teoriler portföy çeşitlendirmesinde ortalama-varyans optimizasyonunu kullansa da piyasalar çoğu zaman rasyonel değildir. Piyasaların "Kalın Kuyruk" (Fat Tail) dağılım özellikleri barındırıp aniden sert şoklar yemesi karşısında, statik Robo Danışmanlar yatırımcının sermayesini eritir. Ancak Hiper-Kişiselleştirilmiş otonom stratejiler, Makro modeller ile yatırımcının kişisel görüşünü analitik olarak harmanlayan Black-Litterman tekniğini kullanır. Ajanların (Agent-based AI), haber akışlarından çektiği hislere göre Black-Litterman görünüm matrisini (View Matrix) dinamik olarak güncelleyerek portföy rotasyonunu saatlik düzeyde yapar.

**Anlık Piyasa Yapıcılık ve Takip Sapması**  
Yüksek servet sahibi (High Net Worth) müşterilerin bireysel risk/getiri skalaları aşırı spesifiktir. "Bana S&P500 endeksine benzer getiri sağlayan, ama kesinlikle Fosil Yakıt hissesi içermeyen, Tracking-Error (Takip Sapması) en fazla %0.5 olan bir portföy kur ve bunu opsiyonlarla hedge et" talebini bir insanın canlı hesaplaması imkânsızdır. Sistem, otonom arbitraj robotları ve derin öğrenme ağları ile bunu mikro saniyelerde matematiksel formüllerle inşa edip canlıda al-sat emirlerine çevirerek VIP hizmet standardını tüm varlık yönetimi iş akışında sanayileştirmektedir.
""",
    "sovereign_risk_ai": """
**Dış Borç Stresi ve Rezerv Yeterliliğinde Akıllı Sensörler**  
Gelişmekte olan ülkelerin devlet tahvili veya kredi temerrüt risklerinde (Sovereign CDS), Merkez Bankası rezervleri ve kısa vadeli dış borç sarmalı en büyük indikatördür. Fakat bu veriler "Gecikmeli" (Lagging) indikatörlerdir, 3-4 hafta sonra açıklanır. Sovereign Risk AI motorumuz, petrol arzı liman yoğunlukları, uydulardan alınan tarımsal rekolte öngörüleri veya limanlardaki konteyner trafiği gibi "Öncü" (Leading) alternatif veri setlerini tarayarak makroekonomik bilançonun erken taslağını oluşturur. 

**Çapraz Kur Dalgalanmaları ve Global Arbitraj**  
Bir ülkedeki lokal kriz anında, o ülkenin devlet kağıdından portföyden kaçışın hangi asimetrik güvenli limanlara (Japon Yeni, İsviçre Frangı, Altın) akacağı sinir ağları ile olasılık haritalarına dönüştürülür. Kriz patlamadan önce modelin yatırım komitesine vereceği Sovereign Hedge stratejileri milyonlarca doların buharlaşmasını önlemekle kalmaz; ters pozisyonlanma (Short-selling) ile ülkenin likidite krizini portföy bazında kâr merkezine dönüştürme marjini bağışlar. Bu akıllı ülke riski izleme altyapısı, devasa fon yöneticilerinin ufkunu manuel Excel takip tablolarından çıkararak kuantum çağına taşımaktadır.
"""
}

generic_blocks = """
**Kurumsal Entegrasyon Mimarlığı ve {category} Çözümleri**  
Sistemin çekirdeği (Core Engine), geleneksel monolitik bankacılık altyapılarının (örneğin AS400 bazlı ana sistemler) yarattığı darboğazları aşmak üzere tamamıyla Mikroservis Tabanlı (Microservices-Oriented) olarak tasarlanmıştır. {category} algoritmalarından alınan her bir aksiyon kararı, asenkron haberleşme kuyrukları (RabbitMQ, Apache Kafka) vasıtasıyla mevduat, kredi ve hesap yönetim modüllerine iletilir. Bu sayede ana bankacılık sisteminde oluşabilecek herhangi bir yük anormalliği makine öğrenimi tarafını etkilemez; sistem asimetrik şoklara karşı tam izolasyon altındadır. Model güncellemeleri Blue-Green deployment prensibiyle canlı ortam durmaksızın uygulanır.

**Veri Güvenliği, KVKK/GDPR ve Veri Anonimleştirme (Data Masking)**  
Algoritmanın {title} operasyonu kapsamındaki eğitim ve çıkarım süreçlerinde kullanılan müşteri verileri, AES-256 seviyesinde donanımsal güvenlik modüllerinde (HSM) şifrelenmektedir. Hassas finansal bilgiler, model antrenmanı ortamına aktarılırken sentetik veri üretim jeneratörleri ve "Data Masking" araçlarıyla anonimleştirilir. Kişisel Verilerin Korunması Kanunu (KVKK) ve Avrupa Genel Veri Koruma Tüzüğü (GDPR) çerçevesinde "Unutulma Hakkı" uygulanan müşterilerin ağırlıkları, ağ içerisindeki kısmi unutma algoritmaları (Federated Learning ve Machine Unlearning) kullanılarak modellerden başarıyla geri çekilir.

**Cloud-Native Çalışma Düzeni ve Heterojen Veritabanları**  
Sistem veritabanı tercihlerinde de çoklu yapılandırma mevcuttur. Müşteri logları ve zaman serisi (Time-series) akışları NoSQL veri tabanlarında kümelenirken; cüzdan, bakiye ve kesin işlem kayıtları (ACID garantisi için) yüksek performanslı ilişkisel veri tabanlarında (PostgreSQL tabanlı NewSQL cluster'larında) işlenir. Bu hibrit bulut ve on-premise donanım konfigürasyonları, modellerin 7 gün 24 saat, minimum %99.99 uptime garantisi ile çalışmasını sağlar.

**Maliyet Etkisi (ROI) ve Gelecek Stratejisi**  
Finans sektörü otomasyon devrimini bir maliyet optimizasyonu aracı olmaktan çıkarıp, rekabetin ana ekseni haline getirmiştir. Projenin Tier-1 veya Tier-2 bankalara entegre edilmesi, operasyonel işgücü maliyetlerini (Opex) %60 oranında düşürürken, asıl kazancı (Alpha generation & Risk mitigation) yanlış kararlardan dönülen temerrüt zararlarını azaltarak yaratır. Kümülatif Yatırım Getirisi (ROI) analizi, bu tip gelişmiş sistemlerin ilk 18 ay içerisinde maliyetini fazlasıyla kompanse ettiğini ortaya koymaktadır.
"""

for art in ARTICLES:
    content = art["content"]
    
    # Specific expansions for the short ones
    if art["id"] in specific_expansions:
        content += "\n" + specific_expansions[art["id"]]
    
    # Check if we already appended generic blocks to prevent duplication if run multiple times
    if "Kurumsal Entegrasyon Mimarlığı" not in content:
        content += "\n\n" + generic_blocks.format(title=art["title"], category=art["category"])
        
    art["content"] = content

# Write to ui/academy_data.py safely
with codecs.open("ui/academy_data.py", "w", "utf-8") as f:
    f.write("from copy import deepcopy\n\n")
    f.write("ARTICLES = [\n")
    for art in ARTICLES:
        f.write("    {\n")
        f.write(f'        "id": "{art["id"]}",\n')
        f.write(f'        "title": "{art["title"]}",\n')
        f.write(f'        "category": "{art["category"]}",\n')
        f.write(f'        "read_time": "{art["read_time"]}",\n')
        f.write(f'        "short_desc": "{art["short_desc"]}",\n')
        f.write(f'        "image_idx": {art["image_idx"]},\n')
        f.write(f'        "content": """{art["content"]}"""\n')
        f.write("    },\n")
    f.write("]\n\n")
    f.write("def get_articles():\n")
    f.write("    return deepcopy(ARTICLES)\n")

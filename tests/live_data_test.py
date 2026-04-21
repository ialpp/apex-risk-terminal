import sys
import os
import unittest
import warnings
import datetime

# Add root to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_orchestrator import DataOrchestrator
from modules.realtime_risk_monitor import RealtimeRiskMonitor
from modules.nlp_intelligence import LiveNewsProvider
from config import LIVE_DATA_MODE

class TestLiveDataFlow(unittest.TestCase):
    
    def setUp(self):
        # Ignore SSL verification warnings in tests as we purposefully bypassed it
        warnings.filterwarnings("ignore", category=UserWarning)
        self.orchestrator = DataOrchestrator()
        self.news_provider = LiveNewsProvider()
        
    def test_yfinance_connectivity(self):
        """Orkestratörün canlı veri çekebildiğini doğrula."""
        print(f"\n[TEST] Veri Orkestratörü Canlı Bağlantısı Kontrol Ediliyor...")
        # LIVE_DATA_MODE'un açık olduğundan emin ol
        self.assertTrue(LIVE_DATA_MODE, "LIVE_DATA_MODE config.py'da 'True' olmalı!")
        
        stream = self.orchestrator.get_market_data("AAPL", force_refresh=True)
        self.assertIsNotNone(stream)
        self.assertEqual(stream.source, "YAHOO_FINANCE")
        self.assertGreater(len(stream.points), 0)
        print(f"[OK] Canlı Borsa Verisi Alındı: AAPL @ {stream.points[-1].value:.2f}")

    def test_live_news_fetching(self):
        """Haber servisinin canlı haber çekebildiğini doğrula."""
        print(f"[TEST] Canlı Haber Akışı Kontrol Ediliyor...")
        news = self.news_provider.fetch_live_news()
        self.assertGreater(len(news), 0, "Canlı haber akışı boş geldi!")
        print(f"[OK] Canlı Haberler Alındı: {len(news)} adet güncel haber.")
        for item in news[:2]:
            print(f"  - {item.headline[:60]}...")

    def test_crypto_forex_live(self):
        """Kripto ve Forex parite canlılığını doğrula."""
        print(f"[TEST] Kripto ve Forex Canlı Veri Kontrolü...")
        
        # USD/TRY kontrolü
        try_stream = self.orchestrator.get_market_data("TRY=X", force_refresh=True)
        self.assertIsNotNone(try_stream)
        print(f"[OK] Canlı Kur: USD/TRY @ {try_stream.points[-1].value:.4f}")
        
        # BTC kontrolü
        btc_stream = self.orchestrator.get_market_data("BTC-USD", force_refresh=True)
        self.assertIsNotNone(btc_stream)
        print(f"[OK] Canlı BTC: BTC-USD @ {btc_stream.points[-1].value:.0f}")

if __name__ == "__main__":
    unittest.main()

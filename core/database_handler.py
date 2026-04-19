import time
"""
core/database_handler.py
Kurumsal SQLite ORM Katmanı — Tüm veri işlemlerinin merkezi.
Kullanıcı yönetimi, müşteri kayıtları, analiz logları, başvurular,
belgeler, notlar ve sistem ayarlarını yönetir.
"""

import sqlite3
import pandas as pd
import numpy as np
import hashlib
import os
import json
from datetime import datetime, timedelta
from config import DB_FILE, ROLES


class DatabaseHandler:
    """
    Kurumsal düzey SQLite ORM (Object-Relational Mapping) simülasyonu.
    Tüm veri işlemleri bu sınıf üzerinden gerçekleşir.
    """

    def __init__(self):
        self.db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), DB_FILE
        )
        self._setup_all_tables()
        self._migrate_schema()
        self._seed_default_data()

    # ──────────────────────────────────────────────────────────────
    #  BAĞLANTI YÖNETİMİ
    # ──────────────────────────────────────────────────────────────

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Dict benzeri erişim
        conn.execute("PRAGMA journal_mode=WAL")  # Performans
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ──────────────────────────────────────────────────────────────
    #  TABLO OLUŞTURMA
    # ──────────────────────────────────────────────────────────────

    def _setup_all_tables(self):
        conn = self.get_connection()
        c = conn.cursor()

        # 1. KULLANICI TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                username          TEXT    UNIQUE NOT NULL,
                password_hash     TEXT    NOT NULL,
                role              TEXT    NOT NULL DEFAULT 'Risk Analisti',
                full_name         TEXT,
                email             TEXT    UNIQUE,
                phone             TEXT,
                department        TEXT,
                avatar_color      TEXT    DEFAULT '#4f46e5',
                is_active         INTEGER DEFAULT 1,
                failed_attempts   INTEGER DEFAULT 0,
                locked_until      TIMESTAMP,
                last_login        TIMESTAMP,
                preferred_lang    TEXT    DEFAULT 'tr',
                preferred_theme   TEXT    DEFAULT 'dark',
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. MÜŞTERİ TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code       TEXT    UNIQUE NOT NULL,
                full_name           TEXT    NOT NULL,
                national_id         TEXT    UNIQUE,
                birth_date          TEXT,
                age                 INTEGER,
                phone               TEXT,
                email               TEXT,
                address             TEXT,
                city                TEXT,
                occupation          TEXT,
                employer            TEXT,
                employment_years    REAL    DEFAULT 0,
                monthly_income      REAL    NOT NULL,
                additional_income   REAL    DEFAULT 0,
                total_debt          REAL    DEFAULT 0,
                credit_card_count   INTEGER DEFAULT 0,
                late_payment_count  INTEGER DEFAULT 0,
                credit_history_years REAL   DEFAULT 1,
                home_ownership      TEXT    DEFAULT 'Kiracı',
                monthly_expenses    REAL    DEFAULT 0,
                dependents          INTEGER DEFAULT 0,
                education_level     TEXT    DEFAULT 'Lisans',
                credit_score        REAL,
                risk_category       TEXT,
                segment             TEXT,
                tags                TEXT    DEFAULT '[]',
                notes               TEXT,
                assigned_analyst    TEXT,
                is_active           INTEGER DEFAULT 1,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. KREDİ BAŞVURU TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                application_no      TEXT    UNIQUE NOT NULL,
                customer_id         INTEGER REFERENCES customers(id),
                customer_code       TEXT,
                loan_type           TEXT    NOT NULL,
                requested_amount    REAL    NOT NULL,
                requested_term      INTEGER NOT NULL,
                purpose             TEXT,
                collateral_type     TEXT,
                collateral_value    REAL    DEFAULT 0,
                monthly_payment_est REAL,
                interest_rate_est   REAL,
                status              TEXT    DEFAULT 'İncelemede',
                ml_decision         INTEGER,
                ml_probability      REAL,
                ml_risk_score       REAL,
                fraud_score         REAL,
                analyst_decision    TEXT,
                analyst_notes       TEXT,
                processed_by        TEXT,
                processed_at        TIMESTAMP,
                created_by          TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. ANALİZ LOG TABLOSU (AUDİT TRAİL)
        c.execute("""
            CREATE TABLE IF NOT EXISTS analysis_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                analyst_name    TEXT,
                customer_code   TEXT,
                customer_name   TEXT,
                age             INTEGER,
                income          REAL,
                debt            REAL,
                dti_ratio       REAL,
                late_payments   INTEGER,
                card_count      INTEGER,
                credit_score    REAL,
                ml_result       INTEGER,
                ml_probability  REAL,
                fraud_score     REAL,
                risk_category   TEXT,
                action_taken    TEXT,
                ip_address      TEXT    DEFAULT 'N/A',
                session_id      TEXT,
                timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. BELGE TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id     INTEGER REFERENCES customers(id),
                application_id  INTEGER REFERENCES applications(id),
                doc_type        TEXT    NOT NULL,
                doc_name        TEXT    NOT NULL,
                doc_path        TEXT,
                file_size       INTEGER,
                verified        INTEGER DEFAULT 0,
                verified_by     TEXT,
                verified_at     TIMESTAMP,
                uploaded_by     TEXT,
                uploaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes           TEXT
            )
        """)

        # 6. MÜŞTERİ NOTLARI TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_notes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id     INTEGER REFERENCES customers(id),
                author          TEXT    NOT NULL,
                note_text       TEXT    NOT NULL,
                note_type       TEXT    DEFAULT 'Genel',
                is_pinned       INTEGER DEFAULT 0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. KREDİ SKORU GEÇMİŞ TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS score_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id     INTEGER REFERENCES customers(id),
                customer_code   TEXT,
                credit_score    REAL    NOT NULL,
                risk_category   TEXT,
                dti_ratio       REAL,
                calculated_by   TEXT,
                note            TEXT,
                recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 8. ERKEN UYARI LOG TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS early_warnings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id     INTEGER REFERENCES customers(id),
                customer_code   TEXT,
                warning_type    TEXT    NOT NULL,
                severity        TEXT    NOT NULL,
                message         TEXT    NOT NULL,
                is_resolved     INTEGER DEFAULT 0,
                resolved_by     TEXT,
                resolved_at     TIMESTAMP,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 9. SİSTEM LOG TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                level       TEXT    NOT NULL,
                module      TEXT,
                message     TEXT    NOT NULL,
                user        TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 10. FİNANSAL HEDEF TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id     INTEGER REFERENCES customers(id),
                goal_type       TEXT    NOT NULL,
                target_score    REAL,
                current_score   REAL,
                target_date     TEXT,
                description     TEXT,
                status          TEXT    DEFAULT 'Aktif',
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 11. BANKACILIK HAREKETLERİ TABLOSU (AÇIK BANKACILIK)
        c.execute("""
            CREATE TABLE IF NOT EXISTS banking_transactions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id     INTEGER REFERENCES customers(id),
                transaction_id  TEXT    NOT NULL,
                tx_date         TIMESTAMP NOT NULL,
                merchant        TEXT    NOT NULL,
                amount_try      REAL    NOT NULL,
                tx_type         TEXT    NOT NULL,
                category        TEXT    NOT NULL,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 12. FİYATLAMA VE RAROC SENARYO TABLOSU
        c.execute("""
            CREATE TABLE IF NOT EXISTS pricing_scenarios (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id         INTEGER REFERENCES customers(id),
                analyst_name        TEXT,
                loan_amount         REAL,
                interest_rate       REAL,
                pd_prob             REAL,
                economic_capital    REAL,
                raroc_score         REAL,
                decision            TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 13. MAKRO EKONOMETRİ ZAMAN SERİSİ
        c.execute("""
            CREATE TABLE IF NOT EXISTS macro_time_series (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name   TEXT    NOT NULL,
                target_date     TIMESTAMP NOT NULL,
                inflation_pct   REAL,
                policy_rate_pct REAL,
                usd_try         REAL,
                cds_spread      REAL,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 14. PORTFÖY VALUE-AT-RISK (VaR) SİMÜLASYONLARI
        c.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_var_history (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                analyst_name        TEXT,
                total_exposure      REAL,
                expected_loss       REAL,
                var_99              REAL,
                var_999             REAL,
                expected_shortfall  REAL,
                economic_capital    REAL,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 15. RAG / LLM OTONOM KOMİTE RAPORLARI
        c.execute("""
            CREATE TABLE IF NOT EXISTS llm_reports (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name       TEXT    NOT NULL,
                requested_amount    REAL,
                credit_score        REAL,
                pd_prob             REAL,
                macro_risk_level    TEXT,
                generated_report    TEXT    NOT NULL,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────────────────────
    #  SCHEMA MİGRASYONU (Eski DB'ye eksik kolonları ekler)
    # ──────────────────────────────────────────────────────────────

    def _migrate_schema(self):
        """
        Mevcut veritabanındaki eksik kolonları ALTER TABLE ile ekler.
        Bu sayede eski DB'yi silmeden şema güncellenir.
        """
        conn = self.get_connection()
        c = conn.cursor()

        # users tablosuna eklenecek kolonlar: (kolon_adı, tip ve default)
        users_columns = [
            ("full_name",       "TEXT"),
            ("email",           "TEXT"),
            ("phone",           "TEXT"),
            ("department",      "TEXT"),
            ("avatar_color",    "TEXT    DEFAULT '#4f46e5'"),
            ("is_active",       "INTEGER DEFAULT 1"),
            ("failed_attempts", "INTEGER DEFAULT 0"),
            ("locked_until",    "TIMESTAMP"),
            ("last_login",      "TIMESTAMP"),
            ("preferred_lang",  "TEXT    DEFAULT 'tr'"),
            ("preferred_theme", "TEXT    DEFAULT 'dark'"),
            ("updated_at",      "TIMESTAMP"),
        ]

        # Mevcut users kolonlarını al
        c.execute("PRAGMA table_info(users)")
        existing = {row["name"] for row in c.fetchall()}

        for col_name, col_def in users_columns:
            if col_name not in existing:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass  # Kolon zaten varsa sessizce geç

        # customers tablosuna eklenecek kolonlar
        customers_columns = [
            ("segment",      "TEXT"),
            ("tags",         "TEXT DEFAULT '[]'"),
            ("notes",        "TEXT"),
            ("is_active",    "INTEGER DEFAULT 1"),
            ("updated_at",   "TIMESTAMP"),
            ("risk_category","TEXT"),
            ("credit_score", "REAL"),
            ("assigned_analyst", "TEXT"),
        ]

        c.execute("PRAGMA table_info(customers)")
        existing_cust = {row["name"] for row in c.fetchall()}

        for col_name, col_def in customers_columns:
            if col_name not in existing_cust:
                try:
                    c.execute(f"ALTER TABLE customers ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass

        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────────────────────
    #  VARSAYILAN VERİ EKİMİ
    # ──────────────────────────────────────────────────────────────

    def _seed_default_data(self):
        """Sisteme ilk kez girildiğinde varsayılan kullanıcıları oluşturur.
        
        Şifreler Streamlit secrets'tan okunur.
        Secrets yoksa (local dev) fallback değerler kullanılır.
        
        .streamlit/secrets.toml örneği:
            [demo_users]
            admin_password   = "GüçlüŞifre123!"
            analyst_password = "AnalistŞifre456!"
            mudur_password   = "MüdürŞifre789!"
            stajyer_password = "StajyerŞifre012!"
        """
        try:
            import streamlit as st
            secrets = st.secrets.get("demo_users", {})
            admin_pwd   = secrets.get("admin_password",   "admin123")
            analyst_pwd = secrets.get("analyst_password", "analist123")
            mudur_pwd   = secrets.get("mudur_password",   "mudur123")
            stajyer_pwd = secrets.get("stajyer_password", "stajyer123")
        except Exception:
            # Streamlit context dışında (test ortamı vb.) fallback
            admin_pwd, analyst_pwd, mudur_pwd, stajyer_pwd = (
                "admin123", "analist123", "mudur123", "stajyer123"
            )

        default_users = [
            ("admin",    admin_pwd,   "Head Analist",    "Sistem Yöneticisi", "admin@proquant.com",  "Risk Yönetimi"),
            ("analist1", analyst_pwd, "Risk Analisti",   "Ahmet Yıldız",      "ahmet@proquant.com",  "Bireysel Bankacılık"),
            ("mudur",    mudur_pwd,   "Genel Müdür",     "Mehmet Özcan",      "mudur@proquant.com",  "Üst Yönetim"),
            ("stajyer",  stajyer_pwd, "Stajyer Analist", "Zeynep Kaya",       "zeynep@proquant.com", "Staj Programı"),
        ]
        for uname, pwd, role, full_name, email, dept in default_users:
            self.add_user(uname, pwd, role, full_name, email, dept)

    # ──────────────────────────────────────────────────────────────
    #  KULLANICI YÖNETİMİ
    # ──────────────────────────────────────────────────────────────

    def add_user(self, username, password, role="Risk Analisti",
                 full_name=None, email=None, department=None) -> bool:
        conn = self.get_connection()
        c = conn.cursor()
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            c.execute("""
                INSERT OR IGNORE INTO users
                    (username, password_hash, role, full_name, email, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, pwd_hash, role, full_name, email, department))
            conn.commit()
            return c.rowcount > 0
        finally:
            conn.close()

    def verify_user(self, username: str, password: str) -> dict | None:
        conn = self.get_connection()
        c = conn.cursor()
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()

        # Hesap kilitli mi?
        c.execute("SELECT locked_until FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if row and row["locked_until"]:
            locked_until = datetime.fromisoformat(row["locked_until"])
            if datetime.now() < locked_until:
                conn.close()
                return {"error": "locked", "until": locked_until.strftime("%H:%M")}

        c.execute("""
            SELECT id, username, password_hash, role, full_name, email,
                   department, preferred_lang, preferred_theme, is_active
            FROM users WHERE username=?
        """, (username,))
        user = c.fetchone()

        if user and user["password_hash"] == pwd_hash and user["is_active"]:
            # Başarılı giriş: sıfırla
            c.execute("""
                UPDATE users SET failed_attempts=0, locked_until=NULL, last_login=?
                WHERE username=?
            """, (datetime.now().isoformat(), username))
            conn.commit()
            conn.close()
            return {
                "id":       user["id"],
                "username": user["username"],
                "role":     user["role"],
                "full_name": user["full_name"] or username,
                "email":    user["email"],
                "department": user["department"],
                "lang":     user["preferred_lang"],
                "theme":    user["preferred_theme"],
            }

        # Başarısız giriş
        if user:
            c.execute("UPDATE users SET failed_attempts=failed_attempts+1 WHERE username=?", (username,))
            c.execute("SELECT failed_attempts FROM users WHERE username=?", (username,))
            attempts = c.fetchone()["failed_attempts"]
            from config import MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lock_time = (datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
                c.execute("UPDATE users SET locked_until=? WHERE username=?", (lock_time, username))
            conn.commit()
        conn.close()
        return None

    def get_all_users(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT id, username, full_name, role, email, department, is_active, last_login, created_at FROM users",
            conn
        )
        conn.close()
        return df

    def update_user_preferences(self, username: str, lang: str, theme: str):
        conn = self.get_connection()
        conn.execute(
            "UPDATE users SET preferred_lang=?, preferred_theme=?, updated_at=? WHERE username=?",
            (lang, theme, datetime.now().isoformat(), username)
        )
        conn.commit()
        conn.close()

    def update_user_password(self, username: str, new_password: str):
        conn = self.get_connection()
        pwd_hash = hashlib.sha256(new_password.encode()).hexdigest()
        conn.execute(
            "UPDATE users SET password_hash=?, updated_at=? WHERE username=?",
            (pwd_hash, datetime.now().isoformat(), username)
        )
        conn.commit()
        conn.close()

    def toggle_user_status(self, username: str) -> bool:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT is_active FROM users WHERE username=?", (username,))
        row = c.fetchone()
        new_status = 0 if row["is_active"] else 1
        conn.execute("UPDATE users SET is_active=? WHERE username=?", (new_status, username))
        conn.commit()
        conn.close()
        return bool(new_status)

    # ──────────────────────────────────────────────────────────────
    #  MÜŞTERİ YÖNETİMİ
    # ──────────────────────────────────────────────────────────────

    def _generate_customer_code(self) -> str:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM customers")
        count = c.fetchone()["cnt"]
        conn.close()
        return f"PQC-{datetime.now().year}-{str(count+1).zfill(6)}"

    def add_customer(self, data: dict) -> str:
        """Yeni müşteri ekler ve oluşturulan müşteri kodunu döndürür."""
        conn = self.get_connection()
        c = conn.cursor()
        code = self._generate_customer_code()
        c.execute("""
            INSERT INTO customers (
                customer_code, full_name, national_id, birth_date, age, phone, email,
                address, city, occupation, employer, employment_years, monthly_income,
                additional_income, total_debt, credit_card_count, late_payment_count,
                credit_history_years, home_ownership, monthly_expenses, dependents,
                education_level, assigned_analyst, tags, notes
            ) VALUES (
                :customer_code, :full_name, :national_id, :birth_date, :age, :phone, :email,
                :address, :city, :occupation, :employer, :employment_years, :monthly_income,
                :additional_income, :total_debt, :credit_card_count, :late_payment_count,
                :credit_history_years, :home_ownership, :monthly_expenses, :dependents,
                :education_level, :assigned_analyst, :tags, :notes
            )
        """, {**data, "customer_code": code,
              "tags": data.get("tags", "[]"),
              "notes": data.get("notes", "")})
        conn.commit()
        conn.close()
        return code

    def get_customer_by_code(self, code: str) -> dict | None:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE customer_code=?", (code,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_customers(self, active_only=True) -> pd.DataFrame:
        conn = self.get_connection()
        query = "SELECT * FROM customers"
        if active_only:
            query += " WHERE is_active=1"
        query += " ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def search_customers(self, query: str) -> pd.DataFrame:
        conn = self.get_connection()
        like = f"%{query}%"
        df = pd.read_sql_query("""
            SELECT * FROM customers
            WHERE full_name LIKE ? OR customer_code LIKE ? OR national_id LIKE ? OR email LIKE ?
            ORDER BY created_at DESC
        """, conn, params=(like, like, like, like))
        conn.close()
        return df

    def update_customer_score(self, customer_code: str, score: float,
                               risk_category: str, analyst: str):
        conn = self.get_connection()
        conn.execute("""
            UPDATE customers SET credit_score=?, risk_category=?, updated_at=?
            WHERE customer_code=?
        """, (score, risk_category, datetime.now().isoformat(), customer_code))
        conn.execute("""
            INSERT INTO score_history (customer_id, customer_code, credit_score, risk_category, calculated_by)
            SELECT id, ?, ?, ?, ? FROM customers WHERE customer_code=?
        """, (customer_code, score, risk_category, analyst, customer_code))
        conn.commit()
        conn.close()

    def update_customer(self, customer_code: str, data: dict):
        conn = self.get_connection()
        data["updated_at"] = datetime.now().isoformat()
        data["customer_code"] = customer_code
        fields = ", ".join([f"{k}=:{k}" for k in data if k != "customer_code"])
        conn.execute(f"UPDATE customers SET {fields} WHERE customer_code=:customer_code", data)
        conn.commit()
        conn.close()

    def add_customer_tag(self, customer_code: str, tag: str):
        cust = self.get_customer_by_code(customer_code)
        if cust:
            tags = json.loads(cust.get("tags") or "[]")
            if tag not in tags:
                tags.append(tag)
            self.update_customer(customer_code, {"tags": json.dumps(tags, ensure_ascii=False)})

    def import_customers_from_df(self, df: pd.DataFrame, analyst: str) -> int:
        """CSV/XLSX'ten toplu müşteri yükleme. Eklenen sayısını döndürür."""
        count = 0
        for _, row in df.iterrows():
            try:
                data = row.to_dict()
                data["assigned_analyst"] = analyst
                self.add_customer(data)
                count += 1
            except Exception:
                pass
        return count

    def get_score_history(self, customer_code: str) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT * FROM score_history WHERE customer_code=? ORDER BY recorded_at ASC
        """, conn, params=(customer_code,))
        conn.close()
        return df

    # ──────────────────────────────────────────────────────────────
    #  BAŞVURU YÖNETİMİ
    # ──────────────────────────────────────────────────────────────

    def _generate_application_no(self) -> str:
        import random
        return f"APP-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000,99999)}"

    def create_application(self, data: dict) -> str:
        conn = self.get_connection()
        c = conn.cursor()
        app_no = self._generate_application_no()
        c.execute("""
            INSERT INTO applications (
                application_no, customer_id, customer_code, loan_type, requested_amount,
                requested_term, purpose, collateral_type, collateral_value,
                monthly_payment_est, interest_rate_est, status, created_by
            ) VALUES (
                :application_no, :customer_id, :customer_code, :loan_type, :requested_amount,
                :requested_term, :purpose, :collateral_type, :collateral_value,
                :monthly_payment_est, :interest_rate_est, :status, :created_by
            )
        """, {**data, "application_no": app_no})
        conn.commit()
        conn.close()
        return app_no

    def get_applications(self, customer_code: str = None) -> pd.DataFrame:
        conn = self.get_connection()
        if customer_code:
            df = pd.read_sql_query(
                "SELECT * FROM applications WHERE customer_code=? ORDER BY created_at DESC",
                conn, params=(customer_code,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM applications ORDER BY created_at DESC", conn
            )
        conn.close()
        return df

    def update_application_status(self, app_no: str, status: str,
                                   analyst_notes: str, processed_by: str,
                                   ml_decision: int = None, ml_prob: float = None,
                                   fraud_score: float = None):
        conn = self.get_connection()
        conn.execute("""
            UPDATE applications SET
                status=?, analyst_notes=?, processed_by=?, processed_at=?,
                ml_decision=?, ml_probability=?, fraud_score=?
            WHERE application_no=?
        """, (status, analyst_notes, processed_by, datetime.now().isoformat(),
              ml_decision, ml_prob, fraud_score, app_no))
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────────────────────
    #  ANALİZ LOGLAMA
    # ──────────────────────────────────────────────────────────────

    def log_analysis(self, analyst: str, customer_code: str, customer_name: str,
                     age: int, income: float, debt: float, dti: float,
                     late_payments: int, card_count: int, credit_score: float,
                     ml_result: int, ml_prob: float, fraud_score: float,
                     risk_category: str, action: str = "Analiz"):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO analysis_logs (
                analyst_name, customer_code, customer_name, age, income, debt,
                dti_ratio, late_payments, card_count, credit_score,
                ml_result, ml_probability, fraud_score, risk_category, action_taken
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (analyst, customer_code, customer_name, age, income, debt,
              dti, late_payments, card_count, credit_score,
              ml_result, ml_prob, fraud_score, risk_category, action))
        conn.commit()
        conn.close()

    def get_recent_logs(self, limit: int = 100) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query(
            f"SELECT * FROM analysis_logs ORDER BY timestamp DESC LIMIT {limit}",
            conn
        )
        conn.close()
        return df

    # ──────────────────────────────────────────────────────────────
    #  MÜŞTERİ NOTLARI
    # ──────────────────────────────────────────────────────────────

    def add_note(self, customer_id: int, author: str, text: str,
                 note_type: str = "Genel", pinned: bool = False):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO customer_notes (customer_id, author, note_text, note_type, is_pinned)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, author, text, note_type, int(pinned)))
        conn.commit()
        conn.close()

    def get_customer_notes(self, customer_id: int) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT * FROM customer_notes WHERE customer_id=? ORDER BY is_pinned DESC, created_at DESC
        """, conn, params=(customer_id,))
        conn.close()
        return df

    # ──────────────────────────────────────────────────────────────
    #  ERKEN UYARI SİSTEMİ
    # ──────────────────────────────────────────────────────────────

    def add_warning(self, customer_id: int, customer_code: str,
                    warning_type: str, severity: str, message: str):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO early_warnings (customer_id, customer_code, warning_type, severity, message)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, customer_code, warning_type, severity, message))
        conn.commit()
        conn.close()

    def get_active_warnings(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT ew.*, c.full_name FROM early_warnings ew
            LEFT JOIN customers c ON ew.customer_id = c.id
            WHERE ew.is_resolved=0 ORDER BY ew.created_at DESC
        """, conn)
        conn.close()
        return df

    def resolve_warning(self, warning_id: int, resolved_by: str):
        conn = self.get_connection()
        conn.execute("""
            UPDATE early_warnings SET is_resolved=1, resolved_by=?, resolved_at=?
            WHERE id=?
        """, (resolved_by, datetime.now().isoformat(), warning_id))
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────────────────────
    #  FİNANSAL HEDEFLER
    # ──────────────────────────────────────────────────────────────

    def add_financial_goal(self, customer_id: int, goal_type: str,
                            target_score: float, current_score: float,
                            target_date: str, description: str):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO financial_goals
                (customer_id, goal_type, target_score, current_score, target_date, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, goal_type, target_score, current_score, target_date, description))
        conn.commit()
        conn.close()

    def get_customer_goals(self, customer_id: int) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM financial_goals WHERE customer_id=? ORDER BY created_at DESC",
            conn, params=(customer_id,)
        )
        conn.close()
        return df

    # ──────────────────────────────────────────────────────────────
    #  PORTFÖY İSTATİSTİKLERİ (Dashboard KPI'ları İçin)
    # ──────────────────────────────────────────────────────────────

    def get_portfolio_stats(self) -> dict:
        conn = self.get_connection()
        c = conn.cursor()

        stats = {}

        c.execute("SELECT COUNT(*) FROM customers WHERE is_active=1")
        stats["total_customers"] = c.fetchone()[0]

        c.execute("SELECT AVG(credit_score) FROM customers WHERE credit_score IS NOT NULL")
        stats["avg_score"] = round(c.fetchone()[0] or 0, 1)

        c.execute("SELECT COUNT(*) FROM applications WHERE status='Onaylandı'")
        approved = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM applications")
        total_apps = c.fetchone()[0]
        stats["approval_rate"] = round((approved / total_apps * 100) if total_apps > 0 else 0, 1)

        c.execute("SELECT SUM(requested_amount) FROM applications WHERE status='Onaylandı'")
        stats["total_portfolio"] = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM applications WHERE status='İncelemede'")
        stats["pending_applications"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM early_warnings WHERE is_resolved=0")
        stats["active_warnings"] = c.fetchone()[0]

        c.execute("""
            SELECT risk_category, COUNT(*) as cnt FROM customers
            WHERE risk_category IS NOT NULL GROUP BY risk_category
        """)
        stats["risk_distribution"] = {row[0]: row[1] for row in c.fetchall()}

        c.execute("""
            SELECT segment, COUNT(*) as cnt FROM customers
            WHERE segment IS NOT NULL GROUP BY segment
        """)
        stats["segment_distribution"] = {row[0]: row[1] for row in c.fetchall()}

        conn.close()
        return stats

    def get_monthly_application_trend(self) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT strftime('%Y-%m', created_at) as month,
                   COUNT(*) as applications,
                   SUM(CASE WHEN status='Onaylandı' THEN 1 ELSE 0 END) as approved
            FROM applications
            GROUP BY month ORDER BY month
        """, conn)
        conn.close()
        return df

    # ──────────────────────────────────────────────────────────────
    #  SİSTEM LOGLAMA
    # ──────────────────────────────────────────────────────────────

    def sys_log(self, level: str, message: str, module: str = None, user: str = None):
        conn = self.get_connection()
        conn.execute("""
            INSERT INTO system_logs (level, module, message, user)
            VALUES (?, ?, ?, ?)
        """, (level, module, message, user))
        conn.commit()
        conn.close()

    def get_system_logs(self, limit: int = 200) -> pd.DataFrame:
        conn = self.get_connection()
        df = pd.read_sql_query(
            f"SELECT * FROM system_logs ORDER BY created_at DESC LIMIT {limit}", conn
        )
        conn.close()
        return df


# Singleton instance
db = DatabaseHandler()

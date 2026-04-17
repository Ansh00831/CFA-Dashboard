import sqlite3
import os

DB_PATH = "study.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                date TEXT PRIMARY KEY,
                hours REAL,
                topic TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                done INTEGER DEFAULT 0,
                due_date TEXT,
                completed_date TEXT
            )
        """)
        
        # Database Migration: Safely add new date columns if they don't exist yet
        c.execute("PRAGMA table_info(todos)")
        cols = [row[1] for row in c.fetchall()]
        if "due_date" not in cols:
            c.execute("ALTER TABLE todos ADD COLUMN due_date TEXT")
        if "completed_date" not in cols:
            c.execute("ALTER TABLE todos ADD COLUMN completed_date TEXT")
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS module_states (
                topic_key TEXT,
                module TEXT,
                is_done INTEGER DEFAULT 0,
                confidence INTEGER DEFAULT 3,
                completion_date TEXT,
                PRIMARY KEY (topic_key, module)
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS mock_scores (
                mock TEXT PRIMARY KEY,
                date TEXT,
                target REAL,
                overall REAL,
                FSA REAL, Quant REAL, Fixed_Income REAL,
                Equity REAL, Ethics REAL, Derivatives REAL,
                PM REAL, Economics REAL, Corp_Issuers REAL, Alts REAL
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                topic TEXT,
                error_type TEXT,
                concept TEXT,
                tags TEXT
            )
        """)
        
        c.execute("SELECT COUNT(*) FROM mock_scores")
        if c.fetchone()[0] == 0:
            mocks =[
                ("Mock 1", "2026-08-25", 58, 0),
                ("Mock 2", "2026-09-13", 63, 0),
                ("Mock 3", "2026-09-28", 68, 0),
                ("Mock 4", "2026-10-12", 70, 0),
                ("Mock 5", "2026-11-08", 72, 0)
            ]
            for m in mocks:
                c.execute("INSERT INTO mock_scores (mock, date, target, overall) VALUES (?,?,?,?)", m)
                
        conn.commit()
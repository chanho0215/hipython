import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/service_logs.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prediction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        city TEXT,
        input_datetime TEXT,
        season INTEGER,
        holiday INTEGER,
        workingday INTEGER,
        weather INTEGER,
        temp REAL,
        atemp REAL,
        humidity REAL,
        windspeed REAL,
        predicted_count REAL
    )
    """)
    conn.commit()
    conn.close()

def save_log(data: dict, predicted_count: float):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO prediction_logs (
        created_at, city, input_datetime, season, holiday, workingday,
        weather, temp, atemp, humidity, windspeed, predicted_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        data["city"],
        data["datetime"],
        data["season"],
        data["holiday"],
        data["workingday"],
        data["weather"],
        data["temp"],
        data["atemp"],
        data["humidity"],
        data["windspeed"],
        predicted_count
    ))

    conn.commit()
    conn.close()
    
def get_logs(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT id, created_at, city, input_datetime, season, holiday, workingday,
           weather, temp, atemp, humidity, windspeed, predicted_count
    FROM prediction_logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    cols = [desc[0] for desc in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    conn.close()
    return rows
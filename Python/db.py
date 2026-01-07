# db.py
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "garden_system.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

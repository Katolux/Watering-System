import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "garden_system.db"
DEMO_DB_PATH = BASE_DIR / "dev_data" / "gardenhub_demo.db"


def get_db_path():
    configured = os.environ.get("GARDENHUB_DB_PATH")
    return Path(configured).resolve() if configured else DEFAULT_DB_PATH.resolve()


def is_demo_database():
    return get_db_path() == DEMO_DB_PATH.resolve()


def get_conn():
    conn = sqlite3.connect(get_db_path(), timeout=10, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

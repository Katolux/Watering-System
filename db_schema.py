from db import get_conn


def init_beds_and_sensors_tables():
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS beds (
                bed_id TEXT PRIMARY KEY,
                active INTEGER DEFAULT 1
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                sensor_id TEXT PRIMARY KEY,
                bed_id TEXT,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (bed_id) REFERENCES beds(bed_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS plants (
                plant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                min_moisture INTEGER,
                max_moisture INTEGER,
                base_minutes INTEGER
            )
        """)


        cur.execute("""
            CREATE TABLE IF NOT EXISTS bed_plantings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bed_id TEXT NOT NULL,
                plant_id TEXT NOT NULL,
                plant_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (bed_id) REFERENCES beds(bed_id),
                FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                date TEXT NOT NULL,
                level TEXT NOT NULL,
                source TEXT NOT NULL,
                bed_id TEXT,
                message TEXT NOT NULL,
                details TEXT
            )
        """)


def init_watering_events_table():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watering_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                date TEXT,
                bed_id TEXT,
                minutes INTEGER,
                mode TEXT,
                soil_factor REAL,
                temp_factor REAL,
                rain_factor REAL,
                source_decision_id INTEGER,
                note TEXT
            )
        """)


def init_watering_decisions_table():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS watering_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                date TEXT,
                bed_id TEXT,
                plant_name TEXT,
                avg_moisture INTEGER,
                temp_max REAL,
                precipitation REAL,
                base_minutes INTEGER,
                final_minutes INTEGER,
                soil_factor REAL,
                temp_factor REAL,
                rain_factor REAL
            )
        """)


def init_sensor_readings_table():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                date TEXT NOT NULL,
                bed_id TEXT,
                sensor_id TEXT NOT NULL,
                slot INTEGER NOT NULL,
                moisture_raw INTEGER NOT NULL,
                UNIQUE (sensor_id, date, slot)
            )
        """)


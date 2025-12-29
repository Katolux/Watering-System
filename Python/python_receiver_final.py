from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timezone

DB_NAME = "garden_system.db"
app = Flask(__name__)


def init_sensor_readings_table():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            date TEXT NOT NULL,
            bed_id TEXT,
            sensor_id TEXT NOT NULL,
            moisture_raw INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_sensor_readings_table()

def save_reading(bed_id, sensor_id, moisture_raw):
  
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    date_str = now.date().isoformat()        

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sensor_readings (timestamp, date, bed_id, sensor_id, moisture_raw)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, date_str, bed_id, sensor_id, moisture_raw))
    conn.commit()
    conn.close()

@app.route("/soil", methods=["POST"])
def receive_soil():
    data = request.get_json(silent=True) or {}

    # bed is optional; allow missing / null / "test"
    bed_id = data.get("bed")  # may be None
    sensor_id = data.get("sensor")
    moisture = data.get("moisture")

    if sensor_id is None or moisture is None:
        return jsonify({"status": "error", "error": "Missing sensor or moisture"}), 400

    try:
        moisture = int(moisture)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "error": "moisture must be an integer"}), 400

    save_reading(bed_id, sensor_id, moisture)

    # ---------- DEBUG PRINT ----------
    print(
        f"[SENSOR] saved | "
        f"bed={bed_id} | "
        f"sensor={sensor_id} | "
        f"moisture={moisture}"
    )
    # ---------------------------------


    return jsonify({"status": "ok"}), 200



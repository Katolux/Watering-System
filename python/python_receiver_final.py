from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

DB_NAME = "garden_system.db"

app = Flask(__name__)

# ---------- DB INIT ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            date TEXT,
            bed_id TEXT,
            sensor_id TEXT,
            reading_index INTEGER,
            moisture_raw INTEGER
        )
    """)

    conn.commit()
    conn.close()

# ---------- HELPERS ----------
def get_next_reading_index(conn, bed_id, sensor_id, date):
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM sensor_readings
        WHERE bed_id = ? AND sensor_id = ? AND date = ?
    """, (bed_id, sensor_id, date))

    count = cur.fetchone()[0]
    return count + 1  # 1, 2, 3

# ---------- ROUTE ----------
@app.route("/soil", methods=["POST"])
def receive_soil():
    data = request.json

    bed_id = data["bed"]
    sensor_id = data["sensor"]
    moisture = int(data["moisture"])

    now = datetime.utcnow()
    date_str = now.date().isoformat()
    timestamp = now.isoformat()

    conn = sqlite3.connect(DB_NAME)

    reading_index = get_next_reading_index(
        conn, bed_id, sensor_id, date_str
    )

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sensor_readings
        (timestamp, date, bed_id, sensor_id, reading_index, moisture_raw)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        date_str,
        bed_id,
        sensor_id,
        reading_index,
        moisture
    ))

    conn.commit()
    conn.close()

    print(
        f"{date_str} | {bed_id} | {sensor_id} | "
        f"reading {reading_index} | moisture {moisture}"
    )

    return jsonify({"status": "ok", "reading_index": reading_index}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

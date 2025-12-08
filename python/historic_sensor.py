import sqlite3
from datetime import datetime, timedelta

DB_NAME = "garden_system.db"

def get_last_10_days_sensors():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cutoff = datetime.utcnow() - timedelta(days=10)

    cursor.execute(
        "SELECT * FROM sensor_data WHERE timestamp >= ? ORDER BY timestamp DESC",
        (cutoff.isoformat(),)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def print_last_10_days_sensors():
    rows = get_last_10_days_sensors()

    if not rows:
        print("No sensor data in the last 10 days.")
        return

    print("\nLast 10 Days of Sensor Data:")
    print("-" * 50)

    for ts, moisture, soil_t, air_t, hum in rows:
        print(f"{ts} | Moisture {moisture} | Soil {soil_t}°C | Air {air_t}°C | Humidity {hum}%")

    print("-" * 50)

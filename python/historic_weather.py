import sqlite3
from datetime import datetime, timedelta

DB_NAME = "garden_system.db"

# ----------------------------
# GET LAST 10 DAYS OF WEATHER
# ----------------------------
def get_last_10_days_weather():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cutoff = datetime.utcnow() - timedelta(days=10)

    cursor.execute(
        "SELECT * FROM weather_data WHERE timestamp >= ? ORDER BY timestamp DESC",
        (cutoff.isoformat(),)
    )

    rows = cursor.fetchall()
    conn.close()
    return rows

# ----------------------------
# PRINT WEATHER HISTORY
# ----------------------------
def print_last_10_days_weather():
    rows = get_last_10_days_weather()

    if not rows:
        print("No weather data in the last 10 days.")
        return

    print("\n🌤️  Last 10 Days of Weather Forecast Data:")
    print("-" * 70)

    for (
        ts,
        temp_max,
        temp_min,
        precipitation,
        sunshine,
        wind,
        humidity,
        cloud_cover,
        rain_prob
    ) in rows:
        print(
            f"{ts} | Max {temp_max}°C | Min {temp_min}°C | Rain {precipitation}mm | "
            f"Sun {sunshine}min | Wind {wind} km/h | Hum {humidity}% | "
            f"Clouds {cloud_cover}% | Rain Prob {rain_prob}%"
        )

    print("-" * 70)

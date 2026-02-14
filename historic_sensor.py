import sqlite3
from datetime import datetime, timedelta
from db import get_conn

def get_last_10_days_weather():
    with get_conn() as conn:
        cursor = conn.cursor()

        cutoff = datetime.utcnow() - timedelta(days=10)

        cursor.execute(
            """
            SELECT
                timestamp,
                temp_max,
                temp_min,
                precipitation,
                sunshine,
                wind_avg,
                humidity_avg
            FROM weather_data
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (cutoff.isoformat(),)
        )

        rows = cursor.fetchall()
        conn.close()
        return rows


def print_last_10_days_weather():
    rows = get_last_10_days_weather()

    if not rows:
        print("No weather data in the last 10 days.")
        return

    print("\n🌤️  Last 10 Days of Weather Data:")
    print("-" * 70)

    for ts, temp_max, temp_min, precipitation, sunshine, wind, humidity in rows:
        print(
            f"{ts} | "
            f"Max {temp_max:.1f}°C | "
            f"Min {temp_min:.1f}°C | "
            f"Rain {precipitation:.2f} mm | "
            f"Sun {sunshine:.0f} min | "
            f"Wind {wind if wind is not None else 'n/a'} | "
            f"Hum {humidity if humidity is not None else 'n/a'}"
        )

    print("-" * 70)

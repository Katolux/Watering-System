import sqlite3

DB_NAME = "garden_system.db"


def get_last_days_weather(days=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            date,
            temp_max,
            temp_min,
            precipitation,
            sunshine,
            daylight,
            wind_max,
            wind_dir
        FROM weather_data
        ORDER BY date DESC
        LIMIT ?
        """,
        (days,)
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def print_last_days_weather(days=10):
    rows = get_last_days_weather(days)

    if not rows:
        print("No weather data available.")
        return

    print(f"\n🌤️  Last {len(rows)} Days of Weather")
    print("-" * 70)

    for (
        date,
        temp_max,
        temp_min,
        precipitation,
        sunshine,
        daylight,
        wind_max,
        wind_dir
    ) in rows:
        print(
            f"{date} | "
            f"Max {temp_max:.1f}°C | "
            f"Min {temp_min:.1f}°C | "
            f"Rain {precipitation:.2f} mm | "
            f"Sun {sunshine:.0f} min | "
            f"Daylight {daylight:.0f} min | "
            f"Wind {wind_max:.1f} km/h @ {wind_dir:.0f}°"
        )

    print("-" * 70)

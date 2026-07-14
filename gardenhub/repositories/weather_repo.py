from datetime import datetime, date, timedelta

from gardenhub.db.connection import get_conn


def save_weather_record(record):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO weather_data (
                date,
                timestamp,
                temp_max,
                temp_min,
                precipitation,
                sunshine,
                daylight,
                wind_max,
                wind_dir
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                timestamp = excluded.timestamp,
                temp_max = excluded.temp_max,
                temp_min = excluded.temp_min,
                precipitation = excluded.precipitation,
                sunshine = excluded.sunshine,
                daylight = excluded.daylight,
                wind_max = excluded.wind_max,
                wind_dir = excluded.wind_dir
            """,
            (
                record["date"],
                datetime.utcnow().isoformat(),
                record["temp_max"],
                record["temp_min"],
                record["precipitation"],
                record["sunshine"],
                record["daylight"],
                record["wind_max"],
                record["wind_dir"],
            ),
        )


def get_latest_weather_date():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM weather_data")
        row = cur.fetchone()
    return row[0]


def should_refresh_weather():
    try:
        latest = get_latest_weather_date()
    except Exception:
        return True

    if latest is None:
        return True

    latest_date = date.fromisoformat(latest)
    return (date.today() - latest_date) >= timedelta(days=3)


def get_last_days_weather(days=10):
    with get_conn() as conn:
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
        return rows


def get_today_weather_record():
    with get_conn() as conn:
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
            WHERE date = date('now')
            LIMIT 1
            """
        )
        return cur.fetchone()


def get_today_weather():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT temp_max, precipitation
            FROM weather_data
            WHERE date = ?
        """, (date.today().isoformat(),))
        row = cur.fetchone()

    if row is None:
        raise ValueError("No weather data for today")

    return row  # (temp_max, precipitation)

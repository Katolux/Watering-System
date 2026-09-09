from datetime import datetime, date, timedelta, timezone

from gardenhub.db.connection import get_conn


WEATHER_REFRESH_INTERVAL = timedelta(hours=1)


def save_weather_record(record):
    """Save or update one daily weather record."""

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO weather_data (
                date,
                timestamp,
                temp_max,
                temp_min,
                precipitation,
                precipitation_probability_max,
                sunshine,
                daylight,
                sunrise,
                sunset,
                wind_max,
                wind_gusts_max,
                wind_dir,
                daily_weather_code,
                et0
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(date) DO UPDATE SET
                timestamp = excluded.timestamp,
                temp_max = excluded.temp_max,
                temp_min = excluded.temp_min,
                precipitation = excluded.precipitation,
                precipitation_probability_max = excluded.precipitation_probability_max,
                sunshine = excluded.sunshine,
                daylight = excluded.daylight,
                sunrise = excluded.sunrise,
                sunset = excluded.sunset,
                wind_max = excluded.wind_max,
                wind_gusts_max = excluded.wind_gusts_max,
                wind_dir = excluded.wind_dir,
                daily_weather_code = excluded.daily_weather_code,
                et0 = excluded.et0
            """,
            (
                record["date"],
                datetime.now(timezone.utc).isoformat(),
                record["temp_max"],
                record["temp_min"],
                record["precipitation"],
                record["precipitation_probability_max"],
                record["sunshine"],
                record["daylight"],
                record["sunrise"],
                record["sunset"],
                record["wind_max"],
                record["wind_gusts_max"],
                record["wind_dir"],
                record["weather_code"],
                record["et0"],
            ),
        )


def save_current_weather(record):
    """Save current conditions on today's weather row."""

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO weather_data (
                date,
                timestamp,
                current_timestamp,
                current_temperature,
                current_humidity,
                current_apparent_temperature,
                current_is_day,
                current_precipitation,
                current_weather_code,
                current_cloud_cover,
                current_pressure,
                current_wind_speed,
                current_wind_dir,
                current_wind_gusts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(date) DO UPDATE SET
                timestamp = excluded.timestamp,
                current_timestamp = excluded.current_timestamp,
                current_temperature = excluded.current_temperature,
                current_humidity = excluded.current_humidity,
                current_apparent_temperature = excluded.current_apparent_temperature,
                current_is_day = excluded.current_is_day,
                current_precipitation = excluded.current_precipitation,
                current_weather_code = excluded.current_weather_code,
                current_cloud_cover = excluded.current_cloud_cover,
                current_pressure = excluded.current_pressure,
                current_wind_speed = excluded.current_wind_speed,
                current_wind_dir = excluded.current_wind_dir,
                current_wind_gusts = excluded.current_wind_gusts
            """,
            (
                record["date"],
                datetime.now(timezone.utc).isoformat(),
                record["timestamp"],
                record["temperature"],
                record["humidity"],
                record["apparent_temperature"],
                record["is_day"],
                record["precipitation"],
                record["weather_code"],
                record["cloud_cover"],
                record["pressure"],
                record["wind_speed"],
                record["wind_direction"],
                record["wind_gusts"],
            ),
        )


def get_weather_records(days=60):
    with get_conn() as conn:
        conn.row_factory = __import__("sqlite3").Row

        rows = conn.execute(
            """
            SELECT *
            FROM weather_data
            ORDER BY date DESC
            LIMIT ?
            """,
            (days,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_latest_weather_date():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM weather_data"
        ).fetchone()

    return row[0]


def should_refresh_weather():
    """Refresh if weather has not been fetched recently."""

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT MAX(timestamp)
            FROM weather_data
            """
        ).fetchone()

    if row is None or row[0] is None:
        return True

    try:
        last_refresh = datetime.fromisoformat(row[0])

        if last_refresh.tzinfo is None:
            last_refresh = last_refresh.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - last_refresh

        return age >= WEATHER_REFRESH_INTERVAL

    except ValueError:
        return True


def get_last_days_weather(days=10):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                date,
                temp_max,
                temp_min,
                precipitation,
                precipitation_probability_max,
                sunshine,
                daylight,
                sunrise,
                sunset,
                wind_max,
                wind_gusts_max,
                wind_dir,
                daily_weather_code,
                et0
            FROM weather_data
            ORDER BY date DESC
            LIMIT ?
            """,
            (days,),
        ).fetchall()

    return rows


def get_today_weather_record():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT *
            FROM weather_data
            WHERE date = ?
            LIMIT 1
            """,
            (date.today().isoformat(),),
        ).fetchone()


def get_today_weather():
    """Return the two values currently used by the watering engine."""

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT temp_max, precipitation
            FROM weather_data
            WHERE date = ?
            """,
            (date.today().isoformat(),),
        ).fetchone()

    if row is None:
        raise ValueError("No weather data for today")

    return row

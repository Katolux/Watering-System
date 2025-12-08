import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import sqlite3
from datetime import datetime

DB_NAME = "garden_system.db"


def init_weather_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            timestamp TEXT,
            date TEXT,
            temp_max REAL,
            temp_min REAL,
            precipitation REAL,
            sunshine REAL,
            daylight REAL
        )
    """)
    conn.commit()
    conn.close()


def save_weather_record(record):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO weather_data VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.utcnow().isoformat(),
            record["date"],
            record["temp_max"],
            record["temp_min"],
            record["precipitation"],
            record["sunshine"],
            record["daylight"],
        ),
    )
    conn.commit()
    conn.close()


def refresh_weather():
    print("\n=== REFRESH WEATHER v3 – DEBUG BUILD ===")  # FINGERPRINT LINE

    init_weather_db()

    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 47.4455,
        "longitude": 9.342,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "sunshine_duration",
            "sunrise",
            "sunset",
            "precipitation_sum",
            "daylight_duration",
        ],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "cloud_cover",
            "sunshine_duration",
            "wind_speed_10m",
        ],
        "models": "best_match",
        "timezone": "auto",
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m")
    print(f"Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")

    daily = response.Daily()

    temp_max = daily.Variables(0).ValuesAsNumpy()
    temp_min = daily.Variables(1).ValuesAsNumpy()
    sunshine = daily.Variables(2).ValuesAsNumpy()
    precipitation = daily.Variables(5).ValuesAsNumpy()
    daylight = daily.Variables(6).ValuesAsNumpy()

    dates = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s"),
        end=pd.to_datetime(daily.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    )

    print("\n🌤️  Daily Forecast (Formatted)")
    print("-------------------------------------------")

    for i in range(len(dates)):
        # convert seconds → minutes
        sunshine_minutes = float(sunshine[i]) / 60
        daylight_minutes = float(daylight[i]) / 60

        record = {
            "date": str(dates[i].date()),
            "temp_max": float(temp_max[i]),
            "temp_min": float(temp_min[i]),
            "precipitation": float(precipitation[i]),
            "sunshine": sunshine_minutes,
            "daylight": daylight_minutes,
        }

        save_weather_record(record)

        print(
            f"{record['date']} | "
            f"Max {record['temp_max']:.1f}°C | "
            f"Min {record['temp_min']:.1f}°C | "
            f"Rain {record['precipitation']:.2f} mm | "
            f"Sun {sunshine_minutes:.0f} min | "
            f"Daylight {daylight_minutes:.0f} min"
        )

    print("-------------------------------------------")
    print("Weather data saved in SQLite (v3, converted).")

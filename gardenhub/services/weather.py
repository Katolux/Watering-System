from datetime import datetime, timezone

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from gardenhub.db.schema import init_weather_db
from gardenhub.repositories.weather_repo import save_current_weather, save_weather_record


def refresh_weather(latitude, longitude, timezone_name="UTC"):
    """Fetch Open-Meteo data for coordinates resolved from the active garden."""
    print("\n=== REFRESH WEATHER ===")

    init_weather_db()

    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "sunshine_duration",
            "sunrise",
            "sunset",
            "precipitation_sum",
            "daylight_duration",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant",
            "weather_code",
        ],
        "models": "best_match",
        "timezone": timezone_name,
    }

    response = openmeteo.weather_api(url, params=params)[0]
    daily = response.Daily()

    temp_max = daily.Variables(0).ValuesAsNumpy()
    temp_min = daily.Variables(1).ValuesAsNumpy()
    sunshine = daily.Variables(2).ValuesAsNumpy()
    precipitation = daily.Variables(5).ValuesAsNumpy()
    daylight = daily.Variables(6).ValuesAsNumpy()
    wind_max = daily.Variables(7).ValuesAsNumpy()
    wind_dir = daily.Variables(8).ValuesAsNumpy()
    weather_code = daily.Variables(9).ValuesAsNumpy()

    dates = pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s"),
        end=pd.to_datetime(daily.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left",
    )

    print("\nDaily Forecast (Formatted)")
    print("-------------------------------------------")

    for i in range(len(dates)):
        sunshine_minutes = float(sunshine[i]) / 60
        daylight_minutes = float(daylight[i]) / 60
        record = {
            "date": str(dates[i].date()),
            "temp_max": float(temp_max[i]),
            "temp_min": float(temp_min[i]),
            "precipitation": float(precipitation[i]),
            "sunshine": sunshine_minutes,
            "daylight": daylight_minutes,
            "wind_max": float(wind_max[i]),
            "wind_dir": float(wind_dir[i]),
            "weather_code": int(weather_code[i]),
        }
        save_weather_record(record)
        print(
            f"{record['date']} | "
            f"Max {record['temp_max']:.1f} C | "
            f"Min {record['temp_min']:.1f} C | "
            f"Rain {record['precipitation']:.2f} mm | "
            f"Sun {sunshine_minutes:.0f} min | "
            f"Daylight {daylight_minutes:.0f} min | "
            f"Wind max {record['wind_max']:.1f} km/h | "
            f"Dir {record['wind_dir']:.0f} deg"
        )

    current = response.Current()
    current_timestamp = datetime.fromtimestamp(current.Time(), tz=timezone.utc)
    save_current_weather({
        "date": current_timestamp.date().isoformat(),
        "timestamp": current_timestamp.isoformat(),
        "temperature": float(current.Variables(0).Value()),
        "humidity": float(current.Variables(1).Value()),
        "pressure": float(current.Variables(2).Value()),
        "weather_code": int(current.Variables(3).Value()),
        "wind_speed": float(current.Variables(4).Value()),
        "wind_direction": float(current.Variables(5).Value()),
    })

    print("-" * 70)
    print("Weather data saved in SQLite.")

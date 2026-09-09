from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from gardenhub.db.schema import init_weather_db
from gardenhub.repositories.weather_repo import (
    save_current_weather,
    save_weather_record,
)


WEATHER_CACHE_SECONDS = 3600
WEATHER_CACHE_PATH = Path(__file__).resolve().parents[2] / ".cache"


def _weather_session():
    """Return the shared cache-backed provider session used by every refresh path."""

    return retry(
        requests_cache.CachedSession(
            str(WEATHER_CACHE_PATH),
            expire_after=WEATHER_CACHE_SECONDS,
        ),
        retries=5,
        backoff_factor=0.2,
    )


def fetch_weather_data(
    latitude,
    longitude,
    timezone_name="UTC",
    force_refresh=False,
):

    timezone_name = timezone_name or "UTC"

    openmeteo = openmeteo_requests.Client(
        session=_weather_session()
    )

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "is_day",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ],

        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "et0_fao_evapotranspiration",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "sunshine_duration",
        ],

        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "sunrise",
            "sunset",
            "daylight_duration",
            "sunshine_duration",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
            "et0_fao_evapotranspiration",
        ],

        "models": "best_match",
        "timezone": timezone_name,
    }

    response = openmeteo.weather_api(
        url,
        params=params,
        force_refresh=force_refresh,
    )[0]

    raw_timezone = response.Timezone()

    if isinstance(raw_timezone, bytes):
        response_timezone = raw_timezone.decode()
    elif raw_timezone:
        response_timezone = str(raw_timezone)
    else:
        response_timezone = timezone_name

    # ==============================================================
    # CURRENT
    # ==============================================================

    current = response.Current()

    current_timestamp = (
        pd.to_datetime(
            current.Time(),
            unit="s",
            utc=True,
        )
        .tz_convert(response_timezone)
    )

    current_data = {
        "date": current_timestamp.date().isoformat(),
        "timestamp": current_timestamp.isoformat(),
        "temperature": float(current.Variables(0).Value()),
        "humidity": float(current.Variables(1).Value()),
        "apparent_temperature": float(current.Variables(2).Value()),
        "is_day": int(current.Variables(3).Value()),
        "precipitation": float(current.Variables(4).Value()),
        "weather_code": int(current.Variables(5).Value()),
        "cloud_cover": float(current.Variables(6).Value()),
        "pressure": float(current.Variables(7).Value()),
        "wind_speed": float(current.Variables(8).Value()),
        "wind_direction": float(current.Variables(9).Value()),
        "wind_gusts": float(current.Variables(10).Value()),
    }

    # ==============================================================
    # HOURLY
    # ==============================================================

    hourly = response.Hourly()

    hourly_dates = pd.date_range(
        start=pd.to_datetime(
            hourly.Time(),
            unit="s",
            utc=True,
        ),
        end=pd.to_datetime(
            hourly.TimeEnd(),
            unit="s",
            utc=True,
        ),
        freq=pd.Timedelta(
            seconds=hourly.Interval()
        ),
        inclusive="left",
    ).tz_convert(response_timezone)

    hourly_data = pd.DataFrame({
        "date": hourly_dates,
        "temperature": hourly.Variables(0).ValuesAsNumpy(),
        "humidity": hourly.Variables(1).ValuesAsNumpy(),
        "apparent_temperature": hourly.Variables(2).ValuesAsNumpy(),
        "precipitation_probability": hourly.Variables(3).ValuesAsNumpy(),
        "precipitation": hourly.Variables(4).ValuesAsNumpy(),
        "weather_code": hourly.Variables(5).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(6).ValuesAsNumpy(),
        "et0": hourly.Variables(7).ValuesAsNumpy(),
        "wind_speed": hourly.Variables(8).ValuesAsNumpy(),
        "wind_direction": hourly.Variables(9).ValuesAsNumpy(),
        "wind_gusts": hourly.Variables(10).ValuesAsNumpy(),
        "sunshine_duration": hourly.Variables(11).ValuesAsNumpy(),
    })

    # ==============================================================
    # DAILY
    # ==============================================================

    daily = response.Daily()

    daily_dates = pd.date_range(
        start=pd.to_datetime(
            daily.Time(),
            unit="s",
            utc=True,
        ),
        end=pd.to_datetime(
            daily.TimeEnd(),
            unit="s",
            utc=True,
        ),
        freq=pd.Timedelta(
            seconds=daily.Interval()
        ),
        inclusive="left",
    ).tz_convert(response_timezone)

    weather_code = daily.Variables(0).ValuesAsNumpy()
    temp_max = daily.Variables(1).ValuesAsNumpy()
    temp_min = daily.Variables(2).ValuesAsNumpy()
    sunrise = daily.Variables(3).ValuesInt64AsNumpy()
    sunset = daily.Variables(4).ValuesInt64AsNumpy()
    daylight = daily.Variables(5).ValuesAsNumpy()
    sunshine = daily.Variables(6).ValuesAsNumpy()
    precipitation = daily.Variables(7).ValuesAsNumpy()
    precipitation_probability_max = daily.Variables(8).ValuesAsNumpy()
    wind_max = daily.Variables(9).ValuesAsNumpy()
    wind_gusts_max = daily.Variables(10).ValuesAsNumpy()
    wind_direction = daily.Variables(11).ValuesAsNumpy()
    et0 = daily.Variables(12).ValuesAsNumpy()

    sunrise_dates = (
        pd.to_datetime(
            sunrise,
            unit="s",
            utc=True,
        )
        .tz_convert(response_timezone)
    )

    sunset_dates = (
        pd.to_datetime(
            sunset,
            unit="s",
            utc=True,
        )
        .tz_convert(response_timezone)
    )

    daily_records = []

    for i in range(len(daily_dates)):
        daily_records.append({
            "date": daily_dates[i].date().isoformat(),
            "weather_code": int(weather_code[i]),
            "temp_max": float(temp_max[i]),
            "temp_min": float(temp_min[i]),
            "sunrise": sunrise_dates[i].isoformat(),
            "sunset": sunset_dates[i].isoformat(),
            "daylight": float(daylight[i]) / 60,
            "sunshine": float(sunshine[i]) / 60,
            "precipitation": float(precipitation[i]),
            "precipitation_probability_max": float(
                precipitation_probability_max[i]
            ),
            "wind_max": float(wind_max[i]),
            "wind_gusts_max": float(wind_gusts_max[i]),
            "wind_dir": float(wind_direction[i]),
            "et0": float(et0[i]),
        })

    return {
        "timezone": response_timezone,
        "current": current_data,
        "hourly": hourly_data,
        "daily": daily_records,
    }


def refresh_weather(
    latitude,
    longitude,
    timezone_name="UTC",
    force_refresh=False,
):

    init_weather_db()

    weather = fetch_weather_data(
        latitude,
        longitude,
        timezone_name,
        force_refresh=force_refresh,
    )

    save_current_weather(
        weather["current"]
    )

    for record in weather["daily"]:
        save_weather_record(record)

    return weather

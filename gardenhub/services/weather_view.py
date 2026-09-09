import math
from datetime import date, datetime, timezone

from gardenhub.repositories.weather_repo import get_weather_records
from gardenhub.services.garden_context import (
    get_active_garden,
    get_garden_context,
)


WEATHER_CODES = {
    0: ("Clear", "sun"),
    1: ("Mainly clear", "sun"),
    2: ("Partly cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "cloud"),
    48: ("Rime fog", "cloud"),
    51: ("Light drizzle", "rain"),
    53: ("Drizzle", "rain"),
    55: ("Heavy drizzle", "rain"),
    56: ("Freezing drizzle", "rain"),
    57: ("Heavy freezing drizzle", "rain"),
    61: ("Light rain", "rain"),
    63: ("Rain", "rain"),
    65: ("Heavy rain", "rain"),
    66: ("Freezing rain", "rain"),
    67: ("Heavy freezing rain", "rain"),
    71: ("Light snow", "snow"),
    73: ("Snow", "snow"),
    75: ("Heavy snow", "snow"),
    77: ("Snow grains", "snow"),
    80: ("Light rain showers", "rain"),
    81: ("Rain showers", "rain"),
    82: ("Heavy rain showers", "rain"),
    85: ("Snow showers", "snow"),
    86: ("Heavy snow showers", "snow"),
    95: ("Thunderstorm", "storm"),
    96: ("Thunderstorm with hail", "storm"),
    99: ("Severe thunderstorm", "storm"),
}


def _weather_condition(code):
    try:
        return WEATHER_CODES.get(int(code), ("Conditions unavailable", "cloud"))
    except (TypeError, ValueError):
        return "Conditions unavailable", "cloud"


def _updated_label(value):
    if not value:
        return "Update time unavailable"
    try:
        updated = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        minutes = max(0, int((datetime.now(timezone.utc) - updated).total_seconds() / 60))
    except (TypeError, ValueError):
        return "Update time unavailable"
    if minutes < 1:
        return "Updated just now"
    if minutes < 60:
        return f"Updated {minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"Updated {hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"Updated {days} day{'s' if days != 1 else ''} ago"


def _garden_impact(today):
    if not today:
        return "Weather guidance will appear after the next successful update."
    rain = today.get("precipitation") or 0
    wind = today.get("wind_max") or 0
    high = today.get("temp_max")
    if rain >= 10:
        return "Substantial rain is expected. Outdoor watering may not be needed."
    if rain >= 2:
        return "Rain is expected. Check soil conditions before watering."
    if high is not None and high >= 30:
        return "Hot conditions are expected. Check plants for heat stress."
    if wind >= 30:
        return "Strong wind is expected. Secure vulnerable pots and supports."
    return "Mild conditions are expected with no major weather pressure today."


def get_weather_snapshot(days=60, garden_context=None, current_data=None, hourly_data=None):
    garden_context = garden_context or get_garden_context()
    active_garden = get_active_garden(garden_context) or {}
    location = active_garden.get("location") or {}
    records = get_weather_records(days)
    today_date = datetime.now(timezone.utc).date()

    for record in records:
        record["date_value"] = date.fromisoformat(record["date"])
        record["condition"], record["condition_icon"] = _weather_condition(
            record.get("daily_weather_code")
        )
        record["day_label"] = record["date_value"].strftime("%a")
        record["date_label"] = (
            f"{record['date_value'].strftime('%b')} {record['date_value'].day}"
        )

    today = next((row for row in records if row["date_value"] == today_date), None)
    forecast = sorted(
        (row for row in records if row["date_value"] > today_date),
        key=lambda row: row["date_value"],
    )
    history = sorted(
        (row for row in records if row["date_value"] <= today_date),
        key=lambda row: row["date_value"],
    )
    insight_records = history[-14:]

    if current_data is not None:
        current_code = current_data.get("weather_code")
        current_condition, current_icon = _weather_condition(current_code)

        current = {
            "timestamp": current_data.get("timestamp"),
            "temperature": current_data.get("temperature"),
            "humidity": current_data.get("humidity"),
            "apparent_temperature": current_data.get("apparent_temperature"),
            "is_day": current_data.get("is_day"),
            "precipitation": current_data.get("precipitation"),
            "cloud_cover": current_data.get("cloud_cover"),
            "pressure": current_data.get("pressure"),
            "wind_speed": current_data.get("wind_speed"),
            "wind_direction": current_data.get("wind_direction"),
            "wind_gusts": current_data.get("wind_gusts"),
            "weather_code": current_code,
            "condition": current_condition,
            "condition_icon": current_icon,
            "updated_label": _updated_label(current_data.get("timestamp")),
        }

    else:
        current_code = today.get("current_weather_code") if today else None
        current_condition, current_icon = _weather_condition(current_code)

        current = {
            "timestamp": today.get("current_timestamp") if today else None,
            "temperature": today.get("current_temperature") if today else None,
            "humidity": today.get("current_humidity") if today else None,
            "apparent_temperature": (
                today.get("current_apparent_temperature") if today else None
            ),
            "is_day": today.get("current_is_day") if today else None,
            "precipitation": (
                today.get("current_precipitation") if today else None
            ),
            "cloud_cover": (
                today.get("current_cloud_cover") if today else None
            ),
            "pressure": today.get("current_pressure") if today else None,
            "wind_speed": today.get("current_wind_speed") if today else None,
            "wind_direction": (
                today.get("current_wind_dir") if today else None
            ),
            "wind_gusts": (
                today.get("current_wind_gusts") if today else None
            ),
            "weather_code": current_code,
            "condition": current_condition,
            "condition_icon": current_icon,
            "updated_label": _updated_label(
                (today.get("current_timestamp") or today.get("timestamp"))
                if today
                else None
            ),
        }
    
    total_rain = sum(row.get("precipitation") or 0 for row in insight_records)
    wet_days = sum(1 for row in insight_records if (row.get("precipitation") or 0) > 0)
    dry_days = len(insight_records) - wet_days
    highs = [row["temp_max"] for row in insight_records if row.get("temp_max") is not None]
    lows = [row["temp_min"] for row in insight_records if row.get("temp_min") is not None]
    winds = [row["wind_max"] for row in insight_records if row.get("wind_max") is not None]

    insights = [
        {
            "icon": "rain",
            "text": (
                f"{total_rain:.1f} mm of rain across {wet_days} wet "
                f"day{'s' if wet_days != 1 else ''}"
            ),
        },
        {
            "icon": "sun",
            "text": f"{dry_days} dry day{'s' if dry_days != 1 else ''} in the selected period",
        },
    ]
    if highs and lows:
        insights.append(
            {
                "icon": "thermometer",
                "text": f"Recorded range: {min(lows):.1f}°C to {max(highs):.1f}°C",
            }
        )
    if winds:
        insights.append(
            {"icon": "wind", "text": f"Strongest recorded wind: {max(winds):.1f} km/h"}
        )
    if len(insight_records) >= 14:
        previous = insight_records[:7]
        latest = insight_records[-7:]
        previous_average = sum(
            (row["temp_max"] + row["temp_min"]) / 2 for row in previous
        ) / len(previous)
        latest_average = sum(
            (row["temp_max"] + row["temp_min"]) / 2 for row in latest
        ) / len(latest)
        change = latest_average - previous_average
        insights.append(
            {
                "icon": "trend",
                "text": (
                    f"Average temperature is {abs(change):.1f}°C "
                    f"{'warmer' if change >= 0 else 'cooler'} than the previous week"
                ),
            }
        )
    hourly_records = []

    if hourly_data is not None:
        for _, row in hourly_data.iterrows():
            condition, condition_icon = _weather_condition(
                row["weather_code"]
            )

            sunshine_seconds = float(row.get("sunshine_duration", 0) or 0)
            if not math.isfinite(sunshine_seconds):
                sunshine_seconds = 0
            sunshine_minutes = min(
                60,
                max(0, sunshine_seconds / 60),
            )
            timestamp = row["date"]

            hourly_records.append({
                "time": row["date"].isoformat(),
                "date_label": f"{timestamp.strftime('%a')} {timestamp.day}",
                "temperature": float(row["temperature"]),
                "humidity": float(row["humidity"]),
                "apparent_temperature": float(row["apparent_temperature"]),
                "sunshine_minutes": sunshine_minutes,
                "precipitation_probability": float(
                    row["precipitation_probability"]
                ),
                "precipitation": float(row["precipitation"]),
                "weather_code": int(row["weather_code"]),
                "condition": condition,
                "condition_icon": condition_icon,
                "cloud_cover": float(row["cloud_cover"]),
                "et0": float(row["et0"]),
                "wind_speed": float(row["wind_speed"]),
                "wind_direction": float(row["wind_direction"]),
                "wind_gusts": float(row["wind_gusts"]),
            })

    current_hour = (current.get("timestamp") or "")[:13]
    if current_hour:
        hourly_records = [
            record
            for record in hourly_records
            if record["time"][:13] >= current_hour
        ]
    hourly_records = hourly_records[:24]

    previous_date = None
    for record in hourly_records:
        record_date = record["time"][:10]
        record["is_new_day"] = previous_date is not None and record_date != previous_date
        previous_date = record_date

    return {
        "location": {
            **location,
            "label": location.get("address_label")
            or (
                f"{location['latitude']:.4f}°N, {location['longitude']:.4f}°E"
                if location.get("latitude") is not None
                and location.get("longitude") is not None
                else "Location unavailable"
            ),
        },
        "current": current,
        "today": today,
        "forecast": forecast,
        "history": list(reversed(history)),
        "hourly": hourly_records,
        "summary": {
            "days": len(insight_records),
            "total_rain": total_rain,
            "wet_days": wet_days,
            "dry_days": dry_days,
            "highest": max(highs) if highs else None,
            "lowest": min(lows) if lows else None,
            "strongest_wind": max(winds) if winds else None,
        },
        "garden_impact": _garden_impact(today),
        "insights": insights,
    }


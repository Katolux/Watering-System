import time
from datetime import datetime, date

from gardenhub.services.watering_engine import run_watering_engine
from gardenhub.repositories.sensors_repo import get_today_moisture_slots
from gardenhub.repositories.system_events_repo import log_system_event
from gardenhub.repositories.weather_repo import should_refresh_weather
from gardenhub.services.weather import refresh_weather
from gardenhub.services.garden_context import (
    get_garden_context,
    get_weather_coordinates,
)


last_run_date = None


def should_run():
    now = datetime.now()
    hour = now.hour

    if 5 <= hour <= 10:
        slots = get_today_moisture_slots()

        for bed_slots in slots.values():
            if 1 in bed_slots:
                return True

        if hour >= 9:
            log_system_event(
                level="WARNING",
                source="scheduler",
                message="Slot1 missing - forced engine run",
            )
            return True

    return False


if __name__ == "__main__":
    while True:
        try:
            today = date.today()

            # WEATHER REFRESH
            if should_refresh_weather():
                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Starting weather refresh",
                )

                coordinates = get_weather_coordinates(
                    get_garden_context(False)
                )

                refresh_weather(
                    coordinates["latitude"],
                    coordinates["longitude"],
                    coordinates["timezone"],
                    force_refresh=True,
                )

                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Completed weather refresh",
                )

            # WATERING ENGINE
            if should_run() and last_run_date != today:
                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Starting watering engine run",
                )

                run_watering_engine()
                last_run_date = today

                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Completed watering engine run",
                )

                time.sleep(3600)

        except Exception as e:
            log_system_event(
                level="ERROR",
                source="scheduler",
                message="Scheduler crashed during execution",
                details=str(e),
            )

            time.sleep(60)

        time.sleep(60)
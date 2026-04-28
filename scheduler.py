import time
from datetime import datetime, date, timedelta

from watering_engine import run_watering_engine
from repositories import get_today_moisture_slots
from system_events_repo import log_system_event
from get_weather_new import refresh_weather


# Track last successful runs
last_run_date = None
last_weather_refresh = None
WEATHER_REFRESH_INTERVAL = timedelta(days=3)


def should_run():
    now = datetime.now()
    hour = now.hour

    # Only consider running in morning window
    if 5 <= hour <= 10:
        slots = get_today_moisture_slots()

        # If slot 1 exists anywhere -> run
        for bed_slots in slots.values():
            if 1 in bed_slots:
                return True

        # Fallback: if it's after 09:00 and slot1 is still missing, run anyway
        if hour >= 9:
            log_system_event(
                level="WARNING",
                source="scheduler",
                message="Slot1 missing - forced engine run"
            )
            return True

    return False


def should_refresh_weather():
    global last_weather_refresh

    now = datetime.now()

    if last_weather_refresh is None:
        return True

    if now - last_weather_refresh >= WEATHER_REFRESH_INTERVAL:
        return True

    return False


if __name__ == "__main__":
    while True:
        try:
            today = date.today()
            now = datetime.now()

            # WEATHER REFRESH
            if should_refresh_weather():
                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Starting weather refresh"
                )

                refresh_weather()
                last_weather_refresh = now

                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Completed weather refresh"
                )

            # WATERING ENGINE
            if should_run() and last_run_date != today:
                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Starting watering engine run"
                )

                run_watering_engine()
                last_run_date = today

                log_system_event(
                    level="INFO",
                    source="scheduler",
                    message="Completed watering engine run"
                )

                # After a run, sleep longer (avoid re-running within the window)
                time.sleep(3600)

        except Exception as e:
            log_system_event(
                level="ERROR",
                source="scheduler",
                message="Scheduler crashed during execution",
                details=str(e)
            )
            time.sleep(60)

        time.sleep(60)
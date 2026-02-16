import time
from datetime import datetime, date

from watering_engine import run_watering_engine
from repositories import get_today_moisture_slots
from system_events_repo import log_system_event


# Track last successful run so we don't run multiple times per day
last_run_date = None


def should_run():
    now = datetime.now()
    hour = now.hour
    minute = now.minute

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


if __name__ == "__main__":
    while True:
        try:
            today = date.today()

            # Run at most once per day
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
                message="Scheduler crashed during engine execution",
                details=str(e)
            )
            time.sleep(60)

        time.sleep(60)

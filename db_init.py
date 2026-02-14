from db_schema import (
    init_beds_and_sensors_tables,
    init_sensor_readings_table,
    init_watering_events_table,
    init_watering_decisions_table,
)

def init_all_tables():
    init_beds_and_sensors_tables()
    init_sensor_readings_table()
    init_watering_events_table()
    init_watering_decisions_table()

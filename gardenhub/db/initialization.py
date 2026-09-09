from gardenhub.db.schema import (
    init_beds_and_sensors_tables,
    init_sensor_readings_table,
    init_watering_events_table,
    init_watering_decisions_table,
    init_weather_db,
    init_planner_layouts_table,
    init_garden_location_table,
)


def init_all_tables():
    init_beds_and_sensors_tables()
    init_sensor_readings_table()
    init_watering_events_table()
    init_watering_decisions_table()
    init_weather_db()
    init_planner_layouts_table()
    init_garden_location_table()

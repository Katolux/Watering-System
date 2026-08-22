# GardenHub Operations

## Scope

This guide covers normal local operation, monitoring and basic recovery for the current GardenHub prototype.

GardenHub is still under active development. It can run continuously on a Raspberry Pi or similar Linux host, but it should not yet be treated as a safety-critical or unattended irrigation controller.

The current runtime consists mainly of:

- the Flask web application;
- the separate scheduler process;
- optional ESP32/Arduino soil-moisture nodes;
- a local SQLite database;
- outbound Open-Meteo requests.

Physical watering hardware is not currently controlled by GardenHub.

## Runtime processes

### Flask application

The Flask process serves:

- Workspace;
- Planner;
- Garden Control;
- Weather;
- History;
- Notifications;
- Encyclopedia;
- bed, sensor and watering pages;
- Planner JSON persistence endpoints;
- the soil-sensor receiver endpoint.

Start manually with:

```bash
source .venv/bin/activate
python3 app.py
```

### Scheduler

The scheduler runs separately:

```bash
source .venv/bin/activate
python3 scheduler.py
```

Its current jobs are:

- refreshing Weather;
- running the watering recommendation engine during its configured morning logic.

The scheduler does not operate valves or create proof of physical watering.

## Checking whether GardenHub is running

For a manual development deployment:

```bash
ps aux | grep -E "python3 (app|scheduler)\.py" | grep -v grep
```

Normally you should see one Flask process and one scheduler process.

If system services are added later, use the corresponding service-manager commands instead. The current repository should not assume that `gardenhub-web` or `gardenhub-scheduler` systemd units already exist.

## Stopping GardenHub

When stopping a manually launched environment, stop both processes.

If necessary:

```bash
pkill -f "python3 app.py"
pkill -f "python3 scheduler.py"
```

Check afterward that no stale GardenHub process is still holding port `5000`.

This is especially important during development because an old Flask process can make browser testing appear to show code that is no longer current.

## Logs and errors

When processes are launched manually, errors are normally visible in their terminals.

If output has been redirected to log files, inspect those specific files rather than assuming fixed log names.

A future managed-service installation should use the operating system's service logs.

GardenHub also stores application-level `system_events` in SQLite. These are useful for user-facing warnings and history, but they are not a replacement for process/runtime logs.

## Checking the database

The normal local database is SQLite.

Before running direct SQL commands, make sure you are inspecting the intended database rather than a demo or disposable test database.

A simple integrity check can be run with SQLite:

```bash
sqlite3 garden_system.db "PRAGMA integrity_check;"
```

Expected result:

```text
ok
```

If the output is not `ok`, stop write-producing processes before attempting recovery.

## Sensor readings

To inspect the most recent readings:

```bash
sqlite3 garden_system.db "
SELECT bed_id, sensor_id, slot, moisture_raw, moisture_pct, timestamp
FROM sensor_readings
ORDER BY timestamp DESC
LIMIT 10;"
```

If expected readings are missing, check:

- ESP32/Arduino power and Wi-Fi;
- the configured GardenHub host;
- the `/sensor_data` endpoint;
- Flask runtime output;
- whether the sender is using the expected sensor and bed identifiers.

Do not diagnose a sensor as “offline” solely because its configured `active` flag is false. GardenHub does not yet have a real connectivity/heartbeat model.

Likewise, the application does not yet calculate a reliable stale/last-seen health state.

## Watering recommendations

To inspect recent stored recommendations:

```bash
sqlite3 garden_system.db "
SELECT bed_id, final_minutes, timestamp
FROM watering_decisions
ORDER BY timestamp DESC
LIMIT 10;"
```

These rows mean that GardenHub calculated a recommendation.

They do **not** mean that watering physically occurred.

The current recommendation engine can skip a bed when required data is unavailable or incomplete. Mixed plantings are also still handled through simplified aggregate watering values.

## Watering records

Recent manual watering records can be inspected with:

```bash
sqlite3 garden_system.db "
SELECT bed_id, minutes, mode, timestamp
FROM watering_events
ORDER BY timestamp DESC
LIMIT 10;"
```

A watering event is a stored record.

It is not a controller acknowledgement and does not prove that a valve or pump ran.

The current UI action that records manual watering should therefore be interpreted as **record manual watering**, not as a hardware command.

## Weather

GardenHub stores current/daily Open-Meteo data in `weather_data`.

Recent stored rows can be inspected with:

```bash
sqlite3 garden_system.db "
SELECT date, temperature_2m_max, precipitation_sum
FROM weather_data
ORDER BY date DESC
LIMIT 10;"
```

The exact available columns may evolve as Weather is redesigned.

Important current limitation: the maximum stored forecast date is **not** a reliable indicator of when Weather was last successfully retrieved.

Because future forecast rows are stored, an old retrieval can still contain dates several days ahead.

The Weather backend is scheduled for redesign, including better freshness metadata and clearer current/hourly/daily semantics.

## Scheduler checks

The scheduler currently keeps important run guards in process memory.

That means:

- restarting it can lose its once-per-day state;
- restarting can allow duplicate recommendation runs;
- one bed's early reading can trigger the day's run before other beds report.

If scheduler behaviour looks wrong, inspect recent `watering_decisions` and runtime output rather than assuming it has exactly-once semantics.

Until the scheduler is redesigned, restarts should be treated cautiously during the morning recommendation window.

## Planner and Garden Control

Planner layouts are stored separately in `planner_layouts`.

A successful Planner save persists geometry and object metadata but does not modify beds, plantings or other operational domain records.

Garden Control reads the saved layout and joins matching `bedId` references to current operational data.

If a Garden Control bed does not show live domain information, verify that the saved Planner object's `bedId` exactly matches an existing bed record.

Missing/stale references are intentionally preserved rather than silently deleted.

## History and notifications

History is assembled from several existing sources:

- Weather rows;
- sensor readings;
- watering events;
- system events.

Notifications are also derived from `system_events`.

There is currently no separate unread/read or active/resolved notification state.

A warning appearing in Notifications should therefore be treated as a stored warning/error record, not necessarily as proof that the condition is still active.

## Demo mode

The deterministic demo database is for demonstrations and frontend validation.

Do not use demo data as:

- a backup;
- evidence of real sensor operation;
- evidence of real watering;
- a source of current garden history.

When debugging unexpected values, first confirm whether the application is using the local garden database or demo database.

## Backups

GardenHub does not yet have a complete automated backup system.

Before risky changes, create a copy of the real SQLite database while the application and scheduler are stopped.

For example:

```bash
mkdir -p backups
cp garden_system.db backups/garden_system_$(date +%F_%H%M).db
```

Keep backups outside disposable test directories.

Important times to back up include:

- before pulling schema-changing code;
- before manual database cleanup;
- before large plant-data operations;
- before testing new scheduler/automation behaviour.

A proper automated backup and restore process remains future operations work.

## Recovery

If the application behaves unexpectedly:

1. stop Flask and scheduler;
2. confirm no stale process is still running;
3. inspect logs/runtime output;
4. run `PRAGMA integrity_check`;
5. verify the database path and database mode;
6. restart Flask;
7. verify the UI;
8. restart the scheduler only after the application state looks correct.

If the database is actually damaged and a known-good backup exists, restore the backup while GardenHub is stopped.

If no backup exists, do not immediately delete or recreate the database. Preserve the file first so its data can be inspected or recovered.

## Updating a running installation

Before pulling a new version:

1. stop Flask;
2. stop the scheduler;
3. back up the current real database;
4. inspect the Git working tree;
5. pull/update the repository;
6. refresh Python dependencies if needed;
7. review schema/data changes;
8. start Flask and smoke-test the main pages;
9. start the scheduler;
10. monitor the first Weather/recommendation cycle.

GardenHub does not yet have a general migration framework, so updates that alter the schema deserve manual review.

## Common failure checks

| Symptom | First checks |
| --- | --- |
| App does not open | Confirm Flask is running and port `5000` is free/listening |
| Browser shows old behaviour | Look for a stale Flask process serving old code |
| No sensor readings | Check node power/Wi-Fi, sender host, IDs and Flask receiver output |
| Sensor shown inactive/offline | Remember configured inactive is not connectivity state |
| Weather looks stale | Check retrieval/runtime output; future forecast date alone does not prove freshness |
| No watering recommendation | Check bed active state, plant watering configuration, sensor readings and scheduler timing |
| Duplicate recommendations | Check whether the scheduler was restarted; run state is not durable yet |
| Watering event exists but nothing watered | Expected: current events are records, not hardware execution |
| Garden Control bed lacks operational data | Check the saved Planner `bedId` against the real bed ID |
| Notifications say warning | Treat as stored event history; active/resolved state is not tracked |

## Operational safety boundary

The current version is appropriate for:

- local garden development;
- Planner use;
- plant knowledge;
- Weather testing;
- sensor ingestion;
- watering recommendation experiments;
- manual watering records;
- historical review.

It should **not** currently be relied on for:

- unattended physical watering;
- exactly-once scheduler behaviour;
- proof of sensor connectivity;
- proof of water delivery;
- public internet exposure;
- multi-user hosting;
- safety-critical automation.

Before physical actuation is introduced, GardenHub needs stronger scheduler durability, sensor identity/health, safety limits, controller state and verified delivery behaviour.

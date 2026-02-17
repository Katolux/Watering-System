Got it. Below is an updated **`docs/ARCHITECTURE.md`** with:

* An **ASCII diagram** (in a fenced code block you can paste directly).
* Clear note that **minutes are an interim proxy**, and the long-term model is **water volume (L/day or mm/day)** with flow-based runtime conversion.
* A couple of wording tweaks to keep it portfolio-accurate without locking you into today’s implementation.

---

# GardenHUB Architecture

GardenHUB is a small IoT system for garden monitoring and irrigation automation. It ingests sensor readings from Arduino/ESP nodes, stores them in SQLite, combines them with weather signals, and produces daily watering recommendations. A lightweight Flask UI provides monitoring and configuration.

```text
+-------------------+          Wi-Fi / HTTP POST           +---------------------------+
|  Sensor Node(s)   |  --------------------------------->  | Raspberry Pi (GardenHUB) |
|  (Arduino/ESP32)  |                                      |                           |
|                   |                                      |  +---------------------+  |
|  - wake schedule  |                                      |  | Flask Web App       |  |
|  - read moisture  |                                      |  |  (app.py)           |  |
|  - POST payload   |                                      |  |                     |  |
+-------------------+                                      |  |  - UI routes         |  |
                                                          |  |  - Receiver endpoint |  |
                                                          |  |    (python_receiver) |  |
                                                          |  +----------+----------+  |
                                                          |             |             |
                                                          |             v             |
                                                          |      +-------------+      |
                                                          |      |  SQLite DB  |      |
                                                          |      | garden_system.db   |
                                                          |      +------+------+      |
                                                          |             |             |
                                                          |             v             |
                                                          |  +---------------------+  |
                                                          |  | Scheduler           |  |
                                                          |  | (scheduler.py)      |  |
                                                          |  |                     |  |
                                                          |  | - weather refresh   |  |
                                                          |  | - run engine (AM)   |  |
                                                          |  +----------+----------+  |
                                                          |             |             |
                                                          |             v             |
                                                          |  +---------------------+  |
                                                          |  | Watering Engine     |  |
                                                          |  | (watering_engine.py)|  |
                                                          |  |                     |  |
                                                          |  | - decisions + logs  |  |
                                                          |  +---------------------+  |
                                                          +---------------------------+

Current actuation: DRY RUN (log only)
Future actuation: Valve control (flow-based volume delivery)
```

---

## High-Level Data Flow

1. **Sensor node (Arduino/ESP)** wakes on schedule and reads soil moisture.
2. Node sends an **HTTP POST** to the Raspberry Pi (Flask receiver).
3. Flask stores readings in **SQLite** (`sensor_readings`) using a daily **slot** system (1–6).
4. Weather is refreshed periodically and stored in **SQLite** (`weather_data`).
5. A scheduler process triggers the **watering engine** once per day (morning window).
6. The watering engine produces a watering recommendation and logs:

   * `watering_decisions` (calculation + factors)
   * `watering_events` (dry-run/manual events)
7. UI displays sensor history, weather, decisions, and system events.

---

## Components

### 1) Sensor Nodes (Arduino/ESP)

**Responsibility**

* Read soil moisture sensor(s)
* Connect to Wi-Fi
* POST readings to the Pi endpoint

**Current behavior**

* Wake → read → send → sleep (scheduled runs per day)

**Payload fields (typical)**

* `sensor_id`
* `bed_id` *(current test mode; planned: assign bed in UI instead)*
* `moisture_raw`
* optional: timestamp/metadata

---

### 2) Raspberry Pi Host

Runs two Python processes:

#### A) Flask Web App (`app.py`)

**Responsibilities**

* Web UI routes (beds, plants, sensors, history, automation)
* Receiver blueprint (`python_receiver.py`) for sensor POST ingestion
* DB initialization on startup (`db_init.init_all_tables`)
* Weather refresh check (if configured)

#### B) Scheduler (`scheduler.py`)

**Responsibilities**

* Runs continuously
* Triggers:

  * weather refresh checks
  * watering engine execution in a morning window
* Designed to run autonomously without user interaction

---

## Database (SQLite)

### Core tables (summary)

#### `beds`

* `bed_id` (TEXT PK)
* `active` (INTEGER)

#### `sensors`

* `sensor_id` (TEXT PK)
* `bed_id` (TEXT, FK to beds; planned: nullable with “unassigned” state)
* `active` (INTEGER)

#### `plants`

Stores plant configuration used by the engine.

* `plant_id` (TEXT PK)
* `name`
* moisture targets *(interim: raw or % depending on calibration stage)*
* **water requirement targets (future)** *(e.g., L/day or mm/day)*
* base reference for scheduling *(interim: minutes; future: volume)*

#### `bed_plantings`

* bed ↔ plant mapping + quantity
* supports future multi-plant beds

#### `sensor_readings`

* `timestamp`, `date`
* `sensor_id`, `bed_id`
* `slot` (1–6)
* `moisture_raw`
* `UNIQUE(sensor_id, date, slot)` prevents duplicates

#### `weather_data`

* stores forecast/history signals used by the engine

#### `watering_decisions`

Decision output per bed per day.

* engine inputs snapshot (moisture summary, weather)
* decision output *(interim: minutes; future: volume target)*
* factor breakdown for explainability

#### `watering_events`

Records when watering was triggered.

* mode: manual / auto_dry *(future: auto_live)*
* references decision when applicable

#### `system_events`

Structured system logging and warnings.

---

## Slot System (Sensor Readings)

GardenHUB uses **slots (1–6)** per day to represent reading cycles. Slots are assigned sequentially based on how many readings already exist that day, rather than being anchored to exact clock times.

**Benefits**

* Robust if a reading is missed or the system starts late
* Prevents runaway inserts beyond expected daily cycles
* Simple daily aggregation for the engine

**Tradeoff**

* Slots are not guaranteed to map to a specific time-of-day unless the sensor node enforces it

---

## Watering Engine

### Inputs

* Bed configuration + plant configuration (`beds`, `plants`, `bed_plantings`)
* Sensor readings (daily slots, averages, morning reading preference)
* Weather signals (e.g., temperature and precipitation)

### Output

**Interim (current)**

* Produces **watering runtime in minutes** as a proxy for delivery.

**Planned (flow-based)**

* Produces a **target water volume** (e.g., **L/day** or **mm/day per bed**).
* Runtime becomes a derived value:

  * `runtime_minutes = target_liters / (measured_flow_l_per_min)`

### Execution

* Triggered by scheduler once per day (morning window)
* Can also be triggered manually via UI endpoints (admin/testing)

---

## Web UI (Flask + Templates)

Primary UI areas:

* **Automation dashboard**: bed statuses, slots, summaries, events
* **Beds management**: create beds, assign plants, view current state
* **Plants management**: create/edit plant configuration *(delete/edit planned)*
* **Sensors management**: create/assign sensors *(unassigned discovery planned)*
* **History**: weather history and (future) sensor/decision history

---

## Current Design Decisions

* **SQLite** for simplicity and portability
* **Separate scheduler process** to keep Flask request handling lightweight
* **Explainable decisions** (factor breakdown logged) to support later ML work
* **Dry-run mode** before controlling physical valves

---

## Planned Architectural Evolution

* Sensor nodes will send `sensor_id` only; bed assignment will be managed in UI/DB
* Add per-sensor calibration (raw → %)
* Replace nohup with systemd services for always-on deployment
* Add health monitoring (last_seen, heartbeat, alerts)
* Transition from **minutes-based output** to **flow-based volume targets** (L/day or mm/day)
* Expand to valve control and irrigation zone management

---
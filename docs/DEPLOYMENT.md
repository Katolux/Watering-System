# GardenHub Deployment

## Scope

GardenHub is currently intended for local deployment and testing, typically on a Raspberry Pi or another small Linux machine on the same network as the garden hardware.

The application is not designed for public internet exposure in its current form. It has no user authentication, no CSRF protection, and the sensor receiver trusts the local network.

GardenHub currently runs two Python processes:

- the Flask web application;
- the recommendation/Weather scheduler.

Physical irrigation control is not part of the current deployment.

## Requirements

A typical Raspberry Pi deployment needs:

- Raspberry Pi 3B+ or newer;
- Raspberry Pi OS or another Debian-based Linux distribution;
- Python 3.10+;
- internet access for Open-Meteo;
- local network access for the browser UI;
- optional ESP32/Arduino sensor nodes for soil-moisture readings.

Sensor hardware is optional. The Planner, Encyclopedia, Weather and other non-hardware parts of GardenHub can still be used without it.

## Clone and install

Clone the repository and enter the project directory:

```bash
git clone https://github.com/Katolux/Watering-System.git
cd Watering-System
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Database setup

GardenHub uses SQLite.

The Flask application initializes the required schema during startup, so a separate database-initialization command is normally unnecessary.

The current schema includes the main garden, plant, sensor, Weather, watering, system-event and Planner layout tables.

The development database is still evolving, so database files should not be treated as portable schema migrations between arbitrary project versions.

Plant knowledge is seeded separately from the JSON source files when needed. Follow the current seeding script in the repository rather than relying on older `db_init.py` instructions.

## Running GardenHub manually

Activate the environment:

```bash
source .venv/bin/activate
```

Start the Flask application:

```bash
python3 app.py
```

In a second terminal, start the scheduler:

```bash
source .venv/bin/activate
python3 scheduler.py
```

The web interface is normally available on port `5000`:

```text
http://<host-ip>:5000
```

The scheduler is a separate long-running process. It refreshes Weather and runs watering recommendations; it does not control irrigation hardware.

## ESP32 / Arduino sensor nodes

The current sensor receiver accepts HTTP POST requests at:

```text
POST /sensor_data
```

The primary firmware posts a sensor ID, bed ID and raw moisture value to the GardenHub host.

Wi-Fi credentials and other private hardware configuration must remain outside version control. Use the example secrets/configuration file in the repository as a template for local setup.

The current firmware still contains some prototype assumptions around server, bed and sensor identity. Before deploying a new node, verify the actual firmware configuration rather than relying on old documentation examples.

## Local network use

GardenHub currently binds to the local network so it can be opened from other devices on the same LAN.

A stable IP address or DHCP reservation for the host is useful, especially when ESP32/Arduino nodes post directly to it.

This is a trusted-network deployment model.

Do not expose the current Flask service directly to the public internet.

## Running in the background

For short development/testing sessions, the web application and scheduler can be started manually in separate terminals.

For a more permanent Raspberry Pi installation, they should eventually run as managed services rather than through `nohup` or an open shell.

A future operational setup should provide separate service definitions for:

- GardenHub web;
- GardenHub scheduler.

Managed services should handle:

- startup on boot;
- restart after failure;
- predictable working directory and virtual environment;
- logs through the system service manager.

The repository does not currently contain a complete supported `systemd` deployment package, so service files should not be described as already implemented.

## Updating an installation

Before updating:

1. stop the running Flask application;
2. stop the scheduler;
3. back up any database that contains real garden data;
4. review the incoming project changes.

Then update the repository:

```bash
git pull
```

Activate the environment and refresh dependencies when necessary:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Restart the application and scheduler afterward.

Because GardenHub does not yet have a general migration framework, schema-changing updates should be reviewed carefully before using an existing long-lived database.

## Backups

Automatic backup handling is planned but is not currently a complete application feature.

For a real installation, the SQLite database should be copied regularly while development continues.

At minimum, keep a known-good backup before:

- pulling a version with schema changes;
- running data migrations or cleanup scripts;
- making major plant-data changes;
- testing new automation behaviour.

A future operational setup should include automatic local backups and a documented restore procedure.

## Weather dependency

GardenHub uses Open-Meteo for current and daily forecast data.

The host therefore needs outbound internet access for Weather refreshes.

If Weather retrieval fails, the rest of the local application can still run, although some Weather-dependent watering calculations will use their existing fallback behaviour.

Weather location/freshness handling is currently being redesigned, so deployment configuration should not yet assume a finished per-garden Weather setup.

## Demo mode

GardenHub also supports a deterministic demo database/context used for demonstrations and frontend testing.

Demo data is separate from the normal local garden database and should not be confused with a production backup or real garden history.

Live Weather refresh is intentionally limited in demo behaviour where appropriate.

## Security

The current application is suitable for a trusted home/local network, not for public hosting.

Current limitations include:

- no login/authentication;
- no authorization model;
- no CSRF protection;
- unauthenticated sensor HTTP ingestion;
- no HTTPS termination inside the Flask application.

If GardenHub is ever exposed beyond a trusted LAN, it will need a deliberate security/deployment phase rather than simply opening port `5000`.

That phase would include authentication, HTTPS/reverse proxying, firewall rules, secrets management and stronger device identity.

## Current deployment boundary

A current GardenHub deployment can provide:

- the web interface;
- Planner persistence;
- Garden Control;
- Encyclopedia and plant data;
- Open-Meteo Weather retrieval;
- ESP32/Arduino soil-moisture ingestion;
- watering recommendation calculation;
- manual watering records;
- History and system events;
- the recommendation scheduler.

It does **not** currently provide:

- physical valve/relay control;
- verified water delivery;
- flow feedback;
- persisted irrigation schedules;
- controller health/state;
- multi-garden server hosting;
- public-user authentication.

These boundaries should remain explicit until the corresponding backend and hardware work exists.

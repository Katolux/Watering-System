# GardenHUB – Operations Guide (v1)

This document describes how to operate, monitor, maintain, and recover the GardenHUB system once deployed.

---

# 1. Runtime Overview

GardenHUB consists of two main processes:

1. **Flask Web Application**

   * Serves UI
   * Receives sensor data via HTTP
   * Displays history and system state

2. **Scheduler**

   * Runs weather refresh checks
   * Executes watering engine
   * Logs system events

Both processes must be running for full functionality.

---

# 2. Checking System Status

## Check Running Processes

```bash
ps aux | grep -E "python3 (app|scheduler)\.py" | grep -v grep
```

Expected:

* `python3 app.py`
* `python3 scheduler.py`

---

## If Using systemd (Recommended)

```bash
systemctl status gardenhub-web
systemctl status gardenhub-scheduler
```

---

# 3. Viewing Logs

## If running with nohup

```bash
tail -f flask.log
tail -f scheduler.log
```

## If running with systemd

```bash
journalctl -u gardenhub-web -f
journalctl -u gardenhub-scheduler -f
```

---

# 4. Verifying Sensor Data Flow

To confirm sensor ingestion:

```bash
sqlite3 garden_system.db "SELECT COUNT(*) FROM sensor_readings;"
```

To view latest readings:

```bash
sqlite3 garden_system.db "
SELECT bed_id, sensor_id, slot, moisture_raw, timestamp
FROM sensor_readings
ORDER BY timestamp DESC
LIMIT 10;"
```

If count remains zero:

* Check Arduino WiFi connection
* Verify POST endpoint
* Check Flask log for errors

---

# 5. Verifying Watering Engine Execution

Check last decisions:

```bash
sqlite3 garden_system.db "
SELECT bed_id, final_minutes, timestamp
FROM watering_decisions
ORDER BY timestamp DESC
LIMIT 5;"
```

Check watering events:

```bash
sqlite3 garden_system.db "
SELECT bed_id, minutes, mode, timestamp
FROM watering_events
ORDER BY timestamp DESC
LIMIT 5;"
```

---

# 6. Weather Monitoring

Check latest weather refresh:

```bash
sqlite3 garden_system.db "
SELECT date FROM weather_data
ORDER BY date DESC
LIMIT 5;"
```

If weather does not update:

* Confirm scheduler running
* Confirm location configuration
* Check network connectivity

---

# 7. Database Backup

## Manual Backup

```bash
cp garden_system.db backups/garden_system_$(date +%F).db
```

## Recommended: Weekly Cron Backup

Example cron entry:

```bash
0 3 * * 0 cp ~/Watering-System/garden_system.db ~/Watering-System/backups/garden_system_$(date +\%F).db
```

This creates a backup every Sunday at 03:00.

---

# 8. Safe Restart Procedure

If system behaves unexpectedly:

```bash
pkill -f "python3 app.py"
pkill -f "python3 scheduler.py"

source .venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
nohup python3 scheduler.py > scheduler.log 2>&1 &
```

If using systemd:

```bash
sudo systemctl restart gardenhub-web
sudo systemctl restart gardenhub-scheduler
```

---

# 9. Sensor Health Monitoring (Operational Policy)

A sensor may be considered **stale** if:

* No reading received in X hours (configurable)
* Fewer than expected daily readings

Operational recommendation:

* System should log WARNING
* Watering engine must not crash
* System should fall back to safe watering logic

---

# 10. Engine Safety Policy (v1)

The watering engine must:

* Run once per day
* Log all decisions
* Log all watering events
* Continue operation even if:

  * Weather unavailable
  * Some sensors missing
  * One bed fails

System must never:

* Crash due to missing sensor
* Skip watering entirely due to single failure

---

# 11. Disaster Recovery

If database is corrupted:

1. Stop services
2. Restore latest backup
3. Restart services

If no backup exists:

* Reinitialize DB
* Reconfigure beds, sensors, plants

Sensor data history will be lost.

---

# 12. Common Failure Scenarios
´´´
| Issue                            | Likely Cause          | Action                   |
| -------------------------------- | --------------------- | ------------------------ |
| No sensor readings               | Arduino not posting   | Check WiFi, secrets file |
| Weather not updating             | Scheduler not running | Restart scheduler        |
| UI loads but no data             | DB path mismatch      | Verify DB location       |
| App not accessible               | Flask not running     | Restart service          |
| Decisions logged but no watering | DRY_RUN enabled       | Expected behavior        |
´´´
---

# 13. Performance Notes

* SQLite is sufficient for single-user local deployment
* Suitable for:

  * Home garden
  * Greenhouse
  * Small-scale automation
* For multi-user / cloud:

  * Migrate to PostgreSQL
  * Use production WSGI server (gunicorn)

---

# 14. Operational Scope (v1)

Stable for:

* Continuous unattended operation (local network)
* Multi-day sensor ingestion
* Automated watering decisions
* Logging and historical review

Not yet included:

* Remote access hardening
* Multi-user authentication
* Production-grade web server
* Automatic cloud backups


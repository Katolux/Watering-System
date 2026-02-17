# GardenHUB – Deployment Guide (v1)

This document describes how to deploy GardenHUB on a Raspberry Pi for local operation and testing.

---

# 1. System Requirements

* Raspberry Pi (3B+ or newer recommended)
* Raspberry Pi OS (Debian-based)
* Python 3.10+
* Internet connection
* Arduino device configured to send sensor data via HTTP POST
* Local network access (for UI)

---

# 2. Clone the Repository

On the Raspberry Pi:

```bash
cd ~
git clone https://github.com/Katolux/Watering-System.git
cd Watering-System
```

---

# 3. Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

# 4. Initialize the Database

```bash
python3 -c "from db_init import init_all_tables; init_all_tables(); print('Database initialized')"
```

This will create all required tables:

* beds
* sensors
* plants
* bed_plantings
* sensor_readings
* weather_data
* watering_decisions
* watering_events
* system_events

---

# 5. Configure Arduino Credentials (Required)

Create a local file named:

```
arduino_secrets.h
```

This file must NOT be committed to version control.

Example:

```cpp
#define WIFI_SSID     "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"
#define FLASK_HOST    "192.168.x.x"
#define FLASK_PORT    5000
```

Ensure the Arduino posts sensor readings to:

```
http://<raspberry-pi-ip>:5000/<receiver-endpoint>
```

---

# 6. Running the Application (Manual Mode)

Start Flask:

```bash
source .venv/bin/activate
python3 app.py
```

Start Scheduler (separate terminal):

```bash
source .venv/bin/activate
python3 scheduler.py
```

Access the UI from any device on the same network:

```
http://<raspberry-pi-ip>:5000
```

---

# 7. Running in Background (Testing Mode)

For unattended testing:

```bash
source .venv/bin/activate
nohup python3 app.py > flask.log 2>&1 &
nohup python3 scheduler.py > scheduler.log 2>&1 &
```

Check running processes:

```bash
ps aux | grep python3
```

Check logs:

```bash
tail -f flask.log
tail -f scheduler.log
```

---

# 8. Updating the Application

To update to the latest version:

```bash
cd ~/Watering-System
git pull
```

Restart Flask and Scheduler afterward.

---

# 9. Recommended Production Setup

For long-term stability, replace `nohup` with `systemd` services:

* gardenhub-web.service
* gardenhub-scheduler.service

This ensures:

* Automatic startup on boot
* Automatic restart on crash
* Centralized logging via `journalctl`

---

# 10. Network Access

The application runs on:

```
http://0.0.0.0:5000
```

Access via:

```
http://<raspberry-pi-ip>:5000
```

Ensure the Raspberry Pi:

* Has a static IP (recommended)
* Is reachable within the local network

---

# 11. Security Notice

This version is intended for local network use.

For public exposure:

* Use a reverse proxy (nginx)
* Enable HTTPS
* Implement authentication
* Configure firewall rules

---

# Deployment Status (v1 Scope)

Current deployment supports:

* Sensor ingestion via HTTP POST
* Weather refresh scheduling
* Daily watering decision engine
* UI management for beds, plants, sensors
* Logging of decisions and events

Hardware valve actuation is currently DRY_RUN mode (logging only).
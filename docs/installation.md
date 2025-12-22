# Installation Guide

This document explains how to set up the automated irrigation system
using a Raspberry Pi as system coordinator and an Arduino Nano ESP32
as the hardware controller.

---

## 1️⃣ Hardware Setup

### 1.1 Arduino (Hardware Controller)

1. Mount the Arduino Nano ESP32 inside a protected enclosure.
2. Wire capacitive soil moisture sensors to the designated analog pins.
3. Connect relay or MOSFET module to digital output pins.
4. Connect 12 V solenoid valves to the relay/MOSFET outputs.
5. Provide common ground between Arduino and relay module.
6. Power Arduino via USB or regulated 5 V supply.

Responsibilities:
- Read soil moisture sensors
- Open/close solenoid valves
- Execute commands received from the Raspberry Pi

---

### 1.2 Raspberry Pi (System Coordinator)

1. Install Raspberry Pi OS (Lite recommended).
2. Ensure network connectivity (Ethernet or Wi-Fi).
3. Connect Raspberry Pi to Arduino via USB or serial interface.
4. (Optional) Mount Raspberry Pi in the same enclosure with proper ventilation.

Responsibilities:
- Run irrigation logic
- Store data in SQLite database
- Download daily weather data
- Send commands to Arduino

---

### 1.3 Water System

- Drip irrigation only (assumed throughout the project)
- 12 V solenoid valves
- Main line with reducers to micro-tubing
- External 12 V power supply sized for valves

---

## 2️⃣ Software Setup

### 2.1 Raspberry Pi

Update system:
- sudo apt update && sudo apt upgrade

Install required packages:
- sudo apt install python3 python3-pip sqlite3

Install Python dependencies:
- pip3 install requests

Clone the repository:
- git clone <repository_url>
- cd watering-system

Initialize database:
- Ensure garden_system.db exists
- Create required tables if not already present

Configure:
- Soil types and coefficients
- Plant types and coefficients
- Base watering time per zone

### 2.2 Arduino

Install Arduino IDE
Select board: Arduino Nano ESP32
Upload firmware from /arduino/ or /firmware/ directory

Verify:
Sensor readings are transmitted
Valve commands are executed correctly

---

## 3 Weather Data Setup

Configure Open-Meteo parameters in the Python script
Enable daily data download:
Temperature (daily max)
Rain probability
Precipitation
Wind speed
Confirm weather data is stored locally before logic execution

---

## 4 Testing

Verify soil moisture readings in the database
Run irrigation logic in dry-run mode (no valve activation)
Validate calculated watering duration
Enable valve actuation

Observe:
- Correct valve timing
- Safe shutdown behavior
- No over-watering

---

## 5 Deployment

- Install sensors at representative root depth
- Secure all electronics in IP67 enclosure
- Provide strain relief for cables
- Route tubing cleanly per zone
- Monitor system behavior during first days
- Adjust coefficients during calibration phase

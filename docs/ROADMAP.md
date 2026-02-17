# 🌱 GardenHUB Roadmap
---
Project status:
Version 1 (Proof of Concept) is deployed and running on Raspberry Pi.
Arduino → WiFi → Flask → DB pipeline is working.
Sensor readings are stored.
Scheduler and engine execute.
UI is accessible remotely.

This roadmap defines structured next steps from stable v1 → calibrated v1.1 → expanded v2.

## ✅ Version 1 – Running & Testing (Current Phase)
**Core Working Features**

- Arduino sends moisture readings over HTTP

- Readings stored in SQLite

- Slot system (1–6 daily cycles)

- Weather fetched & stored

- Watering engine calculates decisions (dry run)

- Decisions logged

- Scheduler runs automatically

- UI shows:

    - Sensor readings

    - Weather history

    - Bed status

    - Watering decisions

    - System events

### Current Testing Goals (2-week burn-in)

- Confirm sensor readings arrive consistently

- Confirm scheduler runs once/day

- Confirm weather refresh logic

- Monitor for crashes

- Observe decision engine behavior under real rain

- Identify calibration mismatches

## 🔧 Version 1.1 – Stabilization & Calibration
### 1️⃣ Sensor Calibration System
**Goals**

- Convert raw sensor values → meaningful %

- Allow broad early calibration (loose bands)

- Later refine with accurate dry/wet reference

**Tasks**

- Store per-sensor:

    - raw_dry

    - raw_wet

- Compute percentage:
```
pct = (raw - raw_dry) / (raw_wet - raw_dry) * 100
```

- Store both raw + pct

- UI shows both

- Engine uses % thresholds (not raw)

### 2️⃣ Engine Calibration & Rain Logic
**Problem**

Rain occurred but watering still triggered.

**Improvements**

- Add rain override rule:

    - If forecast rain ≥ X mm → cap watering

    - If yesterday rain ≥ Y mm → skip watering

- Log override reason clearly in system_events

- Add global max minutes per bed/day

- Add global max total watering minutes/day

- Add DRY_RUN safety gate (True by default)

### 3️⃣ Sensor Management Improvements
**Goals**

Make system usable without code changes.

**Features**

- Auto-create sensor entry when unknown sensor_id posts

- Mark as:

    - Unassigned

    - Active

- UI table showing:

    - sensor_id

    - assigned bed

    - active toggle

    - last_seen timestamp

    - status badge (OK / stale / offline)

- Allow:

    - Assign to bed

    - Unassign from bed

    - Rename sensor

- Stale detection:

    - If not seen in X hours → WARNING

### 4️⃣ Beds & Plants Improvements
**Needed Fixes**

- Multiple plants per bed supported properly

- Remove plant assignment option

- Change plant quantity

-  Delete plant (or soft delete)

- Delete bed (safe delete)

- Display multiple plantings per bed correctly

### 5️⃣ Reliability Improvements (Critical)
**Replace nohup with systemd**

Two services:

    - gardenhub-web

    - gardenhub-scheduler

Requirements:

    - Auto start on boot

    - Auto restart on crash

    - Logs via journalctl

    - No terminal babysitting required

### 6️⃣ Automatic Backups
**Goals**

Avoid losing months of data.

**Phase 1**

- Daily SQLite backup with timestamp

- Stored locally in /backups/

**Phase 2 (optional)**

- Sync to laptop via:

    rsync

    scp

    SMB share

- Future: cloud backup

## 🌍 Version 2 – Climate & Portability
### 7️⃣ Location Configuration in UI
**Goals**

Remove hardcoded weather location.

**Features**

- UI header section:

    - If no location → prompt to set

    - If set → display place name

- Store:

    - latitude

    - longitude

- Weather refresh uses stored lat/lon

**Future Upgrade**

- Map-based selector

- Reverse geocoding

- Hardiness zone display (7a, etc.)

- Frost date estimation

## 🌿 Plant JSON Library System
**Goals**

Create reusable structured plant knowledge base.

**JSON Schema (Initial Fields)**

    - plant_id

    - name

    - min_moisture (%)

    - max_moisture (%)

    - base_minutes

    - rooting_depth

    - growth_stage_notes

    - typical_mm_per_week

    - notes

**Tasks**

- Define JSON standard

- Create tomato full spec

- Add:

    - Onion

    - Garlic

    - Lettuce

    - Broccoli

    - Potato

    - etc

- Create safe importer:

    - Insert or ignore

    - No duplicates

    - GUI editing remains functional

## 🚿 Version 2 – Irrigation Planner Module

### 8️⃣ Water Flow Calculator
**Feature: 10L Test**

- User inputs:

    - Time to fill 10L bucket

- System calculates:

    - L/min flow rate

### 9️⃣ Zone Designer

User inputs:

    - Tube lengths

    - Tube diameter

    - Dripline spacing

    - Emitter L/h rating

    - Number of emitters

System calculates:

    - Total zone flow requirement

    - Recommended runtime

    - Whether multiple zones can run simultaneously

### 🔟 Pressure Loss & Friction Model

Implement formula:

    - Hazen-Williams (recommended)
    or

    - Darcy-Weisbach

Warn user if:

    - Excessive pressure drop

    - 1/4” tube too long

    - End emitters likely underperform

### 1️⃣1️⃣ Bed Water Volume Calculation

Given:

    - Bed dimensions (e.g., 177×88×30 cm)

    - Dripline layout

Calculate:

    - Liters required to deliver X mm water depth

    - Required runtime based on flow rate

## 🎨 Version 2 – UI Enhancements

- Clean dashboard layout

- Graphs:

    - Sensor trends

    - Weather

    - Watering history

- CSV export

- Excel export

- Garden layout visual planner

- Zone types:

    - Bed

    - Pot

    - Greenhouse

## 🔐 Version 2 – System Monitoring Dashboard

Add health page:

    - Last scheduler heartbeat

    - Last engine run

    - Last weather refresh

    - Last sensor reading per sensor

    - System warnings summary

## 🚨 Critical Safety Reminders

Before enabling valves:

- DRY_RUN must default to True

- Hard cap minutes per bed/day

- Hard cap total minutes/day

- Panic stop toggle in UI

- Fail-safe watering mode when sensors are stale/missing

    - degrade to conservative base watering

    - log warnings

    - enforce hard caps


## 🧠 Long-Term Vision

GardenHUB becomes:

- Modular irrigation controller

- Multi-zone system

- Portable (any location worldwide)

- Climate-aware

- Data-backed

- Possibly subscription-based plant knowledge layer

## 🧪 Current Priority Order

1. Stabilize v1 for 2 weeks

2. Add systemd services

3. Add backups

4. Fix plant form regression

5. Implement calibration layer

6. Tune rain override logic

7. Improve sensor onboarding

Everything else follows after stability.
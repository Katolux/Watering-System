# 🌱 GardenHUB Roadmap

---

## 📌 Current Status

* Raspberry Pi deployment running
* Arduino → WiFi → Flask → SQLite pipeline working
* Sensor readings stored and processed
* Scheduler + watering engine running
* UI accessible remotely
* ~1 month real-world test completed (sensor reliability + scheduler validation)

System is stable enough for iteration, but not yet production-safe.

---

## 🧱 Version 1.2 – Plant System & Backend Cleanup (Current Work)

**Branch:** `v1.2-plants-seeding-cleanup`

### Purpose

Transition from simple plant model → structured JSON-based system
while stabilizing backend before further expansion.

### What changed

* JSON plant definitions (50+ plants)
* Seeder system (bulk import)
* Variety system with overrides
* Rich plant metadata:

  * soil
  * calendar
  * nutrition
  * care
  * companions
* Full JSON stored in DB
* New plant CRUD UI

### Temporary compromise

Watering still uses simplified values derived from JSON:

* `min_moisture`
* `max_moisture`
* `base_minutes`

### Current focus

* Fix schema ↔ repository mismatches
* Fix route/template inconsistencies
* Prevent runtime crashes (watering engine, DB issues)
* Remove silent DB failures (`INSERT OR IGNORE`)
* Clean duplicate imports and legacy code
* Improve project structure (pre-refactor stage)

### Status

⚠️ Transitional phase (mixed old + new logic)
🎯 Goal: stable enough to merge into `main`

---

## 🔧 Version 1.1 – Calibration & Reliability (Next Step)

### 1️⃣ Sensor Calibration System

**Goals**

* Convert raw sensor values → meaningful %
* Allow early loose calibration
* Later refine with accurate dry/wet reference

**Tasks**

* Store per-sensor:

  * raw_dry
  * raw_wet

* Compute:

```
pct = (raw - raw_dry) / (raw_wet - raw_dry) * 100
```

* Store both raw + pct
* UI shows both
* Engine uses % instead of raw

---

### 2️⃣ Engine Calibration & Rain Logic

**Problem**

Rain occurred but watering still triggered.

**Improvements**

* Rain override rules:

  * Forecast rain ≥ X mm → cap watering
  * Yesterday rain ≥ Y mm → skip watering

* Log override reasons (system_events)

* Add safety caps:

  * Max minutes per bed/day
  * Max total watering per day

* Add `DRY_RUN = True` safety mode

---

### 3️⃣ Sensor Management Improvements

**Goals**

Make system usable without code changes.

**Features**

* Auto-create sensor if unknown sensor_id posts

* Mark sensors:

  * unassigned
  * active

* UI table:

  * sensor_id
  * assigned bed
  * active toggle
  * last_seen timestamp
  * status (OK / stale / offline)

* Actions:

  * assign to bed
  * unassign
  * rename sensor

* Stale detection:

  * no data for X hours → WARNING

---

### 4️⃣ Beds & Plants Improvements

* Support multiple plantings per bed (correctly)
* Remove plant assignment
* Change plant quantity
* Soft delete plantings
* Safe delete bed
* Display multiple plantings clearly

---

### 5️⃣ Reliability Improvements (Critical)

Replace `nohup` with `systemd`

Services:

* gardenhub-web
* gardenhub-scheduler

Requirements:

* Auto start on boot
* Auto restart on crash
* Logs via `journalctl`
* No manual terminal dependency

---

### 6️⃣ Automatic Backups

**Phase 1**

* Daily SQLite backup
* Stored locally in `/backups/`

**Phase 2 (optional)**

* Sync via:

  * rsync
  * scp
  * SMB

* Future: cloud backup

---

## 🔮 Version 1.3 – Watering Model Redesign

### Problem

Current watering logic assumes:

* one plant per bed
* fixed thresholds

This does not reflect real garden conditions.

---

### Planned improvements

* Multiple plantings per bed handled correctly
* "Main crop" vs companion plants
* Mixed crop logic (combine watering needs)
* Sensor depth awareness:

  * shallow (10 cm)
  * deep (30 cm)
* Soil type influence on moisture behavior
* Growth-stage-based watering (from JSON)

---

### Goal

Move from:

👉 simple rule engine
→ **context-aware irrigation system**

---

## 🌿 Plant JSON System (Current Design)

Current JSON structure includes:

* names (multi-language)
* category & family
* UI metadata
* spacing
* root depth & type
* soil preferences
* water need profile
* irrigation sensitivity
* calendar (months + weeks)
* nutrition
* care / pruning
* companions
* varieties with overrides

---

### Current behavior

Seeder converts JSON → simplified watering values:

* `min_moisture`
* `max_moisture`
* `base_minutes`

Full JSON is stored for future logic (v1.3+)

---

## 🌍 Version 2 – Climate & Portability

### 7️⃣ Location Configuration in UI

**Goals**

Remove hardcoded weather location.

**Features**

* UI location setup
* Store:

  * latitude
  * longitude
* Weather uses stored coordinates

**Future**

* Map selector
* Reverse geocoding
* Hardiness zones
* Frost estimation

---

## 🚿 Version 2 – Irrigation Planner Module

### 8️⃣ Water Flow Calculator

* User inputs: time to fill 10L bucket
* System outputs: L/min flow

---

### 9️⃣ Zone Designer

Inputs:

* tube length
* diameter
* emitter spacing
* emitter flow (L/h)

Outputs:

* total flow requirement
* runtime
* zone compatibility

---

### 🔟 Pressure Loss Model

* Hazen-Williams (preferred)
* or Darcy-Weisbach

Warnings:

* excessive pressure loss
* long 1/4” runs
* uneven emitter output

---

### 1️⃣1️⃣ Bed Water Volume

Given:

* bed dimensions

Calculate:

* liters required
* runtime needed

---

## 🎨 Version 2 – UI Enhancements

* Clean dashboard
* Graphs:

  * sensor trends
  * weather
  * watering history
* CSV export
* Excel export
* Garden layout planner
* Zone types:

  * bed
  * pot
  * greenhouse

---

## 🔐 Version 2 – System Monitoring

* Scheduler heartbeat
* Last engine run
* Last weather update
* Sensor health
* System warnings

---

## 🚨 Safety Rules (Critical)

Before enabling valves:

* DRY_RUN = True by default
* Hard cap minutes per bed/day
* Hard cap total minutes/day
* Panic stop toggle in UI
* Fail-safe mode if sensors fail:

  * fallback watering
  * log warnings
  * enforce caps

---

## 🧠 Long-Term Vision

GardenHUB becomes:

* Modular irrigation controller
* Multi-zone system
* Climate-aware
* Data-driven
* Portable globally
* Potential SaaS / knowledge layer

---

## 🧪 Current Priority Order

1. Stabilize v1.2 branch
2. Merge v1.2 into `main`
3. Add systemd services
4. Add backups
5. Improve sensor onboarding
6. Implement calibration layer
7. Redesign watering model (v1.3)

---

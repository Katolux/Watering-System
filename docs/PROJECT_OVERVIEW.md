# GardenHUB Project Overview

## Purpose

GardenHUB is an evolving gardening platform for hobby gardeners. It began as a personal Raspberry Pi and Arduino irrigation project, but the long-term product vision is broader: one connected system for planning a garden, understanding plants, designing irrigation, using local weather, collecting sensor data, and producing explainable watering recommendations.

GardenHUB should eventually help a user answer questions such as:

- What is planted in each bed?
- What can be planted now in this location and season?
- How much water does each bed need?
- How long should an irrigation zone run?
- How do tubing length, diameter, emitters, flow, and pressure affect runtime?
- Did a moisture increase come from rain, manual watering, or the automatic system?
- How did plants, watering, and weather perform over time?

The project should remain useful without hardware. Hardware and automation are optional extensions, not requirements for using the planner, encyclopedia, weather, and recommendation features.

---

## Current Product Scope

The current application is a Flask and SQLite prototype with:

- Raspberry Pi deployment
- Arduino/ESP32 sensor ingestion
- soil-moisture calibration
- SQLite data storage
- weather integration through Open-Meteo
- a standalone scheduler
- explainable watering decisions
- manual and dry-run watering events
- bed and sensor management
- a JSON-based plant encyclopedia
- plant varieties and companion relationships
- a responsive Jinja/CSS web interface

Current physical actuation remains disabled. Watering output is still a dry-run/logging workflow.

---

## Long-Term Product Vision

GardenHUB may evolve into a commercial gardening platform containing:

### Garden planning

- mobile-first visual garden map
- beds, pots, greenhouse, paths, trees, compost, water tanks, and other objects
- real dimensions and scale
- plant placement using spacing rules
- seasonal planting plans
- crop rotation and companion planting support

### Irrigation planning

- irrigation zones
- tubing paths and measured lengths
- tubing diameter
- emitter spacing and flow
- bucket-test input
- flow and pressure-aware runtime calculations
- water-volume targets per bed
- optional hardware control

### Plant knowledge

- professional plant encyclopedia
- varieties
- sowing, transplanting, and harvest calendars
- soil, nutrition, care, pruning, support, roots, and watering information
- companion planting
- regional frost-date and seasonal recommendations

### Monitoring and recommendations

- weather-aware watering
- sensor history
- stale/offline sensor detection
- automatic detection of rain or manual watering from moisture jumps
- explainable recommendations
- future AI-assisted observations based on the user’s own garden history

### Product capabilities

- user accounts
- configurable garden location
- multiple gardens
- light and dark appearance
- multiple languages
- phone, tablet, and desktop support
- optional subscriptions and premium planning/analysis features

These are future directions, not instructions to implement during the current structural refactor.

---

## Current Development Priority

The current branch is focused on structural organization only.

The immediate objective is to reorganize the existing working Python code into a clear, professional, maintainable package structure while preserving all current behavior.

This is not a rewrite.

This is not a functional redesign.

This is not frontend work.

This is not the moment to add new product features.

---

## Development Principles

- Reliability over complexity
- Simple, explicit Python over clever abstractions
- Preserve working behavior during structural changes
- Prefer moving existing code over rewriting it
- Separate structural, functional, and visual work
- Test after every small phase
- Keep commits narrow and reversible
- Real-world testing before live valve control
- Explainable decisions rather than opaque automation
- Hardware-independent product value

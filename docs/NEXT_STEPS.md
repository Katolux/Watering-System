# GardenHUB Next Steps

## Purpose

This document defines the next development priorities after the v1.2 stabilization, backend cleanup, Blueprint refactor, and basic UI improvement phase.

The next goal is to validate the improved system on the Raspberry Pi, improve reliability, and prepare the project for smarter irrigation logic and a more polished user experience.

---

## 1. Final Review Before Deploy

Before deploying again to the Raspberry Pi:

- Run full manual smoke test
- Check all routes after Blueprint refactor
- Confirm database initializes correctly
- Confirm weather refresh works
- Confirm sensor ingestion endpoint still works
- Confirm watering engine dry-run works
- Confirm no obvious template or navigation errors
- Confirm plant, sensor, bed, and watering pages load correctly
- Confirm no hardcoded old routes remain in templates

---

## 2. Raspberry Pi Deployment Test

After review:

- Pull latest branch/main on Raspberry Pi
- Start Flask app
- Start scheduler
- Confirm UI loads from phone/laptop
- Confirm sensor readings are received
- Confirm weather data is stored
- Confirm watering decisions are generated
- Monitor logs for errors
- Run a new real-world test cycle

---

## 3. Reliability Workstream

Priority before real valve control:

- Replace `nohup` with `systemd`
- Add automatic SQLite backups
- Add safe restart/shutdown procedure
- Add scheduler heartbeat
- Add sensor stale/offline detection
- Add clearer system warnings
- Add DRY_RUN safety caps
- Add max watering per bed/day
- Add max total watering per day

---

## 4. Bed and Sensor Management Improvements

Current missing management actions:

- Add delete bed option
- Add safe delete / deactivate bed behavior
- Add delete sensor option
- Add unassign sensor option
- Add rename sensor option
- Improve handling of unassigned sensors
- Improve UI feedback when adding/assigning beds or sensors
- Prevent accidental destructive actions with confirmation pages

---

## 5. Dashboard and UI Improvements

Improve the app toward a cleaner, more user-friendly product:

- Improve homepage dashboard
- Improve weather card
- Show latest system events
- Show bed status summary
- Show latest watering decisions
- Make mobile layout clearer
- Improve plant encyclopedia layout
- Use card-based views where useful
- Improve tables and forms
- Add clearer status colors
- Add dark/light mode
- Add language support later:
  - English
  - German
  - possibly Spanish
- Make the UI feel closer to a small commercial app

---

## 6. Plant Encyclopedia Improvements

Improve the plant system as both a user tool and future irrigation knowledge base:

- Make plant detail pages easier to read
- Improve plant cards/listing layout
- Add better visual grouping:
  - watering
  - soil
  - calendar
  - nutrition
  - care
  - companions
  - varieties
- Add more plants over time
- Improve existing plant JSON quality
- Add useful external/reference links where appropriate
- Add season-based suggestions
- Add last-frost-date-based suggestions
- Add current-month planting suggestions
- Add crop timing guidance based on region and season

---

## 7. Automatic Watering Event Detection

Future logic should detect watering or rain events from sensor behavior.

Possible logic:

- Detect sudden moisture increase
- Compare moisture jump against weather data
- If rain was recorded/forecast, classify as likely rain
- If no rain occurred, classify as likely manual watering
- Log detected event in `system_events`
- Later add detected watering event to `watering_events`
- Use this to improve future watering decisions

Goal:

- System understands not only planned watering, but also real-world water events.

---

## 8. v1.3 Watering Model Improvements

The current model still uses simplified watering values:

- `min_moisture`
- `max_moisture`
- `base_minutes`

Future v1.3 logic should use more of the JSON/DB plant data.

Planned improvements:

- Support multiple plants per bed properly
- Add main crop vs companion crop concept
- Ignore companion plants for watering when appropriate
- Use mixed-crop watering rules
- Use sensor depth and position
- Use soil profile to adjust watering
- Use root depth more intelligently
- Use growth-stage watering from plant JSON
- Improve rain override logic
- Improve temperature response
- Add clearer watering decision explanations

---

## 9. Arduino / Sensor Node Code Improvements

The Arduino code should become easier to maintain and update.

Current issue:

- Editing code is cumbersome
- Device may require blank upload/reset workflow before updates

Planned improvements:

- Clean Arduino code structure
- Move configuration into clear constants
- Make sensor IDs easier to change
- Make WiFi/server configuration easier to manage
- Improve sleep/wake logic clarity
- Improve debug output
- Document upload/update procedure
- Consider safer OTA-style update workflow later if realistic

---

## 10. Future Garden Planner

Longer-term feature.

Goal:

- Build a visual garden planner connected to the irrigation system.

Possible features:

- Visual bed layout using JavaScript + SVG/canvas
- Place plants visually inside beds
- Store bed dimensions
- Store plant positions
- Calculate tube lengths
- Estimate flow/pressure requirements
- Estimate required water volume per bed
- Connect visual plan to irrigation logic

This is not part of immediate v1.3 unless hardware and testing time are available.

---

## 11. Hardware / Irrigation Expansion

Future hardware work depends on budget and testing capacity.

Potential future tasks:

- Add real valve control
- Test solenoid valves
- Test pressure/flow behavior
- Add flow meter
- Add multiple zones
- Improve tubing layout
- Validate emitter performance
- Add pressure/flow calculations from real data

Hardware features should only be coded deeply once they can be tested physically.

---

## 12. Suggested Priority Order

1. Final audit and smoke test
2. Deploy latest version to Raspberry Pi
3. Run new real-world test cycle
4. Add systemd services
5. Add automatic backups
6. Add delete/unassign management for beds and sensors
7. Improve dashboard and plant encyclopedia UI
8. Add sensor stale/offline detection
9. Improve watering event detection
10. Start v1.3 watering model redesign
11. Improve Arduino code maintainability
12. Plan future garden planner and hardware expansion

---

## Immediate Next Action

Run a final audit of the current v1.2 branch before Raspberry Pi deployment and deploy/run new set of tests indoors/outdoors.
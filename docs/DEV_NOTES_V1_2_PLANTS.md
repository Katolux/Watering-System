# V1.2 Plant System Changes

## Summary
This update moves the plant system from a minimal plant list into a richer plant encyclopedia and manual management flow aligned with the JSON/DB schema.

## Completed changes

### 1. Moisture system migrated to %
- Sensor readings now store both raw and moisture_pct.
- Watering logic now uses moisture percentage instead of raw values.
- Plant moisture targets are now treated as percentage targets.
- Bed status and average moisture use % logic.

### 2. Plant JSON seeding
- Implemented plant seeder for importing plant family JSON files.
- Seeder supports:
  - base plant import
  - companions import
  - varieties import
  - resolved_json storage for varieties
- Seeder uses 2-pass logic so companion foreign keys work correctly.
- Watering defaults are derived from:
  - water_need_overall
  - root depth

### 3. Plant encyclopedia
- Added plant catalog page using seeded DB data.
- Added plant detail page showing:
  - identity
  - watering data
  - spacing and roots
  - soil JSON
  - calendar JSON
  - nutrition JSON
  - care JSON
  - varieties
  - companions

### 4. Add plant form upgraded
- Replaced basic admin-style form with richer plant entry form.
- New form includes:
  - identity
  - UI fields
  - spacing
  - root depth/type
  - water need
  - irrigation sensitivity
  - mulch
  - soil info
  - nutrition info
  - sowing/transplant/harvest months
  - days to maturity
  - care/support/pruning
- min_moisture, max_moisture, and base_minutes are auto-derived.

### 5. Add variety form upgraded
- Replaced minimal variety form with override-oriented variety form.
- New variety form supports overrides for:
  - sowing months
  - transplant months
  - harvest months
  - days to maturity
  - spacing
  - support
  - pruning

## Current architecture state
- Runtime app structure remains mostly unchanged to reduce risk during active testing.
- New seeding logic lives in the seeding package/module.
- DB is now rich enough to support:
  - encyclopedia views
  - future interpreter layer
  - variety-aware watering logic
  - bed assignment improvements

## Remaining follow-up items
- Improve plant encyclopedia UI styling.
- Update bed assignment flow to support plant + variety selection directly from bed pages.
- Manual edit/delete for plants and varieties added; further validation and UI polish still needed.
- Implement plant interpreter layer to derive irrigation behavior from DB/JSON traits instead of relying only on seeded defaults.
- Later refactor project structure into clearer modules (routes/services/repositories) once testing is stable.
Project Roadmap

This roadmap outlines the planned development stages for the Automated Watering System.
It follows a simple progression: get basic readings working → add logic → add weather → improve intelligence.

Phase 1 – Core System (IN PROGRESS)

Soil moisture sensor reading

DHT22 temperature and humidity

Manual pump activation using relay

Basic Arduino structure: main + sensors

First debugging output over Serial

Status: In progress

Phase 2 – Basic Irrigation Logic

Moisture thresholds for watering

Simple IF/ELSE decision-making

Cooldown timers between cycles

Safety cutoff for low tank level

First working irrigation cycle

Status: Planned

Phase 3 – Weather Integration (Python + Arduino)

Python (Raspberry Pi):

Retrieve hourly and daily forecast using Open-Meteo

Use temperature, humidity, rain probability, precipitation, cloud cover, sunshine duration, wind speed

Process data using the get_weather.py script

Save simplified JSON output for Arduino/ESP to read

Arduino / ESP:

Load simplified forecast data

Use weather to adjust watering logic

Status: Planned

Phase 4 – Smart Watering Logic (Advanced)

Full intelligent watering including:

Environmental Factors:

Temperature effect (hot → more water, cold → less)

Wind effect (windy → more evaporation → more water)

Sunshine duration

Rain probability + rainfall trend

Soil Factors:

Clay: slow absorption, high retention

Sandy: fast absorption, low retention

Loam: balanced behavior

Plant Factors:

High-demand (tomato, cucumber)

Medium-demand (herbs, flowers)

Low-demand (rosemary, lavender)

Combined watering calculation:
base_time × temperature_factor × wind_factor × soil_factor × plant_factor

Status: Future

Phase 5 – Data Logging & Dashboard

Store moisture, weather, and watering events

Display live sensor data

Manual watering button via web interface

Adjust thresholds from dashboard

Status: Future

Phase 6 – Final Deployment & Stabilisation

Waterproof housing for electronics

Cable routing and tubing optimization

Multi-zone irrigation possibility

Field calibration and adjustment

Status: Later

Phase 7 – Optional Add-Ons

Fertilizer injector

Greenhouse integration

Light intensity sensor

Soil nutrient monitoring

Adaptive learning model (very future)

Roadmap Philosophy

Start simple → get it working → grow it into a smart, adaptive system.

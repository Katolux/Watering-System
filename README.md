# Watering System – Automated Irrigation for a 70 m² Garden

An open-source, hardware-first automated irrigation system for my ~70 m² home garden in Switzerland.  
This project is part of my personal learning journey as I transition into the tech field, and also serves as a showcase of my logic, coding style, and problem-solving approach.

---

## 🌱 Project Overview

This system monitors soil moisture and environmental conditions to control irrigation cycles.
Weather-based optimisation and prediction are planned future steps.
The goal is to reduce water waste, maintain consistent soil health, and eventually build a fully autonomous irrigation controller.

The project is intentionally simple and modular so anyone can replicate or adapt it for their own garden.

---

##🔧 Hardware

System architecture:
- Raspberry Pi (system coordinator and data hub)
- Arduino Nano ESP32 (real-time hardware controller)

Raspberry Pi responsibilities:
- Runs core irrigation logic
- Stores all data in SQLite (garden_system.db)
- Manages soil and plant coefficients
- Ingests daily weather data
- Future web dashboard and ML logic

Arduino responsibilities:
- Reads soil moisture sensors
- Controls solenoid valves
- Executes commands received from the Raspberry Pi
- Provides a safe, deterministic hardware layer

Sensors:
- Capacitive soil moisture sensors (multi-zone)

Actuation:
- 12 V solenoid valves (drip irrigation)
- Relay or MOSFET module

Water system:
- Drip irrigation (assumed throughout the project)

Other components:
- External 12 V power supply
- Waterproof IP67 enclosure
- Internal jumper wiring


---

## 🧠 Software Features

🧠 Software Features

- Soil moisture readings from hardware sensors
- Weather-based modifiers (rain, wind, temperature)
- Fixed base watering time per irrigation zone
- Water demand calculation based on:
  - Soil moisture
  - Soil type coefficients
  - Plant type coefficients
- All coefficients stored and versioned in the database
- Single SQLite database for all system data

Planned extensions:
- Seasonal calibration using historical data
- Predictive watering models (ML)
- Remote monitoring dashboard

Note: Weather data acquisition is implemented; integration into irrigation decisions is actively under development.


##🧪 Technologies Used

Embedded:
- Arduino C++ (Nano ESP32)

System & backend:
- Raspberry Pi (Linux)
- Python
- SQLite (single database: garden_system.db)

Data & logic:
- Coefficient-based water demand models
- Modular logic layers (sensor → calculation → actuation)

External data:
- Open-Meteo API (daily aggregates only – planned)


---

## 👨‍💻 About Me

I’m Alfonso (“Katolux”). 
My background includes:
- Gastronomy and professional cooking (+10 years).  
- Licensed boat captain/skipper with global experience as delivery and charter skipper. 
- Technical roles at Banco Santander España (handling ISO 20022 XML remittance files)  
- Apple Genius & technical support  

I am now transitioning into a tech career and building this project as part of my portfolio and skill development.  
I use AI tools to assist with debugging and redundancy validation while remaining fully engaged with the architecture and logic.

---

## 🤝 Contributions

This is an open project.  
If you find it useful or want to adapt it for your garden, feel free to fork it, open issues, or send PRs.  
Suggestions and improvements are welcome — everything helps me learn.

---

## 📜 License

MIT License — free to use and modify.

---

Thank you for stopping by!  
— **Katolux**

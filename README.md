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

Controller:
- Arduino Nano ESP32 (primary controller)

Sensors:
- Capacitive soil moisture sensors (analog, multi-zone)
- Optional environmental sensor (temperature) – future expansion

Actuation:
- 12 V solenoid valves (drip irrigation)
- Relay or MOSFET module for valve control

Water system:
- Drip irrigation (assumed throughout the project)
- 1/2" main line with reducers to micro-tubing (4/7 mm) or drip tubing.

Other components:
- External 12 V power supply
- Waterproof IP67 enclosure
- Internal jumper wiring (Dupont / JST as appropriate)

---

## 🧠 Software Features

🧠 Software Features

- Reads soil moisture from hardware sensors
- Fixed base watering time per zone
- Conditional watering logic based on soil thresholds
- Daily weather data ingestion (future step)
- Data logging to a single SQLite database
- Modular design for additional sensors and zones

Future features (planned):
- Weather-based modifiers (rain, wind, heat)
- Predictive watering models (ML)
- Remote monitoring dashboard
- Error detection and redundancy checks  

---

## 🧪 Technologies Used

- **Arduino C++**  
- **Open-Meteo API** (HTTP GET requests via WiFi module, future step)  
- **JSON parsing** for forecast data  
- **Basic state machine logic** for irrigation scheduling  
- Planned future integration with:
  - Raspberry Pi for data logging
  - Web dashboard for remote monitoring

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

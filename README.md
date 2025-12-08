# Watering System – Automated Irrigation for a 70 m² Garden

An open-source watering system designed for my 70 m² home garden in Switzerland.  
This project is part of my personal learning journey as I transition into the tech field, and also serves as a showcase of my logic, coding style, and problem-solving approach.

---

## 🌱 Project Overview

This system monitors soil moisture, temperature, and weather forecasts to automatically optimise watering cycles.  
The goal is to reduce water waste, maintain consistent soil health, and eventually build a fully autonomous irrigation controller.

The project is intentionally simple and modular so anyone can replicate or adapt it for their own garden.

---

## 🔧 Hardware

**Microcontroller:** Arduino Uno R3  
**Sensors:**
- Capacitive Soil Moisture Sensor v2.0  
- DHT22 (Temperature & Humidity)  
- Water Level Sensor (Basic Float or Ultrasonic HC-SR04 — depending on final choice)  
- Relay Module for pump/valve control  

**Other components:**  
- 12 V water pump or solenoid valve  
- 4/7 mm irrigation tubing (via Temu)  
- Power supply and wiring  
- Optional: protective enclosure for outdoor installation  

---

## 🧠 Software Features

- Reads real-time soil moisture and temperature  
- Fetches weather data (rain probability, temperature forecast) from **Open-Meteo API**  
- Smart watering logic:
  - Skip irrigation if rain is forecast
  - Delay watering if soil moisture is already above threshold
  - Protect plants during heat spikes or cold nights
- Error detection and redundancy checks  
- Modular structure for additional sensors or expansions

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

I’m Alfonso (“Katolux”), 36 years old.  
My background includes:
- Gastronomy and professional cooking (15 years)  
- Licensed boat captain/sjipper with global experience as delivery and charter skipper 
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

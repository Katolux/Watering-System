# Sensor List

This project uses several sensors to collect environmental data for automated irrigation control.  
Below is the list of sensors included in the current version of the system.

---

## 🌱 Soil Moisture Sensor – Capacitive v2.0
- **Type:** Analog capacitive moisture sensor  
- **Purpose:** Detect soil moisture level to determine watering frequency  
- **Advantages:**  
  - More reliable than resistive sensors  
  - Less prone to corrosion  
- **Output:** 0–1023 analog value (Arduino ADC)

---

## 🌡️ Temperature & Humidity Sensor – DHT22
- **Type:** Digital temperature & humidity  
- **Purpose:**  
  - Adjust watering logic based on heat  
  - Protect plants during cold nights  
- **Output:**  
  - Temperature in °C  
  - Humidity in %

---

## 💧 Water Level Sensor (Tank)
Depending on final selection, the system may use:
- **Float sensor** (simple ON/OFF water level detection)  
or  
- **HC-SR04 ultrasonic sensor** (measure tank height)

**Purpose:** Avoid running the pump dry.

---

## ⚡ Relay Module (Pump / Valve Control)
- **Type:** 1–4 channel relay module  
- **Purpose:** Switch water pump or solenoid valve based on irrigation logic  
- **Input:** 5V digital  
- **Output:** 12V or 220V depending on configuration

---

## 📌 Additional Planned Sensors (Future)
- Light intensity sensor (LDR or BH1750)  
- Air pressure sensor (BMP280)  

The system is modular, and more sensors may be added as the project evolves.


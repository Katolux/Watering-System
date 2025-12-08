# Installation Guide

This document explains how to set up the watering system.

---

## 1️⃣ Hardware Setup

1. Connect Arduino Uno to breadboard.  
2. Wire capacitive moisture sensors to analog pins.  
3. Wire DHT22 to digital pin with pull-up resistor.  
4. Connect relay module to digital output pins.  
5. Connect pump or solenoid valve through relay.  
6. Connect power supplies (5V for Arduino, 12V for pump).  
7. Optional: Add ESP8266/ESP32 for API support.

---

## 2️⃣ Software Setup

1. Install Arduino IDE.  
2. Install required libraries:
   - `DHT sensor library`
   - `ArduinoJSON` (for API parsing — future)
   - `HTTPClient` (future with ESP module)

3. Upload code from `/src/` folder.  
4. Modify thresholds in `watering_logic.ino` as needed.

---

## 3️⃣ Testing

1. Open Serial Monitor.  
2. Check moisture readings.  
3. Check DHT22 output.  
4. Trigger manual watering test.  
5. Confirm pump activation and shutoff logic.

---

## 4️⃣ Deployment

- Place sensors in soil at representative locations.  
- Protect electronics inside a waterproof enclosure.  
- Route tubing to all plant zones.  
- Adjust settings as needed after field testing.


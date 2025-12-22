# Hardware Components

The watering system is built from affordable, easy-to-find components.  
This file lists the main parts used in the project and their function.

---

## 🧠 Controllers

### **Raspberry Pi**
- System coordinator and logic controller  
- Runs irrigation logic and coefficient calculations  
- Stores data in SQLite database  
- Downloads daily weather data from Open-Meteo  
- Sends commands to the Arduino  

### **Arduino Nano ESP32**
- Hardware controller  
- Reads soil moisture sensors  
- Controls solenoid valves via relay or MOSFET  
- Executes commands received from the Raspberry Pi  


---

## 🪠 Watering Components
- **12V solenoid valves** (drip irrigation)  
- **1/2" main water line with reducers**  
- **4/7 mm irrigation tubing**  
- **Connectors, T-joints, drippers**  
- **12V power supply**  


---

## 📡 Connectivity
- USB or serial connection between Raspberry Pi and Arduino  
- Network connectivity on Raspberry Pi (Ethernet or Wi-Fi)  
- Weather data retrieved by Raspberry Pi (no separate ESP module required)  


---

## 🔌 Power Management
- 5V power supply for Raspberry Pi  
- 5V supply for Arduino (USB or regulated)  
- 12V supply for solenoid valves  
- Common ground shared between control and actuation circuits  


---

## 🛠️ Tools Used
- Breadboard (early prototyping only)  
- Soldering iron (permanent installation)  
- Wire strippers, electrical tape, heat shrink  
- Multimeter (voltage and continuity checks)  
- Wire strippers, electrical tape, heat shrink  

---

More detailed wiring diagrams and enclosure layouts can be found in the documentation folder.


More detailed diagrams and wiring instructions can be found in the documentation folder.


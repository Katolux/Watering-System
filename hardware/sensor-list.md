Sensor List

This document describes the sensors used by the automated irrigation system.
Only sensors that are currently used or architecturally supported are listed here.

🌱 Soil Moisture Sensors (Capacitive)

Type: Analog capacitive soil moisture sensors

Purpose:

Measure soil moisture in the root zone

Provide feedback for irrigation duration calculation

Characteristics:

Resistant to corrosion (no exposed electrodes)

Suitable for long-term soil installation

Usage:

Multiple sensors can be installed across irrigation zones

Readings are averaged over a short time window

Output:

Analog value (ADC), interpreted and calibrated in software

Soil moisture sensors influence watering duration, not whether irrigation is allowed.

💧 Optional Water Tank Level Sensor

Type: Simple float switch (digital)

Purpose:

Detect low water level in supply tank

Prevent irrigation when insufficient water is available

Behavior:

When a low level is detected:

Irrigation is blocked

Valves remain closed

Event is logged

No ultrasonic distance sensors are used.

⚡ Actuation Interface (Not a Sensor)

While not a sensor, the actuation interface is part of the physical I/O layer:

Type: Relay module or MOSFET driver

Purpose:

Switch 12 V solenoid valves

Control:

Digital output from Arduino

This interface executes commands calculated by the Raspberry Pi.

#include <Wire.h>
#include "Adafruit_seesaw.h"
#include "Adafruit_AM2320.h"

// --- Soil Sensor ---
Adafruit_seesaw soilSensor;

// --- Air Sensor (Temperature + Humidity) ---
Adafruit_AM2320 airSensor = Adafruit_AM2320();

// Timing
unsigned long lastRead = 0;
const unsigned long interval = 1000;  // read every 1 sec

void setup() {
  Serial.begin(9600);

  // Initialize soil sensor
  if (!soilSensor.begin(0x36)) {
    Serial.println("{\"error\":\"soil_not_found\"}");
    while (1);
  }

  // Initialize air sensor
  if (!airSensor.begin()) {
    Serial.println("{\"error\":\"air_not_found\"}");
    while (1);
  }

  Serial.println("{\"status\":\"sensors_ready\"}");
}

void loop() {

  unsigned long now = millis();
  if (now - lastRead >= interval) {
    lastRead = now;

    // Read soil
    uint16_t moisture = soilSensor.touchRead(0);
    float soilTemp = soilSensor.getTemp();

    // Read air
    float airTemp = airSensor.readTemperature();
    float humidity = airSensor.readHumidity();

    if (isnan(airTemp) || isnan(humidity)) {
      Serial.println("{\"error\":\"am2320_read_fail\"}");
      return;
    }

    // Output JSON
    Serial.print("{\"moisture\":");
    Serial.print(moisture);
    Serial.print(",\"soil_temp\":");
    Serial.print(soilTemp, 1);
    Serial.print(",\"air_temp\":");
    Serial.print(airTemp, 1);
    Serial.print(",\"humidity\":");
    Serial.print(humidity, 1);
    Serial.println("}");
  }
}


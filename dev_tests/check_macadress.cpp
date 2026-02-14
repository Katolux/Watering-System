#include <WiFi.h>
#include "arduino_secrets.h"

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("ESP32 MAC address:");
  Serial.println(WiFi.macAddress());
}

void loop() {
  
}

// This code initializes the serial communication, retrieves the ESP32's MAC address using the WiFi library,
// and prints it to the serial monitor. The loop function is empty since we only need to get the MAC address once during setup.
// To save the MAC adress with your connection and avoid issues with Andruino Nano changes of IP.
// We used this to save the an IP to the Andruino.

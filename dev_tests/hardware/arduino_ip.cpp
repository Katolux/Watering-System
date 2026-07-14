#include <WiFi.h>
#include "arduino_secrets.h"


//to check IP on Andruino Nano, as it can change with hard resets or similar

const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;


void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("Booting...");
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");

  // IMPORTANT: wait until IP is actually assigned
  while (WiFi.localIP().toString() == "0.0.0.0") {
    delay(100);
  }

  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // nothing
}
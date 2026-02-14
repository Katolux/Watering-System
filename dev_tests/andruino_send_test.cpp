#include <WiFi.h>
#include <HTTPClient.h>
#include "arduino_secrets.h"

//simple test to make sure the andruino is sending info and we can catch it with the flask server

// -------- WIFI ----------
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;


// -------- SERVER (your laptop) ----------
const char* serverURL = "your sever URL here, e.g. http://";

// -------- SENSOR ----------
const int SENSOR_PIN = A0;

// -------- SAMPLING ----------
const unsigned long SAMPLE_TIME_MS = 5000;
const unsigned long SAMPLE_INTERVAL_MS = 100;

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // ---- 5s averaging ----
  unsigned long start = millis();
  long sum = 0;
  int count = 0;

  while (millis() - start < SAMPLE_TIME_MS) {
    int v = analogRead(SENSOR_PIN);
    sum += v;
    count++;
    delay(SAMPLE_INTERVAL_MS);
  }

  int average = sum / count;

  Serial.print("Average moisture: ");
  Serial.println(average);

  // ---- send to computer ----
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    String payload = "{";
    payload += "\"node\":\"bed_1\",";
    payload += "\"sensor\":\"soil_1\",";
    payload += "\"moisture\":" + String(average);
    payload += "}";

    int code = http.POST(payload);
    Serial.print("HTTP response: ");
    Serial.println(code);

    http.end();
  }

  delay(60000); // 1 minute between sends
}

#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>
#include "esp_sleep.h"
#include "arduino_secrets.h"


// ---------------- WIFI ----------------
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;


// ---------------- SERVER ----------------

const char* serverURL = "http://192.168.1.99:5000/sensor_data";

// ---------------- IDS ----------------
const char* BED_ID    = "bed_1";
const char* SENSOR_ID = "soil_1";

// ---------------- SENSOR ----------------
const int SENSOR_PIN = A0;   

// ---------------- TIME (NTP) ----------------
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec      = 3600; // CET
const int   daylightOffset_sec = 3600; // DST 

// ---------------- SCHEDULE ----------------
struct RunTime { int hour; int minute; bool done; };

RunTime runs[] = {
  {6,  30, false},
  {9,  0, false},
  {13, 0, false},
  {16, 0, false},
  {18, 0, false},
  {20, 0, false}
};
const int RUNS_COUNT = sizeof(runs) / sizeof(runs[0]);

// ---------------- SAMPLING ----------------

const int SAMPLES = 80;
const int SAMPLE_DELAY_MS = 10;

// ---------------- POWER ----------------
const bool USE_DEEP_SLEEP = true;

// ---------------- HELPERS ----------------
static bool ensureTime(tm &timeinfo);
static void resetDailyFlags();
static int  secondsUntilNextRun(const tm &timeinfo);
static void sleepForSeconds(int seconds);
static int  readSoilAverage();
static bool postReading(int moisture);

void setup() {
  Serial.begin(115200);
  delay(800);

  
  analogReadResolution(12); // 0..4095 on ESP32 family

WiFi.begin(ssid, password);
Serial.print("Connecting WiFi");

unsigned long start = millis();
while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {  // 15s timeout
  delay(400);
  Serial.print(".");
}

if (WiFi.status() != WL_CONNECTED) {
  Serial.println("\n[WIFI] Failed to connect. Sleeping 300s.");
  sleepForSeconds(300);
}

  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  delay(800);
}

void loop() {
  tm timeinfo;
  if (!ensureTime(timeinfo)) {
    Serial.println("[TIME] Failed. Retry in 5s.");
    delay(5000);
    return;
  }

  const int h = timeinfo.tm_hour;
  const int m = timeinfo.tm_min;

  // Reset flags around midnight (once)
  if (h == 0 && m == 0) {
    resetDailyFlags();
    delay(65000);
    return;
  }

  // Scheduled run
  for (int i = 0; i < RUNS_COUNT; i++) {
    RunTime &r = runs[i];
    if (!r.done && h == r.hour && m == r.minute) {
      Serial.printf("[RUN] %02d:%02d\n", r.hour, r.minute);

      int avg = readSoilAverage();
      Serial.printf("[SENSOR] avg=%d\n", avg);

      bool ok = postReading(avg);
      Serial.printf("[HTTP] %s\n", ok ? "OK" : "FAIL");

      r.done = true;

      int secs = secondsUntilNextRun(timeinfo);
      if (secs < 10) secs = 60;
      Serial.printf("[SLEEP] %d seconds\n", secs);
      sleepForSeconds(secs);
      return;
    }
  }

  // Idle: sleep until next run
  int secs = secondsUntilNextRun(timeinfo);
  if (secs < 10) secs = 60;
  Serial.printf("[IDLE] next in %d seconds\n", secs);
  sleepForSeconds(secs);
}

// ---------------- IMPLEMENTATION ----------------

static bool ensureTime(tm &timeinfo) {
  // Try a few times to get NTP time
  for (int i = 0; i < 5; i++) {
    if (getLocalTime(&timeinfo)) return true;
    delay(300);
  }
  return false;
}

static void resetDailyFlags() {
  for (int i = 0; i < RUNS_COUNT; i++) runs[i].done = false;
  Serial.println("[SCHEDULE] Reset daily flags");
}

static int secondsUntilNextRun(const tm &timeinfo) {
  const int nowMinutes = timeinfo.tm_hour * 60 + timeinfo.tm_min;

  int bestDeltaMin = 24 * 60; // minutes
  bool found = false;

  for (int i = 0; i < RUNS_COUNT; i++) {
    const int runMin = runs[i].hour * 60 + runs[i].minute;

    if (!runs[i].done && runMin >= nowMinutes) {
      int delta = runMin - nowMinutes;
      if (delta < bestDeltaMin) {
        bestDeltaMin = delta;
        found = true;
      }
    }
  }

  if (!found) {
    // no runs left today -> tomorrow first run
    resetDailyFlags();
    const int firstRunMin = runs[0].hour * 60 + runs[0].minute;
    const int toMidnight  = (24 * 60) - nowMinutes;
    bestDeltaMin = toMidnight + firstRunMin;
  }

  // wake slightly after the minute flips
  return bestDeltaMin * 60 + 5;
}

static void sleepForSeconds(int seconds) {
  if (seconds <= 0) seconds = 60;

  if (!USE_DEEP_SLEEP) {
    delay((unsigned long)seconds * 1000UL);
    return;
  }

  esp_sleep_enable_timer_wakeup((uint64_t)seconds * 1000000ULL);
  Serial.flush();
  esp_deep_sleep_start();
}

static int readSoilAverage() {
  long sum = 0;
  int minv = 1000000;
  int maxv = -1;

  // Small robustness: drop min/max to reduce spikes
  for (int i = 0; i < SAMPLES; i++) {
    int v = analogRead(SENSOR_PIN);
    sum += v;
    if (v < minv) minv = v;
    if (v > maxv) maxv = v;
    delay(SAMPLE_DELAY_MS);
  }

  sum -= minv;
  sum -= maxv;
  return (int)(sum / (SAMPLES - 2));
}

static bool postReading(int moisture) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Not connected");
    return false;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"bed\":\"" + String(BED_ID) + "\",";
  payload += "\"sensor\":\"" + String(SENSOR_ID) + "\",";
  payload += "\"moisture\":" + String(moisture);
  payload += "}";

  int code = http.POST(payload);
  String resp = http.getString();
  http.end();

  Serial.printf("[HTTP] code=%d\n", code);
  if (resp.length()) {
    Serial.print("[HTTP] body=");
    Serial.println(resp);
  }

  return (code >= 200 && code < 300);
}


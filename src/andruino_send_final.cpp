#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>

// -------- WIFI ----------
const char* ssid = "your wifi";
const char* password = "your password";

// -------- PYTHON SERVER ----------
const char* serverURL = "your Ip for the server";

// -------- SENSOR ----------
const int SENSOR_PIN = A0;

// -------- TIME ----------
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 3600;
const int daylightOffset_sec = 3600;

// -------- SCHEDULE ----------
struct RunTime {
  int hour;
  int minute;
  bool done;
};

RunTime runs[] = {
  {6, 30, false},
  {13, 0, false},
  {18, 0, false}
};

// -------- SAMPLING ----------
const unsigned long SAMPLE_TIME_MS = 5000;
const unsigned long SAMPLE_INTERVAL_MS = 100;

// -------- FUNCTION DECLARATIONS ----------
int readSoilAverage();
bool sendToServer(int moisture);
void goToSleepUntilNextRun(int seconds);

void setup() {
  Serial.begin(115200);
  delay(2000);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
}

void loop() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    delay(1000);
    return;
  }

  int currentHour = timeinfo.tm_hour;
  int currentMinute = timeinfo.tm_min;

  // Reset daily flags at midnight
  if (currentHour == 0 && currentMinute == 0) {
    for (auto &r : runs) r.done = false;
    delay(60000);
    return;
  }

  for (auto &r : runs) {
    if (!r.done &&
        currentHour == r.hour &&
        currentMinute == r.minute) {

      i

#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>
// Connect to wifi, stablish connection with our python server and send the average of the reading from the sensor
// to Python, so pythons stores them in the DB. To upload to Andruino nano

// -------- WIFI ----------
const char* ssid = "your wifi";
const char* password = "your password";

// -------- PYTHON SERVER ----------
const char* serverURL = "http://192.168.1.31:5000/soil";

// -------- SENSOR ----------
const int SENSOR_PIN = A0;

// -------- TIME ----------
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 3600;      // UTC+1
const int daylightOffset_sec = 3600;  // DST

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
void sendToServer(int moisture);
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

      int moisture = readSoilAverage();
      sendToServer(moisture);

      r.done = true;

      // For now: sleep 6 hours after sending
      goToSleepUntilNextRun(6 * 60 * 60);
    }
  }

  delay(30000);
}

// -------- FUNCTIONS ----------

int readSoilAverage() {
  unsigned long start = millis();
  long sum = 0;
  int count = 0;

  while (millis() - start < SAMPLE_TIME_MS) {
    sum += analogRead(SENSOR_PIN);
    count++;
    delay(SAMPLE_INTERVAL_MS);
  }

  int avg = sum / count;
  Serial.print("Soil moisture avg: ");
  Serial.println(avg);
  return avg;
}

void sendToServer(int moisture) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"bed\":\"bed_1\",";
  payload += "\"sensor\":\"soil_1\",";
  payload += "\"moisture\":" + String(moisture);
  payload += "}";

  int code = http.POST(payload);

  Serial.print("HTTP code: ");
  Serial.println(code);

  http.end();
}

void goToSleepUntilNextRun(int seconds) {
  Serial.print("Sleeping for ");
  Serial.print(seconds);
  Serial.println(" seconds");

  esp_sleep_enable_timer_wakeup((uint64_t)seconds * 1000000ULL);
  esp_deep_sleep_start();

}

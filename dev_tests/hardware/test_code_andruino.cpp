// DFROBOT SEN0308
// Board: Arduino Nano ESP32
// Safe for 3.3V ADC

const int SENSOR_PIN = A0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("SEN0308 test – Nano ESP32");
}

void loop() {
  int rawValue = analogRead(SENSOR_PIN);

  Serial.print("Raw ADC value: ");
  Serial.println(rawValue);

  delay(1000);
}

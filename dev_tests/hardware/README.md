# Hardware Diagnostics

This folder contains manual Arduino/ESP32 and receiver diagnostics. They are
development aids, not the primary GardenHub firmware or application runtime.

- `arduino_test` and `test_code_andruino.cpp` read soil-sensor values.
- `check_macadress.cpp` prints the ESP32 MAC address.
- `arduino_ip.cpp` prints the ESP32 IP address after Wi-Fi connection.
- `arduino_send_test.cpp` posts a simple test payload to a Flask receiver.
- `python_receiver_test.py` is the paired standalone Flask `/ping` receiver for
  the HTTP-post experiment.

Before compiling a diagnostic that includes `arduino_secrets.h`, use the
repository-root `arduino_secrets.example.h` to provide an ignored local header
in the include context expected by the Arduino toolchain. Do not commit real
credentials.

The primary firmware remains at repository root as `arduino_send_final.cpp`.

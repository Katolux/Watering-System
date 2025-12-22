import serial
import json
import sqlite3
from datetime import datetime

# ----------------------------
# CONFIGURATION
# ----------------------------
SERIAL_PORT = "COM3"  # Change to correct  Arduino port
BAUD_RATE = 9600
DB_NAME = "garden_system.db"


# ----------------------------
# DATABASE SETUP
# ----------------------------
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (
            timestamp TEXT,
            moisture REAL,
            soil_temp REAL,
            air_temp REAL,
            humidity REAL
        )
        """
    )

    conn.commit()
    conn.close()


# ----------------------------
# SAVE SENSOR DATA
# ----------------------------
def save_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO sensor_data VALUES (?, ?, ?, ?, ?)",
        (
            datetime.utcnow().isoformat(),
            data.get("moisture"),
            data.get("soil_temp"),
            data.get("air_temp"),
            data.get("humidity"),
        ),
    )

    conn.commit()
    conn.close()


# ----------------------------
# READ FROM ARDUINO (with 5-second averaging)
# ----------------------------
def read_from_arduino(run_seconds=5, store=True):
    print(f"Connecting to Arduino on {SERIAL_PORT}...")

    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        print("ERROR: Cannot open serial port:", e)
        return

    print(f"Connected! Reading sensor data for {run_seconds} seconds...")

    readings = []
    start_time = datetime.utcnow()

    while (datetime.utcnow() - start_time).total_seconds() < run_seconds:
        try:
            line = arduino.readline().decode().strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                readings.append(data)
            except json.JSONDecodeError:
                continue

        except Exception as e:
            print("ERROR:", e)
            break

    if not readings:
        print("No valid readings received.")
        return

    # Compute averaged values
    avg = {
        "moisture": sum(r["moisture"] for r in readings) / len(readings),
        "soil_temp": sum(r["soil_temp"] for r in readings) / len(readings),
        "air_temp": sum(r["air_temp"] for r in readings) / len(readings),
        "humidity": sum(r["humidity"] for r in readings) / len(readings),
    }

    print("Averaged Reading:", avg)

    if store:
        save_to_db(avg)
        print("Saved to database!")

    return avg


# ----------------------------
# CONTINUOUS READ MODE (manual mode)
# ----------------------------
def read_continuous():
    print(f"Connecting to Arduino on {SERIAL_PORT}...")

    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        print("ERROR: Cannot open serial port:", e)
        return

    print("Connected! Reading sensor data... Press CTRL+C to stop.\n")

    while True:
        try:
            line = arduino.readline().decode().strip()
            if not line:
                continue

            print("RAW:", line)

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print("Invalid JSON, skipping...")
                continue

            print(
                f"Moisture: {data['moisture']} | "
                f"Soil Temp: {data['soil_temp']}°C | "
                f"Air Temp: {data['air_temp']}°C | "
                f"Humidity: {data['humidity']}%"
            )

            save_to_db(data)

        except KeyboardInterrupt:
            print("\nStopping continuous mode.")
            break
        except Exception as e:
            print("ERROR:", e)


# ----------------------------
# MAIN EXECUTION
# ----------------------------
if __name__ == "__main__":
    init_database()

    print("1 = 5-second average\n2 = continuous reading")
    mode = input("Choose mode: ")

    if mode == "1":
        read_from_arduino()
    elif mode == "2":
        read_continuous()
    else:
        print("Invalid mode.")

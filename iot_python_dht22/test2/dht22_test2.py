#!/usr/bin/env python3
"""DHT22 reader on Raspberry Pi 4 (legacy Adafruit-DHT).

Same control flow and output as the piddlerintheroot example:
    https://piddlerintheroot.com/dht22/

Uses Adafruit-DHT so it runs on Raspbian Stretch / Python 3.5.
Activate the project venv first:
    source /home/pi/iot_python_dht22/env/bin/activate
    python3 /home/pi/iot_python_dht22/test2/dht22_test2.py

Wiring (BCM GPIO 4):
    DHT22 +   -> RPi 3.3V (pin 1 or 17)
    DHT22 OUT -> RPi GPIO 4 (pin 7)
    DHT22 -   -> RPi GND
"""

import sys
import time

import Adafruit_DHT

# BCM GPIO number for the DATA line (physical pin 7 = GPIO 4).
DHT22_GPIO = 4
SENSOR_TYPE = Adafruit_DHT.DHT22
READ_INTERVAL_SECONDS = 2.0


def read_dht22():
    # Single attempt per loop (like the CircuitPython example); retry on next interval.
    humidity, temperature_c = Adafruit_DHT.read(SENSOR_TYPE, DHT22_GPIO)
    if humidity is None or temperature_c is None:
        raise RuntimeError("Sensor returned empty values")
    return temperature_c, humidity


def main():
    print("Starting DHT22 on GPIO {}. Press Ctrl+C to exit.\n".format(DHT22_GPIO))

    while True:
        try:
            temperature_c, humidity = read_dht22()
            temperature_f = temperature_c * (9 / 5) + 32
            print(
                "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                    temperature_f, temperature_c, humidity
                )
            )

        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going.
            print(error.args[0])
            time.sleep(READ_INTERVAL_SECONDS)
            continue
        except KeyboardInterrupt:
            print("exiting script")
            break

        time.sleep(READ_INTERVAL_SECONDS)

    return 0


if __name__ == "__main__":
    sys.exit(main())

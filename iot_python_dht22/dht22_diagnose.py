#!/usr/bin/env python3
"""Hardware and software diagnostics for DHT22 wiring."""

import argparse
import subprocess
import sys

from config import DHT22_GPIO

PIN_MAP = {
    4: 7,
    17: 11,
    27: 13,
    22: 15,
    7: 26,
}


def run(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return output.decode("utf-8", "ignore").strip()
    except subprocess.CalledProcessError as error:
        return error.output.decode("utf-8", "ignore").strip()


def main():
    parser = argparse.ArgumentParser(description="Diagnose DHT22 wiring and software")
    parser.add_argument("--gpio", type=int, default=DHT22_GPIO)
    args = parser.parse_args()

    physical = PIN_MAP.get(args.gpio, "?")
    print("=== DHT22 diagnostics ===")
    print("Target BCM GPIO: {} (physical pin {})".format(args.gpio, physical))
    print("Model:", run("tr -d '\\0' < /proc/device-tree/model"))
    print()

    print("--- GPIO line level ---")
    pigpiod_running = run("pgrep pigpiod || true")
    if not pigpiod_running:
        print("pigpiod is not running.")
        print("Start it once with: sudo pigpiod")
    else:
        print("pigpiod is running (pid {}).".format(pigpiod_running))

    try:
        import pigpio

        pi = pigpio.pi()
        if pi.connected:
            level = pi.read(args.gpio)
            print("GPIO {} idle level: {} ({})".format(
                args.gpio,
                level,
                "HIGH - looks OK" if level else "LOW - wiring/pull-up issue likely",
            ))
            pi.stop()
        else:
            print("Could not connect to pigpiod.")
    except ImportError:
        print("python3-pigpio is not installed in this environment.")

    print()
    print("--- Sensor read attempts ---")

    try:
        from pigpio_dht22 import read_dht22

        temperature_c, humidity = read_dht22(args.gpio)
        print("[pigpio] OK  Temp={:.1f}C Humidity={:.1f}%".format(temperature_c, humidity))
        return 0
    except Exception as error:
        print("[pigpio] FAIL:", error)

    try:
        import Adafruit_DHT

        humidity, temperature_c = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22,
            args.gpio,
            retries=3,
            delay_seconds=2,
        )
        if humidity is None or temperature_c is None:
            raise RuntimeError("Sensor returned empty values")
        print("[Adafruit_DHT] OK  Temp={:.1f}C Humidity={:.1f}%".format(temperature_c, humidity))
        return 0
    except Exception as error:
        print("[Adafruit_DHT] FAIL:", error)

    print()
    print("--- Likely causes ---")
    print("1. DATA wire not on physical pin {} (BCM GPIO {}).".format(physical, args.gpio))
    print("2. VCC not on pin 1/17 (3.3V) or pin 2/4 (5V).")
    print("3. GND not connected to any ground pin (6, 9, 14, 20, 25, 30, 34, 39).")
    print("4. Bare sensor missing 4.7k-10k pull-up between VCC and DATA.")
    print("5. Wrong sensor type (DHT11 vs DHT22) or defective module.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Continuous DHT22 temperature and humidity readings on Raspberry Pi 4."""

import argparse
import sys
import time

from config import DHT22_GPIO, READ_INTERVAL_SECONDS
from sensor import close_sensor, init_sensor, read_sensor


def main() -> int:
    parser = argparse.ArgumentParser(description="Read DHT22 sensor continuously")
    parser.add_argument(
        "--gpio",
        type=int,
        default=DHT22_GPIO,
        help="BCM GPIO number for DATA pin (default: {})".format(DHT22_GPIO),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=READ_INTERVAL_SECONDS,
        help="Seconds between readings (default: {})".format(READ_INTERVAL_SECONDS),
    )
    args = parser.parse_args()

    init_sensor(args.gpio)
    print("Starting DHT22 on GPIO {}. Press Ctrl+C to exit.\n".format(args.gpio))

    try:
        while True:
            try:
                temperature_c, humidity = read_sensor(args.gpio)
                temperature_f = temperature_c * (9 / 5) + 32
                print(
                    "Temp: {:.1f}°C ({:.1f}°F) | Humidity: {:.1f}%".format(
                        temperature_c, temperature_f, humidity
                    )
                )
            except RuntimeError:
                # DHT22 timing errors are common; retry on the next interval.
                pass

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    finally:
        close_sensor()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Single DHT22 reading for quick wiring verification."""

import argparse
import sys

from config import DHT22_GPIO
from sensor import close_sensor, init_sensor, read_sensor


def main() -> int:
    parser = argparse.ArgumentParser(description="Read DHT22 sensor once")
    parser.add_argument(
        "--gpio",
        type=int,
        default=DHT22_GPIO,
        help="BCM GPIO number for DATA pin (default: {})".format(DHT22_GPIO),
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Number of attempts before failing (default: 5)",
    )
    args = parser.parse_args()

    init_sensor(args.gpio)

    try:
        for attempt in range(1, args.retries + 1):
            try:
                temperature_c, humidity = read_sensor(args.gpio)
                temperature_f = temperature_c * (9 / 5) + 32
                print("GPIO: {}".format(args.gpio))
                print("Temperature: {:.1f}°C ({:.1f}°F)".format(temperature_c, temperature_f))
                print("Humidity: {:.1f}%".format(humidity))
                return 0
            except RuntimeError as error:
                print("Attempt {}/{} failed: {}".format(attempt, args.retries, error), file=sys.stderr)

        print("Could not read sensor. Check wiring and GPIO pin.", file=sys.stderr)
        return 1
    finally:
        close_sensor()


if __name__ == "__main__":
    sys.exit(main())

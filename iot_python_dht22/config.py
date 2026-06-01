"""DHT22 wiring defaults for Raspberry Pi 4 (see _inception PDF)."""

# Physical pin 7 = GPIO 4 (standard default for DHT22 data line)
DHT22_GPIO = 4

# Minimum delay between readings (seconds). DHT22 requires ~2s between reads.
READ_INTERVAL_SECONDS = 2.0

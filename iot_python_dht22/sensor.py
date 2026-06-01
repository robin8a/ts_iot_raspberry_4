"""DHT22 sensor access with modern or legacy library fallback."""

from config import DHT22_GPIO

USE_LEGACY = False
dht_device = None
_legacy_sensor_type = None


def _init_modern(gpio_number):
    import board
    import adafruit_dht

    gpio_pins = {
        4: board.D4,
        17: board.D17,
        27: board.D27,
        22: board.D22,
    }
    pin = gpio_pins.get(gpio_number)
    if pin is None:
        supported = ", ".join(str(n) for n in sorted(gpio_pins))
        raise ValueError("Unsupported GPIO {}. Supported: {}".format(gpio_number, supported))

    return adafruit_dht.DHT22(pin)


def init_sensor(gpio_number=DHT22_GPIO):
    global USE_LEGACY, dht_device, _legacy_sensor_type

    try:
        dht_device = _init_modern(gpio_number)
        USE_LEGACY = False
        _legacy_sensor_type = None
    except ImportError:
        import Adafruit_DHT

        dht_device = None
        _legacy_sensor_type = Adafruit_DHT.DHT22
        USE_LEGACY = True

    return dht_device or _legacy_sensor_type


def read_sensor(gpio_number=DHT22_GPIO):
    if USE_LEGACY and _legacy_sensor_type is None:
        init_sensor(gpio_number)
    elif not USE_LEGACY and dht_device is None:
        init_sensor(gpio_number)

    if USE_LEGACY:
        import Adafruit_DHT

        humidity, temperature_c = Adafruit_DHT.read_retry(
            _legacy_sensor_type,
            gpio_number,
            retries=5,
            delay_seconds=2,
        )
        if humidity is None or temperature_c is None:
            raise RuntimeError("Sensor returned empty values")
        return temperature_c, humidity

    temperature_c = dht_device.temperature
    humidity = dht_device.humidity
    if temperature_c is None or humidity is None:
        raise RuntimeError("Sensor returned empty values")
    return temperature_c, humidity


def close_sensor():
    global dht_device, _legacy_sensor_type
    if dht_device is not None and not USE_LEGACY and hasattr(dht_device, "exit"):
        dht_device.exit()
    dht_device = None
    _legacy_sensor_type = None

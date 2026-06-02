"""DHT22 sensor access with pigpio, modern, or legacy library fallback."""

from config import DHT22_GPIO

BACKEND = None
dht_device = None
_legacy_sensor_type = None
_pigpio_gpio = None

SUPPORTED_GPIO = (4, 7, 17, 22, 27)


def _validate_gpio(gpio_number):
    if gpio_number not in SUPPORTED_GPIO:
        supported = ", ".join(str(n) for n in SUPPORTED_GPIO)
        raise ValueError("Unsupported GPIO {}. Supported BCM pins: {}".format(gpio_number, supported))


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


def _init_pigpio(gpio_number):
    import pigpio

    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("pigpiod is not running. Start it with: sudo pigpiod")
    pi.stop()
    return gpio_number


def init_sensor(gpio_number=DHT22_GPIO):
    global BACKEND, dht_device, _legacy_sensor_type, _pigpio_gpio

    _validate_gpio(gpio_number)

    try:
        dht_device = _init_modern(gpio_number)
        BACKEND = "modern"
        _legacy_sensor_type = None
        _pigpio_gpio = None
    except ImportError:
        try:
            _pigpio_gpio = _init_pigpio(gpio_number)
            BACKEND = "pigpio"
            dht_device = None
            _legacy_sensor_type = None
        except (ImportError, RuntimeError):
            import Adafruit_DHT

            dht_device = None
            _legacy_sensor_type = Adafruit_DHT.DHT22
            _pigpio_gpio = None
            BACKEND = "legacy"

    return dht_device or _legacy_sensor_type or _pigpio_gpio


def read_sensor(gpio_number=DHT22_GPIO):
    if BACKEND is None:
        init_sensor(gpio_number)

    if BACKEND == "pigpio":
        from pigpio_dht22 import read_dht22

        return read_dht22(gpio_number)

    if BACKEND == "legacy":
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
    global dht_device, _legacy_sensor_type, _pigpio_gpio, BACKEND
    if dht_device is not None and BACKEND == "modern" and hasattr(dht_device, "exit"):
        dht_device.exit()
    dht_device = None
    _legacy_sensor_type = None
    _pigpio_gpio = None
    BACKEND = None

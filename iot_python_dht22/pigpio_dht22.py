"""DHT22 reader using pigpio (requires pigpiod daemon)."""

import time

import pigpio


class DHT22Reader(object):
    """Minimal DHT22 driver based on the pigpio example by Joan Evans."""

    def __init__(self, pi, gpio):
        self.pi = pi
        self.gpio = gpio
        self.high_tick = 0
        self.bit = 0
        self.bits = []
        self.temperature = None
        self.humidity = None
        self.staleness = 0
        self.bad_checksum = True

        self.pi.set_mode(self.gpio, pigpio.INPUT)
        self.pi.set_pull_up_down(self.gpio, pigpio.PUD_UP)
        self.cb = self.pi.callback(self.gpio, pigpio.EITHER_EDGE, self._cb)

    def _cb(self, gpio, level, tick):
        if level == 1:
            self.high_tick = tick
            return

        if self.high_tick == 0:
            return

        self.bits.append(tick - self.high_tick)
        self.bit += 1
        if self.bit != 40:
            return

        self.pi.set_watchdog(self.gpio, 0)
        total = sum(self.bits)
        if 8500 <= total <= 9500:
            data = []
            for index in range(5):
                byte = 0
                for bit in range(8):
                    if self.bits[index * 8 + bit] > 100:
                        byte |= 1 << (7 - bit)
                data.append(byte)

            if data[0] + data[1] + data[2] + data[3] == data[4]:
                self.humidity = ((data[0] << 8) + data[1]) * 0.1
                self.temperature = (((data[2] & 0x7F) << 8) + data[3]) * 0.1
                if data[2] & 0x80:
                    self.temperature = -self.temperature
                self.bad_checksum = False

        self.bits = []
        self.bit = 0
        self.high_tick = 0

    def trigger(self):
        self.bad_checksum = True
        self.temperature = None
        self.humidity = None
        self.bits = []
        self.bit = 0
        self.high_tick = 0

        self.pi.write(self.gpio, 0)
        self.pi.set_mode(self.gpio, pigpio.OUTPUT)
        time.sleep(0.02)
        self.pi.set_mode(self.gpio, pigpio.INPUT)
        self.pi.set_pull_up_down(self.gpio, pigpio.PUD_UP)
        self.pi.set_watchdog(self.gpio, 250)
        self.staleness = time.time()

    def cancel(self):
        self.cb.cancel()
        self.pi.set_watchdog(self.gpio, 0)


def read_dht22(gpio, timeout=5.0):
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("pigpiod is not running. Start it with: sudo pigpiod")

    reader = DHT22Reader(pi, gpio)
    try:
        reader.trigger()
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not reader.bad_checksum and reader.temperature is not None:
                return reader.temperature, reader.humidity
            time.sleep(0.05)
        raise RuntimeError("Sensor returned empty values")
    finally:
        reader.cancel()
        pi.stop()

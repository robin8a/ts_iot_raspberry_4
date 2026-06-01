# DHT22 on Raspberry Pi 4 — Process & Testing

This document records the design decisions, deployment process, and testing performed to bring the DHT22 temperature/humidity sensor online on the Raspberry Pi at `192.168.20.26`.

Source guide: `_inception/how to connect the sensor dht22 to raspberry pi 4.pdf`.

Project code lives at:

- Workstation: `iot_python_dht22/`
- Raspberry Pi: `/home/pi/iot_python_dht22/`

---

## 1. Hardware wiring

Default wiring used by the scripts (matches the PDF guide):

| DHT22 pin       | Raspberry Pi 4 pin            | Notes                                  |
| --------------- | ----------------------------- | -------------------------------------- |
| VCC (Power)     | Pin 1 or 17 (3.3V)            | 3.3V recommended for GPIO logic levels |
| DATA (Signal)   | Pin 7 (**GPIO 4 / BCM 4**)    | Standard default                       |
| NC              | —                             | Bare 4-pin sensors only; do not wire   |
| GND             | Pin 9, 14, 20, or 25 (GND)    | Any ground pin                         |

If using a bare DHT22 (not a pre-soldered module), add a **4.7kΩ–10kΩ pull-up resistor** between VCC and DATA. Modules typically have it built in.

Power down the Pi before wiring.

---

## 2. Project layout

```
iot_python_dht22/
├── config.py                  # GPIO pin and read interval defaults
├── sensor.py                  # Modern + legacy library fallback
├── dht22_single_read.py       # One-shot read for wiring verification
├── dht22_test.py              # Continuous readings (Ctrl+C to stop)
├── requirements.txt           # Modern stack (adafruit-circuitpython-dht)
├── requirements-legacy.txt    # Legacy stack (Adafruit-DHT) for old Raspbian
└── setup.sh                   # Bootstraps venv + dependencies
```

### Design notes

- **`sensor.py` abstraction**: tries to load the modern CircuitPython library (`board`, `adafruit_dht`) first and falls back to the legacy `Adafruit_DHT` library on older Python (3.5–3.7) where the modern wheels do not install. Same `init_sensor()` / `read_sensor()` / `close_sensor()` API in both paths so the test scripts stay simple.
- **`setup.sh` auto-detection**: inspects `python3 --version` and picks `requirements-legacy.txt` for Python ≤ 3.7, otherwise installs `python3-pip python3-venv libgpiod-dev` via `apt` and uses the modern requirements file.
- **Python 3.5 compatibility**: scripts use `.format(...)` strings instead of f-strings and avoid PEP 526 type annotations in modules that run on the Pi, so they execute on Raspbian Stretch.
- **DHT22 timing**: a 2-second minimum interval between reads is enforced via `READ_INTERVAL_SECONDS` in `config.py`. Spurious `RuntimeError` from the sensor is caught and ignored on the next interval.

---

## 3. Deployment process

The target Pi reports:

```
Linux raspberrypi 4.19.66-v7+ #1253 SMP Thu Aug 15 11:49:46 BST 2019 armv7l
Python 3.5.3
```

This is Raspbian **Stretch**, which is EOL — `apt update` fails because the Stretch suite was removed from the official mirrors, and `pip` over `pypi.org` works only because piwheels SSL is incompatible with this OpenSSL version. The legacy path was therefore the only viable install route on this device.

### Steps taken

1. SSH connectivity verified with `pi@192.168.20.26` (password auth).
2. Created `/home/pi/iot_python_dht22/` on the Pi.
3. Copied all project files via `scp` (one file per invocation; bulk `scp -r` with glob expansion failed against this server).
4. Ran `setup.sh` over SSH:
   - Detected Python 3.5 → chose `requirements-legacy.txt`.
   - Created venv at `/home/pi/iot_python_dht22/env`.
   - Upgraded `pip` to 20.3.4 (last version supporting Python 3.5).
   - Installed `Adafruit-DHT 1.4.0` from PyPI (piwheels mirror was unreachable due to SSL, pip transparently fell back to pypi.org).

### Setup output (excerpt)

```
==> Detected Python 3.5
==> Using legacy DHT library (Adafruit-DHT)
==> Creating virtual environment at /home/pi/iot_python_dht22/env...
==> Installing Python dependencies...
Successfully installed pip-20.3.4
...
Successfully installed Adafruit-DHT-1.4.0

Setup complete. Run:
  source /home/pi/iot_python_dht22/env/bin/activate
  python3 /home/pi/iot_python_dht22/dht22_single_read.py
  python3 /home/pi/iot_python_dht22/dht22_test.py
```

### Issues fixed during setup

| Issue                                              | Resolution                                                        |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| `apt update` 404 on Stretch repos                  | Skip `apt` install on legacy path; only do it for modern Pi OS.   |
| `f"..."` syntax error in `python3 -c` on Pi (3.5) | Switched all f-strings to `.format(...)`.                         |
| `_OLD_VIRTUAL_PATH: unbound variable` on `source` | Relaxed `set -euo pipefail` to `set -eo pipefail` in `setup.sh`. |
| Modern `adafruit-circuitpython-dht` won't build   | Auto-fallback to `Adafruit-DHT` via Python version check.         |
| `scp -r dir/*` failed (exit 255)                   | Upload files one at a time.                                       |

---

## 4. Running the scripts

On the Pi:

```bash
ssh pi@192.168.20.26
source /home/pi/iot_python_dht22/env/bin/activate

# Single read (wiring sanity check)
python3 /home/pi/iot_python_dht22/dht22_single_read.py

# Continuous readings
python3 /home/pi/iot_python_dht22/dht22_test.py
```

### CLI flags

Both scripts accept:

- `--gpio N` — BCM GPIO number for the DATA pin. Supported: `4`, `17`, `27`, `22`. Default: `4`.
- `--interval S` *(continuous only)* — Seconds between readings. Default: `2.0`.
- `--retries N` *(single read only)* — Attempts before giving up. Default: `5`.

### Expected output

Single read:

```
GPIO: 4
Temperature: 23.4°C (74.1°F)
Humidity: 56.2%
```

Continuous:

```
Starting DHT22 on GPIO 4. Press Ctrl+C to exit.

Temp: 23.4°C (74.1°F) | Humidity: 56.2%
Temp: 23.4°C (74.1°F) | Humidity: 56.3%
...
```

---

## 5. Testing performed

| Test                            | Result                                              |
| ------------------------------- | --------------------------------------------------- |
| SSH connectivity to the Pi      | OK — `Linux raspberrypi 4.19.66-v7+ ... armv7l`     |
| Remote directory creation       | OK — `/home/pi/iot_python_dht22/`                   |
| File upload (7 files via scp)   | OK                                                  |
| `setup.sh` execution            | OK — venv + `Adafruit-DHT 1.4.0` installed          |
| `dht22_single_read.py` run      | **No sensor response** — timed out after 60s        |

The script timeout on the single-read test indicates the sensor itself did not respond, which is almost always one of:

1. **DHT22 not yet physically connected** to the Pi.
2. **DATA wire on the wrong GPIO** — re-verify Pin 7 (BCM 4) or pass `--gpio <N>` matching your wiring.
3. **Missing pull-up resistor** on a bare (non-module) DHT22.
4. **Power not provided** to VCC or GND not connected.

Re-run the single read after verifying wiring; legitimate readings should appear within 5 attempts.

---

## 6. Troubleshooting reference

| Symptom                                                       | Likely cause / fix                                                                                                       |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `RuntimeError: A raw reading was not successful` (occasional) | Normal DHT22 jitter; the script retries automatically.                                                                   |
| All attempts fail / script hangs                              | Wiring issue — see section 5. Verify GPIO with `gpio readall` or `pinout`.                                               |
| `ImportError: No module named 'board'`                        | Venv not activated, or modern library not installed. Run `source env/bin/activate` and re-check `pip list`.              |
| Pi runs newer OS (Bookworm+) and we want the modern stack     | Delete `env/` and re-run `setup.sh`; it will detect the new Python and install `adafruit-circuitpython-dht` + `libgpiod`. |
| `externally-managed-environment` error from pip               | Already handled — `setup.sh` always installs into a dedicated venv.                                                      |

---

## 7. Next steps

- Physically wire the DHT22 per section 1 and re-run `dht22_single_read.py` to confirm a valid reading.
- Consider upgrading the Pi from Raspbian Stretch to a current Raspberry Pi OS release so the modern CircuitPython stack (as recommended by the PDF) can be used.
- Once readings are stable, integrate the sensor reader with the broader IoT pipeline (e.g. publish over MQTT or push to the TerraSacha backend).

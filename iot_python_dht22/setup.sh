#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/env"
PYTHON_VERSION="$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"

echo "==> Detected Python ${PYTHON_VERSION}"

if [[ "${PYTHON_VERSION}" == "3.5" || "${PYTHON_VERSION}" == "3.6" || "${PYTHON_VERSION}" == "3.7" ]]; then
  REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements-legacy.txt"
  echo "==> Using legacy DHT library (Adafruit-DHT)"
else
  REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
  echo "==> Using modern DHT library (adafruit-circuitpython-dht)"
  echo "==> Installing system packages..."
  sudo apt update
  sudo apt install -y python3-pip python3-venv libgpiod-dev
fi

echo "==> Creating virtual environment at ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r "${REQUIREMENTS_FILE}"

echo
echo "Setup complete. Run:"
echo "  source ${VENV_DIR}/bin/activate"
echo "  python3 ${SCRIPT_DIR}/dht22_single_read.py"
echo "  python3 ${SCRIPT_DIR}/dht22_test.py"

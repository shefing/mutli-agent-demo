#!/usr/bin/env bash

# Setup script for Python 3.11 environment with full requirements install.
# - Installs Homebrew (optional, if missing)
# - Installs python@3.11 via Homebrew (if missing)
# - Creates/activates venv with Python 3.11
# - Installs requirements.txt
#
# Usage:
#   bash setup_env_py311.sh
#   source venv/bin/activate
#   streamlit run multi_agent_demo/app.py

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

echo "[1/7] Checking Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo "Homebrew installed. You may need to follow on-screen PATH instructions, then re-run this script."
fi

echo "[2/7] Ensuring python@3.11 is installed"
if ! brew list --versions python@3.11 >/dev/null 2>&1; then
  brew update
  brew install python@3.11
fi

PY311_BIN="$(brew --prefix)/opt/python@3.11/bin/python3.11"
if [ ! -x "$PY311_BIN" ]; then
  echo "Could not locate python3.11 at $PY311_BIN"
  echo "Please ensure python@3.11 is installed and accessible."
  exit 1
fi

echo "[3/7] Removing existing venv (if any)"
rm -rf venv

echo "[4/7] Creating virtual environment with Python 3.11"
"$PY311_BIN" -m venv venv

echo "[5/7] Activating virtual environment"
# shellcheck source=/dev/null
source venv/bin/activate

echo "[6/7] Upgrading pip"
python -m pip install --upgrade pip

echo "[7/7] Installing full requirements from requirements.txt"
pip install -r requirements.txt

echo "\nAll set! To start the app run:"
echo "    source venv/bin/activate"
echo "    streamlit run multi_agent_demo/app.py"

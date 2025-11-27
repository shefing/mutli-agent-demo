#!/usr/bin/env bash

# Fast setup script for this repository.
# It creates a Python virtual environment, activates it, and installs
# the minimum packages needed to run the Streamlit app.
#
# Usage:
#   bash setup_env.sh
#   # then in the same shell session
#   source venv/bin/activate
#   streamlit run multi_agent_demo/app.py

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

echo "[1/5] Creating virtual environment: venv"
python3 -m venv venv

echo "[2/5] Activating virtual environment"
# shellcheck source=/dev/null
source venv/bin/activate

echo "[3/5] Upgrading pip (optional but recommended)"
python -m pip install --upgrade pip || true

echo "[4/5] Installing minimal runtime dependencies"
# Minimal deps installed during this session to run the app on Python 3.9:
# - streamlit
# - python-dotenv
# - plotly
pip install \
  streamlit \
  python-dotenv \
  plotly

echo "[5/5] Done. To start the app run:"
echo "    source venv/bin/activate"
echo "    streamlit run multi_agent_demo/app.py"

echo "\nNotes:"
echo "- Full dependency set in requirements.txt may require Python >= 3.10 (ideally 3.11)."
echo "- If you have Python 3.11 installed, you can recreate the venv with:"
echo "    rm -rf venv && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

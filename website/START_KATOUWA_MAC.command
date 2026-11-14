#!/bin/bash
# KATOUWA launcher. Installs dependencies in a separate local venv (does not edit your Poetry project).
set -e
cd "$(dirname "$0")"
if command -v python3.11 >/dev/null 2>&1; then
  PYTHON=python3.11
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON=python3.12
else
  PYTHON=python3
fi
if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
. .venv/bin/activate
python -m pip install --disable-pip-version-check -r requirements.txt
printf '\nStarting KATOUWA Streamlit interface...\n'
python -m streamlit run app.py

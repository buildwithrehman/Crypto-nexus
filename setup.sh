#!/usr/bin/env bash
set -euo pipefail

# 1 & 2. Strict shell error handling and robust repository root determination
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "Starting CryptoNexus Offline Setup..."

# 3 & 4. Verify Python exists and is version 3.11+
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is not installed or not in PATH."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "ERROR: Python 3.11+ is required. Found version: $PYTHON_VERSION"
    exit 1
fi
echo "Verified Python version: $PYTHON_VERSION"

# 5. Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found in ${SCRIPT_DIR}."
    exit 1
fi

# 6 & 7. Verify wheels/ exists BEFORE attempting installation
if [ ! -d "wheels" ]; then
    echo "ERROR: The 'wheels/' directory is missing."
    echo "This is an offline installation. You must supply all required offline wheels in the 'wheels/' directory."
    echo "Installation cannot proceed without network access. Exiting."
    exit 1
fi

# 8. Create .venv if it does not exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment '.venv'..."
    python3 -m venv .venv
else
    echo "Virtual environment '.venv' already exists."
fi

# 9. Use the .venv Python/pip
VENV_PYTHON=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

if [ ! -f "$VENV_PIP" ]; then
    echo "ERROR: Pip not found in virtual environment."
    exit 1
fi

# 10 & 11. Install ONLY from wheels/ using offline command
echo "Installing dependencies offline from wheels/..."
"$VENV_PIP" install \
    --no-index \
    --find-links wheels/ \
    -r requirements.txt

# 12, 13 & 14. Verify required imports and report failures explicitly
echo "Verifying imports..."
"$VENV_PYTHON" -c "
import sys
modules = [
    'fastapi', 'pydantic', 'uvicorn', 'duckdb', 'pandas', 'numpy',
    'scipy', 'networkx', 'community', 'sklearn', 'hdbscan', 'shap',
    'joblib', 'maxminddb'
]
failed = False
for mod in modules:
    try:
        __import__(mod)
    except ImportError as e:
        print(f'ERROR: Failed to import {mod}: {e}')
        failed = True

if failed:
    sys.exit(1)
print('All required modules imported successfully.')
"

echo "CryptoNexus offline setup completed successfully."
exit 0

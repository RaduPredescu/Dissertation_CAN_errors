#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -c 'import cantools' || { echo 'Install Python dependencies first: python -m pip install -r requirements.txt'; exit 1; }
mkdir -p dbc/upstream
URL='https://raw.githubusercontent.com/commaai/opendbc/master/opendbc/dbc/vw_mqbevo.dbc'
curl -fL --retry 3 --connect-timeout 10 "$URL" -o dbc/upstream/vw_mqbevo.dbc
sha256sum dbc/upstream/vw_mqbevo.dbc
python -m scripts.check_upstream
printf '\nFor full DBC in the dashboard, start FastAPI with:\n'
printf 'CAN_LAB_DBC_PATH=dbc/upstream/vw_mqbevo.dbc python -m uvicorn dashboard_api.app:app --reload\n'

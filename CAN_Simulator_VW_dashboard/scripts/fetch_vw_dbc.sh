#!/usr/bin/env bash
set -euo pipefail
mkdir -p dbc/upstream
URL='https://raw.githubusercontent.com/commaai/opendbc/master/opendbc/dbc/vw_mqbevo.dbc'
curl -fL --retry 3 "$URL" -o dbc/upstream/vw_mqbevo.dbc
sha256sum dbc/upstream/vw_mqbevo.dbc
printf '\nDBC original salvat pentru comparare. Nu este automat considerat valid pentru Tiguan CT 2025.\n'
python3 scripts/check_upstream.py

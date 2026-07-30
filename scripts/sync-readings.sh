#!/usr/bin/env bash
# Pull the latest readings.csv from the Pi into this repo before a portfolio push.
set -euo pipefail
cd "$(dirname "$0")/.."
scp admin@plant-pi.local:~/plant-monitor/readings.csv ./readings.csv

if [[ ! -s readings.csv ]]; then
  echo "Error: readings.csv is empty after sync." >&2
  exit 1
fi

header="$(head -1 readings.csv | tr -d '\r\n')"
if [[ "$header" != "timestamp,plant_id,plant_name,raw_value,moisture_percentage,status_category" ]]; then
  echo "Error: readings.csv has an unexpected header: $header" >&2
  exit 1
fi

# Normalize line endings for git / pandas on Mac
sed -i '' $'s/\r$//' readings.csv 2>/dev/null || sed -i 's/\r$//' readings.csv

echo "Synced readings.csv ($(wc -l < readings.csv) lines)"
echo "Next: git add readings.csv && git commit -m 'Update readings snapshot' && git push"

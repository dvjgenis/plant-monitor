#!/usr/bin/env bash
# Pull the latest readings.csv from the Pi into this repo before a portfolio push.
set -euo pipefail
cd "$(dirname "$0")/.."
scp admin@plant-pi.local:~/plant-monitor/readings.csv ./readings.csv
echo "Synced readings.csv ($(wc -l < readings.csv) lines)"
echo "Next: git add readings.csv && git commit -m 'Update readings snapshot' && git push"

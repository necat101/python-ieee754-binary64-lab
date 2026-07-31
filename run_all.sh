#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "=== python-ieee754-binary64-lab ==="
python3 run.py
python3 -m unittest test_binary64 -v
python3 results_to_md.py
echo "=== done: results.json / results.csv / RESULTS.md ==="

#!/usr/bin/env bash
# run_lab.sh — Linux/macOS wrapper for python-ieee754-binary64-lab
# Runs cases, unittest, and regenerates RESULTS.md
set -euo pipefail
cd "$(dirname "$0")"

# find a suitable python (>= 3.12)
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1; then
    if "$py" -c 'import sys; exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then
      PYTHON="$py"
      break
    fi
  fi
done

if [ -z "${PYTHON:-}" ]; then
  echo "ERROR: Python 3.12+ required – none found in PATH (tried: python3, python, py)" >&2
  exit 1
fi

ver=$("$PYTHON" -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))')
echo "=== python-ieee754-binary64-lab | Python $ver ==="
echo

echo "[1/3] Running cases..."
"$PYTHON" run.py
echo

echo "[2/3] Running unittest..."
"$PYTHON" -m unittest test_binary64 -v
echo

echo "[3/3] Rendering RESULTS.md..."
"$PYTHON" results_to_md.py
echo

echo "=== done ==="
echo "  results.json  — full per-case output"
echo "  results.csv   — summary table"
echo "  RESULTS.md    — rendered summary"

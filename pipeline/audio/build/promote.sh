#!/bin/bash
# promote.sh <Id>: after the critic passed, commit its record (pipeline/audio/critic/<Id>.json) and the takes'
# provenance rows become the generated rows (one row per path). Refuses without a passing record on the current bytes.
set -e
cd "$(dirname "$0")/../../.."
python3 pipeline/audio/build/provenance.py record "$1"
python3 pipeline/audio/build/provenance.py generated "$1"

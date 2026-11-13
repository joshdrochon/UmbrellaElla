#!/bin/bash
# promote.sh <Id>: after the critic passed, the takes' provenance rows become the generated rows (one row per path).
set -e
cd "$(dirname "$0")/../../.."
python3 pipeline/audio/build/provenance.py generated "$1"

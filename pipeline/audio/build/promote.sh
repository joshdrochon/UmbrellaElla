#!/bin/bash
# promote.sh <Id>: after the critic passed, drop the placeholder provenance rows and add the generated rows.
set -e
cd "$(dirname "$0")/../../.."
grep -v "^Audio/Source/$1/.*placeholder: audio critic fail" pipeline/art/provenance.csv > /tmp/prov.$$ && cp /tmp/prov.$$ pipeline/art/provenance.csv && rm /tmp/prov.$$
python3 pipeline/audio/build/provenance.py "$1"

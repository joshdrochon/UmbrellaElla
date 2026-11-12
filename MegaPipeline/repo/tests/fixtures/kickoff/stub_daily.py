#!/usr/bin/env python3
"""Stands in for `bash tools/ue/daily.sh` in the kickoff --until tests (KICKOFF_PACKAGE_CMD): no engine. It writes the
DAILY record line tools/ue_run.py daily writes, for the commit it runs on. STUB_DAILY_FAIL=1: the smoke fails."""
import os
import subprocess
import sys

sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "unknown"
smoke = "FAIL" if os.environ.get("STUB_DAILY_FAIL") == "1" else "PASS"
line = (f"DAILY {sha} | stub-mac/Darwin 24.6.0 | Development | clean=PASS build=PASS test=PASS package=PASS "
        f"smoke={smoke} | Not checked: display")
rec = os.path.join("Saved", "Logs", "pipeline", "daily-records.txt")
os.makedirs(os.path.dirname(rec), exist_ok=True)
with open(rec, "a", encoding="utf-8") as fh:
    fh.write(line + "\n")
print(line)
sys.exit(1 if smoke == "FAIL" else 0)

#!/usr/bin/env python3
"""Import artella's Ella sheets into their slots as tracked _PH stand-ins (never under the passed name).

  python3 tools/build/assets/art_ella_import.py [idle ...]

Each state maps to its source sheet and its art-inventory visual id. Idle is Josh's approved grid (pipeline/art/approvals.json,
piece ella-up-open), imported untouched: its sha256 is checked against approvals.json before the import, and a mismatch stops it.
The dark silhouette (tools/build/assets/art_ella_silhouette.py) stays a proof file only (lead order, Nov 13 20:05).
The import itself runs through tools/build/assets/import_art_candidate.py (UnrealEditor-Cmd -run=pythonscript
-unattended -nullrhi -nosplash -nocrashreports, through the slot lock), which lands it as <slot>_PH.
Take the LFS lock on the .uasset first (git lfs lock Content/UmbrellaElla/Art/Ella/T_Ella_<State>_PH.uasset).
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SIL = os.path.join("pipeline", "art", "proof", "artella", "silhouette")
APPROVALS = os.path.join("pipeline", "art", "approvals.json")
# state -> (source sheet, art-inventory visual id, approvals.json piece or None). Only idle is imported today.
SHEETS = {
    "idle": (os.path.join("pipeline", "art", "proof", "standins", "ella-up-open", "Ella_idle_N24_grid.png"), "ella-state:Idle", "ella-up-open"),
}


def approved_sha(piece):
    with open(os.path.join(ROOT, APPROVALS), encoding="utf-8") as fh:
        return {a["piece"]: a["sha256"] for a in json.load(fh).get("approvals", [])}.get(piece)


def main(argv):
    states = argv or ["idle"]
    for s in states:
        if s not in SHEETS:
            raise SystemExit("art_ella_import: unknown state %r (known: %s)" % (s, ", ".join(sorted(SHEETS))))
        png, slot, piece = SHEETS[s]
        if piece:
            want = approved_sha(piece)
            with open(os.path.join(ROOT, png), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()
            if got != want:
                raise SystemExit("art_ella_import: %s sha256 %s is not the approved %s bytes (%s)" % (png, got, piece, want))
            print("art_ella_import: %s sha256 %s = approvals.json %s" % (png, got, piece))
        rc = subprocess.call([sys.executable, os.path.join(HERE, "import_art_candidate.py"), os.path.join(ROOT, png), slot])
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

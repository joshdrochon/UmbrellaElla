#!/usr/bin/env python3
"""Import artella's Ella sheets into their slots as tracked _PH stand-ins (never under the passed name).

  python3 tools/build/assets/art_ella_import.py [idle ...]

Each state maps to its source sheet (made by tools/build/assets/art_ella_silhouette.py) and its art-inventory visual id.
The import itself runs through tools/build/assets/import_art_candidate.py (UnrealEditor-Cmd -run=pythonscript
-unattended -nullrhi -nosplash -nocrashreports, through the slot lock), which lands it as <slot>_PH.
Take the LFS lock on the .uasset first (git lfs lock Content/UmbrellaElla/Art/Ella/T_Ella_<State>_PH.uasset).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SIL = os.path.join("pipeline", "art", "proof", "artella", "silhouette")
# state -> (source sheet, art-inventory visual id). Only idle is imported today; hurt and down wait for a frame that shows them.
SHEETS = {
    "idle": (os.path.join(SIL, "ella-idle_N24_grid.png"), "ella-state:Idle"),
}


def main(argv):
    states = argv or ["idle"]
    for s in states:
        if s not in SHEETS:
            raise SystemExit("art_ella_import: unknown state %r (known: %s)" % (s, ", ".join(sorted(SHEETS))))
        png, slot = SHEETS[s]
        rc = subprocess.call([sys.executable, os.path.join(HERE, "import_art_candidate.py"), os.path.join(ROOT, png), slot])
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""B7 measured check: Ella's z at the route shots stays inside the arena picture band.

Usage: python3 pipeline/art/proof/move/b7/check_ceiling.py <run log>
Reads the JOURNEY_STEP line of each `shot b7_*` step (ella=(x,z)) and the matching PNG next to this file.
Band: arena bottom 0 to top 1080 (ArenaCameraTuning.ArenaHeight, arena spawned at the origin), so Ella's root may be
at most 1080 - capsule half-height 44 = 1036 (the Start Game stop agentplay measured). The camera scrolls only in X.
"""
import re
import sys
from pathlib import Path

B7_ARENA_TOP_Z = 1080.0
B7_START_GAME_STOP_Z = 1036.0
B7_TOLERANCE = 0.5
B7_SHOTS = ("b7_01_route_idle60", "b7_02_keeper_handoff")


def main(log_path):
    text = Path(log_path).read_text(errors="replace")
    here = Path(__file__).resolve().parent
    ok = True
    for name in B7_SHOTS:
        lines = [l for l in text.splitlines() if "JOURNEY_STEP" in l and f'cmd="shot {name}' in l]
        if not lines:
            print(f"B7 FAIL {name}: no JOURNEY_STEP line")
            ok = False
            continue
        line = lines[-1]
        m = re.search(r"ella=\((-?\d+),(-?\d+)\)", line)
        mode = re.search(r"mode=(\w+)", line)
        if not m:
            print(f"B7 FAIL {name}: no ella position")
            ok = False
            continue
        x, z = float(m.group(1)), float(m.group(2))
        png = here / f"{name}.png"
        passed = (0.0 <= z <= B7_START_GAME_STOP_Z + B7_TOLERANCE) and "result=PASS" in line and png.exists()
        ok &= passed
        print(f"B7 {'PASS' if passed else 'FAIL'} {name}: mode={mode.group(1) if mode else '?'} ella_x={x:.0f} "
              f"ella_z={z:.0f} max_z={B7_START_GAME_STOP_Z:.0f} (arena top {B7_ARENA_TOP_Z:.0f}) png={'yes' if png.exists() else 'no'}")
    print("B7 RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

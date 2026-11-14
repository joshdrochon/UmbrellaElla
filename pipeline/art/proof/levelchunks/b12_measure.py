"""B12 capture check (levelchunks): in the real game the real-key walker goes CP0 -> CP1 from the route ceiling with no
assist, past x 1 920 (the arena's home right wall), and Ella is drawn in the CP1 shot.
Usage: python3 pipeline/art/proof/levelchunks/b12_measure.py <journey.log>
Reads the trimmed `route 1 60 1` step (the second `route` step) and the `shot b12_cp1` line, if any."""
import re
import sys

HOME_RIGHT_WALL_X = 1920.0  # arena width: the wall that stood in slot 0 on the route before the fix
WALKER_TIMEOUT_S = 60.0


def main():
    lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
    routes = [ln for ln in lines if ln.startswith("JOURNEY_STEP") and 'cmd="route ' in ln]
    assists = [ln for ln in lines if "JOURNEY_ASSIST routeassist=1" in ln and "ASSIST placed" in ln]
    shot = next((ln for ln in lines if 'cmd="shot b12_cp1"' in ln), "")
    if len(routes) < 2:
        print("B12_CAPTURE_FAIL: fewer than two route steps in the log")
        return 1
    step = routes[1]
    ok_step = " result=PASS " in step
    cp = re.search(r'detail="cp=(\d+)', step)
    secs = re.search(r"after ([\d.]+)s", step)
    best = re.search(r"x_best=(-?\d+)", step)
    drawn = re.search(r"ella=drawn\((\d+),(\d+)\)", shot)
    cp_v = int(cp.group(1)) if cp else -1
    secs_v = float(secs.group(1)) if secs else None
    best_v = float(best.group(1)) if best else None
    print(f"b12_measure route_step={'PASS' if ok_step else 'FAIL'} cp={cp_v} after_s={secs_v} x_best={best_v} "
          f"assist_placed={len(assists)} shot_ella={'drawn' + str(drawn.groups()) if drawn else 'not drawn'}")
    ok = (ok_step and cp_v == 1 and secs_v is not None and secs_v < WALKER_TIMEOUT_S and best_v is not None
          and best_v > HOME_RIGHT_WALL_X and not assists and drawn is not None)
    print("B12_CAPTURE_" + ("OK" if ok else "FAIL") + ": real-key walker CP0 -> CP1 from the route ceiling, no assist, Ella drawn at CP1")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

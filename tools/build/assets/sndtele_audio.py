#!/usr/bin/env python3
"""sndtele lane: rebuild the telegraph and motion sounds (docs/build/areas/sndtele.md).
Reuses the audio area's helpers without forking them: pipeline/audio/build/{regen.py,critic.sh,provenance.py}
(read from this tree once area/audio is merged, else from the area/audio branch into Saved/sndtele/build/, never
committed). This file only adds the lane's recipes (tools/build/assets/sndtele_recipes.py), the seamless-loop step
and sorted provenance rows.
  sndtele_audio.py build <Id> [--fresh] [--tries N]   layers -> mix -> (loops: crossfade wrap) -> measured checks
  sndtele_audio.py critic <Id> [--event]              new audio_loop round + fresh blind critic session + verdict
                                                      (--event: the brief also names the sound's event, see
                                                      docs/build/requests/sndtele.md)
  sndtele_audio.py prov generated <Id> | prov placeholder <Id> "<gap>"
ElevenLabs key: source ~/.umbrella-ella.env in the one shell that runs `build`; it is never printed."""
import csv, math, os, runpy, struct, subprocess, sys, types, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from sndtele_recipes import RECIPES  # noqa: E402

CARD = "SNDTELE"
HELPERS = ("regen.py", "critic.sh", "provenance.py")
PROV = ROOT / "pipeline/art/provenance.csv"
XFADE_S = 0.5          # loop wrap crossfade; the mix is rendered this much longer than the loop


def helper_dir():
    """The audio area's build folder: in this tree when merged, else a scratch copy from its branch."""
    d = ROOT / "pipeline/audio/build"
    if all((d / f).is_file() for f in HELPERS):
        return d
    d = ROOT / "Saved/sndtele/build"
    d.mkdir(parents=True, exist_ok=True)
    for f in HELPERS:
        for ref in ("area/audio", "origin/area/audio"):
            r = subprocess.run(["git", "show", f"{ref}:pipeline/audio/build/{f}"], capture_output=True, cwd=ROOT)
            if r.returncode == 0:
                (d / f).write_bytes(r.stdout)
                break
        else:
            sys.exit(f"cannot read pipeline/audio/build/{f} from area/audio")
    return d


def recipes_module(recipes):
    m = types.ModuleType("recipes")
    m.RECIPES = recipes
    sys.modules["recipes"] = m


def loopify(path, loop_s):
    """Seamless loop: the first XFADE_S of the take is an equal-power blend with what follows the loop end, so the
    last sample runs straight into the first."""
    with wave.open(str(path), "rb") as w:
        rate, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if ch != 1 or sw != 2:
        sys.exit(f"{path}: loopify wants 16-bit mono")
    s = struct.unpack(f"<{n}h", raw)
    keep = int(round(loop_s * rate)); x = n - keep
    if x < 64:
        sys.exit(f"{path}: {n / rate:.2f} s is too short for a {loop_s} s loop")
    out = list(s[:keep])
    for i in range(x):
        p = 0.5 * math.pi * i / x
        out[i] = int(max(-32767, min(32767, s[i] * math.sin(p) + s[keep + i] * math.cos(p))))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(struct.pack(f"<{keep}h", *out))


def build(sid, fresh=False, tries=4):
    rec = dict(RECIPES[sid])
    loop_s = rec.pop("loop_s", None)
    if loop_s:
        rec["seconds"] = loop_s + XFADE_S
        rec["fade_out"] = 0.001
    recipes_module({sid: rec})
    os.environ.setdefault("REGEN_DIR", str(ROOT / "Saved/sndtele/gen"))
    argv = sys.argv
    sys.argv = ["regen.py", sid, "--tries", str(tries)] + (["--fresh"] if fresh else [])
    try:
        runpy.run_path(str(helper_dir() / "regen.py"), run_name="regen")
    finally:
        sys.argv = argv
    takes = sorted((ROOT / "Audio/Source" / sid).glob("*.wav"))
    if loop_s:
        for t in takes:
            loopify(t, loop_s)
    r = subprocess.run([sys.executable, "tools/audio_style_check.py", "check", "Audio/Source", "--ids", sid],
                       cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


def event_line(sid, brief):
    """Workaround for the packet defect in docs/build/requests/sndtele.md: the blind packet gives the family target
    (several different events) but not which event this sound is for, so the critic cannot answer A5. Adds that one
    fact from pipeline/audio/sound-list.csv to the copied brief; no id, no history."""
    with open(ROOT / "pipeline/audio/sound-list.csv", newline="", encoding="utf-8") as fh:
        row = {r["id"]: r for r in csv.DictReader(fh)}[sid]
    kind = "a seamless loop" if row["kind"] == "loop" else "a one-shot"
    line = (f"The event X is for, from the team's sound list: {row['event']} ({kind}; class {row['class']}). "
            "Judge A5 against this event; the family target above also describes other events of the same family.")
    if row["kind"] == "loop":
        line += (" X is a loop that plays for as long as the event lasts: it has no onset and no tail by design, and"
                 " attack_ms and decay_s (one-shot measures) are not checked for it, so their ranges do not apply.")
    line += "\n\n"
    text = Path(brief).read_text(encoding="utf-8")
    anchor = "Brand rules for every sound in this game:"
    if anchor not in text:
        sys.exit(f"{brief}: no '{anchor}' line to place the event before")
    Path(brief).write_text(text.replace(anchor, line + anchor, 1), encoding="utf-8")
    return 0


def critic(sid, event=False):
    """Stock critic.sh (the gate's packet), or with --event the same script plus the event line in the brief."""
    sh = helper_dir() / "critic.sh"
    if event:
        src = sh.read_text()
        anchor = 'cp -R "$PKT"/. "$D"/'
        if anchor not in src:
            sys.exit("critic.sh changed: cannot place the event line")
        sh = ROOT / "Saved/sndtele/build/critic_event.sh"
        sh.parent.mkdir(parents=True, exist_ok=True)
        sh.write_text(src.replace(anchor, anchor + f'\npython3 "$ROOT/tools/build/assets/sndtele_audio.py" event-line "$PIECE" "$D/brief.md" || exit 2', 1))
    return subprocess.run(["bash", str(sh), sid, CARD], cwd=ROOT).returncode


def place_sorted(rows, sid):
    """This id's rows sit where asset_path order puts them among the Audio/Source rows (parallel lanes then rarely
    touch the same lines)."""
    pre = f"Audio/Source/{sid}/"
    mine = sorted((r for r in rows if r and r[0].startswith(pre)), key=lambda r: r[0])
    rest = [r for r in rows if not (r and r[0].startswith(pre))]
    at = None
    for i, r in enumerate(rest):
        if r and r[0].startswith("Audio/Source/"):
            if r[0] > pre:
                at = i
                break
            at = i + 1
    at = len(rest) if at is None else at
    return rest[:at] + mine + rest[at:]


def prov(cmd, sid, gap=""):
    mod = runpy.run_path(str(helper_dir() / "provenance.py"), run_name="provenance")
    recipes_module({sid: RECIPES[sid]})
    with open(PROV, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    mod["ROOT"] = ROOT
    if cmd == "generated" or not any(r and r[0].startswith(f"Audio/Source/{sid}/") for r in rows):
        rows = mod["generated"](rows, sid)
    if cmd == "placeholder":
        rows = mod["placeholder"](rows, sid, gap)
    rows = place_sorted(rows, sid)
    with open(PROV, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)
    print(f"provenance: {sid} {cmd}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "build":
        tries = int(a[a.index("--tries") + 1]) if "--tries" in a else 4
        sys.exit(build(a[1], "--fresh" in a, tries))
    if len(a) >= 2 and a[0] == "critic":
        sys.exit(critic(a[1], "--event" in a))
    if len(a) == 3 and a[0] == "event-line":
        sys.exit(event_line(a[1], a[2]))
    if len(a) >= 3 and a[0] == "prov" and a[1] in ("generated", "placeholder"):
        sys.exit(prov(a[1], a[2], a[3] if len(a) > 3 else ""))
    sys.exit(__doc__)

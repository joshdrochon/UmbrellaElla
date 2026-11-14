#!/usr/bin/env python3
"""Art slots: the asset name every shipped visual is drawn from (Josh, Nov 12). Stdlib only.

  art_slots.py cpp        print the catalogue rows for Source/.../Feedback/Art/ArtSlotCatalog.inc
  art_slots.py check      FAIL if ArtSlotCatalog.inc differs from what this file derives from docs/build/art-inventory.csv
  art_slots.py list       print visual -> slot -> drawn_by
  art_slots.py standins   print each stand-in picture's verdict (ok / unkeyed / framed)

A slot is /Game/UmbrellaElla/Art/<Folder>/<Asset> (Asset carries its prefix, T_ for a texture). The game loads the passed
asset <Asset> first and the tracked placeholder <Asset>_PH second, and draws the stand-in only when neither exists.
An art lane imports a candidate into <Asset>_PH with tools/build/assets/import_art_candidate.py.

Stand-in admission (visualqa, Josh's 15:50 frame): a sprite-like stand-in (anything but a full-screen backdrop or
screen) must be keyed on transparency and carry no drawn frame border. One that fails is generated with
bStandInOk = false, and the game never loads its _PH (the plain stand-in, or nothing, is drawn instead).
"""
import csv
import hashlib
import json
import os
import re
import struct
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INC = os.path.join("Source", "UmbrellaElla", "Private", "Feedback", "Art", "ArtSlotCatalog.inc")
CSV = os.path.join("docs", "build", "art-inventory.csv")
STANDINS = os.path.join("pipeline", "art", "standins.json")
# video_to_strip.py --grid-cols: every packed stand-in grid in the repo is cut 6 cells per row (artvideo, videoframes).
GRID_COLS = 6
SHEET_NAME = re.compile(r"_N(\d+)_(grid|strip)\.png$")
GAME_ROOT = "/Game/UmbrellaElla/Art"
VFX_COLS = 8
VFX_RAW = os.path.join("Art", "Source", "VFX", "Raw")
# Pictures that legitimately fill the frame edge to edge: no keying or frame test.
FULL_FRAME_KINDS = ("bg-layer", "bg", "screen", "menu-backdrop", "ui")
# Full-screen effects: a darkening over the whole view, drawn edge to edge on purpose.
FULL_FRAME_VISUALS = {"vfx-sheet:VFX_Blackout"}
# Measured on a copy scaled to this many pixels on its long side.
STANDIN_PROBE_PX = 192
# Verdicts measured by this reader, keyed "<sha256>:<cols>x<rows>" (a cache of probe_alpha; never a second reader).
VERDICT_CACHE = os.path.join("pipeline", "art", "standin-verdicts.json")
READER_VERSION = "py-area-1"
# Keyed: at least this share of the picture's pixels are clear (alpha < STANDIN_CLEAR_ALPHA).
STANDIN_MIN_CLEAR = 0.05
STANDIN_CLEAR_ALPHA = 16
# Framed: an opaque line runs along at least this share of an edge, inside the outer band, on 2 or more sides.
STANDIN_FRAME_COVER = 0.70
STANDIN_FRAME_BAND = 0.04
STANDIN_FRAME_SIDES = 2

BG_LAYER = {"Sky": "Paper", "FarLand": "Skyline", "Base": "BgBase", "NearArchitecture": "BgArchitecture",
            "ClockWaterWind": "BgClockWaterWind"}
BG = {"atmosphere": "BgAtmosphere", "water": "BgWater", "clocks": "BgClock", "land": "BgLand", "start-end": "BgStartEnd"}
ELLA = {"ella:free-fall": "Ella_FreeFall", "ella:hop-cartwheel-dash": "Ella_Motion", "ella:mode-transition": "Ella_Transition",
        "ella:condition-100-to-0": "Ella_Condition", "ella:living-critical": "Ella_Critical",
        "umbrella:prop": "Umbrella", "umbrella:repair": "UmbrellaRepair"}
KEEPER = {"body-hover-flap": "Owl", "clock-cover-glass-hands": "Clock", "living-departure": "Departure",
          "mechanism-front": "MechFront", "mechanism-middle": "MechMiddle", "mechanism-rear": "MechRear",
          "part-masks-7-6-4-0": "DamageMasks", "talon-empty-and-closed": "Talon", "wings-gust-wear": "Wing"}
UI_SOURCE = {"ui:clock-face": "ClockFace", "ui:ground-Grain": "Grain", "ui:ground-Ground": "Ground",
             "ui:head-Paused": "HeadPaused", "ui:head-Settings": "HeadSettings", "ui:panel": "Panel", "ui:title-lockup": "TitleLockup"}
NO_SLOT = {"ui:font"}   # a font file, not a texture: nothing to load
UI = {"ui:xp-ring": "XpRing", "ui:spell-wheel": "SpellWheel", "ui:device-and-remap-prompts": "Prompts"}
SHOTS = {"shot:red": "OwlBolt", "shot:red-impact": "BoltHit", "shot:gold": "WandShot", "shot:stream-beam": "StreamBeam",
         "shot:yellow": "YellowShot", "wind:current-field": "WindZone", "wind:decor-lines": "WindLines"}
SCENE = {"scene:gameplay-frame": "Frame", "world:mill-and-traps": "WorldMill", "world:refuge-and-yellow-bay": "WorldRefuge",
         "world:solids": "WorldSolids", "world:solids-block": "WorldSolidsBlock"}
TILED = {"bg-layer:Sky"}   # paper: UV-tiled across the panel

# visual prefix -> the C++ class that loads the slot today ("-" = no consumer yet; see docs/build/requests/artslots.md)
CONSUMER = [("bg-layer:", "UUmbrellaBackdropSubsystem"), ("ella-state:", "UEllaAnimPresenterComponent"),
            ("enemy:", "UEnemyPresenterSubsystem"),
            ("wind:", "UWindPresenterSubsystem"), ("shot:red-impact", "UUmbrellaVfxSubsystem"), ("shot:red", "UShotPresenterSubsystem"),
            ("shot:gold", "UShotPresenterSubsystem"), ("shot:yellow", "UShotPresenterSubsystem"), ("keeper:body-hover-flap", "UKeeperPresenterSubsystem"),
            ("keeper:wings-gust-wear", "UKeeperPresenterSubsystem"), ("keeper:mechanism-", "UKeeperPresenterSubsystem"),
            ("keeper:clock-cover", "UKeeperPresenterSubsystem"), ("keeper:talon-", "UKeeperPresenterSubsystem"),
            ("vfx-sheet:", "VfxSheetVisual"), ("screen:", "UUiArtSubsystem"),
            ("bg:", "USceneArtSubsystem"), ("scene:", "USceneArtSubsystem"),
            ("shot:stream-beam", "UShotPresenterSubsystem"),
            ("keeper:living-departure", "UKeeperPresenterSubsystem"), ("keeper:part-masks-", "UKeeperPresenterSubsystem"),
            ("world:", "UWorldArtSubsystem"), ("ui:", "UUiArtSubsystem"), ("menu-backdrop:", "UUiArtSubsystem"),
            ("vfx-material:", "VfxSheetVisual"),
            ("ella:", "UEllaAnimPresenterComponent"), ("umbrella:", "UEllaAnimPresenterComponent")]


def derive(visual):
    """(folder, asset, cols, tile) for a visual id, or None."""
    kind, _, rest = visual.partition(":")
    if visual.startswith("bg-layer:") and rest in BG_LAYER:
        return "Scene", "T_" + BG_LAYER[rest], 1, visual in TILED
    if kind == "bg" and rest in BG:
        return "Scene", "T_" + BG[rest], 1, False
    if kind == "ella-state":
        return "Ella", "T_Ella_" + rest, 1, False
    if visual in ELLA:
        return "Ella", "T_" + ELLA[visual], 1, False
    if kind == "enemy":
        return "Enemy", "T_Enemy_" + rest.replace(":", "_"), 1, False
    if kind == "keeper" and rest in KEEPER:
        return "Keeper", "T_Keeper_" + KEEPER[rest], 1, False
    if kind == "menu-backdrop":
        return "UI", "T_MenuBackdrop_" + rest, 1, False
    if kind == "screen":
        return "UI", "T_Screen_" + rest, 1, False
    if visual in UI_SOURCE:
        return "UI", "T_UI_" + UI_SOURCE[visual], 1, False
    if visual in UI:
        return "UI", "T_" + UI[visual], 1, False
    if visual in SHOTS:
        return "Shots", "T_" + SHOTS[visual], 1, False
    if visual in SCENE:
        return "Scene", "T_" + SCENE[visual], 1, False
    if kind == "vfx-sheet":
        return "VFX", "T_" + rest, VFX_COLS, False
    if kind == "vfx-material":
        return "VFX", rest, 1, False
    return None


def png_size(path):
    """(width, height) from a PNG header, or None."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
    except OSError:
        return None
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def sheet_layout(copy_path, size):
    """(cols, rows) of a packed frame sheet named <stem>_N<n>_grid/strip.png, or None for a single picture.
    FAIL when the picture does not split into whole cells (the slot would draw a cut frame)."""
    m = SHEET_NAME.search(copy_path or "")
    if not m:
        return None
    frames = int(m.group(1))
    cols = frames if m.group(2) == "strip" else GRID_COLS
    rows = -(-frames // cols)
    if size and (size[0] % cols or size[1] % rows):
        raise SystemExit("FAIL art_slots: %s (%dx%d) does not split into %dx%d cells" % (copy_path, size[0], size[1], cols, rows))
    return cols, rows


def read_png_rgba(path):
    """(width, height, rows of RGBA bytes) for an 8-bit non-interlaced PNG. Stdlib only."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG: %s" % path)
    i, idat, w, h, depth, ctype, interlace = 8, [], 0, 0, 8, 6, 0
    while i < len(data):
        ln = struct.unpack(">I", data[i:i + 4])[0]
        tag, chunk = data[i + 4:i + 8], data[i + 8:i + 8 + ln]
        if tag == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif tag == b"IDAT":
            idat.append(chunk)
        i += 12 + ln
    if depth != 8 or interlace or ctype not in (0, 2, 4, 6):
        raise ValueError("unsupported PNG layout in %s" % path)
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw, stride, rows, prev, p = zlib.decompress(b"".join(idat)), w * bpp, [], bytearray(w * bpp), 0
    for _ in range(h):
        kind, line = raw[p], bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            if kind == 1:
                line[x] = (line[x] + a) & 255
            elif kind == 2:
                line[x] = (line[x] + prev[x]) & 255
            elif kind == 3:
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
            elif kind == 4:
                b, c = prev[x], (prev[x - bpp] if x >= bpp else 0)
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    alpha = (lambda r, x: r[x * bpp + bpp - 1]) if ctype in (4, 6) else (lambda r, x: 255)
    return w, h, [[alpha(r, x) for x in range(w)] for r in rows]


def shrink_alpha(w, h, alpha, longest=None):
    """Area-average an alpha grid down to `longest` pixels on its long side (aspect kept). Pure, stdlib only."""
    longest = STANDIN_PROBE_PX if longest is None else longest
    if max(w, h) <= longest:
        return w, h, alpha
    scale = float(longest) / max(w, h)
    tw, th = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    xs = [(tx * w // tw, max(tx * w // tw + 1, (tx + 1) * w // tw)) for tx in range(tw)]
    out = []
    for ty in range(th):
        y0, y1 = ty * h // th, max(ty * h // th + 1, (ty + 1) * h // th)
        sums = [0] * w
        for y in range(y0, y1):
            row = alpha[y]
            for x in range(w):
                sums[x] += row[x]
        n = y1 - y0
        out.append([sum(sums[a:b]) // ((b - a) * n) for a, b in xs])
    return tw, th, out


def probe_alpha(path):
    """Alpha grid of the picture at STANDIN_PROBE_PX on its long side: one Python reader on every machine (no image
    tool), so the generated verdicts never depend on what is installed (16:28 gate review)."""
    w, h, alpha = read_png_rgba(path)
    return shrink_alpha(w, h, alpha)


def file_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_verdict_cache():
    try:
        with open(os.path.join(ROOT, VERDICT_CACHE), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return data.get("verdicts", {}) if data.get("reader") == READER_VERSION else {}


_CACHE = None


def standin_verdict_alpha(w, h, alpha, full_frame=False, cols=1, rows=1):
    """"ok", "unkeyed" or "framed" for a stand-in alpha grid; a sheet is judged on its first cell. Pure."""
    if full_frame or not w or not h:
        return "ok"
    w, h = max(1, w // max(1, cols)), max(1, h // max(1, rows))
    alpha = [row[:w] for row in alpha[:h]]
    clear = sum(1 for row in alpha for a in row if a < STANDIN_CLEAR_ALPHA)
    if clear < STANDIN_MIN_CLEAR * w * h:
        return "unkeyed"
    bx, by = max(2, int(round(w * STANDIN_FRAME_BAND))), max(2, int(round(h * STANDIN_FRAME_BAND)))
    opaque = lambda x, y: alpha[y][x] >= 128  # noqa: E731
    sides = [
        sum(1 for x in range(w) if any(opaque(x, y) for y in range(by))) / w,
        sum(1 for x in range(w) if any(opaque(x, y) for y in range(h - by, h))) / w,
        sum(1 for y in range(h) if any(opaque(x, y) for x in range(bx))) / h,
        sum(1 for y in range(h) if any(opaque(x, y) for x in range(w - bx, w))) / h,
    ]
    return "framed" if sum(1 for c in sides if c >= STANDIN_FRAME_COVER) >= STANDIN_FRAME_SIDES else "ok"


def standin_picture(visual):
    """Repo path of the picture imported as the visual's _PH, or None."""
    try:
        with open(os.path.join(ROOT, STANDINS), encoding="utf-8") as fh:
            rec = json.load(fh).get("slots", {}).get(visual)
    except (OSError, ValueError):
        rec = None
    if isinstance(rec, dict) and rec.get("copy"):
        return rec["copy"]
    kind, _, rest = visual.partition(":")
    if kind == "vfx-sheet":
        raw = os.path.join(VFX_RAW, rest + "_PH.png")
        if os.path.exists(os.path.join(ROOT, raw)):
            return raw
    return None


_VERDICTS = {}


def standin_verdict(visual):
    """Verdict for the visual's stand-in picture ("ok" when there is none to judge)."""
    if visual not in _VERDICTS:
        pic = standin_picture(visual)
        full = visual.partition(":")[0] in FULL_FRAME_KINDS or visual in FULL_FRAME_VISUALS
        if not pic or full or not os.path.exists(os.path.join(ROOT, pic)):
            _VERDICTS[visual] = "ok"
        else:
            d = derive(visual)
            layout = sheet_layout(pic, png_size(os.path.join(ROOT, pic))) or ((d[2], 1) if d else (1, 1))
            global _CACHE
            if _CACHE is None:
                _CACHE = load_verdict_cache()
            key = "%s:%dx%d" % (file_sha(os.path.join(ROOT, pic)), layout[0], layout[1])
            if key not in _CACHE:
                w, h, alpha = probe_alpha(os.path.join(ROOT, pic))
                _CACHE[key] = standin_verdict_alpha(w, h, alpha, cols=layout[0], rows=layout[1])
            _VERDICTS[visual] = _CACHE[key]
    return _VERDICTS[visual]


def standin_layouts():
    """visual -> (cols, rows) for every stand-in imported from a packed frame sheet (pipeline/art/standins.json)."""
    try:
        with open(os.path.join(ROOT, STANDINS), encoding="utf-8") as fh:
            slots = json.load(fh).get("slots", {})
    except (OSError, ValueError):
        return {}
    out = {}
    for visual, rec in slots.items():
        copy = rec.get("copy") if isinstance(rec, dict) else None
        layout = sheet_layout(copy, png_size(os.path.join(ROOT, copy)) if copy else None)
        if layout:
            out[visual] = layout
    return out


def consumer(visual):
    for prefix, cls in CONSUMER:
        if visual.startswith(prefix):
            return cls
    return "-"


def slot_path(visual):
    d = derive(visual)
    return "%s/%s/%s" % (GAME_ROOT, d[0], d[1]) if d else ""


def visuals():
    with open(os.path.join(ROOT, CSV), newline="", encoding="utf-8") as fh:
        return [r["visual"] for r in csv.DictReader(fh)]


def cpp_rows(vis=None):
    out = []
    sheets = standin_layouts()
    for v in (vis if vis is not None else visuals()):
        d = derive(v)
        if v in NO_SLOT:
            continue
        if not d:
            raise SystemExit("FAIL art_slots: no slot rule for %s" % v)
        if d[2] == 1:
            # A one-picture slot whose stand-in is a packed sheet draws one cell of it (standins.json layout).
            cols, rows = sheets.get(v, (1, 1))
        else:
            # The slot names its own column count (a VFX or flipbook strip): one row.
            cols, rows = d[2], 1
        ok = standin_verdict(v) == "ok"
        out.append('\t{ TEXT("%s"), TEXT("%s"), TEXT("%s"), %d, %s, TEXT("%s"), %d, %s },'
                   % (v, d[0], d[1], cols, "true" if d[3] else "false", consumer(v), rows, "true" if ok else "false"))
    return "// Generated by tools/build/art_slots.py cpp from docs/build/art-inventory.csv: do not edit by hand.\n" + \
        "\n".join(out) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "check"
    if cmd == "cpp":
        sys.stdout.write(cpp_rows())
        return 0
    if cmd == "standins":
        for v in visuals():
            if v not in NO_SLOT and standin_picture(v):
                print("%-36s %-8s %s" % (v, standin_verdict(v), standin_picture(v)))
        return 0
    if cmd == "verdicts":
        # Measure every stand-in with the one reader and store the results by picture hash (commit the file).
        global _CACHE
        _CACHE = {}
        for v in visuals():
            if v not in NO_SLOT:
                standin_verdict(v)
        with open(os.path.join(ROOT, VERDICT_CACHE), "w", encoding="utf-8") as fh:
            json.dump({"reader": READER_VERSION, "verdicts": dict(sorted(_CACHE.items()))}, fh, indent=1)
            fh.write("\n")
        print("art_slots: %d stand-in verdicts -> %s" % (len(_CACHE), VERDICT_CACHE))
        return 0
    if cmd == "list":
        for v in visuals():
            print("%s -> %s (%s)" % (v, slot_path(v), consumer(v)))
        return 0
    want = cpp_rows()
    try:
        with open(os.path.join(ROOT, INC), encoding="utf-8") as fh:
            have = fh.read()
    except OSError:
        have = ""
    if have != want:
        print("FAIL art_slots: %s is out of date: python3 tools/build/art_slots.py cpp > %s" % (INC, INC))
        return 1
    names = [slot_path(v) for v in visuals() if v not in NO_SLOT]
    if len(set(names)) != len(names):
        dup = sorted({n for n in names if names.count(n) > 1})
        print("FAIL art_slots: two visuals share a slot: %s" % ", ".join(dup))
        return 1
    print("art_slots: PASS (%d slots)" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())

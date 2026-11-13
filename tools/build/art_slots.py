#!/usr/bin/env python3
"""Art slots: the asset name every shipped visual is drawn from (Josh, Nov 12). Stdlib only.

  art_slots.py cpp        print the catalogue rows for Source/.../Feedback/Art/ArtSlotCatalog.inc
  art_slots.py check      FAIL if ArtSlotCatalog.inc differs from what this file derives from docs/build/art-inventory.csv
  art_slots.py list       print visual -> slot -> drawn_by

A slot is /Game/UmbrellaElla/Art/<Folder>/<Asset> (Asset carries its prefix, T_ for a texture). The game loads the passed
asset <Asset> first and the tracked placeholder <Asset>_PH second, and draws the stand-in only when neither exists.
An art lane imports a candidate into <Asset>_PH with tools/build/assets/import_art_candidate.py.
"""
import csv
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INC = os.path.join("Source", "UmbrellaElla", "Private", "Feedback", "Art", "ArtSlotCatalog.inc")
CSV = os.path.join("docs", "build", "art-inventory.csv")
GAME_ROOT = "/Game/UmbrellaElla/Art"
VFX_COLS = 8

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
         "world:solids": "WorldSolids"}
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
            ("shot:stream-beam", "UShotPresenterSubsystem")]


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
    for v in (vis if vis is not None else visuals()):
        d = derive(v)
        if v in NO_SLOT:
            continue
        if not d:
            raise SystemExit("FAIL art_slots: no slot rule for %s" % v)
        out.append('\t{ TEXT("%s"), TEXT("%s"), TEXT("%s"), %d, %s, TEXT("%s") },'
                   % (v, d[0], d[1], d[2], "true" if d[3] else "false", consumer(v)))
    return "// Generated by tools/build/art_slots.py cpp from docs/build/art-inventory.csv: do not edit by hand.\n" + \
        "\n".join(out) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "check"
    if cmd == "cpp":
        sys.stdout.write(cpp_rows())
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

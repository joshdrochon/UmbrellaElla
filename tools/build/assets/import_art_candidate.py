#!/usr/bin/env python3
"""Import a candidate picture into its art slot so the game draws it (for an art lane's in-engine context capture).

  python3 tools/build/assets/import_art_candidate.py <png> <slot>
      <slot> = a visual id from docs/build/art-inventory.csv ("bg-layer:FarLand") or a slot path
      ("/Game/UmbrellaElla/Art/Scene/T_Skyline"). The slot column of that csv says which name each piece imports under.
  Lands as <slot>_PH: the game loads the passed <slot> first, then the _PH, and draws the stand-in only if neither exists.
  It stays a tracked _PH until the piece passes its art loop (worker-rules quality bars); never import under the passed name here.

Plain python re-launches itself in the editor through the slot lock:
  UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/import_art_candidate.py -unattended -nullrhi -nosplash -nocrashreports
with UMB_ART_PNG / UMB_ART_SLOT in the environment. Then run the context capture:
  tools/build/run_game.sh -SmokeShot=Saved/Logs/pipeline/<piece>-shot.png -SmokeQuitAfter=15
Texture settings follow pipeline/art/import-rules.md (UI group, no mips, sRGB, never stream, clamp; wrap for tiled paper).
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAME_ROOT = "/Game/UmbrellaElla/Art"
CSV = os.path.join(ROOT, "docs", "build", "art-inventory.csv")
PLACEHOLDER = "_PH"


def resolve(slot):
    """(destination folder, asset name incl. _PH, tiled) for a visual id or slot path."""
    tiled = False
    if slot.startswith("/Game/"):
        path = slot[: -len(PLACEHOLDER)] if slot.endswith(PLACEHOLDER) else slot
        with open(CSV, newline="", encoding="utf-8") as fh:
            tiled = any(r["slot"] == path and r["visual"] == "bg-layer:Sky" for r in csv.DictReader(fh))
    else:
        with open(CSV, newline="", encoding="utf-8") as fh:
            rows = {r["visual"]: r for r in csv.DictReader(fh)}
        if slot not in rows:
            raise SystemExit("import_art_candidate: no visual %r in docs/build/art-inventory.csv" % slot)
        path = rows[slot]["slot"]
        tiled = slot == "bg-layer:Sky"
    if not path.startswith(GAME_ROOT + "/") or path.count("/") != GAME_ROOT.count("/") + 2:
        raise SystemExit("import_art_candidate: %r is not a slot under %s/<Folder>/<Asset>" % (path, GAME_ROOT))
    folder, asset = path.rsplit("/", 1)
    if not asset.startswith("T_"):
        raise SystemExit("import_art_candidate: %s is not a texture slot (T_ prefix); vfx-material rows are materials, not images, so there is nothing to import" % path)
    return folder, asset + PLACEHOLDER, tiled


def in_editor():
    import unreal
    png = os.environ["UMB_ART_PNG"]
    folder, name, tiled = resolve(os.environ["UMB_ART_SLOT"])
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    path = "%s/%s" % (folder, name)
    tex = unreal.EditorAssetLibrary.load_asset(path)
    if not tex:
        raise RuntimeError("ART_SLOT_IMPORT failed %s" % path)
    addr = unreal.TextureAddress.TA_WRAP if tiled else unreal.TextureAddress.TA_CLAMP
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("address_x", addr)
    tex.set_editor_property("address_y", addr)
    unreal.EditorAssetLibrary.save_asset(path)
    unreal.log("ART_SLOT_IMPORT %s %dx%d" % (path, tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))


def launch(png, slot):
    if not os.path.isfile(png):
        raise SystemExit("import_art_candidate: no such file %s" % png)
    resolve(slot)   # fail on a bad slot before the editor starts
    ue = os.environ.get("UE_ROOT", "/Users/Shared/Epic Games/UE_5.8")
    exe = os.path.join(ue, "Engine", "Binaries", "Mac", "UnrealEditor-Cmd")
    cmd = [os.path.join(ROOT, "tools", "build", "ue_slot.sh"), exe, os.path.join(ROOT, "UmbrellaElla.uproject"),
           "-run=pythonscript", "-script=" + os.path.abspath(__file__), "-unattended", "-nullrhi", "-nosplash",
           "-nocrashreports"]
    env = dict(os.environ, UMB_ART_PNG=os.path.abspath(png), UMB_ART_SLOT=slot)
    return subprocess.call(cmd, env=env, cwd=ROOT)


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        if len(sys.argv) != 3:
            raise SystemExit(__doc__)
        sys.exit(launch(sys.argv[1], sys.argv[2]))
    in_editor()

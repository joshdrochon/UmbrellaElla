#!/usr/bin/env python3
"""Import several scene candidates into their _PH slots in ONE editor launch (artscene; same settings as
tools/build/assets/import_art_candidate.py, which does one picture per launch).

  python3 tools/build/assets/art_scene_import.py <png> <slot> [<png> <slot> ...]
      <slot> = a visual id from docs/build/art-inventory.csv ("bg-layer:FarLand", "world:solids").
Plain python re-launches itself in the editor through the slot lock with UMB_ART_PAIRS in the environment.
Every picture lands as <slot>_PH: a tracked placeholder until its art loop passes.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import import_art_candidate as one  # noqa: E402


def in_editor():
    for png, slot in json.loads(os.environ["UMB_ART_PAIRS"]):
        os.environ["UMB_ART_PNG"] = png
        os.environ["UMB_ART_SLOT"] = slot
        one.in_editor()


def launch(pairs):
    for png, slot in pairs:
        if not os.path.isfile(png):
            raise SystemExit("art_scene_import: no such file %s" % png)
        one.resolve(slot)
    ue = os.environ.get("UE_ROOT", "/Users/Shared/Epic Games/UE_5.8")
    exe = os.path.join(ue, "Engine", "Binaries", "Mac", "UnrealEditor-Cmd")
    cmd = [os.path.join(ROOT, "tools", "build", "ue_slot.sh"), exe, os.path.join(ROOT, "UmbrellaElla.uproject"),
           "-run=pythonscript", "-script=" + os.path.abspath(__file__), "-unattended", "-nullrhi", "-nosplash",
           "-nocrashreports"]
    env = dict(os.environ, UMB_ART_PAIRS=json.dumps([[os.path.abspath(p), s] for p, s in pairs]))
    return subprocess.call(cmd, env=env, cwd=ROOT)


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        args = sys.argv[1:]
        if not args or len(args) % 2:
            raise SystemExit(__doc__)
        sys.exit(launch(list(zip(args[0::2], args[1::2]))))
    in_editor()

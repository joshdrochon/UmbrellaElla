"""Central audio import: only the takes listed in $AUDIOIMPORT_PLAN (a JSON {"import": [repo-relative WAVs]}) become
USoundWave assets at /Game/UmbrellaElla/Audio/<Id>/SW_<Id>_NN; loop rows get the looping flag. Fails loudly (exit 1) on any
import error. The plan is made by tools/build/assets/audioimport_plan.py (critic pass, not a tracked placeholder).
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/audioimport_import.py -unattended -nullrhi -nosplash -nocrashreports"""
import csv
import json
import os
import sys
import unreal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEST = "/Game/UmbrellaElla/Audio"
plan = json.load(open(os.environ.get("AUDIOIMPORT_PLAN") or os.path.join(ROOT, "Saved", "audioimport_plan.json")))
with open(os.path.join(ROOT, "pipeline", "audio", "sound-list.csv"), newline="", encoding="utf-8") as fh:
    kinds = {r["id"]: r["kind"] for r in csv.DictReader(fh)}
tasks, names = [], []
for rel in plan["import"]:
    sid = rel.split("/")[2]
    name = os.path.basename(rel)[:-4]
    t = unreal.AssetImportTask()
    t.filename = os.path.join(ROOT, rel)
    t.destination_path = "%s/%s" % (DEST, sid)
    t.destination_name = name
    t.replace_existing = True
    t.automated = True
    t.save = True
    tasks.append(t)
    names.append(("%s/%s/%s" % (DEST, sid, name), kinds.get(sid) == "loop"))
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
bad = []
for path, loop in names:
    wave = unreal.EditorAssetLibrary.load_asset(path)
    if not wave:
        bad.append(path)
        continue
    if loop:
        wave.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.save_loaded_asset(wave)
unreal.log("audioimport_import: %d imported, %d failed" % (len(names) - len(bad), len(bad)))
for p in bad:
    unreal.log_error("audioimport_import FAILED: %s" % p)
if bad:
    sys.exit(1)

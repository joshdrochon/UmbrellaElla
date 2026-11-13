"""Import every sndlaunch take as /Game/UmbrellaElla/Audio/<Id>/SW_<Id>_<NN> (rebuildable).
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=Audio/Source/sndlaunch_import.py -unattended -nullrhi -nosplash -nocrashreports"""
import glob
import os
import unreal

IDS = ["StreamStart", "StreamLoop", "StreamRelease", "TwinStarsFire", "NeedleFire", "KeeperYellowLaunch", "GustRelease",
       "TalonSlash", "FrontCastLaunch", "MiddleCastLaunch", "RearCastLaunch", "ClockBeatRepeat", "WardenShot",
       "FloodShot", "CourierShot", "BellowsGust"]
LOOPS = {"StreamLoop"}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
tasks, waves = [], []
for sid in IDS:
    for src in sorted(glob.glob(os.path.join(ROOT, "Audio", "Source", sid, "SW_%s_[0-9][0-9].wav" % sid))):
        name = os.path.splitext(os.path.basename(src))[0]
        t = unreal.AssetImportTask()
        t.filename = src
        t.destination_path = "/Game/UmbrellaElla/Audio/%s" % sid
        t.destination_name = name
        t.replace_existing = True
        t.automated = True
        t.save = True
        tasks.append(t)
        waves.append((sid, t.destination_path + "/" + name))
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for sid, path in waves:
    if sid in LOOPS:
        w = unreal.EditorAssetLibrary.load_asset(path)
        if w:
            w.set_editor_property("looping", True)
            unreal.EditorAssetLibrary.save_loaded_asset(w)
unreal.log("sndlaunch_import done: %d takes" % len(tasks))

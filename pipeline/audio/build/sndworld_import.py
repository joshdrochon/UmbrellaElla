"""Import the sndworld sounds into /Game/UmbrellaElla/Audio/<Id>/ (editor python; loops set looping).
Run: UnrealEditor-Cmd <uproject> -run=pythonscript -script=pipeline/audio/build/sndworld_import.py -unattended -nullrhi -nosplash -nocrashreports"""
import os
import unreal

SNDWORLD_IDS = {
    "WindZoneLoop": True, "GustLoop": True, "ClockTickLoop": True, "AirMillLoop": True, "RefugeLoop": True,
    "MusicIntro": True, "MusicContest": True, "MusicDesperation": True, "WindBed": True,
    "MillAmbience": True, "BossApproach": True, "RealmClocks": True,
}
SNDWORLD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
tasks = []
for sid in SNDWORLD_IDS:
    src = os.path.join(SNDWORLD_ROOT, "Audio", "Source", sid, "SW_%s_00.wav" % sid)
    if not os.path.isfile(src):
        unreal.log_warning("missing %s" % src)
        continue
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = "/Game/UmbrellaElla/Audio/%s" % sid
    t.destination_name = sid
    t.replace_existing = True
    t.automated = True
    t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for sid, loop in SNDWORLD_IDS.items():
    wave = unreal.EditorAssetLibrary.load_asset("/Game/UmbrellaElla/Audio/%s/%s" % (sid, sid))
    if wave and loop:
        wave.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.save_loaded_asset(wave)
unreal.log("sndworld_import done: %d sounds" % len(tasks))

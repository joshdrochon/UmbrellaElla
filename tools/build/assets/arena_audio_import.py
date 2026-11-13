"""Import the arena cue sounds as USoundWave assets (rebuildable).
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/arena_audio_import.py -unattended -nullrhi -nosplash -nocrashreports
Cue name -> source take (Audio/Source/<Id>/SW_<Id>_00.wav). Cue names match UUmbrellaCueSubsystem::CueForEvent."""
import os
import unreal

CUES = {
    "Shot": ("WandBolt", False),
    "Hit": ("HitOwl", False),
    "Absorb": ("ShieldCatch", False),
    "AbsorbFail": ("PlayerHurt", False),
    "KeeperHit": ("HitOwl", False),
    "KeeperAttack": ("OwlBoltLaunch", False),
    "StartMusic": ("MusicTitle", True),
    "EndMusic": ("EndEvent", False),
    "LevelUp": ("LevelUpClock", False),
}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEST = "/Game/UmbrellaElla/Audio"

tasks = []
for cue, (sound_id, _loop) in CUES.items():
    src = os.path.join(ROOT, "Audio", "Source", sound_id, "SW_%s_00.wav" % sound_id)
    if not os.path.isfile(src):
        unreal.log_warning("missing %s" % src)
        continue
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = DEST
    t.destination_name = cue
    t.replace_existing = True
    t.automated = True
    t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for cue, (_id, loop) in CUES.items():
    wave = unreal.EditorAssetLibrary.load_asset("%s/%s" % (DEST, cue))
    if wave and loop:
        wave.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.save_loaded_asset(wave)
unreal.log("arena_audio_import done: %d cues" % len(tasks))

# Every sound-list row with takes in Audio/Source: /Game/UmbrellaElla/Audio/<Id>/SW_<Id>_NN, the names
# UUmbrellaCueSubsystem::PlayRow loads. Loop rows get the looping flag.
import csv
with open(os.path.join(ROOT, "pipeline", "audio", "sound-list.csv"), newline="", encoding="utf-8") as fh:
    LIVE = [r for r in csv.DictReader(fh) if r["tier"] != "cut"]
take_tasks = []
take_names = []
for row in LIVE:
    folder = os.path.join(ROOT, "Audio", "Source", row["id"])
    if not os.path.isdir(folder):
        continue
    for name in sorted(os.listdir(folder)):
        if not (name.startswith("SW_%s_" % row["id"]) and name.endswith(".wav")):
            continue
        t = unreal.AssetImportTask()
        t.filename = os.path.join(folder, name)
        t.destination_path = "%s/%s" % (DEST, row["id"])
        t.destination_name = name[:-4]
        t.replace_existing = True
        t.automated = True
        t.save = True
        take_tasks.append(t)
        take_names.append(("%s/%s/%s" % (DEST, row["id"], name[:-4]), row["kind"] == "loop"))
if take_tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(take_tasks)
for path, loop in take_names:
    wave = unreal.EditorAssetLibrary.load_asset(path)
    if wave and loop:
        wave.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.save_loaded_asset(wave)
unreal.log("arena_audio_import done: %d per-sound takes" % len(take_tasks))

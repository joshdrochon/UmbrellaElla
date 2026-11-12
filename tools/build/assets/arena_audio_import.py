"""Import the arena cue sounds as USoundWave assets (rebuildable).
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/arena_audio_import.py
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

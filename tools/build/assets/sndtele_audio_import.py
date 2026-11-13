"""Import the sndtele lane's takes as USoundWave assets (rebuildable), one folder per sound id.
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/sndtele_audio_import.py -unattended -nullrhi -nosplash -nocrashreports
Same import pattern as arena_audio_import.py (which imports the arena cue names into the Audio root); this one takes
Audio/Source/<Id>/SW_<Id>_NN.wav to /Game/UmbrellaElla/Audio/<Id>/SW_<Id>_NN, sets looping from the sound list kind
and the sound class from the list class when the audio core assets (Audio/Core/SCL_*) exist."""
import csv
import glob
import os
import unreal

IDS = ("UmbrellaFlap", "EllaFallLoop", "FreeFallRush", "OwlWingLoop", "OwlBoltTravelLoop", "GustWindup", "TalonWarning",
       "CastWarning", "RearMidpointClack", "ChainTravel", "ClockBeat", "WardenWarning", "WardenMove", "FloodWarning",
       "FloodStiltMove", "CourierFlightLoop", "CourierWarning", "ShutterWarning", "BellowsWarning")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEST = "/Game/UmbrellaElla/Audio"

with open(os.path.join(ROOT, "pipeline", "audio", "sound-list.csv"), newline="", encoding="utf-8") as fh:
    ROWS = {r["id"]: r for r in csv.DictReader(fh)}

tasks, made = [], []
for sound_id in IDS:
    for src in sorted(glob.glob(os.path.join(ROOT, "Audio", "Source", sound_id, "SW_%s_[0-9][0-9].wav" % sound_id))):
        t = unreal.AssetImportTask()
        t.filename = src
        t.destination_path = "%s/%s" % (DEST, sound_id)
        t.destination_name = os.path.splitext(os.path.basename(src))[0]
        t.replace_existing = True
        t.automated = True
        t.save = True
        tasks.append(t)
        made.append((sound_id, "%s/%s" % (t.destination_path, t.destination_name)))
    if not any(m[0] == sound_id for m in made):
        unreal.log_warning("sndtele_audio_import: no take for %s" % sound_id)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

done = 0
for sound_id, path in made:
    wave = unreal.EditorAssetLibrary.load_asset(path)
    if not wave:
        unreal.log_error("sndtele_audio_import: %s did not import" % path)
        continue
    row = ROWS[sound_id]
    wave.set_editor_property("looping", row["kind"] == "loop")
    cls_path = "%s/Core/SCL_%s" % (DEST, row["class"])
    if unreal.EditorAssetLibrary.does_asset_exist(cls_path):
        wave.set_editor_property("sound_class_object", unreal.EditorAssetLibrary.load_asset(cls_path))
    unreal.EditorAssetLibrary.save_loaded_asset(wave)
    done += 1
unreal.log("sndtele_audio_import done: %d of %d takes" % (done, len(made)))

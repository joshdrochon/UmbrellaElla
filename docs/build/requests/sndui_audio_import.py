"""Import the sndui lane's UI sounds as USoundWave assets (rebuildable). Same pattern as tools/build/assets/arena_audio_import.py.
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=docs/build/requests/sndui_audio_import.py -unattended -nullrhi -nosplash -nocrashreports
Audio/Source/<Id>/SW_<Id>_00.wav -> /Game/UmbrellaElla/Audio/<Id>/SW_<Id>_00 plus the cue the game plays, SC_<Id>
(one wave player): sound class SCL_UI, concurrency SCON_UI (pipeline/audio/audio-rules.json), 2D (no attenuation). A sound with no WAV yet is skipped with a warning."""
import os
import unreal

IDS = ("SpellSelect SpellUnavailable UiMove UiSelect UiBack PauseIn PauseOut UiOpen UiClose UiSliderTick UiTransition UiBlocked "
       "SettingsSaved BindingCaptured BindingConflict TutorialPrompt TutorialStep TutorialDone TutorialSkip XpGain WeaponUnlock "
       "UpgradePurchase UpgradeRefund RunStart RunComplete StoryTextAppear StoryPageReveal StoryAdvance SceneTransition").split()
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEST = "/Game/UmbrellaElla/Audio"
lib = unreal.EditorAssetLibrary

tasks = []
for sid in IDS:
    src = os.path.join(ROOT, "Audio", "Source", sid, "SW_%s_00.wav" % sid)
    if not os.path.isfile(src):
        unreal.log_warning("sndui_audio_import: missing %s" % src)
        continue
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = "%s/%s" % (DEST, sid)
    t.destination_name = "SW_%s_00" % sid
    t.replace_existing = True
    t.automated = True
    t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
ui_class = lib.load_asset(DEST + "/Core/SCL_UI")
ui_con = lib.load_asset(DEST + "/Core/SCON_UI")
done = 0
for t in tasks:
    wave = lib.load_asset("%s/%s" % (t.destination_path, t.destination_name))
    if not wave:
        unreal.log_error("sndui_audio_import: not imported %s" % t.destination_name)
        continue
    wave.set_editor_property("sound_class_object", ui_class)
    wave.set_editor_property("concurrency_set", [ui_con])
    wave.set_editor_property("attenuation_settings", None)
    lib.save_loaded_asset(wave)
    sid = t.destination_name[3:-3]
    cue_path = "%s/SC_%s" % (t.destination_path, sid)
    if lib.does_asset_exist(cue_path):
        lib.delete_asset(cue_path)
    cue = unreal.AssetToolsHelpers.get_asset_tools().create_asset("SC_%s" % sid, t.destination_path, unreal.SoundCue,
                                                                  unreal.SoundCueFactoryNew())
    if not cue:
        unreal.log_error("sndui_audio_import: no cue for %s" % sid)
        continue
    player = unreal.new_object(unreal.SoundNodeWavePlayer, outer=cue)   # the factory's initial wave is protected in 5.8
    player.set_editor_property("sound_wave", wave)
    cue.set_editor_property("first_node", player)
    cue.set_editor_property("sound_class_object", ui_class)
    cue.set_editor_property("concurrency_set", [ui_con])
    cue.set_editor_property("attenuation_settings", None)
    cue.set_editor_property("override_attenuation", False)
    lib.save_loaded_asset(cue)
    done += 1
unreal.log("sndui_audio_import done: %d of %d sounds" % (done, len(IDS)))

"""Create the audio core assets (rebuildable): sound classes, master submix with a limiter, concurrency groups.
Run: UnrealEditor-Cmd UmbrellaElla.uproject -run=pythonscript -script=tools/build/assets/arena_audio_core.py -unattended -nullrhi -nosplash -nocrashreports
Spec: pipeline/audio/audio-rules.md section 2, numbers in pipeline/audio/audio-rules.json. Output: /Game/UmbrellaElla/Audio/Core.
SCON_Default is the project default concurrency (Config/DefaultEngine.ini [/Script/Engine.AudioSettings])."""
import json
import os
import unreal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEST = "/Game/UmbrellaElla/Audio/Core"
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary


def make(name, cls, factory):
    path = "%s/%s" % (DEST, name)
    if lib.does_asset_exist(path):
        return lib.load_asset(path)
    return tools.create_asset(name, DEST, cls, factory)


def save(a):
    lib.save_loaded_asset(a)


# --- submix: SM_Master with one dynamics processor in Limiter mode
master = make("SM_Master", unreal.SoundSubmix, unreal.SoundSubmixFactory())
fxf = unreal.SoundSubmixEffectFactory()
fxf.set_editor_property("sound_effect_submix_preset_class", unreal.SubmixEffectDynamicsProcessorPreset)
fx = make("SMFX_MasterLimiter", unreal.SubmixEffectDynamicsProcessorPreset, fxf)
st = fx.get_editor_property("settings")
st.set_editor_property("dynamics_processor_type", unreal.SubmixEffectDynamicsProcessorType.LIMITER)
fx.set_editor_property("settings", st)
master.set_editor_property("submix_effect_chain", [fx])
save(fx)
save(master)

# --- sound classes
def sclass(name, parent):
    c = make(name, unreal.SoundClass, unreal.SoundClassFactory())
    if parent is not None:
        c.set_editor_property("parent_class", parent)
    p = c.get_editor_property("properties")
    p.set_editor_property("default_submix", master)
    c.set_editor_property("properties", p)
    save(c)
    return c

sfx = sclass("SCL_SFX", None)
sclass("SCL_Telegraph", sfx)
sclass("SCL_UI", sfx)
sclass("SCL_Music", None)

# --- concurrency groups (numbers from audio-rules.json) + the project default
with open(os.path.join(ROOT, "pipeline", "audio", "audio-rules.json"), encoding="utf-8") as f:
    spec = json.load(f)["concurrency"]["assets"]
RULES = {"StopLowestPriority": unreal.MaxConcurrentResolutionRule.STOP_LOWEST_PRIORITY}
groups = dict(spec)
groups["SCON_Default"] = {"max_count": 16, "retrigger_time": 0.0, "resolution_rule": "StopLowestPriority",
                          "voice_steal_release_time": 0.03}
for name, g in groups.items():
    a = make(name, unreal.SoundConcurrency, unreal.SoundConcurrencyFactory())
    s = a.get_editor_property("concurrency")
    s.set_editor_property("limit_to_owner", False)
    # The 5.8 factory turns platform scaling on, and then MaxCount is ignored for PlatformMaxCount (16): every group
    # allowed 16 voices and a Keeper volley stacked (fix-audio). Off, so max_count is the limit.
    s.set_editor_property("enable_max_count_platform_scaling", False)
    s.set_editor_property("max_count", int(g["max_count"]))
    s.set_editor_property("resolution_rule", RULES[g["resolution_rule"]])
    s.set_editor_property("retrigger_time", float(g["retrigger_time"]))
    s.set_editor_property("voice_steal_release_time", float(g["voice_steal_release_time"]))
    s.set_editor_property("volume_scale", float(g.get("volume_scale", 1.0)))
    a.set_editor_property("concurrency", s)
    save(a)
unreal.log("arena_audio_core: done")

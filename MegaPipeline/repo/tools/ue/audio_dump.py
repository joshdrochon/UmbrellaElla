"""Editor dump of the audio setup for `tools/audio_check.py --ue-dump`.

Source: pipeline/audio/ue/audio_dump.py (audio lane). Copied byte for byte to tools/ue/audio_dump.py before the jam,
because tools/ is frozen during it. tests/test_audio_check.py fails if the two differ.
Run in the editor on the project, then check the result:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script=tools/ue/audio_dump.py   [VERIFY 5.8.4 spelling]
  python3 tools/audio_check.py --ue-dump Saved/AudioDump.json
Format: tests/fixtures/audio/ue_dump_pass.json. Every editor property name below is [VERIFY] on 5.8.4.
A property that cannot be read is never guessed: its name goes in the dump's `unread` list, and
audio_check fails while that list is not empty. So the first editor run shows which names are wrong.
"""
import json
import os
import re
import subprocess
import sys

TOOL = "tools/ue/audio_dump.py"
ROOT_PATH = "/Game/UmbrellaElla/Audio"
PLAYABLE = ("SoundCue", "MetaSoundSource", "SoundWave")


class Reader:
    """Reads editor properties and records every one it cannot read."""

    def __init__(self):
        self.unread = []

    def get(self, obj, prop, where):
        try:
            return obj.get_editor_property(prop)
        except Exception:  # unreal raises a plain Exception for an unknown property
            self.unread.append(f"{where}.{prop}")
            return None


def name_of(obj):
    return obj.get_name() if obj is not None else None


def class_of(obj):
    return obj.get_class().get_name()


def enum_name(v):
    """STOP_LOWEST_PRIORITY -> StopLowestPriority."""
    raw = getattr(v, "name", None) or str(v).split(".")[-1].split(":")[0].strip("<> ")
    return "".join(p.capitalize() for p in raw.split("_")) if raw.isupper() or "_" in raw else raw


def walk_cue(node, rd, where, seen=None):
    """Yield every node under a cue's first node."""
    seen = set() if seen is None else seen
    if node is None or id(node) in seen:
        return
    seen.add(id(node))
    yield node
    for c in rd.get(node, "child_nodes", where) or []:
        yield from walk_cue(c, rd, where, seen)


def sound_class(obj, rd, where):
    props = rd.get(obj, "properties", where)
    return {
        "name": name_of(obj),
        "parent": name_of(rd.get(obj, "parent_class", where)),
        "default_submix": name_of(rd.get(props, "default_submix", where + ".properties")) if props is not None else None,
    }


def submix(obj, rd, where):
    effects = []
    for e in rd.get(obj, "submix_effect_chain", where) or []:
        label = class_of(e)
        settings = rd.get(e, "settings", where + ".effect") if "Dynamics" in label else None
        if settings is not None:
            label += ":" + enum_name(rd.get(settings, "dynamics_processor_type", where + ".effect.settings"))
        effects.append(label)
    return {"name": name_of(obj), "parent": name_of(rd.get(obj, "parent_submix", where)), "effects": effects}


def concurrency(obj, rd, where):
    s = rd.get(obj, "concurrency", where)
    w = where + ".concurrency"
    if s is None:
        return {"name": name_of(obj)}
    return {
        "name": name_of(obj),
        "max_count": rd.get(s, "max_count", w),
        "resolution_rule": enum_name(rd.get(s, "resolution_rule", w)),
        "retrigger_time": rd.get(s, "retrigger_time", w),
        "voice_steal_release_time": rd.get(s, "voice_steal_release_time", w),
        "volume_scale": rd.get(s, "volume_scale", w),  # ducks older voices of the group as new ones start
    }


def sound(obj, rd, where):
    cls = class_of(obj)
    out = {"class": cls, "name": name_of(obj),
           "sound_class": name_of(rd.get(obj, "sound_class_object", where))}
    if cls == "SoundWave":
        out["looping"] = bool(rd.get(obj, "looping", where))
        return out
    out["priority"] = rd.get(obj, "priority", where)
    out["concurrency"] = sorted(name_of(c) for c in (rd.get(obj, "concurrency_set", where) or []))
    att = rd.get(obj, "attenuation_settings", where)
    override = bool(rd.get(obj, "override_attenuation", where))
    out["attenuation"] = name_of(att)
    out["spatialize"] = att is not None or override  # [VERIFY] no attenuation and no override = 2D
    looping = False
    if cls == "SoundCue":
        for n in walk_cue(rd.get(obj, "first_node", where), rd, where + ".node"):
            nc = class_of(n)
            if nc == "SoundNodeLooping":
                looping = True
            elif nc == "SoundNodeWavePlayer" and rd.get(n, "looping", where + ".WavePlayer"):
                looping = True
            elif nc == "SoundNodeRandom":
                out["random_takes"] = len(rd.get(n, "child_nodes", where + ".Random") or [])
                out["no_repeat"] = bool(rd.get(n, "randomize_without_replacement", where + ".Random"))
            elif nc == "SoundNodeModulator":
                out["pitch_min"] = rd.get(n, "pitch_min", where + ".Modulator")
                out["pitch_max"] = rd.get(n, "pitch_max", where + ".Modulator")
    # A MetaSoundSource graph is not read: loops and varied sounds are SoundCues (audio-rules.md section 2).
    out["looping"] = looping
    return out


def build_dump(ue, root=ROOT_PATH, commit="", engine=None):
    """Walk every asset under root. `ue` is the unreal module (a fake one in tests)."""
    rd = Reader()
    reg = ue.AssetRegistryHelpers.get_asset_registry()
    dump = {"tool": TOOL, "engine": engine or str(ue.SystemLibrary.get_engine_version()),
            "commit": commit, "root": root, "sound_classes": [], "submixes": [], "concurrency": [],
            "assets": [], "unread": rd.unread}
    for ad in sorted(reg.get_assets_by_path(root, recursive=True), key=lambda a: str(a.get_asset().get_name())):
        obj = ad.get_asset()
        cls, where = class_of(obj), name_of(obj)
        if cls == "SoundClass":
            dump["sound_classes"].append(sound_class(obj, rd, where))
        elif cls == "SoundSubmix":
            dump["submixes"].append(submix(obj, rd, where))
        elif cls == "SoundConcurrency":
            dump["concurrency"].append(concurrency(obj, rd, where))
        elif cls in PLAYABLE:
            dump["assets"].append(sound(obj, rd, where))
    m = re.match(r"\d+\.\d+\.\d+", dump["engine"])
    dump["engine"] = m.group(0) if m else dump["engine"]
    return dump


def git_commit(cwd):
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=cwd, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main():
    import unreal  # only inside the editor
    proj = unreal.Paths.project_dir()
    dump = build_dump(unreal, commit=git_commit(proj))
    out = os.path.join(unreal.Paths.project_saved_dir(), "AudioDump.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=1)
    unreal.log(f"audio_dump: wrote {out} assets={len(dump['assets'])} unread={len(dump['unread'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate the sound -> bus event cue table the cue subsystem plays from.
  cue_table.py write   rewrite Feedback/Audio/UmbrellaCueTable.cpp from sound-list.csv, audio-rules.json and ROUTES
  cue_table.py check   exit 1 when the committed file is not what `write` would produce (tests/test_audio_cue_table.py)
One row per route; a sound with no bus event yet is a Direct row (Event Count) played by name through
UUmbrellaCueSubsystem::PlaySoundById. Every sound-list row that is not cut has at least one row."""
import csv, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "Source", "UmbrellaElla", "Public", "Feedback", "Audio", "UmbrellaCueData.h")
CLASS_ENUM = {"SFX": "SFX", "Telegraph": "Telegraph", "Music": "Music", "UI": "UI"}
MECH = ["MECH_FRONT", "MECH_MIDDLE", "MECH_REAR"]

# id -> [(event, match, value)]; match is Any, Detail, Target or LeftDetail. Details are what the emitters write
# (UmbrellaActionRules::ActionName, shot kind, Health "Damage"/"Heal", Keeper part names, attack ids).
ROUTES = {
    "UmbrellaOpen": [("UmbrellaConfigChanged", "Detail", "Rise")],
    "UmbrellaClose": [("UmbrellaConfigChanged", "Detail", "ShootFall")],
    "UmbrellaFlap": [("UmbrellaConfigChanged", "Detail", "Rise")],
    "EllaFallLoop": [("UmbrellaConfigChanged", "Detail", "ShootFall"), ("UmbrellaConfigChanged", "Detail", "AbsorbFall")],
    "FreeFallRush": [("UmbrellaConfigChanged", "Detail", "FreeFall")],
    "AbsorbStart": [("UmbrellaConfigChanged", "Detail", "AbsorbFall")],
    "AbsorbLoop": [("UmbrellaConfigChanged", "Detail", "AbsorbFall")],
    "AbsorbStop": [("UmbrellaConfigChanged", "LeftDetail", "AbsorbFall")],
    "GustCatch": [("WindEntered", "Any", "")],
    "WindZoneLoop": [("WindEntered", "Any", "")],
    "WindExit": [("WindExited", "Any", "")],
    "ShieldCatch": [("CatchSucceeded", "Any", "")],
    "ShieldHeal": [("PlayerHealthChanged", "Detail", "Heal")],
    "PlayerHurt": [("PlayerHealthChanged", "Detail", "Damage")],
    "LifeLost": [("LifeLost", "Any", "")],
    "EllaDown": [("PlayerDefeated", "Any", "")],
    "FailSting": [("PlayerDefeated", "Any", "")],
    "Restart": [("CheckpointRetried", "Any", "")],
    "CheckpointReached": [("CheckpointReached", "Any", "")],
    "WandBolt": [("ProjectileSpawned", "Detail", "PlayerBlast")],
    "OwlBoltLaunch": [("ProjectileSpawned", "Detail", "EnemyRed")],
    "KeeperYellowLaunch": [("ProjectileSpawned", "Detail", "EnemyYellow")],
    "SmallBlastImpact": [("ProjectileContact", "Detail", "Consumed")],
    "WandBoltFade": [("ProjectileContact", "Detail", "Passed")],
    "HitOwl": [("BossTargetHit", "Target", m) for m in MECH],
    "HitWing": [("BossTargetHit", "Target", "WINGS")],
    "HitClock": [("BossTargetHit", "Target", "CLOCK")],
    "EyeHit": [("BossTargetHit", "Target", "EYE")],
    "HitEnemy": [("BossTargetHit", "Detail", "Enemy")],
    "WingsBreak": [("BossPartDestroyed", "Target", "WINGS")],
    "MechanismBreak": [("BossPartDestroyed", "Target", m) for m in MECH],
    "GustWindup": [("BossAttackTelegraphed", "Detail", "GUST_Band")],
    "TalonWarning": [("BossAttackTelegraphed", "Detail", "TALON_Rake")],
    "CastWarning": [("BossAttackTelegraphed", "Detail", d) for d in ("MECH_Front_Cast", "MECH_Middle_Curve", "MECH_Rear_TwoStage")],
    "ClockBeat": [("BossAttackTelegraphed", "Detail", "CLOCK_DoubleBeat")],
    "PhaseChime": [("PhaseStarted", "Any", "")],
    "EndEvent": [("EncounterCompleted", "Any", "")],
    "SurvivedSting": [("EncounterCompleted", "Any", "")],
    "XpGain": [("XPAwarded", "Any", "")],
    "LevelUpClock": [("LevelGained", "Any", "")],
    "RunComplete": [("RunCompleted", "Any", "")],
    "UiSelect": [("ModeSelected", "Any", "")],
    "MusicTitle": [("ModeSelected", "Any", "")],
}
# Loops that replace each other: starting one stops the others of its group; the stop event ends the group.
LOOP_GROUP = {"UmbrellaFlap": "move", "EllaFallLoop": "move", "FreeFallRush": "move", "AbsorbLoop": "move",
              "WindZoneLoop": "wind"}
GROUP_STOPS = [("wind", "WindExited")]


def rows():
    with open(os.path.join(ROOT, "pipeline", "audio", "sound-list.csv"), newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["tier"] != "cut"]


def render():
    rules = json.load(open(os.path.join(ROOT, "pipeline", "audio", "audio-rules.json"), encoding="utf-8"))
    cc = rules["concurrency"]
    unknown = sorted(set(ROUTES) - {r["id"] for r in rows()})
    if unknown:
        raise SystemExit("ROUTES names ids that are not live sound-list rows: %s" % unknown)
    lines = []
    for r in rows():
        con = cc["by_id"].get(r["id"]) or cc["by_family"].get(r["family"]) or ""
        loop = "true" if r["kind"] == "loop" else "false"
        group = LOOP_GROUP.get(r["id"], "")
        for ev, match, value in ROUTES.get(r["id"]) or [("Count", "Any", "")]:
            lines.append('\t{TEXT("%s"), EUmbrellaEventType::%s, EUmbrellaCueMatch::%s, TEXT("%s"), EUmbrellaCueClass::%s, '
                         'TEXT("%s"), %s, %s, %sf, TEXT("%s")},' % (r["id"], ev, match, value, CLASS_ENUM[r["class"]],
                                                                  con, loop, r["takes"], "%.2f" % float(r["pitch_jitter"]), group))
    stops = ["\t{TEXT(\"%s\"), EUmbrellaEventType::%s}," % s for s in GROUP_STOPS]
    return ('// Generated by pipeline/audio/build/cue_table.py from pipeline/audio/sound-list.csv; do not edit by hand.\n'
            '// Included once, by UmbrellaCueRules.cpp.\n#pragma once\n\n'
            '#include "Feedback/Audio/UmbrellaCueTable.h"\n\n'
            'namespace UmbrellaCueData\n{\n'
            'inline const TArray<FUmbrellaSoundCue>& Rows()\n{\n'
            '\tstatic const TArray<FUmbrellaSoundCue> Table = {\n%s\n\t};\n\treturn Table;\n}\n\n'
            'inline const TArray<FUmbrellaLoopGroupStop>& Stops()\n{\n'
            '\tstatic const TArray<FUmbrellaLoopGroupStop> Stops = {\n%s\n\t};\n\treturn Stops;\n}\n}\n'
            % ("\n".join("\t" + l for l in lines), "\n".join("\t" + s for s in stops)))


def main(argv):
    text = render()
    if argv[:1] == ["check"]:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur != text:
            print("UmbrellaCueData.h is out of date: run pipeline/audio/build/cue_table.py write")
            return 1
        return 0
    if argv[:1] == ["write"]:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

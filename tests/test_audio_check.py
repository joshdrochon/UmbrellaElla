"""Tests for tools/audio_check.py. WAVs are LFS-only in this repo and CI checks out without LFS, so the
WAV fixtures are written to a temp folder by make_wav() below. The dump and log fixtures are text in
tests/fixtures/audio/. Each passing input is broken on purpose in one way and must fail on that rule."""
import copy
import csv
import io
import json
import math
import os
import re
import struct
import sys
import tempfile
import unittest
import wave
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_check  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "audio")
RULES = audio_check.load_rules()
# The list rules are checked on the frozen GDD 1.3 sound list (the ids these tests break on purpose); the GDD SH1.0
# list is checked by test_repo_list_passes_stolen_hour below and by tests/test_audio_events.py.
L13 = os.path.join(ROOT, "tests", "fixtures", "gdd13")
L13_LIST = os.path.join(L13, "pipeline", "audio", "sound-list.csv")
ROWS = audio_check.load_list(L13_LIST)
L13_MAP = audio_check.load_json_file(os.path.join(L13, "pipeline", "audio", "sound-events.json"))
LIVE_ROWS = audio_check.load_list()   # the GDD SH1.0 sound list
PROV_HEAD = "asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution\n"


def make_wav(path, rate=48000, bits=16, channels=1, dur=0.3, amp=0.5, lead_ms=0.0, freq=440.0, phase=0.0,
             fade_ms=5.0, tail_ms=6.0):
    """A sine burst. A whole number of cycles over dur makes a clean loop; phase != 0 makes a click.
    One-shots end with a fade_ms fade and tail_ms of silence; loops pass fade_ms=0, tail_ms=0."""
    n = int(rate * dur)
    lead = int(rate * lead_ms / 1000)
    fade = int(rate * fade_ms / 1000)
    full = (1 << (bits - 1)) - 1
    frames = bytearray()
    for k in range(n + int(rate * tail_ms / 1000)):
        v = 0.0 if k < lead or k >= n else amp * math.sin(2 * math.pi * freq * (k - lead) / rate + phase)
        if fade and n - fade <= k < n:
            v *= (n - k) / fade
        s = int(round(v * full))
        b = struct.pack("<h", s) if bits == 16 else s.to_bytes(3, "little", signed=True)
        frames += b * channels
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(bits // 8)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


LOOP = {"fade_ms": 0, "tail_ms": 0}
GOOD = {  # file -> make_wav kwargs; covers every P0 row; each family sits within 3 dB of its median
    "SW_WandBolt_00.wav": {}, "SW_WandBolt_01.wav": {"freq": 500}, "SW_WandBolt_02.wav": {"freq": 560},
    "SW_OwlBoltLaunch_00.wav": {"amp": 0.45},
    "SW_HitOwl_00.wav": {}, "SW_HitOwl_01.wav": {"freq": 330}, "SW_HitOwl_02.wav": {"freq": 300},
    "SW_PlayerHurt_00.wav": {"amp": 0.55, "bits": 24},
    "SW_GustLoop_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 200, "amp": 0.3},
    "SW_OwlBoltWindup_00.wav": {"freq": 700},
    "SW_UmbrellaOpen_00.wav": {"freq": 260}, "SW_UmbrellaClose_00.wav": {"freq": 280},
    "SW_EndEvent_00.wav": {"channels": 2, "freq": 220},
    "SW_ShieldCatch_00.wav": {"freq": 310}, "SW_ShieldHeal_00.wav": {"freq": 340}, "SW_GustCatch_00.wav": {"freq": 290},
}
P1_FILES = {"SW_GustWindup_00.wav": {"freq": 650}, "SW_PhaseChime_00.wav": {"channels": 2, "freq": 300},
            "SW_FailSting_00.wav": {"channels": 2, "freq": 350},
            "SW_LowHealthLoop_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 210},
            "SW_UmbrellaCreak_00.wav": {"dur": 0.5, **LOOP, "freq": 230}, "SW_UmbrellaTear_00.wav": {"freq": 240},
            "SW_SurvivedSting_00.wav": {"channels": 2, "freq": 330}, "SW_UiSelect_00.wav": {"freq": 900},
            "SW_HitClock_00.wav": {"freq": 360}, "SW_HitWing_00.wav": {"freq": 380},
            "SW_MusicIntro_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 200, "amp": 0.3},
            "SW_MusicContest_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 220, "amp": 0.3},
            "SW_MusicDesperation_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 240, "amp": 0.3}}
# Coverage rows (pipeline/audio/sound-events.json): every P1 sound the game plays, so --release needs them too
AMB = {"dur": 0.5, **LOOP, "amp": 0.3}
P1_FILES.update({
    **{f"SW_{i}_00.wav": {"freq": 800 + 20 * k} for k, i in enumerate(
        ("UiMove", "UiBack", "UiOpen", "UiClose", "UiSliderTick"))},
    **{f"SW_{i}_00.wav": {"channels": 2, "freq": 900 + 20 * k} for k, i in enumerate(("UiTransition", "PauseIn", "PauseOut"))},
    "SW_MusicTitle_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 260, "amp": 0.3},
    "SW_EncounterStart_00.wav": {"channels": 2, "freq": 230}, "SW_Restart_00.wav": {"channels": 2, "freq": 250},
    "SW_EllaDown_00.wav": {"freq": 270},
    "SW_WindBed_00.wav": {**AMB, "channels": 2, "freq": 180}, "SW_WindZoneLoop_00.wav": {**AMB, "channels": 2, "freq": 190},
    "SW_ClockTickLoop_00.wav": {**AMB, "freq": 210}, "SW_BelfryAmbience_00.wav": {**AMB, "channels": 2, "freq": 170},
    "SW_WindExit_00.wav": {"freq": 300}, "SW_GustEnd_00.wav": {"freq": 320}, "SW_ShieldRaise_00.wav": {"freq": 330},
    "SW_EllaBump_00.wav": {"freq": 350},
    **{f"SW_{i}_00.wav": {"dur": 0.5, **LOOP, "freq": 400 + 20 * k} for k, i in enumerate(
        ("UmbrellaFlap", "EllaFallLoop", "OwlBoltTravelLoop"))},
    "SW_OwlWingLoop_00.wav": {"channels": 2, "dur": 0.5, **LOOP, "freq": 460},
    "SW_OwlBoltFade_00.wav": {"freq": 600}, "SW_WandBoltFade_00.wav": {"freq": 620},
})


class WavScan(unittest.TestCase):
    def build(self, files=GOOD, prov_skip=()):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        src = os.path.join(root, "Audio", "Source")
        lines = []
        for name, kw in files.items():
            sid = name.split("_")[1]
            d = os.path.join(src, sid)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name)
            if kw == "lfs":
                with open(p, "wb") as f:
                    f.write(b"version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 10\n")
            else:
                make_wav(p, **kw)
            if name not in prov_skip:
                lines.append(f"Audio/Source/{sid}/{name},Rick,hand-made,Audacity,,,,,2026-11-12,CC0,\n")
        prov = os.path.join(root, "prov.csv")
        with open(prov, "w") as f:
            f.write(PROV_HEAD + "".join(lines))
        return src, prov, root

    def run_scan(self, files=GOOD, prov_skip=(), fail_lfs=False, release=False):
        src, prov, root = self.build(files, prov_skip)
        return audio_check.scan(src, RULES, ROWS, prov, root=root, fail_lfs_pointer=fail_lfs, release=release)

    def broken(self, name, kw):
        files = dict(GOOD)
        files[name] = kw
        return self.run_scan(files)[0]

    def test_good_set_passes(self):
        problems, skipped, measured = self.run_scan()
        self.assertEqual(problems, [])
        self.assertEqual(len(measured), len(GOOD))

    def test_peak_over_minus_1_dbfs_fails(self):
        p = self.broken("SW_HitOwl_00.wav", {"amp": 0.99})
        self.assertTrue(any("peak" in x for x in p), p)

    def test_sample_rate_fails(self):
        p = self.broken("SW_HitOwl_00.wav", {"rate": 22050})
        self.assertTrue(any("22050 Hz" in x for x in p), p)

    def test_channels_must_match_list(self):
        p = self.broken("SW_HitOwl_00.wav", {"channels": 2})
        self.assertTrue(any("channel" in x for x in p), p)

    def test_leading_silence_fails_on_one_shot(self):
        p = self.broken("SW_HitOwl_00.wav", {"lead_ms": 40})
        self.assertTrue(any("silence before" in x for x in p), p)

    def test_one_shot_click_at_the_end_fails(self):
        p = self.broken("SW_HitOwl_00.wav", {"fade_ms": 0, "tail_ms": 0})  # stops at full level
        self.assertTrue(any("SW_HitOwl_00.wav: click at the end" in x for x in p), p)
        p = self.broken("SW_GustLoop_00.wav", {"channels": 2, "dur": 0.5, "freq": 200, "amp": 0.3, **LOOP})
        self.assertFalse(any("click at the end" in x for x in p), p)  # loops are checked at the wrap, not the tail

    def test_loop_click_fails(self):
        p = self.broken("SW_GustLoop_00.wav", {"channels": 2, "dur": 0.5, **LOOP, "freq": 200.5, "amp": 0.3})
        self.assertTrue(any("click at the loop point" in x for x in p), p)

    def test_family_rms_mismatch_fails(self):
        p = self.broken("SW_HitOwl_02.wav", {"amp": 0.1})
        self.assertTrue(any("SW_HitOwl_02" in x and "median" in x for x in p), p)

    def test_too_few_takes_fails(self):
        files = dict(GOOD)
        del files["SW_WandBolt_02.wav"]
        p = self.run_scan(files)[0]
        self.assertTrue(any("WandBolt: 2 take" in x for x in p), p)

    def test_empty_folder_fails(self):
        p = self.run_scan(files={})[0]
        self.assertTrue(any("WandBolt: P0 sound has no file" in x for x in p), p)
        self.assertEqual(sum("P0 sound has no file" in x for x in p), sum(r["tier"] == "P0" for r in ROWS))

    def test_missing_p0_sound_fails(self):
        files = dict(GOOD)
        del files["SW_UmbrellaClose_00.wav"]
        p = self.run_scan(files)[0]
        self.assertEqual(p, ["UmbrellaClose: P0 sound has no file in the folder (want SW_UmbrellaClose_00.wav)"])

    def test_release_needs_p1_files(self):
        p = self.run_scan(release=True)[0]
        self.assertTrue(any("GustWindup: P1 sound has no file" in x for x in p), p)
        self.assertFalse(any("ArcWindup" in x for x in p), p)  # P2 is never required
        self.assertEqual(self.run_scan(files={**GOOD, **P1_FILES}, release=True)[0], [])

    def test_missing_provenance_fails(self):
        p = self.run_scan(prov_skip=("SW_WandBolt_01.wav",))[0]
        self.assertTrue(any("no provenance row" in x for x in p), p)

    def test_two_provenance_rows_for_one_take_fail(self):
        src, prov, root = self.build()
        with open(prov, "a") as f:
            f.write("Audio/Source/WandBolt/SW_WandBolt_00.wav,Rick,placeholder: audio critic fail (x),Audacity,,,,,"
                    "2026-11-12,CC0,\n")
        p = audio_check.scan(src, RULES, ROWS, prov, root=root)[0]
        self.assertTrue(any("SW_WandBolt_00.wav: 2 provenance rows" in x for x in p), p)

    def test_repo_ledger_has_one_row_per_take(self):
        self.assertEqual(audio_check.duplicate_provenance(audio_check.DEFAULT_PROV), [])

    # Provenance matches the critic (pipeline/audio/critic/<Id>.json holds the verdicts, keyed by the takes' hash).
    def critic_case(self, verdict, origin, style_pass=True, stale=False, later=None):
        src, prov, root = self.build()
        d = os.path.join(src, "WandBolt")
        h = audio_check.takes_hash([os.path.join(d, f) for f in os.listdir(d)])
        recs = [{"files": "0" * 64 if stale else h, "verdict": verdict, "style_pass": style_pass, "card": "T-1",
                 "round": 1, "at": "2026-11-13T01:00Z"}]
        if later:
            recs.append({"files": h, "verdict": later, "style_pass": True, "card": "GATE", "round": 1,
                         "at": "2026-11-13T02:00Z"})
        os.makedirs(os.path.join(root, audio_check.CRITIC_DIR))
        with open(os.path.join(root, audio_check.CRITIC_DIR, "WandBolt.json"), "w") as f:
            json.dump({"id": "WandBolt", "records": recs}, f)
        with open(prov) as f:
            text = f.read()
        with open(prov, "w") as f:
            f.write(re.sub(r"(SW_WandBolt_\d\d\.wav,Rick,)hand-made", lambda m: m.group(1) + origin, text))
        p = audio_check.scan(src, RULES, ROWS, prov, root=root)[0]
        return [x for x in p if "blind critic" in x]

    def test_passed_take_marked_placeholder_fails(self):
        p = self.critic_case("pass", "placeholder: audio critic fail (x)")
        self.assertEqual(len(p), 3, p)
        self.assertTrue(all("marked placeholder, but the blind critic passed these bytes" in x for x in p), p)

    def test_passed_take_with_generated_origin_passes(self):
        self.assertEqual(self.critic_case("pass", "generated in jam"), [])

    def test_placeholder_is_fine_when_the_pass_was_on_other_bytes_or_missed_the_numbers(self):
        self.assertEqual(self.critic_case("pass", "placeholder: audio critic fail (x)", stale=True), [])
        self.assertEqual(self.critic_case("pass", "placeholder: audio critic fail (x)", style_pass=False), [])

    def test_a_later_fail_on_the_same_bytes_wins(self):
        self.assertEqual(self.critic_case("pass", "placeholder: audio critic fail (x)", later="fail"), [])
        p = self.critic_case("pass", "generated in jam", later="fail")
        self.assertTrue(p and all("the blind critic failed these bytes" in x for x in p), p)

    def test_failed_take_marked_generated_fails_and_an_approved_take_is_left_alone(self):
        self.assertEqual(len(self.critic_case("fail", "generated in jam")), 3)
        self.assertEqual(self.critic_case("fail", "generated in jam; approved by Josh (listened) 2026-11-12"), [])

    def test_repo_ledger_matches_the_critic_records(self):
        prov = audio_check.provenance_rows(audio_check.DEFAULT_PROV)
        takes = {}
        for rel in prov:
            full = os.path.join(ROOT, rel)
            if rel.startswith("Audio/Source/") and rel.endswith(".wav") and os.path.isfile(full):
                with open(full, "rb") as f:
                    if f.read(len(audio_check.LFS_POINTER)) != audio_check.LFS_POINTER:   # CI has no LFS bytes
                        takes.setdefault(rel.split("/")[2], []).append(rel)
        self.assertEqual(audio_check.critic_mismatch(takes, prov, ROOT), [])

    def test_loop_and_check_hash_the_takes_the_same_way(self):
        import audio_loop
        src, _, _ = self.build()
        d = os.path.join(src, "WandBolt")
        files = [os.path.join(d, f) for f in os.listdir(d)]
        self.assertEqual(audio_loop.files_hash(files), audio_check.takes_hash(files))
        self.assertEqual(len(audio_check.takes_hash(files)), 64)

    def test_bad_name_and_unknown_id_fail(self):
        files = dict(GOOD)
        files["SW_EnemyDefeat_00.wav"] = {}
        files["SW_WandBolt_final.wav"] = {}
        p = self.run_scan(files)[0]
        self.assertTrue(any("EnemyDefeat is not in" in x for x in p), p)
        self.assertTrue(any("name must be" in x for x in p), p)

    def test_lfs_pointer_skips_or_fails(self):
        files = dict(GOOD)
        files["SW_PlayerHurt_00.wav"] = "lfs"
        problems, skipped, _ = self.run_scan(files)
        self.assertEqual(problems, [])
        self.assertEqual(len(skipped), 1)
        problems, _, _ = self.run_scan(files, fail_lfs=True)
        self.assertTrue(any("LFS pointer" in x for x in problems), problems)

    def test_cli_exit_codes(self):
        src, prov, root = self.build()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(audio_check.main(["--scan", src, "--provenance", prov]), 1)  # rel paths differ from root
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audio_check.main(["--list"]), 0)
            self.assertEqual(audio_check.main(["--scan", os.path.join(root, "nope")]), 0)
            self.assertEqual(audio_check.main(["--scan", os.path.join(root, "nope"), "--require-dir"]), 1)
            empty = os.path.join(root, "empty")
            os.makedirs(empty)
            self.assertEqual(audio_check.main(["--scan", empty, "--require-dir"]), 1)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(audio_check.main([]), 2)


class SoundList(unittest.TestCase):
    def test_repo_list_passes(self):
        self.assertEqual(audio_check.check_list(ROWS, RULES), [])

    def test_repo_list_covers_the_gdd_sounds(self):
        ids = {r["id"] for r in ROWS}
        for need in ("WandBolt", "OwlBoltLaunch", "OwlBoltWindup", "GustWindup", "GustLoop", "ArcWindup", "HitOwl",
                     "PlayerHurt", "UmbrellaTear", "UmbrellaOpen", "UmbrellaClose", "EndEvent", "PhaseChime", "SurvivedSting",
                     "HitClock", "HitWing"):
            self.assertIn(need, ids)
        self.assertFalse(any("defeat" in i.lower() for i in ids))  # the owl is never killed (GDD §2)

    def test_release_fails_on_tbd_or_missing_fallback(self):
        p = audio_check.check_list(ROWS, RULES, release=True)
        self.assertEqual(sum("does not exist" in x for x in p), 14, p)  # 11 P0 rows + GustWindup + ArcWindup + PhaseChime
        rows = copy.deepcopy(ROWS)
        rows[0]["fallback"] = "TBD-0.15"
        self.assertEqual(audio_check.check_list(rows, RULES), [])  # TBD passes during the jam
        self.assertTrue(any("fallback still TBD" in x for x in audio_check.check_list(rows, RULES, release=True)))

    def test_broken_rows_fail(self):
        rows = copy.deepcopy(ROWS)
        tele = next(r for r in rows if r["class"] == "Telegraph")
        tele["pitch_jitter"] = "0.05"
        rows.append(dict(rows[0]))
        rows[1]["kind"] = "burst"
        rows[2]["owner"] = ""
        p = audio_check.check_list(rows, RULES)
        for want in ("pitch_jitter 0", "duplicate id", "kind 'burst'", "owner is empty"):
            self.assertTrue(any(want in x for x in p), (want, p))

    def test_release_fallback_rules(self):
        p = audio_check.check_list(ROWS, RULES, release=True)
        self.assertFalse(any("UiSelect" in x for x in p), p)  # 'none' is fine on a P1 SFX row
        with tempfile.TemporaryDirectory() as root:
            rows = copy.deepcopy(ROWS)
            for r in rows:
                if r["fallback"] != "none":
                    os.makedirs(os.path.dirname(os.path.join(root, r["fallback"])), exist_ok=True)
                    open(os.path.join(root, r["fallback"]), "wb").close()
            self.assertEqual(audio_check.check_list(rows, RULES, release=True, root=root), [])
            os.remove(os.path.join(root, "pipeline/art/fallback/audio/SW_HitOwl_00.wav"))
            rows[1]["fallback"] = "Content/x.wav"
            p = audio_check.check_list(rows, RULES, release=True, root=root)
            self.assertTrue(any("SW_HitOwl_00.wav does not exist" in x for x in p), p)
            self.assertTrue(any("must be a .wav under" in x for x in p), p)

    def test_p0_or_telegraph_fallback_none_fails(self):
        for sid in ("WandBolt", "ArcWindup"):
            rows = copy.deepcopy(ROWS)
            next(r for r in rows if r["id"] == sid)["fallback"] = "none"
            with self.subTest(sid=sid):
                self.assertTrue(any(f"{sid}: a" in x and "not 'none'" in x for x in audio_check.check_list(rows, RULES)))

    def test_bad_tier_fails(self):
        rows = copy.deepcopy(ROWS)
        rows[0]["tier"] = "MVP"
        self.assertTrue(any("tier 'MVP'" in x for x in audio_check.check_list(rows, RULES)))

    def test_two_telegraphs_fail(self):
        rows = [r for r in ROWS if r["id"] != "ArcWindup"]
        self.assertTrue(any("3 owl attacks" in x for x in audio_check.check_list(rows, RULES)))


class EditorDump(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIX, "ue_dump_pass.json")) as f:
            self.dump = json.load(f)

    def asset(self, name):
        return next(a for a in self.dump["assets"] if a["name"] == name)

    def fails(self, want, release=False):
        p = audio_check.check_dump(self.dump, RULES, ROWS, release)
        self.assertTrue(any(want in x for x in p), (want, p))

    def test_fixture_passes(self):
        self.assertEqual(audio_check.check_dump(self.dump, RULES, ROWS, release=True), [])

    def test_empty_dump_fails(self):
        self.assertTrue(audio_check.check_dump({"assets": []}, RULES, ROWS))

    def test_one_shot_without_concurrency_fails(self):
        self.asset("SC_WandBolt")["concurrency"] = []
        self.fails("SC_WandBolt: concurrency []; want exactly ['SCON_WandBolt']")

    def test_concurrency_settings_fail(self):
        self.dump["concurrency"][0]["max_count"] = 8
        self.dump["concurrency"][0]["resolution_rule"] = "StopOldest"
        self.fails("max_count is 8")
        self.fails("resolution_rule")

    def test_telegraph_priority_below_ambience_fails(self):
        self.asset("SC_GustWindup")["priority"] = 0.5
        self.fails("not above ambience")

    def test_telegraph_pitch_jitter_fails(self):
        self.asset("SC_OwlBoltWindup")["pitch_max"] = 1.05
        self.fails("pitch randomization")

    def test_missing_sound_class_fails(self):
        self.asset("SW_HitOwl_01")["sound_class"] = None
        self.fails("SW_HitOwl_01: sound class None")

    def test_wrong_sound_class_fails(self):
        self.asset("SC_GustWindup")["sound_class"] = "SCL_SFX"
        self.fails("sound list says SCL_Telegraph")

    def test_slider_tree_and_limiter(self):
        self.dump["sound_classes"][1]["parent"] = None
        self.dump["submixes"][0]["effects"].append("SubmixEffectDynamicsProcessorPreset:Limiter")
        self.fails("parent must be SCL_SFX")
        self.fails("2 limiter(s)")

    def test_variation_rules_fail(self):
        a = self.asset("SC_WandBolt")
        a["no_repeat"] = False
        a["random_takes"] = 2
        a["pitch_max"] = 1.2
        self.fails("immediate repeat")
        self.fails("picks from 2 takes")
        self.fails("pitch range")

    def test_looping_must_match_kind(self):
        self.asset("SC_HitOwl")["looping"] = True
        self.fails("looping is True")

    def test_hand_dump_fails(self):
        self.dump["tool"] = "hand"
        del self.dump["engine"]
        self.dump["commit"] = ""
        self.fails("only tools/ue/audio_dump.py")
        self.fails("engine None")
        self.fails("no commit")

    def test_spatialized_asset_fails(self):
        self.asset("SC_HitOwl")["spatialize"] = True
        self.asset("SC_GustLoop")["attenuation"] = "ATT_Default"
        del self.asset("SC_MusicIntro")["attenuation"]
        self.fails("SC_HitOwl: spatialize is True")
        self.fails("SC_GustLoop: attenuation is 'ATT_Default'")
        self.fails("SC_MusicIntro: no attenuation field")

    def test_release_needs_every_p0_p1_sound(self):
        self.dump["assets"] = [a for a in self.dump["assets"] if "EndEvent" not in a["name"]]
        self.fails("EndEvent: in the sound list", release=True)
        self.assertEqual(audio_check.check_dump(self.dump, RULES, ROWS, release=False), [])


class RunLog(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIX, "run_pass.log")) as f:
            self.text = f.read()

    def fails(self, old, new, want, **kw):
        self.assertIn(old, self.text)
        p, _ = audio_check.check_log(self.text.replace(old, new), RULES, rows=ROWS, mapping=L13_MAP, **kw)
        self.assertTrue(any(want in x for x in p), (want, p))

    def test_fixture_passes(self):
        self.assertEqual(audio_check.check_log(self.text, RULES, rows=ROWS, mapping=L13_MAP, release=True), ([], []))

    def test_sound_after_visual_fails(self):
        self.fails("sound_t=4.000 visual_t=4.000", "sound_t=4.100 visual_t=4.000", "after the visual tell")

    def test_short_lead_fails(self):
        self.fails("danger_t=70.350", "danger_t=70.150", "leads danger by 0.150")

    def test_shared_telegraph_sound_fails(self):
        self.fails("sound=ArcWindup", "sound=GustWindup", "shared by attacks")

    def test_late_stem_fails(self):
        self.fails("t_norm=0.251", "t_norm=0.300", "stem MusicContest")

    def test_no_duck_fails(self):
        self.fails("music_db=-12", "music_db=-2", "not ducked")

    def test_master_peak_fails(self):
        self.fails("dbfs=-2.4", "dbfs=-0.4", "master peak")

    def test_voice_cap_and_leak_fail(self):
        self.fails("active=14", "active=30", "30 active")
        self.fails("active=12", "active=20", "rising from 14 to 20")

    def test_slider_leak_fails(self):
        self.fails("class=SCL_SFX volume=0.0", "class=SCL_SFX volume=0.7", "SFX at 0 but SC_GustLoop")

    def drop(self, *needles):
        return "\n".join(l for l in self.text.splitlines() if not any(n in l for n in needles))

    def test_missing_p0_telegraph_fails(self):
        p, _ = audio_check.check_log(self.drop("telegraph attack=OwlBolt", "spawn attack=OwlBolt"), RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("telegraph OwlBolt: no telegraph line" in x for x in p), p)

    def test_attack_with_spawn_needs_telegraph(self):
        p, _ = audio_check.check_log(self.drop("telegraph attack=Arc"), RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("telegraph Arc: no telegraph line, but it has a spawn line" in x for x in p), p)
        self.assertEqual(audio_check.check_log(self.drop("attack=Arc"), RULES, rows=ROWS, mapping=L13_MAP)[0], [])  # P2 cut: fine

    def test_release_needs_p1_telegraph(self):
        text = self.drop("attack=Gust", "gust_param")
        self.assertEqual(audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP)[0], [])
        p, _ = audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP, release=True)
        self.assertTrue(any("telegraph Gust: no telegraph line" in x for x in p), p)

    def test_wrong_windup_for_attack_fails(self):
        self.fails("attack=OwlBolt sound=OwlBoltWindup", "attack=OwlBolt sound=GustWindup", "windup for OwlBolt is OwlBoltWindup")
        self.fails("spawn attack=Arc", "spawn attack=Laser", "attack 'Laser'")

    def test_gust_param_must_change(self):
        text = self.text.replace("value=0.85", "value=0.20").replace("value=0.00", "value=0.20")
        p, _ = audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("gust at t=50.8" in x and "follow gust strength" in x for x in p), p)
        p, _ = audio_check.check_log(self.drop("gust_param"), RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("gust_param missing" in x for x in p), p)
        self.fails("value=0.85", "value=1.5", "value in 0..1")

    def test_stems_must_layer(self):
        self.fails("t=45.2 layered=1", "t=45.2", "MusicContest: needs layered=1")
        self.fails("layered=1 start=bar\n", "layered=1 start=now\n", "start=now")
        self.fails("fade_s=0.5", "fade_s=2.0", "fade_s <= 0.5")
        lines = self.text.splitlines()
        stop = next(l for l in lines if "stem_stop" in l)
        lines.remove(stop)
        lines.insert(4, stop)
        p, _ = audio_check.check_log("\n".join(lines), RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("MusicIntro: stops before end_event" in x for x in p), p)

    def test_virtualized_telegraph_fails(self):
        self.fails("active=12 virtual_telegraph=0", "active=12 virtual_telegraph=1", "virtualized")

    def test_music_missing_is_note_unless_required(self):
        text = "\n".join(l for l in self.text.splitlines() if "AUDIO: stem" not in l)
        p, notes = audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP)
        self.assertEqual(p, [])
        self.assertEqual(len(notes), 1)
        p, _ = audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP, require_music=True)
        self.assertTrue(any("no stem lines" in x for x in p), p)

    def test_empty_log_fails(self):
        self.assertTrue(audio_check.check_log("nothing here", RULES, rows=ROWS, mapping=L13_MAP)[0])


class BlindId(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIX, "blind_id_pass.csv"), newline="") as f:
            self.rec = list(csv.DictReader(f))

    def fails(self, rec, want):
        p = audio_check.check_blind_id(rec, RULES, ROWS)
        self.assertTrue(any(want in x for x in p), (want, p))

    def test_fixture_passes(self):
        self.assertEqual(audio_check.check_blind_id(self.rec, RULES, ROWS), [])
        set_ = audio_check.blind_id_set(ROWS, RULES)
        self.assertTrue({"OwlBoltWindup", "GustWindup", "ArcWindup", "HitOwl", "PlayerHurt"} <= set(set_))
        self.assertFalse(any(r["kind"] == "loop" for r in set_.values()))

    def test_two_players_fail(self):
        self.fails([r for r in self.rec if r["player"] != "P3"], "2 player(s); need 3")

    def test_missed_telegraph_fails(self):
        next(r for r in self.rec if r["player"] == "P1" and r["sound"] == "GustWindup")["answer"] = "ArcWindup"
        self.fails(self.rec, "P1: missed telegraph(s) ['GustWindup']")

    def test_under_90_percent_fails(self):
        heard = [r for r in self.rec if r["player"] == "P2"]
        for r in heard[-5:]:
            r["answer"] = "WandBolt" if r["sound"] != "WandBolt" else "HitOwl"
        self.fails(self.rec, f"P2: named {sum(r['answer'] == r['sound'] for r in heard)}/{len(heard)}")

    def test_unheard_sound_fails(self):
        self.fails([r for r in self.rec if not (r["player"] == "P3" and r["sound"] == "EndEvent")],
                   "P3: did not hear ['EndEvent']")

    def test_cli(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audio_check.main(["--blind-id", os.path.join(FIX, "blind_id_pass.csv"), "--list-file", L13_LIST]), 0)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("player,sound,answer\nP1,WandBolt,WandBolt\n")
        self.addCleanup(os.remove, f.name)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audio_check.main(["--blind-id", f.name, "--list-file", L13_LIST]), 1)


class Docs(unittest.TestCase):
    OWN = ["pipeline/roles/audio.md", "pipeline/audio/audio-rules.md"]

    def test_own_docs_pass(self):
        texts = {}
        for rel in self.OWN:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                texts[rel] = f.read()
        self.assertEqual(audio_check.check_docs(texts, RULES, ROWS), [])

    def test_unknown_sound_name_fails(self):
        p = audio_check.check_docs({"x.md": "- [ ] `SC_EnemyDefeat` plays on kill\n- [ ] `SC_HitOwl` ok"}, RULES, ROWS)
        self.assertEqual(len(p), 1)
        self.assertIn("SC_EnemyDefeat", p[0])

    def test_sfx_names_in_data_must_be_list_ids(self):
        bad = '"sound": "SFX_Owl_BoltWindup", "cue": "SFX_ClockChime"'
        p = audio_check.check_docs({"x.json": bad}, RULES, ROWS)
        self.assertEqual(len(p), 2, p)
        self.assertEqual(audio_check.check_docs({"x.json": '"sound": "SFX_OwlBoltWindup"'}, RULES, ROWS), [])
        self.assertEqual(audio_check.check_docs({"x.md": "`SW_WandBolt_00`, `SW_<Id>_00.wav`, SCL_SFX"}, RULES, ROWS), [])

    def test_repo_feel_and_encounter_sounds_are_list_ids(self):
        texts = {}
        for rel in ("pipeline/feel/feel.json", "pipeline/level/encounter.json"):
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                texts[rel] = f.read()
        self.assertEqual(audio_check.check_docs(texts, RULES, LIVE_ROWS), [])
        self.assertIn('"TalonWarning"', texts["pipeline/level/encounter.json"])
        self.assertIn("SFX_ShieldCatch", texts["pipeline/feel/feel.json"])
        with open(os.path.join(ROOT, ".github", "workflows", "pipeline-checks.yml")) as f:
            ci = f.read()
        self.assertRegex(ci, r"audio_check\.py --docs .*pipeline/level/encounter\.json pipeline/feel/feel\.json")

    def test_stale_old_design_refs_fail(self):
        for line in ("6 sounds, one per MVP 10 event (open, close, attack hit, enemy defeat, hurt, wind loop)",
                     "play the 8 key sounds (`docs/game-spec.md`) in random order",
                     "the art-bible or `docs/game-spec.md` audio row"):
            with self.subTest(line=line):
                self.assertTrue(audio_check.check_docs({"x.md": line}, RULES, ROWS))
        self.assertEqual(audio_check.check_docs({"x.md": "controls in docs/game-spec.md"}, RULES, ROWS), [])
        # GDD 1.3 reuses "MVP 10" for the shield card, so a 1.3 sound line naming it is not stale.
        self.assertEqual(audio_check.check_docs({"x.md": "ShieldCatch sound before the MVP 10 DEF-01 card"}, RULES, ROWS), [])

    def test_repo_docs_pass_the_ci_audio_docs_step(self):
        """The exact file set the CI step reads must pass, so CI is not red on the committed tree."""
        import glob
        files = ["AGENTS.md"] + sorted(glob.glob(os.path.join(ROOT, "pipeline", "*.md"))) \
            + sorted(glob.glob(os.path.join(ROOT, "pipeline", "*", "*.md"))) \
            + [os.path.join(ROOT, "pipeline", "level", "encounter.json"), os.path.join(ROOT, "pipeline", "feel", "feel.json")]
        texts = {}
        for f in files:
            path = f if os.path.isabs(f) else os.path.join(ROOT, f)
            with open(path, encoding="utf-8") as fh:
                texts[os.path.relpath(path, ROOT)] = fh.read()
        self.assertEqual(audio_check.check_docs(texts, RULES, LIVE_ROWS), [])


class Concurrency(unittest.TestCase):
    """Each family has its own concurrency group, so a wand bolt never blocks or steals a hurt or a windup."""
    def setUp(self):
        with open(os.path.join(FIX, "ue_dump_pass.json")) as f:
            self.dump = json.load(f)

    def asset(self, name):
        return next(a for a in self.dump["assets"] if a["name"] == name)

    def problems(self):
        return audio_check.check_dump(self.dump, RULES, ROWS)

    def test_families_get_their_own_group(self):
        by = {r["id"]: r for r in ROWS}
        self.assertEqual(audio_check.concurrency_for(by["WandBolt"], RULES), "SCON_WandBolt")
        self.assertEqual(audio_check.concurrency_for(by["PlayerHurt"], RULES), "SCON_Hurt")
        self.assertEqual(audio_check.concurrency_for(by["OwlBoltWindup"], RULES), "SCON_Telegraph")
        self.assertEqual(audio_check.concurrency_for(by["HitOwl"], RULES), "SCON_Hit")
        groups = {audio_check.concurrency_for(by[i], RULES) for i in ("WandBolt", "PlayerHurt", "GustWindup")}
        self.assertEqual(len(groups), 3)

    def test_telegraph_in_the_wand_group_fails(self):
        self.asset("SC_GustWindup")["concurrency"] = ["SCON_WandBolt"]
        p = self.problems()
        self.assertTrue(any("SC_GustWindup: concurrency ['SCON_WandBolt']" in x for x in p), p)

    def test_hurt_sharing_a_second_group_fails(self):
        self.asset("SC_PlayerHurt")["concurrency"] = ["SCON_Hurt", "SCON_Hit"]
        self.assertTrue(any("SC_PlayerHurt: concurrency" in x for x in self.problems()))

    def test_group_settings_and_missing_group_fail(self):
        tele = next(c for c in self.dump["concurrency"] if c["name"] == "SCON_Telegraph")
        tele["retrigger_time"] = 0.05
        self.dump["concurrency"] = [c for c in self.dump["concurrency"] if c["name"] != "SCON_Hurt"]
        p = self.problems()
        self.assertTrue(any("SCON_Telegraph: retrigger_time is 0.05, want 0.0" in x for x in p), p)
        self.assertTrue(any("concurrency asset SCON_Hurt is missing" in x for x in p), p)

    def test_launch_and_hit_groups_duck_older_voices(self):
        for g in ("SCON_Launch", "SCON_Hit"):
            self.assertEqual(RULES["concurrency"]["assets"][g]["volume_scale"], 0.8)
        self.assertEqual(self.problems(), [])
        launch = next(c for c in self.dump["concurrency"] if c["name"] == "SCON_Launch")
        launch["volume_scale"] = 1.0
        self.assertTrue(any("SCON_Launch: volume_scale is 1.0, want 0.8" in x for x in self.problems()))
        del launch["volume_scale"]
        self.assertTrue(any("SCON_Launch: volume_scale is None" in x for x in self.problems()))

    def test_list_row_with_no_group_fails(self):
        rows = copy.deepcopy(ROWS)
        rows[0]["id"], rows[0]["family"] = "Rattle", "creak"
        p = audio_check.check_list(rows, RULES)
        self.assertTrue(any("Rattle: no concurrency asset for family 'creak'" in x for x in p), p)

    def test_compressor_is_not_a_limiter(self):
        self.dump["submixes"][0]["effects"] = ["SubmixEffectDynamicsProcessorPreset:Compressor"]
        self.assertTrue(any("0 limiter(s)" in x for x in self.problems()))

    def test_unread_fields_fail(self):
        self.dump["unread"] = ["SC_WandBolt.priority"]
        self.assertTrue(any("1 editor field(s) unread" in x for x in self.problems()))
        del self.dump["unread"]
        self.assertTrue(any("no unread list" in x for x in self.problems()))


class MixPhases(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIX, "run_pass.log")) as f:
            self.text = f.read()

    def test_every_phase_has_a_line(self):
        for phase in ("intro", "contest", "desperation"):
            text = "\n".join(l for l in self.text.splitlines() if f"phase={phase}" not in l)
            with self.subTest(phase=phase):
                p, _ = audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP)
                self.assertTrue(any(f"no master_peak line for phase {phase}" in x for x in p), p)

    def test_desperation_clip_fails(self):
        text = self.text + "AUDIO: master_peak phase=desperation dbfs=+3.0\n"
        p, _ = audio_check.check_log(text, RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("master peak 3.0 dBFS in desperation" in x for x in p), p)

    def test_unknown_phase_fails(self):
        p, _ = audio_check.check_log(self.text + "AUDIO: master_peak phase=boss dbfs=-3\n", RULES, rows=ROWS, mapping=L13_MAP)
        self.assertTrue(any("phase 'boss'" in x for x in p), p)


class BlindIdMore(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FIX, "blind_id_pass.csv"), newline="") as f:
            self.rec = list(csv.DictReader(f))

    def test_hit_surfaces_are_in_the_set(self):
        self.assertTrue({"HitClock", "HitWing", "HitOwl"} <= set(audio_check.blind_id_set(ROWS, RULES)))

    def test_missed_must_name_fails_even_above_90_percent(self):
        next(r for r in self.rec if r["player"] == "P1" and r["sound"] == "PlayerHurt")["answer"] = "HitOwl"
        p = audio_check.check_blind_id(self.rec, RULES, ROWS)
        self.assertEqual(p, ["blind-id P1: missed ['PlayerHurt']; every player must name these"])

    def test_player_floor_turns_fail_into_note(self):
        two = [r for r in self.rec if r["player"] != "P3"]
        self.assertTrue(audio_check.check_blind_id(two, RULES, ROWS))  # default floor = 3: FAIL
        rules = copy.deepcopy(RULES)
        rules["blind_id"]["players_floor"] = 2
        notes = []
        self.assertEqual(audio_check.check_blind_id(two, rules, ROWS, notes), [])
        self.assertEqual(len(notes), 1)
        one = [r for r in self.rec if r["player"] == "P1"]
        self.assertTrue(audio_check.check_blind_id(one, rules, ROWS))


class Muted(unittest.TestCase):
    def load(self):
        with open(os.path.join(FIX, "muted_pass.csv"), newline="") as f:
            return list(csv.DictReader(f))

    def test_fixture_passes(self):
        self.assertEqual(audio_check.check_muted(self.load(), RULES), [])

    def test_unread_state_fails(self):
        rec = self.load()
        rec[1]["attack"] = "no"
        self.assertEqual(audio_check.check_muted(rec, RULES),
                         ["muted P2: attack is 'no'; with sound off it must still read on screen"])

    def test_missing_column_or_rows_fail(self):
        self.assertTrue(audio_check.check_muted([{"player": "P1", "phase": "yes"}], RULES))
        self.assertTrue(audio_check.check_muted([], RULES))

    def test_cli(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audio_check.main(["--muted", os.path.join(FIX, "muted_pass.csv"), "--list-file", L13_LIST]), 0)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("player,phase,attack,umbrella_tier\nP1,yes,,yes\n")
        self.addCleanup(os.remove, f.name)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(audio_check.main(["--muted", f.name, "--list-file", L13_LIST]), 1)


# ---------------------------------------------------------------- day-0 cards the audio gates depend on

AUDIO_DOCS = ["pipeline/roles/audio.md", "pipeline/audio/audio-rules.md"]
DAY0 = os.path.join(ROOT, "pipeline", "day0-cards.md")
CARD_REF = re.compile(r"(?i)\bcards?\s+(\d+\.\d+[a-z]?)\b")
DAY0_ROW = re.compile(r"^\|\s*(\d+\.\d+[a-z]?)\s*\|", re.M)


def missing_cards(doc_texts, day0_text):
    """Card ids a doc cites ("card 0.17", "cards 0.4a") that have no row in day0-cards.md."""
    have = set(DAY0_ROW.findall(day0_text))
    return sorted({f"{path}: card {cid}" for path, text in doc_texts.items()
                   for cid in CARD_REF.findall(text) if cid not in have})


class CitedDay0Cards(unittest.TestCase):
    """The --ue-dump and --log gates only mean something once the day-0 cards that make their inputs exist."""
    def test_every_cited_card_has_a_day0_row(self):
        texts = {}
        for rel in AUDIO_DOCS:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                texts[rel] = f.read()
        cited = {c for t in texts.values() for c in CARD_REF.findall(t)}
        self.assertTrue({"0.15", "0.4c", "0.5a"} <= cited, cited)
        with open(DAY0, encoding="utf-8") as f:
            day0 = f.read()
        self.assertEqual(missing_cards(texts, day0), [], "add these rows to pipeline/day0-cards.md")

    def test_missing_row_fails_and_present_row_passes(self):
        day0 = "| # | Card |\n|---|---|\n| 0.17 | Audio core |\n| 0.4a | MCP |\n"
        self.assertEqual(missing_cards({"x.md": "after card 0.17 and card 0.4a"}, day0), [])
        self.assertEqual(missing_cards({"x.md": "day-0 card 0.18 prints it"}, day0), ["x.md: card 0.18"])
        self.assertEqual(missing_cards({"x.md": "a 0.18 s fade"}, day0), [])  # plain numbers are not card ids


# ---------------------------------------------------------------- audio_dump.py against a fake editor

STAGED_DUMP = os.path.join(ROOT, "pipeline", "audio", "ue", "audio_dump.py")
HOME_DUMP = os.path.join(ROOT, "tools", "ue", "audio_dump.py")


def load_dump_tool():
    import importlib.util
    path = STAGED_DUMP  # the copy in tools/ue/ must match it byte for byte (test_home_copy_matches_staged)
    spec = importlib.util.spec_from_file_location("audio_dump", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeEnum:
    def __init__(self, name):
        self.name = name


class FakeObj:
    def __init__(self, cls, name, props):
        self.cls, self.name, self.props = cls, name, props

    def get_name(self):
        return self.name

    def get_class(self):
        return FakeObj("Class", self.cls, {})

    def get_editor_property(self, n):
        if n not in self.props:
            raise Exception(f"no property {n}")
        return self.props[n]


class FakeAD:
    def __init__(self, obj):
        self.obj = obj

    def get_asset(self):
        return self.obj


def fake_editor(fix):
    """An unreal module whose /Game/UmbrellaElla/Audio holds the assets the fixture describes."""
    objs = {}
    for s in fix["submixes"]:
        lim = FakeObj("SubmixEffectDynamicsProcessorPreset", "Lim", {"settings": FakeObj(
            "Settings", "s", {"dynamics_processor_type": FakeEnum("LIMITER")})})
        objs[s["name"]] = FakeObj("SoundSubmix", s["name"], {"parent_submix": None, "submix_effect_chain": [lim]})
    for c in fix["sound_classes"]:
        objs[c["name"]] = FakeObj("SoundClass", c["name"], {"parent_class": None, "properties": FakeObj(
            "SoundClassProperties", "p", {"default_submix": objs[c["default_submix"]]})})
    for c in fix["sound_classes"]:
        objs[c["name"]].props["parent_class"] = objs.get(c["parent"])
    for c in fix["concurrency"]:
        settings = FakeObj("SoundConcurrencySettings", "c", {
            "max_count": c["max_count"], "resolution_rule": FakeEnum("STOP_LOWEST_PRIORITY"),
            "retrigger_time": c["retrigger_time"], "voice_steal_release_time": c["voice_steal_release_time"],
            "volume_scale": c["volume_scale"]})
        objs[c["name"]] = FakeObj("SoundConcurrency", c["name"], {"concurrency": settings})

    def node(cls, children=(), **props):
        return FakeObj(cls, cls, {"child_nodes": list(children), **props})

    for a in fix["assets"]:
        base = {"sound_class_object": objs[a["sound_class"]]}
        if a["class"] == "SoundWave":
            objs[a["name"]] = FakeObj("SoundWave", a["name"], {**base, "looping": a["looping"]})
            continue
        if a.get("random_takes"):
            top = node("SoundNodeModulator", [node("SoundNodeRandom", [node("SoundNodeWavePlayer", looping=False)
                                                                       for _ in range(a["random_takes"])],
                                                   randomize_without_replacement=a["no_repeat"])],
                       pitch_min=a["pitch_min"], pitch_max=a["pitch_max"])
        else:
            top = node("SoundNodeWavePlayer", looping=a["looping"])
        objs[a["name"]] = FakeObj(a["class"], a["name"], {
            **base, "priority": a["priority"], "concurrency_set": [objs[n] for n in a.get("concurrency", [])],
            "attenuation_settings": None, "override_attenuation": False, "first_node": top})

    class Registry:
        def get_assets_by_path(self, path, recursive=False):
            return [FakeAD(o) for o in objs.values()] if path == "/Game/UmbrellaElla/Audio" and recursive else []

    class ue:
        class AssetRegistryHelpers:
            @staticmethod
            def get_asset_registry():
                return Registry()

        class SystemLibrary:
            @staticmethod
            def get_engine_version():
                return "5.8.4-0+++UE5+Release-5.8"
    return ue, objs


class AudioDumpTool(unittest.TestCase):
    """The dump tool's output, read from a fake editor, passes the checker; break the editor, it fails."""
    def setUp(self):
        with open(os.path.join(FIX, "ue_dump_pass.json")) as f:
            self.fix = json.load(f)
        self.tool = load_dump_tool()
        self.ue, self.objs = fake_editor(self.fix)

    def dump(self):
        return self.tool.build_dump(self.ue, commit="abc1234")

    def test_dump_of_a_good_project_passes(self):
        d = self.dump()
        self.assertEqual(d["tool"], "tools/ue/audio_dump.py")
        self.assertEqual(d["engine"], "5.8.4")
        self.assertEqual(d["unread"], [])
        self.assertEqual(audio_check.check_dump(d, RULES, ROWS, release=True), [])

    def test_telegraph_in_wand_group_fails(self):
        self.objs["SC_OwlBoltWindup"].props["concurrency_set"] = [self.objs["SCON_WandBolt"]]
        p = audio_check.check_dump(self.dump(), RULES, ROWS)
        self.assertTrue(any("SC_OwlBoltWindup: concurrency ['SCON_WandBolt']" in x for x in p), p)

    def test_wrong_property_name_lands_in_unread_and_fails(self):
        del self.objs["SC_WandBolt"].props["priority"]
        d = self.dump()
        self.assertIn("SC_WandBolt.priority", d["unread"])
        self.assertTrue(any("unread" in x for x in audio_check.check_dump(d, RULES, ROWS)))

    def test_attenuation_makes_it_3d_and_fails(self):
        self.objs["SC_HitOwl"].props["attenuation_settings"] = FakeObj("SoundAttenuation", "ATT_Default", {})
        p = audio_check.check_dump(self.dump(), RULES, ROWS)
        self.assertTrue(any("SC_HitOwl: spatialize is True" in x for x in p), p)

    def test_full_volume_burst_fails(self):
        self.objs["SCON_Hit"].props["concurrency"].props["volume_scale"] = 1.0
        p = audio_check.check_dump(self.dump(), RULES, ROWS)
        self.assertTrue(any("SCON_Hit: volume_scale is 1.0, want 0.8" in x for x in p), p)

    def test_compressor_mode_fails(self):
        eff = self.objs["SM_Master"].props["submix_effect_chain"][0]
        eff.props["settings"].props["dynamics_processor_type"] = FakeEnum("COMPRESSOR")
        self.assertTrue(any("0 limiter(s)" in x for x in audio_check.check_dump(self.dump(), RULES, ROWS)))

    def test_home_copy_matches_staged(self):
        self.assertTrue(os.path.exists(HOME_DUMP), "tools/ue/audio_dump.py is missing: copy "
                        "pipeline/audio/ue/audio_dump.py there byte for byte before the freeze")
        with open(HOME_DUMP, encoding="utf-8") as a, open(STAGED_DUMP, encoding="utf-8") as b:
            self.assertEqual(a.read(), b.read(), "tools/ue/audio_dump.py differs from pipeline/audio/ue/audio_dump.py")


class P0SoundTiers(unittest.TestCase):
    """Dry run B H8: a P0 feature's sound is never cut, dropped a tier or removed."""
    def test_tiers(self):
        rows = audio_check.load_list(L13_LIST)
        self.assertEqual(audio_check.p0_tier_problems(rows, rows, root=L13), [])
        up = copy.deepcopy(rows)
        next(r for r in up if r["id"] == "HitClock")["tier"] = "P0"
        self.assertEqual(audio_check.p0_tier_problems(up, rows, root=L13), [], "raising a tier is fine")
        for rid, tier in (("ShieldCatch", "P2"), ("GustCatch", "cut"), ("ShieldCatch", "P1"), ("HitClock", "P2")):
            with self.subTest(rid=rid, tier=tier):   # broken on purpose
                bad = copy.deepcopy(rows)
                next(r for r in bad if r["id"] == rid)["tier"] = tier
                self.assertTrue(audio_check.p0_tier_problems(bad, rows, root=L13))
        cut = copy.deepcopy(rows)
        next(r for r in cut if r["id"] == "GustCatch")["tier"] = "cut"
        self.assertTrue(audio_check.p0_tier_problems(cut, root=L13), "cut fails even without the base list")
        gone = [r for r in rows if r["id"] != "ShieldCatch"]
        self.assertTrue(audio_check.p0_tier_problems(gone, rows, root=L13))
        p2 = copy.deepcopy(rows)
        next(r for r in p2 if r["id"] == "ArcWindup")["tier"] = "cut"
        self.assertEqual(audio_check.p0_tier_problems(p2, rows, root=L13), [], "a non-P0 sound may be cut")


    def test_rewording_the_gdd_cell_changes_nothing(self):
        """Final-7 B H2: the P0 sounds come from the manifest's `sounds` lists, not the row's own gdd cell."""
        rows = audio_check.load_list(L13_LIST)
        for rid, gdd, tier in (("ShieldCatch", "GDD 1.3 §6 front shield", "cut"), ("GustCatch", "safe wind", "P2"),
                               ("ShieldCatch", "GDD 1.3 §6 front shield", "P0")):
            with self.subTest(rid=rid, tier=tier):   # broken on purpose
                bad = copy.deepcopy(rows)
                r = next(r for r in bad if r["id"] == rid)
                r["gdd"], r["tier"] = gdd, tier
                self.assertTrue(audio_check.p0_tier_problems(bad, rows, root=L13), "against the base list")
                self.assertTrue(audio_check.p0_tier_problems(bad, root=L13), "without the base list (push to main)")
        gone = [r for r in rows if r["id"] != "GustCatch"]
        self.assertTrue(any("missing, but docs/feature-manifest.json" in p for p in audio_check.p0_tier_problems(gone, root=L13)))

    def test_manifest_p0_sounds_are_append_only(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import manifest_check as mc
        with open(os.path.join(L13, "docs", "feature-manifest.json"), encoding="utf-8") as f:
            man = json.load(f)
        self.assertEqual(mc.sound_pin_problems(man, man), [])
        bad = copy.deepcopy(man)
        rec = next(f for f in bad["features"] if f["feature_id"] == "DEF-01")
        rec["sounds"] = []   # broken on purpose: cut the shield sound through the manifest
        self.assertTrue(any(k == "sounds" for k, _, _ in mc.sound_pin_problems(bad, man)))
        more = copy.deepcopy(man)
        next(f for f in more["features"] if f["feature_id"] == "DEF-01")["sounds"].append("ShieldHeal")
        self.assertEqual(mc.sound_pin_problems(more, man), [], "adding a sound is fine")


if __name__ == "__main__":
    unittest.main()

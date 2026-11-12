"""Every thing in the game that makes a sound has one (pipeline/audio/sound-events.json, audio_check.py --events and the
run-time `AUDIO: event` lines). Each rule has the live repo passing and a source or log broken on purpose."""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_check  # noqa: E402

# The coverage rules are checked on the frozen GDD 1.3 data (states, attacks and shield sounds the rules were written
# around); the GDD SH1.0 repo data is checked in StolenHourCoverage below.
L13 = os.path.join(ROOT, "tests", "fixtures", "gdd13")
ROWS = audio_check.load_list(os.path.join(L13, "pipeline", "audio", "sound-list.csv"))
RULES = audio_check.load_rules()
MAP = audio_check.load_json_file(os.path.join(L13, "pipeline", "audio", "sound-events.json"))
STYLE = audio_check.load_json_file(os.path.join(L13, "pipeline", "audio", "style.json"))
SOURCES = ["docs/feature-manifest.json", "docs/gdd/CURRENT", "pipeline/unreal/gameplay-code.md",
           "pipeline/ui/menus.md", "pipeline/ui/signals.json"]


class Coverage(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        cur = open(os.path.join(L13, "docs/gdd/CURRENT")).read().strip()
        for rel in SOURCES + [f"docs/gdd/{cur}"]:
            os.makedirs(os.path.dirname(os.path.join(self.d, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(L13, rel), os.path.join(self.d, rel))
        self.gdd = os.path.join(self.d, "docs/gdd", cur)

    def check(self, rows=ROWS, mapping=MAP, style=STYLE):
        return audio_check.check_events(rows, mapping, style, root=self.d)

    def edit(self, rel, old, new):
        p = os.path.join(self.d, rel)
        text = open(p, encoding="utf-8").read()
        self.assertIn(old, text)
        open(p, "w", encoding="utf-8").write(text.replace(old, new, 1))

    def test_repo_covers_every_source(self):
        self.assertEqual(audio_check.check_events(ROWS, MAP, STYLE, L13), [])
        keys = audio_check.event_sources(L13)
        for want in ("event:BossAttackTelegraphed", "state:SHIELD_DESCENT", "state:PAUSED", "attack:base-bolt",
                     "feature:WIND-01", "screen:title", "setting:text-size", "ui:focus", "ui:back"):
            self.assertIn(want, keys)
        self.assertGreaterEqual(len(keys), 90)

    def test_broken_on_purpose_new_event_with_no_sound_fails(self):
        p = os.path.join(self.d, "docs/feature-manifest.json")
        m = json.load(open(p))
        m["events"].append("OwlScreeched")
        json.dump(m, open(p, "w"))
        self.assertTrue(any(x.startswith("event:OwlScreeched") for x in self.check()), self.check())

    def test_broken_on_purpose_new_state_screen_setting_and_menu_action_fail(self):
        self.edit(os.path.relpath(self.gdd, self.d), "| DEFEATED |", "| STUNNED | Owl stun. | Stops. | APPROVED_P0 |\n| DEFEATED |")
        self.edit("pipeline/ui/menus.md", "→ quit.", "→ credits → quit.")
        self.edit("pipeline/ui/menus.md", "Text size (100", "Subtitles (On / Off), Text size (100")
        self.edit("pipeline/unreal/gameplay-code.md", "CatchSucceeded, CatchFailed,", "CatchSucceeded, CatchFailed, GearJammed,")
        p = self.check()
        for want in ("state:STUNNED", "screen:credits", "setting:subtitles", "event:GearJammed"):
            self.assertTrue(any(x.startswith(want) for x in p), (want, p))

    def test_broken_on_purpose_bad_keys_fail(self):
        cases = {
            "not a row": ({"event:WindExited": {"sounds": ["WindGone"]}}, "WindGone is not a row"),
            "silent no reason": ({"event:WindExited": {"silent": " "}}, "silent needs a reason"),
            "pending approved": ({"event:WindExited": {"pending": "WIND-01"}}, "pending on WIND-01"),
            "two kinds": ({"event:WindExited": {"sounds": ["WindExit"], "silent": "x"}}, "exactly one of"),
            "stale": ({"state:FLYING": {"sounds": ["WindExit"]}}, "state:FLYING: not in its source"),
            "manifest sound dropped": ({"feature:OWL-01": {"sounds": ["OwlBoltLaunch", "OwlBoltTravelLoop", "OwlBoltFade"]}},
                                       "the manifest lists OwlBoltWindup"),
        }
        for name, (patch, want) in cases.items():
            with self.subTest(name):
                m = copy.deepcopy(MAP)
                m["keys"].update(patch)
                self.assertTrue(any(want in x for x in self.check(mapping=m)), self.check(mapping=m))

    def test_broken_on_purpose_orphan_row_and_row_without_style_family(self):
        rows = copy.deepcopy(ROWS) + [dict(ROWS[0], id="OwlHoot")]
        p = self.check(rows=rows)
        self.assertTrue(any("OwlHoot: no sound-events.json key uses it" in x for x in p), p)
        self.assertTrue(any("OwlHoot: no style family" in x for x in p), p)
        st = copy.deepcopy(STYLE)
        st["families"]["hit"]["members"].append("WandBolt")
        self.assertTrue(any("WandBolt: in 2 style families" in x for x in self.check(style=st)))

    def test_cut_row_leaves_its_event_silent_and_fails(self):
        rows = copy.deepcopy(ROWS)
        next(r for r in rows if r["id"] == "WindExit")["tier"] = "cut"
        self.assertTrue(any("event:WindExited: every sound is cut" in x for x in self.check(rows=rows)))


LINE = "LogUmbrellaElla: AUDIO: event key={k} sound={s} t=1.0"


class RunTime(unittest.TestCase):
    def ev(self, *pairs):
        return audio_check.parse_log("\n".join(LINE.format(k=k, s=s) for k, s in pairs))

    def test_fixture_log_passes(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "audio", "run_pass.log")) as fh:
            text = fh.read()
        self.assertEqual(audio_check.check_log(text, RULES, rows=ROWS, mapping=MAP), ([], []))

    def test_event_with_its_sound_passes(self):
        self.assertEqual(audio_check.check_event_lines(
            self.ev(("state:SHIELD_DESCENT", "ShieldRaise"), ("event:TestPresetLoaded", "none")), MAP), [])

    def test_broken_on_purpose_event_fired_with_no_sound_fails(self):
        p = audio_check.check_event_lines(self.ev(("event:WindExited", "none")), MAP)
        self.assertTrue(any("fired with no sound playing" in x for x in p), p)

    def test_broken_on_purpose_unknown_key_or_wrong_sound_fails(self):
        p = audio_check.check_event_lines(self.ev(("event:OwlScreeched", "HitOwl"), ("ui:back", "UiSelect")), MAP)
        self.assertTrue(any("OwlScreeched" in x and "not a key" in x for x in p), p)
        self.assertTrue(any("played UiSelect" in x for x in p), p)

    def test_no_event_lines_is_a_note_then_a_release_failure(self):
        notes = []
        self.assertEqual(audio_check.check_event_lines([], MAP, notes=notes), [])
        self.assertTrue(notes)
        self.assertTrue(audio_check.check_event_lines([], MAP, release=True))

    def test_cli_events_mode(self):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audio_check.main(["--events"]), 0)


class StolenHourCoverage(unittest.TestCase):
    """GDD SH1.0: the repo's sound list covers the four MOVE-19 modes, the Keeper preset's attacks and every Rule ID."""

    def test_repo_covers_every_source(self):
        rows = audio_check.load_list()
        mapping = audio_check.load_json_file(audio_check.DEFAULT_EVENTS)
        style = audio_check.load_json_file(audio_check.DEFAULT_STYLE)
        self.assertEqual(audio_check.check_events(rows, mapping, style), [])
        keys = audio_check.event_sources()
        for want in ("state:overhead-rise", "state:fast-free-fall", "attack:talon-rake", "attack:mech-rear-two-stage",
                     "feature:OWL-16", "feature:FLOW-48", "screen:tutorial", "setting:controller", "event:LevelGained"):
            self.assertIn(want, keys)
        self.assertEqual(mapping["keys"]["feature:FLOW-48"]["sounds"], ["XpGain", "LevelUpClock"])
        cut = {r["id"] for r in rows if r["tier"] == "cut"}
        self.assertIn("ChargeRelease", cut, "Stored Thunder / charge is out of GDD SH1.0 scope (MOVE-12)")
        self.assertFalse(any("Thunder" in r["id"] for r in rows if r["tier"] != "cut"))
        g1 = {r["id"] for r in rows if r["tier"] == "P0"}
        self.assertLessEqual({"WandBolt", "TalonWarning", "ClockBeat", "AbsorbStart", "MusicTitle"}, g1,
                             "G1 sounds (the Start Game mode) are P0 so the run makes them first")


if __name__ == "__main__":
    unittest.main()

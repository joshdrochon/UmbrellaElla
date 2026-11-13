import importlib.util
import json
import os
import pathlib
import re
import tempfile
import threading
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ap = load("agent_play", "tools/build/agent_play.py")
pc = load("playtest_check", "tools/build/playtest_check.py")


def jwrite(path, obj):
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f)
    os.replace(path + ".tmp", path)


class FakeGame:
    """The hook's file protocol (AgentPlayHookSubsystem.cpp) in a thread: frames out, turn files in, result at the end."""

    def __init__(self, dir, res, low, comparison, max_game_s, log_path, end_after=2, outcome="cleared", warnings=1):
        self.dir, self.res, self.low, self.comparison = dir, res, low, comparison
        self.end_after, self.outcome, self.warnings = end_after, outcome, warnings
        self.t = None
        self.stopped = False
        self.seen_turns = []

    def start(self):
        os.makedirs(os.path.join(self.dir, "frames"), exist_ok=True)
        self.t = threading.Thread(target=self.run, daemon=True)
        self.t.start()

    def alive(self):
        return self.t is not None and self.t.is_alive()

    def stop(self):
        self.stopped = True

    def frame(self, n):
        with open(os.path.join(self.dir, "frames", "f%06d.jpg" % n), "wb") as f:
            f.write(b"\xff\xd8\xff\xd9")

    def run(self):
        n = turn = 0
        self.frame(1)
        n = 1
        jwrite(os.path.join(self.dir, "status.json"), {"state": "ready", "turn": 0, "frame": n, "game_s": 0})
        while not self.stopped:
            tf = os.path.join(self.dir, "turn_%04d.txt" % (turn + 1))
            if os.path.exists(os.path.join(self.dir, "stop.txt")):
                self.finish("stopped", n, turn)
                return
            if os.path.exists(tf):
                turn += 1
                self.seen_turns.append(open(tf).read())
                for _ in range(3):
                    n += 1
                    self.frame(n)
                if turn >= self.end_after:
                    self.finish(self.outcome, n, turn)
                    return
                jwrite(os.path.join(self.dir, "status.json"), {"state": "paused", "turn": turn, "frame": n, "game_s": turn})
            time.sleep(0.01)

    def finish(self, outcome, n, turn):
        jwrite(os.path.join(self.dir, "result.json"), {
            "outcome": outcome, "res": self.res, "debug": 0, "health": "low" if self.low else "healthy",
            "profile": "comparison" if self.comparison else "natural", "turns": turn, "game_s": turn, "shots": 6,
            "useful_hits": 1, "damage": 1.0, "warnings": self.warnings, "reset_s": 2.5, "idle_s": 1.0, "idle_share": 0.2,
            "teleport_steps": 0, "autoaim": 0, "invuln": 0, "teleport": 0})
        jwrite(os.path.join(self.dir, "status.json"), {"state": "ended", "turn": turn, "frame": n, "game_s": turn})


class FakePlayer:
    def __init__(self, boring="no", understood=True, warning=True, script=("hold J 400", "wait 100")):
        self.boring, self.understood, self.warning, self.script = boring, understood, warning, list(script)
        self.calls = []
        self.cost = 0.0

    def ask(self, text, images):
        self.calls.append((text, images))
        if "BEFORE playing" in text:
            return json.dumps({"expect": {"solid": "the island", "harmful": "the guard shot", "background": "clouds"},
                               "plan": "drop and ride up", "say": "pretty", "turn": self.script})
        if "The attempt is over" in text:
            return json.dumps({"words": "It was ok.", "understood": self.understood, "warning_noticed": self.warning,
                               "warning_what": "a raised flag", "too_slight": True, "boring": self.boring, "boring_why": "short"})
        return json.dumps({"say": "going", "warning_seen": self.warning, "turn": self.script})


class TurnScriptTests(unittest.TestCase):
    def test_good_script(self):
        self.assertEqual(ap.validate_turn("hold D 600\ntap J\nwait 300\n# c\ndown K\nwait 200\nup K\nrelease_all"), [])

    def test_refusals(self):
        for bad in ("tap Tilde", "teleport 1 2", "wait -5", "wait 3001", "wait 2000\nwait 2000", "hold J",
                    "tap F1", "tap Escape", "\n".join(["tap J"] * 25)):
            self.assertTrue(ap.validate_turn(bad), bad)

    def test_key_table_matches_game_rules(self):
        src = (ROOT / "Source/UmbrellaElla/Private/Smoke/AgentPlayRules.cpp").read_text()
        cpp = dict(re.findall(r'\{TEXT\("([^"]+)"\), TEXT\("([^"]+)"\)\}', src))
        self.assertEqual(cpp, ap.KEYS)

    def test_limits_match_game_rules(self):
        hdr = (ROOT / "Source/UmbrellaElla/Public/Smoke/AgentPlayRules.h").read_text()
        self.assertIn("MaxTurnMillis = %d" % ap.MAX_TURN_MS, hdr)
        self.assertIn("MaxLines = %d" % ap.MAX_LINES, hdr)

    def test_player_cannot_name_a_non_input(self):
        # No move/aim/heal verbs exist in either parser.
        src = (ROOT / "Source/UmbrellaElla/Private/Smoke/AgentPlayRules.cpp").read_text()
        for word in ("teleport", "aim", "heal", "invuln", "godmode"):
            self.assertNotIn('"%s"' % word, src.lower())


class ReplyTests(unittest.TestCase):
    def test_parse_fenced_and_loose(self):
        self.assertEqual(ap.parse_reply('```json\n{"a": 1}\n```')["a"], 1)
        self.assertEqual(ap.parse_reply('Sure. {"turn": ["tap J"]} bye')["turn"], ["tap J"])
        self.assertEqual(ap.parse_reply("no json"), {})

    def test_pick_frames(self):
        paths = ["f%d" % i for i in range(10)]
        self.assertEqual(ap.pick_frames(paths, 2), ["f0", "f9"])
        self.assertEqual(ap.pick_frames(paths[:1], 2), ["f0"])
        self.assertEqual(ap.pick_frames([], 2), [])

    def test_as_bool(self):
        self.assertTrue(ap.as_bool("yes"))
        self.assertFalse(ap.as_bool("no"))
        self.assertFalse(ap.as_bool(None))


class AttemptTests(unittest.TestCase):
    def run_attempt(self, **kw):
        d = tempfile.mkdtemp()
        game = FakeGame(d, "1280x720", False, False, 90, os.path.join(d, "g.log"), **{k: v for k, v in kw.items() if k in ("end_after", "outcome", "warnings")})
        player = FakePlayer(**{k: v for k, v in kw.items() if k in ("boring", "understood", "warning", "script")})
        game.start()
        rec = ap.play_attempt(game, player, d, max_turns=kw.get("max_turns", 10), sleep=lambda s: time.sleep(0.005))
        rec["result"] = ap.read_result(d, timeout=2)
        game.stop()
        return d, game, player, rec

    def test_full_attempt_records_every_haz16_item(self):
        d, game, player, rec = self.run_attempt()
        self.assertEqual(rec["expect"]["solid"], "the island")
        self.assertTrue(rec["plan"])
        self.assertEqual(rec["final"]["boring"], "no")
        self.assertTrue(rec["warning_flags"] >= 1)
        self.assertEqual(rec["result"]["outcome"], "cleared")
        self.assertEqual(len(game.seen_turns), 2)
        # The player saw only images + the controls text: its first prompt carries the controls, never a source path.
        first = player.calls[0][0]
        self.assertIn("CONTROLS", first)
        self.assertNotIn("Source/", first)
        for text, images in player.calls:
            for im in images:
                self.assertIn("/frames/", im)

    def test_bad_script_is_refused_and_costs_no_turn(self):
        d, game, player, rec = self.run_attempt(script=["tap Tilde"], end_after=1, max_turns=3)
        self.assertTrue(rec["refused"])
        self.assertEqual(game.seen_turns, [])
        self.assertIn("refused", player.calls[1][0])
        self.assertEqual(rec["result"]["outcome"], "stopped")

    def test_player_stop_ends_the_game(self):
        d, game, player, rec = self.run_attempt(end_after=99, max_turns=2)
        self.assertEqual(rec["result"]["outcome"], "stopped")
        self.assertTrue(os.path.exists(os.path.join(d, "stop.txt")))


class LogTests(unittest.TestCase):
    def attempts(self, res, health, profile="natural", boring="no", understood=True, outcome="cleared"):
        return {"plan": "p", "expect": {"solid": "a", "harmful": "b", "background": "c"}, "warning_flags": 1, "turns": [1],
                "final": {"words": "w", "understood": understood, "boring": boring, "warning_noticed": True, "too_slight": boring == "yes"},
                "result": {"outcome": outcome, "res": res, "health": health, "profile": profile, "shots": 4, "useful_hits": 1,
                           "damage": 1, "warnings": 1, "reset_s": 2, "idle_s": 1, "teleport": 0, "debug": 0}}

    def good_log(self):
        atts = [self.attempts(r, h) for r in ("1280x720", "1920x1080") for h in ("healthy", "low")]
        return ap.build_log(atts, "commit=x")

    def test_group_lines_pass_the_checker(self):
        res = pc.evaluate(self.good_log())
        self.assertTrue(res["HAZ-16"]["pass"], res["HAZ-16"])

    def test_boring_attempt_fails_the_checker(self):
        atts = [self.attempts(r, h, boring="yes") for r in ("1280x720", "1920x1080") for h in ("healthy", "low")]
        res = pc.evaluate(ap.build_log(atts, "x"))
        self.assertFalse(res["HAZ-16"]["pass"])

    def test_mac_sizes_pass(self):
        atts = [self.attempts(r, h) for r in ("1280x720", "1728x1117") for h in ("healthy", "low")]
        res = pc.evaluate(ap.build_log(atts, "x"))
        self.assertTrue(res["HAZ-16"]["pass"], res["HAZ-16"])

    def test_scripted_lines_do_not_count(self):
        scripted = ("PLAYTEST_HAZ16 res=1280x720 debug=0 health=healthy autoaim=0 invuln=0 teleport=0 boring=0 cleared=1\n"
                    "PLAYTEST_HAZ16 res=1920x1080 debug=0 health=low autoaim=0 invuln=0 teleport=0 boring=0 cleared=1\n")
        self.assertFalse(pc.evaluate(scripted)["HAZ-16"]["pass"])

    def test_one_size_only_fails(self):
        atts = [self.attempts("1280x720", h) for h in ("healthy", "low")]
        self.assertFalse(pc.evaluate(ap.build_log(atts, "x"))["HAZ-16"]["pass"])

    def test_comparison_gate(self):
        d = tempfile.mkdtemp()
        for i, (b, u) in enumerate([("yes", True), ("yes", True)], 1):
            os.makedirs(os.path.join(d, "attempt_%02d" % i))
            json.dump(self.attempts("1280x720", "healthy", boring=b, understood=u), open(os.path.join(d, "attempt_%02d" % i, "attempt.json"), "w"))
        self.assertTrue(ap.comparison_allowed(d)[0])
        os.makedirs(os.path.join(d, "attempt_03"))
        json.dump(self.attempts("1280x720", "healthy", boring="no"), open(os.path.join(d, "attempt_03", "attempt.json"), "w"))
        self.assertFalse(ap.comparison_allowed(d)[0])
        self.assertFalse(ap.comparison_allowed(tempfile.mkdtemp())[0])

    def test_comparison_line_never_passes_a_natural_reject(self):
        atts = [self.attempts(r, h, boring="yes") for r in ("1280x720", "1920x1080") for h in ("healthy", "low")]
        atts += [self.attempts(r, h, profile="comparison") for r in ("1280x720", "1920x1080") for h in ("healthy", "low")]
        res = pc.evaluate(ap.build_log(atts, "x"))
        self.assertFalse(res["HAZ-16"]["pass"])

    def test_main_runs_with_fakes_and_writes_the_log(self):
        out = tempfile.mkdtemp()
        factory = lambda *a: FakeGame(*a)
        code = ap.main(["--res", "1280x720", "--health", "both", "--attempts", "1", "--out", out],
                       game_factory=factory, player_factory=lambda: FakePlayer())
        self.assertEqual(code, 0)
        text = open(os.path.join(out, "haz16.log")).read()
        self.assertEqual(text.count("PLAYTEST_HAZ16 "), 2)
        self.assertIn("health=low", text)

    def test_main_refuses_comparison_without_natural(self):
        self.assertEqual(ap.main(["--profile", "comparison", "--out", tempfile.mkdtemp()]), 2)


if __name__ == "__main__":
    unittest.main()

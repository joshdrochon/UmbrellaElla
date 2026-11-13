"""Builder and critic loop for audio (tools/audio_loop.py) and its enforcement on audio PRs (tools/check_pr.py rule
audio). A small git repo with synthetic takes; every rule has a passing case and one broken on purpose."""
import contextlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import audio_loop  # noqa: E402
import check_card  # noqa: E402
import check_pr  # noqa: E402
from test_audio_style import R, write  # noqa: E402

STYLE_FAM = {"members": ["UiMove", "UiBack"], "character": "a soft escapement tick", "instruments": "tick",
             "register": "mid-high", "reverb": "small", "prompt": "tick",
             "ranges": {"centroid_hz": [1500, 8000], "decay_s": [0.2, 2.0], "lufs": [-35, -8]}}


def tone(freq, rt=0.6):
    return [0.5 * 10 ** (-3 * i / (rt * R)) * math.sin(2 * math.pi * freq * i / R) for i in range(int(rt * 1.5 * R))]


class Loop(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        shutil.copytree(os.path.join(ROOT, "pipeline", "audio"), os.path.join(self.d, "pipeline", "audio"))
        p = os.path.join(self.d, "pipeline", "audio", "style.json")
        st = json.load(open(p))
        for f in st["families"].values():
            f["members"] = [m for m in f["members"] if m not in STYLE_FAM["members"]]
        st["families"]["test_ui"] = STYLE_FAM
        json.dump(st, open(p, "w"))
        self.git("init", "-q")
        self.take("UiBack", 3000)
        self.commit()

    def git(self, *a):
        return subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              capture_output=True, text=True, check=True).stdout

    def commit(self):
        self.git("add", "-A", "Audio", "pipeline")
        self.git("commit", "-q", "-m", "x", "--allow-empty")

    def take(self, sid, freq, rt=0.6):
        write(os.path.join(self.d, "Audio", "Source", sid, f"SW_{sid}_00.wav"), [tone(freq, rt)])

    def run_loop(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = audio_loop.main([args[0], "--card", "UE-40", "--root", self.d, *args[1:]])
        return rc, buf.getvalue()

    def start(self):
        rc, o = self.run_loop("start", "--issue", "40", "--ids", "UiMove", "--builder", "builder-1")
        self.assertEqual(rc, 0, o)

    def test_packet_is_blind(self):
        self.take("UiMove", 2500)
        self.start()
        rc, o = self.run_loop("round", "--piece", "UiMove")
        self.assertEqual(rc, 0, o)
        pk = re.search(r"CRITIC PACKET: (\S+)", o).group(1)
        files = sorted(os.listdir(pk))
        self.assertEqual(files, ["R1.png", "R1.wav", "X_00.png", "X_00.wav", "brief.md"])
        brief = open(os.path.join(pk, "brief.md")).read()
        for leak in ("UiMove", "UiBack", "builder-1", "round", "SW_"):
            self.assertNotIn(leak, brief.replace("Round", ""))
        self.assertIn("a soft escapement tick", brief)
        self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(pk), "key.json")), "the key stays outside")

    def test_loop_packet_has_no_one_shot_ranges(self):
        """A loop is never judged on attack_ms / decay_s: audio_style_check does not apply them to a loop, so the
        packet neither lists those ranges nor prints those numbers, and says the sound is a loop. A one-shot keeps them."""
        self.take("WindZoneLoop", 600, rt=2.0)       # sound-list kind loop, style family wind (ranges attack_ms, decay_s)
        self.take("UiMove", 2500)
        rc, o = self.run_loop("start", "--issue", "40", "--ids", "WindZoneLoop,UiMove", "--builder", "builder-1")
        self.assertEqual(rc, 0, o)
        briefs = {}
        for sid in ("WindZoneLoop", "UiMove"):
            rc, o = self.run_loop("round", "--piece", sid)
            self.assertEqual(rc, 0, o)
            briefs[sid] = open(os.path.join(re.search(r"CRITIC PACKET: (\S+)", o).group(1), "brief.md")).read()
        loop = briefs["WindZoneLoop"]
        self.assertIn("Kind: a seamless loop", loop)
        self.assertNotIn("attack_ms", loop.split("Kind: a seamless loop")[0])
        self.assertNotRegex(loop, r"(attack_ms|decay_s)\s*[=\d-]")       # no range, no measured number
        self.assertRegex(loop, r"centroid_hz 150\.\.2800")                # the ranges that do apply are still there
        self.assertNotIn("WindZoneLoop", loop)
        self.assertRegex(briefs["UiMove"], r"decay_s 0\.2\.\.2\.0")
        self.assertRegex(briefs["UiMove"], r"decay_s=")
        self.assertNotIn("seamless loop", briefs["UiMove"].split("Brand rules")[0])

    def test_full_loop_closes_and_check_pr_accepts_it(self):
        self.take("UiMove", 400)                      # too dark: fails the measured check
        self.start()
        self.run_loop("round", "--piece", "UiMove")
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "critic-1", "--verdict", "fail",
                              "--gap", "it sounds like a low thud, not a bright escapement tick")
        self.assertEqual(rc, 1, o)
        self.take("UiMove", 2500)                     # the builder revises
        self.run_loop("round", "--piece", "UiMove")
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "critic-2", "--verdict", "pass")
        self.assertEqual(rc, 0, o)
        rc, o = self.run_loop("close")
        self.assertEqual(rc, 1, "broken on purpose: the takes are not committed yet\n" + o)
        self.assertIn("uncommitted", o)
        self.commit()
        rc, o = self.run_loop("close")
        self.assertEqual(rc, 0, o)
        sha = self.git("rev-parse", "HEAD").strip()[:12]
        self.assertIn(f"audio_loop close: PASS card=UE-40 pieces=1 commit={sha}", o)
        body = (f"## Task\nPart of #40. Card ID: UE-40\n## What changed\nAudio/Source/UiMove/SW_UiMove_00.wav\n"
                f"## Evidence\ncommit={sha} engine=none config=none host=mac run=none\n{o}")
        s = check_pr.sections(body)
        self.assertEqual(check_pr.audio_problems(s, []), [])
        # broken on purpose: stale commit, critic = builder, a missing piece, a FAIL line
        stale = check_pr.sections(body.replace(f"commit={sha} engine", "commit=abcdef123456 engine"))
        self.assertTrue(check_pr.audio_problems(stale, []))
        same = check_pr.sections(body.replace("critic=critic-2", "critic=builder-1"))
        self.assertTrue(any("critic session is the builder's" in p for p in check_pr.audio_problems(same, [])))
        more = check_pr.audio_problems(s, ["Audio/Source/UiBack/SW_UiBack_00.wav"])
        self.assertTrue(any(p.startswith("UiBack: no `AUDIO LOOP: PASS") for p in more), more)
        failing = check_pr.sections(body + "\naudio_style check: FAIL files=1 commit=" + sha + "\n")
        self.assertTrue(any("not closed" in p for p in check_pr.audio_problems(failing, [])))
        self.assertEqual(check_pr.audio_problems(check_pr.sections(body.replace("Audio/Source/UiMove/SW_UiMove_00.wav",
                                                                               "docs/x.md")), []), [])
        # broken on purpose: the take changes after the critic passed it
        self.take("UiMove", 2600)
        self.commit()
        rc, o = self.run_loop("close")
        self.assertEqual(rc, 1, o)
        self.assertIn("not the ones the critic passed", o)

    def test_critic_must_be_separate_and_fresh(self):
        self.take("UiMove", 2500)
        self.start()
        self.run_loop("round", "--piece", "UiMove")
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "builder-1", "--verdict", "pass")
        self.assertEqual(rc, 2, o)
        self.assertIn("separate session", o)
        rc, _ = self.run_loop("verdict", "--piece", "UiMove", "--critic", "critic-1", "--verdict", "fail", "--gap", "x y")
        self.run_loop("round", "--piece", "UiMove")
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "critic-1", "--verdict", "pass")
        self.assertEqual(rc, 2, o)
        self.assertIn("fresh critic", o)
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "critic-2", "--verdict", "fail")
        self.assertEqual(rc, 2, "a fail names its biggest gap\n" + o)
        self.take("UiMove", 2700)
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "critic-2", "--verdict", "pass")
        self.assertEqual(rc, 2, o)
        self.assertIn("changed after the packet", o)

    def test_reply_json_pass_needs_every_row(self):
        self.take("UiMove", 2500)
        self.start()
        self.run_loop("round", "--piece", "UiMove")
        rows = {f"A{i}": [True, "ok"] for i in range(1, 9)}
        rows["A8"] = [False, "not on the bar"]
        rp = os.path.join(self.d, "reply.json")
        json.dump({"rows": rows, "verdict": "pass", "biggest_gap": "none"}, open(rp, "w"))
        rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", "c1", "--reply", rp)
        self.assertEqual(rc, 2, o)

    def test_stuck_after_three_rounds_without_improvement_then_resume(self):
        self.take("UiMove", 2500)
        self.start()
        gap = "the tail is far too long for a menu tick"
        codes = []
        for i in range(4):
            self.run_loop("round", "--piece", "UiMove")
            rc, o = self.run_loop("verdict", "--piece", "UiMove", "--critic", f"critic-{i}", "--verdict", "fail",
                                  "--gap", gap)
            codes.append(rc)
        self.assertEqual(codes, [1, 1, 1, 4], o)
        line = next(ln for ln in o.splitlines() if ln.startswith("NEEDS HUMAN:"))
        self.assertRegex(line, check_card.NEEDS_HUMAN)
        self.assertIn("Audio/Source/UiMove/SW_UiMove_00.wav", line)
        rc, o = self.run_loop("round", "--piece", "UiMove")
        self.assertEqual(rc, 2, "a stuck piece waits for the audio owner\n" + o)
        rc, o = self.run_loop("resume", "--piece", "UiMove", "--by", "audio-owner", "--note", "shorter, drier tick")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.run_loop("round", "--piece", "UiMove")[0], 0)

    def test_a_new_gap_or_a_better_number_is_progress(self):
        self.take("UiMove", 2500)
        self.start()
        codes = []
        for i in range(5):
            self.run_loop("round", "--piece", "UiMove")
            codes.append(self.run_loop("verdict", "--piece", "UiMove", "--critic", f"c{i}", "--verdict", "fail",
                                       "--gap", ["too loud attack", "wrong room size", "bell partial missing",
                                                 "needs more brass weight", "metallic ring too long"][i])[0])
        self.assertEqual(codes, [1] * 5)


class Placeholders(Loop):
    """A piece the audio API could not make (no key, an HTTP error, no credits left) is a tracked placeholder: close
    lists it as AUDIO PLACEHOLDER, check_pr takes that line only when the provenance says so, and kickoff's loop
    driver judges the other pieces with a fresh critic per round (tools/kickoff.py audio_loop_card)."""
    # the Loop fixture only, not its tests a second time
    test_packet_is_blind = test_full_loop_closes_and_check_pr_accepts_it = test_critic_must_be_separate_and_fresh = None
    test_reply_json_pass_needs_every_row = test_stuck_after_three_rounds_without_improvement_then_resume = None
    test_a_new_gap_or_a_better_number_is_progress = None

    def mark_placeholder(self, sid, reason="elevenlabs failed: HTTP 401 quota_exceeded"):
        path = os.path.join(self.d, "pipeline", "art", "provenance.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new = not os.path.isfile(path)
        with open(path, "a", encoding="utf-8") as fh:
            if new:
                fh.write("asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution\n")
            fh.write(f"Audio/Source/{sid}/SW_{sid}_00.wav,Audio agent,synthesized in jam; placeholder: {reason},"
                     "Procedural synthesis (tools/assetgen.py synth),none,x,,,2026-11-12,CC0,none\n")

    def test_close_lists_a_placeholder_piece_and_check_pr_needs_its_provenance(self):
        self.take("UiMove", 2500)
        self.mark_placeholder("UiMove")
        self.commit()
        self.start()
        rc, o = self.run_loop("close")
        self.assertEqual(rc, 0, o)
        sha = self.git("rev-parse", "HEAD").strip()[:12]
        self.assertIn(f"AUDIO PLACEHOLDER: piece=UiMove takes=1 commit={sha}", o)
        self.assertNotIn("audio_style check: PASS files=0", o)
        body = (f"## Task\nPart of #40. Card ID: UE-40\n## What changed\nAudio/Source/UiMove/SW_UiMove_00.wav\n"
                f"## Evidence\ncommit={sha} engine=none config=none host=mac run=none\n{o}")
        self.assertEqual(check_pr.audio_problems(check_pr.sections(body), [], root=self.d), [])
        # broken on purpose: the same line for a take whose provenance is no placeholder
        os.remove(os.path.join(self.d, "pipeline", "art", "provenance.csv"))
        probs = check_pr.audio_problems(check_pr.sections(body), [], root=self.d)
        self.assertTrue(any(p.startswith("UiMove: no `AUDIO LOOP: PASS") for p in probs), probs)

    def test_kickoff_drives_the_critic_and_skips_placeholders(self):
        import kickoff
        self.take("UiMove", 400)                      # too dark: the first critic fails it
        self.mark_placeholder("UiBack")
        self.commit()
        rc, o = self.run_loop("start", "--issue", "40", "--ids", "UiMove,UiBack", "--builder", "builder-1")
        self.assertEqual(rc, 0, o)
        sessions, asks, failed = [], [], []
        boxes = tempfile.mkdtemp(dir=self.d)

        def session(card_id, role, cwd, box, prompt, env, review=False, critic=False):
            sessions.append((role, critic, os.path.basename(box)))
            if critic:
                ok = "X_00.wav" in os.listdir(cwd) and len([x for x in sessions if x[1]]) > 1
                rows = {f"A{i}": [ok, "r"] for i in range(1, 9)}
                with open(os.path.join(box, "reply.json"), "w") as fh:
                    json.dump({"rows": rows, "verdict": "pass" if ok else "fail",
                               "biggest_gap": "none" if ok else "a dull thud, not a bright tick", "basis": "spectrogram"}, fh)
            else:                                     # the builder revises the piece and commits
                self.take("UiMove", 2500)
                self.commit()
            return 0

        k = kickoff.Kickoff.__new__(kickoff.Kickoff)
        k.session, k.j, k.post_outbox, k.fulfil = session, lambda *a, **kw: None, lambda c, b: False, lambda c, b, w: False
        k.outbox = lambda name: tempfile.mkdtemp(prefix=name, dir=boxes)
        k.prompt = lambda *a, **kw: "revise"
        k.block = lambda c: asks.append("blocked")
        k.raise_ask = lambda *a, **kw: asks.append(a)
        k.session_failed = lambda c, cid, what, why, box=None, pr=None: failed.append(why) or "retry"
        card = type("C", (), {"key": "40", "number": 40, "body": "", "human": None, "owner_key": "audio"})()
        box = tempfile.mkdtemp(dir=self.d)
        self.assertIs(k.audio_loop_card(card, "UE-40", self.d, box, "ue-40-x"), True, failed)
        self.assertEqual([s[:2] for s in sessions], [("audio", True), ("audio", False), ("audio", True)],
                         "critic fails, the builder revises, a NEW critic passes; UiBack is never judged")
        self.assertNotEqual(sessions[0][2], sessions[2][2], "each round has its own critic session")
        self.assertEqual(asks, [])
        pr = open(os.path.join(box, "pr.md")).read()
        self.assertIn("audio_loop close: PASS card=UE-40 pieces=2", pr)
        self.assertIn("AUDIO LOOP: PASS piece=UiMove rounds=2", pr)
        self.assertIn("AUDIO PLACEHOLDER: piece=UiBack", pr)


if __name__ == "__main__":
    unittest.main()

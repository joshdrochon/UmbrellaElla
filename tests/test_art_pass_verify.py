"""A pass record is the panel run's output, never an agent's text (Josh, Nov 12).

tools/art_loop.py saves the panel's raw evidence next to the record; tools/build/art_pass_verify.py derives the verdict
from it again. Broken on purpose: a hand-written passing record, an edited vote (evidence only, and evidence plus its
manifest), a changed image, a record that changed without its evidence, an agent session writing records, a gate re-run
whose fresh critics pick the reference."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
sys.path.insert(0, HERE)
import art_inventory  # noqa: E402
import art_loop  # noqa: E402
import art_pass_verify  # noqa: E402
from png import write_png  # noqa: E402

PASS_CHECKS = (True, 0.9, [], {c: "pass" for c in art_loop.CHECKS})
KEEP_AGENT = {"JAM_ROLE": ""}


def honest(winner):
    """A stand-in critic that answers from the key: calibration folders right, the real pair `winner`
    ('SAME', 'ours' or 'reference')."""
    def ask(folder):
        with open(folder.rstrip("/\\") + ".key.json", encoding="utf-8") as fh:
            key = json.load(fh)
        lines = []
        for f in sorted(list(key["calibration"]) + [key["folder"]]):
            if f == key["folder"]:
                ans = "SAME" if winner == "SAME" else key["ours"] if winner == "ours" else \
                    ("Y" if key["ours"] == "X" else "X")
            else:
                ans = key["calibration"][f]
            lines.append(f"{f}: WINNER: {ans} | GAP: the paper grain")
        return "\n".join(lines) + "\n"
    return ask


class PanelRepo(unittest.TestCase):
    PIECE, CARD, IMG = "scene", "0.99", "Art/Scene.png"

    def setUp(self):
        self.env = mock.patch.dict(os.environ, KEEP_AGENT)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        # small images and a small references.json: the real team art takes minutes to decode in pure Python
        for rel, col in (("pipeline/art/reference/a.png", (200, 60, 40)), ("pipeline/art/reference/bar.png", (40, 60, 200)),
                         ("evals/art-judge/crude.png", (90, 90, 90))):
            full = os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            write_png(full, 12, 8, [[(col[0] + x, col[1] + y, col[2], 255) for x in range(12)] for y in range(8)])
        refs = {"references": [{"id": "ka", "path": "pipeline/art/reference/a.png", "kind": "image"},
                               {"id": "kbar", "path": "pipeline/art/reference/bar.png", "kind": "image"}],
                "elements": {}, "scene": {"what": "A paper stage. Enough.", "refs": ["ka"]},
                "quality_bar": {"refs": ["kbar"], "by_piece": {}, "default": "kbar"}}
        with open(os.path.join(self.root, "pipeline", "art", "references.json"), "w") as fh:
            json.dump(refs, fh)
        with open(os.path.join(self.root, "evals", "art-judge", "critic-calibration.json"), "w") as fh:
            json.dump({"crude": [{"file": "evals/art-judge/crude.png", "elements": ["scene"]}]}, fh)
        os.makedirs(os.path.join(self.root, "Art"))
        self.ours = os.path.join(self.root, self.IMG)
        write_png(self.ours, 16, 9, [[(30 + x, 20 + y, 15, 255) for x in range(16)] for y in range(9)])
        patcher = mock.patch.object(art_loop, "measure", lambda *a: PASS_CHECKS)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.refs, self.rh = art_loop.refs_and_hash(self.root)

    def panel(self, ask, rnd=1):
        """A real panel run through art_loop's own functions; the record it logs. Returns the round record."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        rec, items = art_loop.panel_run(self.root, self.CARD, self.PIECE, self.ours, tmp, rnd, ask, True, True, self.refs)
        art_loop.attach_evidence(self.root, self.CARD, self.PIECE, rec, items, self.rh)
        rec.pop("measure_lines", None)
        art_loop.write_critic_record(self.root, self.CARD, self.PIECE, rec, self.rh, "abc1234")
        return rec

    def records(self):
        return art_pass_verify.load_piece_records(self.root)[self.PIECE]

    def verify(self, **kw):
        return art_pass_verify.verify_record(self.root, self.PIECE, self.records()[-1], remeasure=False, **kw)

    def evidence(self):
        return os.path.join(self.root, self.records()[-1]["evidence"])

    def rewrite_record(self, **over):
        path = os.path.join(self.root, art_loop.CRITIC_DIR, self.PIECE + ".json")
        data = json.load(open(path))
        data["records"][-1].update(over)
        json.dump(data, open(path, "w"))


class RealPanelRun(PanelRepo):
    def test_a_real_panel_runs_saves_evidence_and_verifies(self):
        rec = self.panel(honest("SAME"))
        self.assertEqual(rec["verdict"], "same")
        self.assertTrue(rec["manifest"])
        ev = self.evidence()
        self.assertEqual(self.records()[-1]["evidence"], f"pipeline/art/critic/scene/{rec['round']}")
        man = json.load(open(os.path.join(ev, "manifest.json")))
        self.assertEqual(art_loop.file_sha256(os.path.join(ev, "manifest.json")), rec["manifest"])
        self.assertEqual(man["shipped"]["sha256"], art_loop.content_sha(self.ours))
        self.assertEqual(len(man["sessions"]), art_loop.PANEL * len(man["required"]))
        some = man["sessions"][0]
        self.assertIn("WINNER:", open(os.path.join(ev, "sessions", some + ".answer.md")).read())
        self.assertTrue(os.path.isfile(os.path.join(ev, "packets", some, "prompt.md")))
        self.assertEqual(man["prompt"], art_loop.prompt_id())
        self.assertEqual(self.verify(), [])
        self.assertEqual(art_pass_verify.check(self.root, remeasure=False), [])
        self.assertIn(self.PIECE, art_inventory.passed_pieces(None, self.root))

    def test_no_absolute_home_path_in_the_evidence(self):
        self.panel(honest("SAME"))
        for dp, _, names in os.walk(self.evidence()):
            for n in names:
                if n.endswith((".json", ".md")):
                    self.assertNotRegex(open(os.path.join(dp, n), errors="replace").read(), r"/Users/|/home/")

    def test_a_panel_the_critics_fail_has_no_evidence_and_no_pass(self):
        rec = self.panel(honest("reference"))
        self.assertEqual(rec["verdict"], "reference")
        self.assertFalse(rec.get("manifest"))
        self.assertEqual(art_pass_verify.verified_pieces(self.root), set())


class BrokenOnPurpose(PanelRepo):
    def test_a_hand_written_passing_record_fails(self):
        art_loop.write_critic_record(self.root, self.CARD, self.PIECE, {
            "round": 1, "verdict": "ours", "checks": True, "pairs": {"reference": "ours", "quality_bar": "ours"},
            "panel": 3, "calibration": {"sessions": 15, "passed": 15}, "sha": art_loop.content_sha(self.ours),
            "file": self.ours}, self.rh, "abc")
        lines = art_pass_verify.check(self.root, remeasure=False)
        self.assertTrue(any("no panel evidence" in x for x in lines), lines)
        self.assertEqual(art_inventory.passed_pieces(None, self.root), set())

    def test_hand_written_evidence_with_a_forged_manifest_still_fails_the_derivation(self):
        self.panel(honest("SAME"))
        ev = self.evidence()
        name = sorted(os.listdir(os.path.join(ev, "sessions")))[0]
        p = os.path.join(ev, "sessions", name)
        key = json.load(open(os.path.join(ev, "keys", name.replace(".answer.md", ".key.json"))))
        text = open(p).read()
        bad = "Y" if key["ours"] == "X" else "X"   # the reference wins this session
        open(p, "w").write(re.sub(r"(%s: WINNER: )\w+" % key["folder"], r"\g<1>" + bad, text))
        self.assertTrue(any("changed after the panel" in x for x in self.verify()))   # manifest hash catches the edit
        man_p = os.path.join(ev, "manifest.json")
        man = json.load(open(man_p))
        man["files"]["sessions/" + name] = art_loop.file_sha256(p)
        json.dump(man, open(man_p, "w"), indent=1, sort_keys=True)
        self.rewrite_record(manifest=art_loop.file_sha256(man_p))
        probs = self.verify()
        self.assertTrue(any("re-derived from the raw critic answers" in x for x in probs), probs)

    def test_an_edited_vote_fails(self):
        self.panel(honest("SAME"))
        ev = self.evidence()
        name = sorted(os.listdir(os.path.join(ev, "sessions")))[0]
        p = os.path.join(ev, "sessions", name)
        open(p, "a").write("\nWINNER: X\n")
        self.assertTrue(any("evidence file" in x and "changed" in x for x in self.verify()))

    def test_an_edited_record_fails(self):
        self.panel(honest("reference"))   # the record says reference; flip it to ours
        self.rewrite_record(verdict="ours", checks=True, manifest="0" * 64, evidence="pipeline/art/critic/scene/1")
        self.assertNotEqual(art_pass_verify.check(self.root, remeasure=False), [])

    def test_a_changed_image_fails(self):
        self.panel(honest("SAME"))
        write_png(self.ours, 16, 9, [[(200, 20, 15, 255)] * 16 for _ in range(9)])
        self.assertTrue(any("changed after its panel" in x for x in self.verify()))
        self.assertEqual(art_inventory.passed_pieces(None, self.root), set())

    def test_an_extra_or_missing_evidence_file_fails(self):
        self.panel(honest("SAME"))
        ev = self.evidence()
        open(os.path.join(ev, "sessions", "extra.answer.md"), "w").write("A: WINNER: SAME")
        self.assertTrue(any("not in the manifest" in x for x in self.verify()))
        os.remove(os.path.join(ev, "sessions", "extra.answer.md"))
        os.remove(os.path.join(ev, "sessions", sorted(os.listdir(os.path.join(ev, "sessions")))[0]))
        self.assertTrue(any("is missing" in x for x in self.verify()))

    def test_a_record_changed_without_its_evidence_fails(self):
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", self.root] + list(a),
                                        capture_output=True, text=True, check=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-q", "-m", "empty")   # base: nothing recorded
        self.panel(honest("SAME"))
        git("add", "-A")
        git("commit", "-q", "-m", "panel")
        base = git("rev-parse", "HEAD~1").stdout.strip()
        self.assertEqual(art_pass_verify.check(self.root, base, False), [])
        self.assertEqual(art_pass_verify.newly_passed(self.root, base), [self.PIECE])
        self.rewrite_record(gap="edited note")   # the record changed; no evidence file did
        git("add", "-A")
        git("commit", "-q", "-m", "tweak")
        lines = art_pass_verify.check(self.root, "HEAD~1", False)
        self.assertTrue(any("evidence files" in x and "did not" in x for x in lines), lines)

    def test_an_agent_session_cannot_write_records_or_run_the_panel(self):
        self.panel(honest("SAME"))
        with mock.patch.dict(os.environ, {"JAM_ROLE": "gameplay-dev"}):
            before = open(os.path.join(self.root, art_loop.CRITIC_DIR, "scene.json")).read()
            self.assertIsNone(art_loop.write_critic_record(self.root, "x", "scene", {"round": 9, "verdict": "ours"}))
            self.assertIsNone(art_loop.save_evidence(self.root, "x", "scene", {"round": 9}, [], "h"))
            self.assertEqual(before, open(os.path.join(self.root, art_loop.CRITIC_DIR, "scene.json")).read())
            rc = art_loop.main(["--root", self.root, "run", "--card", "x", "--piece", "scene", "--ours", self.ours])
            self.assertEqual(rc, 2)

    def test_the_hook_refuses_agent_writes_to_the_critic_folder(self):
        hook = os.path.join(ROOT, "pipeline", "agent-ops", "hook.py")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT, JAM_ROLE="gameplay-dev", AGENT_OPS_PLATFORM="linux")
        for tool, ti in (("Write", {"file_path": os.path.join(ROOT, "pipeline/art/critic/owl-bolt.json"), "content": "{}"}),
                         ("Write", {"file_path": os.path.join(ROOT, "pipeline/art/critic/owl-bolt/1/manifest.json"),
                                    "content": "{}"}),
                         ("Bash", {"command": "echo '{}' > pipeline/art/critic/owl-bolt/1/sessions/a.answer.md"})):
            with self.subTest(ti=ti):
                p = subprocess.run([sys.executable, hook, "guard"], input=json.dumps(
                    {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti, "cwd": ROOT}),
                    capture_output=True, text=True, env=env)
                self.assertEqual(p.returncode, 2, p.stderr)


class GateRerun(PanelRepo):
    def test_the_gates_fresh_panel_passes_a_genuine_pass(self):
        self.panel(honest("SAME"))
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        good, rec = art_loop.rerun(self.root, self.PIECE, tmp, honest("SAME"))
        self.assertTrue(good, rec)
        self.assertEqual(rec["panel"], art_loop.PANEL)
        self.assertEqual(os.listdir(os.path.join(self.root, "pipeline/art/critic/scene")), ["1"])   # nothing written

    def test_the_gates_fresh_panel_fails_a_forged_pass(self):
        self.panel(honest("SAME"))   # a record whose evidence says the critics passed it
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        good, rec = art_loop.rerun(self.root, self.PIECE, tmp, honest("reference"))
        self.assertFalse(good)
        self.assertEqual(rec["verdict"], "reference")


class Wiring(unittest.TestCase):
    def text(self, rel):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_gate_quality_gate_and_prepackage_run_the_verifier_as_blocking(self):
        gate = self.text("tools/build/gate.sh")
        self.assertIn('chk art_pass_verify python3 tools/build/art_pass_verify.py check --base "$MAIN"', gate)
        self.assertIn("art_loop.py gate-rerun", gate)
        self.assertIn("newly-passed", gate)
        sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
        import quality_gate
        self.assertIn("art_pass_verify", quality_gate.BLOCKING)
        self.assertIn("art_pass_verify.py", self.text("tools/build/prepackage.sh"))

    def test_critic_folder_is_kickoff_only_in_gates(self):
        gates = json.loads(self.text("pipeline/agent-ops/gates.json"))
        self.assertIn("pipeline/art/critic/**", gates["kickoff_only_paths"])

    def test_the_repository_records_verify(self):
        self.assertEqual(art_pass_verify.check(ROOT, remeasure=False), [])


if __name__ == "__main__":
    unittest.main()

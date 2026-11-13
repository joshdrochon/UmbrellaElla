"""The story gate: tools/story_check.py (machine half), the blind critic's STORY_CRITIC line, check_pr rule story,
check_card rule story and the human-only grace kind for story canon. Each rule is also broken on purpose: a planted
bad line, a stripped deny term, a stale hash or a missing critic line must turn the check red."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import check_card  # noqa: E402
import check_pr  # noqa: E402
import manifest_check  # noqa: E402
import story_check as sc  # noqa: E402
import hermetic  # noqa: E402  read-only-safe rmtree (Windows)

BIBLE = os.path.join(ROOT, sc.BIBLE)
RULES = os.path.join(ROOT, sc.RULES)


def bible():
    return sc.parse_bible(sc.read_text(BIBLE))


def rules():
    return sc.load_rules(RULES)


def row(text, surface="screen", facts="", ship="no", rid="X.1"):
    return {"id": rid, "surface": surface, "text": text, "facts": facts, "ship": ship, "note": "", "_n": 2}


def kinds(text, nar_ok=False, **kw):
    return {k for k, _, _ in sc.line_problems([row(text, **kw)], bible(), rules(), nar_ok)}


class RepoStoryFilesPass(unittest.TestCase):
    def test_bible_and_lines_pass(self):
        found, bh, sh, n, b = sc.run(ROOT, BIBLE, os.path.join(ROOT, sc.LINES), RULES, os.path.join(ROOT, sc.MANIFEST))
        self.assertEqual(found, [])
        self.assertRegex(bh + sh, r"^[0-9a-f]{16}$")

    def test_calibration_set_fails_where_it_should(self):
        probs, n = sc.calibrate(os.path.join(ROOT, sc.CALIBRATION), rules(), bible())
        self.assertEqual(probs, [])
        self.assertGreaterEqual(n, 20)

    def test_calibration_catches_a_checker_with_the_deny_list_stripped(self):
        broken = dict(rules(), deny=[d for d in rules()["deny"] if d["term"] not in ("Strixon", "Mary Poppins")])
        probs, _ = sc.calibrate(os.path.join(ROOT, sc.CALIBRATION), broken, bible())
        self.assertTrue(any("bad-deny" in p for p in probs), probs)
        self.assertTrue(any("bad-trademark" in p for p in probs), probs)

    def test_strixon_is_denied_and_nar_is_authorized(self):
        self.assertIn("Strixon", [d["term"] for d in rules()["deny"]])
        self.assertTrue(sc.nar_authorized(os.path.join(ROOT, sc.MANIFEST)))   # SH1.0 NAR-* records are authorized
        names = {n["name"]: n["status"] for n in bible()["names"]}
        self.assertEqual(names["Keeper of Time"], "PROPOSED")       # the owl's title is a proposal, not canon
        self.assertTrue(all(f["status"] != "GDD" for fid, f in bible()["facts"].items() if fid.startswith("P")))


class BibleBrokenOnPurpose(unittest.TestCase):
    def problems(self, old, new):
        text = sc.read_text(BIBLE)
        self.assertIn(old, text)
        return sc.bible_problems(sc.parse_bible(text.replace(old, new, 1)), rules())

    def test_deny_term_as_a_name_fails(self):
        p = self.problems("| the owl | opponent |", "| Strixon | opponent |")
        self.assertIn("deny", {k for k, _, _ in p})

    def test_never_use_must_list_every_deny_term(self):
        p = self.problems("Today: Strixon (undecided owl name,", "Today: (undecided owl name,")
        self.assertTrue(any("does not list" in m for _, _, m in p), p)

    def test_story_chat_row_marked_gdd_fails(self):
        p = self.problems("a life she does not know she was meant to lose. | PROPOSED | S3 (the post's closing line) |",
                          "a life she does not know she was meant to lose. | GDD | S3 (the post's closing line) |")
        self.assertTrue(any("cites a GDD source" in m for _, _, m in p), p)

    def test_self_confirmed_status_word_fails(self):
        p = self.problems("| Keeper of Time | epithet for the owl | PROPOSED |", "| Keeper of Time | epithet for the owl | CONFIRMED |")
        self.assertTrue(any("status 'CONFIRMED'" in m for _, _, m in p), p)

    def test_contradiction_needs_its_gdd_fact(self):
        p = self.problems("| F3 | The owl cannot be killed.", "| F9 | The owl cannot be killed.")
        self.assertTrue(any("needs a GDD row F3" in m for _, _, m in p), p)

    def test_bad_regex_and_missing_section_fail(self):
        self.assertTrue(self.problems("\\b(?:evil\\|wicked)", "\\b(?:evil\\|wicked"))
        self.assertTrue(any("Tone target" in m for _, _, m in self.problems("## Tone target", "## Voice")))


class LinesBrokenOnPurpose(unittest.TestCase):
    def test_good_lines_pass(self):
        self.assertEqual(kinds("Play", surface="button"), set())
        self.assertEqual(kinds("Press Esc to pause.", surface="prompt"), set())
        self.assertEqual(kinds("The owl departs. Ella is still in the air.", surface="end_card", facts="F3"), set())
        self.assertEqual(kinds("The owl departs. She is still in the air.", surface="end_card", facts="F3",
                               ship="yes", nar_ok=True), set())
        # Ella is CONFIRMED (agent default, D-new-story-canon): her name ships
        self.assertEqual(kinds("The owl departs. Ella is still in the air.", surface="end_card", facts="F3",
                               ship="yes", nar_ok=True), set())
        # a still-PROPOSED fact (P9) never ships
        self.assertIn("ship", kinds("Her mother defied death out of love.", surface="intro_card", facts="P9",
                                    ship="yes", nar_ok=True))

    def test_each_rule_fails_its_line(self):
        cases = [
            ("deny", dict(text="Strixon waits above.", surface="screen")),
            ("deny", dict(text="Ella flies like Mary Poppins.", surface="screen")),
            ("banned", dict(text="Awesome run.", surface="screen")),
            ("exclaim", dict(text="You survived!", surface="screen")),
            ("caps", dict(text="RETRY NOW", surface="button")),
            ("emoji", dict(text="Survived \U0001F989", surface="screen")),
            ("length", dict(text="one two three four five", surface="title")),
            ("name", dict(text="Ella calls for Tomas below.", surface="screen")),
            ("contradiction", dict(text="Ella kills the owl at dawn.", surface="end_card", facts="F3")),
            ("contradiction", dict(text="Close the umbrella to rise.", surface="tooltip")),
            ("contradiction", dict(text="The evil owl waits.", surface="screen")),
            ("fact", dict(text="The hand is gone.", surface="clue")),
            ("fact", dict(text="The hand is gone.", surface="clue", facts="Z9")),
            ("ship", dict(text="Her mother defied death out of love.", surface="intro_card", facts="P9", ship="yes")),
            ("ship", dict(text="Umbrella Ella", surface="title", ship="yes")),
            ("nar", dict(text="The owl departs.", surface="end_card", facts="F3", ship="yes")),
            ("surface", dict(text="Hello there.", surface="poster")),
        ]
        for want, kw in cases:
            with self.subTest(want=want, text=kw["text"]):
                self.assertIn(want, kinds(**kw))

    def test_csv_shape(self):
        rows, probs = sc.read_lines("id,surface,text\n")
        self.assertTrue(probs)
        rows, probs = sc.read_lines("id,surface,text,facts,ship,note\nA,button,Play,,maybe,\nA,button,Quit,,no,\n")
        got = sc.line_problems(rows, bible(), rules(), False)
        self.assertTrue(any("ship 'maybe'" in m for _, _, m in got))
        self.assertTrue(any("duplicate id" in m for _, _, m in got))


class ScanTableCritic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_scan_string_table_and_page(self):
        good = self.write("ST_UI.csv", "Key,SourceString\nTitle.Play,Play\nPause.Resume,Resume\n")
        bad = self.write("ST_bad.csv", "Key,SourceString\nTitle.Play,Play with Strixon\nFail.Text,GAME OVER!\n")
        page = self.write("page.md", "Short description: like Mary Poppins in the dark\n")
        self.assertEqual(sc.scan_problems([good], rules(), bible()), ([], 2))
        got = {k for k, _, _ in sc.scan_problems([bad], rules(), bible())[0]}
        self.assertTrue({"deny", "exclaim", "caps", "banned"} <= got, got)
        self.assertIn("deny", {k for k, _, _ in sc.scan_problems([page], rules(), bible())[0]})
        self.assertEqual(sc.scan_problems([os.path.join(ROOT, "pipeline/submission/itch-page.md")], rules(), bible())[0], [])

    def test_table_matches_lines(self):
        rows, _ = sc.read_lines("id,surface,text,facts,ship,note\nTitle.Play,button,Play,,no,\n")
        self.assertEqual(sc.table_problems(self.write("a.csv", "Key,SourceString\nTitle.Play,Play\n"), rows)[0], [])
        self.assertTrue(sc.table_problems(self.write("b.csv", "Key,SourceString\nTitle.Play,Start\n"), rows)[0])
        self.assertTrue(sc.table_problems(self.write("c.csv", "Key,SourceString\nTitle.Quit,Quit\n"), rows)[0])

    def test_critic_line(self):
        r = rules()
        ok = "STORY_CRITIC: PASS lines=3 bible=aaaaaaaa sheet=bbbbbbbb rubric=story-rubric/1 cycle=2 builder=s1 critic=s2"
        self.assertEqual(sc.critic_problems(ok, r, "aaaaaaaa", "bbbbbbbb", 3), [])
        # D-new-no-round-cap: no cycle cap. Broken on purpose if someone adds one back: cycle 40 is well formed
        self.assertEqual(sc.critic_problems(ok.replace("cycle=2", "cycle=40"), r, "aaaaaaaa", "bbbbbbbb", 3), [])
        for old, new in [("bible=aaaaaaaa", "bible=cccccccc"), ("critic=s2", "critic=s1"), ("cycle=2", "cycle=0"),
                         ("PASS", "FAIL"), ("story-rubric/1", "story-rubric/0"), ("lines=3", "lines=2")]:
            with self.subTest(break_=new):
                self.assertTrue(sc.critic_problems(ok.replace(old, new), r, "aaaaaaaa", "bbbbbbbb", 3))
        self.assertTrue(sc.critic_problems("critic says fine", r, "aaaaaaaa", "bbbbbbbb", 3))


class StuckRule(unittest.TestCase):
    """D-new-no-round-cap: the story loop has no cycle cap; it asks Richard only after 3 FAIL cycles in a row with the
    same false rows and no fewer of them."""

    def answer(self, verdict, *falses, cycle=1):
        rows = []
        for lid in ("Title.Play", "Card.Open"):
            rows.append(f"{lid}: " + " | ".join(f"S{i} false \"x\" (Tone target)" if (lid, f"S{i}") in falses
                                                 else f"S{i} true" for i in range(1, 9)))
        return "\n".join(rows) + (f"\nSTORY_CRITIC: {verdict} lines=2 bible=aaaaaaaa sheet=bbbbbbbb "
                                  f"rubric=story-rubric/1 cycle={cycle} builder=s1 critic=s{cycle + 1}\n")

    def test_stuck_only_after_three_flat_fails(self):
        same = self.answer("FAIL", ("Title.Play", "S3"))
        self.assertEqual(sc.critic_round(same), ("FAIL", [("Title.Play", "S3")]))
        self.assertTrue(sc.stuck([sc.critic_round(same)] * 3))
        self.assertFalse(sc.stuck([sc.critic_round(same)] * 2), "two cycles are not enough")
        better = [self.answer("FAIL", ("Title.Play", "S3"), ("Card.Open", "S5")), same, same]
        self.assertFalse(sc.stuck([sc.critic_round(a) for a in better]), "fewer false rows is an improvement")
        moved = [same, self.answer("FAIL", ("Card.Open", "S5")), same]
        self.assertFalse(sc.stuck([sc.critic_round(a) for a in moved]), "a different gap is not the same gap")
        # broken on purpose if someone adds a cap: 30 cycles that keep changing never escalate
        many = [sc.critic_round(self.answer("FAIL", (("Title.Play", "Card.Open")[i % 2], f"S{1 + i % 8}")))
                for i in range(30)]
        self.assertFalse(sc.stuck(many))

    def test_cli_exit_codes(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        files = []
        for i in range(3):
            f = os.path.join(d, f"c{i}.txt")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(self.answer("FAIL", ("Title.Play", "S3"), cycle=i + 1))
            files.append(f)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sc.main(["--stuck"] + files), 4, out.getvalue())
        self.assertIn("story_check: STUCK", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sc.main(["--stuck"] + files[:2]), 0)
        self.assertIn("not stuck", out.getvalue())


class CheckPrStoryRule(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        for rel in (sc.BIBLE, sc.LINES, sc.RULES):
            os.makedirs(os.path.dirname(os.path.join(self.root, rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(self.root, rel))
        b = sc.sha8(sc.read_text(os.path.join(self.root, sc.BIBLE)))
        s = sc.sha8(sc.read_text(os.path.join(self.root, sc.LINES)))
        self.pass_line = f"story_check: PASS bible={b} sheet={s} lines=0 names=8 facts=18"
        self.critic = (f"STORY_CRITIC: PASS lines=0 bible={b} sheet={s} rubric=story-rubric/1 cycle=1 "
                       "builder=2026-11-12T10:00 critic=2026-11-12T10:20")

    def tearDown(self):
        hermetic.rmtree(self.root)

    def probs(self, evidence, changed=("pipeline/story/lines.csv",), base=None):
        s = {"Evidence": evidence, "What changed": ""}
        return check_pr.story_problems(s, list(changed), self.root, base)

    def test_both_lines_pass(self):
        self.assertEqual(self.probs(self.pass_line + "\n" + self.critic), [])
        self.assertEqual(self.probs("nothing", changed=("docs/balance.md",)), [])

    def test_broken_evidence_fails(self):
        cases = {
            "no critic": self.pass_line,
            "no check": self.critic,
            "critic FAIL last": self.pass_line + "\n" + self.critic + "\n" + self.critic.replace("PASS", "FAIL"),
            "same session": self.pass_line + "\n" + self.critic.replace("critic=2026-11-12T10:20", "critic=2026-11-12T10:00"),
            "cycle 0": self.pass_line + "\n" + self.critic.replace("cycle=1", "cycle=0"),
            "check FAIL": "story_check: FAIL 2 problem(s)\n" + self.pass_line + "\n" + self.critic,
            "critic on another version": self.pass_line + "\n"
            + self.critic.replace("sheet=" + self.critic.split("sheet=")[1][:8], "sheet=00000000"),
        }
        for name, ev in cases.items():
            with self.subTest(name):
                self.assertTrue(self.probs(ev), name)

    def test_no_cycle_cap(self):
        """D-new-no-round-cap: a PASS on cycle 12 is accepted (the old D21 cap refused cycle 4)."""
        self.assertEqual(self.probs(self.pass_line + "\n" + self.critic.replace("cycle=1", "cycle=12")), [])

    def test_stale_hash_after_an_edit_fails(self):
        with open(os.path.join(self.root, sc.LINES), "a", encoding="utf-8") as fh:
            fh.write("Title.Play,button,Play,,no,\n")
        self.assertTrue(any("stale" in p for p in self.probs(self.pass_line + "\n" + self.critic)))

    def test_string_table_and_page_need_a_scan_pass(self):
        for path in check_pr.STORY_TEXT_FILES:
            with self.subTest(path):
                self.assertTrue(self.probs("nothing pasted", changed=(path,)))
                self.assertEqual(self.probs("story_check: PASS scan files=1 strings=12", changed=(path,)), [])

    def test_newly_confirmed_row_needs_richards_line(self):
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        run = lambda *a: subprocess.run(["git", *a], cwd=self.root, env=env, capture_output=True, check=True)  # noqa: E731
        run("init", "-q")
        run("add", "-A")
        run("commit", "-qm", "base")
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True).stdout.strip()
        p = os.path.join(self.root, sc.BIBLE)
        text = sc.read_text(p).replace("| P1 | Ella was meant to die.", "| P1 | Ella was meant to die.", 1)
        text = text.replace("lose. | PROPOSED | S3 (the", "lose. | CONFIRMED 2026-11-12 (Richard) | S3 (the", 1)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        b = sc.sha8(sc.read_text(p))
        ev = (self.pass_line.replace(self.pass_line.split("bible=")[1][:8], b) + "\n"
              + self.critic.replace(self.critic.split("bible=")[1][:8], b))
        changed = ("pipeline/story/story-bible.md",)
        self.assertTrue(any("STORY CONFIRM" in x for x in self.probs(ev, changed, base)))
        self.assertTrue(any("STORY CONFIRM" in x for x in self.probs(ev + "\nSTORY CONFIRM: by=Josh P9", changed, base)))
        self.assertEqual(self.probs(ev + "\nSTORY CONFIRM: by=Richard P9", changed, base), [])


class StoryCardsAndHumans(unittest.TestCase):
    def test_story_day0_cards_need_both_lines(self):
        from test_day0_cards import day0_rows, file_card
        rows = {r[0]: r for r in day0_rows()}
        for n in ("0.34", "0.35", "0.36"):   # renumbered from 0.29-0.31 (the encounter cards hold those)
            with self.subTest(card=n):
                self.assertTrue(rows[n][2].startswith("Story"))
                body, title = file_card(rows[n])
                self.assertEqual(check_card.problems(body, ROOT, title), [])
                broken = body.replace("STORY_CRITIC: PASS", "critic said ok")   # broken on purpose
                self.assertIn("story", {k for k, _ in check_card.problems(broken, ROOT, title)})

    def test_story_canon_is_never_a_grace_default(self):
        self.assertIsNotNone(manifest_check.grace_kind("confirm story canon P1-P10 https://github.com/x/y/issues/9"))
        self.assertIsNotNone(manifest_check.grace_kind("pick the owl's name"))
        self.assertIsNone(manifest_check.grace_kind("tuning card inside the approved range"))

    def test_story_role_is_wired(self):
        with open(os.path.join(ROOT, "pipeline/agent-ops/gates.json"), encoding="utf-8") as fh:
            gates = json.load(fh)
        self.assertEqual(gates["roles"]["story"], "Story")
        self.assertIn("pipeline/story/story.json", gates["gate_paths"])
        self.assertIn("Story", check_card.roles(ROOT))
        with open(os.path.join(ROOT, "pipeline/human-checkpoints.md"), encoding="utf-8") as fh:
            self.assertIn("Confirm story canon", fh.read())


if __name__ == "__main__":
    unittest.main()

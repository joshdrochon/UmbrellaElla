"""Tests for tools/check_card.py (Producer's task-card linter). Each broken_* fixture is a good
card with one thing broken on purpose; the linter must catch it with the right kind, and the
good cards (template shape and issue-form shape) must pass."""
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_card  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "cards")
# The good cards build MOVE-13 and HAZ-19 (GDD SH1.0, APPROVED_P0). The fixture manifest is the real one plus a few
# non-P0 records (UMB-03 PROPOSED, HAZ-01 experiment ticket #7) so the Hook only and experiment rules can be checked.
SIGNED = os.path.join(HERE, "fixtures", "manifest", "signed_off.json")


def setUpModule():
    check_card.MANIFEST_PATH = SIGNED


def tearDownModule():
    check_card.MANIFEST_PATH = None
TITLE = "[UE-031] Spikes damage Ella"

# fixture -> problem kinds that must all appear (and nothing outside this set)
BROKEN = {
    "broken_empty_field": {"field"},
    "broken_missing_field": {"field"},
    "broken_placeholder": {"field"},
    "broken_template_id": {"field", "id"},
    "broken_mvp_unknown": {"mvp"},
    "broken_owner_not_a_role": {"owner"},
    "broken_owner_is_reviewer": {"owner"},
    "broken_no_lane": {"lane"},
    "broken_lane_whole_repo": {"lane"},
    "broken_vague_done": {"done"},
    "broken_form_no_response": {"field"},
}


def card(name):
    with open(os.path.join(FIX, name + ".md"), encoding="utf-8") as f:
        return f.read()


def kinds(body, title=None):
    return {k for k, _ in check_card.problems(body, ROOT, title)}


class CheckCardTests(unittest.TestCase):
    def test_good_template_card_passes(self):
        self.assertEqual(check_card.problems(card("good_template")), [])

    def test_good_issue_form_card_passes(self):
        self.assertEqual(check_card.problems(card("good_form"), title=TITLE), [])

    def test_each_broken_card_is_caught(self):
        for name, want in BROKEN.items():
            with self.subTest(card=name):
                self.assertEqual(kinds(card(name), TITLE), want)

    def test_form_without_each_new_field_fails(self):
        # Player outcome, Out of scope, Used by, Needs were added to the issue form; dropping any one fails.
        body = card("good_form")
        for label in ("Player outcome", "Out of scope", "Used by", "Needs", "Context"):
            with self.subTest(field=label):
                broken = body.replace("### " + label, "### Removed " + label)
                self.assertIn(("field", f"missing field '{label}'"), check_card.problems(broken, ROOT, TITLE))

    def test_issue_form_has_every_field_the_linter_reads(self):
        with open(os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "task.yml"), encoding="utf-8") as f:
            labels = re.findall(r'label:\s*"?([^"\n]+)', f.read())
        for prefix, _ in check_card.FORM_LABELS:
            with self.subTest(field=prefix):
                self.assertTrue(any(lb.startswith(prefix) for lb in labels), prefix)

    # Dry run 2, H8: the form must offer every role the Day-0 table and AGENTS.md use
    @staticmethod
    def form_options(text, field_id):
        block = text.split(f"id: {field_id}\n", 1)[1]
        return [o.strip() for o in re.search(r"options:\s*\[(.*?)\]", block).group(1).split(",")]

    def missing_roles(self, text):
        owners, reviewers = self.form_options(text, "owner"), self.form_options(text, "reviewer")
        out = [r for r in check_card.roles(ROOT) if r not in owners]
        with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as f:
            for line in f:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 4 and re.fullmatch(r"0\.\d+[a-z]?", cells[0]):
                    rev = cells[3]
                    if rev not in reviewers:
                        out.append(rev)
        return sorted(set(out))

    def test_issue_form_offers_every_role(self):
        with open(os.path.join(ROOT, ".github", "ISSUE_TEMPLATE", "task.yml"), encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(self.missing_roles(text), [])
        broken = text.replace(", Level Designer, UI and UX, Agent Ops]", "]")
        self.assertEqual(self.missing_roles(broken), ["Agent Ops", "Level Designer", "UI and UX"])

    def test_untouched_template_fails_on_many_fields(self):
        with open(os.path.join(ROOT, "pipeline", "templates", "task-card.md"), encoding="utf-8") as f:
            block = f.read().split("```")[1]
        found = check_card.problems(block)
        self.assertGreaterEqual(len([k for k, _ in found if k == "field"]), 10, found)

    def test_vague_line_with_a_number_is_allowed(self):
        body = card("good_template").replace("  - [ ] tools/ue/build.sh exits 0 and the log is attached",
                                             "  - [ ] float feels right: apex height 180-220 uu after 1.0 s open")
        self.assertEqual(check_card.problems(body), [])

    def test_vague_line_mixed_with_good_lines_is_still_rejected(self):
        body = card("good_template").replace("  - [ ] tools/ue/build.sh exits 0 and the log is attached",
                                             "  - [ ] the umbrella looks good")
        self.assertEqual(kinds(body), {"done"})

    def test_broken_mvp_card_from_the_dry_run_is_caught(self):
        # Dry-run finding: GDD ref none, Player outcome none, a Game Designer reviewing C++, a .umap and
        # Config/ in the lane with no lock and no SMOKE_OK all passed with 0 problems.
        base = card("good_template")
        cases = {
            "gdd none": (base.replace(base.split("\n")[3], "GDD ref:       none"), "field"),
            "outcome none": (base.replace(base.split("\n")[4], "Player outcome: none"), "field"),
            "source reviewer": (base.replace("Reviewer role: Dev Lead", "Reviewer role: Game Designer"), "owner"),
            "umap unlocked": (base.replace("Source/UmbrellaElla/Private/Tests/Umbrella*",
                                           "Source/UmbrellaElla/Private/Tests/Umbrella*, Content/UmbrellaElla/Maps/L_Graybox.umap"), "lane"),
            "config no smoke": (base.replace("Source/UmbrellaElla/Private/Tests/Umbrella*",
                                             "Source/UmbrellaElla/Private/Tests/Umbrella*, Config/DefaultGame.ini"), "done"),
        }
        for name, (body, kind) in cases.items():
            with self.subTest(case=name):
                self.assertIn(kind, kinds(body))
        self.assertEqual(kinds(base.replace("MVP item:      2", "MVP item:      Day 0")
                                   .replace(base.split("\n")[3], "GDD ref:       none")
                                   .replace("Features:      MOVE-13", "Features:      none")), set())

    def test_mvp_alternatives(self):
        base = card("good_template")
        self.assertEqual(kinds(base.replace("MVP item:      2", "MVP item:      Day 0")
                               .replace("Features:      MOVE-13", "Features:      none")), set())
        self.assertEqual(kinds(base.replace("MVP item:      2", "MVP item:      Day 0")), {"mvp"}, "dry run A M8")
        # GDD SH1.0 approves everything as P0: the brief's stretch list is "none", so no Stretch item exists
        gust = base.replace("MVP item:      2", "MVP item:      Stretch: owl gust").replace(
            "Features:      MOVE-13", "Features:      OWL-02 Hook only")
        self.assertEqual(kinds(gust), {"mvp"})
        self.assertEqual(kinds(base.replace("MVP item:      2", "MVP item:      Stretch: jetpack")), {"mvp"})
        self.assertEqual(kinds(base.replace("MVP item:      2", "MVP item:      soon")), {"mvp"})

    def test_mvp_item_must_match_its_features(self):
        # dry run B M4: a card with MVP 10 (shield) and COM-01 (attack) passed
        base = card("good_template")  # MVP 2 = the movement IDs; Features MOVE-13
        self.assertEqual(kinds(base), set())
        self.assertEqual(kinds(base.replace("MVP item:      2", "MVP item:      10")), {"mvp"})   # 10 = enemies
        mf = check_card.mvp_features(ROOT)
        self.assertEqual(mf[10], {f"COM-{n}" for n in range(12, 19)} | {"ART-10", "ANIM-08"})
        self.assertLessEqual({f"OWL-{n:02d}" for n in range(6, 36)}, mf[5], "a range names every ID in it")
        self.assertEqual(check_card.line_features("OWL-06..OWL-08, COM-05"), {"OWL-06", "OWL-07", "OWL-08", "COM-05"})

    def test_p0_card_is_never_hook_only_or_stretch(self):
        """Dry run B H5 / A M1: an APPROVED_P0 ID is built in full on an MVP card."""
        base = card("good_template")  # MVP 2, Features MOVE-13 (APPROVED_P0), Cut tier MVP
        self.assertEqual(kinds(base), set())
        breaks = {
            "hook only": base.replace("Features:      MOVE-13", "Features:      MOVE-13 Hook only"),
            "stretch with a P0": base.replace("MVP item:      2", "MVP item:      Stretch: owl gust"),
            "stretch cut tier": base.replace("Cut tier:      MVP", "Cut tier:      Stretch-3"),
            "day 0 with a P0": base.replace("MVP item:      2", "MVP item:      Day 0"),
        }
        for name, body in breaks.items():
            with self.subTest(name):
                got = check_card.problems(body)
                self.assertTrue(any("APPROVED_P0" in why for _, why in got), got)

    def test_p0_cut_tier_on_the_issue_form(self):
        """Dry run B H2: the form puts budget and tier in one field; a Stretch tier on a P0 card fails there too."""
        base = card("good_form").replace("HAZ-19", "HAZ-20, HAZ-21")
        self.assertIn("HAZ-20, HAZ-21", base)
        check_card.MANIFEST_PATH = None   # the real manifest: every GDD SH1.0 Rule ID is APPROVED_P0
        self.addCleanup(setattr, check_card, "MANIFEST_PATH", SIGNED)
        self.assertFalse([w for _, w in check_card.problems(base) if "Cut tier" in w], "an honest MVP tier passes")
        for tier in ("Stretch-1", "Stretch cut", "stretch", "MVP?", "mvp"):
            with self.subTest(tier):
                body = base.replace("60 min agent + 15 min human, MVP", "60 min agent + 15 min human, " + tier)
                self.assertTrue(any("Cut tier" in w for _, w in check_card.problems(body)))

    def test_form_without_title_still_lints_body(self):
        self.assertEqual(check_card.problems(card("good_form")), [])

    def test_cli_exit_codes_and_event(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(check_card.main([os.path.join(FIX, "good_template.md")]), 0)
            self.assertEqual(check_card.main([os.path.join(FIX, "broken_vague_done.md")]), 1)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"issue": {"title": "[UE-000] ", "body": card("good_form")}}, f)
        os.environ["GITHUB_EVENT_PATH"] = f.name
        try:
            with redirect_stdout(out):
                self.assertEqual(check_card.main(["--event"]), 1)  # template title "[UE-000]"
        finally:
            del os.environ["GITHUB_EVENT_PATH"]
            os.remove(f.name)
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            self.assertEqual(check_card.main([]), 2)


class NeedsHumanGrace(unittest.TestCase):
    """The 2 h grace default (pipeline/human-checkpoints.md): an unanswered ask past 2 h lists GRACE EXPIRED -> <role>;
    the human-only kinds never get a grace path."""
    NOW = check_card.parse_time("2026-11-12T13:00Z")

    @staticmethod
    def ask(n, line, *later):
        return {"number": n, "labels": [{"name": "needs-human"}],
                "comments": [{"body": "ROLE: Producer | session 2026-11-12T10:00Z\n" + line}]
                + [{"body": b} for b in later]}

    def queue(self, *issues):
        return check_card.needs_human_queue(list(issues), self.NOW)

    def test_expired_goes_to_its_role(self):
        lines, probs = self.queue(
            self.ask(5, "NEEDS HUMAN: Rick merge PR #9 #9 2026-11-12T10:00Z"),
            self.ask(6, "NEEDS HUMAN: TD-human pick the 2D approach (D4) #6 2026-11-12T10:30Z"),
            self.ask(7, "NEEDS HUMAN: Richard confirm the owl telegraph colour #7 2026-11-12T11:00Z"),
            self.ask(8, "NEEDS HUMAN: Rick confirm the stretch order #8 2026-11-12T12:00Z"),
            self.ask(9, "NEEDS HUMAN: Rick confirm the stretch order #9 2026-11-12T10:00Z", "Done, kept the order."))
        self.assertEqual(probs, [])
        self.assertEqual(lines, ["#5 Rick: merge PR #9 #9 GRACE EXPIRED -> Producer",
                                 "#6 TD-human: pick the 2D approach (D4) #6 GRACE EXPIRED -> Technical Director",
                                 "#7 Richard: confirm the owl telegraph colour #7 GRACE EXPIRED -> Producer for Richard",
                                 "#8 Rick: confirm the stretch order #8 grace ends 2026-11-12T14:00Z",
                                 "#9 Rick: confirm the stretch order #9 human replied"])
        # broken on purpose: an agent's own ROLE: comment is not a human reply, so the grace still expires
        lines, _ = self.queue(self.ask(9, "NEEDS HUMAN: Rick confirm the stretch order #9 2026-11-12T10:00Z",
                                       "ROLE: Producer | session x\nstill waiting"))
        self.assertTrue(lines[0].endswith("GRACE EXPIRED -> Producer"), lines)

    def test_human_only_kinds_never_get_a_grace_path(self):
        asks = {
            "submission": "NEEDS HUMAN: Josh submit the final entry on the jam form #11",
            "upload": "NEEDS HUMAN: Josh run butler push for the G4 zip #11",
            "packaging": "NEEDS HUMAN: Marta run daily.ps1 on the Windows packaging machine #11",
            "launch": "NEEDS HUMAN: Marta launch the gate zip on the second Windows machine #11",
            "playtest": "NEEDS HUMAN: Rick run playtest P3 #11",
            "editor check": "NEEDS HUMAN: Rick open L_Graybox.umap for the editor check #11",
            "gate_paths": "NEEDS HUMAN: TD-human add Source/** to gate_paths in gates.json #11",
            "tools": "NEEDS HUMAN: TD-human merge the change to tools/check_pr.py #11",
            "CI": "NEEDS HUMAN: TD-human approve the CI workflow edit #11",
            "role card": "NEEDS HUMAN: TD-human approve the role card edit #11",
            "model tier": "NEEDS HUMAN: Josh move audio to the Hard calls model tier #11",
            "delete": "NEEDS HUMAN: Rick delete the old owl sprites another card made #11",
            "P0": "NEEDS HUMAN: Richard cut DEF-01 from P0 #11",
            "range": "NEEDS HUMAN: Richard approve the arena width outside the 5A range #11",
        }
        for name, line in asks.items():
            with self.subTest(name):
                lines, probs = self.queue(self.ask(11, line + " 2026-11-12T08:00Z"))
                self.assertEqual(probs, [])
                self.assertIn("HUMAN ONLY", lines[0])
                self.assertNotIn("GRACE", lines[0])

    def test_broken_ask_without_a_timestamp_is_a_problem(self):
        lines, probs = self.queue(self.ask(5, "NEEDS HUMAN: Rick merge PR #9 #9"))
        self.assertEqual(lines, [])
        self.assertTrue(probs and "no UTC timestamp" in probs[0], probs)
        # the status board reads the queue without a clock, and stays as it was
        self.assertEqual(check_card.needs_human_queue([self.ask(5, "NEEDS HUMAN: Rick merge PR #9 #9")]),
                         (["#5 Rick: merge PR #9 #9"], []))

    def test_cli(self):
        issues = [self.ask(5, "NEEDS HUMAN: Rick merge PR #9 #9 2026-11-12T10:00Z")]
        for now, want, code in (("2026-11-12T12:01Z", "GRACE EXPIRED -> Producer", 0),
                                ("2026-11-12T11:59Z", "grace ends", 0)):
            out = io.StringIO()
            stdin = sys.stdin
            sys.stdin = io.StringIO(json.dumps(issues))
            try:
                with redirect_stdout(out):
                    self.assertEqual(check_card.main(["--needs-human", "--now", now]), code)
            finally:
                sys.stdin = stdin
            self.assertIn(want, out.getvalue())


if __name__ == "__main__":
    unittest.main()

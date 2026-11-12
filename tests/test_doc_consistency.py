"""Cross-document agreements from red-team round 2. Each test reads the live docs; editing one doc
so it contradicts the others (for example a Shipping SMOKE_OK requirement while D-new-smoke is open)
makes the test fail."""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def shipping_smoke_required(text):
    """True if the text requires SMOKE_OK on Shipping without deferring to D-new-smoke."""
    for line in text.splitlines():
        if re.search(r"Shipping", line) and re.search(r"SMOKE_OK|smoke", line, re.I) \
                and "D-new-smoke" not in line and not re.search(r"\bno\b|\bnot\b|\bonly if\b|unless", line, re.I):
            return line
    return None


class SmokeIsAnOpenDecision(unittest.TestCase):
    FILES = ["pipeline/day0-cards.md", "pipeline/roles/technical-director.md", "docs/decisions.md",
             "pipeline/checklists/submission.md", "pipeline/roles/qa-build.md"]

    def test_no_file_requires_a_shipping_smoke(self):
        for rel in self.FILES:
            with self.subTest(file=rel):
                self.assertIsNone(shipping_smoke_required(read(rel)))

    def test_detector_catches_a_shipping_smoke_requirement(self):
        self.assertTrue(shipping_smoke_required("- [ ] Smoke on the Shipping build: `SMOKE_OK` present"))
        self.assertIsNone(shipping_smoke_required("- [ ] Shipping smoke only if D-new-smoke picks it"))

    def test_td_no_longer_turns_on_shipping_logging_by_default(self):
        self.assertNotIn("bUseLoggingInShipping = true", read("pipeline/roles/technical-director.md"))


class OneContentPath(unittest.TestCase):
    def test_art_path_is_the_same_everywhere(self):
        for rel in ("pipeline/roles/asset-specialist.md", "pipeline/templates/asset-brief.md",
                    "pipeline/templates/task-card.md"):
            with self.subTest(file=rel):
                text = read(rel)
                self.assertNotRegex(text, r"(?<!UmbrellaElla/)\bContent/(?:Art|Ella)/")
                self.assertIn("Content/UmbrellaElla/Art/", text)


class PeopleAndScreens(unittest.TestCase):
    def test_day1_seats_are_blockers(self):
        brief = read("docs/jam-brief.md")
        for seat in ("Integration owner", "Packaging and submission owner", "Windows packaging machine",
                     "Game design owner", "Technical Director, human"):
            with self.subTest(seat=seat):
                row = [ln for ln in brief.splitlines() if ln.startswith("| " + seat)]
                self.assertTrue(row and "BLOCKER" in row[0], seat)
        self.assertIn("BLOCKER", [r for r in read("pipeline/day0-cards.md").splitlines() if r.startswith("| 0.0 ")][0])

    def test_spec_has_the_fail_screen_the_brief_asks_for(self):
        self.assertIn("fail screens", read("docs/jam-brief.md"))
        self.assertIn("Fail screen", read("docs/game-spec.md"))
        self.assertIn("D-new-lose", read("docs/decisions.md"))

    def test_submission_lists_every_playtest(self):
        n = max(int(x) for x in re.findall(r"^\| P(\d+) \|", read("pipeline/qa/playtests.md"), re.M))
        self.assertIn(f"P1-P{n}", read("pipeline/checklists/submission.md"))

    def test_spike_list_matches_template(self):
        tmpl = set(re.findall(r"D\d+", read("pipeline/templates/spike-card.md").split("\n\n")[1]))
        row = [r for r in read("pipeline/day0-cards.md").splitlines() if r.startswith("| 0.11 ")][0]
        self.assertTrue(tmpl <= set(re.findall(r"D\d+", row)), tmpl - set(re.findall(r"D\d+", row)))


WORLD_NAME = re.compile(r"UmbrellaElla\.[A-Za-z]+(?:\.[A-Za-z]+)+")


def bad_world_names(text):
    """World-test names without a `.World.` segment: names ending in InWorld, or a name labelled 'world test'
    right before it ("World test `X`") or right after it ("`X` (world test: ..."). A line can list rule tests and
    a world test together, so only the labelled name counts. Without the segment, check_automation_report holds
    the test to the 1 s rule-test limit."""
    out = []
    for line in text.splitlines():
        for m in WORLD_NAME.finditer(line):
            name = m.group(0)
            before = line[max(0, m.start() - 14):m.start()].lower()
            after = line[m.end():m.end() + 14].lower()
            labelled = re.search(r"world tests?\W{0,3}$", before) or re.match(r"\W{0,3}\(?world test", after)
            if (name.endswith("InWorld") or labelled) and ".World." not in name:
                out.append(name)
    return out


def doc_files():
    files = ["AGENTS.md"]
    for top in ("pipeline", "evals"):
        for d, _, names in os.walk(os.path.join(ROOT, top)):
            if os.path.join("evals", "reviewer", "runs") in d:
                continue
            files += [os.path.relpath(os.path.join(d, n), ROOT) for n in names if n.endswith(".md")]
    files += [os.path.join("docs", n) for n in os.listdir(os.path.join(ROOT, "docs")) if n.endswith(".md")]
    return sorted(files)


class WorldTestNames(unittest.TestCase):
    def test_every_world_test_name_has_a_world_segment(self):
        for rel in doc_files():
            with self.subTest(file=rel):
                self.assertEqual(bad_world_names(read(rel)), [])

    def test_detector(self):
        self.assertEqual(bad_world_names("World test `UmbrellaElla.Flow.MenuBlocksGameplayInput`"),
                         ["UmbrellaElla.Flow.MenuBlocksGameplayInput"])
        self.assertEqual(bad_world_names("World test `UmbrellaElla.Flow.World.MenuBlocksGameplayInput`"), [])
        self.assertEqual(bad_world_names("`UmbrellaElla.Move.Envelope` (world test: spawns Ella)"), ["UmbrellaElla.Move.Envelope"])
        self.assertEqual(bad_world_names("`UmbrellaElla.Move.Rule` (rule test) and `UmbrellaElla.Move.World.Walk` (world test: ...)"), [])
        self.assertEqual(bad_world_names("`UmbrellaElla.Hazard.SpikeRearmsAfterDelayInWorld`"),
                         ["UmbrellaElla.Hazard.SpikeRearmsAfterDelayInWorld"])


if __name__ == "__main__":
    unittest.main()


def gate_mvp(producer_text, gate):
    """MVP numbers a producer.md gate row names, e.g. 'MVP 1–6, 9, 11' -> {1..6, 9, 11}."""
    row = next(l for l in producer_text.splitlines() if l.startswith(f"| {gate} |"))
    m = re.search(r"MVP ([\d–\-, ]+)", row)
    out = set()
    for part in (m.group(1) if m else "").split(","):
        part = part.strip()
        if re.fullmatch(r"\d+[–-]\d+", part):
            a, b = re.split(r"[–-]", part)
            out |= set(range(int(a), int(b) + 1))
        elif part.isdigit():
            out.add(int(part))
    return out


class StolenHourGates(unittest.TestCase):
    """GDD SH1.0 (D-new-sh10-g1): G1 is the Start Game mode; Director's Cut adds the rest at G2 and G3. The producer
    gate rows, the brief's [G<n>] tags and tools/check_card.py GATE_MVP agree, and no P0 item is stretch or cut."""

    def test_every_mvp_item_is_due_at_g1_g2_or_g3(self):
        import check_card
        brief = read("docs/jam-brief.md")
        mvp = {int(n) for n in re.findall(r"^(\d+)\.\s", brief.split("## MVP", 1)[1].split("\n## ", 1)[0], re.M)}
        prod = read("pipeline/roles/producer.md")
        g1, g2, g3 = gate_mvp(prod, "G1"), gate_mvp(prod, "G2"), gate_mvp(prod, "G3")
        self.assertEqual(g1 | g2 | g3, mvp)
        due = check_card.gate_mvp(ROOT)
        self.assertEqual(set(due["G1"]), g1)
        self.assertEqual(set(due["G2"]) - set(due["G1"]), g2)
        self.assertEqual(set(due["G3"]), mvp)
        line = lambda n: next(l for l in brief.splitlines() if l.startswith(f"{n}. "))
        self.assertIn("Start Game", line(1))
        self.assertIn("Small Blasts", line(3))
        self.assertIn("Keeper fight", line(5))

    def test_every_feature_is_on_an_mvp_line(self):
        import check_card
        import json
        ids = {f["feature_id"] for f in json.loads(read("docs/feature-manifest.json"))["features"]}
        on_lines = set().union(*check_card.mvp_features(ROOT).values())
        self.assertEqual(ids - on_lines, set(), "an APPROVED_P0 Rule ID on no MVP line would never get a card")
        self.assertEqual(on_lines - ids, set())

    def test_gate_parser_catches_a_missing_item(self):
        self.assertEqual(gate_mvp("| G1 | x | MVP 1–6 in the graybox |", "G1"), {1, 2, 3, 4, 5, 6})

    def test_no_p0_item_is_stretch_or_cut(self):
        brief = read("docs/jam-brief.md")
        stretch = re.search(r"^Stretch.*?:\s*\n(.+?)$", brief, re.M).group(1)
        self.assertEqual(stretch.strip(), "none")
        cut = brief.split("## Cut list", 1)[1].split("\n## ", 1)[0]
        cut_lines = "\n".join(l for l in cut.splitlines() if re.match(r"\d\.", l)).lower()
        for words in ("keeper", "director's cut", "progression", "enemies", "small blasts", "tutorial"):
            with self.subTest(words):
                self.assertNotIn(words, cut_lines)
        self.assertIn("Never cut: any MVP item", cut)
        self.assertNotIn("One Stretch card per feature ID behind", read("pipeline/day0-cards.md"))


class Gdd13Sources(unittest.TestCase):
    def test_gdd_is_the_design_source_and_manifest_mirrors_it(self):
        agents = read("AGENTS.md")
        self.assertRegex(agents, r"2\. The current GDD snapshot \(design source\); `docs/feature-manifest.json` mirrors it")

    def test_numbers_come_from_approved_parameters(self):
        self.assertIn("`approved_parameters`", read("pipeline/roles/gameplay-dev.md"))
        self.assertIn("questions-1.3.md", read("pipeline/roles/game-designer.md"))

    def test_required_attack_and_shield_regressions(self):
        tm = read("pipeline/qa/test-map.md")
        for name in ("Attack.FirstShotOnEntry", "Attack.CadenceMatchesApproved", "Attack.FiresPlusXOnly",
                     "Attack.StopsOnExit", "Defense.FrontalArcCatches", "Defense.World.CatchConsumesBoltNoDamage"):
            with self.subTest(name):
                self.assertIn(f"`UmbrellaElla.{name}`", tm)

    def test_playtests_fit_one_bolt_and_no_timer(self):
        pt = read("pipeline/qa/playtests.md")
        p7 = next(l for l in pt.splitlines() if l.startswith("| P7 |"))
        p8 = next(l for l in pt.splitlines() if l.startswith("| P8 |"))
        self.assertIn("2+ owl patterns", p7)
        self.assertNotIn("remaining time", p8)
        self.assertTrue(any(l.startswith("| P12 | Shield blocks and heals") for l in pt.splitlines()))

    def test_shield_feedback_card_precedes_def01(self):
        # GDD SH1.0: the 1.3 shield is gone; its catch / heal feedback card now precedes the yellow absorption card
        d0 = read("pipeline/day0-cards.md")
        self.assertRegex(d0, r"\| 0\.14b \| Yellow catch, heal and wind feedback \(before the MVP 4 absorption card\)")
        self.assertIn("The MVP 4 absorption card (UMB-05, SURV-05) lists this card in After", d0)

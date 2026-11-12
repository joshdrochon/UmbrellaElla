"""GDD 1.3 frozen data (tests/fixtures/gdd13): these rules model the 1.3 timer arena; GDD SH1.0 data is checked in its own tests. Tests for the encounter presets (tools/encounter_spec.py, run by tools/encounter_check.py): rules S1-S13, the
playthrough log P1-P8, the critic loop's card lines C6-C9 and tools/check_pr.py rule encounter. Each failing case
breaks the repo's data on purpose and asserts the rule catches it, with a line that says what to fix."""
import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_pr  # noqa: E402
import encounter_check as ec  # noqa: E402
import encounter_spec as es  # noqa: E402

DATA = os.path.join(ROOT, "tests", "fixtures", "gdd13", "pipeline", "level", "encounter.json")
MD = os.path.join(ROOT, "tests", "fixtures", "gdd13", "pipeline", "level", "encounter.md")
with open(DATA, encoding="utf-8") as fh:
    BASE = json.load(fh)
with open(MD, encoding="utf-8") as fh:
    MD_TEXT = fh.read()
with open(os.path.join(ROOT, "tests", "fixtures", "gdd13", "docs", "feature-manifest.json"), encoding="utf-8") as fh:
    MANIFEST = json.load(fh)
R = "OWL-FIGHT-RICKY"


def run(data, md=None):
    return es.check(data, md, MANIFEST, ROOT, ec.MIN_TELEGRAPH_SEC)


def rules(data, md=None):
    return {r for r, _, _ in run(data, md)[0]}


def ricky(d):
    return d["encounter_presets"]["presets"][R]


def by_id(items, i):
    return next(x for x in items if x["id"] == i)


class RepoData(unittest.TestCase):
    def test_repo_data_passes(self):
        probs, nums = run(BASE, MD_TEXT)
        self.assertEqual(probs, [])
        self.assertTrue(any(n.startswith(f"preset {R}: estimated length") for n in nums), nums)

    def test_encounter_check_main_is_clean(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = ec.main([])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("encounter_check: 0 problem(s)", out.getvalue())

    def test_gdd_baseline_is_the_default_and_unchanged(self):
        b = BASE["encounter_presets"]
        self.assertEqual(b["default"], "GDD-1.3")
        self.assertEqual(b["presets"]["GDD-1.3"]["status"], "baseline")
        # the baseline view reads the approved numbers from the top level (E29 holds them to the manifest)
        v = es.view(BASE, "GDD-1.3")
        bolt = by_id(v["attacks"], "BOLT_Single")
        vals = MANIFEST["approved_parameters"]["values"]
        self.assertEqual(bolt["telegraph"]["sec"], vals["OWL-01.telegraph_delay"]["start"])
        self.assertEqual(bolt["first_at"], vals["OWL-01.initial_grace_s"]["start"])
        self.assertEqual(bolt["cadence_sec"], vals["OWL-01.cadence"]["start"])
        self.assertEqual(v["fight_length_sec"]["max"], vals["END-01.survival_s"]["start"])
        self.assertEqual(ec.check(BASE, MD_TEXT, ec.load_tuning(BASE)[0], manifest=MANIFEST)[0], [])

    def test_ricky_preset_has_the_described_fight(self):
        p = ricky(BASE)
        t = {x["id"]: x for x in p["targets"]}
        self.assertEqual((t["WINGS"]["hp"], t["WINGS"]["shared_hp"], len(t["WINGS"]["regions"])), (180, True, 2))
        self.assertEqual([t[m]["hp"] for m in ("MECH_FRONT", "MECH_MIDDLE", "MECH_REAR")], [100, 110, 120])
        self.assertEqual((t["CLOCK"]["hp"], t["CLOCK"]["floor_pct_before_final"]), (320, 40))
        self.assertEqual(t["WINGS"]["on_break"]["cancels"], ["GUST_Band"])
        gust = by_id(p["attacks"], "GUST_Band")
        self.assertEqual(gust["effect"]["push"], "left")
        self.assertIn("not the push", gust["effect"]["dash"])
        self.assertEqual([c["verb"] for c in gust["not_counterplay"]], ["absorb"])
        self.assertEqual([ph["id"] for ph in p["phases"]], ["wings", "mechanisms", "clock"])
        self.assertEqual(by_id(p["phases"], "mechanisms")["sequence"], ["MECH_FRONT", "MECH_MIDDLE", "MECH_REAR"])
        self.assertEqual(p["entry"], {"full_run": "wings", "boss_practice": "clock"})
        self.assertTrue(p["player"]["shooting_falls"] and p["player"]["absorbing_falls"])
        self.assertEqual(p["player"]["damage_reduces"], ["umbrella_health", "lift"])
        self.assertEqual(by_id(p["attacks"], "RED_Volley")["effect"]["shots"], 4)
        self.assertEqual(by_id(p["attacks"], "YELLOW_Packet")["effect"]["shots"], 2)
        self.assertEqual(p["status"], "proposed")
        self.assertEqual(p["owner"], "Richard")
        self.assertNotIn("ship", p["selectable_in"])


class BreakOnPurpose(unittest.TestCase):
    def broken(self, fn):
        d = copy.deepcopy(BASE)
        fn(d)
        return d

    def assertCatches(self, rule, fn, text=None):
        d = self.broken(fn)
        probs = [p for p in run(d)[0] if p[0] == rule]
        self.assertTrue(probs, f"{rule} not raised")
        if text:
            self.assertTrue(any(text in m for _, _, m in probs), probs)

    def test_s1_proposed_default_ship_and_decision(self):
        self.assertCatches("S1", lambda d: d["encounter_presets"].update(default=R), "only the baseline preset ships")
        self.assertCatches("S1", lambda d: ricky(d)["selectable_in"].append("ship"), "never ships")
        self.assertCatches("S1", lambda d: ricky(d).update(decision="D-new-nope"), "no row in docs/decisions.md")
        self.assertCatches("S1", lambda d: ricky(d).pop("owner"), "no owner")
        self.assertCatches("S1", lambda d: d.pop("encounter_presets"), "missing")

    def test_s2_baseline_never_copies_a_gdd_number(self):
        def copy_tell(d):
            d["encounter_presets"]["presets"]["GDD-1.3"]["attacks"][0]["telegraph"] = {"sec": 0.5}
        self.assertCatches("S2", copy_tell, "copies telegraph")
        self.assertCatches("S2", lambda d: d["encounter_presets"]["presets"]["GDD-1.3"]["phases"][0]["ends_when"]
                           .update(timer=60), "copies a number")

    def test_s3_unknown_names_and_reference(self):
        self.assertCatches("S3", lambda d: by_id(ricky(d)["phases"], "wings")["attacks"].append("NOPE"))
        self.assertCatches("S3", lambda d: ricky(d).update(reference="pipeline/level/reference/missing.md"))
        self.assertCatches("S3", lambda d: ricky(d)["numbers_from_reference"].append("targets.WINGS.armor"))

    def test_s4_unreachable_phase_and_loop(self):
        def orphan(d):
            by_id(ricky(d)["phases"], "wings")["next"] = "clock"
        self.assertCatches("S4", orphan, "not reachable")

        def loop(d):
            by_id(ricky(d)["phases"], "clock").update(next="wings", ends_fight=False)
        self.assertCatches("S4", loop, "loops back")

    def test_s5_unfinishable_phase(self):
        self.assertCatches("S5", lambda d: by_id(ricky(d)["targets"], "WINGS").update(hp=0), "no HP")
        self.assertCatches("S5", lambda d: by_id(ricky(d)["targets"], "WINGS").update(vulnerable_in=["clock"]),
                           "not vulnerable in this phase")
        self.assertCatches("S5", lambda d: by_id(ricky(d)["phases"], "wings")["targets"].remove("WINGS"),
                           "not a target of this phase")

    def test_s6_short_or_sound_only_telegraph(self):
        self.assertCatches("S6", lambda d: by_id(ricky(d)["attacks"], "TALON_Rake")["telegraph"].update(sec=0.2),
                           "floor")
        self.assertCatches("S6", lambda d: by_id(ricky(d)["attacks"], "TALON_Rake")["telegraph"].update(pose=None, vfx=None),
                           "sound alone fails")

    def test_s6_floor_is_the_larger_of_gdd_and_pipeline(self):
        self.assertEqual(es.telegraph_floor(MANIFEST, 0.4), 0.4)
        self.assertEqual(es.telegraph_floor(MANIFEST, 0.1), MANIFEST["approved_parameters"]["values"]
                         ["OWL-01.telegraph_delay"]["min"])

    def test_s7_counterplay(self):
        self.assertCatches("S7", lambda d: by_id(ricky(d)["attacks"], "GUST_Band").update(counterplay=[]), "no counterplay")
        self.assertCatches("S7", lambda d: ricky(d)["player"]["verbs"].remove("catch"), "lacks")
        self.assertCatches("S7", lambda d: by_id(ricky(d)["attacks"], "GUST_Band")["counterplay"].append({"verb": "absorb"}),
                           "as not counterplay")

    def test_s8_pacing(self):
        self.assertCatches("S8", lambda d: by_id(ricky(d)["targets"], "CLOCK").update(hp=3200), "outside the target")
        self.assertCatches("S8", lambda d: ricky(d)["fight_length_sec"].update(max=600), "END-01.survival_s")

    def test_s9_attack_after_its_canceller_broke(self):
        def gust_late(d):
            by_id(ricky(d)["phases"], "mechanisms")["attacks"].append("GUST_Band")
            by_id(ricky(d)["attacks"], "GUST_Band")["phases"].append("mechanisms")
        self.assertCatches("S9", gust_late, "cancels it")
        self.assertCatches("S9", lambda d: by_id(ricky(d)["targets"], "MECH_FRONT")["on_break"].update(new_attacks=True))

    def test_s10_no_attack_during_a_transition(self):
        self.assertCatches("S10", lambda d: by_id(ricky(d)["attacks"], "RED_Volley").update(first_at=0.5),
                           "inside the 2.0 s transition")
        self.assertCatches("S10", lambda d: by_id(ricky(d)["phases"], "clock")["transition_in"].update(new_attacks=True))
        self.assertCatches("S10", lambda d: by_id(ricky(d)["attacks"], "GUST_Band").update(cadence_sec=0.5),
                           "not longer than")

    def test_s11_names(self):
        self.assertCatches("S11", lambda d: by_id(ricky(d)["targets"], "WINGS").pop("hitbox"), "hitboxes.json")
        self.assertCatches("S11", lambda d: by_id(ricky(d)["attacks"], "TALON_Rake").update(art=[]), "references.json")
        self.assertCatches("S11", lambda d: by_id(ricky(d)["attacks"], "TALON_Rake").update(sound=[]), "sound-list.csv")

    def test_s13_doc_drift(self):
        d = copy.deepcopy(BASE)
        by_id(ricky(d)["targets"], "WINGS")["hp"] = 190
        self.assertIn("S13", rules(d, MD_TEXT))
        self.assertIn("S13", rules(BASE, MD_TEXT.replace(es.PBEGIN, "")))


class Ready(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        for sub in ("pipeline/feel", "pipeline/art", "pipeline/audio"):
            os.makedirs(os.path.join(self.root, sub))
        shutil.copy(os.path.join(ROOT, "tests/fixtures/gdd13/pipeline/audio/sound-list.csv"), os.path.join(self.root, "pipeline/audio"))

    def write(self, rel, obj):
        with open(os.path.join(self.root, rel), "w", encoding="utf-8") as fh:
            json.dump(obj, fh)

    def test_baseline_ready_once_rows_exist_and_breaks_without_them(self):
        self.write("pipeline/feel/hitboxes.json", {"entities": [{"id": "owl-body"}, {"id": "owl-clock"}]})
        self.write("pipeline/art/references.json", {"elements": {"owl": {}, "owl-bolt": {}, "bolt-hit": {}}})
        self.assertEqual(es.ready_problems(BASE, "GDD-1.3", self.root), [])
        self.write("pipeline/feel/hitboxes.json", {"entities": [{"id": "owl-body"}]})
        probs = es.ready_problems(BASE, "GDD-1.3", self.root)
        self.assertEqual([m for _, _, m in probs if "owl-clock" in m] != [], True, probs)

    def test_ricky_names_rows_nobody_made_yet(self):
        self.write("pipeline/feel/hitboxes.json", {"entities": []})
        self.write("pipeline/art/references.json", {"elements": {}})
        msgs = " ".join(m for _, _, m in es.ready_problems(BASE, R, self.root))
        for want in ("owl-wing", "gust-band", "TalonWarn", "ClockBeat"):
            self.assertIn(want, msgs)


class Selection(unittest.TestCase):
    def test_contexts(self):
        ids = lambda **kw: [pid for pid, _ in es.presets_for(BASE, **kw)]
        self.assertEqual(ids(context="ship"), ["GDD-1.3"])
        self.assertEqual(ids(gdd_revision="1.3", context="gdd_picker"), ["GDD-1.3", R])
        self.assertIn(R, ids(context="practice"))
        self.assertEqual(ids(gdd_revision="9.9"), [])


EVT = "ENCOUNTER_EVT t={t} preset=OWL-FIGHT-RICKY kind={k} phase={ph}{x}"


def good_log():
    L = []
    add = lambda t, k, ph, x="": L.append(EVT.format(t=t, k=k, ph=ph, x=x))
    add(0, "phase_start", "wings", " entry=full_run")
    add(0, "transition_start", "wings")
    add(2, "transition_end", "wings")
    add(3, "telegraph", "wings", " attack=GUST_Band")
    add(4, "fire", "wings", " attack=GUST_Band")
    add(30, "break", "wings", " target=WINGS")
    add(30, "phase_end", "wings")
    add(30, "phase_start", "mechanisms")
    add(30, "transition_start", "mechanisms")
    add(32, "transition_end", "mechanisms")
    add(33, "telegraph", "mechanisms", " attack=MECH_Front_Throw")
    add(34, "fire", "mechanisms", " attack=MECH_Front_Throw")
    add(50, "break", "mechanisms", " target=MECH_FRONT")
    add(55, "telegraph", "mechanisms", " attack=MECH_Middle_Curve")
    add(56, "fire", "mechanisms", " attack=MECH_Middle_Curve")
    add(70, "break", "mechanisms", " target=MECH_MIDDLE")
    add(90, "break", "mechanisms", " target=MECH_REAR")
    add(90, "phase_end", "mechanisms")
    add(90, "phase_start", "clock")
    add(90, "transition_start", "clock")
    add(92, "transition_end", "clock")
    add(95, "telegraph", "clock", " attack=CLOCK_DoubleBeat")
    add(96, "fire", "clock", " attack=CLOCK_DoubleBeat")
    add(125, "break", "clock", " target=CLOCK")
    add(125, "phase_end", "clock")
    L.append("ENCOUNTER_EVT t=125 preset=OWL-FIGHT-RICKY kind=end")
    return L


class Playthrough(unittest.TestCase):
    def rules(self, lines):
        return {r for r, _, _ in es.check_playthrough(BASE, R, lines)[0]}

    def test_good_log_passes(self):
        probs, summary = es.check_playthrough(BASE, R, ["noise"] + good_log())
        self.assertEqual(probs, [])
        self.assertIn("phases=wings,mechanisms,clock", summary)

    def test_each_break_is_caught(self):
        L = good_log()
        cases = {
            "P1": [x.replace("kind=fire", "kind=boom", 1) for x in L],
            "P2": [x for x in L if "phase=mechanisms" not in x],
            "P3": [x for x in L if "kind=telegraph phase=wings" not in x],
            "P4": L[:2] + [EVT.format(t=1, k="telegraph", ph="wings", x=" attack=RED_Volley")] + L[2:],
            "P5": L[:12] + [EVT.format(t=35, k="telegraph", ph="mechanisms", x=" attack=GUST_Band")] + L[12:],
            "P6": [x for x in L if "target=MECH_MIDDLE" not in x],
            "P7": [x for x in L if "kind=end" not in x],
        }
        for rule, lines in cases.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, self.rules(lines))
        self.assertEqual(self.rules(["nothing here"]), {"P8"})

    def test_short_lead_and_stun(self):
        L = good_log()
        short = [x.replace("t=4 ", "t=3.5 ") for x in L]
        self.assertIn("P3", self.rules(short))
        stun = L[:13] + [EVT.format(t=50.5, k="telegraph", ph="mechanisms", x=" attack=RED_Volley")] + L[13:]
        self.assertIn("P4", self.rules(stun))


def verdict_line(verdict, rnd, gap="none", pt=0, ck=0, spec="x", critic=None, phase="wings"):
    return (f"ENCOUNTER CRITIC: {verdict} preset={R} phase={phase} round={rnd} spec={spec} builder=s1 "
            f"critic={critic or 'c%d' % rnd} capture=#12 playthrough={pt} check={ck} gap={gap}")


def card(spec=None, verdict="PASS", rnd=1, builder="s1", critic="s2", run=True, ready=True, phase="wings", extra=""):
    spec = spec or es.spec_hash(BASE, R, phase)
    lines = [f"Encounter phases: {R}/{phase}"]
    if run:
        lines.append(f"playthrough_check: 0 problem(s) preset={R} phases=wings,mechanisms,clock entry=full_run")
    if ready:
        lines.append(f"encounter_ready: 0 problem(s) preset={R}")
    lines.append(extra)
    if verdict:
        lines.append(f"ENCOUNTER CRITIC: {verdict} preset={R} phase={phase} round={rnd} spec={spec} builder={builder} "
                     f"critic={critic} capture=#12 playthrough=0 check=0 gap=none")
    return "\n".join(lines) + "\n"


class CriticLoop(unittest.TestCase):
    def rules(self, text):
        return {r for r, _, _ in es.card_problems(text, BASE, ROOT)}

    def test_pass_card_is_clean(self):
        self.assertEqual(es.card_problems(card(), BASE, ROOT), [])

    def test_no_phases_line_no_rules(self):
        self.assertEqual(es.card_problems("Encounter phases: none (arena tweak)\n", BASE, ROOT), [])

    def test_breaks(self):
        self.assertIn("C6", self.rules(card(verdict=None)))
        self.assertIn("C6", self.rules(card(verdict="FAIL")))
        self.assertIn("C6", self.rules(card(spec="000000000000")))
        self.assertIn("C6", self.rules(card(builder="s1", critic="s1")))
        self.assertIn("C6", self.rules(card(extra=verdict_line("FAIL", 1)).replace(" playthrough=0 check=0 gap=none", " gap=none")))
        self.assertIn("C8", self.rules(card(run=False)))
        self.assertIn("C9", self.rules(card(ready=False)))

    def test_newest_verdict_wins(self):
        fail_then_pass = card(verdict="PASS", rnd=2, extra=verdict_line("FAIL", 1, "the gust band is not visible", 2, 0))
        self.assertEqual(self.rules(fail_then_pass), set())

    def test_rounds_must_go_up(self):
        self.assertIn("C6", self.rules(card(verdict="PASS", rnd=1, extra=verdict_line("FAIL", 1, "late tell"))))

    def test_no_round_cap(self):
        # Josh's rule: the loop runs until the critic passes. A fixed cap (any round number) must not fail a PASS.
        fails = "\n".join(verdict_line("FAIL", n, f"gap number {n}", 9 - n, 0) for n in range(1, 12))
        self.assertEqual(self.rules(card(verdict="PASS", rnd=12, extra=fails)), set())
        # many FAIL rounds that keep improving are not stuck: keep looping (C6), never needs-human (C7)
        self.assertEqual(self.rules(card(verdict=None, extra=fails)), {"C6"})

    def test_same_gap_but_a_better_score_is_progress(self):
        fails = "\n".join(verdict_line("FAIL", n, "band unreadable", 5 - n, 1) for n in (1, 2, 3))
        self.assertEqual(self.rules(card(verdict=None, extra=fails)), {"C6"})
        fails = "\n".join(verdict_line("FAIL", n, "band unreadable", 2, 4 - n) for n in (1, 2, 3))
        self.assertEqual(self.rules(card(verdict=None, extra=fails)), {"C6"})

    def test_three_rounds_with_no_improvement_go_to_a_human(self):
        fails = "\n".join(verdict_line("FAIL", n, "band unreadable", 2, 1) for n in (1, 2, 3))
        probs = es.card_problems(card(verdict=None, extra=fails), BASE, ROOT)
        self.assertEqual({r for r, _, _ in probs}, {"C7"})
        self.assertIn("needs-human", probs[0][2])
        # two stuck rounds after earlier progress are not yet stuck; the third is
        two = "\n".join([verdict_line("FAIL", 1, "late tell", 3, 0)] +
                        [verdict_line("FAIL", n, "band unreadable", 2, 1) for n in (2, 3)])
        self.assertEqual(self.rules(card(verdict=None, extra=two)), {"C6"})
        three = two + "\n" + verdict_line("FAIL", 4, "Band unreadable.", 2, 1)
        self.assertEqual(self.rules(card(verdict=None, extra=three)), {"C7"})

    def test_spec_change_invalidates_the_pass(self):
        d = copy.deepcopy(BASE)
        by_id(ricky(d)["attacks"], "GUST_Band")["telegraph"]["sec"] = 1.2
        self.assertIn("C6", {r for r, _, _ in es.card_problems(card(), d, ROOT)})

    def test_encounter_check_card_mode_runs_them(self):
        self.assertIn("C6", {r for r, _, _ in ec.check_card_text(card(verdict="FAIL"), BASE)})

    def test_critic_packet_is_blind_and_names_the_verdict(self):
        text = es.critic_packet(BASE, R, "wings")
        self.assertIn(f"spec={es.spec_hash(BASE, R, 'wings')}", text)
        self.assertIn("Do not open the PR body", text)
        self.assertIn("pipeline/level/reference/owl-fight-ricky.md", text)
        self.assertIn("ENCOUNTER CRITIC: PASS", text)
        self.assertIsNone(es.critic_packet(BASE, R, "nope"))


PR = """## Task
Part of #40. Card ID: UE-0.33  Owner role: Encounter Designer  Reviewer role: Game Designer
## What changed
pipeline/level/encounter.json
## Done-when checks
- [x] critic passed
## Evidence
commit=abc1234 engine=none config=none host=mac run=none
encounter_check: 0 problem(s)
{lines}
## Not done / risks
none
Could not read: none
Next: Game Designer reviews
## Binary assets touched
none
## Journal
`journal.py export card=UE-0.33 machine=mac-1 commit=abc1234 events=2`
Next step: Game Designer reviews
"""


class CheckPrEncounterRule(unittest.TestCase):
    def enc(self, body, changed=("pipeline/level/encounter.json",), card_json=None):
        s = check_pr.sections(body)
        return check_pr.encounter_problems(s, list(changed), body, card_json, os.path.join(ROOT, "tests", "fixtures", "gdd13"))

    def test_pass_lines_pass(self):
        self.assertEqual(self.enc(PR.format(lines=card())), [])

    def test_data_change_needs_check_line_and_phases_line(self):
        body = PR.format(lines="").replace("encounter_check: 0 problem(s)\n", "")
        probs = " ".join(self.enc(body))
        self.assertIn("encounter_check: 0 problem(s)", probs)
        self.assertIn("Encounter phases:", probs)
        self.assertEqual(self.enc(PR.format(lines="Encounter phases: none (arena width only)")), [])

    def test_listed_phase_without_pass_fails(self):
        self.assertTrue(any("C6" in p for p in self.enc(PR.format(lines=card(verdict="FAIL")))))

    def test_card_listing_phases_counts_without_a_data_change(self):
        cj = {"title": "[UE-0.33] loop", "body": card(verdict=None)}
        self.assertTrue(any("C6" in p for p in self.enc(PR.format(lines=""), changed=(), card_json=cj)))

    def test_unrelated_pr_untouched(self):
        body = PR.format(lines="").replace("## What changed\npipeline/level/encounter.json", "## What changed\nSource/X.cpp")
        self.assertEqual(self.enc(body, changed=("Source/X.cpp",)), [])


class Wiring(unittest.TestCase):
    def test_role_and_cards_are_filed(self):
        self.assertEqual([p for p in ec.check_wiring(ROOT) if p[0] == "W6"], [])

    def test_missing_role_row_is_caught(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        for rel in ("pipeline/day0-cards.md", "pipeline/qa/test-map.md", "pipeline/qa/playtests.md",
                    "pipeline/level/encounter.json", "pipeline/roles/game-designer.md", "AGENTS.md"):
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, rel), os.path.join(root, rel))
        with open(os.path.join(root, "AGENTS.md"), encoding="utf-8") as fh:
            text = fh.read()
        with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as fh:
            fh.write(text.replace("pipeline/roles/encounter-designer.md", "pipeline/roles/x.md"))
        self.assertIn("W6", {r for r, _, _ in ec.check_wiring(root)})


if __name__ == "__main__":
    unittest.main()

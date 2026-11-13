"""GDD conformance check (tools/build/gdd_spec.py, gdd_check.py): a changed tuning value fails, a decisions row excuses it."""
import json, os, re, shutil, sys, tempfile, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "build"))
import gdd_check, gdd_spec  # noqa: E402


class Tree:
    """A temp copy of just what the check reads: Tuning headers, spec, bindings, a decisions file, playtest logs."""
    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "Source", "UmbrellaElla", "Public"), os.path.join(self.dir, "Source", "UmbrellaElla", "Public"),
                        ignore=lambda d, names: [n for n in names if not (n.endswith("Tuning.h") or os.path.isdir(os.path.join(d, n)))])
        os.makedirs(os.path.join(self.dir, "docs", "build", "playtest-logs"))
        for f in ("gdd-spec.json", "gdd-bindings.json"):
            shutil.copy(os.path.join(ROOT, "docs", "build", f), os.path.join(self.dir, "docs", "build", f))
        self.write("docs/decisions.md", "# Decisions\n| ID | Decision |\n|---|---|\n| D-1 | unrelated row about OWL-08 |\n")
        return self

    def __exit__(self, *a):
        shutil.rmtree(self.dir)

    def path(self, rel):
        return os.path.join(self.dir, rel)

    def write(self, rel, text, mode="w"):
        os.makedirs(os.path.dirname(self.path(rel)), exist_ok=True)
        with open(self.path(rel), mode) as fh:
            fh.write(text)

    def edit(self, rel, old, new):
        text = gdd_check._read(self.path(rel))
        assert old in text, old
        self.write(rel, text.replace(old, new, 1))

    def check(self):
        return gdd_check.check(self.dir)


def fail_lines(lines):
    return [l for l in lines if l.startswith("FAIL")]


class SpecTests(unittest.TestCase):
    def test_spec_is_a_fresh_generation(self):
        self.assertEqual(gdd_check._read(gdd_spec.OUT), gdd_spec.render())

    def test_known_values_are_extracted_with_unit_and_wording(self):
        spec = json.loads(gdd_check._read(gdd_spec.OUT))["values"]
        self.assertEqual((spec["COM-06.damage"]["value"], spec["COM-06.speed"]["unit"]), (10, "units"))
        self.assertEqual(spec["HAZ-10.radius"]["value"], 6)
        self.assertEqual(spec["MOVE-21.hop"]["value"], 40)
        self.assertIn("damage 10", spec["COM-06.damage"]["wording"])

    def test_extract_reads_tolerance_and_ignores_rule_ids(self):
        got = dict(gdd_spec.extract("T-01", "See COM-06 and QA-13. Speed 200 ±10% and range 5 s."))
        self.assertEqual([k for k in got if "13" in k or "06" in k], [])
        self.assertEqual(got["T-01.speed"]["tolerance"], {"value": 10.0, "unit": "%"})

    def test_no_tolerance_when_the_plus_minus_belongs_to_trim(self):
        got = dict(gdd_spec.extract("T-01", "fall 330 ±20% trim, HeroSize 1."))
        self.assertNotIn("tolerance", got["T-01.fall"])


class CheckTests(unittest.TestCase):
    def test_clean_tree_has_no_comdamage_fail(self):
        with Tree() as t:
            lines, _ = t.check()
            self.assertFalse([l for l in fail_lines(lines) if "COM-06.damage" in l])

    def test_main_has_exactly_the_known_hazard_ten_drift(self):
        with Tree() as t:
            lines, _ = t.check()
            self.assertEqual(sorted(l.split(" GDD=")[0] for l in fail_lines(lines)),
                             ["FAIL HAZ-10.radius", "FAIL HAZ-10.value", "FAIL HAZ-10.yields_muzzle"])

    def test_changed_tuning_value_fails_and_names_both_values(self):
        with Tree() as t:
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "SmallDamage = 10.0f", "SmallDamage = 11.0f")
            lines, fails = t.check()
            self.assertIn("FAIL COM-06.damage GDD=10 game=11 FAttackTuning.SmallDamage", lines)
            self.assertGreater(fails, 0)

    def test_fail_lines_are_stable_across_runs_and_carry_no_line_numbers(self):
        with Tree() as t:
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "SmallDamage = 10.0f", "SmallDamage = 11.0f")
            first = fail_lines(t.check()[0])
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "struct UMBRELLAELLA_API FAttackTuning", "// shifts lines\n\nstruct UMBRELLAELLA_API FAttackTuning")
            self.assertEqual(first, fail_lines(t.check()[0]))
            self.assertFalse([l for l in first if re.search(r":\d+", l)])

    def test_decision_row_citing_the_rule_id_excuses_it(self):
        with Tree() as t:
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "SmallDamage = 10.0f", "SmallDamage = 11.0f")
            t.write("docs/decisions.md", "| D-new-x | Small Blast damage 11 for COM-06 | DECIDED |\n", "a")
            lines, _ = t.check()
            self.assertFalse([l for l in fail_lines(lines) if "COM-06.damage" in l])
            self.assertTrue([l for l in lines if l.startswith("EXCUSED COM-06.damage")])

    def test_a_row_citing_another_rule_does_not_excuse(self):
        with Tree() as t:
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "SmallDamage = 10.0f", "SmallDamage = 11.0f")
            t.write("docs/decisions.md", "| D-new-x | about COM-066 and COM-07 | DECIDED |\n", "a")
            self.assertTrue([l for l in fail_lines(t.check()[0]) if "COM-06.damage" in l])

    def test_vector_component_binding(self):
        with Tree() as t:
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "FVector(60.0, 0.0, 0.0)", "FVector(44.0, 0.0, 6.0)")
            lines, _ = t.check()
            self.assertFalse([l for l in fail_lines(lines) if "MuzzleOffset" in l])

    def test_stale_binding_and_broken_binding_fail(self):
        with Tree() as t:
            b = json.loads(gdd_check._read(t.path("docs/build/gdd-bindings.json")))
            b["COM-06.gone"] = {"tuning": "FAttackTuning.SmallDamage"}
            b["COM-06.speed"] = {"tuning": "FAttackTuning.NoSuchField"}
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            lines = fail_lines(t.check()[0])
            self.assertTrue([l for l in lines if l.startswith("FAIL stale COM-06.gone")])
            self.assertTrue([l for l in lines if l.startswith("FAIL broken COM-06.speed")])

    def test_unbound_is_reported_and_counted(self):
        with Tree() as t:
            lines, _ = t.check()
            last = lines[-1]
            m = re.fullmatch(r"MISMATCH=(\d+) BOUND=(\d+) UNBOUND=(\d+)", last)
            self.assertTrue(m, last)
            spec = json.loads(gdd_check._read(t.path("docs/build/gdd-spec.json")))["values"]
            unmeasured = len([l for l in lines if l.startswith('UNMEASURED')])
            self.assertEqual(int(m.group(2)) + int(m.group(3)) + unmeasured, len(spec))
            self.assertTrue([l for l in lines if l.startswith("WARN UNBOUND rule=")])

    def test_playtest_binding_compares_and_reports_unmeasured(self):
        with Tree() as t:
            b = json.loads(gdd_check._read(t.path("docs/build/gdd-bindings.json")))
            b["HAZ-05.recovery"] = {"playtest": {"line": "PLAYTEST_X", "match": {"case": "a"}, "field": "rec"}}
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            self.assertTrue([l for l in t.check()[0] if l.startswith("UNMEASURED HAZ-05.recovery")])
            t.write("docs/build/playtest-logs/run-1.log", "PLAYTEST_X case=a rec=1.2\n")
            self.assertTrue([l for l in fail_lines(t.check()[0]) if "HAZ-05.recovery GDD=1.5s game=1.2" in l])
            t.write("docs/build/playtest-logs/run-2.log", "PLAYTEST_X case=a rec=1.5\n")
            self.assertFalse([l for l in fail_lines(t.check()[0]) if "HAZ-05.recovery" in l])


if __name__ == "__main__":
    unittest.main()

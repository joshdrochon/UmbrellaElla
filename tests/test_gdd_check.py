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
        for ref in {v["const"].split(":")[0] for v in json.loads(gdd_check._read(os.path.join(ROOT, "docs", "build", "gdd-bindings.json"))).values()
                    if isinstance(v, dict) and "const" in v}:     # files a `const` binding reads
            os.makedirs(os.path.dirname(os.path.join(self.dir, ref)), exist_ok=True)
            shutil.copy(os.path.join(ROOT, ref), os.path.join(self.dir, ref))
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

    def test_current_tree_has_no_mismatch_fail(self):
        with Tree() as t:
            lines, _ = t.check()
            self.assertEqual([l for l in fail_lines(lines) if "NOT_IN_GAME" not in l], [])

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
            lines, _ = t.check()
            self.assertFalse([l for l in fail_lines(lines) if "MuzzleOffset" in l])
            t.edit("Source/UmbrellaElla/Public/Attack/AttackTuning.h", "FVector(44.0, 0.0, 6.0)", "FVector(60.0, 0.0, 0.0)")
            lines, _ = t.check()
            self.assertTrue([l for l in fail_lines(lines) if "MuzzleOffset" in l])

    def test_stale_binding_and_broken_binding_fail(self):
        with Tree() as t:
            b = json.loads(gdd_check._read(t.path("docs/build/gdd-bindings.json")))
            b["COM-06.gone"] = {"tuning": "FAttackTuning.SmallDamage"}
            b["COM-06.speed"] = {"tuning": "FAttackTuning.NoSuchField"}
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            lines = fail_lines(t.check()[0])
            self.assertTrue([l for l in lines if l.startswith("FAIL stale COM-06.gone")])
            self.assertTrue([l for l in lines if l.startswith("FAIL broken COM-06.speed")])

    def test_every_spec_value_is_bound_listed_or_counted(self):
        with Tree() as t:
            lines, _ = t.check()
            m = re.fullmatch(r"MISMATCH=(\d+) BOUND=(\d+) UNBINDABLE=(\d+) NOT_IN_GAME_P0=(\d+) NOT_IN_GAME_P1P2=(\d+) UNBOUND_P0=(\d+) UNBOUND_P1P2=(\d+)", lines[-1])
            self.assertTrue(m, lines[-1])
            spec = json.loads(gdd_check._read(t.path("docs/build/gdd-spec.json")))["values"]
            unmeasured = len([l for l in lines if l.startswith("UNMEASURED")])
            self.assertEqual(sum(int(x) for x in m.groups()[1:]) + unmeasured, len(spec))
            self.assertEqual((m.group(6), m.group(7)), ("0", "0"))

    def _bindings(self, t):
        return json.loads(gdd_check._read(t.path("docs/build/gdd-bindings.json")))

    def test_unbound_p0_value_fails(self):
        with Tree() as t:
            b = self._bindings(t)
            b["unbindable"].pop("SURV-07.hp_values")
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            lines, fails = t.check()
            self.assertTrue([l for l in lines if l.startswith("FAIL UNBOUND P0 rule=SURV-07") and "hp_values" in l])
            self.assertTrue(lines[-1].endswith("UNBOUND_P0=1 UNBOUND_P1P2=0"), lines[-1])
            self.assertGreater(fails, 0)

    def test_unbound_p1_value_only_warns(self):
        with Tree() as t:
            b = self._bindings(t)
            b["unbindable"].pop("SURV-07.hp_values")
            spec = json.loads(gdd_check._read(t.path("docs/build/gdd-spec.json")))
            spec["values"]["SURV-07.hp_values"]["priority"] = "P1"
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            t.write("docs/build/gdd-spec.json", json.dumps(spec))
            lines, _ = gdd_check.check(t.dir, check_fresh=False)
            self.assertFalse([l for l in fail_lines(lines) if "UNBOUND" in l])
            self.assertTrue([l for l in lines if l.startswith("WARN UNBOUND rule=SURV-07") and "hp_values" in l])
            self.assertTrue(lines[-1].endswith("UNBOUND_P0=0 UNBOUND_P1P2=1"), lines[-1])

    def test_unbindable_entry_with_reason_passes_and_is_counted(self):
        with Tree() as t:
            b = self._bindings(t)
            n = len(b["unbindable"])
            lines, _ = t.check()
            self.assertIn(f"UNBINDABLE={n}", lines[-1])

    def test_unbindable_needs_a_reason_and_a_real_key_and_no_double_listing(self):
        with Tree() as t:
            b = self._bindings(t)
            b["unbindable"]["SURV-07.hp_values"] = "  "
            b["unbindable"]["SURV-07.nope"] = "gone"
            b["unbindable"]["COM-06.damage"] = "also bound"
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            lines = fail_lines(t.check()[0])
            self.assertTrue([l for l in lines if l.startswith("FAIL unbindable SURV-07.hp_values: needs a reason")])
            self.assertTrue([l for l in lines if l.startswith("FAIL unbindable SURV-07.nope")])
            self.assertTrue([l for l in lines if l.startswith("FAIL unbindable COM-06.damage: also bound")])

    def test_priority_comes_from_the_gdd_row_status(self):
        got = dict(gdd_spec.extract("T-01", "Speed 200.", gdd_spec.priority_of("APPROVED_P0")))
        self.assertEqual(got["T-01.speed"]["priority"], "P0")
        self.assertEqual(gdd_spec.priority_of("OPEN"), "")
        self.assertEqual(gdd_spec.priority_of("APPROVED_P1"), "P1")

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

    def test_expr_binding_follows_the_tuning_and_rejects_non_arithmetic(self):
        with Tree() as t:
            b = json.loads(gdd_check._read(t.path("docs/build/gdd-bindings.json")))
            self.assertEqual(gdd_check.expr_value({"FAStruct.A": 2.0}, "FAStruct.A * 3 + floor(1.5)"), 7.0)
            self.assertIsNone(gdd_check.expr_value({}, "FAStruct.Missing + 1"))
            self.assertIsNone(gdd_check.expr_value({"FAStruct.A": 1.0}, "FAStruct.A + __import__('os')"))
            self.assertEqual(gdd_check.expr_value({}, "xp_to(10, 100)"), 916.0)
            self.assertEqual(gdd_check.expr_value({}, "xp_to(62, 100)"), 7000.0)
            self.assertEqual([l for l in fail_lines(t.check()[0]) if "SURV-06.total_points" in l], [])
            t.edit("Source/UmbrellaElla/Public/Progression/ProgressionTuning.h", "int32 MaxLivesCap = 11", "int32 MaxLivesCap = 12")
            self.assertTrue([l for l in fail_lines(t.check()[0]) if "SURV-06.total_points" in l])

    def test_const_index_reads_the_nth_literal_of_a_pair(self):
        with Tree() as t:
            t.write("Source/X.cpp", "const FVector2D Envelope(185.0f, 285.0f);\n")
            self.assertEqual(gdd_check.const_value(t.dir, "Source/X.cpp:Envelope", 1), 285.0)
            self.assertEqual(gdd_check.const_value(t.dir, "Source/X.cpp:Envelope"), 185.0)
            self.assertIsNone(gdd_check.const_value(t.dir, "Source/X.cpp:Envelope", 2))

    def test_not_in_game_p0_fails_p1_warns_and_is_not_unbindable(self):
        with Tree() as t:
            spec = json.loads(gdd_check._read(t.path("docs/build/gdd-spec.json")))["values"]
            b = self._bindings(t)
            self.assertNotIn("CAM-06.h.2", b["unbindable"])
            self.assertEqual(b["not_in_game"]["CAM-06.h.2"]["owner"].split()[0], "arena")
            lines, fails = t.check()
            p0 = [l for l in lines if l.startswith("FAIL NOT_IN_GAME P0 CAM-06.h.2")]
            self.assertTrue(p0 and "owner=arena" in p0[0] and "missing=" in p0[0], p0)
            self.assertGreater(fails, 0)
            # a P1/P2 value only warns (every spec value is P0 today, so demote one)
            k = "CAM-06.h.2"
            spec[k]["priority"] = "P1"
            t.write("docs/build/gdd-spec.json", json.dumps({"values": spec}))
            lines, _ = gdd_check.check(t.dir, check_fresh=False)
            self.assertTrue([l for l in lines if l.startswith(f"WARN NOT_IN_GAME {k} ")])
            self.assertFalse([l for l in lines if l.startswith("FAIL") and k in l])
            self.assertRegex(lines[-1], rf"NOT_IN_GAME_P0={len(b['not_in_game']) - 1} NOT_IN_GAME_P1P2=1 UNBOUND_P0=0")

    def test_not_in_game_needs_owner_missing_and_a_spec_key(self):
        with Tree() as t:
            b = self._bindings(t)
            b["not_in_game"]["CAM-06.h.2"] = {"owner": "arena"}
            b["not_in_game"]["ZZZ-01.gone"] = {"owner": "a", "missing": "b"}
            t.write("docs/build/gdd-bindings.json", json.dumps(b))
            lines = fail_lines(t.check()[0])
            self.assertTrue([l for l in lines if l.startswith("FAIL not_in_game CAM-06.h.2: needs owner and missing")])
            self.assertTrue([l for l in lines if l.startswith("FAIL not_in_game ZZZ-01.gone")])


if __name__ == "__main__":
    unittest.main()

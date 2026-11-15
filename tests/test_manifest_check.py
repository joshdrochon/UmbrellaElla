"""tools/manifest_check.py: the real manifest passes; each break on purpose is caught with its kind."""
import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import manifest_check as mc  # noqa: E402
import gdd_impact as gi  # noqa: E402


def current():
    """The repo's own manifest, current snapshot (GDD SH1.0) and presets."""
    with open(os.path.join(ROOT, mc.MANIFEST), encoding="utf-8") as fh:
        man = json.load(fh)
    with open(os.path.join(ROOT, mc.current_snapshot(ROOT)), encoding="utf-8") as fh:
        snap = fh.read()
    with open(os.path.join(ROOT, mc.PRESETS), encoding="utf-8") as fh:
        presets = json.load(fh)
    return man, snap, presets


LEGACY = os.path.join(HERE, "fixtures", "gdd13")


def real():
    """A frozen GDD 1.3 trio (manifest and presets as merged before the SH1.0 import, the pinned 1.3 snapshot). GDD
    SH1.0 approves every feature as APPROVED_P0, so the rules for PROPOSED, EXPERIMENT, OFF and DEFERRED records are
    exercised on 1.3 data, where the GDD printed all of them."""
    with open(os.path.join(LEGACY, "docs", "feature-manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    with open(os.path.join(ROOT, "docs", "gdd", "GDD-1.3.md"), encoding="utf-8") as fh:
        snap = fh.read()
    with open(os.path.join(LEGACY, "pipeline", "qa", "presets.json"), encoding="utf-8") as fh:
        presets = json.load(fh)
    return man, snap, presets


def rec(man, fid):
    return [f for f in man["features"] if f["feature_id"] == fid][0]


class ManifestCheck(unittest.TestCase):
    def kinds(self, man, snap=None, presets=None):
        m0, s0, p0 = real()
        return {k for k, _, _ in mc.problems(man, snap if snap is not None else s0, presets if presets is not None else p0)}

    def test_real_manifest_passes(self):
        man, snap, presets = current()
        self.assertEqual(mc.problems(man, snap, presets, mc.read_decisions(ROOT)), [])
        self.assertEqual(mc.main(["--root", ROOT]), 0)
        man, snap, presets = real()
        self.assertEqual(mc.problems(man, snap, presets), [], "the frozen 1.3 trio still passes")

    def test_every_status_is_copied_not_promoted(self):
        man, snap, _ = current()
        # implementation_authorized only where the GDD itself prints APPROVED_P0/P1 (GDD 1.3 section 2)
        for f in man["features"]:
            self.assertEqual(f["implementation_authorized"], f["status"] in ("APPROVED_P0", "APPROVED_P1"), f["feature_id"])
        printed = gi.snapshot_statuses(snap)
        for f in man["features"]:
            if f["status"].startswith("APPROVED"):
                self.assertTrue(printed.get(f["feature_id"], "").startswith(f["status"]), f["feature_id"])

    def test_breaks(self):
        man, _, _ = real()
        cases = []

        def case(kind, fn):
            m = copy.deepcopy(man)
            fn(m)
            cases.append((kind, m))
        case("schema", lambda m: rec(m, "UMB-02").update(status="Proposed"))
        case("schema", lambda m: rec(m, "UMB-02").pop("owner"))
        case("schema", lambda m: rec(m, "UMB-02").update(default_enabled="false"))
        case("unique", lambda m: m["features"].append(copy.deepcopy(rec(m, "UMB-02"))))
        case("resolve", lambda m: rec(m, "SURV-03").update(requires=["UMB-99"]))
        case("resolve", lambda m: rec(m, "SURV-03").update(conflicts=["SURV-03"]))
        case("events", lambda m: rec(m, "UMB-03").update(emits=["CatchMaybe"]))
        case("authorized", lambda m: rec(m, "UMB-03").update(implementation_authorized=True))
        case("authorized", lambda m: rec(m, "UMB-04").update(implementation_authorized=True))
        case("flag", lambda m: rec(m, "UMB-02").update(flag=None))
        case("flag", lambda m: rec(m, "UMB-01").update(flag="UMB_1"))
        case("gdd", lambda m: m["features"].remove(rec(m, "VFX-01")))
        case("gdd", lambda m: m["features"].append(dict(copy.deepcopy(rec(m, "UMB-02")), feature_id="UMB-09", flag="UMB_09")))
        case("gdd", lambda m: rec(m, "OWL-01").update(tests=["QA-99"]))
        case("gdd", lambda m: m.update(gdd_revision="B0.9"))
        case("schema", lambda m: m["build_parameters"]["camera_mode"].update(default="isometric"))
        case("schema", lambda m: m["build_parameters"]["camera_mode"].update(status="UNDECIDED"))
        for kind, m in cases:
            with self.subTest(kind=kind):
                self.assertIn(kind, self.kinds(m))

    def test_approved_parameters_follow_gdd_5a(self):
        man, snap, _ = real()
        self.assertEqual(len(mc.section_5a_rows(snap)), len(mc.PARAM_ROWS))
        self.assertEqual(mc.approved_problems(man, snap), [])
        vals = lambda m: m["approved_parameters"]["values"]
        breaks = {
            "damage start": lambda m: vals(m)["CORE-03.bolt_damage"].update(start=10),
            "timer start": lambda m: vals(m)["END-01.survival_s"].update(start=150),
            "iframes start": lambda m: vals(m)["CORE-03.invulnerability_s"].update(start=1.2),
            "range max": lambda m: vals(m)["COM-01.cadence"].update(max=5.0),
            "step": lambda m: vals(m)["UMB-01.ascent_speed"].update(step=10),
            "seed": lambda m: vals(m)["OWL-01.seed"].update(start=1),
            "missing key": lambda m: vals(m).pop("SURV-03.restore_amount"),
        }
        for name, fn in breaks.items():
            m = copy.deepcopy(man)
            fn(m)
            with self.subTest(name):
                self.assertIn("approved", self.kinds(m))
        # a new 5A row the map does not know fails too
        extra = snap.replace("| Post-hit invulnerability |", "| Dodge roll length | 2 s; step 1 | 1-3 s |\n| Post-hit invulnerability |")
        self.assertTrue(any("PARAM_ROWS" in why for _, _, why in mc.approved_problems(man, extra)))

    def test_approved_p0_must_default_on(self):
        man, _, _ = real()
        rec(man, "COM-01").update(default_enabled=False)
        self.assertIn("p0-on", self.kinds(man))
        man, _, _ = real()
        rec(man, "UMB-03").update(default_enabled=False)  # PROPOSED: off is fine
        self.assertEqual(self.kinds(man), set())

    def test_camera_mode_defaults_to_the_gdd_value(self):
        man, _, _ = real()
        self.assertEqual(man["build_parameters"]["camera_mode"]["default"], "fixed_single_screen")

    def test_experiment_with_named_ticket_may_be_authorized(self):
        man, _, _ = real()
        rec(man, "UMB-04").update(implementation_authorized=True, ticket="#42")
        self.assertEqual(self.kinds(man), set())
        # promoting it without a GDD revision is a status the GDD does not state (dry run B C1)
        rec(man, "UMB-04").update(status="APPROVED_P1", ticket=None, flag="UMB_04")
        self.assertIn("gdd-status", self.kinds(man))

    def test_status_must_equal_the_gdd_stated_status(self):
        """Dry run B C1: demoting a P0 (or promoting an experiment) in the manifest alone fails."""
        man, _, _ = real()
        self.assertEqual(mc.gdd_status_problems(man["features"], real()[1]), [])
        breaks = {
            "DEF-01 demoted": lambda m: rec(m, "DEF-01").update(status="EXPERIMENT", default_enabled=False,
                                                                implementation_authorized=False, priority="experiment"),
            "SURV-03 deferred, P0 left": lambda m: rec(m, "SURV-03").update(status="DEFERRED"),
            "MOVE-02 promoted": lambda m: rec(m, "MOVE-02").update(status="APPROVED_P1", default_enabled=True,
                                                                   implementation_authorized=True),
            "UMB-03 on (GDD says OFF)": lambda m: rec(m, "UMB-03").update(default_enabled=True),
            "NAR-01 authorized": lambda m: rec(m, "NAR-01").update(implementation_authorized=True),
            "VFX-01 unstated, approved": lambda m: rec(m, "VFX-01").update(status="APPROVED_P1"),
            "OWL-04 priority P0": lambda m: rec(m, "OWL-04").update(priority="P0"),
        }
        for name, fn in breaks.items():
            m = copy.deepcopy(man)
            fn(m)
            with self.subTest(name):
                self.assertIn("gdd-status", self.kinds(m))
        self.assertEqual(mc.stated_status("EXPERIMENT / OFF for special effects"), "EXPERIMENT")
        self.assertEqual(mc.stated_status("APPROVED_P0 for fixed-forward configuration"), "APPROVED_P0")
        self.assertEqual(mc.stated_status("Experiment; reset"), "EXPERIMENT")

    def test_p0_off_needs_an_explicit_override(self):
        """Dry run B H3: a DECIDED row lifts p0-on only for IDs it names in 'Overrides:'."""
        man, snap, presets = real()
        rec(man, "DEF-01").update(default_enabled=False)
        head = "| ID | Decision | Owner | Status |\n|---|---|---|---|\n"
        signoff = head + "| D-new-p0-signoff | APPROVED_P0 = DEF-01, SURV-03 | Richard | DECIDED 2026-11-10 (Rick) |\n"
        cut = head + "| D-cut | Ship without the shield. Overrides: DEF-01 | Richard | DECIDED 2026-11-15 (Rick) |\n"
        kinds = lambda d: {k for k, _, _ in mc.problems(man, snap, presets, d)}
        self.assertIn("p0-on", kinds(""))
        self.assertIn("p0-on", kinds(signoff), "naming DEF-01 is not overriding it")
        self.assertIn("p0-on", kinds(cut.replace("DECIDED 2026-11-15 (Rick)", "open")), "an open row lifts nothing")
        self.assertNotIn("p0-on", kinds(cut))
        self.assertEqual(mc.decided_overrides(cut), {"DEF-01"})
        self.assertEqual(mc.decided_overrides(signoff), set())
        # Broken on purpose (dry run B H1): each near-miss row lifts nothing, and is itself a problem.
        row = "| D-cut | Ship without the shield. Overrides: DEF-01 | Richard | DECIDED 2026-11-15 (Rick) |\n"
        near = {
            "settled table, no Owner": "| ID | Rule now | Status |\n|---|---|---|\n| D99 | Shield cut | DECIDED 2026-11-14 (Rick). Overrides: DEF-01 |\n",
            "no table header": row,
            "DECIDED?": head + row.replace("DECIDED 2026-11-15 (Rick)", "DECIDED? not yet, waiting on Richard"),
            "lower case": head + row.replace("DECIDED 2026", "decided 2026"),
            "decorated": head + row.replace("DECIDED 2026", "**DECIDED** 2026"),
            "no date": head + row.replace("DECIDED 2026-11-15 (Rick)", "DECIDED (Rick)"),
            "superseded": head + row.replace("(Rick) |", "(Rick). SUPERSEDED by D60 |"),
            "no owner": head + row.replace("| Richard | DECIDED", "| – | DECIDED"),
            "agent decides": head + row.replace("(Rick)", "(agent)"),
            "producer decides": head + row.replace("(Rick)", "(Josh)"),
        }
        for name, text in near.items():
            with self.subTest(name):
                self.assertEqual(mc.decided_overrides(text), set())
                self.assertIn("p0-on", kinds(text))
        self.assertIn("overrides", kinds(near["DECIDED?"]), "a near-miss DECIDED row with Overrides fails loudly")
        self.assertIn("overrides", kinds(near["agent decides"]))
        self.assertNotIn("overrides", kinds(cut.replace("DECIDED 2026-11-15 (Rick)", "open")), "a proposal is fine")
        # the real decisions file overrides nothing today
        # D-new-creative-director-feel: the only counted overrides are the feel-speed keys Josh signed.
        self.assertEqual(mc.decided_overrides(mc.read_decisions(ROOT)), set(mc.FEEL_KEYS))

    def test_base_preset_changes_nothing_and_presets_enable_only_authorized(self):
        """Dry run B H6."""
        man, snap, presets = real()
        for k, ids in (("disable", ["WIND-01", "OWL-05"]), ("enable", ["SURV-04", "MOVE-02"])):
            p = copy.deepcopy(presets)
            p["presets"][0][k] = ids
            with self.subTest(k=k):
                self.assertIn("presets", self.kinds(man, presets=p))
        p = copy.deepcopy(presets)
        next(x for x in p["presets"] if x["id"] == "T-05")["enable"] = ["WIND-02"]
        self.assertIn("presets", self.kinds(man, presets=p), "an unauthorized experiment is never enabled")
        rec(man, "WIND-02").update(implementation_authorized=True, ticket="#77")
        self.assertNotIn("presets", self.kinds(man, presets=p), "an EXPERIMENT with a ticket may be enabled")

    def test_qa_test_dropped_from_every_record_is_caught(self):
        man, _, _ = real()
        for f in man["features"]:
            f["tests"] = [t for t in f["tests"] if t != "QA-12"]
        self.assertIn("gdd", self.kinds(man))

    def test_presets(self):
        man, _, presets = real()
        p = copy.deepcopy(presets)
        p["presets"] = p["presets"][:-1]
        self.assertIn("presets", self.kinds(man, presets=p))
        p = copy.deepcopy(presets)
        p["presets"][1]["enable"].append("UMB-77")
        self.assertIn("presets", self.kinds(man, presets=p))

    def test_unapproved_feature_is_never_on(self):
        """Dry run B C1: default_enabled true needs implementation_authorized and an APPROVED status."""
        man, _, _ = real()
        self.assertNotIn("off", self.kinds(man))
        for fid in ("NAR-01", "COM-02", "COM-03", "COM-04", "SURV-04", "CAM-02", "MOVE-02", "MOVE-03", "UMB-03"):
            m = copy.deepcopy(man)
            rec(m, fid).update(default_enabled=True)
            with self.subTest(fid):
                self.assertIn("off", self.kinds(m))
        m = copy.deepcopy(man)
        rec(m, "WIND-02").update(default_enabled=True, implementation_authorized=True, ticket="#77")
        self.assertIn("off", self.kinds(m), "an EXPERIMENT with a ticket may be built, never shipped on")

    def test_overrides_never_lift_the_gdd_off_rule(self):
        """Dry run B M1."""
        man, snap, presets = real()
        rec(man, "WIND-02").update(default_enabled=True)
        d = ("| ID | Decision | Owner | Status |\n|---|---|---|---|\n"
             "| D-wind | Wind wear on. Overrides: WIND-02 | Richard | DECIDED 2026-11-15 (Rick) |\n")
        self.assertIn("gdd-status", {k for k, _, _ in mc.problems(man, snap, presets, d)})

    def test_snapshot_pins(self):
        """Dry run B H9: snapshots are pinned by sha256; an edit in place, an unpinned file or a changed pin fails."""
        import shutil
        man, _, _ = current()
        self.assertEqual(mc.pin_problems(man, ROOT, old_manifest=man), [])
        root = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "docs", "gdd"), os.path.join(root, "docs", "gdd"))
            self.assertEqual(mc.pin_problems(man, root), [])
            snap = os.path.join(root, "docs", "gdd", "GDD-1.3.md")
            with open(snap, "rb") as fh:
                raw = fh.read()
            with open(snap, "wb") as fh:
                fh.write(raw.replace(b"\n", b"\r\n"))
            self.assertEqual(mc.pin_problems(man, root), [], "a CRLF checkout hashes the same")
            with open(snap, "wb") as fh:
                fh.write(raw.replace(b"| DEF-01 |", b"| DEF-01 | PROPOSED / OFF |", 1))
            self.assertIn("pin", {k for k, _, _ in mc.pin_problems(man, root)}, "an edit in place fails")
            with open(snap, "wb") as fh:
                fh.write(raw)
            with open(os.path.join(root, "docs", "gdd", "GDD-1.4.md"), "w") as fh:
                fh.write("# GDD snapshot 1.4\n\n| Field | Value |\n|---|---|\n| Revision | 1.4 |\n")
            self.assertIn("pin", {k for k, _, _ in mc.pin_problems(man, root)}, "an unpinned snapshot fails")
            with open(os.path.join(root, "docs", "gdd", "CURRENT"), "w") as fh:
                fh.write("GDD-1.4.md\n")
            m = copy.deepcopy(man)
            m["gdd_snapshot"] = "docs/gdd/GDD-1.4.md"
            m["gdd_snapshots"]["docs/gdd/GDD-1.4.md"] = mc.snapshot_sha256(os.path.join(root, "docs", "gdd", "GDD-1.4.md"))
            self.assertEqual(mc.pin_problems(m, root, old_manifest=man), [], "a new revision adds a pin: honest path")
            m2 = copy.deepcopy(m)
            m2["gdd_snapshots"]["docs/gdd/GDD-1.3.md"] = "0" * 64
            self.assertIn("pin", {k for k, _, _ in mc.pin_problems(m2, root, old_manifest=man)}, "a re-pin fails")
            m3 = copy.deepcopy(m)
            del m3["gdd_snapshots"]["docs/gdd/GDD-B1.0.md"]
            os.remove(os.path.join(root, "docs", "gdd", "GDD-B1.0.md"))
            self.assertIn("pin", {k for k, _, _ in mc.pin_problems(m3, root, old_manifest=man)}, "a dropped pin fails")
        finally:
            shutil.rmtree(root)

    def test_rules_pdf_pin(self):
        """The Official Rules PDF is pinned like a GDD snapshot: the real file or its LFS pointer passes; a changed PDF,
        an unpinned second PDF, a drifted header or a dropped pin fails."""
        import shutil
        man, _, _ = current()
        self.assertEqual(mc.rules_pin_problems(man, ROOT), [])
        root = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "docs", "rules"), os.path.join(root, "docs", "rules"))
            pdf_rel = next(iter(man["rules_pdf"]))
            pdf = os.path.join(root, pdf_rel)
            want = man["rules_pdf"][pdf_rel]
            self.assertEqual(mc.rules_pin_problems(man, root), [])
            with open(pdf, "w") as fh:   # CI checks out with lfs: false
                fh.write(f"version https://git-lfs.github.com/spec/v1\noid sha256:{want}\nsize 541000\n")
            self.assertEqual(mc.rules_pin_problems(man, root), [], "an LFS pointer with the pinned oid passes")
            with open(pdf, "w") as fh:
                fh.write(f"version https://git-lfs.github.com/spec/v1\noid sha256:{'1' * 64}\nsize 541000\n")
            self.assertIn("rules-pin", {k for k, _, _ in mc.rules_pin_problems(man, root)}, "a new PDF, pin not moved")
            with open(pdf, "wb") as fh:
                fh.write(b"%PDF-1.7 edited")
            self.assertIn("rules-pin", {k for k, _, _ in mc.rules_pin_problems(man, root)}, "edited bytes fail")
            shutil.copy(os.path.join(ROOT, pdf_rel), pdf)
            shutil.copy(pdf, os.path.join(root, "docs", "rules", "rules-v2.pdf"))
            self.assertIn("rules-pin", {k for k, _, _ in mc.rules_pin_problems(man, root)}, "an unpinned PDF fails")
            os.remove(os.path.join(root, "docs", "rules", "rules-v2.pdf"))
            txt = os.path.join(root, mc.RULES_TEXT)
            with open(txt, encoding="utf-8") as fh:
                body = fh.read()
            with open(txt, "w", encoding="utf-8") as fh:
                fh.write(body.replace(want, "0" * 64, 1))
            self.assertIn("rules-pin", {k for k, _, _ in mc.rules_pin_problems(man, root)}, "a drifted header fails")
            m = copy.deepcopy(man)
            del m["rules_pdf"]
            self.assertIn("rules-pin", {k for k, _, _ in mc.rules_pin_problems(m, ROOT)}, "a dropped pin fails")
        finally:
            shutil.rmtree(root)

    def test_current_target_is_pinned_whatever_its_name(self):
        """Final-7 B H1: CURRENT pointed at an edited, unpinned copy of 1.3 (gdd-1.3-errata.md) and every check passed."""
        import shutil
        man, _, _ = current()
        root = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "docs", "gdd"), os.path.join(root, "docs", "gdd"))
            gdd = os.path.join(root, "docs", "gdd")
            self.assertEqual(mc.pin_problems(man, root), [])
            with open(os.path.join(gdd, "GDD-1.3.md"), encoding="utf-8") as fh:
                raw = fh.read()
            cases = {
                "renamed copy": ("gdd-1.3-errata.md", raw.replace("| DEF-01 |", "| DEF-01 | PROPOSED / OFF |", 1),
                                 "must name a docs/gdd/GDD-<revision>.md"),
                "name says 1.4, file says 1.3": ("GDD-1.4.md", raw, "that file's Revision is 1.3"),
                "outside docs/gdd": ("../GDD-1.3.md", raw, "must name a docs/gdd/GDD-<revision>.md"),
            }
            for name, (fname, text, why) in cases.items():
                with self.subTest(name):
                    if "/" not in fname:
                        with open(os.path.join(gdd, fname), "w", encoding="utf-8") as fh:
                            fh.write(text)
                    with open(os.path.join(gdd, "CURRENT"), "w") as fh:
                        fh.write(fname + "\n")
                    m = copy.deepcopy(man)
                    m["gdd_snapshot"] = "docs/gdd/" + fname
                    if "/" not in fname:   # even pinned, the attack fails
                        m["gdd_snapshots"]["docs/gdd/" + fname] = mc.snapshot_sha256(os.path.join(gdd, fname))
                    got = mc.pin_problems(m, root, old_manifest=man)
                    self.assertTrue(any(why in msg for _, _, msg in got), got)
                    if "/" not in fname:
                        os.remove(os.path.join(gdd, fname))
            # a same-revision copy under the right name pattern: GDD-1.3b would read Revision 1.3
            with open(os.path.join(gdd, "GDD-1.3.md"), "w", encoding="utf-8") as fh:
                fh.write(raw)
            with open(os.path.join(gdd, "CURRENT"), "w") as fh:
                fh.write(os.path.basename(man["gdd_snapshot"]) + "\n")
            self.assertEqual(mc.pin_problems(man, root), [])
        finally:
            shutil.rmtree(root)

    def test_note(self):
        good = {"commit": "abc1234", "gdd_revision": "B1.0", "test_id": "QA-04", "preset": "T-03", "seed": 7,
                "date": "2026-11-13", "what_changed": "catch_window 0.2 s -> 0.3 s", "observed": "caught 4 of 6",
                "ratings": {"fun": 4, "fairness": 3, "readability": 4, "responsiveness": 5},
                "decision": "retest", "owner": "Rick", "rationale": "window felt late"}
        self.assertEqual(mc.note_problems(good), [])
        for k, v in [("ratings", {"fun": 6}), ("decision", "maybe"), ("what_changed", ["a", "b"]), ("seed", "x")]:
            with self.subTest(field=k):
                self.assertTrue(mc.note_problems(dict(good, **{k: v})))
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(good, fh)
        try:
            self.assertEqual(mc.main(["--note", fh.name]), 0)
        finally:
            os.remove(fh.name)


class GraceDefaultRows(unittest.TestCase):
    """A 2 h grace default row in docs/decisions.md (pipeline/human-checkpoints.md): the exact Status form counts as
    DECIDED; it is rejected on the human-only kinds, on an Overrides (P0) row and on approved_parameters ranges."""
    HEAD = "| ID | Decision needed | Owner | Status |\n|---|---|---|---|\n"
    ROW = ("| D-new-ui-17 | Title screen: press any key, or a Start button? | Producer / time keeper, human | "
           "DECIDED 2026-11-12 (agent default after 2h grace; Producer; human may overturn). Chose a Start button; "
           "needs-human #17 |\n")

    def kinds(self, text):
        man, snap, presets = real()
        return {k for k, _, _ in mc.problems(man, snap, presets, text)}

    def test_grace_row_passes(self):
        for role in mc.GRACE_ROLES:
            with self.subTest(role):
                text = self.HEAD + self.ROW.replace("; Producer;", f"; {role};")
                self.assertEqual(mc.grace_problems(text), [])
                self.assertNotIn("grace", self.kinds(text))
        self.assertEqual(mc.grace_problems(mc.read_decisions(ROOT)), [])

    def test_broken_grace_rows_fail(self):
        row = self.ROW
        broken = {
            "role not a director": row.replace("; Producer;", "; Gameplay Dev;"),
            "no 'human may overturn'": row.replace("; human may overturn", ""),
            "3h, not 2h": row.replace("after 2h grace", "after 3h grace"),
            "no issue link": row.replace("needs-human #17", "needs-human issue"),
            "submission": row.replace("Title screen: press any key, or a Start button?", "Submit the Draft at G2?"),
            "packaging": row.replace("Title screen: press any key, or a Start button?", "Which packaging machine?"),
            "playtest": row.replace("Title screen: press any key, or a Start button?", "Skip playtest P4?"),
            "guardrail": row.replace("Title screen: press any key, or a Start button?", "Loosen a hook in tools/?"),
            "model tier": row.replace("Title screen: press any key, or a Start button?", "Change a model tier?"),
            "delete": row.replace("Title screen: press any key, or a Start button?", "Delete the old owl art?"),
            "range": row.replace("Title screen: press any key, or a Start button?", "Widen approved_parameters?"),
        }
        for name, r in broken.items():
            with self.subTest(name):
                self.assertTrue(mc.grace_problems(self.HEAD + r), name)
                self.assertIn("grace", self.kinds(self.HEAD + r))
        self.assertTrue(mc.grace_problems(row), "a grace row outside the Open decisions table fails")

    def test_grace_row_never_overrides_a_p0(self):
        man, snap, presets = real()
        rec(man, "DEF-01").update(default_enabled=False)
        cut = self.HEAD + self.ROW.replace("Chose a Start button", "Ship without the shield. Overrides: DEF-01")
        self.assertEqual(mc.decided_overrides(cut), set())
        got = mc.problems(man, snap, presets, cut)
        self.assertIn("p0-on", {k for k, _, _ in got}, "DEF-01 stays on: a grace row lifts no P0 rule")
        self.assertTrue([w for k, _, w in got if k == "overrides" and "grace default" in w], got)
        # the same row decided by the design owner does count (the passing side of the same check)
        richard = cut.replace("DECIDED 2026-11-12 (agent default after 2h grace; Producer; human may overturn)",
                              "DECIDED 2026-11-12 (Rick)")
        self.assertEqual(mc.decided_overrides(richard), {"DEF-01"})
        # GDD SH1.0: Rick approves the statuses, so the 1.3 design owner's name no longer lifts a P0
        self.assertEqual(mc.decided_overrides(richard.replace("(Rick)", "(Richard)")), set())


class StolenHourImport(unittest.TestCase):
    """GDD SH1.0 (Ricky, 2026-11-12): its Rule IDs and APPROVED_P0 words are recognized, nothing is dropped."""

    def test_every_rule_id_is_a_p0_record(self):
        man, snap, _ = current()
        stated = gi.snapshot_statuses(snap)
        self.assertEqual(len(stated), 204)
        self.assertEqual({f["feature_id"] for f in man["features"]}, set(stated))
        for f in man["features"]:
            self.assertEqual((f["status"], f["priority"], f["default_enabled"], f["implementation_authorized"]),
                             ("APPROVED_P0", "P0", True, True), f["feature_id"])
        qa = {t for f in man["features"] for t in f["tests"]}
        self.assertEqual(qa, {f"QA-{n}" for n in range(29, 43)})

    def test_idless_rows_are_kept_and_checked(self):
        man, snap, presets = current()
        rows = gi.idless_rows(snap)
        self.assertEqual(sum(1 for r in rows if r[2] == "APPROVED_P0"), 7)
        self.assertEqual(sum(1 for r in rows if r[2] == "OPEN"), 5)
        breaks = {
            "one dropped": lambda m: m["approved_without_id"].pop(3),
            "wrong order": lambda m: m["approved_without_id"].reverse(),
            "carried by nothing": lambda m: m["approved_without_id"][0].update(carried_by="nobody"),
            "carried by an unknown ID": lambda m: m["approved_without_id"][1].update(carried_by="FLOW-99"),
            "demoted": lambda m: m["approved_without_id"][2].update(status="OPEN"),
            "open rows dropped": lambda m: m.update(open_without_id=[]),
        }
        for name, fn in breaks.items():
            m = copy.deepcopy(man)
            fn(m)
            with self.subTest(name):
                self.assertIn("idless", {k for k, _, _ in mc.problems(m, snap, presets)})

    def test_blank_parameter_tables_import_and_prose_starts_match(self):
        man, snap, _ = current()
        self.assertEqual(mc.section_5a_rows(snap), {}, "the template rows are blanks, not parameters")
        self.assertEqual(mc.section_5a_tables(snap), 3)
        self.assertEqual(mc.approved_problems(man, snap), [])
        vals = man["approved_parameters"]["values"]
        self.assertEqual(vals["FLOW-33.chain_damage"]["start"], 1.25)
        for key, bad in (("MOVE-21.rise_speed", {"start": 300}), ("OWL-08.clock_hp", {"start": 320, "min": 0})):
            m = copy.deepcopy(man)
            m["approved_parameters"]["values"][key] = dict(m["approved_parameters"]["values"][key], **bad)
            with self.subTest(key):
                self.assertTrue(mc.approved_problems(m, snap))
        m = copy.deepcopy(man)
        m["approved_parameters"]["values"]["MOVE-21.gravity"] = {"start": 980}
        self.assertTrue(mc.approved_problems(m, snap), "a number the GDD does not print fails")

    def test_sounds_of_a_feature_the_new_gdd_removed_do_not_pin(self):
        man, _, _ = current()
        old, _, _ = real()
        self.assertEqual(mc.sound_pin_problems(man, old), [], "GDD SH1.0 removed OWL-01, DEF-01, ...")
        same = copy.deepcopy(old)
        rec(same, "OWL-01").update(sounds=["OwlBoltLaunch"])
        self.assertIn("sounds", {k for k, _, _ in mc.sound_pin_problems(same, old)}, "same revision: still append-only")

    def test_authoring_guidance_is_not_a_citation(self):
        _, snap, _ = current()
        self.assertIn("QA-BASE", gi.body(snap))
        self.assertNotIn("QA-BASE", gi.cited_body(snap))
        self.assertIn("FLOW-02", gi.cited_body(snap))


if __name__ == "__main__":
    unittest.main()

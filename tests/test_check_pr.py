import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_pr  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hermetic  # noqa: E402

# final-9 A C1: these tests check the PR rules, not the jam's progress. check_pr reads repo state (the smoke hook,
# the QA-01 row, the marked defaults), so its default root here is the pre-jam copy (tests/hermetic.py); a test that
# needs another state passes root= itself.
_problems = check_pr.problems


def _hermetic_problems(body, changed=None, head=None, root=None, card=None, base=None):
    return _problems(body, changed, head, root or hermetic.pre_jam_root(), card, base)


check_pr.problems = _hermetic_problems

GOOD = """## Task
Closes #21. Card ID: UE-004  Owner role: Gameplay Dev  Reviewer role: Dev Lead
## What changed
Source/UmbrellaElla/Private/EllaCharacter.cpp
## Done-when checks
- [x] build passes
## Evidence
commit=abc1234 engine=5.8.4 config=Development host=win run=packaged
PASS  tests=14 failed=0  commit=abc1234
build exit: 0  mode=nonunity  commit=abc1234  warnings: 0  log: Saved/Logs/pipeline/build-1.log
## Not done / risks
none
Could not read: none
Next: Dev Lead reviews
## Binary assets touched
none
""" + """## Journal
### Journal
`journal.py export card=UE-004 machine=win-1 commit=abc1234 events=6`
| # | UTC | Exit | Command |
|---|---|---|---|
| 3 | 2026-11-12T10:00:00Z | 0 | `tools/ue/build.sh` |
Last checkpoint: 2026-11-12T10:05:00Z gameplay-dev: built and tested
Next step: Dev Lead reviews
"""
JOURNAL = GOOD[GOOD.index("## Journal"):]


class CheckPrTests(unittest.TestCase):
    def test_good_body_passes(self):
        self.assertEqual(check_pr.problems(GOOD), [])

    # GDD B: a PR that changes docs/gdd/ or the feature manifest pastes the gdd_impact list
    IMPACT = ("## GDD impact\ngdd_impact old=B1.0 new=B1.1 added=0 removed=0 changed=1 status=1 cited=1\n"
              "status: UMB-03 PROPOSED -> APPROVED_P1\ncited by:\n  pipeline/qa/test-map.md:27 [test-map row QA-04] UMB-03\n")

    def test_gdd_change_needs_impact_list(self):
        for path in ("docs/gdd/GDD-B1.1.md", "docs/feature-manifest.json", "docs/gdd/CURRENT"):
            with self.subTest(path=path):
                self.assertTrue(any("gdd_impact" in p for p in check_pr.problems(GOOD, [path])))
                self.assertEqual(check_pr.problems(GOOD + self.IMPACT, [path]), [])
        body = GOOD.replace("Source/UmbrellaElla/Private/EllaCharacter.cpp", "docs/feature-manifest.json")
        self.assertTrue(any("gdd_impact" in p for p in check_pr.problems(body)))
        half = GOOD + self.IMPACT.split("status:")[0]   # the summary line without the cited-by list
        self.assertTrue(any("gdd_impact" in p for p in check_pr.problems(half, ["docs/gdd/CURRENT"])))
        self.assertEqual(check_pr.problems(GOOD, ["docs/decisions.md"]), [])

    # Journal (AGENTS.md section 6): the PR body carries the journal.py export block for its card
    def test_missing_journal_section_fails(self):
        body = GOOD.replace(JOURNAL, "")
        self.assertIn("missing section '## Journal'", check_pr.problems(body))

    def test_journal_without_export_block_fails(self):
        body = GOOD.replace(JOURNAL, "## Journal\nran the build, all fine\n")
        self.assertTrue(any("journal.py export" in p for p in check_pr.problems(body)))

    def test_journal_for_another_card_fails(self):
        body = GOOD.replace("card=UE-004", "card=UE-9")
        self.assertTrue(any("Card ID is UE-004" in p for p in check_pr.problems(body)))

    def test_human_card_needs_no_journal_export(self):
        # Final-7 A M4: card 0.0 is human work with no agent.sh session
        body = GOOD.replace(JOURNAL, "## Journal\nHuman card, no agent session\n")
        human = {"title": "0.0", "body": "### Owner role\n\nHuman\n\n### Done when\n\nx\n"}
        agent = {"title": "0.6", "body": "### Owner role\n\nGameplay Dev\n\n### Done when\n\nx\n"}
        self.assertEqual(check_pr.problems(body, card=human), [])
        # broken on purpose: an agent card, or no card at all, still needs the export
        for card in (agent, None):
            with self.subTest(card=card and card["title"]):
                self.assertTrue(any("journal.py export" in p for p in check_pr.problems(body, card=card)))

    def test_journal_without_next_step_fails(self):
        body = GOOD.replace("Next step: Dev Lead reviews\n", "")
        self.assertTrue(any("Next step" in p for p in check_pr.problems(body)))

    def test_real_export_output_passes(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, JOURNAL_DB=os.path.join(d, "j.db"))
            run = lambda *a: subprocess.run([sys.executable, os.path.join(ROOT, "tools", "journal.py"), *a],  # noqa: E731
                                            env=env, capture_output=True, text=True, check=True).stdout
            run("start", "--card", "UE-004", "--role", "gameplay-dev")
            run("step", "--card", "UE-004", "--cmd", "tools/ue/build.sh", "--exit", "0")
            run("checkpoint", "--card", "UE-004", "--note", "built", "--next", "Dev Lead reviews")
            block = run("export", "--card", "UE-004")
        self.assertEqual(check_pr.problems(GOOD.replace(JOURNAL, "## Journal\n" + block)), [])

    def test_untouched_template_fails(self):
        with open(os.path.join(ROOT, ".github", "PULL_REQUEST_TEMPLATE.md")) as fh:
            self.assertGreaterEqual(len(check_pr.problems(fh.read())), 5)

    def test_missing_evidence_fails(self):
        body = GOOD.replace("PASS  tests=14 failed=0  commit=abc1234\n", "").replace(CheckPrTests.NONUNITY_LINE, "")
        self.assertIn("section '## Evidence' is empty or still the template", check_pr.problems(body))

    def test_na_evidence_fails(self):
        body = GOOD.replace("PASS  tests=14 failed=0  commit=abc1234", "n/a").replace(CheckPrTests.NONUNITY_LINE, "")
        self.assertTrue(check_pr.problems(body))

    def test_no_issue_link_fails(self):
        self.assertTrue(check_pr.problems(GOOD.replace("Closes #21.", "")))

    # Evidence header (AGENTS.md section 5)
    def test_missing_header_fails(self):
        body = GOOD.replace("commit=abc1234 engine=5.8.4 config=Development host=win run=packaged\n", "")
        self.assertTrue(any("header line" in p for p in check_pr.problems(body)))

    def test_header_missing_one_key_fails(self):
        body = GOOD.replace(" host=win", "")
        self.assertTrue(any("header line" in p for p in check_pr.problems(body)))

    def test_header_matching_head_passes(self):
        self.assertEqual(check_pr.problems(GOOD, head="abc1234deadbeef"), [])

    def test_stale_header_fails(self):
        self.assertTrue(any("stale" in p for p in check_pr.problems(GOOD, head="fff0000deadbeef")))

    # Package evidence when the changed paths need it
    PKG = ("package exit: 0  commit=abc1234  dirty=no  target=UmbrellaElla  log: Saved/Logs/pipeline/package-1.log\nsmoke: exit=0 SMOKE_OK=yes\ncrash folders: 0 new\n"
           "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=0")

    # Day-1 bootstrap (dry run A C1): card 0.3 changes the .uproject and Config/ before the smoke hook
    # (card 0.6) or MVP 2 exist. Each waiver is tied to repo state, so it ends by itself.
    # The smoke's own art lines (tools/ue_run.py shot_checks), as smoke.sh / smoke.ps1 print them
    ART_OK = ("smoke-art: art_check: PASS shot=smoke-game-1-shot.png\n"
              "smoke-art: screen_check: PASS image=smoke-game-1-shot.png size=1920x1080 view=1920x1080 aspect=1.778 "
              "bars=none flat=0 grey=0 outline=0\n"
              "smoke-art: art_judge: PASS scene score=0.81 shot=smoke-game-1-shot.png\n")

    def boot_root(self, smoke_hook=False, qa01="planned", qagp=None, anchors=False):
        import tempfile
        root = tempfile.mkdtemp()
        os.makedirs(os.path.join(root, "pipeline", "qa"))
        with open(os.path.join(root, "pipeline", "qa", "test-map.md"), "w") as f:
            f.write("| QA | Features | Required tests | Card | Status |\n|---|---|---|---|---|\n"
                    f"| QA-01 | UMB-01 | `UmbrellaElla.Umbrella.OpenRises` | #9 | {qa01} |\n"
                    + (f"| QA-GP | QA-BASE | `UmbrellaElla.Smoke.GamepadReachesMoveAttackShield` | | {qagp} |\n"
                       if qagp else ""))
        if smoke_hook:
            os.makedirs(os.path.join(root, "Source", "UmbrellaElla", "Private", "Smoke"))
        if anchors:
            os.makedirs(os.path.join(root, "Content", "UmbrellaElla", "Art", "Anchors"))
        os.makedirs(os.path.join(root, "docs"))
        import shutil
        shutil.copy(os.path.join(ROOT, "docs", "feature-manifest.json"), os.path.join(root, "docs"))
        return root

    def art_body(self, art):
        smoke = ("package exit: 0  commit=abc1234  dirty=no  log: Saved/Logs/pipeline/package-1.log\n"
                 "smoke: exit=0 SMOKE_OK=yes\ncrash folders: 0 new\n"
                 "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 "
                 "commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=0\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=start commit=abc1234 workbench=0 platform=Mac\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=end commit=abc1234 workbench=0 platform=Mac\n" + art)
        return GOOD.replace("PASS  tests=14", smoke + "\nPASS  tests=14")

    def test_smoke_evidence_needs_the_art_and_screen_pass_lines(self):
        """Josh: art checks are automatic; CI rejects pasted smoke evidence without the smoke's own art lines."""
        root = self.boot_root(smoke_hook=True, qa01="merged", anchors=True)
        ch = ["Config/DefaultGame.ini"]
        self.assertEqual(check_pr.problems(self.art_body(self.ART_OK), changed=ch, root=root), [])
        # broken on purpose: no art lines, one missing, a FAIL, a bootstrap line after the anchors exist
        for art, want in [("", "smoke-art: art_check: PASS"),
                          (self.ART_OK.split("\n")[1] + "\n", "smoke-art: art_check: PASS"),
                          (self.ART_OK.replace("screen_check: PASS", "screen_check: FAIL"), "screen_check: FAIL"),
                          (self.ART_OK.replace("art_check: PASS", "art_check: FAIL"), "art_check: FAIL"),
                          (self.ART_OK.replace("art_judge: PASS", "art_judge: FAIL"), "art_judge: FAIL"),
                          (self.ART_OK.split("smoke-art: art_judge")[0], "smoke-art: art_judge: PASS"),
                          (self.ART_OK + "smoke-art: bootstrap: not blocking until x\n", "block now")]:
            with self.subTest(want=want, art=art[:30]):
                found = check_pr.problems(self.art_body(art), changed=ch, root=root)
                self.assertTrue(any(want in p for p in found), found)

    def test_art_bootstrap_accepts_a_fail_only_before_the_anchors(self):
        art = self.ART_OK.replace("art_check: PASS", "art_check: FAIL") + \
            "smoke-art: bootstrap: not blocking until Content/UmbrellaElla/Art/Anchors/ exists (card 0.10b)\n"
        ch = ["Config/DefaultGame.ini"]
        self.assertEqual(check_pr.problems(self.art_body(art), changed=ch,
                                           root=self.boot_root(smoke_hook=True, qa01="merged")), [])
        found = check_pr.problems(self.art_body(art), changed=ch + ["Content/UmbrellaElla/Art/Anchors/T_Ella.uasset"],
                                  root=self.boot_root(smoke_hook=True, qa01="merged"))
        self.assertTrue(any("art_check: FAIL" in p for p in found), found)

    def test_visual_paths_need_package_and_smoke(self):
        for path in ("Content/UmbrellaElla/Art/WindZone/T_WindZone.uasset",
                     "Source/UmbrellaElla/Private/UI/HudWidget.cpp", "Source/UmbrellaElla/Private/Feedback/WindCue.cpp",
                     "pipeline/art/visual-align.json"):
            with self.subTest(path=path):
                self.assertIn("visual path", check_pr.needs_package({}, [path]) or "")
        self.assertIsNone(check_pr.needs_package({}, ["Source/UmbrellaElla/Private/Motor/Motor.cpp"]))

    def test_smoke_line_needs_16x9_view_and_debugdraw_off(self):
        root = self.boot_root(smoke_hook=True, qa01="merged", anchors=True)
        ch = ["Config/DefaultGame.ini"]
        good = "view=1920x1080 aspect=1.778 debugdraw=0"
        for bad, want in [("view=2560x1080 aspect=2.370 debugdraw=0", "not 16:9"),      # the ~1.85:1 build, unlocked
                          ("view=1998x1080 aspect=1.850 debugdraw=0", "not 16:9"),
                          ("view=1920x1080 aspect=1.850 debugdraw=0", "disagrees"),
                          ("debugdraw=0", "no view=WxH"),
                          ("view=1920x1080 aspect=1.778 debugdraw=1", "debugdraw=1"),   # hitbox draws on by default
                          ("view=1920x1080 aspect=1.778", "debugdraw=<none>")]:
            with self.subTest(bad=bad):
                found = check_pr.problems(self.art_body(self.ART_OK).replace(good, bad), changed=ch, root=root)
                self.assertTrue(any(want in p for p in found), found)

    def artref(self, ev, changed, card="UE-31"):
        sec = {"Task": f"Part of #12. Card ID: {card}  Owner role: Asset Specialist  Reviewer role: Art Director",
               "Evidence": "commit=abc1234 engine=5.8.4 config=Development host=win run=packaged\n" + ev}
        return check_pr.artref_problems(sec, changed, ROOT)

    def ref_line(self, card="0.10b", refs=None, commit="abc1234", v="PASS"):
        import art_judge
        return (f"art_ref_check: {v} card={card} target=element:owl score=0.71 min=0.5 "
                f"refs={refs or art_judge.refs_hash()} commit={commit} file=owl.png\n")

    def test_art_paths_need_the_art_ref_check_pass_line(self):
        """Josh: referencing the art is enforced in code (rule artref), including pipeline/art/** edits."""
        for path in ("Content/UmbrellaElla/Art/Owl/T_Owl.uasset", "Art/Source/Owl/Owl.psd",
                     "pipeline/art/art-bible.md", "Art/Source/Owl/owl.sprite.json"):
            with self.subTest(path=path):
                self.assertTrue(any("art_ref_check: PASS" in p for p in self.artref("", [path])))
                found = self.artref(self.ref_line(), [path])
                if path.endswith(".uasset"):   # rule artship: an art asset also needs its image's art-loop pass
                    self.assertEqual(len(found), 1, found)
                    self.assertIn("ships art", found[0])
                else:
                    self.assertEqual(found, [])
        self.assertEqual(self.artref("", ["Source/UmbrellaElla/Private/Motor/Motor.cpp"]), [])

    def test_art_ref_check_line_broken_on_purpose(self):
        ch = ["Content/UmbrellaElla/Art/Owl/T_Owl.uasset"]
        for ev, want in [(self.ref_line(refs="000000000000"), "older or smaller reference set"),
                         (self.ref_line(commit="def5678"), "not the evidence header commit"),
                         (self.ref_line(v="FAIL"), "art_ref_check: FAIL")]:
            with self.subTest(want=want):
                self.assertTrue(any(want in p for p in self.artref(ev, ch)), self.artref(ev, ch))

    def test_art_card_needs_every_piece_through_the_art_loop(self):
        import art_judge
        import art_loop
        refs = art_judge.load_refs()
        pieces = art_loop.pieces(refs, "0.10b")
        self.assertIn("owl", pieces)
        rh = art_judge.refs_hash()
        loop = "".join(f"art_loop: PASS card=0.10b piece={p} verdict=same rounds=4 refs={rh} commit=abc1234\n"
                       for p in pieces)
        self.assertEqual(self.artref(self.ref_line() + loop, [], card="UE-0.10b"), [])
        found = self.artref(self.ref_line(), [], card="UE-0.10b")            # no loop lines: refused
        self.assertTrue(any("have no `art_loop: PASS` line" in p for p in found), found)
        short = loop.replace(f"piece={pieces[0]} ", "piece=other ")           # one piece missing
        self.assertTrue(any(pieces[0] in p for p in self.artref(self.ref_line() + short, [], card="UE-0.10b")))
        stale = loop.replace(f"refs={rh}", "refs=000000000000")
        self.assertTrue(any("loop again" in p for p in self.artref(self.ref_line() + stale, [], card="UE-0.10b")))
        other = self.ref_line(card="0.10c")
        self.assertTrue(any("names card=0.10b" in p for p in self.artref(other + loop, [], card="UE-0.10b")))

    BOOT = "package exit: 0  commit=abc1234  dirty=no  log: Saved/Logs/pipeline/package-1.log\nSMOKE_BOOTSTRAP: no smoke hook before card 0.6"

    def test_card_03_merges_before_the_smoke_hook(self):
        body = GOOD.replace("PASS  tests=14", self.BOOT + "\nPASS  tests=14")
        ch = ["UmbrellaElla.uproject", "Config/DefaultGame.ini"]
        self.assertEqual(check_pr.problems(body, changed=ch, root=self.boot_root()), [])
        # broken on purpose: once card 0.6 merged (or this PR adds it), the bootstrap line is refused
        found = check_pr.problems(body, changed=ch, root=self.boot_root(smoke_hook=True))
        self.assertTrue(any("SMOKE_BOOTSTRAP" in p for p in found), found)
        found = check_pr.problems(body, changed=ch + ["Source/UmbrellaElla/Private/Smoke/SmokeHook.cpp"],
                                  root=self.boot_root())
        self.assertTrue(any("SMOKE_BOOTSTRAP" in p for p in found), found)
        # the bootstrap never replaces `package exit: 0`, and "not run" still fails
        nopkg = GOOD.replace("PASS  tests=14", "SMOKE_BOOTSTRAP: no smoke hook before card 0.6\nPASS  tests=14")
        self.assertTrue(check_pr.problems(nopkg, changed=ch, root=self.boot_root()))
        nr = GOOD.replace("PASS  tests=14", "Not run: package and smoke, no machine\nPASS  tests=14")
        self.assertTrue(check_pr.problems(nr, changed=ch, root=self.boot_root()))

    def test_editor_asset_needs_human_check(self):
        """Editor MCP guardrail: a changed .uasset/.umap is opened and checked by the card's human."""
        ch = ["Content/UmbrellaElla/Art/T_Sky.uasset", "Content/UmbrellaElla/Maps/L_Graybox.umap"]
        line = "EDITOR CHECK: by=Rick opened=Content/UmbrellaElla/Art/T_Sky.uasset,Content/UmbrellaElla/Maps/L_Graybox.umap ok"
        s = {"Evidence": "commit=abc1234 engine=5.8.4\n" + line, "What changed": ""}
        self.assertEqual(check_pr.editor_problems(s, ch), [])
        self.assertEqual(check_pr.editor_problems({"Evidence": "", "What changed": ""}, ["Source/A.cpp"]), [])
        # broken on purpose: no line, one asset left out, a placeholder name
        self.assertTrue(check_pr.editor_problems({"Evidence": "PASS", "What changed": ""}, ch))
        part = {"Evidence": "EDITOR CHECK: by=Rick opened=Content/UmbrellaElla/Art/T_Sky.uasset ok", "What changed": ""}
        self.assertIn("L_Graybox.umap", check_pr.editor_problems(part, ch)[0])
        self.assertTrue(check_pr.editor_problems({"Evidence": line.replace("Rick", "<name>"), "What changed": ""}, ch))

    def test_input_none_only_before_mvp2_with_require_input_off(self):
        smoke = ("package exit: 0  commit=abc1234  dirty=no  log: Saved/Logs/pipeline/package-1.log\nSMOKE_REQUIRE_INPUT=0 tools/ue/smoke.sh: PASS\n"
                 "smoke: exit=0 SMOKE_OK=yes\ncrash folders: 0 new\n"
                 "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input=none load_ms=3000 workbench=0\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=start commit=abc1234 workbench=0 platform=Mac\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=end commit=abc1234 workbench=0 platform=Mac\n"
                 + self.ART_OK +
                 "EDITOR CHECK: by=Rick opened=Content/UmbrellaElla/Maps/L_Graybox.umap ok")
        body = GOOD.replace("PASS  tests=14", smoke + "\nPASS  tests=14")
        ch = ["Content/UmbrellaElla/Maps/L_Graybox.umap"]
        self.assertEqual(check_pr.problems(body, changed=ch, root=self.boot_root(smoke_hook=True)), [])
        # broken on purpose: MVP 2 merged, or the run did not say SMOKE_REQUIRE_INPUT=0
        found = check_pr.problems(body, changed=ch, root=self.boot_root(smoke_hook=True, qa01="merged"))
        self.assertTrue(any("input=none" in p for p in found), found)
        found = check_pr.problems(body.replace("SMOKE_REQUIRE_INPUT=0 ", ""), changed=ch,
                                  root=self.boot_root(smoke_hook=True))
        self.assertTrue(any("input=none" in p for p in found), found)

    def test_gamepad_smoke_required_once_its_card_merged(self):
        """Card 0.6e: the packaged smoke shows a controller moves, attacks and shields. SMOKE_REQUIRE_GAMEPAD=0 is a
        waiver only while the QA-GP row is planned. Broken on purpose: the row merged, or no waiver line."""
        smoke = ("package exit: 0  commit=abc1234  dirty=no  log: Saved/Logs/pipeline/package-1.log\n"
                 "SMOKE_REQUIRE_GAMEPAD=0 tools/ue/smoke.sh: PASS\nsmoke: exit=0 SMOKE_OK=yes\ncrash folders: 0 new\n"
                 + self.ART_OK +
                 "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 "
                 "commit=abc1234 input_vz=-120 input=ok load_ms=3000 workbench=0\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=start commit=abc1234 workbench=0 platform=Mac\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=end commit=abc1234 workbench=0 platform=Mac\n"
                 "EDITOR CHECK: by=Rick opened=Content/UmbrellaElla/Maps/L_Graybox.umap ok")
        body = GOOD.replace("PASS  tests=14", smoke + "\nPASS  tests=14")
        ch = ["Content/UmbrellaElla/Maps/L_Graybox.umap"]
        root = lambda gp: self.boot_root(smoke_hook=True, qa01="merged", qagp=gp)   # noqa: E731
        self.assertEqual(check_pr.problems(body, changed=ch, root=root("planned")), [])
        found = check_pr.problems(body, changed=ch, root=root("merged"))
        self.assertTrue(any("gamepad=<none>" in p for p in found), found)
        found = check_pr.problems(body.replace("SMOKE_REQUIRE_GAMEPAD=0 ", ""), changed=ch, root=root("planned"))
        self.assertTrue(any("gamepad=<none>" in p for p in found), found)
        good = body.replace("input=ok load_ms", "input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms")
        self.assertEqual(check_pr.problems(good.replace("SMOKE_REQUIRE_GAMEPAD=0 ", ""), changed=ch, root=root("merged")), [])

    # Final-6 dry runs: exact tokens on the success path, any failing line fails
    def test_build_line_is_the_scripts_own_line(self):
        """Dry run A H3: the honest build.sh / build.ps1 tail passes; look-alikes and failures do not."""
        ch = ["Source/UmbrellaElla/Private/EllaCharacter.cpp"]
        tail = ("Running UnrealBuildTool: dotnet UnrealBuildTool.dll UmbrellaEllaEditor Mac Development -DisableUnity\n"
                "Total execution time: 312.40 seconds\n$ NONUNITY=1 tools/ue/build.sh\n")
        self.assertEqual(check_pr.problems(GOOD.replace(self.NONUNITY_LINE, tail + self.NONUNITY_LINE), ch), [])
        for bad in ("Running UBT -DisableUnity ... exit: 0\n",                      # typed summary (old shape)
                    "build exit: 0  mode=unity  warnings: 0  log: x\n",             # a unity build
                    "Not run: build exit: 0  mode=nonunity\n",                      # decorated
                    "BUILD EXIT: 0  MODE=NONUNITY\n"):                              # other case
            with self.subTest(bad):
                found = check_pr.problems(GOOD.replace(self.NONUNITY_LINE, bad), ch)
                self.assertTrue(any("mode=nonunity" in p for p in found), found)
        both = GOOD.replace(self.NONUNITY_LINE, self.NONUNITY_LINE + "build exit: 6  mode=nonunity  warnings: 3  log: y\n")
        self.assertTrue(any("failing build line" in p for p in check_pr.problems(both, ch)), "a failing line fails")

    def test_bootstrap_test_line_only_on_card_03(self):
        """Dry run A H4."""
        boot = "PASS  tests=1 failed=0  commit=abc1234 (bootstrap: placeholder tests only, card 0.3)"
        ch = ["Source/UmbrellaElla/Private/EllaCharacter.cpp"]
        body = GOOD.replace("PASS  tests=14 failed=0  commit=abc1234", boot)
        self.assertTrue(any("check_automation_report" in p for p in check_pr.problems(body, ch)))
        card03 = body.replace("Card ID: UE-004", "Card ID: UE-0.3").replace("card=UE-004", "card=UE-0.3")
        self.assertEqual(check_pr.problems(card03, ch), [])
        both = GOOD.replace("PASS  tests=14 failed=0  commit=abc1234", "PASS  tests=14 failed=0  commit=abc1234\nFAIL  tests=14 failed=2")
        self.assertTrue(any("failing test report" in p for p in check_pr.problems(both, ch)))

    def test_linked_card_done_when_decides_package(self):
        """Dry run A H4: dropping the package line from the PR's own copy of Done-when does not drop the need."""
        card = {"title": "x", "body": "### Done when\n- [ ] package + SMOKE_OK on L_Graybox\n"}
        self.assertEqual(check_pr.problems(GOOD), [])
        found = check_pr.problems(GOOD, card=card)
        self.assertTrue(any("linked card's Done-when" in p for p in found), found)

    def test_package_needs_run_packaged(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG).replace("run=packaged", "run=PIE")
        found = check_pr.problems(body, changed=["Config/DefaultGame.ini"])
        self.assertTrue(any("run=packaged" in p for p in found), found)

    def test_failing_or_decorated_package_and_smoke_lines_fail(self):
        """Dry run B H6, A M5: each attack sat next to a passing-looking line and passed."""
        ch = ["Config/DefaultGame.ini"]
        ok = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG)
        self.assertEqual(check_pr.problems(ok, changed=ch), [])
        attacks = {
            "package exit 1": self.PKG.replace("package exit: 0", "package exit: 1") + "\npackage log mentions exit 0 retry",
            "smoke fail + expected": "package exit: 0\nSMOKE_FAIL reason=crash\n" + self.PKG.split("\n")[-1],
            "expected prefix": "package exit: 0\nexpected: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=0",
            "not run prefix": "package exit: 0\nNot run: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=0",
            "no commit": self.PKG.replace(" commit=abc1234", ""),
            "no workbench": self.PKG.replace(" workbench=0", ""),
            "second smoke fails": self.PKG + "\nLogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=12 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=0",
            "typed package": "package step done, exit 0\n" + self.PKG.split("\n")[-1],
        }
        for name, ev in attacks.items():
            with self.subTest(name):
                body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + ev)
                self.assertTrue(check_pr.problems(body, changed=ch), name)

    def test_waivers_fail_closed(self):
        """Dry run B M7, M8: an odd QA-01 Status ends the input waiver; a moved smoke hook ends the bootstrap."""
        smoke = ("package exit: 0  commit=abc1234  dirty=no  log: Saved/Logs/pipeline/package-1.log\nSMOKE_REQUIRE_INPUT=0 tools/ue/smoke.sh: PASS\n"
                 "smoke: exit=0 SMOKE_OK=yes\ncrash folders: 0 new\n"
                 "LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input=none load_ms=3000 workbench=0\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=start commit=abc1234 workbench=0 platform=Mac\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=end commit=abc1234 workbench=0 platform=Mac")
        body = GOOD.replace("PASS  tests=14", smoke + "\nPASS  tests=14")
        ch = ["Content/UmbrellaElla/Maps/L_Graybox.umap"]
        for status in ("merged (#45)", "done", "Merged"):
            with self.subTest(status):
                found = check_pr.problems(body, changed=ch, root=self.boot_root(smoke_hook=True, qa01=status))
                self.assertTrue(any("input=none" in p for p in found), found)
        root = self.boot_root()
        os.makedirs(os.path.join(root, "Source", "UmbrellaElla", "Private", "Boot"))
        with open(os.path.join(root, "Source", "UmbrellaElla", "Private", "Boot", "Hook.cpp"), "w") as f:
            f.write('UE_LOG(LogUmbrellaElla, Display, TEXT("SMOKE_OK map=%s view=1920x1080 aspect=1.778 debugdraw=0"), *Map);\n')
        boot = GOOD.replace("PASS  tests=14", self.BOOT + "\nPASS  tests=14")
        found = check_pr.problems(boot, changed=["Config/DefaultGame.ini"], root=root)
        self.assertTrue(any("SMOKE_BOOTSTRAP" in p for p in found), found)

    def test_evidence_lines_carry_the_pr_head_commit(self):
        """Final-7 B H7, M8: after a push, only the header sha was edited; the build, test and package lines still
        name the old commit. A package of a dirty tree is not evidence either."""
        ch = ["Config/DefaultGame.ini", "Source/UmbrellaElla/Private/EllaCharacter.cpp"]
        ok = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG)
        self.assertEqual(check_pr.problems(ok, changed=ch, head="abc1234ff"), [])
        new_head = ok.replace("commit=abc1234 engine=", "commit=def5678 engine=").replace("SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234",
                                                                                         "SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=def5678")
        cases = {
            "stale build line": ("the nonunity build line is for commit=abc1234", new_head),
            "stale test line": ("the test result line is for commit=abc1234", new_head),
            "stale package line": ("the package line is for commit=abc1234", new_head),
            "build line without commit": ("build line is for commit=<none>", ok.replace("mode=nonunity  commit=abc1234", "mode=nonunity")),
            "test line without commit": ("check_automation_report.py` result line", ok.replace("failed=0  commit=abc1234", "failed=0")),
            "package without commit": ("package exit: 0  commit=<sha>  dirty=no", ok.replace("package exit: 0  commit=abc1234  dirty=no", "package exit: 0")),
            "dirty package": ("dirty=yes", ok.replace("dirty=no", "dirty=yes")),
        }
        for name, (why, body) in cases.items():
            with self.subTest(name):
                found = check_pr.problems(body, changed=ch)
                self.assertTrue(any(why in p for p in found), found)

    def test_smoke_script_output_and_grep_hits_pass(self):
        """Final-7 A H2: the real smoke.ps1 output (ue_run.py smoke-log prints the game's line as is), a Select-String
        hit and a grep -n hit all pass; a look-alike after other text still fails."""
        game = "[2026.11.12-10.00.00:000][  0]LogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=0"
        pkg = "package exit: 0  commit=abc1234  dirty=no  log: x.log\n"
        ch = ["Config/DefaultGame.ini"]
        # final-8 A H1: the run's own verdict (smoke-log summary, crash-check) is pasted with any form of the game line
        pkg += "smoke: exit=0 SMOKE_OK=yes fps=60 worst_ms=20 'Error:'=0\ncrash folders: 0 new\n"
        for name, ev in {"smoke.ps1": "smoke logs: a.log b.log\n" + game + "\nPASS",
                         "Select-String": "C:\\Users\\Joan M\\Saved\\Logs\\pipeline\\smoke-game-1.log:412:" + game,
                         "grep -n": "412:" + game, "grep -n file": "Saved/Logs/pipeline/smoke-game-1.log:412:" + game}.items():
            with self.subTest(name):
                body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + pkg + ev)
                self.assertEqual(check_pr.problems(body, changed=ch), [])
        for name, ev in {"not run": "Not run: see smoke-game-1.log:412:" + game, "expected": "expected: " + game}.items():
            with self.subTest(name):
                body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + pkg + ev)
                self.assertTrue(check_pr.problems(body, changed=ch), name)

    def test_plugin_source_needs_build_and_tests(self):
        # Final-7 B M4: Plugins/<X>/Source/ compiles into the game like Source/
        plug = "Plugins/Workbench/Source/Workbench/Private/Panel.cpp"
        body = GOOD.replace(self.NONUNITY_LINE, "").replace("PASS  tests=14 failed=0  commit=abc1234\n", "x=1\n") \
            .replace("Source/UmbrellaElla/Private/EllaCharacter.cpp", plug)
        found = check_pr.problems(body, changed=[plug])
        self.assertTrue(any("mode=nonunity" in p for p in found), found)
        self.assertEqual(check_pr.problems(GOOD, changed=["Plugins/Workbench/Source/Workbench/Private/Panel.cpp"]), [])

    def test_config_change_without_package_fails(self):
        found = check_pr.problems(GOOD, changed=["Config/DefaultGame.ini"])
        self.assertTrue(any("package evidence" in p for p in found), found)

    def test_each_package_path_needs_package(self):
        for path in ["Content/UmbrellaElla/Maps/L_Main.umap", "Source/UmbrellaElla/UmbrellaElla.Build.cs",
                     "Source/UmbrellaElla.Target.cs", "UmbrellaElla.uproject"]:
            with self.subTest(path=path):
                self.assertTrue(any("package evidence" in p for p in check_pr.problems(GOOD, changed=[path])))

    def test_package_path_named_in_what_changed_fails(self):
        body = GOOD.replace("Source/UmbrellaElla/Private/EllaCharacter.cpp", "Config/DefaultEngine.ini")
        self.assertTrue(any("package evidence" in p for p in check_pr.problems(body)))

    def test_card_done_when_asks_for_package(self):
        body = GOOD.replace("- [x] build passes", "- [x] build passes\n- [ ] package + SMOKE_OK")
        self.assertTrue(any("package evidence" in p for p in check_pr.problems(body)))

    # Findings from the dry runs: a Source/ PR that ran nothing, and a smoke line that breaks the contract
    def test_source_pr_with_engine_none_fails(self):
        body = GOOD.replace("engine=5.8.4 config=Development host=win run=packaged", "engine=none config=none host=win run=none")
        found = check_pr.problems(body, changed=["Source/UmbrellaElla/Private/EllaCharacter.cpp"])
        self.assertTrue(any("engine=none" in p for p in found), found)

    def test_nonunity_not_run_line_fails(self):
        body = GOOD.replace(self.NONUNITY_LINE, "Not run: the -DisableUnity build, exit 0 later\n")
        found = check_pr.problems(body, changed=["Source/UmbrellaElla/Private/EllaCharacter.cpp"])
        self.assertTrue(any("mode=nonunity" in p for p in found), found)

    def test_smoke_line_breaking_the_contract_fails(self):
        body = GOOD.replace("## Not done", self.PKG.replace("fps=60 worst_ms=20", "fps=1 worst_ms=999") + "\n\n## Not done", 1)
        found = check_pr.problems(body, changed=["Config/DefaultGame.ini"])
        self.assertTrue(any("fps=1" in p for p in found) and any("worst_ms=999" in p for p in found), found)

    def test_smoke_map_must_be_a_changed_map(self):
        body = GOOD.replace("## Not done", self.PKG + "\n\n## Not done", 1)
        found = check_pr.problems(body, changed=["Content/UmbrellaElla/Maps/L_Arena.umap"])
        self.assertTrue(any("smoke a changed map" in p for p in found), found)

    def test_package_evidence_present_passes(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG)
        self.assertEqual(check_pr.problems(body, changed=["Config/DefaultGame.ini"]), [])

    def test_smoke_from_the_workbench_tester_package_fails(self):
        # D-new-workbench-debug: PR evidence comes from the submission package (workbench=0).
        ok = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG + " workbench=0")
        self.assertEqual(check_pr.problems(ok, changed=["Config/DefaultGame.ini"]), [])
        bad = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG + " workbench=1")
        found = check_pr.problems(bad, changed=["Config/DefaultGame.ini"])
        self.assertTrue(any("SMOKE_OK workbench=1" in p for p in found), found)

    def test_card_027_may_paste_its_tester_package_smoke(self):
        # Final-7 A M6: card 0.27's Done-when asks for -Workbench proof; that true line no longer fails, but the
        # submission package's workbench=0 line is still required
        tester = "\nLogUmbrellaElla: SMOKE_OK map=L_Graybox view=1920x1080 aspect=1.778 debugdraw=0 fps=60 worst_ms=20 commit=abc1234 input_vz=-120 input=ok gamepad=ok gp_vx=150 gp_attack_vz=-200 gp_shield_vz=-180 load_ms=3000 workbench=1"
        card = {"title": "0.27", "body": "### Done when\nOn a `package.ps1 -Workbench` package it logs WORKBENCH_ON; package + SMOKE_OK\n"}
        win = (self.PKG.replace("target=UmbrellaElla", "target=UmbrellaElla  platform=Win64") + tester
               + "\nLogUmbrellaElla: SMOKE_EFFECTIVE at=start commit=abc1234 workbench=0 platform=Windows\n"
                 "LogUmbrellaElla: SMOKE_EFFECTIVE at=end commit=abc1234 workbench=0 platform=Windows")   # final-9 A H5
        ok = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + win)
        self.assertEqual(check_pr.problems(ok, changed=["Config/DefaultGame.ini"], card=card), [])
        # broken on purpose: no card asking for it, or only the tester line
        self.assertTrue(any("workbench=1" in p for p in check_pr.problems(ok, changed=["Config/DefaultGame.ini"])))
        only = ok.replace("gp_shield_vz=-180 load_ms=3000 workbench=0", "gp_shield_vz=-180 load_ms=3000 workbench=1")
        found = check_pr.problems(only, changed=["Config/DefaultGame.ini"], card=card)
        self.assertTrue(any("no SMOKE_OK line has workbench=0" in p for p in found), found)

    def test_bake_stamp_change_needs_the_bake_check_line(self):
        found = check_pr.problems(GOOD, changed=["pipeline/qa/baked.json"])
        self.assertTrue(any("bake_preset check" in p for p in found), found)
        ok = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\nbake_preset check: PASS preset=T-03 values=12")
        self.assertEqual(check_pr.problems(ok, changed=["pipeline/qa/baked.json"]), [])

    def test_package_without_smoke_ok_fails(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\npackage exit: 0")
        self.assertTrue(check_pr.problems(body, changed=["Config/DefaultGame.ini"]))

    # Red-team round 2, finding 13: "not run" and bare words are not package evidence
    def test_red_team_not_run_pr_fails(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "pr_not_run.md")) as fh:
            body = fh.read()
        found = check_pr.problems(body, changed=["Content/UmbrellaElla/Maps/L_Graybox.umap"])
        self.assertTrue(any("not run" in p for p in found), found)
        self.assertTrue(any("package exit: 0" in p for p in found), found)

    def test_not_run_package_fails_even_with_ok_lines(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG + "\nShipping package: not run")
        self.assertTrue(any("not run" in p for p in check_pr.problems(body, changed=["Config/DefaultGame.ini"])))

    def test_smoke_ok_without_map_fails(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG.replace("map=L_Graybox ", ""))
        self.assertTrue(any("SMOKE_OK map=" in p for p in check_pr.problems(body, changed=["Config/DefaultGame.ini"])))

    def test_package_exit_nonzero_fails(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG.replace("package exit: 0", "package exit: 6"))
        self.assertTrue(any("package exit: 0" in p for p in check_pr.problems(body, changed=["Config/DefaultGame.ini"])))

    def test_smoke_for_another_commit_fails(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\n" + self.PKG.replace("commit=abc1234", "commit=9999999"))
        self.assertTrue(any("SMOKE_OK is for commit" in p for p in check_pr.problems(body, changed=["Config/DefaultGame.ini"])))

    def test_not_run_is_fine_when_no_package_needed(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "tests=14 failed=0  commit=abc1234\npackage: not run (code-only card)")
        self.assertEqual(check_pr.problems(body), [])

    # Finding 5: the link form is open (D-new-port-1); both forms pass, anything else fails
    def test_part_of_and_closes_both_pass(self):
        for link in ("Part of #21.", "Closes #21.", "part of #21.", "Fixes #21."):
            with self.subTest(link=link):
                self.assertEqual(check_pr.problems(GOOD.replace("Closes #21.", link)), [])

    def test_other_link_words_fail(self):
        for link in ("See #21.", "Part of 21.", "Related #21."):
            with self.subTest(link=link):
                self.assertTrue(any("Part of #" in p for p in check_pr.problems(GOOD.replace("Closes #21.", link))))

    def test_template_shows_both_forms_with_default_marked(self):
        with open(os.path.join(ROOT, ".github", "PULL_REQUEST_TEMPLATE.md")) as fh:
            t = fh.read()
        self.assertIn("Part of #<issue>", t)
        self.assertIn("Closes #<issue>", t)
        self.assertRegex(t, r"Default: \"Part of #<issue>\"")
        self.assertIn("D-new-port-1", t)

    def test_ci_card_lookup_accepts_both_forms(self):
        import re
        with open(os.path.join(ROOT, ".github", "workflows", "pipeline-checks.yml")) as fh:
            wf = fh.read()
        pat = re.search(r"re\.search\(r'(.+?)', b\)", wf).group(1)
        for body, want in (("Part of #7.", "7"), ("Closes #8", "8"), ("See #9", None)):
            m = re.search(pat, body)
            self.assertEqual(m.group(1) if m else None, want, body)

    def test_code_only_change_needs_no_package(self):
        self.assertEqual(check_pr.problems(GOOD, changed=["Source/UmbrellaElla/Private/Umbrella/UmbrellaComponent.cpp"]), [])

    # Non-unity build log on every PR that touches Source/ (D-new-nonunity-pr default)
    NONUNITY_LINE = "build exit: 0  mode=nonunity  commit=abc1234  warnings: 0  log: Saved/Logs/pipeline/build-1.log\n"

    def test_source_cpp_change_without_nonunity_log_fails(self):
        body = GOOD.replace(self.NONUNITY_LINE, "")
        found = check_pr.problems(body, changed=["Source/UmbrellaElla/Private/Umbrella/UmbrellaComponent.cpp"])
        self.assertTrue(any("mode=nonunity" in p for p in found), found)

    def test_source_cpp_change_with_nonunity_log_passes(self):
        self.assertIn(self.NONUNITY_LINE, GOOD)
        self.assertEqual(check_pr.problems(GOOD, changed=["Source/UmbrellaElla/Private/Umbrella/UmbrellaComponent.cpp"]), [])

    def test_docs_only_change_needs_no_nonunity_log(self):
        body = GOOD.replace(self.NONUNITY_LINE, "").replace("Source/UmbrellaElla/Private/EllaCharacter.cpp", "docs/balance.md")
        self.assertEqual(check_pr.problems(body, changed=["docs/balance.md"]), [])

    # Dry runs: a claim is not evidence; a Source/ PR pastes the test report line
    def test_vague_evidence_fails(self):
        body = GOOD.replace("tests=14 failed=0  commit=abc1234", "").split("## Evidence")[0] + (
            "## Evidence\ncommit=abc1234 engine=none config=none host=mac run=none\nTests: all good, trust me.\n"
            "## Not done / risks\nnone\nCould not read: none\nNext: none\n## Binary assets touched\nnone\n")
        body = body.replace("Source/UmbrellaElla/Private/EllaCharacter.cpp", "docs/balance.md")
        found = check_pr.problems(body, changed=["docs/balance.md"])
        self.assertTrue(any("no re-runnable line" in p for p in found), found)

    def test_not_run_with_reason_is_evidence(self):
        body = GOOD.split("## Evidence")[0] + (
            "## Evidence\ncommit=abc1234 engine=none config=none host=mac run=none\nNot run: build, docs-only card\n"
            "## Not done / risks\nnone\nCould not read: none\nNext: none\n## Binary assets touched\nnone\n") + JOURNAL
        body = body.replace("Source/UmbrellaElla/Private/EllaCharacter.cpp", "docs/balance.md")
        self.assertEqual(check_pr.problems(body, changed=["docs/balance.md"]), [])

    def test_source_pr_without_test_report_fails(self):
        body = GOOD.replace("PASS  tests=14 failed=0  commit=abc1234\n", "tests: all passed\n")
        found = check_pr.problems(body, changed=["Source/UmbrellaElla/Private/EllaCharacter.cpp"])
        self.assertTrue(any("check_automation_report.py" in p for p in found), found)

    def test_source_pr_with_failed_tests_fails(self):
        body = GOOD.replace("PASS  tests=14 failed=0  commit=abc1234", "FAIL  tests=14 failed=2")
        found = check_pr.problems(body, changed=["Source/UmbrellaElla/Private/EllaCharacter.cpp"])
        self.assertTrue(any("check_automation_report.py" in p for p in found), found)

    def test_template_placeholder_is_not_a_nonunity_log(self):
        body = GOOD.replace(self.NONUNITY_LINE, "<paste the -DisableUnity line here>\n")
        self.assertTrue(any("mode=nonunity" in p for p in check_pr.problems(body)))

    # Not done lines and Next:
    def test_not_done_line_without_link_fails(self):
        body = GOOD.replace("none\nCould not read:", "Mac build not checked\nCould not read:")
        self.assertTrue(any("no link" in p for p in check_pr.problems(body)))

    def test_not_done_lines_with_links_pass(self):
        body = GOOD.replace("none\nCould not read:", "- Mac build not checked, #31\n- tuning default D-new-port-4\n"
                            "- see https://github.com/x/y/issues/2\nCould not read:")
        self.assertEqual(check_pr.problems(body), [])

    def test_could_not_read_line_required(self):
        # Ported rule: an agent says which inputs it could not open instead of implying it read them.
        self.assertEqual(check_pr.problems(GOOD), [])
        for broken in (GOOD.replace("Could not read: none\n", ""), GOOD.replace("Could not read: none", "Could not read: <paths>")):
            with self.subTest(body=broken[-300:]):
                self.assertTrue(any("Could not read" in p for p in check_pr.problems(broken)))
        listed = GOOD.replace("Could not read: none", "Could not read: docs/gdd/questions-B1.0.md (LFS pointer)")
        self.assertEqual(check_pr.problems(listed), [])

    def test_missing_next_fails(self):
        body = GOOD.replace("Next: Dev Lead reviews\n", "")
        self.assertTrue(any("Next:" in p for p in check_pr.problems(body)))

    def test_empty_next_fails(self):
        body = GOOD.replace("Next: Dev Lead reviews", "Next: <next role>")
        self.assertTrue(any("Next:" in p for p in check_pr.problems(body)))

    def test_cli_reads_changed_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            bp, cp = os.path.join(d, "b.md"), os.path.join(d, "c.txt")
            open(bp, "w").write(GOOD)
            open(cp, "w").write("Config/DefaultGame.ini\n")
            import io
            from contextlib import redirect_stdout
            with redirect_stdout(io.StringIO()):
                self.assertEqual(check_pr.main([bp, "--changed", cp]), 1)
                self.assertEqual(check_pr.main([bp]), 0)


if __name__ == "__main__":
    unittest.main()

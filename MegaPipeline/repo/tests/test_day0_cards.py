"""pipeline/day0-cards.md and tools/check_card.py must agree (red-team round 2, findings 11, 12, 36).

Every row of the Day-0 table is filed as an issue-form card, the way the Producer would file it, and
must pass check_card with 0 problems. The red-team's draft cards (tests/fixtures/cards/day0_drafts/,
written from the old Day-0 table) are the cards broken on purpose: each must fail for its known reason."""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import check_card  # noqa: E402
from kickoff import RUNS_ON_MAC, RUNS_ON_WINDOWS, until_plan  # noqa: E402


def kickoff_runs_on_windows(text):
    return bool(RUNS_ON_WINDOWS.search(text))

DRAFTS = os.path.join(HERE, "fixtures", "cards", "day0_drafts")

FORM = """### MVP item (number from docs/jam-brief.md), Day 0, or Stretch: <name>

Day 0

### GDD ref (section + short quote; "none" for tooling cards)

none

### GDD revision (the one in docs/gdd/CURRENT, e.g. B1.0)

1.3

### Features (IDs from docs/feature-manifest.json; "none" for tooling cards)

none

### Player outcome (the player sees X, does Y, can tell why; "none" for tooling cards)

none

### Owner role

{owner}

### Reviewer role (must differ from owner)

{reviewer}

### Human who runs and merges this

{human}

### Inputs and outputs (exact paths)

{lane}

### Context (what the code or asset next to Outputs does today, with file:line)

new files only

### File lane, do-not-touch paths, binary files to lock

Lane: {lane}
Do not touch: {dnt}
Locks: {locks}

### Out of scope (behaviors not to build; the reviewer rejects them)

none

### Used by (BPs, maps, widgets or components that read what this card changes; follow-up card IDs)

{after}

### Needs (build | tests | editor MCP | Windows packaging machine)

build, tests

### Done when (each line checkable)

{done}

### Budget and cut tier

60 min agent + 15 min human, MVP

### Unknowns (Decision needed / Why it matters / Proposed test / Choice; "none" if none)

none
"""


def day0_rows():
    with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as f:
        text = f.read()
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and re.fullmatch(r"0\.\d+[a-z]?", cells[0]):
            rows.append(cells)
    return rows


def file_card(row):
    num, title, owner_human, reviewer, lane, after, done = row
    owner, _, human = (p.strip() for p in owner_human.partition("/"))
    human = re.sub(r"\s*\(sign-off:[^)]*\)", "", human)   # the Producer files the person's name only
    is_map = ".umap" in lane
    body = FORM.format(
        owner=owner, reviewer=reviewer, human=human or "Rick", lane=lane,
        after=re.sub(r"\b0\.\d+[a-z]?\b", lambda m: "UE-" + m.group(0), after) if after != "–" else "none",
        dnt="other maps under Content/UmbrellaElla/Maps/" if is_map else "Content/UmbrellaElla/Maps/**",
        locks=(re.search(r"Content/\S+?\.umap", lane).group(0) if is_map else "none"),
        done="\n".join("- [ ] " + d.strip() for d in done.split("<br>")))
    return body, f"[UE-{num}] {title}"


class Day0CardsPassTheChecker(unittest.TestCase):
    def test_table_has_every_card(self):
        nums = [r[0] for r in day0_rows()]
        for n in ("0.0", "0.1", "0.3", "0.4a", "0.4b", "0.5", "0.6", "0.8", "0.10", "0.11", "0.12"):
            self.assertIn(n, nums)

    def test_each_day0_row_filed_as_a_card_has_zero_problems(self):
        for row in day0_rows():
            body, title = file_card(row)
            with self.subTest(card=row[0]):
                self.assertEqual(check_card.problems(body, ROOT, title), [], title)

    def test_after_column_names_only_earlier_cards(self):
        nums = [r[0] for r in day0_rows()]
        for row in day0_rows():
            for dep in re.findall(r"0\.\d+[a-z]?", row[5]):
                with self.subTest(card=row[0], after=dep):
                    self.assertIn(dep, nums)
                    self.assertNotEqual(dep, row[0])

    def test_smoke_card_waits_for_the_map(self):
        rows = {r[0]: r for r in day0_rows()}
        self.assertIn("0.8", rows["0.6"][5])       # finding 9
        self.assertIn("0.12", rows["0.10"][5])     # finding 19: eval camera switch first
        self.assertIn("D3", rows["0.11"][6])       # finding 22: the spike rows (GDD SH1.0 answers the old attack-form DEC-02)

    def test_breaking_a_filed_day0_card_is_caught(self):
        row = [r for r in day0_rows() if r[0] == "0.8"][0]
        body, title = file_card(row)
        for old, new, kind in [
            (re.search(r"^Lane: .*$", body, re.M).group(0), "Lane: none", "lane"),
            (re.search(r"L_Graybox is one screen.*$", body, re.M).group(0), "that works", "done"),
            ("Dev Lead", "Integrator", "owner"),
        ]:
            with self.subTest(break_=kind):
                self.assertIn(old, body)
                broken = body.replace(old, new, 1)
                if kind == "done":
                    broken = broken.replace("prints 1 or more (pasted)", "is fine").replace(
                        "`+MapsToCook=(FilePath=\"/Game/UmbrellaElla/Maps/L_Graybox\")` is in `Config/DefaultGame.ini`", "MapsToCook updated")
                self.assertIn(kind, {k for k, _ in check_card.problems(broken, ROOT, title)})


class AgentsOwnEveryCard(unittest.TestCase):
    """Josh's call: agents own all build work; a person acts only at a true checkpoint (pipeline/human-checkpoints.md
    "Checkpoint kinds"). Each check has a row broken on purpose."""

    def setUp(self):
        with open(os.path.join(ROOT, "pipeline", "day0-cards.md"), encoding="utf-8") as f:
            self.text = f.read()
        self.roles = check_card.roles(ROOT)

    def probs(self, text):
        return check_card.day0_owner_problems(text, self.roles)

    def row(self, cid):
        return re.search(rf"^\| {re.escape(cid)} \|.*$", self.text, re.M).group(0)

    def test_repo_table_has_no_person_owned_card(self):
        self.assertEqual(self.probs(self.text), [])
        for r in day0_rows():
            with self.subTest(card=r[0]):
                self.assertIn(r[2].partition("/")[0].strip(), self.roles)

    def test_person_as_owner_fails(self):
        r = self.row("0.25")
        broken = self.text.replace(r, r.replace("| Technical Director |", "| Human / TD human |", 1))
        self.assertTrue(any("0.25: owner 'Human'" in p for p in self.probs(broken)), self.probs(broken))

    def test_person_doing_build_work_without_a_checkpoint_fails(self):
        r = self.row("0.4d")
        broken = self.text.replace(r, r.replace("The agent writes `tools/ue/art_dump.py`",
                                                "The TD human writes `tools/ue/art_dump.py`", 1))
        self.assertTrue(any(p.startswith("0.4d: a person acts") for p in self.probs(broken)), self.probs(broken))

    def test_untagged_checkpoint_kind_and_unknown_kind_fail(self):
        r = self.row("0.4b")
        broken = self.text.replace(r, r.replace("(sign-off: submission)", "(sign-off: submission, art direction)", 1))
        self.assertTrue(any("'art direction' is not a checkpoint kind" in p for p in self.probs(broken)))
        broken = self.text.replace(r, r.replace("HUMAN submission:", "HUMAN taste:", 1))
        self.assertTrue(any("'HUMAN taste:' is not a checkpoint kind" in p for p in self.probs(broken)))

    def test_old_person_steps_are_no_longer_checkpoints(self):
        """Gate patches, machine sessions, people rows and design calls are the tools' and agents' now; broken on
        purpose: putting one back as a HUMAN line fails."""
        r = self.row("0.7")
        for kind, line in (("guardrails", "the TD human applies it with `python3 tools/git_gate.py apply UE-0.7`"),
                           ("physical", "the packaging machine owner starts the card's session"),
                           ("people", "each teammate confirms their own People row"),
                           ("design", "the game design owner marks D34 DECIDED")):
            broken = self.text.replace(r, r.replace("| Art Director / TD human |", f"| Art Director / TD human "
                                                    f"(sign-off: {kind}) |", 1).replace(
                "<br>`python3 tools/art_check.py --references`", f"<br>HUMAN {kind}: {line}<br>"
                "`python3 tools/art_check.py --references`", 1))
            self.assertNotEqual(broken, self.text)
            self.assertTrue(any(f"'HUMAN {kind}:' is not a checkpoint kind" in p for p in self.probs(broken)),
                            self.probs(broken))

    def test_only_the_itch_upload_and_api_keys_are_human(self):
        for r in day0_rows():
            with self.subTest(card=r[0]):
                kinds = re.findall(r"(?:^|<br>)HUMAN ([a-z]+):", r[6])
                self.assertTrue(set(kinds) <= {"submission", "secrets"}, kinds)
                for seg in r[6].split("<br>"):
                    if seg.startswith("HUMAN submission:"):
                        self.assertIn("itch", seg)
                self.assertNotIn("Human only", r[3])
                self.assertNotIn("TD human applies", r[6])

    def test_human_only_reviewer_fails(self):
        r = self.row("0.11")
        broken = self.text.replace(r, r.replace("| Producer | Technical Director |", "| Producer | Human only |", 1))
        self.assertTrue(any(p.startswith("0.11: reviewer 'Human only' is a person") for p in self.probs(broken)),
                        self.probs(broken))

    def test_check_card_rejects_a_person_as_owner(self):
        body, title = file_card([c for c in day0_rows() if c[0] == "0.25"][0])
        self.assertEqual(check_card.problems(body, ROOT, title), [])
        broken = body.replace("### Owner role\n\nTechnical Director\n", "### Owner role\n\nHuman\n", 1)
        self.assertNotEqual(broken, body)
        self.assertIn("owner", {k for k, _ in check_card.problems(broken, ROOT, title)})

    def test_kinds_match_the_checkpoint_doc(self):
        with open(os.path.join(ROOT, "pipeline", "human-checkpoints.md"), encoding="utf-8") as f:
            doc = f.read()
        sec = doc.split("## Checkpoint kinds", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(tuple(re.findall(r"^\| `([a-z]+)` \|", sec, re.M)), check_card.CHECKPOINT_KINDS)
        self.assertNotIn("art", " ".join(check_card.CHECKPOINT_KINDS), "art direction is the automated art gate")

    def test_prejam_cards_are_the_workbench_and_setup_cards(self):
        pre = check_card.prejam_cards(ROOT)
        self.assertTrue({"0.25", "0.26", "0.0", "0.1", "0.2"} <= pre, pre)
        self.assertFalse(pre & {"0.3", "0.8", "0.27"}, "cards that make game files wait for the jam start (D39)")
        rows = {r[0]: r for r in day0_rows()}
        for cid in ("0.25", "0.26"):
            self.assertEqual(rows[cid][2], "Technical Director", "the workbench sample is agent-owned, no sign-off")
            self.assertNotIn("Source/", rows[cid][4])

    def test_workbench_debug_toggles_in_acceptance(self):
        rows = {r[0]: r for r in day0_rows()}
        for need in ("AllOffByDefault", "dbg.no_ground_death", "dbg.hover", "dbg.health_bars", "UMBRELLAELLA_WORKBENCH"):
            self.assertIn(need, rows["0.25"][6])
        self.assertIn("EveryTunableHasRange", rows["0.26"][6])
        for need in ("DebugTogglesOffByDefault", "package.ps1 -Workbench", "dbg.hover", "never has them",
                     "dbg.move_model", "1 or 2 at different heights", "rise and fall speed", "DevSettingsDefaultToGdd",
                     "separate from the player's settings menu"):
            self.assertIn(need, rows["0.27"][6])

    def test_gamepad_smoke_card_is_agent_owned_and_runs_on_the_mac(self):
        rows = {r[0]: r for r in day0_rows()}
        r = rows["0.6e"]
        self.assertEqual(r[2].partition("/")[0].strip(), "Gameplay Dev")
        self.assertIn("gamepad=ok", r[6])
        self.assertNotIn("HUMAN physical", r[6])
        self.assertFalse(kickoff_runs_on_windows(r[6]), "the G1 gamepad smoke runs on the Mac")
        self.assertTrue(RUNS_ON_MAC.search(r[6]))
        self.assertIn("tools/ue/smoke.sh", r[6])
        self.assertTrue(kickoff_runs_on_windows(rows["0.6w"][6]), "the Win64 gamepad smoke is the Windows card's")
        self.assertIn("gamepad=ok", rows["0.6w"][6])


class G1RunsOnTheMac(unittest.TestCase):
    """GDD SH1.0 G1 (D-new-sh10-g1) on one Mac: every card on the G1 path builds and is verified on the Mac, every
    Windows-only line is on a separate Windows card that nothing on the path waits for, and no step on the path has a
    person act (kickoff --until G1, tools/kickoff.py until_plan)."""

    def rows(self):
        return {r[0]: r for r in day0_rows()}

    def path(self, rows):
        out, todo = set(), check_card.gate_cards(ROOT, "G1")
        while todo:
            k = todo.pop()
            if k not in out and k in rows:
                out.add(k)
                todo += re.findall(r"0\.\d+[a-z]?", rows[k][5])
        return out

    def test_g1_path_has_no_person_and_no_windows_step(self):
        lines, probs = until_plan("G1")
        self.assertEqual(probs, [], "\n".join(lines))
        rows = self.rows()
        path = self.path(rows)
        self.assertTrue({"0.0", "0.3", "0.5", "0.6", "0.8", "0.4e", "0.6e"} <= path, path)
        for k in path:
            done = rows[k][6]
            with self.subTest(card=k):
                self.assertFalse(kickoff_runs_on_windows(done))
                self.assertNotRegex(done, r"\.ps1\b|\$env:")
                self.assertNotRegex(done, r"(^|<br>)\s*HUMAN [a-z]+:")
        self.assertFalse(path & {"0.3w", "0.6w", "0.4b", "0.6d"}, "the Windows cards never hold up G1")

    def test_skeleton_mac_lines_on_03_windows_lines_on_03w(self):
        rows = self.rows()
        d03, dw = rows["0.3"][6], rows["0.3w"][6]
        for need in ("tools/ue/build.sh", "tools/ue/test.sh --bootstrap", "tools/ue/package.sh", "platform=Mac",
                     "SMOKE_MODE=alive", "SMOKE_BOOTSTRAP"):
            self.assertIn(need, d03)
        self.assertTrue(RUNS_ON_MAC.search(d03))
        for need in ("build.ps1", "test.ps1", "package.ps1", "platform=Win64"):
            self.assertIn(need, dw)
        self.assertTrue(kickoff_runs_on_windows(dw))
        self.assertEqual(re.findall(r"0\.\d+[a-z]?", rows["0.3w"][5]), ["0.3"])
        for k in ("0.6", "0.6e"):
            self.assertTrue(RUNS_ON_MAC.search(rows[k][6]), k)
        self.assertIn("tools/ue/daily.sh", rows["0.6"][6])
        self.assertIn("daily.ps1", rows["0.6w"][6])

    def test_broken_on_purpose_a_windows_line_back_on_03_fails_the_plan(self):
        path = os.path.join(ROOT, "pipeline", "day0-cards.md")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        import shutil
        import tempfile
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "pipeline"))
        os.makedirs(os.path.join(d, "docs"))
        shutil.copy(os.path.join(ROOT, "docs", "jam-brief.md"), os.path.join(d, "docs", "jam-brief.md"))
        row = next(ln for ln in text.splitlines() if ln.startswith("| 0.3 |"))
        for bad, want in ((row.replace("`tools/ue/build.sh` exits 0 on the Mac", "`tools\\ue\\build.ps1` exits 0"),
                           "a Windows step"),
                          (row.replace("Runs on: the Mac build machine", "Runs on: the Windows packaging machine"),
                           "runs on the Windows packaging machine"),
                          (row[:-2] + "<br>HUMAN design: the game design owner signs it |", "a person acts")):
            self.assertNotEqual(bad, row)
            with open(os.path.join(d, "pipeline", "day0-cards.md"), "w", encoding="utf-8") as fh:
                fh.write(text.replace(row, bad))
            _, probs = until_plan("G1", root=d)
            self.assertTrue(any(want in p for p in probs), (want, probs))


# draft card -> problem kinds it must show (written from the old Day-0 table and form)
DRAFT_EXPECT = {
    "c01": {"field", "owner", "done"},   # GDD ref n/a, reviewer "–", Done-when without a value
    "c08": {"field", "done"},            # "Loads in a packaged build" is not measured
    "c09": {"field", "lane", "done"},    # "a throwaway branch" is not a path
    "cvague": {"field", "done"},         # "works and exits 0 eventually" (finding 36)
    "d03": {"done"}, "d04": {"done"}, "d11": {"done"},
    "g": {"field", "done"},              # GDD ref "-"
    "l": {"field", "lane", "done"},      # Lane: none (finding 11)
    "l2": {"field", "lane", "done"},     # Lane: everything (finding 11)
}


class RedTeamDraftsAreRejected(unittest.TestCase):
    def test_each_draft_fails_for_its_reason(self):
        for name, want in DRAFT_EXPECT.items():
            with open(os.path.join(DRAFTS, name + ".md"), encoding="utf-8") as f:
                body = f.read()
            with self.subTest(draft=name):
                got = {k for k, _ in check_card.problems(body, ROOT, "[UE-1] draft")}
                self.assertTrue(want <= got, f"{name}: want {want}, got {got}")

    def test_lane_none_and_everything_rejected_even_with_do_not_touch_paths(self):
        with open(os.path.join(DRAFTS, "l.md"), encoding="utf-8") as f:
            body = f.read().replace("n/a", "none").replace("The level works and exits 0 eventually",
                                                           "`tools/ue/smoke.sh` prints PASS")
        self.assertEqual({k for k, _ in check_card.problems(body, ROOT, "[UE-1] x")}, {"lane"})
        for word in ("everything", "all", "nothing", "whole repo"):
            with self.subTest(lane=word):
                b = body.replace("Lane: none", "Lane: " + word)
                self.assertEqual({k for k, _ in check_card.problems(b, ROOT, "[UE-1] x")}, {"lane"})
        good = body.replace("Lane: none", "Lane: Content/UmbrellaElla/Maps/L_X.umap")
        self.assertEqual(check_card.problems(good, ROOT, "[UE-1] x"), [])

    def test_missing_lane_line_is_a_missing_field(self):
        with open(os.path.join(DRAFTS, "l.md"), encoding="utf-8") as f:
            body = f.read().replace("Lane: none\n", "")
        self.assertIn(("field", "missing field 'File lane'"), check_card.problems(body, ROOT, "[UE-1] x"))

    def test_github_only_lane_allowed(self):
        with open(os.path.join(DRAFTS, "c01b.md"), encoding="utf-8") as f:
            body = f.read().replace("n/a", "none").replace(
                'One pinned issue "Jam tracker" exists. Daily status and build records are posted there',
                '`gh issue list --label tracker` lists 1 pinned issue "Jam tracker"')
        self.assertEqual(check_card.problems(body, ROOT, "[UE-0.1] Jam tracker"), [])


class DoneWhenStrictness(unittest.TestCase):
    """Finding 36: a command result counts only next to the command; hedges always fail."""

    def kinds(self, line):
        with open(os.path.join(HERE, "fixtures", "cards", "good_form.md"), encoding="utf-8") as f:
            body = f.read()
        body = re.sub(r"(### Done when[^\n]*\n\n)(?:- \[ \][^\n]*\n)+", lambda m: m.group(1) + "- [ ] " + line + "\n", body)
        # a Day 0 (tooling) card: these lines test the measurable rule, not the MVP card's engine-test rule (A M9)
        body = body.replace("Stretch: <name>\n\n9\n", "Stretch: <name>\n\nDay 0\n", 1)
        body = body.replace("(IDs from docs/feature-manifest.json)\n\nHAZ-19\n", "(IDs from docs/feature-manifest.json)\n\nnone\n", 1)
        signed = os.path.join(HERE, "fixtures", "manifest", "signed_off.json")   # good_form builds HAZ-19 (P0)
        return {k for k, _ in check_card.problems(body, ROOT, "[UE-31] x", signed)}

    def test_bare_exits_0_is_not_measurable(self):
        self.assertEqual(self.kinds("the map loads and exits 0"), {"done"})

    def test_exits_0_with_command_passes(self):
        self.assertEqual(self.kinds("`tools/ue/smoke.sh` exits 0 on the Development package"), set())

    def test_hedge_fails_even_with_numbers(self):
        self.assertEqual(self.kinds("Z velocity > 0 within 0.5 s, eventually"), {"done"})

    def test_marked_decided_counts(self):
        self.assertEqual(self.kinds("D14 marked DECIDED"), set())

    def test_mvp_feature_card_needs_its_engine_test(self):
        """Dry run A M9: a numeric MVP card whose only Done-when is a build line is not ready."""
        with open(os.path.join(HERE, "fixtures", "cards", "good_form.md"), encoding="utf-8") as f:
            body = f.read()
        signed = os.path.join(HERE, "fixtures", "manifest", "signed_off.json")
        self.assertEqual(check_card.problems(body, ROOT, "[UE-31] x", signed), [])
        bad = re.sub(r"(### Done when[^\n]*\n\n)(?:- \[ \][^\n]*\n)+",
                     lambda m: m.group(1) + "- [ ] `tools/ue/build.sh` exits 0\n", body)
        self.assertIn("done", {k for k, _ in check_card.problems(bad, ROOT, "[UE-31] x", signed)})



class Final7Alignment(unittest.TestCase):
    """Final-7 dry run A H1, H3: the cards, the role cards and the gate checks ask for the same things."""

    def rows(self):
        return {r[0]: r for r in day0_rows()}

    def test_card_03_holds_the_td_done_whens_inside_its_lane(self, rows=None):
        rows = rows or self.rows()
        lane03, done03 = rows["0.3"][4], rows["0.3"][6]
        for need in ("--rules K", "index.json", "`final` UCLASS", "NONUNITY=1"):
            self.assertIn(need, done03)
        self.assertNotIn("pipeline/unreal/", lane03)
        self.assertIn("pipeline/unreal/", rows["0.4a"][4])
        self.assertIn("cpp-rules.md", rows["0.4a"][6])
        with open(os.path.join(ROOT, "pipeline", "roles", "technical-director.md"), encoding="utf-8") as f:
            td = f.read()
        self.assertNotRegex(td, r"a compile log of one is pasted into `pipeline/unreal/cpp-rules.md`")

    def test_card_03_check_catches_a_td_item_left_out(self):
        rows = self.rows()
        broken = dict(rows)
        broken["0.3"] = rows["0.3"][:6] + [rows["0.3"][6].replace("--rules K", "")]   # broken on purpose
        with self.assertRaises(AssertionError):
            self.test_card_03_holds_the_td_done_whens_inside_its_lane(broken)

    def test_g1_scope_matches_gdd_first_playable(self):
        import ue_run
        # GDD 1.3 section 12A: Nov 12 first playable has health/death, timer, restart; player screens are Nov 13.
        # quit-play is due at G1 too: the G1 build goes to testers, and the first test build had no way out but Alt+F4
        self.assertEqual(ue_run.PLAYTHROUGH_DUE["G1"], ["survived", "fail-retry", "fail-bottom", "quit-play"])
        self.assertIn("quit-title", ue_run.PLAYTHROUGH_DUE["G2"])
        with open(os.path.join(ROOT, "pipeline", "roles", "qa-build.md"), encoding="utf-8") as f:
            qa = f.read()
        self.assertIn("both quits join at G2", qa)
        self.assertIn("Due on by G2", qa)
        with open(os.path.join(ROOT, "pipeline", "roles", "producer.md"), encoding="utf-8") as f:
            prod = f.read()
        self.assertRegex(prod, r"\| G1 \|[^\n]*0\.4b[^\n]*0\.6c")
        self.assertRegex(prod, r"\| G2 \|[^\n]*0\.20, 0\.21, 0\.21b, 0\.22")

if __name__ == "__main__":
    unittest.main()

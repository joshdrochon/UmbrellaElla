"""tools/submission_check.py: each rule breaks on purpose and fails, and a good input passes.
Fixture zips and PNGs are built in a temp folder (zip and png must be in Git LFS, so none are committed)."""
import contextlib
import io
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import submission_check as sc  # noqa: E402

GOOD_INFO = "commit=abc1234def\ndate=2026-11-15T18:00:00Z\nconfig=Development\ndirty=no\nworkbench=0\n"
README = "The Last Hour\nControls: A/D move, Space hold opens the umbrella, Esc pause.\n"


def good_files(info=GOOD_INFO):
    return {
        "Windows/TheLastHour.exe": b"MZ",
        "Windows/README.txt": README.encode(),
        "Windows/LICENSE.txt": b"Licence text",
        "Windows/BUILD_INFO.txt": info.encode(),
        "Windows/TheLastHour/Binaries/Win64/TheLastHour.exe": b"MZ",
        "Windows/TheLastHour/Content/Paks/TheLastHour-Windows.pak": b"pak",
        "Windows/Engine/Binaries/Win64/CrashReportClient.exe": b"MZ",
    }


def png(path, w, h, seed=0):
    raw = b"".join(b"\x00" + bytes([seed % 256, 0, 0]) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 1)) + chunk(b"IEND", b""))


class Tmp(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)


class ZipTests(Tmp):
    def make(self, files, name="Inkwell_TheLastHour.zip"):
        p = os.path.join(self.dir, name)
        with zipfile.ZipFile(p, "w") as z:
            for k, v in files.items():
                z.writestr(k, v)
        return p

    def test_workbench_must_be_compiled_out(self):
        # D-new-workbench-debug: the submission package is the workbench=0 target; a tester package fails.
        self.assertEqual(sc.zip_problems(self.make(good_files())), [])
        for info in (GOOD_INFO.replace("workbench=0", "workbench=1"), GOOD_INFO.replace("workbench=0\n", "")):
            with self.subTest(info=info):
                got = sc.zip_problems(self.make(good_files(info)))
                self.assertTrue(any("workbench" in p for p in got), got)

    def test_gate_zip_folder(self):
        os.makedirs(os.path.join(self.dir, "G1-abc1234"))
        good = self.make(good_files(), "G1-abc1234/Inkwell_TheLastHour.zip")
        self.assertEqual(sc.zip_problems(good, "Inkwell", "TheLastHour", gate="G1"), [])
        self.assertTrue(any("need G2-<sha>" in p for p in sc.zip_problems(good, gate="G2")))
        os.makedirs(os.path.join(self.dir, "G1-fff9999"))
        other = self.make(good_files(), "G1-fff9999/Inkwell_TheLastHour.zip")
        self.assertTrue(any("BUILD_INFO commit" in p for p in sc.zip_problems(other, gate="G1")))
        old = self.make(good_files(), "UmbrellaElla-G1-abc1234.zip")
        self.assertTrue(any("folder" in p for p in sc.zip_problems(old, gate="G1")))
        self.assertTrue(any("name" in p for p in sc.zip_problems(old, gate="G1")))

    def test_good_zip_passes(self):
        self.assertEqual(sc.zip_problems(self.make(good_files()), "Inkwell", "TheLastHour", "abc1234"), [])

    def assertFails(self, files, needle, name="Inkwell_TheLastHour.zip", **kw):
        probs = sc.zip_problems(self.make(files, name), **kw)
        self.assertTrue(any(needle in p for p in probs), probs)

    def test_shipping_config_fails(self):
        self.assertFails(good_files(GOOD_INFO.replace("Development", "Shipping")), "config=Shipping")

    def test_wrong_platform_fails(self):
        self.assertFails(good_files(GOOD_INFO + "platform=Mac\n"), "platform=Mac")

    def test_no_win64_binaries_fails(self):
        f = good_files()
        f.pop("Windows/TheLastHour/Binaries/Win64/TheLastHour.exe")
        self.assertFails(f, "not a Win64 package")

    def test_dirty_build_fails(self):
        self.assertFails(good_files(GOOD_INFO.replace("dirty=no", "dirty=yes")), "dirty=yes")

    def test_commit_mismatch_fails(self):
        self.assertFails(good_files(), "is not 9999999", commit="9999999")

    def test_uproject_fails(self):
        f = good_files()
        f["Windows/TheLastHour.uproject"] = b"{}"
        self.assertFails(f, ".uproject")

    def test_source_fails(self):
        f = good_files()
        f["Windows/Source/TheLastHour/Ella.cpp"] = b"int x;"
        self.assertFails(f, "source code")

    def test_loose_uasset_fails(self):
        f = good_files()
        f["Windows/TheLastHour/Content/Maps/L_Arena.umap"] = b"x"
        self.assertFails(f, "outside Paks")

    def test_saved_folder_fails(self):
        f = good_files()
        f["Windows/TheLastHour/Saved/Logs/TheLastHour.log"] = b"log"
        self.assertFails(f, "Saved/")

    def test_size_limit_fails(self):
        self.assertFails(good_files(), "over 10", max_bytes=10)

    def test_bad_name_fails(self):
        self.assertFails(good_files(), "not TeamName_GameName", name="UmbrellaElla-G3-abc.zip")
        self.assertFails(good_files(), "is not Inkwell_TheLastHour", name="Other_TheLastHour.zip", team="Inkwell")

    def test_missing_readme_and_licence_fail(self):
        for need in ("README.txt", "LICENSE.txt", "BUILD_INFO.txt"):
            f = good_files()
            f.pop("Windows/" + need)
            self.assertFails(f, need + " missing")

    def test_readme_without_controls_fails(self):
        f = good_files()
        f["Windows/README.txt"] = b"Hello"
        self.assertFails(f, "no Controls")

    def test_two_game_exes_fail(self):
        f = good_files()
        f["Windows/Other.exe"] = b"MZ"
        self.assertFails(f, "expected 1 game exe")

    def test_not_a_zip_fails(self):
        p = os.path.join(self.dir, "Inkwell_TheLastHour.zip")
        with open(p, "wb") as fh:
            fh.write(b"nope")
        self.assertIn("not a zip file", sc.zip_problems(p))

    def test_cli_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sc.main(["zip", self.make(good_files())]), 0)
            bad = good_files(GOOD_INFO.replace("Development", "Shipping"))
            self.assertEqual(sc.main(["zip", self.make(bad, "Inkwell_Bad.zip")]), 1)
            self.assertEqual(sc.main(["zip", os.path.join(self.dir, "missing.zip")]), 2)
        self.assertIn("sha256=", out.getvalue())


def probe(dur=45.0, w=1920, h=1080, audio=True):
    s = [{"codec_type": "video", "width": w, "height": h}]
    if audio:
        s.append({"codec_type": "audio"})
    return {"format": {"duration": str(dur)}, "streams": s}


class VideoTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(sc.video_problems(probe()), [])
        self.assertEqual(sc.video_problems(probe(30.0, 2560, 1440)), [])

    def test_too_short_and_too_long(self):
        self.assertTrue(sc.video_problems(probe(29.9)))
        self.assertTrue(sc.video_problems(probe(60.5)))

    def test_too_small(self):
        self.assertTrue(any("1280x720" in p for p in sc.video_problems(probe(w=1280, h=720))))

    def test_no_audio(self):
        self.assertTrue(any("audio" in p for p in sc.video_problems(probe(audio=False))))

    def test_no_video_stream(self):
        self.assertIn("no video stream", sc.video_problems({"format": {"duration": "40"}, "streams": []}))

    def test_missing_ffprobe_is_not_run(self):
        real = shutil.which
        try:
            sc.shutil.which = lambda _: None
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sc.main(["video", __file__]), 2)
        finally:
            sc.shutil.which = real

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg not installed")
    def test_real_small_clip_fails(self):
        d = tempfile.mkdtemp()
        try:
            clip = os.path.join(d, "clip.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=2",
                            "-f", "lavfi", "-i", "sine=f=440:d=2", "-shortest", clip], check=True)
            probs = sc.video_problems(sc.probe_video(clip))
            self.assertTrue(any("duration" in p for p in probs) and any("320x240" in p for p in probs), probs)
            lufs = sc.measure_lufs(clip)
            self.assertIsNotNone(lufs)
        finally:
            shutil.rmtree(d)


class LoudnessTests(unittest.TestCase):
    SUMMARY = "Summary:\n\n  Integrated loudness:\n    I:         {} LUFS\n    Threshold: -24.0 LUFS\n"

    def test_parse_and_pass(self):
        lufs = sc.integrated_lufs(self.SUMMARY.format("-14.5"))
        self.assertEqual(lufs, -14.5)
        self.assertEqual(sc.loudness_problems(lufs), [])

    def test_too_quiet_and_too_loud(self):
        self.assertTrue(sc.loudness_problems(sc.integrated_lufs(self.SUMMARY.format("-23.0"))))
        self.assertTrue(sc.loudness_problems(sc.integrated_lufs(self.SUMMARY.format("-9.0"))))

    def test_no_audio(self):
        self.assertTrue(sc.loudness_problems(sc.integrated_lufs("no summary")))


ITCH = ("## Page fields\n| Field | Value |\n|---|---|\n| Title | The Last Hour |\n| Genre | Action |\n"
        "## Team\n| Full name | Role | Team Owner (y/n) | Epic email collected (y/n) |\n|---|---|---|---|\n| Ana Ruiz | Programming | y | y |\n| Bo Chen | Art | n | y |\n"
        "## Credits by role\n- Game design: Ana Ruiz\n- Programming: Ana Ruiz\n- Art: Bo Chen\n- Audio: Bo Chen\n- Production: Ana Ruiz\n- QA: Bo Chen\n")
DECISIONS_OPEN = "| ID | Decision needed | Status |\n|---|---|---|\n| DEC-02 | auto-fire vs player-aimed shot | open |\n"
DECISIONS_DONE = DECISIONS_OPEN.replace("| open |", "| DECIDED 2026-11-12 (Rick): aimed shot |")


class PageTests(Tmp):
    def build(self, cover=(630, 500), shots=("volley", "rise", "gust")):
        if cover:
            png(os.path.join(self.dir, "cover.png"), *cover)
        for i, beat in enumerate(shots):
            png(os.path.join(self.dir, f"shot-{beat}.png"), 1920, 1080, seed=i + 1)

    def test_good(self):
        self.build()
        self.assertEqual(sc.page_problems(self.dir, ITCH), [])

    def test_cover_wrong_ratio(self):
        self.build(cover=(800, 500))
        self.assertTrue(any("315:250" in p for p in sc.page_problems(self.dir, ITCH)))

    def test_cover_too_small(self):
        self.build(cover=(315, 250))
        self.assertTrue(any("below 630x500" in p for p in sc.page_problems(self.dir, ITCH)))

    def test_cover_missing(self):
        self.build(cover=None)
        self.assertIn("cover.png missing", sc.page_problems(self.dir, ITCH))

    def test_too_few_and_too_many_shots(self):
        self.build(shots=("volley", "rise"))
        self.assertTrue(any("2 screenshots" in p for p in sc.page_problems(self.dir, ITCH)))
        for i, b in enumerate(("fall", "gust", "torn", "end")):
            png(os.path.join(self.dir, f"shot-{b}.png"), 1920, 1080, seed=10 + i)
        self.assertTrue(any("6 screenshots" in p for p in sc.page_problems(self.dir, ITCH)))

    def test_unknown_beat_and_duplicate(self):
        self.build()
        png(os.path.join(self.dir, "shot-menu.png"), 1920, 1080, seed=50)
        shutil.copy(os.path.join(self.dir, "shot-rise.png"), os.path.join(self.dir, "shot-fall.png"))
        probs = sc.page_problems(self.dir, ITCH)
        self.assertTrue(any("shot-menu.png" in p for p in probs), probs)
        self.assertTrue(any("same file" in p for p in probs), probs)

    def test_small_shot(self):
        self.build()
        png(os.path.join(self.dir, "shot-end.png"), 1280, 720, seed=60)
        self.assertTrue(any("1280x720" in p for p in sc.page_problems(self.dir, ITCH)))

    def test_tbd_field(self):
        self.build()
        self.assertTrue(any("Genre" in p for p in sc.page_problems(self.dir, ITCH.replace("Action", "TBD"))))
        self.assertTrue(any("no '## Page fields'" in p for p in sc.page_problems(self.dir, "")))

    def test_team_tbd_and_email_not_collected_fail(self):
        self.build()
        probs = sc.page_problems(self.dir, ITCH.replace("| Bo Chen | Art | n | y |", "| TBD | TBD | n | n |"))
        self.assertTrue(any("TBD" in p and "Team row" in p for p in probs), probs)
        self.assertTrue(any("Epic email collected is 'n'" in p for p in probs), probs)

    def test_no_team_rows_fails(self):
        self.build()
        text = ITCH.replace("| Ana Ruiz | Programming | y | y |\n| Bo Chen | Art | n | y |\n", "")
        self.assertTrue(any("no '## Team' table rows" in p for p in sc.page_problems(self.dir, text)))

    def test_credits_by_role_missing_or_unfilled_fails(self):
        self.build()
        probs = sc.page_problems(self.dir, ITCH.replace("- Audio: Bo Chen\n", "- Audio: TBD\n"))
        self.assertTrue(any("'- Audio:" in p for p in probs), probs)
        cut = ITCH.split("## Credits by role")[0]
        self.assertTrue(any("no '## Credits by role'" in p for p in sc.page_problems(self.dir, cut)))

    def test_member_not_credited_fails(self):
        self.build()
        text = ITCH.replace("| Bo Chen | Art | n | y |", "| Bo Chen | Art | n | y |\n| Cy Park | Audio | n | y |")
        self.assertTrue(any("'Cy Park'" in p for p in sc.page_problems(self.dir, text)))

    def test_controls_row_open_fails_and_decided_passes(self):
        self.build()
        self.assertTrue(any("DEC-02" in p and "open" in p for p in sc.page_problems(self.dir, ITCH, DECISIONS_OPEN)))
        self.assertTrue(any("no row DEC-02" in p for p in sc.page_problems(self.dir, ITCH, "| D2 | x | open |\n")))
        self.assertEqual(sc.page_problems(self.dir, ITCH, DECISIONS_DONE), [])

    def test_controls_need_dec02_and_dec01_settled(self):
        both = ("| ID | Decision needed | Status |\n|---|---|---|\n| DEC-02 | auto-fire vs aimed | DECIDED |\n"
                "| DEC-01 | keys | open |\n")
        self.assertTrue(any("DEC-01" in p for p in sc.controls_problems(both)))
        ok = both.replace("| DEC-01 | keys | open |", "| DEC-01 | keys | default accepted #12 |")
        self.assertEqual(sc.controls_problems(ok), [])

    def test_controls_row_with_old_question_fails_even_when_decided(self):
        self.build()
        old = DECISIONS_DONE.replace("auto-fire vs player-aimed shot", "falling attack or shooting from under the umbrella")
        probs = sc.page_problems(self.dir, ITCH, old)
        self.assertTrue(any("not the current GDD question" in p for p in probs), probs)

    def test_team_size_owner_and_full_name(self):
        """Official Rules 1(a), 1(c): 1 to 5 Entrants, full names, exactly one Team Owner."""
        self.assertEqual(sc.team_problems(ITCH), [])
        six = ITCH.replace("| Bo Chen | Art | n | y |\n", "".join(f"| P{i} Lee | QA | n | y |\n" for i in range(5)))
        self.assertTrue(any("6 members" in p for p in sc.team_problems(six)))
        two = ITCH.replace("| Bo Chen | Art | n | y |", "| Bo Chen | Art | y | y |")
        self.assertTrue(any("2 Team Owner" in p for p in sc.team_problems(two)))
        none = ITCH.replace("| Ana Ruiz | Programming | y | y |", "| Ana Ruiz | Programming | n | y |")
        self.assertTrue(any("0 Team Owner" in p for p in sc.team_problems(none)))
        short = ITCH.replace("| Bo Chen |", "| Bo |")
        self.assertTrue(any("full name" in p for p in sc.team_problems(short)))
        nocol = ITCH.replace("| Team Owner (y/n) ", "").replace("|---|---|---|---|", "|---|---|---|") \
            .replace("| y | y |", "| y |").replace("| n | y |", "| y |")
        self.assertTrue(any("no 'Team Owner" in p for p in sc.team_problems(nocol)))

    def test_repo_itch_page_fails_while_team_is_tbd(self):
        probs = sc.team_problems(sc.read(os.path.join(sc.ROOT, sc.ITCH_PAGE)))
        self.assertTrue(any("Team row" in p for p in probs), probs)


HEAD = "asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution\n"


class CreditsTests(Tmp):
    CSV = HEAD + ("Content/Audio/wind.wav,Jo,third-party,,,,,,2026-11-12,CC-BY 4.0,Jo (freesound)\n"
                  "Content/Fonts/Inky.ttf,Foundry,third-party,,,,,,2026-11-12,OFL,Foundry\n"
                  "Content/Art/ella.png,Team,hand-made,,,,,,2026-11-12,team-owned,\n"
                  "pipeline/art/reference/target-keyart.png,x,x,,,,,,2026-11-06,third-party,\n")
    CREDITS = "| Asset | Credit |\n|---|---|\n| Content/Audio/wind.wav | Jo |\n| Content/Fonts/Inky.ttf | Foundry |\n"

    def test_good(self):
        self.assertEqual(sc.credits_problems(self.CSV, self.CREDITS, ["Content/Fonts/Inky.ttf"]), [])

    def test_missing_credit(self):
        probs = sc.credits_problems(self.CSV, self.CREDITS.replace("Content/Audio/wind.wav", ""), [])
        self.assertTrue(any("wind.wav" in p for p in probs), probs)

    def test_fab_row_needs_credit(self):
        csv_text = self.CSV + "Content/Fab/rock.uasset,Studio,Fab,,,,,,2026-11-12,Fab Standard,\n"
        self.assertTrue(any("rock.uasset" in p for p in sc.credits_problems(csv_text, self.CREDITS, [])))

    def test_font_without_row(self):
        probs = sc.credits_problems(self.CSV, self.CREDITS, ["Content/UI/Fonts/Gothic.uasset"])
        self.assertTrue(any("Gothic.uasset" in p for p in probs), probs)

    def test_font_files_scan(self):
        os.makedirs(os.path.join(self.dir, "Content", "UI", "Fonts"))
        open(os.path.join(self.dir, "Content", "UI", "Fonts", "Gothic.uasset"), "w").close()
        open(os.path.join(self.dir, "Inky.otf"), "w").close()
        open(os.path.join(self.dir, "Content", "UI", "Button.uasset"), "w").close()
        self.assertEqual(sc.font_files(self.dir), ["Content/UI/Fonts/Gothic.uasset", "Inky.otf"])

    def test_art_without_provenance_fails(self):
        """Dry run B M1: a PNG under Art/ with no provenance row passed credits."""
        os.makedirs(os.path.join(self.dir, "Art", "Ella"))
        open(os.path.join(self.dir, "Art", "Ella", "ella_idle.png"), "wb").close()
        art = sc.art_files(self.dir)
        self.assertEqual(art, ["Art/Ella/ella_idle.png"])
        self.assertTrue(any("ella_idle.png: art file with no provenance" in p
                            for p in sc.credits_problems(self.CSV, self.CREDITS, [], art)))
        row = self.CSV.rstrip("\n").split("\n")[0].count(",") * ","
        csv_ok = self.CSV + "Art/Ella/ella_idle.png" + row[len(""):] + "\n"
        self.assertEqual([p for p in sc.credits_problems(csv_ok, self.CREDITS, [], art) if "ella_idle" in p], [])


DEVLOG = """## Went right
## Went wrong
## Change next time
## Daily obstacles
### Day 1
- Cook failed on a missing redirector, fixed in https://github.com/x/y/pull/12
- Reviewer eval missed a planted bug, #31
- Smoke hung at boot, gate-G1 record
### Day 2
- one line only, #40
Published: https://team.itch.io/the-last-hour/devlog/1/glass-box
"""


class DevlogTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(sc.devlog_problems(DEVLOG, 1, published=True), [])

    def test_too_few_obstacles(self):
        self.assertTrue(any("Day 2: 1" in p for p in sc.devlog_problems(DEVLOG, 2)))

    def test_line_without_link_does_not_count(self):
        text = DEVLOG.replace(", #31", "")
        self.assertTrue(any("Day 1: 2" in p for p in sc.devlog_problems(text, 1)))

    def test_missing_heading(self):
        self.assertTrue(any("Went wrong" in p for p in sc.devlog_problems(DEVLOG.replace("## Went wrong\n", ""), 1)))

    def test_not_published(self):
        text = DEVLOG.replace("Published: https://", "Published: TBD ")
        self.assertTrue(any("Published" in p for p in sc.devlog_problems(text, 1, published=True)))

    def test_repo_devlog_has_headings(self):
        text = sc.read(os.path.join(sc.ROOT, sc.DEVLOG))
        self.assertEqual(sc.devlog_problems(text, 0), [])


class PrejamTests(unittest.TestCase):
    DECL = "| `abc1234` | project skeleton (card 0.3) |\n"

    def test_declared_and_after_start_pass(self):
        lines = ["abc1234ffff\t2026-11-10T10:00:00-08:00", "def5678aaaa\t2026-11-12T09:00:00-08:00"]
        self.assertEqual(sc.prejam_problems(lines, self.DECL), [])

    def test_undeclared_early_commit_fails(self):
        lines = ["0badbad1111\t2026-11-11T20:59:00-08:00"]
        self.assertTrue(sc.prejam_problems(lines, self.DECL))

    def test_start_is_nov_11_2100_pst(self):
        # GDD 1.3 section 12A: the jam starts Nov 12 00:00 EST = Nov 11 21:00 PST (dry run A M1).
        self.assertEqual(sc.JAM_START.isoformat(), "2026-11-11T21:00:00-08:00")
        self.assertEqual(sc.prejam_problems(["0dd0dd01111\t2026-11-11T21:00:00-08:00"], self.DECL), [])
        self.assertEqual(sc.prejam_problems(["0dd0dd01111\t2026-11-12T00:30:00-05:00"], self.DECL), [])
        self.assertEqual(sc.prejam_problems(["0dd0dd01111\t2026-11-11T23:00:00-08:00"], self.DECL), [])
        self.assertTrue(sc.prejam_problems(["0badbad1111\t2026-11-11T20:59:00-08:00"], self.DECL))
        self.assertTrue(sc.prejam_problems(["0badbad1111\t2026-11-11T23:59:00-05:00"], self.DECL))

    def test_start_is_one_value_in_the_docs(self):
        for rel in ("docs/jam-rules.md", "docs/pre-jam-declaration.md"):
            with open(os.path.join(sc.ROOT, rel), encoding="utf-8") as f:
                text = f.read()
            with self.subTest(rel):
                self.assertIn("2026-11-11T21:00-08:00", text)
                self.assertNotIn("2026-11-12T00:00-08:00", text)

    def test_cli_with_log_file(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "log.txt")
            with open(p, "w") as f:
                f.write("0badbad1111\t2026-11-01T10:00:00-08:00\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sc.main(["prejam", "--log-file", p]), 1)
        finally:
            shutil.rmtree(d)


class DeclarationTests(unittest.TestCase):
    TEXT = "| Item | What |\n|---|---|\n| `tools/*.py`, `tools/ue/*` | scripts |\n| `AGENTS.md` | rules |\n"

    def test_covered(self):
        self.assertEqual(sc.declaration_problems(["tools/a.py", "tools/ue/b.ps1", "AGENTS.md"], self.TEXT), [])

    def test_undeclared_file_fails(self):
        probs = sc.declaration_problems(["Content/Art/ella.png"], self.TEXT)
        self.assertTrue(any("Content/Art/ella.png" in p for p in probs))

    def test_empty_declaration_fails(self):
        self.assertTrue(sc.declaration_problems(["AGENTS.md"], "no table"))

    def test_repo_declaration_covers_head(self):
        # final-9 A C1: the declaration covers what existed before the jam. Once card 0.3 tags jam-start, game files
        # exist and are not pre-jam, so the pre-jam tree is read from that tag; before it, from HEAD.
        tag = subprocess.run(["git", "-C", sc.ROOT, "rev-parse", "--verify", "--quiet", "jam-start^{commit}"],
                             capture_output=True, text=True)
        p = (subprocess.run(["git", "-C", sc.ROOT, "ls-tree", "-r", "--name-only", "jam-start"], capture_output=True,
                            text=True) if tag.returncode == 0 else
             subprocess.run(["git", "-C", sc.ROOT, "ls-files"], capture_output=True, text=True))
        if p.returncode != 0:
            self.skipTest("no git")
        paths = p.stdout.splitlines()
        # In a repo the pipeline was installed into, this test covers the files the pipeline put there (the install
        # record lists them). The team's own pre-jam files are theirs to declare: `submission_check.py declaration`.
        record = os.path.join(sc.ROOT, ".pipeline-installed.json")
        if os.path.isfile(record):
            import json
            with open(record, encoding="utf-8") as f:
                ours = set(json.load(f)["files"]) | {".pipeline-installed.json"}
            paths = [x for x in paths if x in ours]
            self.assertTrue(paths, "install record lists no tracked file")
        text = sc.read(os.path.join(sc.ROOT, sc.DECLARATION))
        self.assertEqual(sc.declaration_problems(paths, text), [])


PST = sc.dt.timezone(sc.dt.timedelta(hours=-8))
AFTER = sc.dt.datetime(2026, 11, 11, 13, 1, tzinfo=PST)
BEFORE = sc.dt.datetime(2026, 11, 11, 12, 59, tzinfo=PST)
BRIEF_OK = 'Theme: "Borrowed time"\nTheme in game: the owl\'s clock runs out while Ella survives on a borrowed hour.\n'


class ThemeTests(unittest.TestCase):
    def test_filled_passes(self):
        self.assertEqual(sc.theme_problems(BRIEF_OK, AFTER), [])

    def test_before_due_passes_empty(self):
        self.assertEqual(sc.theme_problems("", BEFORE), [])

    def test_empty_after_due_fails(self):
        self.assertEqual(len(sc.theme_problems("", AFTER)), 2)

    def test_tbd_and_unquoted_fail(self):
        self.assertTrue(sc.theme_problems(BRIEF_OK.replace('"Borrowed time"', "TBD"), AFTER))
        self.assertTrue(sc.theme_problems(BRIEF_OK.replace('"Borrowed time"', "Borrowed time"), AFTER))
        self.assertTrue(any("Theme in game" in p for p in
                            sc.theme_problems(BRIEF_OK.split("\n")[0] + "\nTheme in game: TBD\n", AFTER)))

    def test_due_is_pst(self):
        # 15:30 EST on Nov 11 is 12:30 PST: not due yet.
        self.assertEqual(sc.theme_problems("", sc.dt.datetime(2026, 11, 11, 15, 30,
                                           tzinfo=sc.dt.timezone(sc.dt.timedelta(hours=-5)))), [])

    def test_cli(self):
        d = tempfile.mkdtemp()
        try:
            b = os.path.join(d, "brief.md")
            with open(b, "w") as f:
                f.write("no theme\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sc.main(["theme", "--brief", b, "--now", "2026-11-11T14:00-08:00"]), 1)
                self.assertEqual(sc.main(["theme", "--brief", b, "--now", "2026-11-11T12:00-08:00"]), 0)
                self.assertEqual(sc.main(["theme", "--brief", b, "--now", "2026-11-11T14:00"]), 2)
        finally:
            shutil.rmtree(d)


class CaptureTests(unittest.TestCase):
    GOOD = "LogInit: start\nLogTemp: CAPTURE_MODE hud=off debug=off cursor=off\n"

    def test_good(self):
        self.assertEqual(sc.capture_problems(self.GOOD), [])

    def test_missing_line_fails(self):
        self.assertTrue(sc.capture_problems("LogInit: start\n"))

    def test_hud_on_fails(self):
        probs = sc.capture_problems(self.GOOD.replace("hud=off", "hud=on"))
        self.assertTrue(any("hud=on" in p for p in probs), probs)

    def test_missing_key_fails(self):
        self.assertTrue(any("cursor" in p for p in sc.capture_problems(self.GOOD.replace(" cursor=off", ""))))


FOOTAGE = """## Clips
### Day 1
### Day 2
- 2-volley-abc1234.mp4
- `2-rise-abc1234.mp4`
### Day 3
- 3-fall-def5678.mp4
- 3-gust-def5678.mp4
- 3-torn-def5678.mp4
- 3-end-def5678.mp4
### Day 4
"""


class FootageTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(sc.footage_problems(FOOTAGE, 3, final=True), [])

    def test_day1_not_required(self):
        self.assertEqual(sc.footage_problems("### Day 1\n", 1), [])

    def test_too_few_clips_fails(self):
        self.assertTrue(any("Day 4: 0" in p for p in sc.footage_problems(FOOTAGE, 4)))
        one = FOOTAGE.replace("- `2-rise-abc1234.mp4`\n", "")
        self.assertTrue(any("Day 2: 1" in p for p in sc.footage_problems(one, 2)))

    def test_wrong_day_and_bad_beat_do_not_count(self):
        moved = FOOTAGE.replace("- 2-volley-abc1234.mp4", "- 3-volley-abc1234.mp4")
        self.assertTrue(any("Day 2: 1" in p for p in sc.footage_problems(moved, 2)))
        bad = FOOTAGE.replace("2-volley", "2-menu")
        probs = sc.footage_problems(bad, 2)
        self.assertTrue(any("2-menu" in p for p in probs) and any("Day 2: 1" in p for p in probs), probs)

    def test_final_needs_every_beat(self):
        probs = sc.footage_problems(FOOTAGE.replace("3-torn", "3-gust2").replace("- 3-end-def5678.mp4\n", ""), 3, final=True,
                                    merged={"gust", "wear"})
        self.assertTrue(any("torn" in p and "end" in p for p in probs), probs)

    def test_p1_beats_wait_for_their_card(self):
        no_p1 = FOOTAGE.replace("3-torn", "3-volley2").replace("gust", "rise")
        self.assertEqual(sc.footage_problems(no_p1, 3, final=True, merged=set()), [])
        probs = sc.footage_problems(no_p1, 3, final=True, merged={"gust", "wear"})
        self.assertTrue(any("gust" in p and "torn" in p for p in probs), probs)

    def test_repo_footage_log_parses(self):
        text = sc.read(os.path.join(sc.ROOT, sc.FOOTAGE))
        self.assertEqual(sorted(sc.footage_clips(text)), [1, 2, 3, 4])
        self.assertEqual(sc.footage_problems(text, 1), [])


class DailyBase(Tmp):
    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)

    def setUp(self):
        super().setUp()
        self.write(sc.DEVLOG, DEVLOG)
        self.write(sc.FOOTAGE, FOOTAGE)
        self.write(sc.BRIEF, BRIEF_OK)


class DailyTests(DailyBase):
    def test_good(self):
        self.assertEqual(sc.daily_problems(1, AFTER, self.dir), [])

    def test_each_input_breaks_it(self):
        self.write(sc.BRIEF, "")
        self.assertTrue(any("Theme" in p for p in sc.daily_problems(1, AFTER, self.dir)))
        self.write(sc.BRIEF, BRIEF_OK)
        self.assertTrue(any("Day 2" in p and "obstacle" in p for p in sc.daily_problems(2, AFTER, self.dir)))
        self.write(sc.FOOTAGE, "")
        self.assertTrue(any("clip" in p for p in sc.daily_problems(2, AFTER, self.dir)))

    def test_repo_day0_passes_before_theme_due(self):
        self.assertEqual(sc.daily_problems(0, BEFORE), [])


CLOCK = """## Clock
Submission deadline: 2026-11-15T17:59-08:00

| Gate | Due |
|---|---|
| G1 | 2026-11-12T20:00-08:00 |
| G2 | 2026-11-13T20:00-08:00 |
| G3 | TBD |
| G4 | TBD |
"""


class StatusHookTests(DailyBase):
    def at(self, iso):
        return sc.parse_now(iso)

    def test_day_ended_from_clock(self):
        self.assertEqual(sc.day_ended(CLOCK, self.at("2026-11-12T19:59-08:00")), 0)
        self.assertEqual(sc.day_ended(CLOCK, self.at("2026-11-12T20:00-08:00")), 1)
        self.assertEqual(sc.day_ended(CLOCK, self.at("2026-11-14T09:00-08:00")), 2)
        self.assertEqual(sc.day_ended(CLOCK.replace("2026-11-12T20:00-08:00", "TBD")
                                      .replace("2026-11-13T20:00-08:00", "TBD"), self.at("2026-11-15T09:00-08:00")), 0)

    def test_empty_day1_devlog_fails_on_day2_morning(self):
        self.write(sc.DEVLOG, DEVLOG.split("### Day 1")[0] + "### Day 1\n### Day 2\n")
        probs = sc.status_hook(CLOCK + BRIEF_OK, self.at("2026-11-13T09:00-08:00"), self.dir)
        self.assertTrue(any("Day 1" in p and "obstacle" in p for p in probs), probs)

    def test_good_day1_passes_on_day2_morning(self):
        self.assertEqual(sc.status_hook(CLOCK + BRIEF_OK, self.at("2026-11-13T09:00-08:00"), self.dir), [])

    def test_before_g1_only_theme(self):
        self.write(sc.DEVLOG, "")
        self.assertEqual(sc.status_hook(CLOCK + BRIEF_OK, self.at("2026-11-12T09:00-08:00"), self.dir), [])
        self.assertTrue(sc.status_hook(CLOCK, self.at("2026-11-12T09:00-08:00"), self.dir))


class WiringTests(Tmp):
    W = (("a.md", "-CaptureMode", "capture card"), ("b.md", "!enemy defeat", "old set gone"))

    def put(self, rel, text):
        with open(os.path.join(self.dir, rel), "w") as f:
            f.write(text)

    def test_wired_passes(self):
        self.put("a.md", "card 0.6c: -CaptureMode logs ...")
        self.put("b.md", "owl, bolts")
        self.assertEqual(sc.wiring_problems(self.dir, self.W), [])

    def test_missing_and_banned_text_fail(self):
        self.put("a.md", "smoke only")
        self.put("b.md", "enemy defeat sound")
        probs = sc.wiring_problems(self.dir, self.W)
        self.assertTrue(any("has no '-CaptureMode'" in p for p in probs), probs)
        self.assertTrue(any("still has 'enemy defeat'" in p for p in probs), probs)

    def test_missing_file_fails(self):
        self.assertTrue(any("a.md" in p for p in sc.wiring_problems(self.dir, self.W[:1])))


class WiringTableTests(unittest.TestCase):
    def test_qa_needle_matches_jam_rule_2(self):
        rules = sc.read(os.path.join(sc.ROOT, sc.JAM_RULES))
        needles = [n for f, n, _ in sc.WIRING if f.endswith("qa-build.md") and not n.startswith("!")]
        self.assertIn("G<n>-<sha>/<TeamName>_<GameName>.zip", needles)
        self.assertIn("`G<n>-<sha>/`", rules)

    def test_new_duties_are_wired(self):
        pairs = {(f, n) for f, n, _ in sc.WIRING}
        for need in (("tools/ue/package.ps1", "README.txt"), ("tools/ue/package.ps1", "LICENSE.txt"),
                     ("pipeline/day0-cards.md", "jam-rules.md row AI"), ("pipeline/roles/producer.md", "submission_check.py daily"),
                     ("pipeline/templates/gate-record.md", "!uploaded to the jam page")):
            self.assertIn(need, pairs)


README_TXT = "Title: The Last Hour\nOne line.\n\nControls\nA/D move\n\nTeam\nInkwell: Rick\n\nCredits\nFont X (OFL)\n"
LICENSE_TXT = "Copyright 2026 Inkwell. All rights reserved.\n"


class FilesTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(sc.files_problems(README_TXT, LICENSE_TXT, final=True), [])

    def test_missing_and_empty_fail(self):
        probs = sc.files_problems(None, "  \n")
        self.assertTrue(any("README.txt missing" in p for p in probs), probs)
        self.assertTrue(any("LICENSE.txt is empty" in p for p in probs), probs)

    def test_missing_section_and_title_fail(self):
        probs = sc.files_problems(README_TXT.replace("Controls\n", "Keys\n").replace("Title:", "Name:"), LICENSE_TXT)
        self.assertTrue(any("'Controls'" in p for p in probs) and any("Title:" in p for p in probs), probs)

    def test_pipeline_text_fails(self):
        self.assertTrue(any("pipeline text" in p for p in sc.files_problems(README_TXT + "ROLE: QA\n", LICENSE_TXT)))
        self.assertTrue(any("pipeline text" in p for p in sc.files_problems(README_TXT + "see card 0.2\n", LICENSE_TXT)))

    def test_no_copyright_fails(self):
        self.assertTrue(any("Copyright" in p for p in sc.files_problems(README_TXT, "Free to play.\n")))

    def test_tbd_fails_only_with_final(self):
        lic = "Copyright 2026 TBD. All rights reserved.\n"
        self.assertEqual(sc.files_problems(README_TXT, lic), [])
        self.assertTrue(any("TBD" in p for p in sc.files_problems(README_TXT, lic, final=True)))

    def test_repo_templates_pass_and_fail_final(self):
        def rd(rel):
            return sc.read(os.path.join(sc.ROOT, rel))
        self.assertEqual(sc.files_problems(rd(sc.README_TXT), rd(sc.LICENSE_TXT)), [])
        self.assertTrue(sc.files_problems(rd(sc.README_TXT), rd(sc.LICENSE_TXT), final=True))


class ButlerTests(unittest.TestCase):
    GOOD = "BUTLER version=v15.21.0 login=ok user=inkwell by=Rick"

    def test_good(self):
        self.assertEqual(sc.butler_problems(self.GOOD), [])

    def test_login_failed(self):
        self.assertTrue(any("login" in p for p in sc.butler_problems(self.GOOD.replace("login=ok", "login=fail"))))

    def test_missing_version_user_by(self):
        probs = sc.butler_problems("BUTLER login=ok user=<itch-user>")
        self.assertTrue(any("version" in p for p in probs) and any("user" in p for p in probs)
                        and any("by" in p for p in probs), probs)

    def test_not_a_butler_line(self):
        self.assertTrue(sc.butler_problems("Gate: G1"))


class RulesTests(unittest.TestCase):
    def test_clean_passes(self):
        self.assertEqual(sc.rules_problems("| Video | quote |\n"), [])

    def test_verify_left_fails(self):
        self.assertTrue(any("2 [VERIFY]" in p for p in sc.rules_problems("[VERIFY a]\n[VERIFY in the PDF]\n")))


class SignoffTests(unittest.TestCase):
    GOOD = "VIDEO first-frame=gameplay logo-first=no gameplay-by=0.5 end=logo+CTA music=yes sfx-beats=yes by=Rick"

    def test_good(self):
        self.assertEqual(sc.signoff_problems(self.GOOD), [])
        self.assertEqual(sc.signoff_problems(self.GOOD.replace("0.5", "4s")), [])

    def test_no_music_fails(self):
        self.assertTrue(any("music" in p for p in sc.signoff_problems(self.GOOD.replace("music=yes", "music=no"))))

    def test_missing_sfx_fails(self):
        self.assertTrue(any("sfx-beats" in p for p in sc.signoff_problems(self.GOOD.replace(" sfx-beats=yes", ""))))

    def test_late_gameplay_fails(self):
        self.assertTrue(any("gameplay-by" in p for p in sc.signoff_problems(self.GOOD.replace("0.5", "6"))))

    def test_logo_first_and_no_name_fail(self):
        self.assertTrue(sc.signoff_problems(self.GOOD.replace("logo-first=no", "logo-first=yes")))
        self.assertTrue(any("by=" in p for p in sc.signoff_problems(self.GOOD.replace(" by=Rick", ""))))

    def test_not_a_video_line(self):
        self.assertTrue(sc.signoff_problems("PLAYTHROUGH commit=abc"))


if __name__ == "__main__":
    unittest.main()


class OfficialRulesChecks(unittest.TestCase):
    """Official Rules 7(h) pre-jam assets, 7(i) English, and the rules command's ties to the pinned PDF text."""
    PROV = HEAD

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "pipeline", "art", "reference"))
        with open(os.path.join(self.root, "pipeline", "art", "reference", "keyart.png"), "wb") as fh:
            fh.write(b"\x89PNG pre-jam key art")

    def tearDown(self):
        shutil.rmtree(self.root)

    def row(self, path, date):
        return self.PROV + f"{path},Ana Ruiz,made in jam,Aseprite,,,,,{date},team,none\n"

    def test_assets_in_jam_pass(self):
        for date in ("2026-11-12", "2026-11-11T21:30-08:00", "2026-11-14"):
            with self.subTest(date=date):
                self.assertEqual(sc.assets_problems(self.row("Art/Sprites/ella.png", date), "", self.root), [])
        self.assertEqual(sc.assets_problems(self.row("pipeline/art/reference/keyart.png", "2026-11-06"), "", self.root), [])

    def test_prejam_asset_fails_unless_sourced(self):
        for date in ("2026-11-06", "2026-11-11", "2026-11-11T20:59-08:00"):
            with self.subTest(date=date):
                self.assertTrue(sc.assets_problems(self.row("Content/UmbrellaElla/Art/T_Sky.uasset", date), "", self.root))
        credits = "## Sourced assets\n| Asset path | Made by | Licence | Why sourced |\n|---|---|---|---|\n" \
                  "| `Content/UmbrellaElla/Art/T_Sky.uasset` | Fab | CC-BY | sky pack |\n"
        self.assertEqual(sc.assets_problems(self.row("Content/UmbrellaElla/Art/T_Sky.uasset", "2026-11-06"), credits,
                                            self.root), [])
        self.assertTrue(sc.assets_problems(self.row("Audio/Source/rain.wav", "last week"), "", self.root))

    def test_reference_art_copied_into_the_game_fails(self):
        os.makedirs(os.path.join(self.root, "Art"))
        shutil.copy(os.path.join(self.root, "pipeline", "art", "reference", "keyart.png"),
                    os.path.join(self.root, "Art", "title.png"))
        self.assertTrue(any("never shipped" in p for p in sc.assets_problems(self.PROV, "", self.root)))

    def test_english(self):
        self.assertEqual(sc.english_problems([("README.txt", "Title: Umbrella Ella\nCredits: José Núñez")]), [])
        for text in ("Título: 雨の傘", "Привет", "Γεια"):
            with self.subTest(text=text):
                self.assertTrue(sc.english_problems([("strings.csv", text)]))

    def test_rules_ties_to_the_pdf_text_and_clock(self):
        jr = sc.read(os.path.join(sc.ROOT, sc.JAM_RULES))
        off = sc.read(os.path.join(sc.ROOT, sc.OFFICIAL_RULES))
        brief = "Submission deadline: 2026-11-15T17:59-08:00\n"
        self.assertEqual(sc.rules_problems(jr, off, brief), [])
        self.assertTrue(sc.rules_problems(jr, off, "Submission deadline: 2026-11-15T20:59-08:00\n"), "wrong deadline")
        self.assertTrue(sc.rules_problems(jr, off.replace("one (1) to five (5)", "one (1) to four (4)"), brief))
        self.assertTrue(sc.rules_problems(jr + "\n[VERIFY] x\n", off, brief))
        uncited = "\n".join(ln.replace("§", "s.") if ln.startswith("| Video |") else ln for ln in jr.splitlines())
        self.assertTrue(any("'Video'" in p for p in sc.rules_problems(uncited, off, brief)))


class ContentSignoff(unittest.TestCase):
    def test_content_line(self):
        good = "CONTENT teen=yes trademarks=ue-logo-only original=yes extra-software=none english=yes by=Rick"
        self.assertEqual(sc.signoff_problems(good), [])
        for bad in (good.replace("teen=yes", "teen=no"), good.replace("ue-logo-only", "some"),
                    good.replace(" by=Rick", ""), good.replace("by=Rick", "by=agent"), good.replace("english=yes", "")):
            with self.subTest(line=bad):
                self.assertTrue(sc.signoff_problems(bad))

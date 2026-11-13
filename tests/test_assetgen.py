"""Agent-driven asset steps (tools/assetgen.py), the audio source rule (audio_check source_problems) and the MCP
config for both agents (tools/mcp_config.py). Every API and app is a stub (tests/fixtures/kickoff/): no network, no
credits. Each check has a passing case and a case broken on purpose."""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures", "kickoff")
sys.path.insert(0, FIX)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audio_check  # noqa: E402
import mcp_config  # noqa: E402
import stubbins  # noqa: E402

PY = sys.executable
KEYS = ("OPENAI_API_KEY", "GEMINI_API_KEY", "IMAGE_SPEND_FILE", "IMAGE_SPEND_CAP_USD", "BLENDER_STUB_LOG", "ASSETGEN_NO_APP_DIRS", "ELEVENLABS_API_KEY", "STABILITY_API_KEY", "JAM_OUTBOX", "JAM_ROLE", "ASSETGEN_FULFIL")


class Work(unittest.TestCase):
    """A small repo with the tools, the art, audio and agent-ops data, and stub tools."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        self.repo = os.path.join(self.d, "repo")
        shutil.copytree(os.path.join(ROOT, "tools"), os.path.join(self.repo, "tools"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        for sub in ("agent-ops", "art", "audio"):
            shutil.copytree(os.path.join(ROOT, "pipeline", sub), os.path.join(self.repo, "pipeline", sub),
                            ignore=shutil.ignore_patterns("reference", "proof", "__pycache__"))   # proof is ~800 MB of lane output no test reads (Nov 13: disk churn)
        lay = os.path.join("pipeline", "art", "reference", "Test_Assets", "SpriteLayout.json")   # the layout entry
        os.makedirs(os.path.dirname(os.path.join(self.repo, lay)), exist_ok=True)
        shutil.copy(os.path.join(ROOT, lay), os.path.join(self.repo, lay))
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        self.bin = stubbins.make(os.path.join(self.d, "bin"))
        self.http_log = os.path.join(self.d, "http.log")

    def env(self, **extra):
        e = {k: v for k, v in os.environ.items() if k not in KEYS}
        e.update(stubbins.tool_env(self.bin))
        e.update(KEYS_NO_KEYCHAIN="1", ASSETGEN_HTTP_STUB=os.path.join(FIX, "http_stub.py"),
                 HTTP_STUB_LOG=self.http_log, PATH=self.bin + os.pathsep + os.environ.get("PATH", ""))
        e.update(extra)
        return {k: v for k, v in e.items() if v is not None}

    def ag(self, *args, **extra):
        p = subprocess.run([PY, "tools/assetgen.py", *args], cwd=self.repo, capture_output=True, text=True,
                           env=self.env(**extra))
        return p.returncode, p.stdout + p.stderr

    def tool(self, *args, **extra):
        p = subprocess.run([PY, *args], cwd=self.repo, capture_output=True, text=True, env=self.env(**extra))
        return p.returncode, p.stdout + p.stderr

    def prov(self):
        with open(os.path.join(self.repo, "pipeline", "art", "provenance.csv"), encoding="utf-8") as fh:
            return {r["asset_path"]: r for r in csv.DictReader(fh)}

    def noblender(self):
        """No Blender anywhere: not on PATH, no $BLENDER, no install folder."""
        return dict(BLENDER=None, ASSETGEN_NO_APP_DIRS="1",
                    PATH=stubbins.system_path(os.path.join(self.d, "sys-bin"), hide=("blender",)))

    def calls(self):
        return open(self.http_log).read().split() if os.path.exists(self.http_log) else []


class ArtSteps(Work):
    """Blender is the art generator (Josh, 11 Nov): every frame is rendered headless from a recipe row; no image API,
    no art key. The stub Blender (tests/fixtures/kickoff/stubbins.py) writes the frames the job names."""

    def test_blender_frames_and_sheet_pass_sprite_check_with_provenance(self):
        log = os.path.join(self.d, "blender.log")
        rc, o = self.ag("blender", "--character", "ella", "--anim", "IdleFloat", "--sheet",
                        "Art/Sprites/Ella/ella_idle.png", BLENDER_STUB_LOG=log)
        self.assertEqual(rc, 0, o)
        self.assertIn("BLENDER ella IdleFloat frames=6 432x352 pivot=229,188 fps=8", o)
        rc, o = self.tool("tools/sprite_check.py", "--scan", "Art")
        self.assertEqual(rc, 0, "renders stay under Raw/, the sheet has its sidecar:\n" + o)
        argv = json.loads(open(log).read().splitlines()[0])
        self.assertEqual(argv[:3], ["-b", "--factory-startup", "-P"])
        self.assertTrue(argv[3].endswith(os.path.join("pipeline", "art", "blender", "render_sprite.py")), argv)
        self.assertEqual(argv[4:6], ["--", "--job"])
        self.assertTrue(argv[6].endswith("Art/Source/Ella/Raw/IdleFloat/Ella_IdleFloat.job.json"), argv)
        p = self.prov()
        rows = [p[f"Art/Source/Ella/Raw/IdleFloat/Ella_IdleFloat_{i:02d}.png"] for i in range(6)]
        for r in rows:
            self.assertEqual(r["tool"], "Blender (headless scripts)")
            self.assertEqual(r["model_version"], "Blender 4.5.0")
            self.assertIn("pipeline/art/blender/render_sprite.py", r["input_images"])
            self.assertIn("Art/Source/Ella/Raw/IdleFloat/Ella_IdleFloat.blend", r["input_images"])
            self.assertIn("Ella_IdleFloat.job.json", r["input_images"])
            self.assertIn("style targets for piece ella-up-open", r["origin"])
            self.assertIn("never shipped", r["origin"])
            self.assertNotIn("pipeline/art/reference/", r["input_images"], "references are style targets, not inputs")
        self.assertEqual({(r["seed"], r["prompt"]) for r in rows}, {(rows[0]["seed"], rows[0]["prompt"])},
                         "every frame: one job, one seed, one recipe")
        self.assertEqual(p["Art/Sprites/Ella/ella_idle.png"]["tool"], "Aseprite CLI")
        side = json.load(open(os.path.join(self.repo, "Art/Sprites/Ella/ella_idle.sprite.json")))
        self.assertEqual((side["frames"], side["fps"], side["anim"]), (6, 8, "IdleFloat"))

    def test_image_renders_a_still_in_session_and_never_queues(self):
        box = os.path.join(self.d, "outbox")
        rc, o = self.ag("image", "--prompt", "the owl bolt", "--out", "Art/Source/Bolt/bolt.png", "--element",
                        "effects", "--provider", "blender", JAM_OUTBOX=box, JAM_ROLE="asset-specialist")
        self.assertEqual(rc, 0, o)
        self.assertIn("via=blender character=bolt anim=Still", o)
        self.assertFalse(os.path.exists(os.path.join(box, "asset-requests.jsonl")), "art needs no key: no queue")
        row = self.prov()["Art/Source/Bolt/bolt.png"]
        self.assertTrue(row["author"].startswith("asset-specialist"))
        self.assertIn("Bolt_Still_00.png", row["input_images"])
        self.assertEqual(self.calls(), [], "no network call for art")

    def test_no_blender_gives_labelled_placeholders(self):
        rc, o = self.ag("image", "--prompt", "Owl", "--out", "Art/Source/Owl/o.png", "--provider", "blender",
                        **self.noblender())
        self.assertEqual(rc, 0, o)
        self.assertIn("PLACEHOLDER", o)
        self.assertIn("placeholder", self.prov()["Art/Source/Owl/o.png"]["origin"])
        rc, o = self.ag("blender", "--character", "owl", "--anim", "Flap", **self.noblender())
        self.assertEqual(rc, 0, o)
        self.assertIn("NOTE: no Blender", o)
        row = self.prov()["Art/Source/Owl/Raw/Flap/Owl_Flap_00.png"]
        self.assertIn("never accepted as art", row["origin"])

    def test_broken_on_purpose_bad_recipe_rows_and_out_dirs_fail(self):
        rc, o = self.ag("blender", "--character", "ella", "--anim", "Attack", "--frames", "9")
        self.assertEqual(rc, 1, o)
        self.assertIn("allows 3-4", o)
        rc, o = self.ag("blender", "--character", "ella", "--anim", "Attack", "--out-dir", "Art/Sprites/Ella")
        self.assertEqual(rc, 1, o)
        self.assertIn("Raw/", o)
        rc, o = self.ag("blender", "--character", "dragon", "--anim", "Flap")
        self.assertEqual(rc, 1, o)
        self.assertIn("no Blender recipe", o)

    def test_broken_on_purpose_opaque_frames_fail_sprite_check(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        from png import write_png
        frames = []
        for i in range(4):
            f = os.path.join(self.repo, f"Art/Source/Ella/Clean/f{i}.png")
            os.makedirs(os.path.dirname(f), exist_ok=True)
            write_png(f, 64, 64, [[(231, 220, 196, 255)] * 64 for _ in range(64)])
            frames.append(f)
        self.ag("sheet", "--frames", *frames, "--out", "Art/Sprites/Ella/ella_idle.png", "--anim", "IdleFloat",
                "--fps", "8")
        rc, o = self.tool("tools/sprite_check.py", "--scan", "Art/Sprites")
        self.assertEqual(rc, 1, "an opaque paper background is not cut out:\n" + o)

    def test_image_model_keys_are_listed_and_never_reach_a_session(self):
        """D-new-art-image-model: the image keys are in the inventory and keys.py, and scrub strips them."""
        inv = json.load(open(os.path.join(ROOT, "pipeline", "agent-ops", "asset-tools.json")))
        self.assertIn("GEMINI_API_KEY", inv["keys"])
        self.assertIn("OPENAI_API_KEY", inv["keys"])
        import keys
        self.assertEqual(set(keys.IMAGE_KEYS), {"GEMINI_API_KEY", "OPENAI_API_KEY"})
        self.assertEqual(keys.scrub({"OPENAI_API_KEY": "x", "GEMINI_API_KEY": "y", "ELEVENLABS_API_KEY": "z",
                                     "HOME": "h"}), {"HOME": "h"}, "no key ever reaches a session")


class PracticeReferenceArt(Work):
    """Josh: in a PRACTICE repo (.pipeline-practice) art cards may place the team's reference art as stand-ins, picked
    by references.json role, so a test run looks right without Blender. Broken on purpose: the same command on a
    non-practice repo fails, and submission_check.py assets fails the stand-in's row there."""

    def setUp(self):
        super().setUp()
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        from png import write_png
        for rel, color in (("pipeline/art/reference/Test_Assets/CHR_Owl_Flap_Damage.png", (90, 60, 30, 255)),
                           ("pipeline/art/reference/Test_Assets/FX_Owl_Missile.png", (160, 40, 30, 255)),
                           ("pipeline/art/reference/Rehearsal/Ella/Ella-Rising-02.png", (20, 20, 24, 255)),
                           ("pipeline/art/reference/Test_Assets/SKY_StarPaper_Tile.png", (200, 180, 140, 255)),
                           ("pipeline/art/reference/discord/art-direction-01.png", (120, 100, 80, 255))):
            full = os.path.join(self.repo, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            write_png(full, 8, 8, [[color] * 8 for _ in range(8)])

    def practice(self):
        with open(os.path.join(self.repo, ".pipeline-practice"), "w") as fh:
            fh.write("practice\n")

    def bytes_of(self, rel):
        with open(os.path.join(self.repo, rel), "rb") as fh:
            return fh.read()

    def test_practice_places_the_best_matching_reference_by_role(self):
        self.practice()
        for out, prompt, want in (("Art/Source/Owl/owl.png", "the clockwork owl, wings open", "CHR_Owl_Flap_Damage"),
                                  ("Art/Source/Bolt/bolt.png", "an owl missile in flight", "FX_Owl_Missile"),
                                  ("Art/Source/Ella/up.png", "Ella rising, umbrella open", "Ella-Rising-02"),
                                  ("Art/Source/Bg/sky.png", "far sky layer", "SKY_StarPaper_Tile")):
            with self.subTest(out=out):
                rc, o = self.ag("image", "--prompt", prompt, "--out", out, "--provider", "reference")
                self.assertEqual(rc, 0, o)
                self.assertIn(want, o)
                row = self.prov()[out]
                self.assertIn("source=reference (practice)", row["origin"])
                self.assertIn(want, row["input_images"])
        rc, o = self.ag("image", "--prompt", "Owl", "--out", "Art/Source/Owl/nokey.png", "--provider", "blender",
                        **self.noblender())   # no Blender: reference, not a placeholder
        self.assertEqual(rc, 0, o)
        self.assertIn("REFERENCE", o)
        self.assertEqual(self.bytes_of("Art/Source/Owl/nokey.png"), self.bytes_of("pipeline/art/reference/Test_Assets/CHR_Owl_Flap_Damage.png"))
        self.assertEqual(self.calls(), [], "no image API call")
        import submission_check as sc
        with open(os.path.join(self.repo, "pipeline", "art", "provenance.csv"), encoding="utf-8") as fh:
            prov = fh.read()
        self.assertEqual([p for p in sc.assets_problems(prov, "", self.repo, start=None) if "Art/Source" in p], [],
                         "a practice repo accepts its labelled stand-ins")
        self.assertTrue(any("source=reference (practice)" in p for p in sc.assets_problems(prov, "", self.repo)),
                        "broken on purpose: the same rows fail on the team repo")

    def test_team_repo_refuses_reference_art(self):
        rc, o = self.ag("image", "--prompt", "Owl", "--out", "Art/Source/Owl/owl.png", "--provider", "reference")
        self.assertEqual(rc, 1, o)
        self.assertIn("practice-repo stand-in only", o)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "Art/Source/Owl/owl.png")))
        rc, o = self.ag("image", "--prompt", "Owl", "--out", "Art/Source/Owl/o.png", "--provider", "blender",
                        **self.noblender())   # no Blender, not practice
        self.assertEqual(rc, 0, o)
        self.assertIn("PLACEHOLDER", o)
        self.assertNotIn("reference", self.prov()["Art/Source/Owl/o.png"]["origin"])

    def test_art_direction_images_are_in_the_pool(self):
        self.practice()
        rc, o = self.ag("image", "--prompt", "a style frame", "--out", "Art/Source/Frame/f.png", "--provider",
                        "reference", "--element", "frame")
        self.assertEqual(rc, 0, o)
        self.assertRegex(o, r"<- (pipeline/art/reference/|Test_Assets/|Rehearsal/)")


class AudioSteps(Work):
    OUT = "Audio/Source/GustCatch/SW_GustCatch_00.wav"

    def make(self, **keys):
        rc, o = self.ag("sfx", "--sound", "GustCatch", "--prompt", "umbrella catches a gust", "--out", "Audio/Raw/g.wav", "--seconds", "1",
                        **keys)
        self.assertEqual(rc, 0, o)
        rc, o = self.ag("edit", "--in", "Audio/Raw/g.wav", "--out", self.OUT)
        self.assertEqual(rc, 0, o)
        return self.prov()[self.OUT]

    def scan_lines(self):
        rc, o = self.tool("tools/audio_check.py", "--scan", "Audio/Source")
        return [ln for ln in o.splitlines() if self.OUT in ln]

    def test_elevenlabs_take_passes_audio_check_with_its_licence(self):
        row = self.make(ELEVENLABS_API_KEY="fake-eleven-0123456789abcdef")
        self.assertEqual(row["tool"], "ElevenLabs Sound Effects API")
        lines = self.scan_lines()
        self.assertTrue(lines and not any(ln.startswith("FAIL") for ln in lines), lines)

    def test_synth_fallback_with_no_key(self):
        row = self.make()
        self.assertEqual(row["tool"], "Procedural synthesis (tools/assetgen.py synth)")
        self.assertEqual(audio_check.source_problems(row), [])

    def test_no_credits_left_makes_a_tracked_placeholder_and_the_run_goes_on(self):
        """ElevenLabs answers HTTP 401 quota_exceeded (the account ran out of credits): the step still exits 0 with a
        procedural take whose provenance says `placeholder: ...`, the edit keeps that mark, --placeholders lists it,
        and only --release fails it. Broken on purpose: the same take with the mark taken out is no placeholder."""
        rc, o = self.ag("sfx", "--sound", "GustCatch", "--out", "Audio/Raw/g.wav", "--seconds", "1",
                        ELEVENLABS_API_KEY="fake-nocredits-0123456789abcdef")
        self.assertEqual(rc, 0, o)
        self.assertIn("PLACEHOLDER Audio/Raw/g.wav", o)
        self.assertIn("quota_exceeded", o)
        self.assertNotIn("fake-nocredits", o, "the key never reaches the output")
        rc, o = self.ag("edit", "--in", "Audio/Raw/g.wav", "--out", self.OUT)
        self.assertEqual(rc, 0, o)
        row = self.prov()[self.OUT]
        self.assertEqual(row["tool"], "Procedural synthesis (tools/assetgen.py synth)")
        self.assertRegex(row["origin"], r"placeholder: elevenlabs failed: HTTP 401 .*quota_exceeded")
        self.assertEqual(audio_check.source_problems(row), [])
        rc, o = self.tool("tools/audio_check.py", "--placeholders")
        self.assertEqual(rc, 0, o)
        self.assertIn(f"PLACEHOLDER {self.OUT}: elevenlabs failed: HTTP 401", o)
        rc, o = self.tool("tools/audio_check.py", "--scan", "Audio/Source")
        self.assertNotIn("tracked placeholder", o)
        rc, o = self.tool("tools/audio_check.py", "--scan", "Audio/Source", "--release")
        self.assertIn(f"{self.OUT}: tracked placeholder", o)
        path = os.path.join(self.repo, "pipeline", "art", "provenance.csv")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace("; placeholder: ", "; ").replace(" placeholder: ", " "))
        rc, o = self.tool("tools/audio_check.py", "--placeholders")
        self.assertIn("0 tracked placeholder take(s)", o)

    def test_network_failure_is_a_placeholder_too(self):
        rc, o = self.ag("sfx", "--sound", "GustCatch", "--out", self.OUT, "--seconds", "1",
                        ELEVENLABS_API_KEY="fake-eleven-0123456789abcdef", ASSETGEN_HTTP_STUB=os.path.join(self.d, "x.py"))
        self.assertEqual(rc, 0, o)
        self.assertIn("PLACEHOLDER", o)
        self.assertIn("placeholder: elevenlabs failed:", self.prov()[self.OUT]["origin"])

    def test_broken_on_purpose_wrong_licence_or_unknown_generator_fails(self):
        row = self.make(STABILITY_API_KEY="fake-stability-0123456789abcdefgh")
        self.assertEqual(row["tool"], "Stable Audio 3 API (Stability AI)")
        self.assertEqual(audio_check.source_problems(row), [])
        self.assertTrue(audio_check.source_problems(dict(row, licence="CC0")))
        self.assertTrue(audio_check.source_problems(dict(row, tool="SomeOtherAI")))
        self.assertEqual(audio_check.source_problems({"tool": "Audacity", "origin": "hand-made", "licence": "CC0"}), [],
                         "a hand-made take with another tool still passes")


class AudioPrompts(Work):
    """Audio prompts come from pipeline/audio/style.json (pipeline/audio/style-target.md), never free text alone."""

    def test_prompt_is_built_from_the_style_target_and_notes_the_key(self):
        rc, o = self.ag("sfx", "--sound", "GustCatch", "--prompt", "less hiss", "--out", "Audio/Raw/g.wav")
        self.assertEqual(rc, 0, o)
        self.assertIn("NOTE: no audio API key", o)
        self.assertIn("perks include no audio tool", o)
        prompt = self.prov()["Audio/Raw/g.wav"]["prompt"]
        style = json.load(open(os.path.join(ROOT, "pipeline", "audio", "style.json")))
        self.assertTrue(prompt.startswith(style["families"]["wind"]["prompts"]["GustCatch"]), prompt)
        rc, o = self.ag("music", "--out", "Audio/Source/MusicIntro/SW_MusicIntro_00.wav", "--seconds", "1")
        self.assertEqual(rc, 0, o)
        self.assertIn("string drone", self.prov()["Audio/Source/MusicIntro/SW_MusicIntro_00.wav"]["prompt"],
                      "the id comes from the out name")

    def test_broken_on_purpose_no_sound_id_or_a_named_game_fails(self):
        rc, o = self.ag("sfx", "--prompt", "a whoosh", "--out", "Audio/Raw/x.wav")
        self.assertEqual(rc, 2, o)
        self.assertIn("name the sound", o)
        rc, o = self.ag("sfx", "--sound", "HitOwl", "--prompt", "like Bloodborne", "--out", "Audio/Raw/x.wav")
        self.assertEqual(rc, 2, o)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "Audio/Raw/x.wav")))

    def test_supplied_row_is_never_generated(self):
        with open(os.path.join(self.repo, "pipeline", "art", "provenance.csv"), "a", encoding="utf-8") as fh:
            fh.write("Audio/Source/GustCatch/SW_GustCatch_00.wav,Rick,supplied,Supplied file (tools/audio_import.py),"
                     "none,trim,,Audio/Import/gust.wav,2026-11-13,Team original,Rick\n")
        rc, o = self.ag("sfx", "--sound", "GustCatch", "--out", "Audio/Raw/g.wav")
        self.assertEqual(rc, 2, o)
        self.assertIn("supplied take", o)


class VideoAndZip(Work):
    def test_capture_cut_then_submission_check_video(self):
        game = stubbins.script(os.path.join(self.bin, "game"), "import time\ntime.sleep(5)", python=PY)
        rc, o = self.ag("capture", "--exe", game, "--seconds", "50", "--out", "Saved/Video/raw.mkv")
        self.assertEqual(rc, 0, o)
        rc, o = self.tool("tools/submission_check.py", "video", "Saved/Video/raw.mkv")
        self.assertEqual(rc, 1, "broken on purpose: the raw capture is not 1080p:\n" + o)
        rc, o = self.ag("cut", "--in", "Saved/Video/raw.mkv", "--out", "pipeline/submission/video/gameplay.mp4",
                        "--duration", "45")
        self.assertEqual(rc, 0, o)
        rc, o = self.tool("tools/submission_check.py", "video", "pipeline/submission/video/gameplay.mp4")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.ag("cut", "--in", "x", "--out", "y.mp4", "--duration", "75")[0], 2)

    def test_zip_step_python_fallback(self):
        pkg = os.path.join(self.repo, "Packaged", "Windows")
        os.makedirs(pkg)
        open(os.path.join(pkg, "README.txt"), "w").close()
        # hide 7z wherever the host installed it (Linux CI runners ship it in /usr/bin)
        sysbin = stubbins.system_path(os.path.join(self.repo, "Saved", "sys-bin"), hide=("7z", "7za", "7zr", "7zz"))
        rc, o = self.ag("zip", "--dir", "Packaged/Windows", "--out", "Saved/Zip/Team_Game.zip", SEVENZIP=None,
                        PATH=sysbin)
        self.assertEqual(rc, 0, o)
        self.assertIn("via=python", o)
        import zipfile
        self.assertEqual(zipfile.ZipFile(os.path.join(self.repo, "Saved/Zip/Team_Game.zip")).namelist(), ["README.txt"])


class McpBothAgents(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)
        shutil.copytree(os.path.join(ROOT, "pipeline", "agent-ops"), os.path.join(self.d, "pipeline", "agent-ops"))

    def gates(self, **kw):
        p = os.path.join(self.d, "pipeline", "agent-ops", "gates.json")
        with open(p) as fh:
            g = json.load(fh)
        g.update(kw)
        with open(p, "w") as fh:
            json.dump(g, fh)

    def test_templates_agree_and_broken_codex_template_fails(self):
        self.assertEqual(mcp_config.problems(self.d), [])
        p = os.path.join(self.d, "pipeline", "agent-ops", "codex-mcp.template.toml")
        text = open(p).read().replace('command = "gimp-mcp"', 'command = "other-gimp"')
        open(p, "w").write(text)
        self.assertTrue(any("gimp-mcp" in x for x in mcp_config.problems(self.d)))

    def test_off_until_kickoff_then_scoped_by_role(self):
        out = os.path.join(self.d, "mcp")
        self.assertEqual(mcp_config.session_args("codex", "asset-specialist", out, self.d), [])
        self.assertEqual(mcp_config.session_args("claude", "asset-specialist", out, self.d), [])
        self.gates(mcp_enabled=True)
        cx = mcp_config.session_args("codex", "asset-specialist", out, self.d)
        self.assertIn('mcp_servers.aseprite-mcp.command="aseprite-mcp"', cx)
        self.assertIn('mcp_servers.unreal-mcp.url="http://127.0.0.1:8000/mcp"', cx)
        self.assertEqual(mcp_config.session_args("codex", "gameplay-dev", out, self.d), [], "not an MCP role")
        cl = mcp_config.session_args("claude", "level-designer", out, self.d)
        self.assertEqual(cl[0], "--mcp-config")
        with open(cl[1]) as fh:
            self.assertEqual(sorted(json.load(fh)["mcpServers"]), ["unreal-mcp"], "level designer: editor only")

    def test_role_outside_mcp_roles_fails(self):
        p = os.path.join(self.d, "pipeline", "agent-ops", "asset-tools.json")
        inv = json.load(open(p))
        inv["mcp"][1]["roles"].append("gameplay-dev")
        json.dump(inv, open(p, "w"))
        self.assertTrue(any("gameplay-dev" in x for x in mcp_config.problems(self.d)))


if __name__ == "__main__":
    unittest.main()

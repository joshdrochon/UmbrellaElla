"""Image tiers and the OpenRouter provider in tools/assetgen.py: the tier picks the model, OpenRouter serves only the
mapped Google models, each provider's cap refuses at its limit, provider/tier/model land in provenance. Fake client
only, never the network."""
import json
import os
import sys
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import assetgen  # noqa: E402
import test_assetgen_image as img  # noqa: E402

DRAFT = "gemini-2.5-flash-image"
FINAL = "gemini-3-pro-image-preview"
OR_KEY = "sk-or-FAKE-0123456789"

OR_STUB = textwrap.dedent('''
    import base64, importlib.util, json, os
    spec = importlib.util.spec_from_file_location("base_stub", {base!r})
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)

    def post(url, headers, body):
        if "openrouter.ai" not in url:
            return base.post(url, headers, body)
        req = json.loads(body)
        with open(os.environ["HTTP_STUB_LOG"], "a") as fh:
            fh.write(json.dumps({{"url": url, "model": req["model"], "image_config": req.get("image_config"),
                                 "key_sent": {key!r} in json.dumps(headers), "inputs": 0}}) + "\\n")
        data = base64.b64encode(base._png()).decode()
        return json.dumps({{"model": req["model"], "usage": {{"cost": float(os.environ.get("STUB_OR_COST", "0.04"))}},
                           "choices": [{{"message": {{"images": [{{"image_url": {{"url": "data:image/png;base64," + data}}}}]}}}}]}}).encode()

    def get(url, headers):
        return base.get(url, headers)
''')


class Tiers(img.ImageWork):
    def setUp(self):
        super().setUp()
        base = self.stub
        self.stub = os.path.join(self.d, "or_stub.py")
        with open(self.stub, "w", encoding="utf-8") as fh:
            fh.write(OR_STUB.format(base=base, key=OR_KEY))

    def img_env(self, **extra):
        return super().img_env(**dict({"OPENROUTER_API_KEY": OR_KEY}, **extra))

    def stub_checks(self, passing):
        """Replace the temp repo's art_check / art_judge with stubs that pass or fail (no real measuring)."""
        t = os.path.join(self.repo, "tools")
        with open(os.path.join(t, "art_check.py"), "w") as fh:
            fh.write("def measure(p, st): return {}\ndef evaluate(m, st): return %s\n" % ("[]" if passing else "['too flat']"))
        with open(os.path.join(t, "art_judge.py"), "w") as fh:
            fh.write("def element(i, files, refs, roots, only): return None, [(files[0], %s, 'x')], []\n" % (
                "9.0" if passing else "0.0"))

    def plant_draft(self, passing):
        self.stub_checks(passing)
        return self.plant("Art/Source/Ella/draft.png")

    def last_call(self):
        return self.counter()["calls"][-1]

    def test_default_tier_is_draft_flash_and_final_is_pro(self):
        rc, o = self.paint("Art/Source/Ella/d.png")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.last_call()["model"], DRAFT)
        self.assertEqual(self.last_call()["tier"], "draft")
        draft = self.plant_draft(passing=True)
        rc, o = self.paint("Art/Source/Ella/f.png", "--tier", "final", "--image-size", "2K", "--from-draft", draft)
        self.assertEqual(rc, 0, o)
        self.assertEqual((self.last_call()["model"], self.last_call()["tier"]), (FINAL, "final"))
        self.assertIn(f"tier=final model={FINAL}", self.prov_row("Art/Source/Ella/f.png")["origin"])

    def test_gemini_provenance_names_provider_tier_and_model(self):
        self.assertEqual(self.paint("Art/Source/Ella/d.png")[0], 0)
        row = self.prov_row("Art/Source/Ella/d.png")
        self.assertIn(f"provider=gemini tier=draft model={DRAFT}", row["origin"])
        self.assertEqual(row["model_version"], DRAFT)

    def test_openrouter_serves_the_mapped_google_model_and_records_it(self):
        rc, o = self.paint("Art/Source/Ella/o.png", "--provider", "openrouter")
        self.assertEqual(rc, 0, o)
        call = self.http()[-1]
        self.assertEqual((call["model"], call["key_sent"]), ("google/" + DRAFT, True))
        row = self.prov_row("Art/Source/Ella/o.png")
        self.assertIn(f"provider=openrouter tier=draft model={DRAFT}", row["origin"])
        self.assertIn("OpenRouter", row["tool"])
        c = self.last_call()
        self.assertEqual((c["provider"], c["model"]), ("openrouter", DRAFT))
        self.assertAlmostEqual(c["cost_usd"], 0.04)
        self.assertNotIn(OR_KEY, open(os.path.join(self.repo, "pipeline/art/provenance.csv")).read())

    def test_non_matching_openrouter_model_is_rejected_with_no_call(self):
        for m in ("gemini-3.1-flash-image-preview", "gpt-image-1", "google/gemini-2.5-flash-image", "anthropic/claude"):
            rc, o = self.paint("Art/Source/Ella/x.png", "--provider", "openrouter", "--model", m, "--image-size", "1K")
            self.assertEqual(rc, 2, o)
            self.assertIn("OPENROUTER REFUSED", o)
        self.assertEqual(self.http(), [])
        self.assertEqual(self.counter()["calls"], [])
        with self.assertRaises(assetgen.ImageRefused):
            assetgen.openrouter_model("some-other-model")

    def test_openrouter_cap_refuses_at_its_limit_and_gemini_is_unaffected(self):
        env = dict(IMAGE_SPEND_OPENROUTER_CAP_USD="0.08", STUB_OR_COST="0.039")
        self.assertEqual(self.paint("Art/Source/Ella/1.png", "--provider", "openrouter", **env)[0], 0)
        self.assertEqual(self.paint("Art/Source/Ella/2.png", "--provider", "openrouter", **env)[0], 0)
        n = len(self.http())
        rc, o = self.paint("Art/Source/Ella/3.png", "--provider", "openrouter", **env)
        self.assertEqual(rc, 2, o)
        self.assertIn("OpenRouter image cap", o)
        self.assertEqual(len(self.http()), n, "the third call never reaches the provider")
        self.assertEqual(self.paint("Art/Source/Ella/g.png", **env)[0], 0, "gemini still has its own room")

    def test_gemini_cap_refuses_at_its_limit_and_openrouter_spend_does_not_count_against_it(self):
        env = dict(IMAGE_SPEND_CAP_USD="0.08", OPENROUTER_API_KEY="")   # no key: no automatic move to openrouter
        self.assertEqual(self.paint("Art/Source/Ella/o.png", "--provider", "openrouter", OPENROUTER_API_KEY=OR_KEY,
                                    IMAGE_SPEND_CAP_USD="0.08")[0], 0)
        self.assertEqual(self.paint("Art/Source/Ella/1.png", **env)[0], 0)
        self.assertEqual(self.paint("Art/Source/Ella/2.png", **env)[0], 0)
        rc, o = self.paint("Art/Source/Ella/3.png", **env)
        self.assertEqual(rc, 2, o)
        self.assertIn("CAP REACHED", o)

    def test_openrouter_used_only_when_gemini_is_near_its_cap(self):
        # 5 final calls at 2K = 0.67. Plenty left: stays on gemini.
        self.assertEqual(self.paint("Art/Source/Ella/a.png", IMAGE_SPEND_CAP_USD="5")[0], 0)
        self.assertEqual(self.last_call()["provider"], "gemini")
        # remaining 0.60 < 0.67: the same model moves to openrouter.
        self.assertEqual(self.paint("Art/Source/Ella/b.png", IMAGE_SPEND_CAP_USD="0.64")[0], 0)
        self.assertEqual(self.last_call()["provider"], "openrouter")
        # no openrouter key: stays on gemini.
        self.assertEqual(self.paint("Art/Source/Ella/c.png", IMAGE_SPEND_CAP_USD="0.64", OPENROUTER_API_KEY="")[0], 0)
        self.assertEqual(self.last_call()["provider"], "gemini")

    def test_a_model_openrouter_does_not_map_never_moves_to_it(self):
        rc, o = self.paint("Art/Source/Ella/n.png", "--model", "gemini-3.1-flash-image-preview", "--image-size", "1K",
                           IMAGE_SPEND_CAP_USD="0.64")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.last_call()["provider"], "gemini")


class SpendGuards(Tiers):
    """Josh's image-spend guards (Nov 13): piece named, in-game context shot, draft first, per-piece cap."""

    def calls(self):
        return len(self.http())

    def test_a_paid_call_must_name_its_piece(self):
        rc, o = self.ag("image", "--prompt", "p", "--out", "Art/Source/Ella/a.png", **self.img_env())
        self.assertEqual(rc, 2, o)
        self.assertIn("PIECE REQUIRED", o)
        self.assertEqual(self.calls(), 0)

    def test_in_game_piece_refused_until_main_has_the_smoke_shot_but_ui_screen_paints(self):
        rc, o = self.paint("Art/Source/Ella/a.png", "--piece", "ella-up-open")
        self.assertEqual(rc, 2, o)
        self.assertIn("NO CONTEXT SHOT", o)
        self.assertEqual(self.calls(), 0)
        rc, o = self.paint("Art/Source/Ella/b.png", "--piece", "ui-title")
        self.assertEqual(rc, 0, o)

    def test_final_needs_a_draft_that_passed_its_checks(self):
        rc, o = self.paint("Art/Source/Ella/f.png", "--tier", "final", "--image-size", "2K")
        self.assertEqual(rc, 2, o)
        self.assertIn("DRAFT FIRST", o)
        draft = self.plant_draft(passing=False)
        rc, o = self.paint("Art/Source/Ella/f.png", "--tier", "final", "--image-size", "2K", "--from-draft", draft)
        self.assertEqual(rc, 2, o)
        self.assertIn("DRAFT NOT PASSED", o)
        self.assertEqual(self.calls(), 0)
        draft = self.plant_draft(passing=True)
        rc, o = self.paint("Art/Source/Ella/f.png", "--tier", "final", "--image-size", "2K", "--from-draft", draft)
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.last_call()["piece"], "ui-title")

    def test_per_piece_cap_refuses_and_logs(self):
        env = dict(IMAGE_SPEND_CAP_USD="50")
        # 0.039 per draft: 12 calls = 0.468; the 13th would pass 0.50
        for i in range(12):
            self.assertEqual(self.paint(f"Art/Source/Ella/{i}.png", **env)[0], 0)
        n = self.calls()
        rc, o = self.paint("Art/Source/Ella/x.png", **env)
        self.assertEqual(rc, 2, o)
        self.assertIn("triage art vs check before more spend", o)
        self.assertEqual(self.calls(), n)
        log = os.path.join(os.path.dirname(self.repo), "logs", "spend-cap.log")
        self.assertIn("triage art vs check before more spend", open(log).read())
        # another piece is unaffected
        self.assertEqual(self.paint("Art/Source/Ella/y.png", "--piece", "ui-pause", **env)[0], 0)


if __name__ == "__main__":
    unittest.main()
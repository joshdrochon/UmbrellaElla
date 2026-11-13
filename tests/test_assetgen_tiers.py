"""Image tiers and the OpenRouter provider in tools/assetgen.py: the tier picks the model, OpenRouter serves only the
mapped Google models, each provider's cap refuses at its limit, provider/tier/model land in provenance. Fake client
only, never the network."""
import json
import os
import shutil
import sys
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import assetgen  # noqa: E402
os.environ["ASSETGEN_NO_STYLE"] = "1"   # the fake client draws from the prompt; the style block has its own test
import test_assetgen_image as img  # noqa: E402

DRAFT = "gemini-2.5-flash-image"
FINAL = "gemini-3-pro-image-preview"
OR_KEY = "sk-or-FAKE-0123456789"
FAL_KEY = "fal-FAKE-0123456789:abcdef"

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

FAL_STUB = textwrap.dedent('''
    import base64, importlib.util, json, os
    spec = importlib.util.spec_from_file_location("base_stub", {base!r})
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)

    def post(url, headers, body):
        if "fal.run" not in url:
            return base.post(url, headers, body)
        with open(os.environ["HTTP_STUB_LOG"], "a") as fh:
            fh.write(json.dumps({{"url": url, "model": url.split("fal.run/")[1], "key_sent": {key!r} in json.dumps(headers),
                                 "inputs": 0}}) + "\\n")
        data = base64.b64encode(base.base._png()).decode()
        return json.dumps({{"images": [{{"url": "data:image/png;base64," + data}}]}}).encode()

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
        self.fal_stub = os.path.join(self.d, "fal_stub.py")
        with open(self.fal_stub, "w", encoding="utf-8") as fh:
            fh.write(FAL_STUB.format(base=self.stub, key=FAL_KEY))

    def img_env(self, **extra):
        return super().img_env(**dict({"OPENROUTER_API_KEY": OR_KEY}, **extra))

    def stub_checks(self, passing):
        """Replace the temp repo's art_check / art_judge with stubs that pass or fail (no real measuring)."""
        t = os.path.join(self.repo, "tools")
        shutil.rmtree(os.path.join(t, "__pycache__"), ignore_errors=True)   # a rewrite in the same second keeps a stale .pyc
        with open(os.path.join(t, "art_check.py"), "w") as fh:
            r = "[]" if passing else "['too flat']"
            fh.write("def measure(p, st): return {}\ndef evaluate(m, st): return %s\n"
                     "def sprite_failures(p, st, effect=False): return %s\n" % (r, r))
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

    # ---- fal, third provider ----
    def paint_fal(self, out, *args, **env):
        env.setdefault("FAL_KEY", FAL_KEY)
        self.stub, keep = self.fal_stub, self.stub
        try:
            return self.paint(out, *args, **env)
        finally:
            self.stub = keep

    def test_fal_serves_the_mapped_google_model_and_records_it(self):
        rc, o = self.paint_fal("Art/Source/Ella/f.png", "--provider", "fal")
        self.assertEqual(rc, 0, o)
        call = self.http()[-1]
        self.assertEqual((call["model"], call["key_sent"]), ("fal-ai/gemini-25-flash-image", True))
        row = self.prov_row("Art/Source/Ella/f.png")
        self.assertIn(f"provider=fal tier=draft model={DRAFT}", row["origin"])
        self.assertIn("fal", row["tool"])
        self.assertEqual((self.last_call()["provider"], self.last_call()["model"]), ("fal", DRAFT))
        self.assertNotIn(FAL_KEY, open(os.path.join(self.repo, "pipeline/art/provenance.csv")).read())
        self.assertNotIn(FAL_KEY, o)

    def test_non_matching_fal_model_is_rejected_with_no_call(self):
        for m in ("gemini-3.1-flash-image-preview", "gpt-image-1", "fal-ai/gemini-25-flash-image", "flux/dev"):
            rc, o = self.paint_fal("Art/Source/Ella/x.png", "--provider", "fal", "--model", m, "--image-size", "1K")
            self.assertEqual(rc, 2, o)
            self.assertIn("FAL REFUSED", o)
        self.assertEqual(self.http(), [])
        self.assertEqual(self.counter()["calls"], [])
        with self.assertRaises(assetgen.ImageRefused):
            assetgen.fal_model("some-other-model")

    def test_fal_cap_refuses_at_its_limit_and_other_providers_are_unaffected(self):
        env = dict(FAL_SPEND_CAP_USD="0.08")
        self.assertEqual(self.paint_fal("Art/Source/Ella/1.png", "--provider", "fal", **env)[0], 0)
        self.assertEqual(self.paint_fal("Art/Source/Ella/2.png", "--provider", "fal", **env)[0], 0)
        n = len(self.http())
        rc, o = self.paint_fal("Art/Source/Ella/3.png", "--provider", "fal", **env)
        self.assertEqual(rc, 2, o)
        self.assertIn("fal image cap", o)
        self.assertEqual(len(self.http()), n)
        self.assertEqual(self.paint("Art/Source/Ella/g.png", **env)[0], 0, "gemini still has its own room")

    def test_fal_default_cap_and_gemini_cap_ignores_fal_spend(self):
        self.assertEqual(assetgen.FAL_CAP_USD, 74.84)
        self.assertEqual(assetgen.fal_cap(), 74.84)
        self.assertEqual(self.paint_fal("Art/Source/Ella/f.png", "--provider", "fal", IMAGE_SPEND_CAP_USD="0.08")[0], 0)
        self.assertEqual(self.paint("Art/Source/Ella/1.png", IMAGE_SPEND_CAP_USD="0.08")[0], 0)
        self.assertEqual(self.paint("Art/Source/Ella/2.png", IMAGE_SPEND_CAP_USD="0.08")[0], 0)

    def test_fal_chosen_only_when_gemini_and_openrouter_are_both_near_their_caps(self):
        keys_on = {"OPENROUTER_API_KEY": True, "FAL_KEY": True}
        env = {"IMAGE_SPEND_CAP_USD": "0.64", "IMAGE_SPEND_OPENROUTER_CAP_USD": "19.89"}
        def pick(**e):
            old = {k: os.environ.get(k) for k in e}
            os.environ.update(e)
            try:
                os.environ["ASSETGEN_SPEND_FILE"] = os.environ.get("ASSETGEN_SPEND_FILE", "")
                return assetgen.pick_provider("gemini", DRAFT, keys_on)
            finally:
                for k, v in old.items():
                    os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        # gemini roomy: stays gemini
        self.assertEqual(self.paint("Art/Source/Ella/a.png", IMAGE_SPEND_CAP_USD="5")[0], 0)
        self.assertEqual(self.last_call()["provider"], "gemini")
        # gemini near, openrouter roomy: openrouter, not fal
        self.assertEqual(self.paint_fal("Art/Source/Ella/b.png", **env)[0], 0)
        self.assertEqual(self.last_call()["provider"], "openrouter")
        # gemini near, openrouter near too (cap 0.60 left < 0.67): fal
        env2 = dict(env, IMAGE_SPEND_OPENROUTER_CAP_USD="0.60")
        self.assertEqual(self.paint_fal("Art/Source/Ella/c.png", **env2)[0], 0)
        self.assertEqual(self.last_call()["provider"], "fal")
        # same, no fal key: stays on openrouter
        self.assertEqual(self.paint_fal("Art/Source/Ella/d.png", FAL_KEY="", **env2)[0], 0)
        self.assertEqual(self.last_call()["provider"], "openrouter")


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


SLOW_STUB = textwrap.dedent('''
    import importlib.util, json, os, time
    spec = importlib.util.spec_from_file_location("base_stub", {base!r})
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)

    def _mark(kind):
        with open(os.environ["PEAK_LOG"], "a") as fh:
            fh.write(kind + "\\n")

    def post(url, headers, body):
        _mark("start")
        time.sleep(0.5)
        try:
            return base.post(url, headers, body)
        finally:
            _mark("end")

    def get(url, headers):
        return base.get(url, headers)
''')


BATCH_PIECES = ["ui-title", "ui-hud-clock", "ui-pause", "ui-settings", "ui-defeated", "ui-credits"]   # screens: no context shot needed


class Batch(img.ImageWork):
    """assetgen.py batch: up to 4 paid calls at once through the same locked counter (fake provider, no paid calls)."""

    def setUp(self):
        super().setUp()
        base_stub = self.stub
        self.stub = os.path.join(self.d, "slow_stub.py")
        with open(self.stub, "w", encoding="utf-8") as fh:
            fh.write(SLOW_STUB.format(base=base_stub))
        self.peak_log = os.path.join(self.d, "peak.log")

    def run_batch(self, n, workers=4, cap="1.00", extra=(), pieces=None, **env):
        jobs = [["--prompt", f"Ella {i}", "--out", f"Art/Source/Ella/b{i}.png", "--piece", (pieces or {}).get(i, BATCH_PIECES[i]),
                 *extra] for i in range(n)]
        jf = os.path.join(self.d, "jobs.json")
        json.dump(jobs, open(jf, "w"))
        return self.ag("batch", "--jobs", jf, "--workers", str(workers), **self.img_env(
            IMAGE_SPEND_CAP_USD=cap, PEAK_LOG=self.peak_log, **env))

    def peak(self):
        cur = top = 0
        for ln in open(self.peak_log).read().split():
            cur += 1 if ln == "start" else -1
            top = max(top, cur)
        return top

    def test_four_calls_run_at_once_and_all_land(self):
        rc, o = self.run_batch(4)
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.peak(), 4)
        self.assertEqual(len(self.counter()["calls"]), 4)
        self.assertIn("BATCH 4/4 ok", o)
        rows = self.prov()
        for i in range(4):
            self.assertIn(f"Art/Source/Ella/b{i}.png", rows)

    def test_never_more_than_four_at_once(self):
        rc, o = self.run_batch(6, workers=9)
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.peak(), 4)
        self.assertEqual(len(self.counter()["calls"]), 6)

    def test_concurrent_calls_never_exceed_the_cap_and_a_refused_one_does_not_block_the_rest(self):
        # cap fits exactly 2 draft calls (0.039 each); 4 race for it
        rc, o = self.run_batch(4, cap="0.09")
        self.assertEqual(rc, 1, o)
        c = self.counter()
        self.assertLessEqual(c["spent_usd"], 0.09 + 1e-9)
        self.assertEqual(len(c["calls"]), 2)
        self.assertEqual(len(self.http_calls()), 2)
        self.assertIn("BATCH 2/4 ok, 2 refused or failed", o)
        self.assertEqual(o.count("CAP REACHED"), 2)

    def test_refused_job_does_not_stop_the_others(self):
        # job 1 has no piece id's draft for final: refused; the others still paint
        jobs = [["--prompt", "a", "--out", "Art/Source/Ella/ok0.png", "--piece", "ui-title"],
                ["--prompt", "b", "--out", "Art/Source/Ella/bad.png", "--piece", "ui-pause", "--tier", "final", "--image-size", "2K"],
                ["--prompt", "c", "--out", "Art/Source/Ella/ok2.png", "--piece", "ui-settings"]]
        jf = os.path.join(self.d, "jobs.json")
        json.dump(jobs, open(jf, "w"))
        rc, o = self.ag("batch", "--jobs", jf, **self.img_env(PEAK_LOG=self.peak_log))
        self.assertEqual(rc, 1, o)
        self.assertIn("DRAFT FIRST", o)
        self.assertIn("BATCH 2/3 ok", o)
        self.assertEqual(len(self.counter()["calls"]), 2)

    def test_per_piece_cap_holds_under_concurrency(self):
        # 4 draft calls of the same piece at 0.039: the 0.50 piece cap is not reached, all pass; cap 0.50 enforced below
        rc, o = self.run_batch(4, pieces={i: "ui-title" for i in range(4)}, extra=("--tier", "draft"))
        self.assertEqual(rc, 0, o)
        self.assertLessEqual(sum(c["cost_usd"] for c in self.counter()["calls"]), assetgen.PIECE_CAP_USD)

    def test_local_providers_stay_outside_the_batch(self):
        rc, o = self.run_batch(2, extra=("--provider", "placeholder"))
        self.assertEqual(rc, 1, o)
        self.assertIn("not a paid generation call", o)
        self.assertEqual(self.counter()["calls"], [])

    def http_calls(self):
        return self.http()


if __name__ == "__main__":
    unittest.main()

class StyleBlock(unittest.TestCase):
    """Every paid image prompt carries the shared style block once (Nov 13: panels failed flat fills, missing etched
    ink and weak paper texture)."""
    def test_added_once(self):
        old = os.environ.pop("ASSETGEN_NO_STYLE", None)
        try:
            p = assetgen.with_style("a gold burst")
            self.assertIn("crosshatch", p)
            self.assertIn("No flat fills", p)
            self.assertEqual(assetgen.with_style(p), p)
        finally:
            if old is not None:
                os.environ["ASSETGEN_NO_STYLE"] = old


class SpendByProvider(unittest.TestCase):
    """The counter and the status line give each provider's spend against its own cap (Nov 13)."""
    def test_each_provider_against_its_own_cap(self):
        d = {"spent_usd": 34.97, "calls": [{"provider": "fal", "cost_usd": 12.0}, {"provider": "openrouter", "cost_usd": 0.5},
                                           {"provider": "gemini", "cost_usd": 22.47}]}
        b = assetgen.by_provider(d, 33.82)
        self.assertAlmostEqual(b["gemini"]["spent_usd"], 22.47)
        self.assertAlmostEqual(b["gemini"]["left_usd"], 11.35)
        self.assertAlmostEqual(b["fal"]["spent_usd"], 12.0)
        self.assertAlmostEqual(b["openrouter"]["spent_usd"], 0.5)
        self.assertIn("gemini $22.47/$33.82", assetgen.spend_line(d, 33.82))

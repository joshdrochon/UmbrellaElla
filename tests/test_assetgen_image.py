"""Image model provider in tools/assetgen.py image (D-new-art-image-model): gemini (default) and openai through a fake
client (ASSETGEN_HTTP_STUB), never the network. Provenance row, prompt log, the GDD ART-03 / BG-02 pre-jam input guard,
the shared spend counter and its hard cap, and the no-key result. Each check has a passing case and one broken on
purpose."""
import base64
import csv
import json
import os
import shutil
import subprocess
import sys
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import test_assetgen as base  # noqa: E402

PY = sys.executable
FAKE_KEY = "fake-image-key-0000"
GEMINI_PRICE = 0.039   # asset-tools.json gemini-image price_usd_per_image gemini-2.5-flash-image
INPUT_PRICE = 0.001

STUB = textwrap.dedent('''
    """Fake image client: answers the Gemini and OpenAI image endpoints with a small PNG; logs one JSON line per call
    (url, whether the key header was sent, the number of input images). STUB_FAIL=<code> answers that HTTP error."""
    import base64, io, json, os, sys, urllib.error
    sys.path.insert(0, {tools!r})
    import png

    def _png():
        path = os.environ["STUB_PNG"]
        if not os.path.exists(path):
            rows = [[(0, 255, 0, 255) if (x < 4 or y < 4 or x > 59 or y > 59) else (40, 30, 50, 255)
                     for x in range(64)] for y in range(64)]
            png.write_png(path, 64, 64, rows)
        return open(path, "rb").read()

    def post(url, headers, body):
        key_sent = {key!r} in json.dumps(headers)
        inputs = 0
        if "generativelanguage" in url:
            parts = json.loads(body)["contents"][0]["parts"]
            inputs = sum(1 for p in parts if "inline_data" in p)
        elif "images/edits" in url:
            inputs = body.count(b'name="image[]"')
        with open(os.environ["HTTP_STUB_LOG"], "a") as fh:
            fh.write(json.dumps({{"url": url, "key_sent": key_sent, "inputs": inputs}}) + "\\n")
        code = os.environ.get("STUB_FAIL")
        if code:
            raise urllib.error.HTTPError(url, int(code), "err", {{}}, io.BytesIO(b'{{"error":{{"message":"bad"}}}}'))
        data = base64.b64encode(_png()).decode()
        if "generativelanguage" in url:
            return json.dumps({{"modelVersion": "gemini-2.5-flash-image", "usageMetadata": {{"candidatesTokenCount": 1290}},
                               "candidates": [{{"finishReason": "STOP", "content": {{"parts": [
                                   {{"inlineData": {{"mimeType": "image/png", "data": data}}}}]}}}}]}}).encode()
        if "api.openai.com" in url:
            return json.dumps({{"data": [{{"b64_json": data}}]}}).encode()
        raise OSError("no stub for " + url)
''')


class ImageWork(base.Work):
    def setUp(self):
        super().setUp()
        self.stub = os.path.join(self.d, "image_stub.py")
        with open(self.stub, "w", encoding="utf-8") as fh:
            fh.write(STUB.format(tools=os.path.join(ROOT, "tools"), key=FAKE_KEY))
        self.spend = os.path.join(self.d, "shared", "image-spend.json")
        refs = os.path.join(self.repo, "pipeline", "art", "references.json")
        if not os.path.exists(refs):
            shutil.copy(os.path.join(ROOT, "pipeline", "art", "references.json"), refs)

    def img_env(self, **extra):
        e = dict(GEMINI_API_KEY=FAKE_KEY, IMAGE_SPEND_FILE=self.spend, IMAGE_SPEND_CAP_USD="1.00",
                 ASSETGEN_HTTP_STUB=self.stub, STUB_PNG=os.path.join(self.d, "stub.png"), JAM_ROLE="asset-specialist")
        e.update(extra)
        return e

    def paint(self, out, *more, **extra):
        return self.ag("image", "--prompt", "Ella rising, umbrella open overhead", "--out", out, *more,
                       **self.img_env(**extra))

    def http(self):
        if not os.path.exists(self.http_log):
            return []
        return [json.loads(ln) for ln in open(self.http_log) if ln.strip()]

    def counter(self):
        return json.load(open(self.spend)) if os.path.exists(self.spend) else {"spent_usd": 0.0, "calls": []}

    def prov_row(self, path):
        return self.prov().get(path)

    def plant(self, rel, png_from=None, row=None):
        """A PNG at rel (bytes of png_from, else the stub's image), with an optional provenance row."""
        full = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if png_from:
            shutil.copy(png_from, full)
        else:
            import png
            png.write_png(full, 8, 8, [[(10, 20, 30, 255)] * 8 for _ in range(8)])
        if row:
            path = os.path.join(self.repo, "pipeline", "art", "provenance.csv")
            rows = []
            if os.path.exists(path):
                rows = list(csv.DictReader(open(path, encoding="utf-8", newline="")))
            rows.append(dict({"asset_path": rel}, **row))
            with open(path, "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, ["asset_path", "author", "origin", "tool", "model_version",
                                    "prompt", "seed", "input_images", "date", "licence", "attribution"],
                                   lineterminator="\n")
                w.writeheader()
                for r in rows:
                    w.writerow({k: r.get(k, "") for k in w.fieldnames})
        return full


class GeminiCall(ImageWork):
    def test_gemini_is_the_default_and_writes_the_full_provenance_row_and_prompt_log(self):
        rc, o = self.paint("Art/Source/Ella/ella_up_open.png", "--seed", "7")
        self.assertEqual(rc, 0, o)
        self.assertIn("via=gemini", o)
        self.assertNotIn(FAKE_KEY, o, "the key is never printed")
        calls = self.http()
        self.assertEqual(len(calls), 1)
        self.assertIn("gemini-2.5-flash-image:generateContent", calls[0]["url"])
        self.assertTrue(calls[0]["key_sent"])
        row = self.prov_row("Art/Source/Ella/ella_up_open.png")
        inv = json.load(open(os.path.join(ROOT, "pipeline", "agent-ops", "asset-tools.json")))
        t = [x for x in inv["tools"] if x["id"] == "gemini-image"][0]
        self.assertEqual(row["tool"], t["name"])
        self.assertEqual(row["model_version"], "gemini-2.5-flash-image")
        self.assertIn("Ella rising", row["prompt"])
        self.assertEqual(row["seed"], "7")
        self.assertEqual(row["input_images"], "")
        self.assertRegex(row["date"], r"^20\d\d-\d\d-\d\dT\d\d:\d\d\+00:00$")
        self.assertEqual(row["licence"], t["licence"])
        self.assertTrue(row["origin"].startswith("generated in jam"))
        self.assertTrue(row["author"].startswith("asset-specialist"))
        self.assertNotIn(FAKE_KEY, open(os.path.join(self.repo, "pipeline", "art", "provenance.csv")).read())
        req = json.load(open(os.path.join(self.repo, "Art/Source/Ella/ella_up_open.request.json")))
        self.assertEqual((req["prompt"], req["cost_usd"]), ("Ella rising, umbrella open overhead", GEMINI_PRICE))
        logs = os.path.join(self.repo, "Saved", "agent-log")
        lines = [json.loads(ln) for f in os.listdir(logs) for ln in open(os.path.join(logs, f)) if ln.strip()]
        self.assertEqual([(r["event"], r["kind"], r["out"]) for r in lines],
                         [("prompt", "image", "Art/Source/Ella/ella_up_open.png")])
        rc, o = self.tool("tools/prompt_log.py", "export", "--log", logs)
        self.assertEqual(rc, 0, o)
        self.assertIn("Ella rising, umbrella open overhead", o, "prompt_log export carries the image prompt")
        c = self.counter()
        self.assertAlmostEqual(c["spent_usd"], GEMINI_PRICE)
        self.assertEqual([x["status"] for x in c["calls"]], ["done"])

    def test_no_key_is_a_clear_no_key_result_and_no_placeholder(self):
        rc, o = self.paint("Art/Source/Ella/nokey.png", GEMINI_API_KEY=None, KEYS_NO_KEYCHAIN="1")
        self.assertEqual(rc, 2, o)
        self.assertIn("NO KEY: GEMINI_API_KEY", o)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "Art/Source/Ella/nokey.png")),
                         "no placeholder pretends to be art")
        self.assertNotIn("Art/Source/Ella/nokey.png", self.prov(), "no provenance row for an image never made")
        self.assertEqual(self.http(), [])
        self.assertEqual(self.counter()["spent_usd"], 0.0)

    def test_provider_rejects_the_request_refunded_and_no_image(self):
        rc, o = self.paint("Art/Source/Ella/bad.png", STUB_FAIL="400")
        self.assertEqual(rc, 1, o)
        self.assertIn("HTTP 400", o)
        self.assertIn("refunded", o)
        self.assertEqual(self.counter()["spent_usd"], 0.0)
        self.assertEqual(self.counter()["calls"][0]["status"], "failed")
        self.assertFalse(os.path.exists(os.path.join(self.repo, "Art/Source/Ella/bad.png")))

    def test_server_error_keeps_its_cost(self):
        rc, o = self.paint("Art/Source/Ella/bad.png", STUB_FAIL="503")
        self.assertEqual(rc, 1, o)
        self.assertAlmostEqual(self.counter()["spent_usd"], GEMINI_PRICE, msg="it may be billed: counted")

    def test_unpriced_model_is_refused_before_any_call(self):
        rc, o = self.paint("Art/Source/Ella/x.png", "--model", "some-unpriced-model")
        self.assertEqual(rc, 2, o)
        self.assertIn("no published price", o)
        self.assertEqual(self.http(), [])


class OpenAICall(ImageWork):
    def test_openai_generation_and_edit_with_an_in_jam_input(self):
        rc, o = self.paint("Art/Source/Ella/a.png", "--provider", "openai", "--quality", "low",
                           GEMINI_API_KEY=None, OPENAI_API_KEY=FAKE_KEY)
        self.assertEqual(rc, 0, o)
        row = self.prov_row("Art/Source/Ella/a.png")
        self.assertEqual(row["seed"], "none (no seed parameter)")
        self.assertIn("OpenAI", row["tool"])
        self.assertAlmostEqual(self.counter()["spent_usd"], 0.011)
        rc, o = self.paint("Art/Source/Ella/b.png", "--provider", "openai", "--quality", "low",
                           "--input", "Art/Source/Ella/a.png", GEMINI_API_KEY=None, OPENAI_API_KEY=FAKE_KEY)
        self.assertEqual(rc, 0, o)
        calls = self.http()
        self.assertEqual([c["url"].rsplit("/", 1)[-1] for c in calls], ["generations", "edits"])
        self.assertEqual(calls[1]["inputs"], 1)
        self.assertAlmostEqual(self.counter()["spent_usd"], 0.011 + 0.011 + 0.01)


class PrejamGuard(ImageWork):
    def refused(self, inp, why):
        before = self.counter()["spent_usd"]
        rc, o = self.paint("Art/Source/Ella/next.png", "--input", inp)
        self.assertEqual(rc, 2, o)
        self.assertIn("PRE-JAM INPUT REFUSED", o)
        self.assertIn(why, o)
        self.assertEqual(self.http(), [], "no call made")
        self.assertEqual(self.counter()["spent_usd"], before, "nothing counted")
        self.assertFalse(os.path.exists(os.path.join(self.repo, "Art/Source/Ella/next.png")))

    def test_reference_folder_image_refused(self):
        self.plant("pipeline/art/reference/Rehearsal/Ella/Ella-Rising-02.png")
        self.refused("pipeline/art/reference/Rehearsal/Ella/Ella-Rising-02.png", "pre-jam team art")

    def test_quality_bar_and_team_studies_refused(self):
        self.plant("pipeline/art/reference/discord/20261111-0319_Ricky_roadwarden-sundial-casters.png")
        self.refused("pipeline/art/reference/discord/20261111-0319_Ricky_roadwarden-sundial-casters.png",
                     "pre-jam team art")
        self.plant("Assets/Art/Ella-Rising-Pose-Study-01.png")
        self.refused("Assets/Art/Ella-Rising-Pose-Study-01.png", "pre-jam team art")

    def test_copy_of_a_reference_refused_by_its_bytes(self):
        ref = self.plant("pipeline/art/reference/target-keyart.png")
        self.plant("Art/Source/Ella/copied.png", png_from=ref,
                   row={"origin": "generated in jam", "date": "2026-11-12T20:00+00:00"})
        self.refused("Art/Source/Ella/copied.png", "same bytes as the pre-jam image pipeline/art/reference/target-keyart.png")

    def test_no_provenance_or_a_date_before_the_jam_refused(self):
        self.plant("Art/Source/Ella/stray.png")
        self.refused("Art/Source/Ella/stray.png", "no provenance row")
        self.plant("Art/Source/Ella/old.png", row={"origin": "generated in jam", "date": "2026-11-10T12:00+00:00"})
        self.refused("Art/Source/Ella/old.png", "before the jam start")

    def test_placeholder_is_not_an_input(self):
        self.plant("Art/Source/Ella/ph.png", row={"origin": "placeholder made in jam; x", "date": "2026-11-12T20:00+00:00"})
        self.refused("Art/Source/Ella/ph.png", "placeholder")

    def test_our_in_jam_image_accepted_as_input(self):
        rc, o = self.paint("Art/Source/Ella/first.png")
        self.assertEqual(rc, 0, o)
        rc, o = self.paint("Art/Source/Ella/second.png", "--input", "Art/Source/Ella/first.png")
        self.assertEqual(rc, 0, o)
        self.assertEqual(self.http()[1]["inputs"], 1)
        self.assertEqual(self.prov_row("Art/Source/Ella/second.png")["input_images"], "Art/Source/Ella/first.png")
        self.assertAlmostEqual(self.counter()["spent_usd"], 2 * GEMINI_PRICE + INPUT_PRICE)


class SpendCap(ImageWork):
    def test_cap_stops_further_calls(self):
        cap = dict(IMAGE_SPEND_CAP_USD="0.08")
        self.assertEqual(self.paint("Art/Source/Ella/1.png", **cap)[0], 0)
        self.assertEqual(self.paint("Art/Source/Ella/2.png", **cap)[0], 0)
        rc, o = self.paint("Art/Source/Ella/3.png", **cap)
        self.assertEqual(rc, 2, o)
        self.assertIn("CAP REACHED", o)
        self.assertEqual(len(self.http()), 2, "the third call never reaches the provider")
        self.assertAlmostEqual(self.counter()["spent_usd"], 2 * GEMINI_PRICE)

    def test_no_cap_or_no_counter_means_no_paid_call(self):
        rc, o = self.paint("Art/Source/Ella/1.png", IMAGE_SPEND_CAP_USD=None)
        self.assertEqual(rc, 2, o)
        self.assertIn("NO CAP", o)
        rc, o = self.paint("Art/Source/Ella/1.png", IMAGE_SPEND_FILE=None)
        self.assertEqual(rc, 2, o)
        self.assertIn("NO COUNTER", o)
        self.assertEqual(self.http(), [])

    def test_one_counter_shared_by_parallel_workers_never_passes_the_cap(self):
        """Eight workers at once against a cap that fits three calls: exactly three run (the lock holds)."""
        env = self.env(**self.img_env(IMAGE_SPEND_CAP_USD=str(3 * GEMINI_PRICE + 0.001)))
        procs = [subprocess.Popen([PY, "tools/assetgen.py", "image", "--prompt", "p", "--out", f"Art/Source/P/{i}.png"],
                                  cwd=self.repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                 for i in range(8)]
        outs = [(p.wait(), p.stdout.read()) for p in procs]
        self.assertEqual(sorted(rc for rc, _ in outs), [0, 0, 0, 2, 2, 2, 2, 2], outs)
        self.assertEqual(len(self.http()), 3)
        c = self.counter()
        self.assertAlmostEqual(c["spent_usd"], 3 * GEMINI_PRICE)
        self.assertEqual(len(c["calls"]), 3)


if __name__ == "__main__":
    unittest.main()

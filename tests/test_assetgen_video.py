"""assetgen video mode (artvideo): image-to-video on fal, the fixed Veo model only, live price, in-jam input, the shared
counter with its own 1 USD per-piece cap, provenance (model, prompt, input, seed, cost). Fake client, never the network."""
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

FAL_KEY = "fal-FAKE-0123456789"
MODEL = "fal-ai/veo3.1/fast/image-to-video"
JAM_ROW = {"author": "team", "origin": "generated in jam", "tool": "x", "model_version": "x", "prompt": "x", "seed": "1",
           "input_images": "", "date": "2026-11-13T01:00+00:00", "licence": "team", "attribution": "none"}

VSTUB = textwrap.dedent('''
    import json, os
    def _log(d):
        with open(os.environ["HTTP_STUB_LOG"], "a") as fh:
            fh.write(json.dumps(d) + "\\n")
    def post(url, headers, body):
        req = json.loads(body)
        _log({{"url": url, "key_sent": {key!r} in json.dumps(headers), "audio": req.get("generate_audio"),
              "prompt": req["prompt"], "seed": req.get("seed"), "data_uri": req["image_url"].startswith("data:image/png")}})
        return json.dumps({{"request_id": "r1", "status_url": "https://queue.fal.run/s", "response_url": "https://queue.fal.run/r"}}).encode()
    def get(url, headers):
        if "models/pricing" in url:
            return json.dumps({{"prices": [{{"unit_price": float(os.environ.get("STUB_PRICE", "0.15"))}}]}}).encode()
        if "/v1/models" in url:
            return json.dumps({{"models": [{{"metadata": {{"status": os.environ.get("STUB_STATUS", "active")}}}}]}}).encode()
        if url.endswith("/s"):
            return b'{{"status": "COMPLETED"}}'
        if url.endswith("/r"):
            return b'{{"video": {{"url": "https://v3.fal.media/x.mp4", "content_type": "video/mp4"}}}}'
        return b"FAKEMP4"
''')


class Video(img.ImageWork):
    def setUp(self):
        super().setUp()
        with open(self.stub, "w", encoding="utf-8") as fh:
            fh.write(VSTUB.format(key=FAL_KEY))
        self.plant("pipeline/art/proof/in.png", row=JAM_ROW)

    def vid(self, *more, **extra):
        env = self.img_env(FAL_KEY=FAL_KEY, IMAGE_SPEND_CAP_USD="5.00")
        env.update(extra)
        args = ["video", "--prompt", "Ella floats, the umbrella sways", "--input", "pipeline/art/proof/in.png",
                "--out", "pipeline/art/proof/out.mp4"]
        if "--piece" not in more:
            args += ["--piece", "ella-idle-video"]
        return self.ag(*args, *more, **env)

    def test_call_writes_mp4_provenance_and_counter(self):
        rc, o = self.vid("--seed", "11")
        self.assertEqual(rc, 0, o)
        self.assertNotIn(FAL_KEY, o)
        self.assertEqual(open(os.path.join(self.repo, "pipeline/art/proof/out.mp4"), "rb").read(), b"FAKEMP4")
        post = [c for c in self.http() if "audio" in c][0]
        self.assertFalse(post["audio"])
        self.assertTrue(post["key_sent"] and post["data_uri"])
        self.assertIn("chroma green", post["prompt"])
        self.assertIn(MODEL, post["url"])
        row = self.prov_row("pipeline/art/proof/out.mp4")
        self.assertEqual((row["model_version"], row["seed"], row["input_images"]), (MODEL, "11", "pipeline/art/proof/in.png"))
        self.assertIn("Ella floats", row["prompt"])
        self.assertIn("$0.600", row["origin"])
        c = self.counter()
        self.assertAlmostEqual(c["spent_usd"], 0.60)
        self.assertEqual(c["calls"][0]["piece"], "ella-idle-video")

    def test_other_model_refused(self):
        rc, o = self.vid("--model", "fal-ai/veo3.1/image-to-video")
        self.assertEqual(rc, 2, o)
        self.assertIn("VIDEO MODEL REFUSED", o)
        self.assertEqual(self.http(), [])

    def test_deprecated_endpoint_refused_no_spend(self):
        rc, o = self.vid(STUB_STATUS="deprecated")
        self.assertEqual(rc, 2, o)
        self.assertIn("NOT ACTIVE", o)
        self.assertEqual(self.counter()["spent_usd"], 0.0)

    def test_prejam_input_refused(self):
        self.plant("pipeline/art/proof/old.png", row=dict(JAM_ROW, date="2026-01-01T00:00+00:00"))
        rc, o = self.ag("video", "--prompt", "p", "--input", "pipeline/art/proof/old.png", "--out", "pipeline/art/proof/o.mp4",
                        "--piece", "p", **self.img_env(FAL_KEY=FAL_KEY))
        self.assertEqual(rc, 2, o)
        self.assertIn("PRE-JAM INPUT REFUSED", o)

    def test_no_key_and_no_piece(self):
        rc, o = self.vid(FAL_KEY=None, KEYS_NO_KEYCHAIN="1")
        self.assertEqual(rc, 2, o)
        self.assertIn("NO KEY: FAL_KEY", o)
        rc, o = self.ag("video", "--prompt", "p", "--input", "pipeline/art/proof/in.png", "--out", "o.mp4",
                        **self.img_env(FAL_KEY=FAL_KEY))
        self.assertEqual(rc, 2, o)
        self.assertIn("PIECE REQUIRED", o)

    def test_piece_cap_is_one_dollar(self):
        self.assertEqual(self.vid()[0], 0, "first call 0.60 fits")
        rc, o = self.vid()
        self.assertEqual(rc, 2, o)
        self.assertIn("PIECE CAP", o)
        self.assertIn("$1.00", o)
        self.assertAlmostEqual(self.counter()["spent_usd"], 0.60)

    def test_total_cap_refuses(self):
        rc, o = self.vid(IMAGE_SPEND_CAP_USD="0.50")
        self.assertEqual(rc, 2, o)
        self.assertIn("CAP REACHED", o)


if __name__ == "__main__":
    unittest.main()

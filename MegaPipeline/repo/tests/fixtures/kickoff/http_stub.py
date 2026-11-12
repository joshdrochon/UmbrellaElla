"""Stands in for the vendor APIs in tests (ASSETGEN_HTTP_STUB / CONNECTIONS_HTTP_STUB): no network, no credits.
post(): ElevenLabs and Stability return WAV bytes (art has no API: Blender, pipeline/art/blender/); an ElevenLabs key
that reads 'nocredits' gets the HTTP 401 quota_exceeded answer an account with no credits left gets.
get(): an auth ping answers 200 unless the key reads 'revoked'.
Each call is appended to $HTTP_STUB_LOG (URL only, never a header)."""
import io
import json
import math
import os
import struct
import wave


def _log(url):
    if os.environ.get("HTTP_STUB_LOG"):
        with open(os.environ["HTTP_STUB_LOG"], "a", encoding="utf-8") as fh:
            fh.write(url + "\n")


def _wav(seconds=1.0, rate=48000):
    buf = io.BytesIO()
    n = int(seconds * rate)
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            env = math.exp(-5 * i / n) if i < n - 480 else 0.0
            frames += struct.pack("<h", int(0.5 * 32767 * env * math.sin(2 * math.pi * 220 * i / rate)))
        w.writeframes(bytes(frames))
    return buf.getvalue()


def post(url, headers, body):
    _log(url)
    if "elevenlabs.io" in url and any("nocredits" in v for v in headers.values()):   # the account ran out of credits
        import urllib.error
        raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, io.BytesIO(
            b'{"detail":{"status":"quota_exceeded","message":"This request exceeds your quota of 10000."}}'))
    if "elevenlabs.io" in url or "stability.ai" in url:
        return _wav(json.loads(body).get("duration_seconds") or 1.0)
    raise OSError(f"http_stub: no stub for {url}")


def get(url, headers):
    _log(url)
    return 401 if any("revoked" in v for v in headers.values()) else 200

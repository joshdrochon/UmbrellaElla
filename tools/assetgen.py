#!/usr/bin/env python3
"""Agent-driven art, audio, video and zip steps (issue #13 Architecture Defense). Stdlib only plus the tools in
pipeline/agent-ops/asset-tools.json. Every step is one command an agent runs; each output gets its provenance row in
pipeline/art/provenance.csv written here (author, origin, tool, model, prompt, input, date, licence), so nothing is
done by hand. The gates stay the same: art_check.py / sprite_check.py for art, audio_check.py --scan for audio,
submission_check.py video / loudness / zip for the video and the zip.

Art (Blender is the art generator: every sprite and background is modelled, rigged, lit and rendered by an agent in
Blender headless; scripts and recipes in pipeline/art/blender/)
  blender --character <id> --anim <Anim> [--out-dir Art/Source/<Asset>/Raw/<Anim>] [--frames N] [--seed S]
          [--sheet Art/Sprites/<Asset>/<name>.png]
          Renders every frame of one recipe row (pipeline/art/blender/characters.json; frame size, pivot and facing
          from the references.json `layout` entry, fps and frame count from style.json anims) at a fixed orthographic
          camera, transparent background, ink-and-paper NPR (toon shading in the palette darks, Freestyle ink lines,
          paper grain): `blender -b --factory-startup -P pipeline/art/blender/render_sprite.py -- --job <job.json>`.
          Renders, the job and the .blend stay under a Raw/ folder; --sheet then assembles the sheet (step `sheet`).
          One provenance row per frame: tool Blender, the version, the recipe line as prompt, the seed, inputs = the
          scripts, the recipe, the job and the .blend, origin naming the style targets (reference only, never shipped).
          No Blender (PATH, $BLENDER, or the usual install folder): labelled placeholder frames, which can never
          pass the art loop (tools/art_loop.py) or ship (check_pr.py, submission_check.py art).
  blender --script PY --out PNG [-- args]   any other Blender script, headless
  video   --prompt P --input OURS.png --out X.mp4 --piece ID [--seed S]
          Image-to-video on fal, the fixed model fal-ai/veo3.1/fast/image-to-video (any other --model is refused; the live model
          page must say "active"), 4 s, audio off, the prompt gets the flat chroma-green background text. Same guards as `image`
          (in-jam input, FAL_KEY, shared counter), priced from fal's live per-second price, its own 1 USD per-piece cap.
          Writes the mp4, <stem>.request.json and the provenance row (model, prompt, input image, seed, cost).
  batch   --jobs jobs.json [--workers 4]   up to 4 paid `image` calls at once (each job = one image argument list); same caps per call
  image   --prompt P --out pipeline/art/proof/ImageProof/<name>.png (proof images; shipped art goes under Art/) [--provider gemini|openai|openrouter|fal] [--tier draft|final] [--input OURS.png ...] [--model M]
          [--size WxH] [--aspect 4:1] [--image-size 0.5K|1K|2K|4K] [--seed S] [--quality low|medium|high]
          Image model (D-new-art-image-model; default gemini, key GEMINI_API_KEY; openai optional, OPENAI_API_KEY):
          one still from the prompt. Order: every --input is guarded first (GDD ART-03 / BG-02: a file under
          pipeline/art/reference/ or Assets/, a references.json or quality-bar image, the same bytes as one, an image
          with no provenance row or one dated before the jam start is REFUSED; our in-jam images may be inputs), then
          the key (none: NO KEY, exit 2, no placeholder; in a kickoff session it is queued), then the price from
          asset-tools.json price_usd_per_image, then the shared spend counter (env IMAGE_SPEND_FILE, locked): the
          cost is reserved before the call and the call is REFUSED when it would pass the hard total cap
          IMAGE_SPEND_CAP_USD (no cap or no counter set: no paid call). A request the provider rejects (HTTP 4xx)
          is refunded; any other failure keeps its cost. Writes the PNG, <stem>.request.json (full prompt, model,
          seed, inputs, cost, usage), the provenance row and a prompt line in Saved/agent-log/<day>.jsonl.
          Gemini: the aspect ratio is always sent (--aspect, else the nearest to --size; 1:4, 4:1, 1:8, 8:1 only on
          3.1 flash); a gemini 3.x model needs an explicit --image-size (it sets the price). Thinking tokens: the
          counter reserves asset-tools.json `thinking` reserve_fraction before the call and settles the reply's
          thoughtsTokenCount and promptTokenCount after it (docs/build/art-image-model.md).
  image-models   the image models on the Gemini key (models.list, free), each marked priced or UNPRICED
          [--element owl|character|effects|background|frame] [--character <id>] [--anim <Anim>]
          [--provider blender|placeholder|reference]
          One still: the element's (or --character's) recipe rendered by Blender, frame 0 of --anim (default
          its Still row, else its first). Fallback `--provider placeholder` (and no Blender): a labelled dark
          placeholder so the build never waits, never accepted as art. PRACTICE repos only (.pipeline-practice):
          `--provider reference` places the team's best-matching reference picture (pipeline/art/references.json by
          role, with the team art it joins, plus any image under pipeline/art/reference/) as a stand-in, and a
          practice run with no Blender uses it in place of the placeholder.
          Provenance says `source=reference (practice)`. On the team repo it FAILs (GDD 1.3 7C, Official Rules 7(h);
          submission_check.py assets fails such a row too)
  clean   --in PNG --out PNG [--xcf XCF]   GimpCLI, else GIMP 3 batch, else a Python colour-key cut: the corner
          colour becomes transparent (cut out for sprite_check)
  clean   --in PNG --out PNG --chroma 00FF00 [--grow 2] [--hue-tol 40]   image-model output painted on flat chroma:
          HSV key, the mask grown 1-2 px, the cut edge despilled; FAILs when the corners are not the key colour and
          WARNs on green inside the subject or key colour enclosed by it. --via rembg: the rembg cut-out fallback
  frames  --in KEYED_STRIP --count N --out-dir DIR [--frame WxH] [--pad 8] [--stem S] [--no-register]   one painted strip of N poses
          cut into N equal frames, each figure at its own scale on one bottom-centre baseline; <stem>.frames.json
          records the figure heights and their spread (scale drift). Then `sheet` assembles them
  crop    --in SHEET --mask KEYED_SHEET --count N --figure K --out PNG [--pad 24]   figure K of N cut out of a painted
          sheet on its own background: the single-figure input for a strip (a whole sheet makes the model copy it)
  sheet   --frames F1 F2 ... --out Art/Sprites/<name>.png --anim <Anim> --fps N [--kind silhouette]
          Aseprite CLI (horizontal sheet + JSON data), else a Python strip; writes the .sprite.json sidecar
Audio
  sfx     --sound <Id> --out Audio/Source/<Id>/SW_<Id>_<NN>.wav [--prompt "revision"] [--seconds S]
          [--provider elevenlabs|stable-audio|synth]
  music   --sound <Id> --out Audio/Source/<Id>/SW_<Id>_00.wav [--prompt "revision"] [--seconds S] [--provider ...]
          The prompt is built from pipeline/audio/style.json (the sound's style family) and its sound-list row
          (tools/audio_style_check.py build_prompt); --prompt only adds a revision, e.g. the critic's biggest gap.
          <Id> comes from --sound or from an --out named SW_<Id>_<NN>.wav. A prompt that names a game, studio or
          composer fails. Key: one audio API key (ELEVENLABS_API_KEY or STABILITY_API_KEY) on every machine that
          runs kickoff, because the jam perks include no audio tool. With no key the step makes a procedural
          placeholder, which is never on the quality bar (pipeline/audio/style-target.md)
  edit    --in WAV --out WAV [--start S] [--duration S] [--fade-ms N] [--lufs -14]   ffmpeg, else sox, else Python
          (trim and fade only). Audacity is the human fallback, never a pipeline step
Video and package
  capture --exe GAME --seconds S --out Saved/Video/raw.mkv [--via ffmpeg|obs] [--args "..."]
          launches the packaged build and records it (ffmpeg screen capture, or OBS through obs-websocket / obs-cmd)
  cut     --in RAW --out pipeline/submission/video/gameplay.mp4 [--start S] [--duration 45]   ffmpeg: 1920x1080,
          H.264 + AAC, -14 LUFS; then `submission_check.py video` and `loudness` measure it (Clipchamp: human fallback)
  zip     --dir PACKAGE --out Team_Game.zip     7-Zip CLI, else Python zipfile; then `submission_check.py zip`
Kickoff
  fulfil  --outbox DIR   run the queued API requests of an agent session (tools/kickoff.py calls it with the keys)

API steps (audio, and the image model's paid calls) need a key (tools/keys.py: env or OS keychain). Inside an agent session
(JAM_OUTBOX set) there is never a key, so an API step is QUEUED to $JAM_OUTBOX/asset-requests.jsonl and exits 3; kickoff
runs it with the key after the session and starts the next session with the files in place. With no key at fulfil
time the offline fallback runs (procedural audio) and the provenance row says so.
Test seams (never set in a jam): ASSETGEN_HTTP_STUB=<file.py> defines post(url, headers, body) -> bytes in place of
the network; the tool commands come from the env names in asset-tools.json (GIMPCLI, ASEPRITE, BLENDER, FFMPEG, ...);
ASSETGEN_NO_APP_DIRS=1 skips the install folders asset-tools.json `app_paths` lists (a test without Blender).
Exit 0 = done, 1 = the tool failed, 2 = usage or a missing tool, 3 = queued for kickoff.
"""
import argparse
import csv
import datetime as dt
import importlib.util
import io
import json
import math
import os
import random
import re
import shlex
import shutil
import struct
import subprocess
import sys
import threading
import time
import wave
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import keys  # noqa: E402
import png  # noqa: E402

INVENTORY = os.path.join(ROOT, "pipeline", "agent-ops", "asset-tools.json")
PROVENANCE = "pipeline/art/provenance.csv"
PROV_COLS = ["asset_path", "author", "origin", "tool", "model_version", "prompt", "seed", "input_images", "date",
             "licence", "attribution"]
QUEUED = 3
API_CMDS = ("sfx", "music")


class ToolMissing(Exception):
    pass


def inventory():
    with open(INVENTORY, encoding="utf-8") as fh:
        return json.load(fh)


def tool(tid):
    for t in inventory()["tools"]:
        if t["id"] == tid:
            return t
    raise KeyError(tid)


def command(tid):
    """The argv prefix for a CLI tool: its env override (may hold arguments), else the command on PATH."""
    t = tool(tid)
    if t.get("env") and os.environ.get(t["env"]):
        v = os.environ[t["env"]]
        if os.path.isfile(v):   # a bare path: Windows backslashes and spaces survive (shlex.split would eat them)
            return [v]
        return shlex.split(v)
    exe = shutil.which(t.get("command") or "")
    if not exe and os.environ.get("ASSETGEN_NO_APP_DIRS") != "1":
        import glob   # an app installed in its usual folder but not on PATH (Blender.app on a Mac)
        for pat in t.get("app_paths") or []:
            hits = sorted(glob.glob(os.path.expandvars(os.path.expanduser(pat))))
            if hits and os.access(hits[-1], os.X_OK):
                exe = hits[-1]
                break
    if not exe:
        raise ToolMissing(f"{t['name']}: `{t.get('command')}` is not on PATH (or set {t.get('env')})")
    return [exe]


def have(tid):
    try:
        command(tid)
        return True
    except ToolMissing:
        return False


def run(argv, **kw):
    p = subprocess.run(argv, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        raise RuntimeError(f"`{' '.join(argv[:3])} ...` exited {p.returncode}: {(p.stderr or p.stdout)[-400:]}")
    return p


# ---------- repo, provenance ----------
def repo_root():
    p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else os.getcwd()


def rel(path, root):
    """path relative to root with / separators. Both sides resolved: on Windows git prints a folder's long name while
    the working folder can carry its 8.3 short name (RUNNER~1 for runneradmin), and the two must match."""
    full = os.path.abspath(path)
    full = os.path.join(os.path.realpath(os.path.dirname(full)), os.path.basename(full))   # the file itself stays as named
    return os.path.relpath(full, os.path.realpath(root)).replace(os.sep, "/")


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M+00:00")


def role_author():
    role = os.environ.get("JAM_ROLE") or "human"
    return f"{role} (agent session via tools/assetgen.py)" if role != "human" else "team (tools/assetgen.py)"


PY_TOOL = {"name": "tools/assetgen.py (pure Python)",
           "licence": "team code (no third-party application); output belongs to the team"}


_FILE_WRITES = threading.RLock()   # batch threads share provenance.csv and the prompt log


def write_provenance(root, out, tid, prompt="", model="", inputs=(), origin="generated in jam", note="", info=None,
                     seed=""):
    """Add or replace the row for `out` (one row per asset path). info: {name, licence} for a source that is not
    an asset-tools.json tool (the team's reference art in a practice repo)."""
    with _FILE_WRITES:
        return _write_provenance(root, out, tid, prompt, model, inputs, origin, note, info, seed)


def _write_provenance(root, out, tid, prompt, model, inputs, origin, note, info, seed):
    path = os.path.join(root, PROVENANCE)
    rows = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8", newline="") as fh:
            rows = [r for r in csv.DictReader(fh)]
    t = info or tool(tid)
    key = rel(out, root)
    row = {"asset_path": key, "author": role_author(), "origin": origin + (f"; {note}" if note else ""),
           "tool": t["name"], "model_version": model, "prompt": (prompt or "").replace("\n", " ")[:300], "seed": str(seed),
           "input_images": ";".join(rel(i, root) for i in inputs), "date": now_iso(), "licence": t["licence"],
           "attribution": "see pipeline/submission/credits.md" if "attribution" in t["licence"].lower() else "none"}
    rows = [r for r in rows if r.get("asset_path") != key] + [row]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, PROV_COLS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in PROV_COLS})
    return row


# ---------- network (kickoff only) ----------
def http_post(url, headers, body):
    stub = os.environ.get("ASSETGEN_HTTP_STUB")
    if stub:
        spec = importlib.util.spec_from_file_location("assetgen_http_stub", stub)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.post(url, headers, body)
    import urllib.request
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:   # noqa: S310  vendor API from asset-tools.json
        return r.read()


def http_get(url, headers):
    stub = os.environ.get("ASSETGEN_HTTP_STUB")
    if stub:
        spec = importlib.util.spec_from_file_location("assetgen_http_stub", stub)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.get(url, headers)
    import urllib.request
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=60) as r:   # noqa: S310  vendor API from asset-tools.json
        return r.read()


def queue_or_key(args, key_name):
    """The key, or None after queueing this command for kickoff (agent session) / when no key exists."""
    k = keys.get(key_name)
    if k:
        return k
    outbox = os.environ.get("JAM_OUTBOX")
    if outbox and not os.environ.get("ASSETGEN_FULFIL"):
        os.makedirs(outbox, exist_ok=True)
        with open(os.path.join(outbox, "asset-requests.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"argv": args, "cwd": os.getcwd(), "role": os.environ.get("JAM_ROLE")}) + "\n")
        print(f"QUEUED: {args[0]} {args[args.index('--out') + 1] if '--out' in args else ''} -> kickoff runs it with "
              f"{key_name} after this session (tools/assetgen.py fulfil)")
        raise SystemExit(QUEUED)
    return None


# ---------- images ----------
def placeholder_png(path, w=256, h=256, label_seed=0):
    """A dark silhouette ellipse on transparency: cut out, so sprite_check's background and fill rules pass."""
    rows = []
    cx, cy, rx, ry = w / 2, h * 0.55, w * 0.32, h * 0.38
    for y in range(h):
        row = []
        for x in range(w):
            inside = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0
            row.append((22, 20, 24, 255) if inside else (0, 0, 0, 0))
        rows.append(row)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    png.write_png(path, w, h, rows)


# ---------- practice stand-ins: the team's reference art ----------
REFERENCE_SOURCE = "source=reference (practice)"
ELEMENT_ROLE = {"owl": "owl", "character": "character poses", "effects": "effects", "background": "scale",
                "frame": "composition target"}
ELEMENT_WORDS = (("effects", ("bolt", "missile", "projectile", "wand", "shot", "fx", "wind", "gust", "spark", "repair",
                              "impact")),
                 ("owl", ("owl", "clock", "boss")),
                 ("background", ("sky", "skyline", "background", "tile", "paper", "layer", "parallax")),
                 ("frame", ("style frame", "styleframe", "keyart", "key art", "composition", "scene")),
                 ("character", ("ella", "witch", "umbrella", "player", "hero", "girl")))


def practice_repo(root):
    try:
        import practice
        return practice.is_practice(root)
    except Exception:   # noqa: BLE001  no practice module: never a practice repo
        return os.path.isfile(os.path.join(root, ".pipeline-practice"))


def guess_element(text):
    low = (text or "").lower()
    for element, words in ELEMENT_WORDS:
        if any(w in low for w in words):
            return element
    return "frame"


def real_png(path):
    """A PNG on disk, not a Git LFS pointer (a checkout without LFS, like the CI runner, leaves pointers)."""
    try:
        with open(path, "rb") as fh:
            return fh.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def reference_pool(root):
    """[(repo path, roles)] of the team's reference pictures that exist: pipeline/art/references.json as every art
    tool reads it (tools/art_check.py load_spec: the team art under Assets/ and Mockups/ joined), then any other
    image under pipeline/art/reference/ (e.g. the #art-direction images) as a composition target."""
    out, seen = [], set()
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import art_check
        spec = art_check.load_spec(root)
    except (OSError, ValueError, ImportError):
        spec = {}
    for r in spec.get("references", []):
        p = r.get("path") or ""   # a kind described entry has no file
        if p.lower().endswith(".png") and real_png(os.path.join(root, p)):
            role = r.get("role", [])
            out.append((p, [role] if isinstance(role, str) else list(role),
                        bool(r.get("judge", not r.get("judge_exempt")))))
            seen.add(p)
    rdir = os.path.join(root, "pipeline", "art", "reference")
    for d, _, fs in os.walk(rdir):
        for f in sorted(fs):
            p = rel(os.path.join(d, f), root)
            if f.lower().endswith(".png") and p not in seen and real_png(os.path.join(d, f)):
                out.append((p, ["composition target"], True))
    return out


POOL_STOP = {"png", "jpg", "art", "source", "sprites", "assets", "test", "rehearsal", "pipeline", "reference", "the",
             "and", "content", "umbrellaella", "clean"}


def pick_reference(root, element, text):
    """The best-matching reference for an element: its role first, then words shared with the prompt and path."""
    role = ELEMENT_ROLE.get(element, "composition target")
    words = {w for w in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split()
             if len(w) > 2 and w not in POOL_STOP}
    best, best_score = None, None
    for path, roles, judge in reference_pool(root):
        name = "".join(c if c.isalnum() else " " for c in path.lower()).split()
        score = (3 if role in roles else 0) + sum(1 for w in words if any(w in n for n in name)) + (0.5 if judge else 0)
        if best_score is None or score > best_score:
            best, best_score = path, score
    return best


def place_reference(a, root, why):
    if not practice_repo(root):
        print("FAIL: reference art is a practice-repo stand-in only (.pipeline-practice). On the team repo every "
              "shipped image is made during the jam: generate it (GDD 1.3 7C; Official Rules 7(h); "
              "submission_check.py assets)")
        return 1
    stem = os.path.splitext(os.path.basename(a.out))[0]
    element = a.element or guess_element(f"{a.prompt} {stem}")
    src = pick_reference(root, element, f"{a.prompt} {stem}")
    if not src:
        return None
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    shutil.copyfile(os.path.join(root, src), a.out)
    write_provenance(root, a.out, None, a.prompt, "none", inputs=[os.path.join(root, src)],
                     origin=f"team reference art, {REFERENCE_SOURCE}", note=f"element={element}; {why}; never shipped",
                     info={"name": "team reference art (pipeline/art/references.json)",
                           "licence": "team reference, practice repo only (not for the jam entry)"})
    print(f"REFERENCE {rel(a.out, root)} <- {src} element={element} ({REFERENCE_SOURCE})")
    return 0


PLACEHOLDER_ORIGIN = "placeholder made in jam"
PLACEHOLDER_NOTE = "labelled placeholder, never accepted as art (art loop, check_pr, submission_check art)"


def placeholder(root, out, w, h, prompt, why):
    placeholder_png(out, w, h)
    write_provenance(root, out, "blender", prompt, "none", origin=PLACEHOLDER_ORIGIN, note=f"{why}; {PLACEHOLDER_NOTE}")
    print(f"PLACEHOLDER {rel(out, root)} ({why}; labelled in provenance, never accepted as art)")


def blender_plan():
    sys.path.insert(0, os.path.join(ROOT, "pipeline", "art", "blender"))
    import plan
    return plan


def recipe_for(root, element, character):
    """The recipe id for an image: --character, else the recipe whose `element` is this element."""
    if character:
        return character
    for cid, ch in (blender_plan().recipes(root).get("characters") or {}).items():
        if ch.get("element") == element:
            return cid
    return None


def style_targets(root, character, anim):
    """(piece, reference ids) the critic judges this recipe row against: its judge element's first references and
    the quality bar. Style targets only: recorded in provenance, never a render input, never shipped."""
    ch = (blender_plan().recipes(root).get("characters") or {}).get(character) or {}
    piece = ((ch.get("anims") or {}).get(anim) or {}).get("piece") or ch.get("piece")
    try:
        import art_check
        spec = art_check.load_spec(root if os.path.isfile(os.path.join(root, "pipeline", "art", "references.json"))
                                   else ROOT)
    except (ImportError, OSError, ValueError):
        return piece, []
    refs = ((spec.get("elements") or {}).get(piece) or {}).get("refs", [])[:3]
    qb = spec.get("quality_bar") or {}
    bar = (qb.get("by_piece") or {}).get(piece, qb.get("default")) if piece else None
    return piece, refs + ([bar] if bar and bar not in refs else [])


def render(a, root, character, anim, out_dir, frames=None):
    """Render one recipe row with Blender: (job, frame paths), one provenance row per frame. Raises ToolMissing (no
    Blender), RuntimeError (Blender failed) or ValueError (the recipe row cannot be planned)."""
    plan = blender_plan()
    j = plan.job(character, anim, out_dir, root=root, frames=frames, seed=getattr(a, "seed", None))
    if "Raw" not in j["out_dir"].split("/"):
        raise ValueError(f"renders are raw output: put --out-dir under a Raw/ folder (got {j['out_dir']}); "
                         "the sheet step makes the file that ships")
    prefix = command("blender")
    os.makedirs(j["out_dir"], exist_ok=True)
    job_path = f"{j['out_dir']}/{j['asset']}_{j['anim']}.job.json"   # out_dir uses /; one separator on Windows too
    with open(job_path, "w", encoding="utf-8") as fh:
        json.dump(j, fh, indent=1)
        fh.write("\n")
    p = run(plan.blender_argv(prefix, job_path, root=root))
    m = plan.RENDER_LINE.search(p.stdout or "")
    gone = [f for f in j["frames"] if not os.path.isfile(f)]
    if not m or gone:
        raise RuntimeError(f"Blender printed no BLENDER_RENDER line or missed frames {gone[:2]}: "
                           f"{(p.stdout + p.stderr)[-300:]}")
    version = m.group("version")
    piece, targets = style_targets(root, character, anim)
    scripts = [os.path.join(ROOT, "pipeline", "art", "blender", f)
               for f in ("render_sprite.py", "stand_ins.py", "characters.json")]
    note = (f"Blender {version} render from pipeline/art/blender (freestyle={m.group('freestyle') or '?'}, "
            f"compositor={m.group('compositor') or '?'}); style targets for piece {piece or 'none'}: "
            f"{', '.join(targets) or 'none'} (pipeline/art/references.json; reference only, never shipped)")
    for f in j["frames"]:
        write_provenance(root, f, "blender", plan.describe(j), f"Blender {version}",
                         inputs=scripts + [job_path, j["blend"]], origin="rendered in jam", note=note,
                         seed=j["look"].get("seed", ""))
    print(f"BLENDER {character} {anim} frames={len(j['frames'])} {j['frame_size'][0]}x{j['frame_size'][1]} "
          f"pivot={j['pivot_px'][0]:g},{j['pivot_px'][1]:g} fps={j['fps']} version={version} -> "
          f"{rel(j['out_dir'], root)}")
    return j, j["frames"], version


def cmd_image(a, argv, root):
    provider = a.provider
    if provider in IMAGE_PROVIDERS:
        try:
            return cmd_image_model(a, argv, root, provider)
        except ImageRefused as e:
            print(f"REFUSED: image: {e}")
            return 2
    if provider == "reference":
        rc = place_reference(a, root, "asked for")
        if rc is not None:
            return rc
        print("FAIL: no reference picture is present (pipeline/art/references.json); check out the team repo's main")
        return 1
    stem = os.path.splitext(os.path.basename(a.out))[0]
    w, h = (min(int(v), 256) for v in a.size.lower().split("x"))
    if provider == "placeholder":
        placeholder(root, a.out, w, h, a.prompt, "asked for a placeholder")
        return 0
    element = a.element or guess_element(f"{a.prompt} {stem}")
    character = recipe_for(root, element, a.character)
    if not character:
        placeholder(root, a.out, w, h, a.prompt,
                    f"no Blender recipe for element {element} (pipeline/art/blender/characters.json)")
        return 0
    anims = ((blender_plan().recipes(root).get("characters") or {}).get(character) or {}).get("anims") or {}
    anim = a.anim or ("Still" if "Still" in anims else next(iter(anims), "Still"))
    out_dir = "/".join([os.path.dirname(a.out).replace(os.sep, "/") or ".", "Raw", stem])
    try:
        j, frames, version = render(a, root, character, anim, out_dir)
    except ToolMissing as e:
        if practice_repo(root) and place_reference(a, root, "no Blender") == 0:
            return 0
        placeholder(root, a.out, w, h, a.prompt, f"no Blender: {e}")
        return 0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    shutil.copyfile(frames[0], a.out)
    piece, targets = style_targets(root, character, anim)
    write_provenance(root, a.out, "blender", f"{a.prompt} | {blender_plan().describe(j)}", f"Blender {version}",
                     inputs=[frames[0], j["blend"]], origin="rendered in jam",
                     note=f"frame 0 of {character} {anim}; style targets for piece {piece or 'none'}: "
                          f"{', '.join(targets) or 'none'} (reference only, never shipped)",
                     seed=j["look"].get("seed", ""))
    print(f"IMAGE {rel(a.out, root)} via=blender character={character} anim={anim} version={version}")
    return 0


# ---------- image model providers (D-new-art-image-model) ----------
IMAGE_PROVIDERS = {"gemini": ("gemini-image", "GEMINI_API_KEY"), "openai": ("openai-image", "OPENAI_API_KEY"),
                   "openrouter": ("gemini-image", "OPENROUTER_API_KEY"),   # openrouter, fal: Google's models, Google's price table
                   "fal": ("gemini-image", "FAL_KEY")}
GOOGLE_PROVIDERS = ("gemini", "openrouter", "fal")
# Tiers (Josh, Nov 12): drafts on the cheap flash model, final candidates on Pro. Ids checked against the key's
# models.list (image-models) on Nov 12: gemini-2.5-flash-image and gemini-3-pro-image-preview both exist and are priced.
IMAGE_TIERS = {"draft": "gemini-2.5-flash-image", "final": "gemini-3-pro-image-preview"}
# OpenRouter serves the SAME Google models only: our model id -> OpenRouter's id for that model (checked against
# openrouter.ai/api/v1/models, free, Nov 12: both tiers' models are offered). Anything else is refused, no fallback.
OPENROUTER_MODELS = {"gemini-2.5-flash-image": "google/gemini-2.5-flash-image",
                     "gemini-3-pro-image-preview": "google/gemini-3-pro-image-preview"}
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_CAP_USD = 19.89   # hard cap on OpenRouter spend in the shared counter (IMAGE_SPEND_OPENROUTER_CAP_USD overrides)
OPENROUTER_NEAR_CALLS = 5    # OpenRouter is used only when Gemini's remaining cap < this many final calls
OPENROUTER_INFO = {"name": "OpenRouter (Google Gemini image models)",
                   "licence": "OpenRouter Terms; output of the Google model: Gemini API Additional Terms of Service "
                              "(Google claims no ownership of generated output)"}
# fal serves the SAME Google models only (checked free, Nov 13: both exist on fal). Same rule: other ids refused.
FAL_MODELS = {"gemini-2.5-flash-image": "fal-ai/gemini-25-flash-image",
              "gemini-3-pro-image-preview": "fal-ai/gemini-3-pro-image-preview"}
FAL_ENDPOINT = "https://fal.run/"
FAL_CAP_USD = 74.84   # hard cap on fal spend in the shared counter (FAL_SPEND_CAP_USD overrides)
FAL_INFO = {"name": "fal (Google Gemini image models)",
            "licence": "fal Terms; output of the Google model: Gemini API Additional Terms of Service "
                       "(Google claims no ownership of generated output)"}
GEMINI_RATIOS = ("1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9")
GEMINI_IMAGE_SIZES = ("0.5K", "1K", "2K", "4K")
OPENAI_SIZES = {"1024x1024": 1.0, "1024x1536": 1.5, "1536x1024": 1.5}
SPEND_LOCK_TRIES = 600   # 0.05 s apart: half a minute for another worker's counter write


class ImageRefused(Exception):
    """The image call must not run (no key, no cap, the cap reached, a pre-jam input). Never a placeholder."""


def _sha(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def prejam_images(root):
    """{repo path: sha256} of every pre-jam picture: anything under pipeline/art/reference/ or Assets/ (the team's
    key art, references, studies and quality-bar images) and every image path pipeline/art/references.json names."""
    out = {}
    paths = set()
    for top in (os.path.join(root, "pipeline", "art", "reference"), os.path.join(root, "Assets")):
        for d, _, fs in os.walk(top):
            paths.update(os.path.join(d, f) for f in fs if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
    try:
        with open(os.path.join(root, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            spec = json.load(fh)
        paths.update(os.path.join(root, r["path"]) for r in spec.get("references", []) if r.get("path"))
    except (OSError, ValueError):
        pass
    for f in paths:
        if os.path.isfile(f):
            try:
                out[rel(f, root)] = _sha(f)
            except OSError:
                continue
    return out


def provenance_row(root, path):
    p = os.path.join(root, PROVENANCE)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("asset_path") == rel(path, root):
                return r
    return None


def jam_start():
    import submission_check
    return submission_check.JAM_START


def refuse_prejam_input(root, path):
    """None when `path` may be an image-model input, else why not (GDD ART-03, BG-02: no pre-jam image is ever an
    input; an in-jam image we made, with its provenance row dated after the jam start, may be)."""
    if not os.path.isfile(path):
        return f"{path}: no such file"
    r = rel(path, root)
    pre = prejam_images(root)
    if r.startswith(("pipeline/art/reference/", "Assets/")) or r in pre:
        return f"{r} is pre-jam team art (a reference, key art, study or quality-bar image)"
    sha = _sha(path)
    same = [p for p, h in pre.items() if h == sha]
    if same:
        return f"{r} has the same bytes as the pre-jam image {same[0]}"
    row = provenance_row(root, path)
    if not row:
        return f"{r} has no provenance row, so nothing shows it was made in the jam"
    try:
        made = dt.datetime.fromisoformat((row.get("date") or "").replace("Z", "+00:00"))
    except ValueError:
        return f"{r}: provenance date {row.get('date')!r} is not ISO 8601"
    if made.tzinfo is None or made < jam_start():
        return f"{r}: provenance date {row.get('date')} is before the jam start {jam_start().isoformat()}"
    if REFERENCE_SOURCE in (row.get("origin") or "") or PLACEHOLDER_ORIGIN in (row.get("origin") or ""):
        return f"{r}: provenance origin {row.get('origin')!r} is a reference stand-in or a placeholder, not our art"
    return None


def sized_by_image_size(t, model):
    """True when the model is priced (and so asked) by imageConfig.imageSize: gemini 3.x image models."""
    return t["id"] == "gemini-image" and isinstance((t.get("price_usd_per_image") or {}).get(model), dict)


def gemini_ratios(t, model):
    return tuple(t.get("aspect_ratios") or GEMINI_RATIOS) + tuple((t.get("aspect_ratios_extra") or {}).get(model) or ())


def image_price(t, model, quality, size, n_inputs, image_size=None):
    """USD for one output image from asset-tools.json's published price (price_usd_per_image), plus the input images
    at price_usd_per_input_image. Gemini 3.x prices by image_size, openai by quality and size."""
    table = t.get("price_usd_per_image") or {}
    price = table.get(model)
    if price is None:
        raise ImageRefused(f"no published price for model {model} in asset-tools.json ({t['id']} "
                           f"price_usd_per_image): an unpriced call cannot be counted against the cap")
    if isinstance(price, dict) and t["id"] == "gemini-image":
        if image_size not in price:
            raise ImageRefused(f"no published price for {model} at image size {image_size} (asset-tools.json; "
                               f"priced: {', '.join(price)}): pass --image-size")
        price = price[image_size]
    elif isinstance(price, dict):
        if quality not in price:
            raise ImageRefused(f"no published price for {model} quality {quality} (asset-tools.json)")
        price = price[quality]
        price *= OPENAI_SIZES.get(size, 1.5)
    return round(float(price) + n_inputs * float(t.get("price_usd_per_input_image") or 0), 6)


def thinking_rate(t, model):
    """(usd per thinking token, reserve fraction). A model with no row that still reports thinking tokens is billed
    at the highest rate in the table, so the counter never under-counts."""
    table = t.get("thinking") or {}
    row = table.get(model)
    if row:
        return float(row["usd_per_token"]), float(row.get("reserve_fraction") or 0)
    rates = [float(r["usd_per_token"]) for r in table.values()] or [0.0]
    return max(rates), 0.0


def settled_cost(t, model, image_cost, n_inputs, usage):
    """The real cost of a finished call: the published image price, the input tokens (prompt text and input images)
    and the thinking tokens, from the reply's usageMetadata. With no usage the reserve stands."""
    usage = usage or {}
    cost = image_cost
    in_rate = (t.get("usd_per_input_token") or {}).get(model)
    if in_rate is not None and usage.get("promptTokenCount") is not None:
        cost += float(usage["promptTokenCount"]) * float(in_rate)
    else:
        cost += n_inputs * float(t.get("price_usd_per_input_image") or 0)
    thoughts = int(usage.get("thoughtsTokenCount") or 0)
    if thoughts:
        cost += thoughts * thinking_rate(t, model)[0]
    return round(cost, 6)


class _SpendLock:
    """An exclusive lock on <counter>.lock shared by every worker process (fcntl, else msvcrt, else O_EXCL)."""

    def __init__(self, path):
        self.path = path + ".lock"
        self.fh = None

    def __enter__(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self.fh = open(self.path, "a+")
        try:
            import fcntl
            fcntl.flock(self.fh, fcntl.LOCK_EX)
            return self
        except ImportError:
            pass
        import msvcrt
        for _ in range(SPEND_LOCK_TRIES):
            try:
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
                return self
            except OSError:
                time.sleep(0.05)
        raise ImageRefused(f"the spend counter {self.path} stayed locked; no call made")

    def __exit__(self, *exc):
        try:
            import fcntl
            fcntl.flock(self.fh, fcntl.LOCK_UN)
        except ImportError:
            import msvcrt
            self.fh.seek(0)
            msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
        self.fh.close()


def spend_settings():
    """(counter file, cap USD). Both are required: no shared counter or no cap means no paid call."""
    cap_s = (os.environ.get("IMAGE_SPEND_CAP_USD") or "").strip()
    path = (os.environ.get("IMAGE_SPEND_FILE") or "").strip()
    if not cap_s:
        raise ImageRefused("NO CAP: IMAGE_SPEND_CAP_USD is not set, so no paid image call runs (the cap comes from "
                           "the build lead with Josh's Spend OK; tools/build/start_area.sh sets it)")
    try:
        cap = float(cap_s)
    except ValueError:
        raise ImageRefused(f"NO CAP: IMAGE_SPEND_CAP_USD={cap_s!r} is not a number")
    if not path:
        raise ImageRefused("NO COUNTER: IMAGE_SPEND_FILE is not set, so this call could not be counted with every "
                           "other worker's (tools/build/start_area.sh sets it)")
    return path, cap


def _read_spend(path):
    if not os.path.isfile(path):
        return {"spent_usd": 0.0, "calls": []}
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    d.setdefault("calls", [])
    d["spent_usd"] = float(d.get("spent_usd") or 0)
    return d


def _write_spend(path, d):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
        fh.write("\n")
    os.replace(tmp, path)


def openrouter_cap():
    v = (os.environ.get("IMAGE_SPEND_OPENROUTER_CAP_USD") or "").strip()
    return float(v) if v else OPENROUTER_CAP_USD


def fal_cap():
    v = (os.environ.get("FAL_SPEND_CAP_USD") or "").strip()
    return float(v) if v else FAL_CAP_USD


def provider_spent(d):
    """(openrouter USD, every other provider's USD, fal USD) in the counter. spent_usd stays the total of all."""
    def of(name):
        return sum(float(c.get("cost_usd") or 0) for c in d["calls"]
                   if c.get("provider") == name and not c.get("refunded"))
    orr, fal = of("openrouter"), of("fal")
    return round(orr, 6), round(max(0.0, d["spent_usd"] - orr - fal), 6), round(fal, 6)


PIECE_CAP_USD = 0.50   # Josh, Nov 13: per-piece image spend cap, both providers, keyed by piece in the counter
SMOKE_SHOT_MARK = "SmokeShotFrames"
SMOKE_HOOK = "Source/UmbrellaElla/Private/Smoke/SmokeHookSubsystem.cpp"


def piece_cap():
    v = (os.environ.get("IMAGE_SPEND_PIECE_CAP_USD") or "").strip()
    return float(v) if v else PIECE_CAP_USD


def smoke_shot_on_main(root):
    """True when origin/main has screenfix's frame-based smoke shot (-SmokeShotFrames in the smoke hook)."""
    try:
        r = subprocess.run(["git", "-C", root, "show", f"origin/main:{SMOKE_HOOK}"], capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0 and SMOKE_SHOT_MARK in r.stdout


def piece_is_screen(root, piece):
    """A UI screen piece (an element with a ui block in references.json) has no in-game context pair."""
    try:
        with open(os.path.join(root, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            refs = json.load(fh)
    except (OSError, ValueError):
        return False
    return bool((refs.get("elements", {}).get(piece) or {}).get("ui"))


def piece_needs_context(root, piece):
    """True when the piece needs an in-game context pair: any piece that is not a UI screen."""
    return not piece_is_screen(root, piece)


def draft_checks_passed(root, piece, draft):
    """(ok, why) for a draft file: art_check against style.json, and for a judge element the art_ref_check
    element score (best file >= score_min). Runs the checks; no paid call."""
    if not os.path.isfile(draft):
        return False, f"draft file {draft} does not exist"
    try:
        sys.path.insert(0, os.path.join(root, "tools"))
        import art_check, art_judge
        with open(os.path.join(root, "pipeline", "art", "style.json"), encoding="utf-8") as fh:
            st = json.load(fh)
        fails = art_check.evaluate(art_check.measure(draft, st), st)
        if fails:
            return False, "art_check FAIL: " + "; ".join(fails[:3])
        with open(os.path.join(root, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
            refs = json.load(fh)
        el = refs.get("elements", {}).get(piece)
        if el:
            _, rows, missing = art_judge.element(piece, [draft], refs, [root], set(el["refs"]))
            best = max((r[1] for r in rows), default=0.0)
            if best < el["score_min"]:
                return False, f"art_ref_check element {piece} FAIL: score {best} < {el['score_min']}"
    except Exception as e:   # noqa: BLE001  a check that cannot run is not a pass
        return False, f"the draft checks could not run: {e}"
    return True, "art_check and art_ref_check passed"


def spend_guards(root, a, tier):
    """Josh's image-spend guards 1 and 2 (before any key or counter use); ImageRefused when a guard stops the call."""
    piece = (getattr(a, "piece", None) or "").strip()
    if not piece:
        raise ImageRefused("PIECE REQUIRED: every paid image call names its piece (--piece <id>); no call made")
    if piece_needs_context(root, piece) and not smoke_shot_on_main(root):
        raise ImageRefused(f"NO CONTEXT SHOT: piece {piece} needs an in-game context pair and origin/main has no "
                           f"-{SMOKE_SHOT_MARK} support yet ({SMOKE_HOOK}); only UI screens paint until screenfix's "
                           f"frame-based smoke shot is on main. No call made")
    if tier == "final":
        draft = getattr(a, "from_draft", None)
        if not draft:
            raise ImageRefused("DRAFT FIRST: --tier final needs --from-draft <file>, a draft of this piece whose "
                               "art_check / art_ref_check passed; no call made")
        ok, why = draft_checks_passed(root, piece, draft)
        if not ok:
            raise ImageRefused(f"DRAFT NOT PASSED: {why} ({draft}); fix the draft first. No call made")
    return piece


def log_piece_cap(root, line):
    d = os.path.join(os.path.dirname(os.path.abspath(root)), "logs")
    try:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "spend-cap.log"), "a", encoding="utf-8") as fh:
            fh.write(f"{now_iso()} {line}\n")
    except OSError:
        pass


def spend_reserve(cost, entry):
    """Add `cost` to the shared counter before the call, under the lock; ImageRefused when it would pass the cap of
    its provider (OpenRouter has its own hard cap; every other provider shares IMAGE_SPEND_CAP_USD).
    Returns the call's index in the counter (spend_settle updates it)."""
    path, cap = spend_settings()
    which = entry.get("provider")
    with _SpendLock(path):
        d = _read_spend(path)
        or_spent, other_spent, fal_spent = provider_spent(d)
        spent, limit, name = {"openrouter": (or_spent, openrouter_cap(), "OpenRouter image cap"),
                              "fal": (fal_spent, fal_cap(), "fal image cap (FAL_SPEND_CAP_USD)")}.get(
            which, (other_spent, cap, "total image cap (IMAGE_SPEND_CAP_USD)"))
        if spent + cost > limit + 1e-9:
            raise ImageRefused(f"CAP REACHED: spent ${spent:.3f} of the ${limit:.2f} {name}; this call "
                               f"(${cost:.3f}) would pass it. No call made. "
                               f"Every further {entry.get('provider')} image call stops here (counter {path})")
        piece = entry.get("piece")
        if piece:
            ps = round(sum(float(c.get("cost_usd") or 0) for c in d["calls"]
                           if c.get("piece") == piece and not c.get("refunded")), 6)
            pcap = float(entry.pop("piece_cap", None) or piece_cap())   # video calls carry their own per-piece cap
            if ps + cost > pcap + 1e-9:
                msg = (f"PIECE CAP: piece {piece} has spent ${ps:.3f} of the ${pcap:.2f} per-piece cap; this "
                       f"call (${cost:.3f}) would pass it. triage art vs check before more spend. No call made")
                log_piece_cap(entry.get("root") or os.getcwd(), f"piece={piece} provider={entry.get('provider')} {msg}")
                raise ImageRefused(msg)
        entry.pop("root", None)
        entry.pop("piece_cap", None)
        d["spent_usd"] = round(d["spent_usd"] + cost, 6)
        d["cap_usd"] = cap
        d["openrouter_cap_usd"] = openrouter_cap()
        d["fal_cap_usd"] = fal_cap()
        d["calls"].append(dict(entry, cost_usd=cost, status="reserved", ts=now_iso()))
        _write_spend(path, d)
        return len(d["calls"]) - 1, spent + cost, limit


def gemini_remaining():
    """USD left under Gemini's cap (None when no cap or counter is configured)."""
    try:
        path, cap = spend_settings()
    except ImageRefused:
        return None
    with _SpendLock(path):
        return cap - provider_spent(_read_spend(path))[1]


def openrouter_remaining():
    """USD left under OpenRouter's own cap (None when no counter is configured)."""
    try:
        path, _ = spend_settings()
    except ImageRefused:
        return None
    with _SpendLock(path):
        return openrouter_cap() - provider_spent(_read_spend(path))[0]


def fal_model(model):
    """fal's id for our model; ImageRefused for any model that is not one of the two Google image models."""
    if model not in FAL_MODELS:
        raise ImageRefused(f"FAL REFUSED: {model!r} is not one of the Google models fal may serve "
                           f"({', '.join(FAL_MODELS)}); no fallback to another model")
    return FAL_MODELS[model]


def openrouter_model(model):
    """OpenRouter's id for our model; ImageRefused for any model that is not one of the two Google image models."""
    if model not in OPENROUTER_MODELS:
        raise ImageRefused(f"OPENROUTER REFUSED: {model!r} is not one of the Google models OpenRouter may serve "
                           f"({', '.join(OPENROUTER_MODELS)}); no fallback to another model")
    return OPENROUTER_MODELS[model]


def pick_provider(provider, model, key_present=None):
    """The provider that serves this call. An explicit openrouter or fal is checked against its mapping. Order is
    gemini, then OpenRouter, then fal: gemini moves to OpenRouter only when its remaining cap is below the cost of
    OPENROUTER_NEAR_CALLS final calls, the model is mapped and an OpenRouter key exists; OpenRouter moves on to fal
    only when OpenRouter's own remaining cap is also that low and a fal key exists. Otherwise no silent change.
    key_present, for tests: dict of key name -> bool, or a bool for the OpenRouter key."""
    if provider == "openrouter":
        openrouter_model(model)
        return provider
    if provider == "fal":
        fal_model(model)
        return provider
    if provider != "gemini" or model not in OPENROUTER_MODELS or model not in FAL_MODELS:
        return provider
    def has(name):
        if isinstance(key_present, dict):
            return key_present.get(name, False)
        if key_present is not None:
            return key_present if name == "OPENROUTER_API_KEY" else False
        return bool(keys.get(name))
    left = gemini_remaining()
    final_cost = image_price(tool("gemini-image"), IMAGE_TIERS["final"], "medium", "1024x1024", 0, "2K")
    near = OPENROUTER_NEAR_CALLS * final_cost
    if left is None or left >= near or not has("OPENROUTER_API_KEY"):
        return provider
    or_left = openrouter_remaining()
    if or_left is not None and or_left < near and has("FAL_KEY"):
        return "fal"
    return "openrouter"


def spend_settle(index, status, refund=False, cost=None, **extra):
    """Mark a reserved call done or failed; refund=True gives its cost back (the provider refused the request, so it
    was not billed); cost= replaces the reserve with the real cost (thinking and input tokens from the reply), which
    may be above the reserve: the counter shows the overrun and the next call sees it."""
    path, _ = spend_settings()
    with _SpendLock(path):
        d = _read_spend(path)
        c = d["calls"][index]
        c.update(extra, status=status)
        if refund and not c.get("refunded"):
            c["refunded"] = True
            d["spent_usd"] = round(max(0.0, d["spent_usd"] - float(c.get("cost_usd") or 0)), 6)
        elif cost is not None and not c.get("refunded"):
            reserved = float(c.get("cost_usd") or 0)
            c["reserved_usd"] = reserved
            c["cost_usd"] = round(cost, 6)
            d["spent_usd"] = round(max(0.0, d["spent_usd"] - reserved + cost), 6)
        _write_spend(path, d)
        return d["spent_usd"]


def log_image_prompt(root, prompt, provider, model, out, cost):
    """One `prompt` line in Saved/agent-log/<day>.jsonl, the log tools/prompt_log.py reads and exports."""
    ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    host = os.environ.get("JAM_HOST")
    if host:
        host = re.sub(r"[^A-Za-z0-9_-]", "-", host)[:32]
    else:
        import hashlib
        import socket
        host = "host-" + hashlib.sha256(socket.gethostname().encode()).hexdigest()[:6]
    rec = {"ts": ts, "event": "prompt", "kind": "image", "role": os.environ.get("JAM_ROLE"), "card": None,
           "host": host, "session": None, "tool": provider, "model": model, "out": rel(out, root), "cost_usd": cost,
           "prompt": prompt}
    d = os.path.join(root, "Saved", "agent-log")
    os.makedirs(d, exist_ok=True)
    with _FILE_WRITES, open(os.path.join(d, ts[:10] + ".jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def _ratio(size, ratios=GEMINI_RATIOS):
    w, h = (int(v) for v in size.lower().split("x"))
    want = w / h
    return min(ratios, key=lambda r: abs(int(r.split(":")[0]) / int(r.split(":")[1]) - want))


def gemini_shape(t, model, a):
    """(aspect ratio, image size or None), both checked against the model before any spend. The aspect ratio is
    always sent (from --aspect, else the nearest the model has to --size); a model priced by size needs
    --image-size, and a model without imageSize refuses one."""
    ratios = gemini_ratios(t, model)
    aspect = a.aspect or _ratio(a.size, ratios)
    if aspect not in ratios:
        raise ImageRefused(f"{model} has no aspect ratio {aspect} (asset-tools.json aspect_ratios: {', '.join(ratios)})")
    if sized_by_image_size(t, model):
        if not a.image_size:
            raise ImageRefused(f"{model} needs an explicit --image-size ({', '.join(t['price_usd_per_image'][model])}): "
                               f"the size sets the price and the detail")
        return aspect, a.image_size
    if a.image_size:
        raise ImageRefused(f"{model} takes no imageSize (it paints about 1K); drop --image-size or pick a gemini 3.x "
                           f"image model")
    return aspect, None


def _mime(path):
    with open(path, "rb") as fh:
        head = fh.read(12)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError(f"{path}: not a PNG, JPEG or WebP image")


def gemini_request(t, model, prompt, inputs, aspect, image_size, seed, key):
    import base64
    parts = [{"text": prompt}]
    for f in inputs:
        with open(f, "rb") as fh:
            parts.append({"inline_data": {"mime_type": _mime(f), "data": base64.b64encode(fh.read()).decode()}})
    image_cfg = {"aspectRatio": aspect}
    if image_size:
        image_cfg["imageSize"] = image_size
    cfg = {"responseModalities": ["IMAGE"], "imageConfig": image_cfg}
    if seed is not None:
        cfg["seed"] = int(seed)
    body = json.dumps({"contents": [{"role": "user", "parts": parts}], "generationConfig": cfg}).encode()
    raw = http_post(t["endpoint"].format(model=model), {"x-goog-api-key": key, "Content-Type": "application/json"},
                    body)
    reply = json.loads(raw)
    for cand in reply.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            data = part.get("inlineData") or part.get("inline_data")
            if data and data.get("data"):
                return (base64.b64decode(data["data"]), reply.get("modelVersion") or model,
                        {"usage": reply.get("usageMetadata"), "finish": cand.get("finishReason")})
    why = [c.get("finishReason") for c in reply.get("candidates") or []] or reply.get("promptFeedback")
    texts = [p.get("text") for c in reply.get("candidates") or [] for p in (c.get("content") or {}).get("parts") or []
             if p.get("text")]
    raise RuntimeError(f"gemini returned no image (finish={why}; text={' '.join(texts)[:160]!r})")


def openrouter_request(t, model, prompt, inputs, aspect, image_size, key):
    """One image through OpenRouter's chat completions for the mapped Google model (never any other)."""
    import base64
    parts = [{"type": "text", "text": prompt}]
    for f in inputs:
        with open(f, "rb") as fh:
            parts.append({"type": "image_url", "image_url": {
                "url": f"data:{_mime(f)};base64," + base64.b64encode(fh.read()).decode()}})
    image_cfg = {"aspect_ratio": aspect}
    if image_size:
        image_cfg["image_size"] = image_size
    body = json.dumps({"model": openrouter_model(model), "messages": [{"role": "user", "content": parts}],
                       "modalities": ["image", "text"], "image_config": image_cfg,
                       "usage": {"include": True}}).encode()
    raw = http_post(OPENROUTER_ENDPOINT, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, body)
    reply = json.loads(raw)
    for ch in reply.get("choices") or []:
        for im in (ch.get("message") or {}).get("images") or []:
            url = (im.get("image_url") or {}).get("url") or ""
            if url.startswith("data:") and "," in url:
                return (base64.b64decode(url.split(",", 1)[1]), reply.get("model") or openrouter_model(model),
                        {"usage": reply.get("usage"), "finish": ch.get("finish_reason")})
    raise RuntimeError(f"openrouter returned no image (model={reply.get('model')!r}; error={str(reply.get('error'))[:160]!r})")


def fal_request(t, model, prompt, inputs, aspect, image_size, key):
    """One image through fal for the mapped Google model (never any other); inputs use the model's /edit route."""
    import base64
    body = {"prompt": prompt, "num_images": 1, "aspect_ratio": aspect, "output_format": "png"}
    if image_size:
        body["resolution"] = image_size
    path = fal_model(model)
    if inputs:
        path += "/edit"
        body["image_urls"] = [f"data:{_mime(f)};base64," + base64.b64encode(open(f, "rb").read()).decode() for f in inputs]
    raw = http_post(FAL_ENDPOINT + path, {"Authorization": f"Key {key}", "Content-Type": "application/json"},
                    json.dumps(body).encode())
    reply = json.loads(raw)
    for im in reply.get("images") or []:
        url = im.get("url") or ""
        if url.startswith("data:") and "," in url:
            data = base64.b64decode(url.split(",", 1)[1])
        elif url.startswith("https://"):
            data = http_get(url, {})
        else:
            continue
        return data, fal_model(model), {"description": str(reply.get("description") or "")[:200]}
    raise RuntimeError(f"fal returned no image (model={fal_model(model)!r}; error={str(reply.get('detail') or reply.get('error'))[:160]!r})")


def _multipart(fields, files):
    import uuid
    b = "----assetgen" + uuid.uuid4().hex
    out = io.BytesIO()
    for k, v in fields.items():
        out.write(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    for k, f in files:
        with open(f, "rb") as fh:
            data = fh.read()
        out.write(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{os.path.basename(f)}\"\r\n"
                  f"Content-Type: {_mime(f)}\r\n\r\n".encode() + data + b"\r\n")
    out.write(f"--{b}--\r\n".encode())
    return out.getvalue(), f"multipart/form-data; boundary={b}"


def openai_request(t, model, prompt, inputs, size, quality, key):
    import base64
    auth = {"Authorization": f"Bearer {key}"}
    fields = {"model": model, "prompt": prompt, "size": size if size in OPENAI_SIZES else "auto", "quality": quality,
              "n": "1"}
    if inputs:
        body, ctype = _multipart(fields, [("image[]", f) for f in inputs])
        raw = http_post(t["edit_endpoint"], dict(auth, **{"Content-Type": ctype}), body)
    else:
        fields["n"] = 1
        raw = http_post(t["endpoint"], dict(auth, **{"Content-Type": "application/json"}), json.dumps(fields).encode())
    reply = json.loads(raw)
    data = (reply.get("data") or [{}])[0].get("b64_json")
    if not data:
        raise RuntimeError(f"openai returned no image ({str(reply)[:160]})")
    return base64.b64decode(data), model, {"usage": reply.get("usage")}


def to_png(data, out):
    """Write the model's bytes as a PNG (macOS sips or ffmpeg convert a JPEG or WebP reply)."""
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        with open(out, "wb") as fh:
            fh.write(data)
        return "png"
    tmp = out + ".src"
    with open(tmp, "wb") as fh:
        fh.write(data)
    try:
        if shutil.which("sips"):
            run(["sips", "-s", "format", "png", tmp, "--out", out])
        else:
            run(command("ffmpeg") + ["-y", "-i", tmp, out])
    finally:
        os.remove(tmp)
    return "converted"


def cmd_image_model(a, argv, root, provider):
    """One paid still from an image model. Order: inputs guarded, key, price, cap reserved, call, provenance, log."""
    tier = getattr(a, "tier", None) or "draft"
    model = a.model or (IMAGE_TIERS[tier] if provider in GOOGLE_PROVIDERS else tool(IMAGE_PROVIDERS[provider][0])["model"])
    piece = spend_guards(root, a, tier)
    provider = pick_provider(provider, model)
    tid, key_name = IMAGE_PROVIDERS[provider]
    t = tool(tid)
    google = provider in GOOGLE_PROVIDERS
    inputs = list(a.input or [])
    for f in inputs:
        why = refuse_prejam_input(root, f)
        if why:
            raise ImageRefused(f"PRE-JAM INPUT REFUSED: {why}. GDD ART-03 / BG-02: describe pre-jam art in words "
                               f"(pipeline/art/art-bible.md, the references' notes); only in-jam images we made may "
                               f"be inputs")
    k = keys.get(key_name)
    if not k:
        if os.environ.get("JAM_OUTBOX") and not os.environ.get("ASSETGEN_FULFIL"):
            queue_or_key(argv, key_name)
        raise ImageRefused(f"NO KEY: {key_name} is not set (tools/keys.py status), so no image was made and no "
                           f"placeholder stands in for it. {keys.how_to_set(key_name)}")
    aspect, image_size = gemini_shape(t, model, a) if google else (None, None)
    base_cost = image_price(t, model, a.quality, a.size, len(inputs), image_size)
    image_cost = image_price(t, model, a.quality, a.size, 0, image_size)
    think = round(image_cost * thinking_rate(t, model)[1], 6) if google else 0.0
    cost = round(base_cost + think, 6)
    entry = {"provider": provider, "model": model, "tier": tier, "out": rel(a.out, root), "inputs": len(inputs),
             "piece": piece, "root": root, "from_draft": rel(a.from_draft, root) if getattr(a, "from_draft", None) else None,
             "worker": os.path.basename(root), "role": os.environ.get("JAM_ROLE"), "aspect": aspect,
             "image_size": image_size, "thinking_reserve_usd": think}
    idx, spent, cap = spend_reserve(cost, entry)
    try:
        if provider == "gemini":
            data, version, meta = gemini_request(t, model, a.prompt, inputs, aspect, image_size, a.seed, k)
        elif provider == "openrouter":
            data, version, meta = openrouter_request(t, model, a.prompt, inputs, aspect, image_size, k)
        elif provider == "fal":
            data, version, meta = fal_request(t, model, a.prompt, inputs, aspect, image_size, k)
        else:
            data, version, meta = openai_request(t, model, a.prompt, inputs, a.size, a.quality, k)
    except Exception as e:   # noqa: BLE001  the call failed: settle the counter, report, never a placeholder
        code = getattr(e, "code", None)
        refused = isinstance(code, int) and 400 <= code < 500   # rejected before generation: not billed
        spent = spend_settle(idx, "failed", refund=refused, error=api_error(e) if code else str(e)[:200])
        print(f"FAIL: image {provider} {model}: {api_error(e) if code else e}; counter ${spent:.3f} of ${cap:.2f}"
              + (" (refunded: the provider refused the request)" if refused else " (cost kept: it may be billed)"))
        return 1
    how = to_png(data, a.out)
    if provider == "gemini":
        cost = settled_cost(t, model, image_cost, len(inputs), meta.get("usage"))
    elif provider == "openrouter" and isinstance((meta.get("usage") or {}).get("cost"), (int, float)):
        cost = round(float(meta["usage"]["cost"]), 6)   # what OpenRouter billed for the call
    spent = spend_settle(idx, "done", cost=cost, usage=meta.get("usage"), model_version=version)
    if provider == "gemini":
        seed = a.seed if a.seed is not None else ""
    else:
        seed = "none (no seed parameter)" if provider == "openai" else "none (seed not sent)"
    with open(os.path.splitext(a.out)[0] + ".request.json", "w", encoding="utf-8") as fh:
        json.dump({"provider": provider, "tier": tier, "tool": {"openrouter": OPENROUTER_INFO["name"], "fal": FAL_INFO["name"]}.get(provider, t["name"]),
                   "model": model, "openrouter_model": OPENROUTER_MODELS.get(model) if provider == "openrouter" else None,
                   "fal_model": FAL_MODELS.get(model) if provider == "fal" else None, "model_version": version,
                   "prompt": a.prompt, "seed": seed, "size": a.size, "quality": a.quality, "aspect_ratio": aspect,
                   "image_size": image_size,
                   "input_images": [rel(f, root) for f in inputs], "cost_usd": cost, "reply": meta,
                   "date": now_iso()}, fh, indent=1)
        fh.write("\n")
    cap_name = {"openrouter": "OpenRouter image cap", "fal": "fal image cap"}.get(provider, "shared image cap")
    write_provenance(root, a.out, tid, a.prompt, version, inputs=inputs, origin="generated in jam",
                     info={"openrouter": OPENROUTER_INFO, "fal": FAL_INFO}.get(provider),
                     note=f"image model provider={provider} tier={tier} model={model}; ${cost:.3f} counted against the {cap_name}; full prompt in "
                          f"{rel(os.path.splitext(a.out)[0] + '.request.json', root)}", seed=seed)
    log_image_prompt(root, a.prompt, provider, version, a.out, cost)
    w, h, _ = png.read_png(a.out)
    thoughts = ((meta.get("usage") or {}).get("thoughtsTokenCount") or 0) if provider == "gemini" else 0
    print(f"IMAGE {rel(a.out, root)} via={provider} tier={tier} model={version} {w}x{h} inputs={len(inputs)} "
          f"aspect={aspect or a.size} image_size={image_size or '-'} thinking_tokens={thoughts} cost=${cost:.3f} "
          f"spent=${spent:.3f} of ${cap:.2f} ({how})")
    return 0


# ---------- batch: up to 4 paid generation calls at once (Josh, Nov 13) ----------
BATCH_MAX_WORKERS = 4
BATCH_PROVIDERS = ("gemini", "openai", "openrouter", "fal")   # paid calls only; Blender, keying, scans stay outside


class _ThreadOut:
    """sys.stdout that gives each batch thread its own buffer, so job lines never interleave."""

    def __init__(self, real):
        self.real, self.local = real, threading.local()

    def write(self, s):
        buf = getattr(self.local, "buf", None)
        return buf.write(s) if buf is not None else self.real.write(s)

    def flush(self):
        self.real.flush()

    def __getattr__(self, name):
        return getattr(self.real, name)


def batch_jobs(path):
    """The jobs file: a JSON list; each job is the list of `image` arguments (strings) for one call."""
    with open(path, encoding="utf-8") as fh:
        jobs = json.load(fh)
    if not isinstance(jobs, list) or not jobs or not all(isinstance(j, list) and all(isinstance(x, str) for x in j) for j in jobs):
        raise ValueError(f"{path}: expected a non-empty JSON list of argument lists, e.g. [[\"--prompt\", \"..\", \"--out\", \"..\", \"--piece\", \"..\"]]")
    return jobs


def run_batch(jobs, root, workers):
    """Run each job (an `image` argument list) through cmd_image on up to `workers` threads. Every job goes through the
    same reserve -> call -> settle path as a single `image` call (file-locked counter, provider and per-piece caps,
    draft-first, context-shot guard), so concurrency can never overspend; a refused or failed job does not stop
    the others. Returns [(job index, exit code, output)] in job order."""
    from concurrent.futures import ThreadPoolExecutor
    workers = max(1, min(int(workers), BATCH_MAX_WORKERS))
    proxy = _ThreadOut(sys.stdout)

    def one(i):
        buf = io.StringIO()
        proxy.local.buf = buf
        try:
            args = parser().parse_args(["image"] + jobs[i])
            if args.provider not in BATCH_PROVIDERS:
                print(f"REFUSED: batch: provider {args.provider} is not a paid generation call; run it outside the batch")
                rc = 2
            else:
                rc = cmd_image(args, ["image"] + jobs[i], root)
        except SystemExit:
            print(f"REFUSED: batch: job {i} has bad arguments")
            rc = 2
        except Exception as e:   # noqa: BLE001  one job's crash never stops the others
            print(f"FAIL: batch job {i}: {type(e).__name__}: {str(e)[:200]}")
            rc = 1
        finally:
            proxy.local.buf = None
        return i, rc, buf.getvalue()

    real, sys.stdout = sys.stdout, proxy
    try:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return sorted(ex.map(one, range(len(jobs))))
    finally:
        sys.stdout = real


def cmd_batch(a, argv, root):
    results = run_batch(batch_jobs(a.jobs), root, a.workers)
    for i, rc, out in results:
        for line in out.splitlines():
            print(f"[{i}] {line}")
    bad = [i for i, rc, _ in results if rc]
    print(f"BATCH {len(results) - len(bad)}/{len(results)} ok, {len(bad)} refused or failed"
          + (f" (jobs {', '.join(map(str, bad))})" if bad else "") + f", workers={min(a.workers, BATCH_MAX_WORKERS)}")
    return 1 if bad else 0


def cmd_image_models(a, argv, root):
    """The image models on the Gemini key (models.list: free, not counted), marked priced or not in asset-tools.json.
    An unpriced model can only be used after its published price is added there."""
    t = tool("gemini-image")
    k = keys.get("GEMINI_API_KEY")
    if not k:
        print(f"NO KEY: GEMINI_API_KEY is not set (tools/keys.py status). {keys.how_to_set('GEMINI_API_KEY')}")
        return 2
    try:
        reply = json.loads(http_get(t["models_endpoint"], {"x-goog-api-key": k}))
    except Exception as e:   # noqa: BLE001  report, never print the key
        print(f"FAIL: image-models: {api_error(e) if getattr(e, 'code', None) else e}")
        return 1
    priced = t.get("price_usd_per_image") or {}
    rows = []
    for m in reply.get("models") or []:
        mid = (m.get("name") or "").split("/", 1)[-1]
        if "image" not in mid and "imagen" not in mid:
            continue
        rows.append((mid, m.get("displayName") or "", ",".join(m.get("supportedGenerationMethods") or []),
                     "priced" if mid in priced else "UNPRICED"))
    for r in sorted(rows):
        print("MODEL " + " | ".join(r))
    print(f"IMAGE-MODELS {len(rows)} image models on the key; priced in asset-tools.json: "
          f"{', '.join(sorted(m for m in priced if m in {r[0] for r in rows})) or 'none'}")
    return 0


# ---------- chroma key, despill, strip cutting (art-image-model.md method) ----------
def _hex_rgb(h):
    h = h.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"--chroma {h!r}: give a hex colour like 00FF00")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hue_dist(h1, h2):
    d = abs(h1 - h2) % 1.0
    return min(d, 1.0 - d)


def chroma_key(src, dst, key="00FF00", grow=2, hue_tol=40, s_min=0.30, v_min=0.25, despill_band=4):
    """HSV chroma key. A pixel is background when its hue is within hue_tol degrees of the key's and it is saturated
    and bright enough; the background mask then grows `grow` px into the subject (eats the green fringe the light
    outline sits on), and pixels within `despill_band` px of the cut lose their green spill (g clamped to max(r, b)).
    Returns stats; ValueError when the corners are not the key colour (the background is not a flat chroma)."""
    import colorsys
    kr, kg, kb = _hex_rgb(key)
    kh, ks, kv = colorsys.rgb_to_hsv(kr / 255, kg / 255, kb / 255)
    w, h, rows = png.read_png(src)
    tol = hue_tol / 360.0
    cache = {}

    def is_key(r, g, b):
        c = (r, g, b)
        hit = cache.get(c)
        if hit is None:
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hit = _hue_dist(hh, kh) <= tol and ss >= s_min and vv >= v_min
            if len(cache) < 200000:
                cache[c] = hit
        return hit

    corners = [rows[0][0], rows[0][w - 1], rows[h - 1][0], rows[h - 1][w - 1]]
    bad = [c[:3] for c in corners if c[3] and not is_key(*c[:3])]
    if len(bad) > 1:
        raise ValueError(f"{src}: the corners {bad} are not the key colour #{key.lstrip('#')}: the background is not a "
                         f"flat chroma (check our prompt first; else cut out with --via rembg)")
    bg = bytearray(w * h)
    for y, row in enumerate(rows):
        base = y * w
        for x, (r, g, b, al) in enumerate(row):
            if al == 0 or is_key(r, g, b):
                bg[base + x] = 1
    keyed = sum(bg)
    reached = bytearray(w * h)   # key colour reached from the border; the rest is enclosed by the subject
    stack = [i for i in list(range(w)) + list(range((h - 1) * w, h * w)) + list(range(0, w * h, w))
             + list(range(w - 1, w * h, w)) if bg[i]]
    for i in stack:
        reached[i] = 1
    while stack:
        i = stack.pop()
        y, x = divmod(i, w)
        for j in (i - 1 if x else -1, i + 1 if x < w - 1 else -1, i - w if y else -1, i + w if y < h - 1 else -1):
            if j >= 0 and bg[j] and not reached[j]:
                reached[j] = 1
                stack.append(j)
    enclosed = keyed - sum(reached)
    edge = [i for i in range(w * h) if not bg[i] and _touches(bg, i, w, h)]
    grown = 0
    for _ in range(grow):
        nxt = []
        for i in edge:
            if not bg[i]:
                bg[i] = 2
                grown += 1
        for i in edge:
            y, x = divmod(i, w)
            for j in (i - 1 if x else -1, i + 1 if x < w - 1 else -1, i - w if y else -1, i + w if y < h - 1 else -1):
                if j >= 0 and not bg[j]:
                    nxt.append(j)
        edge = list(set(nxt))
    band = set(edge)
    frontier = list(band)
    for _ in range(max(0, despill_band - 1)):
        nxt = []
        for i in frontier:
            y, x = divmod(i, w)
            for j in (i - 1 if x else -1, i + 1 if x < w - 1 else -1, i - w if y else -1, i + w if y < h - 1 else -1):
                if j >= 0 and not bg[j] and j not in band:
                    band.add(j)
                    nxt.append(j)
        frontier = nxt
    out, despilled, green_inside = [], 0, 0
    for y, row in enumerate(rows):
        orow = []
        for x, (r, g, b, al) in enumerate(row):
            i = y * w + x
            if bg[i]:
                orow.append((0, 0, 0, 0))
                continue
            lim = max(r, b)
            if g > lim:
                if i in band:
                    g = lim
                    despilled += 1
                elif is_key(r, g, b) or (g > lim + 40):
                    green_inside += 1
            orow.append((r, g, b, 255))
        out.append(orow)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    png.write_png(dst, w, h, out)
    return {"size": [w, h], "keyed_px": keyed, "grown_px": grown, "despilled_px": despilled,
            "green_inside_px": green_inside, "enclosed_key_px": enclosed, "opaque_px": w * h - keyed - grown}


def _touches(bg, i, w, h):
    y, x = divmod(i, w)
    return ((x and bg[i - 1]) or (x < w - 1 and bg[i + 1]) or (y and bg[i - w]) or (y < h - 1 and bg[i + w]))


def key_out(src, dst, tol=40):
    """Python cut: pixels near the corner colour become transparent."""
    w, h, rows = png.read_png(src)
    bg = rows[0][0][:3]
    out = []
    for row in rows:
        out.append([(0, 0, 0, 0) if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= tol or a == 0
                    else (r, g, b, 255) for r, g, b, a in row])
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    png.write_png(dst, w, h, out)


def cmd_clean(a, argv, root):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.via == "rembg":
        run(command("rembg") + ["i", "-m", a.rembg_model, a.inp, a.out])
        write_provenance(root, a.out, "rembg", inputs=[a.inp], origin="edited in jam",
                         note=f"rembg cut-out, model {a.rembg_model}", model=a.rembg_model)
        print(f"CLEAN {rel(a.out, root)} via=rembg model={a.rembg_model}")
        return 0
    if a.chroma:
        st = chroma_key(a.inp, a.out, a.chroma, grow=a.grow, hue_tol=a.hue_tol)
        write_provenance(root, a.out, "python", info=PY_TOOL, inputs=[a.inp], origin="edited in jam",
                         note=f"python HSV chroma key #{a.chroma.lstrip('#')}, mask grown {a.grow} px, despilled "
                              f"(tools/assetgen.py clean --chroma)")
        warn = ""
        if st["green_inside_px"]:
            warn += (f" WARN: {st['green_inside_px']} green px inside the subject (check our prompt: no green in the "
                     f"subject)")
        if st["enclosed_key_px"]:
            warn += (f" WARN: {st['enclosed_key_px']} key-colour px enclosed by the subject were cut: a real gap "
                     f"(arm and body) or green in the subject; look at the cut")
        print(f"CLEAN {rel(a.out, root)} via=chroma key=#{a.chroma.lstrip('#')} " +
              " ".join(f"{k}={v}" for k, v in st.items() if k != "size") + warn)
        return 0
    if have("gimpcli"):
        run(command("gimpcli") + ["clean", a.inp, a.out] + (["--xcf", a.xcf] if a.xcf else []))
        used = "gimpcli"
    elif have("gimp"):
        script = (f"img = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path({a.inp!r})); "
                  f"Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, img, Gio.File.new_for_path({a.out!r}), None)")
        run(command("gimp") + ["-i", "--batch-interpreter", "python-fu-eval", "-b", script, "-b", "Gimp.quit()"])
        key_out(a.out, a.out)
        used = "gimp"
    else:
        key_out(a.inp, a.out)
        used = "python"
    write_provenance(root, a.out, used, info=PY_TOOL if used == "python" else None, inputs=[a.inp],
                     origin="edited in jam",
                     note="python colour-key cut (no GIMP on PATH)" if used == "python" else "")
    print(f"CLEAN {rel(a.out, root)} via={used}")
    return 0


def _segments(occ, min_gap):
    """[(start, end)] runs of occupied indices, gaps shorter than min_gap bridged."""
    segs = []
    for i, v in enumerate(occ):
        if not v:
            continue
        if segs and i - segs[-1][1] <= min_gap:
            segs[-1][1] = i
        else:
            segs.append([i, i])
    return segs


def figure_boxes(src, count, min_gap=6, min_px=50, cells=False, inset=0):
    """The bounding boxes (x0, y0, x1, y1) of the `count` separate figures in a keyed strip, in strip order.
    cells=True: cut the strip into `count` equal cells instead of looking for gaps (figures that touch, or a strip
    the model drew inside boxes); `inset` px at every cell edge are dropped (the box lines)."""
    w, h, rows = png.read_png(src)
    vertical = h > w
    n_long = h if vertical else w
    if cells:
        n_short = w if vertical else h
        boxes = []
        for k in range(count):
            a0, a1 = k * n_long // count + inset, (k + 1) * n_long // count - 1 - inset
            xs, ys = [], []
            for y, row in enumerate(rows):
                for x, px in enumerate(row):
                    along, across = (y, x) if vertical else (x, y)
                    if px[3] and a0 <= along <= a1 and inset <= across < n_short - inset:
                        xs.append(x)
                        ys.append(y)
            if len(xs) < min_px:
                raise ValueError(f"{src}: cell {k + 1} of {count} is empty (the strip does not hold {count} poses)")
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
        return w, h, rows, boxes
    occ = [0] * n_long
    for y, row in enumerate(rows):
        for x, px in enumerate(row):
            if px[3]:
                occ[y if vertical else x] += 1
    segs = [s for s in _segments([c > 0 for c in occ], min_gap) if sum(occ[s[0]:s[1] + 1]) >= min_px]
    while len(segs) > count:   # bridge the narrowest gap (a loose umbrella tip, a stray drop)
        k = min(range(len(segs) - 1), key=lambda j: segs[j + 1][0] - segs[j][1])
        segs[k:k + 2] = [[segs[k][0], segs[k + 1][1]]]
    if len(segs) != count:
        raise ValueError(f"{src}: found {len(segs)} separate figures, wanted {count} (the figures touch or one is "
                         f"missing: check the prompt asks for {count} separated poses with a gap)")
    boxes = []
    for a0, a1 in segs:
        xs, ys = [], []
        for y, row in enumerate(rows):
            for x, px in enumerate(row):
                if px[3] and a0 <= (y if vertical else x) <= a1:
                    xs.append(x)
                    ys.append(y)
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
    return w, h, rows, boxes


def split_strip(src, count, min_gap=6, pad=8, frame=None, min_px=50, cells=False, inset=0,
                register=True, band=None, span_mode="base"):
    """Cut a keyed strip (transparent background) of `count` figures side by side (or stacked when the strip is
    taller than wide) into `count` equal frames. Each figure is placed bottom-centre on one baseline, then (register)
    registered by tools/frame_register.py: scaled about its anchor (bottom-centre of the lowest `band` mask rows) to
    the strip's median span and moved so every anchor sits on one pixel, which removes the frame-to-frame jitter a
    painted strip has. Returns (frames as (w, h, rows), stats); stats["anchor"] goes to the sidecar."""
    w, h, rows, boxes = figure_boxes(src, count, min_gap, min_px, cells=cells, inset=inset)
    bw = max(b[2] - b[0] + 1 for b in boxes)
    bh = max(b[3] - b[1] + 1 for b in boxes)
    fw, fh = frame or (bw + 2 * pad, bh + 2 * pad)
    if bw > fw or bh > fh:
        raise ValueError(f"{src}: the largest figure is {bw}x{bh}, larger than --frame {fw}x{fh}")
    frames = []
    for x0, y0, x1, y1 in boxes:
        cw, ch = x1 - x0 + 1, y1 - y0 + 1
        ox, oy = (fw - cw) // 2, fh - pad - ch if fh - pad - ch >= 0 else fh - ch
        out = [[(0, 0, 0, 0)] * fw for _ in range(fh)]
        for y in range(ch):
            src_row = rows[y0 + y]
            dst_row = out[oy + y]
            for x in range(cw):
                px = src_row[x0 + x]
                if px[3]:
                    dst_row[ox + x] = px
        frames.append((fw, fh, out))
    heights = [b[3] - b[1] + 1 for b in boxes]
    widths = [b[2] - b[0] + 1 for b in boxes]
    stats = {"frames": count, "frame": [fw, fh], "figure_heights": heights, "figure_widths": widths,
             "height_spread_pct": round(100.0 * (max(heights) - min(heights)) / max(heights), 1),
             "pivot": "bottom-centre", "cut": f"equal cells, inset {inset} px" if cells else "gaps"}
    if register:
        import frame_register as fr
        frames, info = fr.register(frames, band=band or fr.BAND, span_mode=span_mode)
        stats.update({"anchor": info["anchor"], "registration": {k: info[k] for k in ("span", "span_mode", "band", "frames")},
                      "jitter": fr.jitter(frames, band=band or fr.BAND, span_mode=span_mode)})
        edge = [i for i, (w_, h_, r_) in enumerate(frames)
                if any(px[3] for px in r_[0]) or any(px[3] for px in r_[-1])
                or any(row[0][3] or row[-1][3] for row in r_)]
        if edge:
            stats["registration"]["touches_edge"] = edge   # registration moved a figure into the frame edge: raise --pad
    return frames, stats


def cmd_frames(a, argv, root):
    frame = tuple(int(v) for v in a.frame.lower().split("x")) if a.frame else None
    try:
        frames, st = split_strip(a.inp, a.count, pad=a.pad, frame=frame, cells=a.cells, inset=a.inset,
                                 register=not a.no_register, band=a.anchor_band, span_mode=a.span)
    except ValueError as e:
        print(f"FAIL: frames: {e}")
        return 1
    os.makedirs(a.out_dir, exist_ok=True)
    stem = a.stem or os.path.splitext(os.path.basename(a.inp))[0]
    outs = []
    for i, (fw, fh, rows) in enumerate(frames):
        out = os.path.join(a.out_dir, f"{stem}_{i:02d}.png")
        png.write_png(out, fw, fh, rows)
        write_provenance(root, out, "python", info=PY_TOOL, inputs=[a.inp], origin="edited in jam",
                         note=f"frame {i} of {a.count} cut from the strip, bottom-centre pivot "
                              f"(tools/assetgen.py frames)")
        outs.append(rel(out, root))
    with open(os.path.join(a.out_dir, f"{stem}.frames.json"), "w", encoding="utf-8") as fh_:
        json.dump(dict(st, source=rel(a.inp, root), outputs=outs), fh_, indent=1)
        fh_.write("\n")
    print(f"FRAMES {a.count} from {rel(a.inp, root)} frame={st['frame'][0]}x{st['frame'][1]} "
          f"heights={st['figure_heights']} spread={st['height_spread_pct']}% -> {rel(a.out_dir, root)}")
    if "anchor" in st:
        print(f"REGISTERED anchor={st['anchor'][0]},{st['anchor'][1]} offset={st['jitter']['offset_px']:g}px "
              f"scale_drift={st['jitter']['scale_pct']:.1f}%" +
              (f" TOUCHES_EDGE frames {st['registration']['touches_edge']}: raise --pad"
               if st["registration"].get("touches_edge") else ""))
    return 0


def cmd_crop(a, argv, root):
    """One figure out of a painted sheet, on its own key-colour background: the image-model input for a strip (a
    whole sheet as the input makes the model copy the sheet's layout into the strip). The keyed sheet (--mask) finds
    the figure; the crop is taken from the unkeyed sheet (--in) so the model sees the same flat background."""
    try:
        _, _, _, boxes = figure_boxes(a.mask, a.count)
    except ValueError as e:
        print(f"FAIL: {e}")
        return 1
    if not 1 <= a.figure <= a.count:
        print(f"FAIL: --figure {a.figure} is not in 1..{a.count}")
        return 2
    w, h, rows = png.read_png(a.inp)
    mw, mh = png.read_png(a.mask)[:2]
    if (w, h) != (mw, mh):
        print(f"FAIL: --in is {w}x{h}, --mask is {mw}x{mh}: the mask must be the keyed copy of the same sheet")
        return 1
    x0, y0, x1, y1 = boxes[a.figure - 1]
    x0, y0, x1, y1 = max(0, x0 - a.pad), max(0, y0 - a.pad), min(w - 1, x1 + a.pad), min(h - 1, y1 + a.pad)
    out = [list(rows[y][x0:x1 + 1]) for y in range(y0, y1 + 1)]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    png.write_png(a.out, x1 - x0 + 1, y1 - y0 + 1, out)
    write_provenance(root, a.out, "python", info=PY_TOOL, inputs=[a.inp, a.mask], origin="edited in jam",
                     note=f"figure {a.figure} of {a.count} cropped from the sheet, box {x0},{y0},{x1},{y1} "
                          f"(tools/assetgen.py crop)")
    print(f"CROP {rel(a.out, root)} figure={a.figure}/{a.count} box={x0},{y0},{x1},{y1} "
          f"size={x1 - x0 + 1}x{y1 - y0 + 1}")
    return 0


def cmd_sheet(a, argv, root):
    frames = a.frames
    sizes = {png.read_png(f)[:2] for f in frames}
    if len(sizes) != 1:
        print(f"FAIL: frames differ in size: {sorted(sizes)}")
        return 1
    fw, fh = sizes.pop()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if have("aseprite"):
        data = os.path.splitext(a.out)[0] + ".aseprite.json"
        run(command("aseprite") + ["-b", *frames, "--sheet", a.out, "--data", data, "--format", "json-array",
                                   "--sheet-type", "horizontal"])
        used = "aseprite"
    else:
        strips = [png.read_png(f)[2] for f in frames]
        rows = [sum((s[y] for s in strips), []) for y in range(fh)]
        png.write_png(a.out, fw * len(frames), fh, rows)
        used = "python"
    side = {"kind": a.kind, "grid": [fw, fh], "frames": len(frames), "size": [fw, fh], "margin": 0, "spacing": 0,
            "loop": True, "anim": a.anim, "fps": a.fps}
    for f in frames:   # the anchor `frames` registered the strip on (<stem>.frames.json beside the cut frames)
        rec = os.path.join(os.path.dirname(f), re.sub(r"_\d+$", "", os.path.splitext(os.path.basename(f))[0]) + ".frames.json")
        if os.path.isfile(rec):
            with open(rec, encoding="utf-8") as fh_:
                j = json.load(fh_)
            if "anchor" in j:
                side["anchor"] = j["anchor"]
                side["anchor_band"] = j["registration"]["band"]
                side["span_mode"] = j["registration"]["span_mode"]
        break
    with open(os.path.splitext(a.out)[0] + ".sprite.json", "w", encoding="utf-8") as fh_:
        json.dump(side, fh_, indent=2)
        fh_.write("\n")
    write_provenance(root, a.out, "aseprite", inputs=frames, origin="assembled in jam",
                     note="python strip (no Aseprite on PATH)" if used == "python" else "")
    print(f"SHEET {rel(a.out, root)} frames={len(frames)} grid={fw}x{fh} via={used}")
    return 0


def cmd_blender(a, argv, root):
    if a.script:   # any other Blender script, headless
        if not a.out:
            print("FAIL: blender --script needs --out")
            return 2
        run(command("blender") + ["-b", "-P", a.script, "--", "--out", a.out] + a.rest)
        write_provenance(root, a.out, "blender", inputs=[a.script], origin="rendered in jam")
        print(f"BLENDER {rel(a.out, root)}")
        return 0
    if not (a.character and a.anim):
        print("FAIL: blender needs --character and --anim (a recipe row in pipeline/art/blender/characters.json), "
              "or --script")
        return 2
    plan = blender_plan()
    ch = (plan.recipes(root).get("characters") or {}).get(a.character) or {}
    out_dir = (a.out_dir or f"Art/Source/{ch.get('asset') or a.character.title()}/Raw/{a.anim}").replace(os.sep, "/")
    try:
        j, frames, _ = render(a, root, a.character, a.anim, out_dir, frames=a.frames)
    except ToolMissing as e:
        j = plan.job(a.character, a.anim, out_dir, root=root, frames=a.frames, seed=a.seed)
        frames = j["frames"]
        for f in frames:
            placeholder(root, f, j["frame_size"][0], j["frame_size"][1], plan.describe(j), f"no Blender: {e}")
        print("NOTE: no Blender: these frames are labelled placeholders; the art loop and the ship gates refuse "
              "them. Install Blender (or set BLENDER=<path>) and render again")
    if a.sheet:
        if len(frames) < 2:
            print(f"FAIL: {a.character} {a.anim} is a still, not a sheet: use its frame (tools/assetgen.py image)")
            return 2
        return cmd_sheet(argparse.Namespace(frames=frames, out=a.sheet, anim=a.anim, fps=j["fps"],
                                            kind="silhouette"), argv, root)
    return 0


# ---------- audio ----------
def synth_wav(path, seconds, seed_text, rate=48000):
    """Procedural fallback: filtered noise with a decaying envelope (one-shot), peak -3 dBFS, silent tail."""
    rnd = random.Random(seed_text)
    n = int(seconds * rate)
    tail = int(0.01 * rate)
    frames, prev = bytearray(), 0.0
    for i in range(n):
        env = math.exp(-4.0 * i / max(n, 1)) if i < n - tail else 0.0
        prev = 0.9 * prev + 0.1 * rnd.uniform(-1, 1)
        v = int(max(-1.0, min(1.0, prev * 5 * env)) * 0.7 * 32767)
        frames += struct.pack("<h", v)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def to_wav(src_bytes, ext, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = out + ext
    with open(tmp, "wb") as fh:
        fh.write(src_bytes)
    try:
        run(command("ffmpeg") + ["-y", "-i", tmp, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", out])
    finally:
        os.remove(tmp)


KEY_NOTE = ("NOTE: no audio API key (ELEVENLABS_API_KEY or STABILITY_API_KEY): this is a procedural placeholder and will "
            "not pass the style bar. Set one audio key on the build machine (tools/keys.py); the jam perks include no "
            "audio tool")


def api_error(e):
    """One line for an audio API failure: the HTTP status and the vendor's message (e.g. ElevenLabs
    `quota_exceeded` when the credits ran out), never the key or the request body."""
    code = getattr(e, "code", None)
    msg = getattr(e, "_assetgen_body", None)   # read once: the second call (counter, then the FAIL line) sees it too
    if msg is None:
        try:
            msg = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        except Exception:   # noqa: BLE001  the body is a courtesy; the status is enough
            msg = ""
        try:
            e._assetgen_body = msg
        except Exception:   # noqa: BLE001
            pass
    msg = re.sub(r"\s+", " ", msg or str(e)).strip()
    return (f"HTTP {code} " if code else f"{type(e).__name__} ") + msg[:400]


def audio_placeholder(a, root, sid, reason):
    """A tracked placeholder take: procedural audio in place of the API take, so the run goes on. Its provenance
    origin says `placeholder: <reason>` (tools/audio_check.py --placeholders lists it, --release fails it, the MVP 15
    audio card regenerates it)."""
    synth_wav(a.out, a.seconds, a.prompt)
    reason = re.sub(r"[\r\n,]+", " ", reason).strip()[:160]
    write_provenance(root, a.out, "synth", a.prompt, "none", origin="synthesized in jam", note=f"placeholder: {reason}")
    print(f"PLACEHOLDER {rel(a.out, root)} sound={sid} seconds={a.seconds}: {reason} (tracked: "
          "tools/audio_check.py --placeholders; regenerate it with an audio API key)")
    if reason.startswith("no audio API key"):
        print(KEY_NOTE)
    return 0


def audio_prompt(a, root):
    """(sound id, prompt, seconds) from pipeline/audio/style.json and the sound list. Raises ValueError."""
    import audio_check
    import audio_style_check
    sid = a.sound
    if not sid:
        m = audio_style_check.NAME.match(os.path.basename(a.out))
        sid = m.group(1) if m else None
    if not sid:
        raise ValueError("name the sound (--sound <Id>, or an --out named SW_<Id>_<NN>.wav): audio prompts come from "
                         "pipeline/audio/style.json")
    base = root if os.path.isfile(os.path.join(root, "pipeline", "audio", "style.json")) else ROOT
    style = audio_style_check.load_style(os.path.join(base, "pipeline", "audio", "style.json"))
    rows = audio_check.load_list(os.path.join(base, "pipeline", "audio", "sound-list.csv"))
    prompt, secs = audio_style_check.build_prompt(sid, style, rows, a.prompt or "")
    return sid, prompt, a.seconds if a.seconds else float(secs or (2.0 if a.cmd == "sfx" else 30.0))


def supplied_block(sid, root):
    """A reason not to generate sid: a teammate supplied it (a supplied take, or a file waiting in Audio/Import/)."""
    import audio_import
    if sid in audio_import.supplied_ids(root):
        return f"{sid} has a supplied take (provenance origin supplied)"
    try:
        _, rows = audio_import.ctx(root if os.path.isfile(os.path.join(root, "pipeline", "audio", "style.json")) else ROOT)
    except (OSError, ValueError):
        return None
    got, _ = audio_import.matches(os.path.join(root, "Audio", "Import"), rows)
    waiting = [f for f, i in got.items() if i == sid]
    return f"{sid} has a supplied file waiting in Audio/Import/ ({waiting[0]})" if waiting else None


def cmd_audio(a, argv, root, music=False):
    try:
        sid, a.prompt, a.seconds = audio_prompt(a, root)
    except ValueError as e:
        print(f"FAIL: {a.cmd}: {e}")
        return 2
    why = supplied_block(sid, root)
    if why:
        print(f"FAIL: {a.cmd}: {why}. Supplied sounds are processed (tools/audio_import.py apply), not replaced by "
              "generated ones; only a row with no supplied file is generated. If the supplied take cannot reach the bar, "
              "the loop's stuck rule hands it to the audio owner")
        return 2
    provider = a.provider
    if provider == "auto":
        provider = "elevenlabs" if keys.get("ELEVENLABS_API_KEY") else (
            "stable-audio" if keys.get("STABILITY_API_KEY") else None)
        if provider is None:
            if os.environ.get("JAM_OUTBOX") and not os.environ.get("ASSETGEN_FULFIL"):
                queue_or_key(argv, "ELEVENLABS_API_KEY")
            return audio_placeholder(a, root, sid, "no audio API key (ELEVENLABS_API_KEY or STABILITY_API_KEY)")
    if provider == "synth":
        synth_wav(a.out, a.seconds, a.prompt)
        write_provenance(root, a.out, "synth", a.prompt, "none", origin="synthesized in jam")
        print(f"SYNTH {rel(a.out, root)} sound={sid} seconds={a.seconds}")
        print(KEY_NOTE)
        return 0
    try:
        if provider == "elevenlabs":
            tid = "elevenlabs-music" if music else "elevenlabs-sfx"
            k = queue_or_key(argv, "ELEVENLABS_API_KEY")
            t = tool(tid)
            body = ({"prompt": a.prompt, "music_length_ms": int(a.seconds * 1000)} if music
                    else {"text": a.prompt, "duration_seconds": a.seconds})
            raw = http_post(t["endpoint"], {"xi-api-key": k or "", "Content-Type": "application/json"},
                            json.dumps(body).encode())
            to_wav(raw, ".mp3", a.out)
        else:
            tid = "stable-audio"
            k = queue_or_key(argv, "STABILITY_API_KEY")
            t = tool(tid)
            raw = http_post(t["endpoint"], {"Authorization": f"Bearer {k or ''}", "Accept": "audio/*",
                                            "Content-Type": "application/json"},
                            json.dumps({"prompt": a.prompt, "duration": a.seconds, "output_format": "wav"}).encode())
            to_wav(raw, ".wav.src", a.out)
    except Exception as e:   # an HTTP error, no credits left, a network or decode failure: never stop the run
        return audio_placeholder(a, root, sid, f"{provider} failed: {api_error(e)}")
    write_provenance(root, a.out, tid, a.prompt, t.get("model", ""))
    print(f"AUDIO {rel(a.out, root)} sound={sid} via={tid} seconds={a.seconds}")
    return 0


def python_trim(src, dst, start, duration, fade_ms):
    with wave.open(src, "rb") as r:
        p = r.getparams()
        r.setpos(min(int(start * p.framerate), p.nframes))
        n = p.nframes if duration is None else int(duration * p.framerate)
        data = r.readframes(n)
    if p.sampwidth == 2 and fade_ms:
        k = int(fade_ms / 1000 * p.framerate) * p.nchannels
        vals = list(struct.unpack(f"<{len(data) // 2}h", data))
        for i in range(min(k, len(vals))):
            vals[-1 - i] = int(vals[-1 - i] * i / k)
        data = struct.pack(f"<{len(vals)}h", *vals)
    with wave.open(dst, "wb") as w:
        w.setparams(p)
        w.writeframes(data)


def cmd_edit(a, argv, root):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp.wav"
    if have("ffmpeg"):
        filt = [f"atrim=start={a.start}" + (f":duration={a.duration}" if a.duration else ""), "asetpts=N/SR/TB"]
        if a.fade_ms:
            filt.append(f"areverse,afade=t=in:d={a.fade_ms / 1000},areverse")
        filt.append(f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11")
        run(command("ffmpeg") + ["-y", "-i", a.inp, "-af", ",".join(filt), "-ar", "48000", "-c:a", "pcm_s16le", tmp])
        used = "ffmpeg"
    elif have("sox"):
        args = command("sox") + [a.inp, tmp, "trim", str(a.start)] + ([str(a.duration)] if a.duration else [])
        if a.fade_ms:
            args += ["fade", "t", "0", "-0", str(a.fade_ms / 1000)]
        run(args + ["norm", "-1"])
        used = "sox"
    else:
        python_trim(a.inp, tmp, a.start, a.duration, a.fade_ms)
        used = "python"
    os.replace(tmp, a.out)
    prior = audio_prov(root, a.inp)
    held = placeholder_reason(root, a.inp)   # an edited placeholder take stays a tracked placeholder
    write_provenance(root, a.out, prior or ("ffmpeg" if used == "python" else used), inputs=[a.inp],
                     origin="generated in jam" if prior else "edited in jam",
                     note=f"trimmed and normalised with {used}" + (f"; placeholder: {held}" if held else ""))
    print(f"EDIT {rel(a.out, root)} via={used}")
    return 0


def placeholder_reason(root, src):
    """The `placeholder: <reason>` of the source's provenance row (a tracked placeholder take), else None."""
    path = os.path.join(root, PROVENANCE)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("asset_path") == rel(src, root):
                m = re.search(r"\bplaceholder:\s*(.+)$", r.get("origin") or "", re.I)
                return m.group(1).strip() if m else None
    return None


def audio_prov(root, src):
    """The tool id of the source's provenance row, so an edited take keeps its generator's licence."""
    path = os.path.join(root, PROVENANCE)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("asset_path") == rel(src, root):
                for t in inventory()["tools"]:
                    if t["name"] == r.get("tool"):
                        return t["id"]
    return None


# ---------- video, zip ----------
def capture_input():
    import platform
    s = platform.system()
    if s == "Windows":
        return ["-f", "gdigrab", "-framerate", "60", "-i", "desktop"]
    if s == "Darwin":
        return ["-f", "avfoundation", "-framerate", "60", "-i", "1:0"]
    return ["-f", "x11grab", "-framerate", "60", "-i", os.environ.get("DISPLAY", ":0")]


def cmd_capture(a, argv, root):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    game = subprocess.Popen([a.exe] + shlex.split(a.args or ""), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if a.via == "obs":
            obs = command("obs")
            run(obs + ["recording", "start"])
            time.sleep(a.seconds)
            run(obs + ["recording", "stop"])
            folder = os.environ.get("OBS_RECORDING_DIR") or ""
            files = sorted((os.path.join(folder, f) for f in os.listdir(folder)), key=os.path.getmtime) if folder else []
            if not files:
                print("FAIL: OBS saved no recording; set OBS_RECORDING_DIR to OBS's recording folder")
                return 1
            shutil.move(files[-1], a.out)
        else:
            run(command("ffmpeg") + ["-y"] + capture_input() + ["-t", str(a.seconds), "-c:v", "libx264", "-preset",
                                                                  "ultrafast", "-pix_fmt", "yuv420p", a.out])
    finally:
        game.terminate()
    print(f"CAPTURE {rel(a.out, root)} via={a.via} seconds={a.seconds}")
    return 0


def cmd_cut(a, argv, root):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=60"
    run(command("ffmpeg") + ["-y", "-ss", str(a.start), "-i", a.inp, "-t", str(a.duration), "-vf", vf,
                             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", a.out])
    print(f"CUT {rel(a.out, root)} duration={a.duration} 1920x1080; next: submission_check.py video and loudness")
    return 0


def cmd_zip(a, argv, root):
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if os.path.exists(a.out):
        os.remove(a.out)
    if have("7zip"):
        run(command("7zip") + ["a", "-tzip", os.path.abspath(a.out), "."], cwd=a.dir)
        used = "7zip"
    else:
        with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
            for d, _, fs in os.walk(a.dir):
                for f in fs:
                    full = os.path.join(d, f)
                    z.write(full, os.path.relpath(full, a.dir))
        used = "python"
    print(f"ZIP {a.out} via={used}; next: submission_check.py zip {a.out}")
    return 0


# ---------- kickoff ----------
def cmd_fulfil(a, argv, root):
    """Run every queued request in OUTBOX with the keys of this (kickoff) process. Writes asset-results.json."""
    path = os.path.join(a.outbox, "asset-requests.jsonl")
    results = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            reqs = [json.loads(ln) for ln in fh if ln.strip()]
        for r in reqs:
            env = dict(os.environ, ASSETGEN_FULFIL="1")
            if r.get("role"):
                env["JAM_ROLE"] = r["role"]
            p = subprocess.run([sys.executable, os.path.abspath(__file__), *r["argv"]], cwd=r.get("cwd") or root,
                               capture_output=True, text=True, env=env)
            results.append({"argv": r["argv"], "exit": p.returncode, "out": (p.stdout + p.stderr).strip()[-400:]})
            print(f"FULFIL exit={p.returncode} {' '.join(r['argv'][:3])}: {(p.stdout or p.stderr).strip()[-200:]}")
        os.replace(path, path + ".done")
    with open(os.path.join(a.outbox, "asset-results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    return 1 if any(r["exit"] for r in results) else 0


# ---------- video mode (artvideo trial): image-to-video on fal, Veo only ----------
# Checked against fal's live model page (GET https://api.fal.ai/v1/models?endpoint_id=..., free) on Nov 13: fal-ai/veo3,
# veo3/fast and veo2 image-to-video are "deprecated"; fal-ai/veo3.1/{,fast/,lite/}image-to-video are "active". Live prices
# (GET /v1/models/pricing, key header, free): 0.40 / 0.15 / 0.05 USD per second. Fast is the fixed model. Anything else is refused.
FAL_VIDEO_MODEL = "fal-ai/veo3.1/fast/image-to-video"
FAL_QUEUE = "https://queue.fal.run/"
FAL_API = "https://api.fal.ai/v1/"
FAL_PRICE_FALLBACK = 0.15       # USD per second, used only when the live price cannot be read
FAL_VIDEO_SECONDS = 4           # fal's shortest Veo 3.1 clip (4s, 6s, 8s); the trial uses its first ~2 s
FAL_VIDEO_PIECE_CAP_USD = 1.00  # per-piece cap of a video piece, inside the shared IMAGE_SPEND_CAP_USD counter
FAL_POLL_SECONDS = 5
FAL_POLL_TRIES = 120
FAL_INFO = {"name": "fal.ai (Google Veo 3.1 Fast, image-to-video)",
            "licence": "fal.ai Terms of Service; output of Google Veo: Google generative AI terms (commercial use allowed on fal; "
                       "SynthID watermark)"}
VIDEO_PROMPT_SUFFIX = (" Flat solid chroma green background (pure #00FF00), the whole frame outside the character stays that "
                       "one green, no floor, no shadows, no gradient, no text. Static locked camera, no zoom, no pan, no cut. "
                       "The character stays in place and keeps her size; only a small gentle idle movement. No sound.")
VIDEO_NEGATIVE = "camera movement, zoom, cut, text, subtitles, logo, background scenery, shadows on the background, people other than the character, sound"


def fal_video_model(model):
    if model != FAL_VIDEO_MODEL:
        raise ImageRefused(f"VIDEO MODEL REFUSED: {model!r} is not the fixed video model {FAL_VIDEO_MODEL}; no fallback")
    return model


def _fal_get_json(url, key=None):
    hdr = {"Authorization": f"Key {key}"} if key else {}
    return json.loads(http_get(url, hdr))


def fal_live_check(model, key):
    """(unit USD per second, status) from fal's live pages. ImageRefused when the endpoint is not active."""
    try:
        d = _fal_get_json(f"{FAL_API}models?endpoint_id={model}")
        status = ((d.get("models") or [{}])[0].get("metadata") or {}).get("status")
    except Exception as e:   # noqa: BLE001
        raise ImageRefused(f"the model page could not be read ({e}); no call made")
    if status != "active":
        raise ImageRefused(f"VIDEO MODEL NOT ACTIVE: fal lists {model} as {status!r}; no call made")
    try:
        d = _fal_get_json(f"{FAL_API}models/pricing?endpoint_id={model}", key)
        price = float(d["prices"][0]["unit_price"])
    except Exception:   # noqa: BLE001
        price = FAL_PRICE_FALLBACK
    return price, status


def fal_video_request(model, prompt, image_path, seed, key):
    """Submit, poll, return (mp4 bytes, reply dict). Audio off. The key only goes in the Authorization header."""
    import base64
    hdr = {"Authorization": f"Key {key}", "Content-Type": "application/json"}
    uri = "data:image/png;base64," + base64.b64encode(open(image_path, "rb").read()).decode()
    body = {"prompt": prompt, "image_url": uri, "duration": f"{FAL_VIDEO_SECONDS}s", "generate_audio": False,
            "resolution": "720p", "aspect_ratio": "16:9", "negative_prompt": VIDEO_NEGATIVE, "seed": seed,
            "auto_fix": False}
    sub = json.loads(http_post(FAL_QUEUE + model, hdr, json.dumps(body).encode()))
    status_url, result_url = sub["status_url"], sub["response_url"]
    for _ in range(FAL_POLL_TRIES):
        st = json.loads(http_get(status_url, hdr))
        if st.get("status") == "COMPLETED":
            break
        if st.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"fal status {st.get('status')}: {str(st)[:200]}")
        if not os.environ.get("ASSETGEN_HTTP_STUB"):
            time.sleep(FAL_POLL_SECONDS)
    else:
        raise RuntimeError("fal: the video was not ready in time (cost kept: it may be billed)")
    res = json.loads(http_get(result_url, hdr))
    vurl = (res.get("video") or {}).get("url")
    if not vurl:
        raise RuntimeError(f"fal: no video in the reply: {str(res)[:200]}")
    return http_get(vurl, {}), {"request_id": sub.get("request_id"), "video": {k: v for k, v in res["video"].items() if k != "url"}}


def cmd_video(a, argv, root):
    try:
        return cmd_video_model(a, argv, root)
    except ImageRefused as e:
        print(f"REFUSED: video: {e}")
        return 2


def cmd_video_model(a, argv, root):
    """One paid image-to-video clip. Order: model fixed, input guarded, key, live price, cap reserved, call, provenance."""
    fal_video_model(a.model or FAL_VIDEO_MODEL)
    piece = (a.piece or "").strip()
    if not piece:
        raise ImageRefused("PIECE REQUIRED: every paid video call names its piece (--piece <id>); no call made")
    why = refuse_prejam_input(root, a.input)
    if why:
        raise ImageRefused(f"PRE-JAM INPUT REFUSED: {why}. GDD ART-03: only in-jam images we made may be inputs")
    k = keys.get("FAL_KEY")
    if not k:
        raise ImageRefused("NO KEY: FAL_KEY is not set, so no video was made")
    price, _ = fal_live_check(FAL_VIDEO_MODEL, k)
    cost = round(price * FAL_VIDEO_SECONDS, 6)
    seed = a.seed if a.seed is not None else 7
    prompt = a.prompt.strip() + VIDEO_PROMPT_SUFFIX
    entry = {"provider": "fal", "model": FAL_VIDEO_MODEL, "kind": "video", "out": rel(a.out, root), "inputs": 1,
             "piece": piece, "root": root, "piece_cap": FAL_VIDEO_PIECE_CAP_USD, "worker": os.path.basename(root),
             "role": os.environ.get("JAM_ROLE"), "seconds": FAL_VIDEO_SECONDS, "unit_usd_per_s": price}
    idx, spent, cap = spend_reserve(cost, entry)
    try:
        data, meta = fal_video_request(FAL_VIDEO_MODEL, prompt, a.input, seed, k)
    except Exception as e:   # noqa: BLE001
        code = getattr(e, "code", None)
        refused = isinstance(code, int) and 400 <= code < 500   # rejected before generation: not billed
        spent = spend_settle(idx, "failed", refund=refused, error=api_error(e) if code else str(e)[:200])
        print(f"FAIL: video fal {FAL_VIDEO_MODEL}: {api_error(e) if code else e}; counter ${spent:.3f} of ${cap:.2f}"
              + (" (refunded: the provider refused the request)" if refused else " (cost kept: it may be billed)"))
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as fh:
        fh.write(data)
    spent = spend_settle(idx, "done", cost=cost, model_version=FAL_VIDEO_MODEL)
    req = os.path.splitext(a.out)[0] + ".request.json"
    with open(req, "w", encoding="utf-8") as fh:
        json.dump({"provider": "fal", "model": FAL_VIDEO_MODEL, "prompt": prompt, "negative_prompt": VIDEO_NEGATIVE,
                   "seed": seed, "duration_s": FAL_VIDEO_SECONDS, "generate_audio": False, "resolution": "720p",
                   "aspect_ratio": "16:9", "input_image": rel(a.input, root), "unit_usd_per_s": price,
                   "cost_usd": cost, "reply": meta, "date": now_iso()}, fh, indent=1)
        fh.write("\n")
    write_provenance(root, a.out, "fal-video", prompt, FAL_VIDEO_MODEL, inputs=[a.input], origin="generated in jam",
                     info=FAL_INFO, seed=seed,
                     note=f"video model fal {FAL_VIDEO_MODEL}, {FAL_VIDEO_SECONDS} s, audio off; ${cost:.3f} counted against the "
                          f"shared image cap; full request in {rel(req, root)}")
    log_image_prompt(root, prompt, "fal", FAL_VIDEO_MODEL, a.out, cost)
    print(f"VIDEO {rel(a.out, root)} via=fal model={FAL_VIDEO_MODEL} {len(data)} bytes seed={seed} cost=${cost:.3f} "
          f"spent=${spent:.3f} of ${cap:.2f}")
    return 0


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("image")
    p.add_argument("--prompt", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--size", default="1024x1024")
    p.add_argument("--provider", choices=("gemini", "openai", "openrouter", "fal", "blender", "placeholder", "reference"),
                   default="gemini")
    p.add_argument("--tier", choices=tuple(IMAGE_TIERS), default="draft",
                   help="draft: gemini-2.5-flash-image (cheap); final: gemini-3-pro-image-preview (art_loop final candidates)")
    p.add_argument("--input", action="append", help="an in-jam image of ours as an image-model input (repeatable; "
                   "pre-jam images are refused)")
    p.add_argument("--model", help="image model (default: the provider's model in asset-tools.json)")
    p.add_argument("--piece", help="the art piece id this paid call is for (required for every paid image call)")
    p.add_argument("--from-draft", dest="from_draft", help="--tier final: the draft file of this piece whose checks passed")
    p.add_argument("--quality", default="medium", choices=("low", "medium", "high"), help="openai quality")
    p.add_argument("--aspect", help="gemini aspect ratio, e.g. 1:1, 16:9, 4:1 (default: nearest to --size)")
    p.add_argument("--image-size", choices=GEMINI_IMAGE_SIZES, help="gemini 3.x output size (required for them)")
    p.add_argument("--element", choices=tuple(ELEMENT_ROLE))
    p.add_argument("--character", help="a recipe in pipeline/art/blender/characters.json (default: by element)")
    p.add_argument("--anim", help="the recipe row (default: Still, else the first)")
    p.add_argument("--seed", type=int)
    p = sub.add_parser("video")
    p.add_argument("--prompt", required=True, help="how the still moves; the chroma-green background text is added")
    p.add_argument("--input", required=True, help="an in-jam still of ours (pre-jam images are refused)")
    p.add_argument("--out", required=True)
    p.add_argument("--piece", help="the video piece id (its own 1 USD cap in the shared counter)")
    p.add_argument("--model", help=f"only {FAL_VIDEO_MODEL} is accepted")
    p.add_argument("--seed", type=int)
    p = sub.add_parser("batch")
    p.add_argument("--jobs", required=True, help="JSON list; each job is one `image` argument list (paid providers only)")
    p.add_argument("--workers", type=int, default=BATCH_MAX_WORKERS, help="concurrent calls, at most 4")
    p = sub.add_parser("clean")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--xcf")
    p.add_argument("--chroma", help="HSV chroma key on this hex colour (e.g. 00FF00): key, grow the mask, despill")
    p.add_argument("--grow", type=int, default=2, help="px the background mask grows into the subject (1-2)")
    p.add_argument("--hue-tol", type=float, default=40.0, help="degrees of hue around the key colour")
    p.add_argument("--via", choices=("auto", "rembg"), default="auto", help="rembg: the fallback cut-out")
    p.add_argument("--rembg-model", default="birefnet-general")
    p = sub.add_parser("frames")
    p.add_argument("--in", dest="inp", required=True, help="a keyed strip (transparent background)")
    p.add_argument("--count", type=int, required=True, help="figures in the strip (2-4 per state)")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--frame", help="WxH of every frame (default: the largest figure plus --pad)")
    p.add_argument("--pad", type=int, default=8)
    p.add_argument("--stem")
    p.add_argument("--cells", action="store_true",
                   help="cut into --count equal cells (thirds for 3), not at gaps: touching figures or a boxed strip")
    p.add_argument("--inset", type=int, default=0, help="with --cells: px dropped at every cell edge (box lines)")
    p.add_argument("--no-register", action="store_true", help="skip frame registration (tools/frame_register.py)")
    p.add_argument("--anchor-band", type=int, help="rows of the lowest mask part that make the anchor (default 8; "
                   "a tall umbrella handle or long skirt may want more)")
    p.add_argument("--span", default="base", help="what stands for scale: base (default), height, width or a row count")
    p = sub.add_parser("image-models")
    p = sub.add_parser("crop")
    p.add_argument("--in", dest="inp", required=True, help="the painted sheet (key-colour background)")
    p.add_argument("--mask", required=True, help="the keyed copy of the same sheet (clean --chroma)")
    p.add_argument("--count", type=int, required=True, help="separate items on the sheet")
    p.add_argument("--figure", type=int, required=True, help="which one, 1-based, left to right")
    p.add_argument("--out", required=True)
    p.add_argument("--pad", type=int, default=24)
    p = sub.add_parser("sheet")
    p.add_argument("--frames", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--anim", required=True)
    p.add_argument("--fps", type=float, required=True)
    p.add_argument("--kind", default="silhouette")
    p = sub.add_parser("blender")
    p.add_argument("--character", help="a recipe in pipeline/art/blender/characters.json")
    p.add_argument("--anim", help="its row: the <Anim> of the flipbook")
    p.add_argument("--out-dir", help="default Art/Source/<Asset>/Raw/<Anim> (must be under a Raw/ folder)")
    p.add_argument("--frames", type=int, help="default: the recipe row's count")
    p.add_argument("--seed", type=int, help="default: the recipe look's seed (same seed, same paper grain)")
    p.add_argument("--sheet", help="then assemble Art/Sprites/<Asset>/<name>.png from the frames")
    p.add_argument("--script", help="any other Blender script, run headless with -- --out OUT")
    p.add_argument("--out")
    p.add_argument("rest", nargs=argparse.REMAINDER)
    for name in ("sfx", "music"):
        p = sub.add_parser(name)
        p.add_argument("--sound", help="sound-list id; the prompt comes from its style family in pipeline/audio/style.json")
        p.add_argument("--prompt", default="", help="a revision added to the style prompt (e.g. the critic's gap)")
        p.add_argument("--out", required=True)
        p.add_argument("--seconds", type=float, help="default: the style family's length")
        p.add_argument("--provider", choices=("auto", "elevenlabs", "stable-audio", "synth"), default="auto")
    p = sub.add_parser("edit")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--duration", type=float)
    p.add_argument("--fade-ms", type=float, default=5.0)
    p.add_argument("--lufs", type=float, default=-14.0)
    p = sub.add_parser("capture")
    p.add_argument("--exe", required=True)
    p.add_argument("--seconds", type=float, default=60.0)
    p.add_argument("--out", required=True)
    p.add_argument("--via", choices=("ffmpeg", "obs"), default="ffmpeg")
    p.add_argument("--args", default="")
    p = sub.add_parser("cut")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--duration", type=float, default=45.0)
    p = sub.add_parser("zip")
    p.add_argument("--dir", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("fulfil")
    p.add_argument("--outbox", required=True)
    return ap


CMDS = {"image": cmd_image, "video": cmd_video, "batch": cmd_batch, "clean": cmd_clean, "sheet": cmd_sheet, "blender": cmd_blender,
        "frames": cmd_frames, "image-models": cmd_image_models, "crop": cmd_crop,
        "sfx": lambda a, v, r: cmd_audio(a, v, r), "music": lambda a, v, r: cmd_audio(a, v, r, music=True),
        "edit": cmd_edit, "capture": cmd_capture, "cut": cmd_cut, "zip": cmd_zip, "fulfil": cmd_fulfil}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    a = parser().parse_args(argv)
    if a.cmd == "cut" and not (30 <= a.duration <= 60):
        print("FAIL: the gameplay video is 30-60 s (Official Rules 1(e)); pass --duration between 30 and 60")
        return 2
    try:
        return CMDS[a.cmd](a, argv, repo_root())
    except ToolMissing as e:
        print(f"NOT CONNECTED: {e} (tools/connections.py lists every tool)")
        return 2
    except (RuntimeError, OSError, ValueError, KeyError) as e:
        print(f"FAIL: {a.cmd}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

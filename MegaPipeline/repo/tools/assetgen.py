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
  image   --prompt P --out Art/Source/<name>.png [--element owl|character|effects|background|frame]
          [--character <id>] [--anim <Anim>] [--provider blender|placeholder|reference]
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

API steps (audio only; art needs no key) need a key (tools/keys.py: env or OS keychain). Inside an agent session
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


def write_provenance(root, out, tid, prompt="", model="", inputs=(), origin="generated in jam", note="", info=None,
                     seed=""):
    """Add or replace the row for `out` (one row per asset path). info: {name, licence} for a source that is not
    an asset-tools.json tool (the team's reference art in a practice repo)."""
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
    tid = "gimp" if used == "python" else used
    write_provenance(root, a.out, tid, inputs=[a.inp], origin="edited in jam",
                     note="python colour-key cut (no GIMP on PATH)" if used == "python" else "")
    print(f"CLEAN {rel(a.out, root)} via={used}")
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
    msg = ""
    try:
        msg = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
    except Exception:   # noqa: BLE001  the body is a courtesy; the status is enough
        msg = ""
    msg = re.sub(r"\s+", " ", msg or str(e)).strip()
    return (f"HTTP {code} " if code else f"{type(e).__name__} ") + msg[:120]


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


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("image")
    p.add_argument("--prompt", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--size", default="1024x1024")
    p.add_argument("--provider", choices=("blender", "placeholder", "reference"), default="blender")
    p.add_argument("--element", choices=tuple(ELEMENT_ROLE))
    p.add_argument("--character", help="a recipe in pipeline/art/blender/characters.json (default: by element)")
    p.add_argument("--anim", help="the recipe row (default: Still, else the first)")
    p.add_argument("--seed", type=int)
    p = sub.add_parser("clean")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--xcf")
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


CMDS = {"image": cmd_image, "clean": cmd_clean, "sheet": cmd_sheet, "blender": cmd_blender,
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

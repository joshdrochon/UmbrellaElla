#!/usr/bin/env python3
"""Render jobs for the Blender stand-ins (stdlib only; tools/assetgen.py blender and the tests import it).

A job is everything render_sprite.py needs, so the Blender side reads no repo file itself:
  character, anim, builder, frame size, pivot (pixel the rig's origin lands on), facing, px_per_unit, fps, loop,
  one pose per frame, the colours (style.json palette + accents by name), the look, the output names.
Sources (pipeline/art/blender/characters.json `_about`): the recipe row, the references.json `layout` entry it names
(SpriteLayout.json: frame_size, pivot_px, faces, fps), the style.json `anims` row (fps and allowed frame count).
A recipe that disagrees with them (a frame count the art bible does not allow, an unknown layout sheet) is refused.

  python3 pipeline/art/blender/plan.py --character owl --anim Flap --out-dir Art/Source/Owl/Raw/Flap   print the job
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RECIPES = os.path.join("pipeline", "art", "blender", "characters.json")
SCRIPT = os.path.join("pipeline", "art", "blender", "render_sprite.py")
# render_sprite.py prints this once per job: the version goes into provenance, the rest into the step's output
RENDER_LINE = re.compile(r"^BLENDER_RENDER version=(?P<version>\S+) frames=(?P<frames>\d+) blend=(?P<blend>\S+)"
                         r"(?: freestyle=(?P<freestyle>\w+))?(?: compositor=(?P<compositor>\w+))?", re.M)


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def recipes(root=REPO):
    p = os.path.join(root, RECIPES)
    return _load(p if os.path.isfile(p) else os.path.join(REPO, RECIPES))


def style(root=REPO):
    p = os.path.join(root, "pipeline", "art", "style.json")
    return _load(p if os.path.isfile(p) else os.path.join(REPO, "pipeline", "art", "style.json"))


def layout_sheets(root=REPO):
    """{sheet name: layout row} from every references.json `layout` entry that is a JSON file in this checkout."""
    sys.path.insert(0, os.path.join(REPO, "tools"))
    out = {}
    try:
        import art_check
        spec = art_check.load_spec(root if os.path.isfile(os.path.join(root, "pipeline", "art", "references.json"))
                                   else REPO)
    except (ImportError, OSError, ValueError):
        return out
    for r in spec.get("references", []):
        role = r.get("role") or []
        p = r.get("path") or ""
        if "layout" in (role if isinstance(role, list) else [role]) and p.lower().endswith(".json"):
            for base in (root, REPO):
                full = os.path.join(base, p)
                if os.path.isfile(full):
                    try:
                        out.update({k: v for k, v in _load(full).items() if isinstance(v, dict)})
                    except ValueError:
                        pass
                    break
    return out


def colours(st):
    """{name: '#rrggbb'} for the style.json palette and every accent colour (names lower case)."""
    out = {p["name"].lower(): p["hex"].lower() for p in st.get("palette", [])}
    for role in ((st.get("accents") or {}).get("roles") or {}).values():
        for c in role.get("colours", []):
            out[c["name"].lower()] = c["hex"].lower()
    return out


def interpolate(keys, n, loop):
    """One pose per frame from keyed poses at t in 0..1 (linear; a loop wraps back to its first key)."""
    keys = sorted(keys, key=lambda k: k.get("t", 0.0))
    if loop and keys:
        keys = keys + [dict(keys[0], t=1.0)]
    out = []
    for i in range(n):
        t = (i / n) if loop else (i / (n - 1) if n > 1 else 0.0)
        a = max([k for k in keys if k.get("t", 0.0) <= t + 1e-9], key=lambda k: k.get("t", 0.0), default=keys[0])
        later = [k for k in keys if k.get("t", 0.0) > t + 1e-9]
        b = min(later, key=lambda k: k.get("t", 0.0)) if later else a
        span = b.get("t", 0.0) - a.get("t", 0.0)
        f = 0.0 if span <= 0 else (t - a.get("t", 0.0)) / span

        def mix(x, y):
            return round(x + (y - x) * f, 4)

        bones = sorted(set(a.get("rot", {})) | set(b.get("rot", {})))
        pose = {"index": i, "rot": {bn: mix(a.get("rot", {}).get(bn, 0.0), b.get("rot", {}).get(bn, 0.0))
                                    for bn in bones}}
        for k in ("canopy", "lift", "flash"):
            if k in a or k in b:
                pose[k] = mix(a.get(k, 0.0), b.get(k, a.get(k, 0.0)))
        out.append(pose)
    return out


def frame_name(asset, anim, i):
    return f"{asset}_{anim}_{i:02d}.png"


def job(character, anim, out_dir, root=REPO, frames=None, seed=None):
    """The render job for one recipe row. Raises ValueError with the reason a row cannot be rendered."""
    rec = recipes(root)
    ch = (rec.get("characters") or {}).get(character)
    if not ch:
        raise ValueError(f"no Blender recipe for {character!r} (pipeline/art/blender/characters.json has "
                         f"{', '.join(sorted(rec.get('characters') or {}))})")
    row = (ch.get("anims") or {}).get(anim)
    if not row:
        raise ValueError(f"{character} has no anim {anim!r} ({', '.join(sorted(ch.get('anims') or {}))})")
    st = style(root)
    lay = {}
    if ch.get("layout"):
        sheets = layout_sheets(root)
        if ch["layout"] not in sheets:
            raise ValueError(f"{character}: layout sheet {ch['layout']} is not in the references.json layout entries")
        lay = sheets[ch["layout"]]
    size = ch.get("frame_size") or lay.get("frame_size")
    pivot = ch.get("pivot_px") or lay.get("pivot_px")
    if not size or not pivot:
        raise ValueError(f"{character}: no frame_size / pivot_px (layout entry or recipe)")
    n = int(frames or row.get("frames") or lay.get("columns") or 1)
    arow = (st.get("anims") or {}).get(anim)
    fps = lay.get("fps") or 0
    if arow:
        want = arow.get("frames")
        if want and not (want[0] <= n <= want[1]):
            raise ValueError(f"{character} {anim}: {n} frames, the art bible allows {want[0]}-{want[1]} "
                             "(style.json anims)")
        f = arow.get("fps")
        fps = f[0] if isinstance(f, list) else f
    elif n > 1:
        raise ValueError(f"{character} {anim}: an animation needs a style.json anims row (the art-bible table)")
    look = dict(rec.get("look") or {})
    look.pop("_about", None)
    if seed is not None:
        look["seed"] = int(seed)
    asset = ch.get("asset") or character.title()
    out_dir = out_dir.replace(os.sep, "/").rstrip("/")
    return {"character": character, "anim": anim, "builder": ch.get("builder", character), "asset": asset,
            "frame_size": [int(size[0]), int(size[1])], "pivot_px": [float(pivot[0]), float(pivot[1])],
            "faces": ch.get("faces") or lay.get("faces") or "right", "px_per_unit": float(ch.get("px_per_unit", 50)),
            "fps": fps, "loop": bool(row.get("loop")), "layout": ch.get("layout") or "recipe",
            "poses": interpolate(row.get("keys") or [{"t": 0.0}], n, bool(row.get("loop"))),
            "colours": colours(st), "look": look, "out_dir": out_dir,
            "frames": [f"{out_dir}/{frame_name(asset, anim, i)}" for i in range(n)],
            "blend": f"{out_dir}/{asset}_{anim}.blend"}


def blender_argv(prefix, job_path, script=None, root=REPO):
    """The headless command line: no UI, factory settings (no user add-ons or preferences), the job after `--`."""
    script = script or os.path.join(root if os.path.isfile(os.path.join(root, SCRIPT)) else REPO, SCRIPT)
    return list(prefix) + ["-b", "--factory-startup", "-P", script, "--", "--job", job_path]


def describe(j):
    """One provenance-sized line: what was rendered and how (the Blender 'prompt')."""
    lk = j["look"]
    return (f"blender stand-in {j['character']} {j['anim']} ({j['builder']} rig): {len(j['frames'])} frame(s) "
            f"{j['frame_size'][0]}x{j['frame_size'][1]} pivot {j['pivot_px'][0]:g},{j['pivot_px'][1]:g} "
            f"faces {j['faces']} {j['fps']} fps; ink-and-paper NPR: toon {'/'.join(lk.get('shades', []))}, "
            f"Freestyle {lk.get('line_px')} px ink lines, paper grain {lk.get('grain')}, ortho camera, "
            "transparent film; layout " + j["layout"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--character", required=True)
    ap.add_argument("--anim", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--frames", type=int)
    a = ap.parse_args(argv)
    try:
        print(json.dumps(job(a.character, a.anim, a.out_dir, frames=a.frames), indent=1))
    except ValueError as e:
        print(f"plan: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

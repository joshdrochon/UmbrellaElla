#!/usr/bin/env python3
"""Audio gate for THE LAST HOUR. Stdlib only. Rules: pipeline/audio/audio-rules.json.
Sound list: pipeline/audio/sound-list.csv. Detail: pipeline/audio/audio-rules.md.

Modes:
  --list                 sound-list.csv is well formed (columns, classes, kinds, tiers, takes, jitter);
                         P0 and Telegraph rows never have fallback `none`; with --release every
                         fallback is a file under pipeline/art/fallback/ that exists, or `none`
  --scan DIR             every WAV under DIR (Audio/Source) is named SW_<Id>_<NN>.wav, its <Id> is in
                         the sound list, and it passes: PCM 16/24 bit, 44.1/48 kHz, channels as listed,
                         peak <= -1 dBFS, leading silence <= 10 ms and last 5 ms <= -60 dBFS (one-shots),
                         no click at the loop
                         point (loops), active RMS within 3 dB of its family median, take count per id,
                         and a provenance row (author, origin, licence) in pipeline/art/provenance.csv; a row whose
                         tool is an allowed audio source (asset-tools.json: ElevenLabs, Stable Audio, synthesis,
                         ffmpeg, SoX, Audacity, Fab) has that source's licence, and a generated take names one.
                         Every P0 row (P0 and P1 with --release) needs all its take files: an empty
                         folder fails
  --ue-dump JSON         an editor dump of sound assets (format: tests/fixtures/audio/ue_dump_pass.json):
                         every asset has one of the 4 sound classes, every non-music one-shot uses its
                         own family's concurrency asset with its exact settings (incl. volume_scale), telegraphs outrank ambience
                         and have no pitch jitter, variation ids pick from >= 3 takes with no repeats,
                         the SFX/Telegraph/UI classes sit under SCL_SFX, all classes route to SM_Master,
                         and SM_Master has one limiter. The dump names tools/ue/audio_dump.py, the
                         engine version and the commit; every playable asset is 2D (spatialize false,
                         attenuation null); the dump's `unread` list (editor fields it could not read) is empty
  --log FILE             an automation or packaged-build log with `AUDIO:` lines: a telegraph line with the
                         list's own windup sound for every P0 attack (P0+P1 with --release) and every
                         attack with a spawn line, lead times, gust_param changes in every gust, music
                         stems as layers on their phase thresholds that never stop before end_event,
                         music duck after the end event, master peak in every phase (intro, contest, desperation), voice count
                         at 90% (no virtualized telegraph voices), SFX slider at 0
  --blind-id CSV         blind sound ID record (player,sound,answer): >= 3 players, each names >= 90% of
                         the P0+P1 one-shots, 100% of the telegraphs and every must_name sound
  --muted CSV            muted playtest record (player,phase,attack,umbrella_tier, each yes or no): every
                         state a sound signals is also read on screen with sound off
  --events               coverage: every event, state, attack, feature, screen, settings row and menu action in
                         the GDD (docs/gdd/CURRENT), docs/feature-manifest.json, pipeline/unreal/gameplay-code.md,
                         pipeline/ui/menus.md and pipeline/ui/signals.json has a key in pipeline/audio/sound-events.json
                         naming live sound-list rows (or `silent` with a reason, or `pending` on a feature that is
                         not approved yet); every live row is used by a key and has exactly one style family in
                         pipeline/audio/style.json. With --log, each `AUDIO: event key=<key> sound=<id>` line must
                         play one of its key's sounds (sound=none or an unknown key fails)
  --docs FILE...         sound names in docs and data JSON (SW_/SC_/MS_/SFX_<Id>) exist in the sound list, and no line
                         about sound points at the old design (enemy defeat, MVP 10, docs/game-spec.md)
  --placeholders         list the tracked placeholder takes: procedural takes tools/assetgen.py made when the audio
                         API could not (provenance origin `placeholder: <reason>`); with --scan --release each one fails
Flags: --release (TBD fallbacks, missing music and tracked placeholder takes are errors), --require-music,
       --fail-lfs-pointer, --require-dir, --rules, --list-file, --provenance.
Exit 0 = pass, 1 = fail, 2 = usage or input error.
"""
import argparse
import array
import csv
import json
import math
import os
import re
import statistics
import sys
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RULES = os.path.join(ROOT, "pipeline", "audio", "audio-rules.json")
DEFAULT_LIST = os.path.join(ROOT, "pipeline", "audio", "sound-list.csv")
DEFAULT_PROV = os.path.join(ROOT, "pipeline", "art", "provenance.csv")
DEFAULT_EVENTS = os.path.join(ROOT, "pipeline", "audio", "sound-events.json")
DEFAULT_STYLE = os.path.join(ROOT, "pipeline", "audio", "style.json")
LFS_POINTER = b"version https://git-lfs"
LIST_COLUMNS = ["id", "family", "kind", "class", "channels", "takes", "pitch_jitter", "gdd", "tier",
                "event", "owner", "done_when", "fallback"]
KINDS = {"oneshot", "loop"}
LIST_CLASSES = {"SFX", "Telegraph", "Music", "UI"}



def _rel(path, root):
    """os.path.relpath, or the path itself when it is on another drive (Windows: C: vs D:)."""
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path

def load_rules(path=DEFAULT_RULES):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_list(path=DEFAULT_LIST):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fallback_required(row, rules):
    lr = rules["list"]
    return row["tier"] != "cut" and (row["tier"] in lr["fallback_required_tiers"]
                                     or row["class"] in lr["fallback_required_classes"])


def concurrency_for(row, rules):
    """The one concurrency asset a non-music one-shot must use: by id first, then by family."""
    cc = rules["concurrency"]
    return cc["by_id"].get(row["id"]) or cc["by_family"].get(row["family"])


P0_FEATURE = re.compile(r"(?<![\w-])(?:[A-Z]+-\d{2}|QA-BASE)(?![\w-])")
TIER_RANK = {"P0": 0, "P1": 1, "P2": 2, "cut": 3}


def p0_features(root=ROOT):
    try:
        with open(os.path.join(root, "docs", "feature-manifest.json"), encoding="utf-8") as f:
            return {x["feature_id"] for x in json.load(f).get("features", []) if x.get("status") == "APPROVED_P0"}
    except (OSError, ValueError, KeyError):
        return set()


def p0_sounds(root=ROOT):
    """{sound id: [APPROVED_P0 feature IDs]} from the manifest's `sounds` lists (final-7 dry run B H2)."""
    try:
        with open(os.path.join(root, "docs", "feature-manifest.json"), encoding="utf-8") as f:
            feats = json.load(f).get("features", [])
    except (OSError, ValueError):
        return {}
    out = {}
    for x in feats:
        if isinstance(x, dict) and x.get("status") == "APPROVED_P0":
            for s in x.get("sounds") or []:
                out.setdefault(s, []).append(x.get("feature_id"))
    return out


def p0_tier_problems(rows, old_rows=None, root=ROOT):
    """The sound of an APPROVED_P0 feature is never cut, and (against the base branch's list in CI) never removed or
    moved to a lower tier (dry run B H8). Raising a tier is always allowed. Which sounds those are comes from the
    manifest (`sounds` of each APPROVED_P0 record), plus any row whose gdd cell names a P0 ID on either branch, so
    rewording the row's own cell changes nothing (final-7 dry run B H2). A manifest sound's gdd cell must still
    name its feature."""
    p0, out = p0_features(root), []
    by_manifest = p0_sounds(root)
    old = {r.get("id"): r for r in (old_rows or [])}
    new = {r.get("id"): r for r in rows}
    for sid, fids in sorted(by_manifest.items()):
        r = new.get(sid)
        if r is None:
            out.append(f"sound-list {sid}: missing, but docs/feature-manifest.json lists it as the sound of "
                       f"APPROVED_P0 {', '.join(fids)}")
            continue
        named = set(P0_FEATURE.findall(r.get("gdd") or ""))
        lost = [f for f in fids if f not in named]
        if lost:
            out.append(f"sound-list {sid}: gdd cell '{r.get('gdd')}' no longer names {', '.join(lost)}; the manifest "
                       "lists it as that APPROVED_P0 feature's sound")
    for r in rows:
        o = old.get(r["id"])
        ids = sorted((set(P0_FEATURE.findall(r.get("gdd") or "")) | set(P0_FEATURE.findall((o or {}).get("gdd") or "")))
                     & p0 | set(by_manifest.get(r["id"], [])))
        if not ids:
            continue
        if r.get("tier") == "cut":
            out.append(f"sound-list {r['id']}: tier cut, but it is the sound of APPROVED_P0 {', '.join(ids)}")
        o = old.get(r["id"])
        if o and TIER_RANK.get(r.get("tier"), 9) > TIER_RANK.get(o.get("tier"), 9):
            out.append(f"sound-list {r['id']}: tier {o.get('tier')} -> {r.get('tier')}; the sound of APPROVED_P0 "
                       f"{', '.join(ids)} never drops a tier (a cut is an Overrides decision, docs/decisions.md)")
    for i, o in old.items():
        if i not in new and i not in by_manifest and set(P0_FEATURE.findall(o.get("gdd") or "")) & p0:
            out.append(f"sound-list {i}: removed, but it is the sound of an APPROVED_P0 feature")
    return out


def check_list(rows, rules, release=False, root=ROOT):
    """Problems in the sound list itself."""
    out, seen = [], set()
    lr = rules["list"]
    if not rows:
        return ["sound-list: no rows"]
    missing = [c for c in LIST_COLUMNS if c not in rows[0]]
    if missing:
        return [f"sound-list: missing columns {missing}"]
    jmax = rules["variation"]["pitch_jitter_max"]
    for r in rows:
        i = r["id"]
        if not re.match(r"^[A-Z][A-Za-z0-9]*$", i or ""):
            out.append(f"sound-list {i!r}: id must be PascalCase letters and digits")
        if i in seen:
            out.append(f"sound-list {i}: duplicate id")
        seen.add(i)
        if r["kind"] not in KINDS:
            out.append(f"sound-list {i}: kind {r['kind']!r} not in {sorted(KINDS)}")
        if r["class"] not in LIST_CLASSES:
            out.append(f"sound-list {i}: class {r['class']!r} not in {sorted(LIST_CLASSES)}")
        if r["tier"] not in lr["tiers"]:
            out.append(f"sound-list {i}: tier {r['tier']!r} not in {lr['tiers']}")
        if r["channels"] not in ("1", "2"):
            out.append(f"sound-list {i}: channels must be 1 or 2")
        try:
            takes, jit = int(r["takes"]), float(r["pitch_jitter"])
        except ValueError:
            out.append(f"sound-list {i}: takes and pitch_jitter must be numbers")
            continue
        if r["class"] == "Telegraph" and (jit != 0 or takes != 1):
            out.append(f"sound-list {i}: a telegraph has 1 take and pitch_jitter 0 (it must sound the same every time)")
        if jit > jmax:
            out.append(f"sound-list {i}: pitch_jitter {jit} > {jmax}")
        if takes > 1 and takes < rules["variation"]["takes_min"]:
            out.append(f"sound-list {i}: a varied sound has >= {rules['variation']['takes_min']} takes")
        for col in ("owner", "done_when", "fallback", "event"):
            if not (r[col] or "").strip():
                out.append(f"sound-list {i}: {col} is empty")
        fb, need = (r["fallback"] or "").strip(), fallback_required(r, rules)
        if need and fb == lr["fallback_none"]:
            out.append(f"sound-list {i}: a {r['tier']} or Telegraph row needs a fallback file, not 'none'")
        elif release and fb.startswith("TBD"):
            what = "a CC0 file (card 0.15)" if need else f"a CC0 file or '{lr['fallback_none']}'"
            out.append(f"sound-list {i}: fallback still {fb}; release needs {what}")
        elif release and fb != lr["fallback_none"]:
            if not (fb.startswith(lr["fallback_dir"]) and fb.lower().endswith(".wav")):
                out.append(f"sound-list {i}: fallback {fb!r} must be a .wav under {lr['fallback_dir']}")
            elif not os.path.isfile(os.path.join(root, fb)):
                out.append(f"sound-list {i}: fallback file {fb} does not exist")
        if r["kind"] == "oneshot" and r["class"] != "Music" and r["tier"] != "cut":
            con = concurrency_for(r, rules)
            if con is None or con not in rules["concurrency"]["assets"]:
                out.append(f"sound-list {i}: no concurrency asset for family {r['family']!r} in audio-rules.json")
    windups = [r for r in rows if r["class"] == "Telegraph"]
    if len(windups) < 3:
        out.append(f"sound-list: {len(windups)} telegraph sounds; the 3 owl attacks need 3 different ones")
    ids = {r["id"] for r in rows}
    for attack, sid in rules["attacks"].items():
        if sid not in ids:
            out.append(f"sound-list: attack {attack} has no windup row {sid}")
    return out


# ---------------------------------------------------------------- WAV

def dbfs(x):
    return -math.inf if x <= 0 else 20 * math.log10(x)


def read_wav(path):
    """Return (info, channels as lists of floats in -1..1). Raises ValueError for anything not PCM 16/24."""
    try:
        w = wave.open(path, "rb")
    except (wave.Error, EOFError) as e:
        raise ValueError(f"not a PCM WAV ({e})")
    with w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        a = array.array("h")
        a.frombytes(raw)
        if sys.byteorder == "big":
            a.byteswap()
        full = 32768.0
        vals = a
    elif sw == 3:
        vals = [int.from_bytes(raw[k:k + 3], "little", signed=True) for k in range(0, len(raw), 3)]
        full = 8388608.0
    else:
        raise ValueError(f"{sw * 8}-bit samples; use 16 or 24 bit PCM")
    chans = [[v / full for v in vals[c::ch]] for c in range(ch)]
    return {"channels": ch, "bits": sw * 8, "rate": sr, "frames": n}, chans


def measure(chans, rate, gate_dbfs, tail_ms=5):
    """Peak dBFS, leading silence ms, active RMS dB, loop wrap jump, peak dBFS of the last tail_ms."""
    if not chans or not chans[0]:
        return {"peak_dbfs": -math.inf, "lead_ms": math.inf, "rms_db": -math.inf, "wrap": 0.0, "tail_dbfs": -math.inf}
    n = len(chans[0])
    mono_abs = [max(abs(c[k]) for c in chans) for k in range(n)] if len(chans) > 1 else [abs(v) for v in chans[0]]
    peak = max(mono_abs)
    tail = dbfs(max(mono_abs[-max(1, int(rate * tail_ms / 1000)):]))
    gate = 10 ** (gate_dbfs / 20)
    first = next((k for k, v in enumerate(mono_abs) if v >= gate), None)
    if first is None:
        return {"peak_dbfs": dbfs(peak), "lead_ms": math.inf, "rms_db": -math.inf, "wrap": 0.0, "tail_dbfs": tail}
    last = n - 1 - next(k for k, v in enumerate(reversed(mono_abs)) if v >= gate)
    ss = sum(v * v for c in chans for v in c[first:last + 1])
    rms = math.sqrt(ss / (len(chans) * (last - first + 1)))
    wrap = max(abs(c[-1] - c[0]) for c in chans)
    return {"peak_dbfs": dbfs(peak), "lead_ms": first * 1000.0 / rate, "rms_db": dbfs(rms), "wrap": wrap,
            "tail_dbfs": tail}


def provenance_rows(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        return {r["asset_path"]: r for r in csv.DictReader(f)}


GENERATED = ("generated", "synthesized")
# A tracked placeholder take: tools/assetgen.py made a procedural take because the audio API could not (no key, an
# HTTP error, no credits left). Its provenance origin carries `placeholder: <reason>`; the run goes on with it, the
# MVP 15 audio card regenerates it, and --release fails while one is left.
PLACEHOLDER = re.compile(r"\bplaceholder:\s*(.+)$", re.I)


def placeholder_takes(prov_path=None, root=ROOT):
    """{asset path: reason} for every tracked placeholder take in the provenance ledger."""
    rows = provenance_rows(prov_path or os.path.join(root, "pipeline", "art", "provenance.csv"))
    out = {}
    for path, r in rows.items():
        m = PLACEHOLDER.search(r.get("origin") or "")
        if m and path.lower().endswith(".wav"):
            out[path] = m.group(1).strip()
    return out


def audio_sources():
    """{tool name: licence} for the allowed audio sources: the audio tools of pipeline/agent-ops/asset-tools.json
    (ElevenLabs, Stable Audio, procedural synthesis, ffmpeg, SoX, Audacity as the human fallback, Fab packs)."""
    try:
        with open(os.path.join(ROOT, "pipeline", "agent-ops", "asset-tools.json"), encoding="utf-8") as fh:
            tools = json.load(fh)["tools"]
    except (OSError, ValueError, KeyError):
        return {}
    return {t["name"]: t["licence"] for t in tools if "audio" in t.get("stage", "")}


def source_problems(pr, sources=None):
    """A provenance row whose tool is an allowed audio source carries that source's licence terms exactly (as
    tools/assetgen.py writes them); a generated or synthesized take names an allowed source."""
    sources = audio_sources() if sources is None else sources
    tool_name = (pr.get("tool") or "").strip()
    origin = (pr.get("origin") or "").strip().lower()
    if tool_name in sources:
        if (pr.get("licence") or "").strip() != sources[tool_name]:
            return [f"provenance licence for {tool_name} must read '{sources[tool_name]}' "
                    "(pipeline/agent-ops/asset-tools.json)"]
        return []
    if origin.startswith(GENERATED):
        return [f"provenance tool '{tool_name or '(empty)'}' is not an allowed audio source; use one listed in "
                "pipeline/agent-ops/asset-tools.json (tools/assetgen.py writes the row)"]
    return []


def scan(folder, rules, rows, prov_path=DEFAULT_PROV, root=ROOT, fail_lfs_pointer=False, release=False):
    """Return (problems, skipped, measured) for every WAV under folder."""
    wr = rules["wav"]
    by_id = {r["id"]: r for r in rows}
    prov = provenance_rows(prov_path)
    name_re = re.compile(wr["name_regex"])
    problems, skipped, measured, takes = [], [], [], {}
    paths = []
    for d, _, fs in os.walk(folder):
        paths += [os.path.join(d, f) for f in fs if f.lower().endswith(".wav")]
    for p in sorted(paths):
        try:
            rel = os.path.relpath(p, root).replace(os.sep, "/")
        except ValueError:   # Windows: the folder is on another drive than the repo, so no row can match it
            rel = os.path.abspath(p).replace(os.sep, "/")
        base = os.path.basename(p)
        m = name_re.match(base)
        if not m:
            problems.append(f"{rel}: name must be SW_<Id>_<NN>.wav (NN from 00)")
            continue
        sid = m.group(1)
        row = by_id.get(sid)
        if row is None:
            problems.append(f"{rel}: id {sid} is not in pipeline/audio/sound-list.csv")
            continue
        takes.setdefault(sid, []).append(rel)
        pr = prov.get(rel)
        if pr is None:
            problems.append(f"{rel}: no provenance row in {_rel(prov_path, root)}")
        else:
            for k in ("author", "origin", "licence"):
                if not (pr.get(k) or "").strip() or pr.get(k, "").strip().lower().startswith("unknown"):
                    problems.append(f"{rel}: provenance {k} is empty or unknown")
            problems += [f"{rel}: {x}" for x in source_problems(pr)]
            m = PLACEHOLDER.search(pr.get("origin") or "")
            if m and release:
                problems.append(f"{rel}: tracked placeholder ({m.group(1).strip()[:80]}); regenerate it before "
                                "release (tools/assetgen.py sfx|music with an audio API key)")
        with open(p, "rb") as f:
            head = f.read(len(LFS_POINTER))
        if head == LFS_POINTER:
            if fail_lfs_pointer:
                problems.append(f"{rel}: still a Git LFS pointer (run git lfs pull --include='Audio/**')")
            else:
                skipped.append(rel)
            continue
        try:
            info, chans = read_wav(p)
        except ValueError as e:
            problems.append(f"{rel}: {e}")
            continue
        if info["rate"] not in wr["sample_rates"]:
            problems.append(f"{rel}: {info['rate']} Hz; use {' or '.join(map(str, wr['sample_rates']))}")
        if info["bits"] not in wr["bit_depths"]:
            problems.append(f"{rel}: {info['bits']}-bit")
        if str(info["channels"]) != row["channels"]:
            problems.append(f"{rel}: {info['channels']} channel(s); sound list says {row['channels']}")
        mm = measure(chans, info["rate"], wr["gate_dbfs"], wr["tail_ms"])
        if mm["peak_dbfs"] > wr["peak_dbfs_max"]:
            problems.append(f"{rel}: peak {mm['peak_dbfs']:.2f} dBFS > {wr['peak_dbfs_max']} dBFS")
        if mm["rms_db"] == -math.inf:
            problems.append(f"{rel}: silent (nothing above {wr['gate_dbfs']} dBFS)")
            continue
        if row["kind"] == "oneshot" and mm["lead_ms"] > wr["lead_silence_ms_max"]:
            problems.append(f"{rel}: {mm['lead_ms']:.1f} ms of silence before the sound; max {wr['lead_silence_ms_max']} ms")
        if row["kind"] == "oneshot" and mm["tail_dbfs"] > wr["tail_dbfs_max"]:
            problems.append(f"{rel}: click at the end (last {wr['tail_ms']} ms peaks at {mm['tail_dbfs']:.1f} dBFS; "
                            f"max {wr['tail_dbfs_max']} dBFS). Fade the end out")
        if row["kind"] == "loop" and mm["wrap"] > wr["loop_wrap_jump_max"]:
            problems.append(f"{rel}: click at the loop point (last-to-first sample jump {mm['wrap']:.3f} > {wr['loop_wrap_jump_max']})")
        measured.append((rel, row["family"], mm))
    fams = {}
    for rel, fam, mm in measured:
        fams.setdefault(fam, []).append(mm["rms_db"])
    for rel, fam, mm in measured:
        if len(fams[fam]) < 2:
            continue
        med = statistics.median(fams[fam])
        if abs(mm["rms_db"] - med) > wr["family_rms_db_tol"]:
            problems.append(f"{rel}: RMS {mm['rms_db']:.1f} dB is {mm['rms_db'] - med:+.1f} dB from the {fam} median "
                            f"{med:.1f} dB; max ±{wr['family_rms_db_tol']} dB")
    for sid, files in takes.items():
        want = int(by_id[sid]["takes"])
        if len(files) < want:
            problems.append(f"{sid}: {len(files)} take file(s); sound list wants {want}")
    tiers = rules["coverage"]["release_tiers" if release else "tiers"]
    for r in rows:
        if r["tier"] in tiers and r["id"] not in takes:
            n = int(r["takes"])
            want = f"SW_{r['id']}_00.wav" + (f" .. _{n - 1:02d}" if n > 1 else "")
            problems.append(f"{r['id']}: {r['tier']} sound has no file in the folder (want {want})")
    return problems, skipped, measured


# ---------------------------------------------------------------- editor dump

def asset_id(name, rules):
    m = re.match(rules["asset_name_regex"], name or "")
    return m.group(2) if m else None


def check_dump(dump, rules, rows, release=False):
    """Problems in an editor dump of sound classes, submixes, concurrency and sound assets. [VERIFY] fields."""
    out = []
    cl, cc = rules["classes"], rules["concurrency"]
    by_id = {r["id"]: r for r in rows}
    assets = dump.get("assets") if isinstance(dump, dict) else None
    if not assets:
        return ["dump: no assets (a dump that found nothing never passes)"]
    dr = rules["dump"]
    if dump.get("tool") != dr["tool"]:
        out.append(f"dump: tool is {dump.get('tool')!r}; only {dr['tool']} run in the editor makes a dump (no hand dumps)")
    if not re.match(dr["engine_regex"], str(dump.get("engine") or "")):
        out.append(f"dump: engine {dump.get('engine')!r} does not match {dr['engine_regex']}")
    if not str(dump.get("commit") or "").strip():
        out.append("dump: no commit (the dump must name the commit it was made from)")
    classes = {c.get("name"): c for c in dump.get("sound_classes", [])}
    for name in cl["names"]:
        c = classes.get(name)
        if c is None:
            out.append(f"sound class {name} is missing")
            continue
        if name != "SCL_SFX" and name in cl["sfx_slider_covers"] and c.get("parent") != "SCL_SFX":
            out.append(f"sound class {name}: parent must be SCL_SFX so the SFX slider covers it")
        if c.get("default_submix") != cl["master_submix"] and c.get("parent") is None:
            out.append(f"sound class {name}: routes to {c.get('default_submix')}, not {cl['master_submix']}")
    subs = {s.get("name"): s for s in dump.get("submixes", [])}
    master = subs.get(cl["master_submix"])
    if master is None:
        out.append(f"submix {cl['master_submix']} is missing")
    else:
        lim = [e for e in master.get("effects", []) if re.search(cl["limiter_effect_regex"], e)]
        if len(lim) != cl["limiters_on_master"]:
            out.append(f"{cl['master_submix']}: {len(lim)} limiter(s); want exactly {cl['limiters_on_master']}")
    for s in subs.values():
        if s.get("name") != cl["master_submix"] and s.get("parent") != cl["master_submix"]:
            out.append(f"submix {s.get('name')}: parent must be {cl['master_submix']}")
    unread = dump.get("unread")
    if not isinstance(unread, list):
        out.append("dump: no unread list (audio_dump.py lists every editor field it could not read)")
    elif len(unread) > dr["unread_max"]:
        out.append(f"dump: {len(unread)} editor field(s) unread {unread[:5]}; fix the [VERIFY] names in audio_dump.py")
    con = {c.get("name"): c for c in dump.get("concurrency", [])}
    for cname, want_set in cc["assets"].items():
        got_set = con.get(cname)
        if got_set is None:
            out.append(f"concurrency asset {cname} is missing")
            continue
        for k, want in want_set.items():
            got = got_set.get(k)
            ok = abs(float(got) - float(want)) < 1e-6 if isinstance(want, (int, float)) and isinstance(got, (int, float)) else got == want
            if not ok:
                out.append(f"{cname}: {k} is {got!r}, want {want!r}")
    ambience_prio, telegraphs, found = [], [], set()
    for a in assets:
        name = a.get("name", "?")
        sid = asset_id(name, rules)
        if sid is None:
            out.append(f"{name}: name must be SW_/SC_/MS_<Id>")
            continue
        row = by_id.get(sid)
        if row is None:
            out.append(f"{name}: id {sid} is not in the sound list")
            continue
        player = a.get("class") in ("SoundCue", "MetaSoundSource") or not any(
            asset_id(b.get("name"), rules) == sid and b.get("class") != "SoundWave" for b in assets)
        if player:
            found.add(sid)
        sc = a.get("sound_class")
        if sc not in cl["names"]:
            out.append(f"{name}: sound class {sc!r}; want one of {cl['names']}")
        elif sc != cl["by_list_class"][row["class"]]:
            out.append(f"{name}: sound class {sc}; sound list says {cl['by_list_class'][row['class']]}")
        if bool(a.get("looping")) != (row["kind"] == "loop"):
            out.append(f"{name}: looping is {bool(a.get('looping'))}; sound list kind is {row['kind']}")
        if not player:
            continue
        for k in ("spatialize", "attenuation"):
            if k not in a:
                out.append(f"{name}: no {k} field (the dump must report it)")
            elif a[k] != dr[k]:
                out.append(f"{name}: {k} is {a[k]!r}; the fixed 2D camera wants {dr[k]!r} (no pan or fade by distance)")
        if row["kind"] == "oneshot" and row["class"] != "Music":
            want_con, got_con = concurrency_for(row, rules), list(a.get("concurrency") or [])
            if got_con != [want_con]:
                out.append(f"{name}: concurrency {got_con}; want exactly [{want_con!r}] (its family's own group)")
        prio = a.get("priority")
        if row["class"] == "Telegraph":
            telegraphs.append((name, prio))
            if a.get("pitch_min", 1.0) != 1.0 or a.get("pitch_max", 1.0) != 1.0:
                out.append(f"{name}: telegraph has pitch randomization; it must be exact")
        elif row["kind"] == "loop":
            ambience_prio.append(prio if isinstance(prio, (int, float)) else 1.0)
        if int(row["takes"]) > 1:
            j = float(row["pitch_jitter"])
            if (a.get("random_takes") or 0) < int(row["takes"]):
                out.append(f"{name}: random node picks from {a.get('random_takes') or 0} takes; want {row['takes']}")
            if not a.get("no_repeat"):
                out.append(f"{name}: random node allows an immediate repeat")
            lo, hi = a.get("pitch_min", 1.0), a.get("pitch_max", 1.0)
            if lo < 1 - j - 1e-6 or hi > 1 + j + 1e-6 or lo == hi:
                out.append(f"{name}: pitch range {lo}..{hi}; want inside {1 - j:.2f}..{1 + j:.2f} and not fixed")
    top_amb = max(ambience_prio) if ambience_prio else None
    for name, prio in telegraphs:
        if not isinstance(prio, (int, float)):
            out.append(f"{name}: telegraph has no priority")
        elif top_amb is not None and prio <= top_amb:
            out.append(f"{name}: telegraph priority {prio} is not above ambience/music priority {top_amb}")
    if release:
        for r in rows:
            if r["tier"] in ("P0", "P1") and r["id"] not in found:
                out.append(f"{r['id']}: in the sound list ({r['tier']}) but no playable asset in the dump")
    return out


# ---------------------------------------------------------------- log

AUDIO_LINE = re.compile(r"AUDIO:\s+(\w+)((?:\s+\w+=\S+)*)")


def parse_log(text):
    events = []
    for line in text.splitlines():
        m = AUDIO_LINE.search(line)
        if m:
            kv = dict(p.split("=", 1) for p in m.group(2).split())
            events.append((m.group(1), kv))
    return events


def num(kv, k):
    try:
        return float(kv[k])
    except (KeyError, ValueError):
        return None


def check_log(text, rules, release=False, require_music=False, rows=None, mapping=None):
    out, notes = [], []
    rows = load_list() if rows is None else rows
    by_id = {r["id"]: r for r in rows}
    ev = parse_log(text)
    if not ev:
        return ["log: no AUDIO: lines"], notes
    tg, attacks = rules["telegraph"], rules["attacks"]
    tele = [kv for k, kv in ev if k == "telegraph"]
    spawns = [kv for k, kv in ev if k == "spawn"]
    tiers = rules["coverage"]["release_tiers" if release else "tiers"]
    seen = {kv.get("attack") for kv in tele}
    for attack, sid in attacks.items():
        row = by_id.get(sid, {})
        spawned = any(kv.get("attack") == attack for kv in spawns)
        if (row.get("tier") in tiers or spawned) and attack not in seen:
            why = "it has a spawn line" if spawned else f"its windup {sid} is {row.get('tier')}"
            out.append(f"telegraph {attack}: no telegraph line, but {why}")
    for kv in spawns:
        if kv.get("attack") not in attacks:
            out.append(f"spawn: attack {kv.get('attack')!r} is not one of {sorted(attacks)}")
    sound_of = {}
    for kv in tele:
        a, s = kv.get("attack", "?"), kv.get("sound", "?")
        if a not in attacks:
            out.append(f"telegraph {a}: not one of {sorted(attacks)}")
        elif s != attacks[a]:
            out.append(f"telegraph {a}: sound {s}; the sound list windup for {a} is {attacks[a]}")
        st, vt, dt = num(kv, "sound_t"), num(kv, "visual_t"), num(kv, "danger_t")
        if None in (st, vt, dt):
            out.append(f"telegraph {a}: needs sound_t, visual_t and danger_t")
            continue
        if st > vt + tg["visual_tolerance_s"]:
            out.append(f"telegraph {a}: sound starts {st - vt:.3f} s after the visual tell")
        if dt - st < tg["lead_s_min"] - 1e-9:
            out.append(f"telegraph {a}: sound leads danger by {dt - st:.3f} s; min {tg['lead_s_min']} s")
        sound_of.setdefault(a, set()).add(s)
    users = {}
    for a, ss in sound_of.items():
        for s in ss:
            users.setdefault(s, set()).add(a)
    for s, attacks in users.items():
        if len(attacks) > 1:
            out.append(f"telegraph sound {s} is shared by attacks {sorted(attacks)}; each attack needs its own")
    out += check_gust(ev, rules)
    mu = rules["music"]
    stem_kv = [kv for k, kv in ev if k == "stem"]
    stems = {kv.get("name"): num(kv, "t_norm") for kv in stem_kv}
    if not stems:
        (out if (release or require_music) else notes).append("music: no stem lines (music cut or not built)")
    else:
        for name, at in mu["stems"].items():
            got = stems.get(name)
            if got is None:
                out.append(f"stem {name}: no start line")
            elif abs(got - at) > mu["t_norm_tol"]:
                out.append(f"stem {name}: starts at t_norm {got:.3f}; want {at:.2f} ±{mu['t_norm_tol']}")
        for kv in stem_kv:
            n = kv.get("name")
            if kv.get("layered") != "1":
                out.append(f"stem {n}: needs layered=1 (stems stack as vertical layers)")
            if kv.get("start") not in mu["start_modes"]:
                out.append(f"stem {n}: start={kv.get('start')}; want one of {mu['start_modes']} (next bar via Quartz, or a fade)")
            elif kv.get("start") == "fade" and (num(kv, "fade_s") is None or num(kv, "fade_s") > mu["fade_s_max"]):
                out.append(f"stem {n}: start=fade needs fade_s <= {mu['fade_s_max']}")
        end_i = next((i for i, (k, _) in enumerate(ev) if k == "end_event"), None)
        for i, (k, kv) in enumerate(ev):
            if k == "stem_stop" and (end_i is None or i < end_i):
                out.append(f"stem {kv.get('name')}: stops before end_event; layers keep playing to the end")
        if end_i is None:
            out.append("log: no end_event line")
        else:
            ducks = [num(kv, "music_db") for k, kv in ev[end_i:] if k == "duck"]
            if not ducks or ducks[0] is None or ducks[0] > mu["duck_db_max"]:
                out.append(f"end event: music not ducked to <= {mu['duck_db_max']} dB after end_event")
    mx = rules["mix"]
    for phase in mx["phases"]:
        peaks = [num(kv, "dbfs") for k, kv in ev if k == "master_peak" and kv.get("phase") == phase]
        if not peaks:
            out.append(f"mix: no master_peak line for phase {phase}")
        for p in peaks:
            if p is None or p > mx["master_peak_dbfs_max"]:
                out.append(f"mix: master peak {p} dBFS in {phase}; max {mx['master_peak_dbfs_max']} dBFS")
    for k, kv in ev:
        if k == "master_peak" and kv.get("phase") not in mx["phases"]:
            out.append(f"mix: master_peak phase {kv.get('phase')!r} not one of {mx['phases']}")
    vr = rules["voices"]
    vs = [(num(kv, "t"), num(kv, "active")) for k, kv in ev
          if k == "voices" and (num(kv, "t_norm") or 0) >= vr["t_norm_min"]]
    vs = [v for v in vs if None not in v]
    if not vs:
        out.append(f"voices: no voices line at t_norm >= {vr['t_norm_min']}")
    else:
        for t, n in vs:
            if n > vr["max_active"]:
                out.append(f"voices: {int(n)} active at t={t}; max {vr['max_active']}")
        for k, kv in ev:
            vt = num(kv, "virtual_telegraph") if k == "voices" else None
            if vt is not None and vt > vr["virtual_telegraph_max"]:
                out.append(f"voices: {int(vt)} telegraph voice(s) virtualized at t={kv.get('t')} (a tell went silent)")
        pair = next(((a, b) for a in vs for b in vs if b[0] - a[0] >= vr["sample_gap_s"]), None)
        if pair is None:
            out.append(f"voices: need two samples >= {vr['sample_gap_s']} s apart")
        elif pair[1][1] > pair[0][1]:
            out.append(f"voices: rising from {int(pair[0][1])} to {int(pair[1][1])} (leaked voices)")
    slider_i = next((i for i, (k, kv) in enumerate(ev) if k == "slider" and kv.get("class") == "SFX"
                     and num(kv, "value") == 0), None)
    if slider_i is not None:
        covered = set(rules["classes"]["sfx_slider_covers"])
        for k, kv in ev[slider_i + 1:]:
            if k == "voice" and kv.get("class") in covered and (num(kv, "volume") or 0) > 0:
                out.append(f"slider: SFX at 0 but {kv.get('name')} ({kv.get('class')}) plays at volume {kv.get('volume')}")
    if mapping is None:
        try:
            mapping = load_json_file(DEFAULT_EVENTS)
        except (OSError, ValueError):
            mapping = {}
    out += check_event_lines(ev, mapping, release, notes)
    return out, notes


def check_gust(ev, rules):
    """Each gust (spawn line, else telegraph danger_t, for the gust attack) has gust_param values in 0..1 that change."""
    g = rules["gust"]["attack"]
    starts = sorted(num(kv, "t") for k, kv in ev if k == "spawn" and kv.get("attack") == g and num(kv, "t") is not None)
    if not starts:
        starts = sorted(num(kv, "danger_t") for k, kv in ev
                        if k == "telegraph" and kv.get("attack") == g and num(kv, "danger_t") is not None)
    params = [(num(kv, "t"), num(kv, "value")) for k, kv in ev if k == "gust_param"]
    out = []
    for t, v in params:
        if t is None or v is None or not 0 <= v <= 1:
            out.append(f"gust_param: needs t and value in 0..1 (got t={t} value={v})")
    params = [p for p in params if None not in p]
    for n, s in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else math.inf
        vals = [v for t, v in params if s <= t < end]
        if len(set(vals)) - 1 < rules["gust"]["min_changes"]:
            out.append(f"gust at t={s}: gust_param {sorted(set(vals)) or 'missing'}; the loop must follow gust strength")
    return out


def blind_id_set(rows, rules):
    """Sounds in the blind ID test: P0+P1 one-shots, plus every telegraph that is not cut."""
    tiers = rules["blind_id"]["tiers"]
    return {r["id"]: r for r in rows if r["tier"] != "cut" and r["kind"] == "oneshot"
            and (r["tier"] in tiers or r["class"] == "Telegraph")}


def check_blind_id(records, rules, rows, notes=None):
    """records: dicts with player, sound, answer. Every player hears every sound in the set once.
    Fewer than players_min but at least players_floor players is a note, not a FAIL."""
    b, want = rules["blind_id"], blind_id_set(rows, rules)
    out, per = [], {}
    notes = [] if notes is None else notes
    for r in records:
        p, sid = (r.get("player") or "").strip(), (r.get("sound") or "").strip()
        if not p or sid not in want:
            out.append(f"blind-id: row {r} has no player or a sound not in the test set")
            continue
        per.setdefault(p, {})[sid] = (r.get("answer") or "").strip().lower() == sid.lower()
    floor = min(b.get("players_floor", b["players_min"]), b["players_min"])
    if len(per) < floor:
        out.append(f"blind-id: {len(per)} player(s); need {b['players_min']}")
    elif len(per) < b["players_min"]:
        notes.append(f"blind-id: {len(per)} player(s), under {b['players_min']}; run it again at the next playtest")
    for p, got in sorted(per.items()):
        missing = sorted(set(want) - set(got))
        if missing:
            out.append(f"blind-id {p}: did not hear {missing}")
        share = sum(got.values()) / len(want)
        if share < b["per_player_min"] - 1e-9:
            out.append(f"blind-id {p}: named {sum(got.values())}/{len(want)} ({share:.0%}); min {b['per_player_min']:.0%}")
        wrong_tele = sorted(s for s, ok in got.items() if not ok and want[s]["class"] == "Telegraph")
        if wrong_tele and b["telegraph_min"] >= 1.0:
            out.append(f"blind-id {p}: missed telegraph(s) {wrong_tele}; every windup must be named")
        wrong_must = sorted(s for s, ok in got.items() if not ok and s in b.get("must_name", []))
        if wrong_must:
            out.append(f"blind-id {p}: missed {wrong_must}; every player must name these")
    return out


def check_muted(records, rules):
    """Muted playtest: with sound off the player still reads each field on screen (GDD §7)."""
    m = rules["muted"]
    out, players = [], set()
    if not records or any(f not in records[0] for f in ["player"] + m["fields"]):
        return [f"muted: columns must be player,{','.join(m['fields'])}"]
    for r in records:
        p = (r.get("player") or "").strip()
        if not p:
            out.append(f"muted: row {r} has no player")
            continue
        players.add(p)
        for f in m["fields"]:
            v = (r.get(f) or "").strip().lower()
            if v != "yes":
                out.append(f"muted {p}: {f} is {v or 'empty'!r}; with sound off it must still read on screen")
    if len(players) < m["players_min"]:
        out.append(f"muted: {len(players)} player(s); need {m['players_min']}")
    return out


# ---------------------------------------------------------------- docs

DOC_ASSET = re.compile(r"\b(?:SW|SC|MS|SFX)_([A-Za-z0-9_]+)")
DOC_SUFFIX = re.compile(r"(?:_\d{2})?(?:_PH)?_?$")
SOUNDISH = re.compile(r"(?i)\b(sound|audio|sfx|music)")


# ---------------------------------------------------------------- event coverage (sound-events.json)

DERIVED_NS = ("event", "state", "attack", "feature", "screen", "setting", "ui")
UNAPPROVED = {"EXPERIMENT", "PROPOSED", "DEFERRED"}
UI_VERBS = {"focus": r"\b[Ff]ocus\b", "confirm": r"\bConfirm\b", "back": r"\bBack\b", "quit": r"\bQuit\b"}
CAMEL = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z]*)+\b")


def _text(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _between(text, start, end):
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:j if j >= 0 else len(text)]


def load_json_file(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def manifest(root=ROOT):
    try:
        return load_json_file(os.path.join(root, "docs", "feature-manifest.json"))
    except (OSError, ValueError):
        return {}


def event_sources(root=ROOT):
    """{key: source} for everything the design sources say can happen in the game."""
    keys = {}
    m = manifest(root)
    for e in m.get("events") or []:
        keys[f"event:{e}"] = "docs/feature-manifest.json events"
    for f in m.get("features") or []:
        if isinstance(f, dict) and f.get("feature_id"):
            keys[f"feature:{f['feature_id']}"] = "docs/feature-manifest.json features"
    cur = _text(root, "docs/gdd/CURRENT").strip() or "GDD-1.3.md"
    gdd_rel = f"docs/gdd/{cur}"
    gdd = _text(root, gdd_rel)
    vocab = re.search(r"Required semantic events.*?:(.*?)For each:", gdd, re.S)
    for t in CAMEL.findall(vocab.group(1) if vocab else ""):
        keys.setdefault(f"event:{t}", f"{gdd_rel} section 4 event vocabulary")
    code = _text(root, "pipeline/unreal/gameplay-code.md")
    vocab = re.search(r"event vocabulary.*?declared in `Core/`:(.*?)\(the list in", code, re.S)
    for t in CAMEL.findall(vocab.group(1) if vocab else ""):
        keys.setdefault(f"event:{t}", "pipeline/unreal/gameplay-code.md events")
    for sec, where in ((_between(gdd, "### A. Umbrella configuration", "State resolution"), "section 3A states"),
                       (_between(gdd, "## 8. Encounter control", "## 9."), "section 8 states")):
        for st in re.findall(r"^\| ([A-Z][A-Z_]+) \|", sec, re.M):
            keys.setdefault(f"state:{st}", f"{gdd_rel} {where}")
    for row in re.findall(r"^\| ([^|\n]+?) \|", _between(gdd, "Boss patterns and target zones", "Encounter space"), re.M):
        name = _slug(row.split(" (")[0])
        if name and name != "item" and not set(row) <= set("-: "):
            keys.setdefault(f"attack:{name}", f"{gdd_rel} section 7 boss patterns")
    # GDD SH1.0 has no state or boss-pattern table: its four movement modes are the MOVE-19 row ("neither = overhead
    # rise; Shoot only = shooting fall; ...") and the Keeper's attacks are the encounter.json baseline preset's.
    modes = re.search(r"neither = ([a-z ]+); Shoot only = ([a-z ]+); Absorb only = ([a-z ]+); both = ([a-z ]+)[,.]", gdd)
    for st in (modes.groups() if modes else ()):
        keys.setdefault(f"state:{_slug(st)}", f"{gdd_rel} MOVE-19 modes")
    if modes:
        try:
            enc = load_json_file(os.path.join(root, "pipeline", "level", "encounter.json"))
        except (OSError, ValueError):
            enc = {}
        b = (enc or {}).get("encounter_presets") or {}
        for a in ((b.get("presets") or {}).get(b.get("default")) or {}).get("attacks") or []:
            keys.setdefault(f"attack:{_slug(re.sub(r'(?<=[a-z])(?=[A-Z])', '-', a.get('id', '')))}",
                            "pipeline/level/encounter.json baseline preset attacks")
    menus = _text(root, "pipeline/ui/menus.md")
    sm = re.search(r"^Screens:(.*)$", menus, re.M)
    for part in (sm.group(1).split("→") if sm else []):
        name = _slug(re.sub(r"\([^)]*\)", "", part).strip(" ."))
        if name:
            keys.setdefault(f"screen:{name}", "pipeline/ui/menus.md Screens")
    st = re.search(r"Settings rows:(.*?)\.\s+Each", menus, re.S)
    if st:
        body = st.group(1)
        while re.search(r"\([^()]*\)", body):
            body = re.sub(r"\([^()]*\)", "", body)
        chunks = [c.strip() for c in body.split(",") if c.strip()]
        if chunks:
            chunks = chunks[:-1] + [c.strip() for c in chunks[-1].split(" and ")]
        for c in chunks:
            keys.setdefault(f"setting:{_slug(c)}", "pipeline/ui/menus.md settings rows")
    for verb, rx in UI_VERBS.items():
        if re.search(rx, menus):
            keys.setdefault(f"ui:{verb}", "pipeline/ui/menus.md menu actions")
    return keys


def style_families(style):
    fam_of = {}
    for fam, f in (style.get("families") or {}).items():
        for sid in f.get("members") or []:
            fam_of.setdefault(sid, []).append(fam)
    return fam_of


def check_events(rows, mapping, style, root=ROOT, notes=None):
    """Every source event has a key; every key names live rows; every live row is used and has one style family."""
    out = []
    notes = [] if notes is None else notes
    sources = event_sources(root)
    keys = mapping.get("keys") or {}
    by_id = {r["id"]: r for r in rows}
    live = {i for i, r in by_id.items() if r.get("tier") != "cut"}
    status = {f.get("feature_id"): f.get("status") for f in manifest(root).get("features") or [] if isinstance(f, dict)}
    for k in sorted(sources):
        if k not in keys:
            out.append(f"{k} ({sources[k]}): no key in pipeline/audio/sound-events.json; everything that happens in the "
                       "game names its sound rows (or `silent` with a reason)")
    used = set()
    for k, v in sorted(keys.items()):
        ns = k.split(":", 1)[0]
        if ns in DERIVED_NS and k not in sources:
            out.append(f"sound-events {k}: not in its source any more ({ns}); remove or rename the key")
        kinds = [x for x in ("sounds", "silent", "pending") if x in v]
        if len(kinds) != 1:
            out.append(f"sound-events {k}: needs exactly one of sounds, silent or pending (has {kinds or 'none'})")
            continue
        if "silent" in v:
            if not str(v["silent"]).strip():
                out.append(f"sound-events {k}: silent needs a reason")
        elif "pending" in v:
            fid, st = v["pending"], status.get(v["pending"])
            if st not in UNAPPROVED:
                out.append(f"sound-events {k}: pending on {fid}, which is {st or 'not in the manifest'}; an approved "
                           "feature needs its sound rows now")
            else:
                notes.append(f"{k}: pending until {fid} ({st}) is approved")
        else:
            snd = v["sounds"] if isinstance(v["sounds"], list) else []
            if not snd:
                out.append(f"sound-events {k}: sounds is empty")
            for sid in snd:
                if sid not in by_id:
                    out.append(f"sound-events {k}: {sid} is not a row in sound-list.csv")
            used.update(snd)
            if snd and all(s in by_id and s not in live for s in snd):
                out.append(f"sound-events {k}: every sound is cut, so it plays nothing")
    for sid in sorted(live - used):
        out.append(f"sound-list {sid}: no sound-events.json key uses it (what in the game plays it?)")
    for f in manifest(root).get("features") or []:
        if not isinstance(f, dict):
            continue
        mapped = set((keys.get(f"feature:{f.get('feature_id')}") or {}).get("sounds") or [])
        for sid in f.get("sounds") or []:
            if sid not in mapped:
                out.append(f"sound-events feature:{f.get('feature_id')}: the manifest lists {sid}; the key must too")
    try:
        sig = load_json_file(os.path.join(root, "pipeline", "ui", "signals.json"))
    except (OSError, ValueError):
        sig = {}
    for e in sig.get("events") or []:
        sid = (e.get("sound_id") or "").strip()
        if sid and sid not in live:
            out.append(f"signals.json {e.get('event')}: sound_id {sid} is not a live sound-list row")
    fam_of = style_families(style)
    for sid in sorted(live):
        fams = fam_of.get(sid, [])
        if not fams:
            out.append(f"sound-list {sid}: no style family in pipeline/audio/style.json (the critic has no target)")
        elif len(fams) > 1:
            out.append(f"sound-list {sid}: in {len(fams)} style families {fams}; one only")
    for sid in sorted(set(fam_of) - set(by_id)):
        out.append(f"style.json: family member {sid} is not a row in sound-list.csv")
    return out


def check_event_lines(ev, mapping, release=False, notes=None):
    """Run time: every `AUDIO: event key=<key> sound=<id>` line played one of its key's sounds."""
    out = []
    notes = [] if notes is None else notes
    keys = mapping.get("keys") or {}
    lines = [kv for k, kv in ev if k == "event"]
    if not lines:
        (out if release else notes).append("log: no `AUDIO: event key=... sound=...` lines (the Feedback Adapter prints "
                                           "one per event it handles, card 0.5a)")
    for kv in lines:
        key, snd, t = kv.get("key"), kv.get("sound"), kv.get("t", "?")
        ent = keys.get(key)
        if ent is None:
            out.append(f"event {key} at t={t}: not a key in sound-events.json (an event with no sound row)")
        elif "silent" in ent:
            continue
        elif snd in (None, "", "none"):
            out.append(f"event {key} at t={t}: fired with no sound playing")
        elif snd not in (ent.get("sounds") or []):
            out.append(f"event {key} at t={t}: played {snd}, which is not one of its sounds {ent.get('sounds')}")
    return out


def check_docs(texts, rules, rows):
    """texts: {path: text}. Sound names must be in the list; sound lines must not cite the old design."""
    ids = {r["id"] for r in rows}
    out = []
    stale = [s.lower() for s in rules["stale_doc_refs"]]
    for path, text in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            for m in DOC_ASSET.finditer(line):
                if DOC_SUFFIX.sub("", m.group(1)) not in ids:
                    out.append(f"{path}:{n}: {m.group(0)} is not in pipeline/audio/sound-list.csv")
            if SOUNDISH.search(line):
                low = line.lower()
                for s in stale:
                    if s in low:
                        out.append(f"{path}:{n}: sound line cites old-design '{s}'; use pipeline/audio/sound-list.csv")
    return out


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rules", default=DEFAULT_RULES)
    ap.add_argument("--list-file", default=DEFAULT_LIST)
    ap.add_argument("--provenance", default=DEFAULT_PROV)
    ap.add_argument("--events-file", default=DEFAULT_EVENTS)
    ap.add_argument("--style-file", default=DEFAULT_STYLE)
    ap.add_argument("--events", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--tiers-from", metavar="CSV", help="the base branch's sound list (CI): no P0-feature sound drops")
    ap.add_argument("--scan", metavar="DIR")
    ap.add_argument("--ue-dump", metavar="JSON")
    ap.add_argument("--log", metavar="FILE")
    ap.add_argument("--docs", nargs="+", metavar="FILE")
    ap.add_argument("--blind-id", metavar="CSV")
    ap.add_argument("--muted", metavar="CSV")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--require-music", action="store_true")
    ap.add_argument("--fail-lfs-pointer", action="store_true")
    ap.add_argument("--require-dir", action="store_true")
    ap.add_argument("--placeholders", action="store_true",
                    help="list the tracked placeholder takes (provenance origin `placeholder: <reason>`)")
    a = ap.parse_args(argv)
    if a.placeholders:
        ph = placeholder_takes(a.provenance)
        for path in sorted(ph):
            print(f"PLACEHOLDER {path}: {ph[path]}")
        print(f"audio_check placeholders: {len(ph)} tracked placeholder take(s); --release fails while one is left")
        if not (a.list or a.scan or a.ue_dump or a.log or a.docs or a.blind_id or a.muted or a.events):
            return 0
    if not (a.list or a.scan or a.ue_dump or a.log or a.docs or a.blind_id or a.muted or a.events):
        ap.print_usage(sys.stderr)
        return 2
    try:
        rules, rows = load_rules(a.rules), load_list(a.list_file)
        mapping = load_json_file(a.events_file) if (a.events or a.log) else {}
        style = load_json_file(a.style_file) if a.events else {}
    except (OSError, ValueError) as e:
        print(f"audio_check: cannot read rules or sound list: {e}", file=sys.stderr)
        return 2
    problems, notes = [], []
    problems += check_list(rows, rules, a.release)
    if a.events:
        problems += check_events(rows, mapping, style, notes=notes)
    if a.list:
        problems += p0_tier_problems(rows, load_list(a.tiers_from) if a.tiers_from else None)
    if a.scan:
        if not os.path.isdir(a.scan):
            if a.require_dir:
                problems.append(f"{a.scan}: folder does not exist")
            else:
                notes.append(f"SKIP {a.scan}: folder does not exist yet")
        else:
            p, skipped, measured = scan(a.scan, rules, rows, a.provenance, fail_lfs_pointer=a.fail_lfs_pointer,
                                        release=a.release)
            problems += p
            notes += [f"SKIP {s}: Git LFS pointer, not the sound (run git lfs pull)" for s in skipped]
            for rel, fam, mm in measured:
                print(f"{rel}: peak {mm['peak_dbfs']:.2f} dBFS, rms {mm['rms_db']:.1f} dB ({fam}), "
                      f"lead {mm['lead_ms']:.1f} ms, tail {mm['tail_dbfs']:.1f} dBFS, wrap {mm['wrap']:.3f}")
    if a.ue_dump:
        try:
            with open(a.ue_dump, encoding="utf-8") as f:
                dump = json.load(f)
        except (OSError, ValueError) as e:
            print(f"audio_check: cannot read dump: {e}", file=sys.stderr)
            return 2
        problems += check_dump(dump, rules, rows, a.release)
    if a.log:
        try:
            with open(a.log, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            print(f"audio_check: cannot read log: {e}", file=sys.stderr)
            return 2
        p, n = check_log(text, rules, a.release, a.require_music, rows, mapping)
        problems += p
        notes += n
    if a.docs:
        texts = {}
        for d in a.docs:
            try:
                with open(d, encoding="utf-8") as f:
                    texts[d] = f.read()
            except OSError as e:
                print(f"audio_check: cannot read {d}: {e}", file=sys.stderr)
                return 2
        problems += check_docs(texts, rules, rows)
    if a.blind_id:
        try:
            with open(a.blind_id, encoding="utf-8", newline="") as f:
                records = list(csv.DictReader(f))
        except OSError as e:
            print(f"audio_check: cannot read {a.blind_id}: {e}", file=sys.stderr)
            return 2
        problems += check_blind_id(records, rules, rows, notes)
    if a.muted:
        try:
            with open(a.muted, encoding="utf-8", newline="") as f:
                records = list(csv.DictReader(f))
        except OSError as e:
            print(f"audio_check: cannot read {a.muted}: {e}", file=sys.stderr)
            return 2
        problems += check_muted(records, rules)
    for p in problems:
        print(f"FAIL {p}")
    for n in notes:
        print(f"note {n}")
    print(f"audio_check: {'PASS' if not problems else 'FAIL'} errors={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

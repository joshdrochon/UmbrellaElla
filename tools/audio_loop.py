#!/usr/bin/env python3
"""Builder and critic loop for audio cards. Stdlib only. Target: pipeline/audio/style.json; prose and the full rule:
pipeline/audio/style-target.md section 5.

An audio card is split into pieces: one piece per sound id (each music stem is its own piece). For each piece:
  1. the BUILDER agent makes or revises the takes (tools/assetgen.py sfx|music --sound <Id>, prompts from style.json);
  2. `round` measures them (tools/audio_style_check.py) and writes a blind critic packet: the takes renamed X_NN, a
     few approved sounds renamed R<n>, spectrograms, the written target, the numbers. No ids, no history, no notes;
  3. a SEPARATE CRITIC agent (a new session, fresh context, never the builder's session and never a critic of an
     earlier round of this piece) reads only that packet (tools/audio_critic_prompt.md) and answers pass or fail plus
     the single biggest gap; `verdict` records it;
  4. repeat until the critic passes AND the measured check passes on the same files. There is no round cap.
Stuck rule: when the last `stuck_rounds` rounds (style.json loop, now 3) all failed and none improved (no lower
measured distance than every round before it, and the critic named the same gap again), the piece is stuck:
`verdict` prints a `NEEDS HUMAN: Audio-owner ...` line with the files and exits 4. The audio owner listens and decides.
`close` is the only way a card's audio is done: every piece's latest round passed both, the files on disk are the
ones the critic heard, the audio files are committed, and the measured check passes again now. It prints the lines
tools/check_pr.py requires on an audio PR (`AUDIO LOOP: PASS ...`, `audio_style check: PASS ...`,
`audio_loop close: PASS card=<id> ... commit=<sha>`). A piece whose every take is a tracked placeholder (the audio API
could not make it: no key, an HTTP error, no credits left; provenance origin `placeholder: <reason>`) has nothing for a
critic to judge: `close` prints `AUDIO PLACEHOLDER: piece=<Id> ...` for it instead, and the MVP 15 audio card
regenerates it (tools/audio_check.py --placeholders lists them, --release fails them).

Usage:
  audio_loop.py start   --card UE-12 --issue 12 --ids WandBolt,HitOwl --builder <session id>
  audio_loop.py round   --card UE-12 --piece WandBolt
  audio_loop.py verdict --card UE-12 --piece WandBolt --critic <session id> (--reply reply.json |
                        --verdict pass|fail --gap "one sentence")
  audio_loop.py status  --card UE-12
  audio_loop.py resume  --card UE-12 --piece WandBolt --by <audio owner> --note "what to change"   (after a stuck)
  audio_loop.py close   --card UE-12
Common: --root (repo), --audio DIR (default Audio/Source), --state DIR (default Saved/AudioLoop, never committed).
Exit 0 = ok, 1 = fail, 2 = usage or input error, 4 = stuck (needs a human).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import audio_check  # noqa: E402
import audio_style_check as asc  # noqa: E402

PROMPT = os.path.join(HERE, "audio_critic_prompt.md")
STUCK = 4


class LoopError(Exception):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def paths(a):
    root = os.path.abspath(a.root)
    return root, os.path.join(root, a.audio), os.path.join(root, a.state, a.card)


def load_state(sdir):
    p = os.path.join(sdir, "state.json")
    if not os.path.isfile(p):
        raise LoopError(f"no loop for this card yet ({p}); run `audio_loop.py start` first")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_state(sdir, st):
    os.makedirs(sdir, exist_ok=True)
    tmp = os.path.join(sdir, "state.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, os.path.join(sdir, "state.json"))


def piece_files(audio, sid):
    return asc.takes(audio, {sid}).get(sid, [])


def placeholder_piece(root, audio, sid):
    """The reason when every current take of sid is a tracked placeholder (tools/assetgen.py made procedural audio
    because the audio API could not; provenance origin `placeholder: <reason>`), else None. Such a piece has nothing
    for a critic to judge: `close` lists it as `AUDIO PLACEHOLDER:` and the MVP 15 audio card regenerates it."""
    files = piece_files(audio, sid)
    if not files:
        return None
    ph = audio_check.placeholder_takes(root=root)
    rels = [os.path.relpath(f, root).replace(os.sep, "/") for f in files]
    return ph[rels[0]] if all(r in ph for r in rels) else None


def files_hash(files):
    return audio_check.takes_hash(files)   # the same hash the committed critic records carry


def style_ctx(root):
    style = asc.load_style(os.path.join(root, "pipeline", "audio", "style.json"))
    rows = audio_check.load_list(os.path.join(root, "pipeline", "audio", "sound-list.csv"))
    return style, rows


def measure_piece(audio, sid, style, rows):
    files = piece_files(audio, sid)
    if not files:
        raise LoopError(f"{sid}: no takes SW_{sid}_NN.wav under {audio}")
    lines, probs, results = asc.check_takes({sid: files}, style, rows, fail_lfs_pointer=True)
    dist = sum(r["distance"] for r in results.values()) + (0.0 if not probs else 0.001 * len(probs))
    return files, lines, probs, results, round(dist, 4)


def same_gap(a, b):
    wa = {w for w in re.findall(r"[a-z]+", (a or "").lower()) if len(w) > 3}
    wb = {w for w in re.findall(r"[a-z]+", (b or "").lower()) if len(w) > 3}
    if not wa or not wb:
        return (a or "").strip().lower() == (b or "").strip().lower()
    return len(wa & wb) / len(wa | wb) >= 0.5


def improved(rounds, i):
    """Round i moved the piece: the critic passed, the measured distance beat every earlier round, or the critic
    named a different biggest gap (the old one was fixed)."""
    r = rounds[i]
    if i == 0 or r.get("verdict") == "pass":
        return True
    if r["distance"] < min(x["distance"] for x in rounds[:i]) - 1e-6:
        return True
    return not same_gap(r.get("gap"), rounds[i - 1].get("gap"))


def stuck(rounds, n):
    if len(rounds) < n + 1:
        return False
    tail = range(len(rounds) - n, len(rounds))
    return all(rounds[i].get("verdict") == "fail" and not improved(rounds, i) for i in tail)


def neighbours(audio, sid, fam, style, k):
    """Up to k approved takes for consistency: other ids' _00 takes, same family first."""
    fam_of = audio_check.style_families(style)
    other = {i: fs for i, fs in asc.takes(audio).items() if i != sid}
    picks = sorted(other, key=lambda i: (fam_of.get(i, [None])[0] != fam, i))
    out = []
    for i in picks:
        f = sorted(other[i])[0]
        if not asc.is_pointer(f):
            out.append(f)
        if len(out) >= k:
            break
    return out


KIND_NOTE = {
    "oneshot": ("Kind: a one-shot. It plays once each time the event happens, so its onset and its tail are part of the "
                "sound and are judged."),
    "loop": ("Kind: a seamless loop. It plays end to start with no gap, so it has no onset and no tail by design: a "
             "level that runs to the last frame is correct, and a fade in or out would be a defect. attack_ms and decay_s "
             "are one-shot measures; they are not measured or ranged for a loop."),
    "stem": ("Kind: a music stem: one vertical layer of the fight music. It starts on the bar and plays end to start "
             "with the other layers, all at one tempo and one length, so it has no onset and no tail by design: a level "
             "that runs to the last frame is correct, and a fade in or out would be a defect. attack_ms and decay_s are "
             "one-shot measures; they are not measured or ranged for a stem."),
}
# Event text comes from the team's sound list; these parts of it are team bookkeeping, not what the player hears, and
# some would tie the packet to our ids: CamelCase names (sound ids, event-bus names like WindEntered), rule ids and
# state names (OWL-14, SHIELD_DESCENT), and scope notes in brackets.
EVENT_NAME = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+\b")
EVENT_TAG = re.compile(r"\b[A-Z]{2,}(?:[-_][A-Z0-9]+)+\b")
EVENT_SCOPE = re.compile(r"\b(?:to confirm|to discuss|optional|only if)\b", re.I)


def kind_of(sid, rows, style):
    """oneshot, loop or stem (a music stem is a loop row named in style.json music.stems)."""
    if sid in style.get("music", {}).get("stems", []):
        return "stem"
    return next((r["kind"] for r in rows if r["id"] == sid), "oneshot")


def event_text(sid, rows):
    """The sound-list event for sid, blind: no sound id, no internal name or rule id, no scope note."""
    ev = next((r.get("event", "") for r in rows if r["id"] == sid), "")
    ids = sorted({r["id"] for r in rows} | {sid}, key=len, reverse=True)

    def scrub(t):
        for i in ids:
            t = re.sub(rf"\b{re.escape(i)}\b", "", t, flags=re.I)
        return EVENT_TAG.sub("", EVENT_NAME.sub("", t))

    def paren(m):
        inner = m.group(1)
        if EVENT_SCOPE.search(inner):
            return ""
        left = re.sub(r"\s*,\s*(?=,|$)|^\s*,\s*", "", scrub(inner).strip()).strip(" ,;")
        return f"({left})" if len(left.split()) >= 2 or left == inner.strip() else ""

    ev = scrub(re.sub(r"\(([^()]*)\)", paren, ev))
    ev = re.sub(r"\s+([,;:.)])", r"\1", re.sub(r"\s{2,}", " ", ev)).strip(" :;,")
    return ev or "not named"


def family_text(fam, style, kind="oneshot", stem=False):
    """The written target. Only the ranges tools/audio_style_check.py applies to this kind of sound are listed
    (asc.applies: attack_ms and decay_s for one-shots only, tempo_bpm and lra_db for music stems only), so the critic
    never fails a loop on a one-shot range the measured check does not use."""
    f = style["families"][fam]
    rng = "; ".join(f"{k} {lo}..{hi}" for k, (lo, hi) in sorted(f.get("ranges", {}).items()) if asc.applies(k, kind, stem))
    return (f"Character: {f['character']}\nInstruments: {f['instruments']}\nRegister: {f['register']}\n"
            f"Space: {f['reverb']}\nMeasured ranges: {rng}")


def brand_text(style):
    b = style["brand"]
    return (f"{b['world']}\nAlways: " + "; ".join(b["always"]) + "\nNever: " + "; ".join(b["never"]))


def write_packet(rdir, files, near, results, fam, style, kind="oneshot", stem=False, event="not named"):
    pk = os.path.join(rdir, "packet")
    if os.path.isdir(pk):
        shutil.rmtree(pk)
    os.makedirs(pk)
    key = {}
    nums = []
    for i, f in enumerate(sorted(files, key=os.path.basename)):
        name = f"X_{i:02d}"
        shutil.copyfile(f, os.path.join(pk, name + ".wav"))
        asc.spectrogram_png(f, os.path.join(pk, name + ".png"))
        key[name] = os.path.basename(f)
        m = results.get(f, {}).get("metrics", {})
        nums.append(f"{name}: " + asc.summary(m, sorted(k for k in m if k != "silent" and asc.applies(k, kind, stem))))
    for i, f in enumerate(near, 1):
        name = f"R{i}"
        shutil.copyfile(f, os.path.join(pk, name + ".wav"))
        asc.spectrogram_png(f, os.path.join(pk, name + ".png"))
        key[name] = os.path.basename(f)
    with open(PROMPT, encoding="utf-8") as fh:
        tpl = fh.read().split("---", 1)[1]
    note = KIND_NOTE["stem" if stem else kind if kind in KIND_NOTE else "oneshot"]
    brief = (tpl.replace("{event}", f"Event: {event}\n{note}")
             .replace("{family_target}", family_text(fam, style, kind, stem)).replace("{brand}", brand_text(style))
             .replace("{numbers}", "\n".join(nums)))
    with open(os.path.join(pk, "brief.md"), "w", encoding="utf-8") as fh:
        fh.write(brief.lstrip())
    with open(os.path.join(rdir, "key.json"), "w", encoding="utf-8") as fh:
        json.dump(key, fh, indent=1)
    return pk


def cmd_start(a):
    root, audio, sdir = paths(a)
    style, rows = style_ctx(root)
    ids = [i for i in a.ids.split(",") if i]
    bad = [i for i in ids if asc.family_of(i, style) is None or i not in {r["id"] for r in rows}]
    if bad:
        raise LoopError(f"not sound-list rows with one style family: {bad}")
    if os.path.isfile(os.path.join(sdir, "state.json")):
        raise LoopError(f"a loop for {a.card} exists already ({sdir}); use round / verdict / status")
    st = {"card": a.card, "issue": a.issue, "builder": a.builder, "started": now(),
          "pieces": {i: {"family": asc.family_of(i, style), "rounds": []} for i in ids}}
    save_state(sdir, st)
    print(f"audio_loop start: card={a.card} pieces={len(ids)} ({', '.join(ids)}) builder={a.builder}")
    return 0


def piece(st, sid):
    if sid not in st["pieces"]:
        raise LoopError(f"{sid} is not a piece of card {st['card']} ({', '.join(st['pieces'])})")
    return st["pieces"][sid]


def cmd_round(a):
    root, audio, sdir = paths(a)
    st, (style, rows) = load_state(sdir), style_ctx(root)
    pc = piece(st, a.piece)
    if pc["rounds"] and not pc["rounds"][-1].get("verdict"):
        raise LoopError(f"{a.piece} round {len(pc['rounds'])} has no critic verdict yet; record it first")
    if pc.get("stuck"):
        raise LoopError(f"{a.piece} is stuck and waits for the audio owner (see the NEEDS HUMAN line)")
    files, lines, probs, results, dist = measure_piece(audio, a.piece, style, rows)
    n = len(pc["rounds"]) + 1
    rdir = os.path.join(sdir, a.piece, f"round-{n}")
    near = neighbours(audio, a.piece, pc["family"], style, style.get("loop", {}).get("critic_packet_neighbours", 3))
    kind = kind_of(a.piece, rows, style)
    pk = write_packet(rdir, files, near, results, pc["family"], style, "loop" if kind == "stem" else kind,
                      kind == "stem", event_text(a.piece, rows))
    pc["rounds"].append({"n": n, "files": files_hash(files), "paths": [os.path.relpath(f, root).replace(os.sep, "/") for f in files],
                         "style_pass": not probs, "problems": probs, "distance": dist, "at": now()})
    save_state(sdir, st)
    for ln in lines:
        print(ln)
    for p in probs:
        print(f"FAIL {p}")
    print(f"audio_loop round: piece={a.piece} round={n} style={'PASS' if not probs else 'FAIL'} distance={dist}")
    print(f"CRITIC PACKET: {pk}")
    print("Next: start a NEW critic session (not the builder's, not an earlier critic) that reads only that folder, "
          f"starting with brief.md; then `audio_loop.py verdict --card {a.card} --piece {a.piece} --critic <its session> "
          "--reply <its JSON reply>`")
    return 0


def cmd_verdict(a):
    root, audio, sdir = paths(a)
    st, (style, rows) = load_state(sdir), style_ctx(root)
    pc = piece(st, a.piece)
    if not pc["rounds"] or pc["rounds"][-1].get("verdict"):
        raise LoopError(f"{a.piece}: no open round; run `audio_loop.py round` first")
    r = pc["rounds"][-1]
    if a.reply:
        with open(a.reply, encoding="utf-8") as fh:
            rep = json.load(fh)
        verdict, gap = rep.get("verdict"), rep.get("biggest_gap") or ""
        rows_ok = all(v[0] is True for v in (rep.get("rows") or {}).values()) and len(rep.get("rows") or {}) >= 8
        if verdict == "pass" and not rows_ok:
            raise LoopError("the reply says pass but not every row A1-A8 is true")
    else:
        verdict, gap = a.verdict, a.gap or ""
    if verdict not in ("pass", "fail"):
        raise LoopError("verdict is pass or fail")
    gap = gap.strip()
    if verdict == "fail" and (not gap or gap.lower() == "none" or "\n" in gap or len(gap) > 300):
        raise LoopError("a fail names the single biggest gap in one sentence (at most 300 characters)")
    if not a.critic or a.critic == st["builder"]:
        raise LoopError("the critic is a separate session: --critic must differ from the builder's session")
    if any(x.get("critic") == a.critic for x in pc["rounds"][:-1]):
        raise LoopError(f"critic session {a.critic} judged an earlier round of {a.piece}: each round gets a fresh critic")
    if files_hash(piece_files(audio, a.piece)) != r["files"]:
        raise LoopError(f"{a.piece}: the takes changed after the packet was made; run `round` again")
    r.update(verdict=verdict, gap=gap if verdict == "fail" else "none", critic=a.critic, judged=now())
    n = style.get("loop", {}).get("stuck_rounds", 3)
    if verdict == "pass" and r["style_pass"]:
        save_state(sdir, st)
        print(f"audio_loop verdict: piece={a.piece} round={r['n']} critic=pass style=PASS -> piece done; "
              "run `close` when every piece is done")
        return 0
    if stuck(pc["rounds"][pc.get("since", 0):], n):
        pc["stuck"] = True
        save_state(sdir, st)
        files = ",".join(r["paths"])
        print(f"audio_loop verdict: piece={a.piece} round={r['n']} critic={verdict} style="
              f"{'PASS' if r['style_pass'] else 'FAIL'} -> STUCK after {n} rounds with no improvement")
        print(f"NEEDS HUMAN: Audio-owner listen to {a.piece} (stuck {n} rounds; last gap: {gap or 'measured check'}; "
              f"files {files}) #{st['issue']} {now()}")
        return STUCK
    save_state(sdir, st)
    why = gap if verdict == "fail" else "measured check: " + "; ".join(r["problems"])[:300]
    print(f"audio_loop verdict: piece={a.piece} round={r['n']} critic={verdict} style="
          f"{'PASS' if r['style_pass'] else 'FAIL'} -> builder revises: {why}")
    print(f"Next: the builder revises {a.piece} (assetgen --sound {a.piece} --prompt \"<the gap as a change>\"), then "
          "`audio_loop.py round`")
    return 1


def cmd_resume(a):
    """The audio owner listened to a stuck piece and gave direction: the loop goes on (the critic still decides)."""
    root, audio, sdir = paths(a)
    st = load_state(sdir)
    pc = piece(st, a.piece)
    if not pc.get("stuck"):
        raise LoopError(f"{a.piece} is not stuck")
    if not a.note.strip() or a.by == st["builder"]:
        raise LoopError("resume needs the audio owner's name (not the builder session) and a note")
    pc["stuck"] = False
    pc.setdefault("human_notes", []).append({"by": a.by, "note": a.note.strip(), "at": now(),
                                             "after_round": len(pc["rounds"])})
    pc["since"] = len(pc["rounds"])   # the stuck rule counts again from here
    save_state(sdir, st)
    print(f"audio_loop resume: piece={a.piece} by={a.by}; the builder revises: {a.note.strip()}")
    return 0


def cmd_status(a):
    root, audio, sdir = paths(a)
    st = load_state(sdir)
    for sid, pc in st["pieces"].items():
        r = pc["rounds"][-1] if pc["rounds"] else {}
        state = ("stuck" if pc.get("stuck") else "done" if r.get("verdict") == "pass" and r.get("style_pass")
                 else "judging" if r and not r.get("verdict") else "building")
        print(f"{sid}: {state} rounds={len(pc['rounds'])} last_gap={r.get('gap', '-')}")
    return 0


def cmd_close(a):
    root, audio, sdir = paths(a)
    st, (style, rows) = load_state(sdir), style_ctx(root)
    sha, dirty = asc.git_head(root)
    out, probs, nfiles = [], [], 0
    for sid, pc in st["pieces"].items():
        why = placeholder_piece(root, audio, sid)
        if why:
            out.append(f"AUDIO PLACEHOLDER: piece={sid} takes={len(piece_files(audio, sid))} commit={sha[:12]} "
                       f"reason={why[:100]}")
            continue
        r = pc["rounds"][-1] if pc["rounds"] else None
        if r is None:
            probs.append(f"{sid}: no round yet")
            continue
        if r.get("verdict") != "pass":
            probs.append(f"{sid}: latest round {r['n']} critic verdict is {r.get('verdict') or 'missing'}")
            continue
        try:
            files, lines, p, results, dist = measure_piece(audio, sid, style, rows)
        except LoopError as e:
            probs.append(str(e))
            continue
        if p or not r["style_pass"]:
            probs.append(f"{sid}: measured check fails: " + "; ".join(p or r["problems"]))
            continue
        if files_hash(files) != r["files"]:
            probs.append(f"{sid}: the takes on disk are not the ones the critic passed in round {r['n']}; run round")
            continue
        nfiles += len(files)
        out.append(f"AUDIO LOOP: PASS piece={sid} rounds={len(pc['rounds'])} critic={r['critic']} "
                   f"builder={st['builder']} files={r['files'][:12]} commit={sha[:12]}")
    if dirty != "no":
        probs.append("Audio/ or pipeline/audio/ has uncommitted changes: commit the takes, then close")
    for ln in out:
        print(ln)
    for p in probs:
        print(f"FAIL {p}")
    if not probs and nfiles:
        print(f"audio_style check: PASS files={nfiles} commit={sha[:12]} dirty={dirty}")
    print(f"audio_loop close: {'FAIL' if probs else 'PASS'} card={a.card} pieces={len(st['pieces'])} commit={sha[:12]}")
    return 1 if probs else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("start", "round", "verdict", "status", "close", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--card", required=True)
        p.add_argument("--root", default=ROOT)
        p.add_argument("--audio", default=os.path.join("Audio", "Source"))
        p.add_argument("--state", default=os.path.join("Saved", "AudioLoop"))
        if name == "start":
            p.add_argument("--issue", required=True, type=int)
            p.add_argument("--ids", required=True)
            p.add_argument("--builder", required=True)
        if name in ("round", "verdict", "resume"):
            p.add_argument("--piece", required=True)
        if name == "resume":
            p.add_argument("--by", required=True)
            p.add_argument("--note", required=True)
        if name == "verdict":
            p.add_argument("--critic", required=True)
            p.add_argument("--reply")
            p.add_argument("--verdict", choices=("pass", "fail"))
            p.add_argument("--gap")
    a = ap.parse_args(argv)
    if a.cmd == "verdict" and not (a.reply or a.verdict):
        print("audio_loop: verdict needs --reply FILE or --verdict pass|fail", file=sys.stderr)
        return 2
    try:
        return {"start": cmd_start, "round": cmd_round, "verdict": cmd_verdict, "status": cmd_status,
                "close": cmd_close, "resume": cmd_resume}[a.cmd](a)
    except LoopError as e:
        print(f"FAIL {e}")
        return 2
    except (OSError, ValueError) as e:
        print(f"audio_loop: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

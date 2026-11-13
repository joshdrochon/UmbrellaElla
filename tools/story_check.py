#!/usr/bin/env python3
"""Story and text check: every word a player sees agrees with the story bible, uses only its names, keeps the tone and
never names a trademark. Stdlib only. The machine half of the story gate; the blind critic
(tools/story_critic_prompt.md) judges what a regex cannot. A FAIL here is final: the critic cannot override it.

Files:
  pipeline/story/story-bible.md   world, names, facts, tone (the Story role writes it). Names and Facts tables are parsed:
                                  Names  | Name | Kind | Status | Source | Notes |
                                  Facts  | ID | Fact | Status | Source | Never say (regex) |   (escape a regex pipe as \\|)
                                  Status: GDD, DEFERRED, PROPOSED, OPEN or `CONFIRMED <YYYY-MM-DD> (Richard)`.
  pipeline/story/lines.csv        every player-facing line: id,surface,text,facts,ship,note
  pipeline/story/story.json       deny list, banned words, surfaces and their word caps, allowed capitals, GDD
                                  contradictions (a gate file: humans change it)
  docs/feature-manifest.json      NAR-01: narrative surfaces ship only once it is implementation_authorized

Checks on the bible (kind in brackets):
  [bible]   the required sections exist; every Names and Facts row has a valid status and a source that exists;
            fact IDs are unique and every Never-say regex compiles; every story.json contradiction names a GDD fact
  [deny]    no deny-list term outside the bible's "## Never use" section, and that section lists every term
Checks on every line of lines.csv:
  [csv] header and columns; ids unique; a known surface; ship is yes or no; text not empty
  [deny] a deny-list term (Official Rules 15(d); "Strixon" is one) in any line, shipped or not
  [banned] an off-tone word; [exclaim] more than max_exclaim '!'; [caps] an ALL-CAPS word longer than max_caps_run
  [emoji] an emoji or pictograph; [length] more words than the surface allows
  [name] a capitalised word mid-sentence that is not a bible name and not in story.json allow_caps
  [contradiction] text that matches a story.json contradiction or a bible fact's Never-say regex
  [fact] a cited fact ID the bible lacks; a narrative surface (story=true) that cites no fact
  [ship] ship=yes with a cited fact, or a bible name in the text, whose status is not GDD or CONFIRMED
  [nar] ship=yes on a narrative surface while NAR-01 is not implementation_authorized

Usage:
  python3 tools/story_check.py                     bible + lines; prints
                                                   `story_check: PASS bible=<8 hex> sheet=<8 hex> lines=<n> names=<n> facts=<n>`
  python3 tools/story_check.py --scan FILE...      any text a player sees outside lines.csv (the UI string table
                                                   Content/UmbrellaElla/UI/ST_UI.csv, the itch page): deny, banned,
                                                   exclaim, caps, emoji, and names for CSV string tables. Prints
                                                   `story_check: PASS scan files=<n> strings=<n>`
  python3 tools/story_check.py --table CSV        a UI string table (Key and SourceString columns, card 0.20) matches
                                                   lines.csv: every key has a row with the same id and the same text.
                                                   Prints `story_check: PASS table keys=<n>`
  python3 tools/story_check.py --critic "LINE"     a STORY_CRITIC line is well formed and was made on this exact bible
                                                   and sheet by a session other than the builder's
  python3 tools/story_check.py --calibrate [CSV]   every known-bad row of evals/story-critic/calibration.csv that is
                                                   marked machine=yes fails with its kind; every good row passes
  python3 tools/story_check.py --stuck FILE...     the critic's answers, one file per cycle (oldest first). There is no
                                                   cycle cap (D-new-no-round-cap); prints `story_check: STUCK ...` (exit 4)
                                                   only when the newest story.json stuck_cycles (3) cycles in a row are
                                                   FAIL with the same false rows (the same gap) and no fewer of them,
                                                   else `story_check: not stuck` (exit 0)
  python3 tools/story_check.py --hash              prints `bible=<8 hex> sheet=<8 hex>`
  Options: --root R, --bible F, --lines F, --rules F, --manifest F
Exit 0 = PASS, 1 = problems, 2 = usage or unreadable input, 4 = stuck (--stuck: NEEDS HUMAN to Richard).
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLE = "pipeline/story/story-bible.md"
LINES = "pipeline/story/lines.csv"
RULES = "pipeline/story/story.json"
MANIFEST = "docs/feature-manifest.json"
CALIBRATION = "evals/story-critic/calibration.csv"
COLUMNS = ["id", "surface", "text", "facts", "ship", "note"]
SECTIONS = ["Status words", "Sources", "Names", "Facts", "Open questions", "Tone target", "Tone sheet for other lanes",
            "Never use"]
STATUS = re.compile(r"^(?:GDD|DEFERRED|PROPOSED|OPEN|CONFIRMED \d{4}-\d{2}-\d{2} \((?:Richard|agent default[^)]*)\))$")
SHIPPABLE = re.compile(r"^(?:GDD|CONFIRMED \d{4}-\d{2}-\d{2} \((?:Richard|agent default[^)]*)\))$")
CONFIRMED = re.compile(r"^CONFIRMED \d{4}-\d{2}-\d{2} \((?:Richard|agent default[^)]*)\)$")
SOURCE_ID = re.compile(r"\bS\d+\b")
FACT_ID = re.compile(r"^[A-Z]\d+$")
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
BOUNDARY = set(".?!:;…—–")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]")
CRITIC = re.compile(r"^[ \t>$*-]*STORY_CRITIC: (?P<verdict>PASS|FAIL)\s+lines=(?P<lines>\d+)\s+bible=(?P<bible>[0-9a-f]{8})"
                    r"\s+sheet=(?P<sheet>[0-9a-f]{8})\s+rubric=(?P<rubric>\S+)\s+cycle=(?P<cycle>\d+)"
                    r"\s+builder=(?P<builder>\S+)\s+critic=(?P<critic>\S+)", re.M)
PASS_LINE = re.compile(r"^[ \t>$-]*story_check: PASS bible=(?P<bible>[0-9a-f]{8}) sheet=(?P<sheet>[0-9a-f]{8})"
                       r" lines=(?P<lines>\d+)\b", re.M)
SCAN_PASS = re.compile(r"^[ \t>$-]*story_check: PASS (?:scan files=\d+|bible=)", re.M)
FAIL_LINE = re.compile(r"^[ \t>$-]*story_check: FAIL\b", re.M)


# ---- reading -----------------------------------------------------------------------------------
def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def sha8(text):
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:8]


def split_sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def table_rows(section):
    """Data rows of the first Markdown table in a section, cells split on unescaped pipes (`\\|` stays a pipe)."""
    rows = []
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s.strip("|"))]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def parse_bible(text):
    sec = split_sections(text)
    names, facts, sources = [], {}, {}
    for r in table_rows(sec.get("Sources", "")):
        if r and r[0]:
            sources[r[0]] = " ".join(r[1:])
    for r in table_rows(sec.get("Names", "")):
        r = (r + [""] * 5)[:5]
        names.append({"name": r[0], "kind": r[1], "status": r[2], "source": r[3], "notes": r[4]})
    dup = []
    for r in table_rows(sec.get("Facts", "")):
        r = (r + [""] * 5)[:5]
        if r[0] in facts:
            dup.append(r[0])
        facts[r[0]] = {"fact": r[1], "status": r[2], "source": r[3], "never": r[4]}
    return {"text": text, "sections": sec, "names": names, "facts": facts, "sources": sources, "dup": dup}


def load_rules(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def nar_authorized(manifest_path):
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            m = json.load(fh)
    except (OSError, ValueError):
        return False
    need = {"NAR-04", "NAR-05", "NAR-06", "NAR-07"}   # the rows the shipped lines cite
    ok = {f.get("feature_id") for f in m.get("features") or [] if f.get("implementation_authorized")}
    return need <= ok


def read_lines(text):
    """(rows, problems) from lines.csv text. Each row is a dict with its 1-based line number under '_n'."""
    rd = csv.reader(io.StringIO(text))
    try:
        header = next(rd)
    except StopIteration:
        return [], [("csv", "lines.csv", "empty file; the first line is " + ",".join(COLUMNS))]
    if [h.strip() for h in header] != COLUMNS:
        return [], [("csv", "lines.csv", f"header {header} must be exactly {','.join(COLUMNS)}")]
    rows, out = [], []
    for n, cells in enumerate(rd, start=2):
        if not any(c.strip() for c in cells):
            continue
        if len(cells) != len(COLUMNS):
            out.append(("csv", f"lines.csv:{n}", f"{len(cells)} columns, want {len(COLUMNS)} (quote text with commas)"))
            continue
        row = {k: v.strip() for k, v in zip(COLUMNS, cells)}
        row["_n"] = n
        rows.append(row)
    return rows, out


# ---- text rules --------------------------------------------------------------------------------
def word_hits(text, terms):
    return [t for t in terms if re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", text, re.I)]


def name_words(bible):
    words = set()
    for n in bible["names"]:
        words |= set(WORD.findall(n["name"]))
    return words


def text_problems(text, where, rules, bible, check_names=True):
    """Problems any player-facing string can have, whatever file it sits in."""
    out = []
    for t in word_hits(text, [d["term"] for d in rules.get("deny") or []]):
        why = next(d.get("why", "") for d in rules["deny"] if d["term"] == t)
        out.append(("deny", where, f"'{t}' is on the deny list ({why}); never write it"))
    for t in word_hits(text, rules.get("banned_words") or []):
        out.append(("banned", where, f"off-tone word '{t}' (story.json banned_words; bible Tone target)"))
    n = text.count("!")
    if n > int(rules.get("max_exclaim", 0)):
        out.append(("exclaim", where, f"{n} exclamation mark(s); the tone allows {rules.get('max_exclaim', 0)}"))
    allow = set(rules.get("allow_caps") or [])
    names = name_words(bible) if bible else set()
    for w in WORD.findall(text):
        if len(w) > int(rules.get("max_caps_run", 3)) and w.isupper() and w not in allow and w not in names:
            out.append(("caps", where, f"shouting capitals '{w}'"))
    if EMOJI.search(text):
        out.append(("emoji", where, f"emoji or pictograph '{EMOJI.search(text).group(0)}'"))
    if check_names:
        for w in mid_sentence_caps(text):
            if w not in allow and w not in names:
                out.append(("name", where, f"'{w}' looks like a name and is not in the bible's Names table "
                                           "(add it there as PROPOSED, or rewrite)"))
    return out


def mid_sentence_caps(text):
    """Capitalised words that do not start a sentence. Format placeholders such as {Key} are removed first, so the
    word after a leading placeholder counts as the start ("{Key} Open umbrella")."""
    text = re.sub(r"\{[^{}]*\}", "", text)
    out = []
    for m in WORD.finditer(text):
        w = m.group(0)
        if not w[0].isupper() or w.isupper():   # ALL-CAPS words are the caps rule's, not names
            continue
        before = text[:m.start()].rstrip(" \t\"'“‘(")
        if not before or before[-1] in BOUNDARY or before.endswith("\n"):
            continue
        out.append(w)
    return out


def never_say(bible, rules):
    """(fact id, compiled regex, why) for every contradiction: story.json's GDD ones plus the bible's Never-say cells."""
    out = []
    for c in rules.get("contradictions") or []:
        out.append((c["fact"], re.compile(c["regex"], re.I), c.get("why", "")))
    for fid, f in bible["facts"].items():
        if f["never"]:
            try:
                out.append((fid, re.compile(f["never"], re.I), f["fact"]))
            except re.error:
                pass   # reported by bible_problems
    return out


# ---- the two files -----------------------------------------------------------------------------
def bible_problems(bible, rules):
    out = []
    sec = bible["sections"]
    for s in SECTIONS:
        if s not in sec:
            out.append(("bible", BIBLE, f"missing section '## {s}'"))
    if not bible["names"]:
        out.append(("bible", BIBLE, "the Names table has no rows"))
    if not bible["facts"]:
        out.append(("bible", BIBLE, "the Facts table has no rows"))
    for d in bible["dup"]:
        out.append(("bible", BIBLE, f"fact {d} appears twice"))
    rows = [("name", n["name"], n["status"], n["source"]) for n in bible["names"]]
    rows += [("fact", fid, f["status"], f["source"]) for fid, f in bible["facts"].items()]
    for kind, key, status, source in rows:
        where = f"{BIBLE} {kind} '{key}'"
        if kind == "fact" and not FACT_ID.match(key):
            out.append(("bible", where, "fact ID must be a letter and a number (F1, P3)"))
        if not STATUS.match(status):
            out.append(("bible", where, f"status '{status}' is not GDD, DEFERRED, PROPOSED, OPEN or "
                                        "'CONFIRMED <YYYY-MM-DD> (Richard)'"))
        ids = SOURCE_ID.findall(source)
        if not source.strip():
            out.append(("bible", where, "no source"))
        for sid in ids:
            if sid not in bible["sources"]:
                out.append(("bible", where, f"source {sid} is not in the Sources table"))
        if status in ("GDD", "DEFERRED") and not any("GDD" in bible["sources"].get(s, "") for s in ids):
            out.append(("bible", where, f"a {status} row cites a GDD source (a Sources row that names the GDD)"))
    for fid, f in bible["facts"].items():
        if f["never"]:
            try:
                re.compile(f["never"])
            except re.error as e:
                out.append(("bible", f"{BIBLE} fact '{fid}'", f"Never-say regex does not compile: {e}"))
    for c in rules.get("contradictions") or []:
        f = bible["facts"].get(c["fact"])
        if not f or f["status"] != "GDD":
            out.append(("bible", RULES, f"contradiction for {c['fact']} needs a GDD row {c['fact']} in the bible's Facts"))
    never_use = sec.get("Never use", "")
    rest = "\n".join(v for k, v in sec.items() if k != "Never use")
    for d in rules.get("deny") or []:
        if word_hits(rest, [d["term"]]):
            out.append(("deny", BIBLE, f"'{d['term']}' is on the deny list; it may appear only under '## Never use'"))
        if not word_hits(never_use, [d["term"]]):
            out.append(("deny", BIBLE, f"'## Never use' does not list deny-list term '{d['term']}'"))
    return out


def line_problems(rows, bible, rules, nar_ok):
    out = []
    surfaces = rules.get("surfaces") or {}
    seen = set()
    contra = never_say(bible, rules)
    status_of_name = {n["name"]: n["status"] for n in bible["names"]}
    for r in rows:
        where = f"lines.csv:{r['_n']} {r['id'] or '<no id>'}"
        if not r["id"]:
            out.append(("csv", where, "no id"))
        elif r["id"] in seen:
            out.append(("csv", where, "duplicate id"))
        seen.add(r["id"])
        sf = surfaces.get(r["surface"])
        if sf is None:
            out.append(("surface", where, f"surface '{r['surface']}' is not one of {', '.join(surfaces)}"))
        if r["ship"] not in ("yes", "no"):
            out.append(("csv", where, f"ship '{r['ship']}' must be yes or no"))
        text = r["text"]
        if not text:
            out.append(("csv", where, "empty text"))
            continue
        out += text_problems(text, where, rules, bible)
        words = len(WORD.findall(text))
        if sf and words > sf["max_words"]:
            out.append(("length", where, f"{words} words; a {r['surface']} allows {sf['max_words']}"))
        for fid, rx, why in contra:
            if rx.search(text):
                out.append(("contradiction", where, f"contradicts {fid}: {why}"))
        cited = [f.strip() for f in re.split(r"[;\s]+", r["facts"]) if f.strip()]
        for fid in cited:
            if fid not in bible["facts"]:
                out.append(("fact", where, f"cites {fid}, which is not in the bible's Facts"))
        if sf and sf.get("story") and not cited:
            out.append(("fact", where, f"a {r['surface']} line is narrative: cite the bible fact(s) it tells"))
        if r["ship"] == "yes":
            for fid in cited:
                st = bible["facts"].get(fid, {}).get("status", "")
                if fid in bible["facts"] and not SHIPPABLE.match(st):
                    out.append(("ship", where, f"ship=yes but fact {fid} is {st}; only GDD or CONFIRMED (Richard) ships"))
            for name, st in status_of_name.items():
                if name[:1].isupper() and re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", text) \
                        and not SHIPPABLE.match(st):
                    out.append(("ship", where, f"ship=yes but name '{name}' is {st}; only GDD or CONFIRMED (Richard) ships"))
            if sf and sf.get("story") and not nar_ok:
                out.append(("nar", where, "ship=yes on a narrative surface while NAR-01 is DEFERRED / not "
                                          "implementation_authorized (docs/feature-manifest.json)"))
    return out


def scan_problems(paths, rules, bible):
    """(problems, strings) for text files outside lines.csv. A CSV with a SourceString or text column is read per cell
    (a string table): names are checked too. Any other file is read whole: deny, banned, exclaim, caps, emoji."""
    out, strings = [], 0
    for p in paths:
        text = read_text(p)
        if p.lower().endswith(".csv"):
            rd = list(csv.reader(io.StringIO(text)))
            head = [h.strip() for h in rd[0]] if rd else []
            col = next((head.index(c) for c in ("SourceString", "text") if c in head), None)
            if col is not None:
                for n, cells in enumerate(rd[1:], start=2):
                    if col < len(cells) and cells[col].strip():
                        strings += 1
                        out += text_problems(cells[col], f"{p}:{n}", rules, bible)
                continue
        for n, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                strings += 1
                out += [x for x in text_problems(line, f"{p}:{n}", rules, bible, check_names=False)
                        if x[0] in ("deny", "banned", "emoji")]
    return out, strings


def table_problems(path, rows):
    """Every Key of a UI string table has a lines.csv row with that id and exactly that text."""
    rd = list(csv.reader(io.StringIO(read_text(path))))
    head = [h.strip() for h in rd[0]] if rd else []
    if "Key" not in head or "SourceString" not in head:
        return [("csv", path, "a string table needs Key and SourceString columns")], 0
    k, s = head.index("Key"), head.index("SourceString")
    by_id = {r["id"]: r for r in rows}
    out, n = [], 0
    for i, cells in enumerate(rd[1:], start=2):
        if len(cells) <= max(k, s) or not cells[k].strip():
            continue
        n += 1
        key, text = cells[k].strip(), cells[s].strip()
        row = by_id.get(key)
        if row is None:
            out.append(("table", f"{path}:{i}", f"key {key} has no row in {LINES}; the Story role writes every string"))
        elif row["text"] != text:
            out.append(("table", f"{path}:{i}", f"key {key} reads {text!r}, but {LINES} says {row['text']!r}"))
    return out, n


def critic_problems(line, rules, bible_hash, sheet_hash, n_lines):
    m = CRITIC.search(line or "")
    if not m:
        return ["not a STORY_CRITIC line: `STORY_CRITIC: PASS|FAIL lines=<n> bible=<8 hex> sheet=<8 hex> "
                "rubric=<version> cycle=<n> builder=<session> critic=<session>`"]
    out = []
    if m.group("bible") != bible_hash or m.group("sheet") != sheet_hash:
        out.append(f"critic judged bible={m.group('bible')} sheet={m.group('sheet')}, but the files are now "
                   f"bible={bible_hash} sheet={sheet_hash}: re-run the critic on this version")
    if int(m.group("lines")) != n_lines:
        out.append(f"critic judged {m.group('lines')} line(s); lines.csv has {n_lines}")
    if m.group("rubric") != rules.get("rubric_version"):
        out.append(f"rubric {m.group('rubric')} is not the current {rules.get('rubric_version')}")
    if int(m.group("cycle")) < 1:   # no cycle cap (D-new-no-round-cap); --stuck decides when a human looks
        out.append(f"cycle {m.group('cycle')}: cycles count from 1")
    if m.group("builder") == m.group("critic"):
        out.append("builder and critic are the same session; the critic is a separate, fresh session")
    if m.group("verdict") != "PASS":
        out.append("the critic's verdict is FAIL")
    return out


ROW_FALSE = re.compile(r"\b(S\d+)\s+false\b")
ROW_LINE = re.compile(r"^[ \t>*-]*(?P<id>[\w.-]+):\s*S1\s+(?:true|false)\b.*$", re.M)


def critic_round(text):
    """(verdict, false rows) of one critic answer: the verdict line and every `<id>: S1 .. | Sn false ...` row."""
    m = CRITIC.search(text or "")
    if not m:
        raise ValueError("no STORY_CRITIC line in the critic's answer")
    falses = sorted((r.group("id"), f) for r in ROW_LINE.finditer(text) for f in ROW_FALSE.findall(r.group(0)))
    return m.group("verdict"), falses


def stuck(rounds, n=3):
    """True when the newest n critic rounds (oldest first; each (verdict, false rows)) are FAIL in a row with the same
    false rows (the same gap) and no fewer of them than the round before (D-new-no-round-cap). No cycle cap."""
    tail = rounds[-n:]
    if len(tail) < n or any(v != "FAIL" for v, _ in tail):
        return False
    return all(a[1] == b[1] and len(b[1]) >= len(a[1]) for a, b in zip(tail, tail[1:]))


def calibrate(path, rules, bible):
    """Known-bad rows marked machine=yes must fail with their kind; rows with kind 'none' must pass."""
    out, n = [], 0
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for i, r in enumerate(rows, start=2):
        n += 1
        row = {k: (r.get(k) or "").strip() for k in COLUMNS}
        row["_n"] = i
        got = {k for k, _, _ in line_problems([row], bible, rules, nar_ok=False)}
        want = (r.get("kind") or "").strip()
        if want == "none":
            if got:
                out.append(f"{path}:{i} {row['id']}: a good row fails story_check ({', '.join(sorted(got))})")
        elif (r.get("machine") or "").strip() == "yes" and want not in got:
            out.append(f"{path}:{i} {row['id']}: story_check misses '{want}' (got {', '.join(sorted(got)) or 'nothing'})")
    return out, n


# ---- main --------------------------------------------------------------------------------------
def run(root, bible_p, lines_p, rules_p, manifest_p):
    bible_text, lines_text = read_text(bible_p), read_text(lines_p)
    bible, rules = parse_bible(bible_text), load_rules(rules_p)
    rows, out = read_lines(lines_text)
    out = bible_problems(bible, rules) + out
    out += line_problems(rows, bible, rules, nar_authorized(manifest_p))
    return out, sha8(bible_text), sha8(lines_text), len(rows), bible


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--bible")
    ap.add_argument("--lines")
    ap.add_argument("--rules")
    ap.add_argument("--manifest")
    ap.add_argument("--scan", nargs="+", metavar="FILE")
    ap.add_argument("--critic", metavar="LINE")
    ap.add_argument("--table", metavar="CSV")
    ap.add_argument("--calibrate", nargs="?", const="", metavar="CSV")
    ap.add_argument("--hash", action="store_true")
    ap.add_argument("--stuck", nargs="+", metavar="FILE")
    a = ap.parse_args(argv)
    j = lambda p, d: p or os.path.join(a.root, d)   # noqa: E731
    bible_p, lines_p, rules_p, manifest_p = j(a.bible, BIBLE), j(a.lines, LINES), j(a.rules, RULES), j(a.manifest, MANIFEST)
    try:
        if a.stuck:
            n = int(load_rules(j(a.rules, RULES)).get("stuck_cycles", 3))
            rounds = [critic_round(read_text(f)) for f in a.stuck]
            if stuck(rounds, n):
                gap = ", ".join(f"{i} {k}" for i, k in rounds[-1][1][:6])
                print(f"story_check: STUCK cycles={len(rounds)} last {n} FAIL with the same false rows ({gap}) and no "
                      "fewer: log the gap on the card, set it needs-human, ask Richard (NEEDS HUMAN)")
                return 4
            print(f"story_check: not stuck cycles={len(rounds)} (no cycle cap: the loop runs until PASS)")
            return 0
        if a.scan:
            rules, bible = load_rules(rules_p), parse_bible(read_text(bible_p))
            found, strings = scan_problems(a.scan, rules, bible)
            for k, w, m in found:
                print(f"- [{k}] {w}: {m}")
            print(f"story_check: {'PASS' if not found else 'FAIL ' + str(len(found)) + ' problem(s)'} "
                  f"scan files={len(a.scan)} strings={strings}")
            return 1 if found else 0
        found, bh, sh, n, bible = run(a.root, bible_p, lines_p, rules_p, manifest_p)
        rules = load_rules(rules_p)
        if a.hash:
            print(f"bible={bh} sheet={sh}")
            return 0
        if a.table:
            rows, bad = read_lines(read_text(lines_p))
            probs, keys = table_problems(a.table, rows)
            probs = bad + probs
            for k, w, m in probs:
                print(f"- [{k}] {w}: {m}")
            print(f"story_check: {'PASS' if not probs else 'FAIL ' + str(len(probs)) + ' problem(s)'} table keys={keys}")
            return 1 if probs else 0
        if a.critic is not None:
            probs = critic_problems(a.critic, rules, bh, sh, n)
            for p in probs:
                print("- " + p)
            print("story_check: critic line ok" if not probs else f"story_check: critic line FAIL {len(probs)} problem(s)")
            return 1 if probs else 0
        if a.calibrate is not None:
            probs, rows = calibrate(a.calibrate or os.path.join(a.root, CALIBRATION), rules, bible)
            for p in probs:
                print("- " + p)
            print(f"story_check: calibrate {'PASS' if not probs else 'FAIL'} rows={rows}")
            return 1 if probs else 0
    except (OSError, ValueError, KeyError, IndexError) as e:
        print(f"story_check: cannot read input: {e}", file=sys.stderr)
        return 2
    for k, w, m in found:
        print(f"- [{k}] {w}: {m}")
    names, facts = len(bible["names"]), len(bible["facts"])
    if found:
        print(f"story_check: FAIL {len(found)} problem(s) bible={bh} sheet={sh} lines={n}")
        return 1
    print(f"story_check: PASS bible={bh} sheet={sh} lines={n} names={names} facts={facts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

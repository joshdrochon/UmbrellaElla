#!/usr/bin/env python3
"""Story inventory: every piece of player text the game ships is a row in pipeline/story/lines.csv (Josh, Nov 12). Stdlib only.

  story_inventory.py [check]   FAIL lines (exit 1) for
                                 - shipped player text with no lines.csv row (the row's text must equal the source),
                                 - a lines.csv row whose text is in no shipped source (changed or removed in the source);
                               PASS otherwise
  story_inventory.py write     append a row for every shipped text that has none (id, surface, screen in the note)
  story_inventory.py list      print the shipped texts: screen, kind, text
  story_inventory.py summary   TOTAL=<rows> and the count per screen (rows carry `screen=<name>` in the note)

What counts as shipped player text (non-test C++ under Source/, plus Content/UmbrellaElla/UI/Story/StoryCues.tsv):
  LOCTEXT / NSLOCTEXT / INVTEXT literals; FText::FromString(TEXT("...")) (also `c ? TEXT("a") : TEXT("b")`);
  FlowTutorialLine(TEXT("...")); StoryStatsRows labels (Rows.Emplace(TEXT("label"), ...)); credit lines
  (Lines.Add({TEXT(name), TEXT(role)}) shown as "name - role"); the default story table inside StoryRules.cpp and
  StoryCues.tsv (the text column). A literal needs a word of 3+ letters; pure numbers/format strings ("{0}%", "-") are not text.
Dev-only text is excluded (SoundLabelHud, Smoke, Harness, Tests, Debug). Formatted lines are kept as the source template
("Level {0}   Points left {1}", "Level %d").
"""
import csv
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LINES = "pipeline/story/lines.csv"
CUES = "Content/UmbrellaElla/UI/Story/StoryCues.tsv"
COLUMNS = ["id", "surface", "text", "facts", "ship", "note"]
SKIP_PARTS = ("/Tests/", "/Smoke/", "/Harness/", "SoundLabel", "Debug")
STR = r'"((?:[^"\\]|\\.)*)"'
PATTERNS = [
    ("loctext", re.compile(r'\bLOCTEXT\(\s*"\w+"\s*,\s*' + STR + r'\s*\)')),
    ("loctext", re.compile(r'\bNSLOCTEXT\(\s*"[^"]*"\s*,\s*"\w+"\s*,\s*' + STR + r'\s*\)')),
    ("loctext", re.compile(r'\bINVTEXT\(\s*' + STR + r'\s*\)')),
    ("fromstring", re.compile(r'FText::FromString\(\s*TEXT\(\s*' + STR + r'\s*\)\s*\)')),
    ("fromstring", re.compile(r'FText::FromString\([^;]*?\?\s*TEXT\(\s*' + STR + r'\s*\)\s*:\s*TEXT\(\s*' + STR + r'\s*\)')),
    ("tutorial", re.compile(r'FlowTutorialLine\(\s*TEXT\(\s*' + STR + r'\s*\)\s*\)')),
    ("stat-label", re.compile(r'Rows\.Emplace\(\s*TEXT\(\s*' + STR + r'\s*\)')),
]
CREDIT = re.compile(r'Lines\.Add\(\{\s*TEXT\(\s*' + STR + r'\s*\)\s*,\s*(?:TEXT\(\s*' + STR + r'\s*\)|FString\(\))\s*\}\)')
TSV_IN_CODE = re.compile(r'TEXT\("(\w+)\\t([\w.]+)\\t[\d.]+\\t[\d.]+\\t((?:[^"\\]|\\.)*?)\\n"\)')
FLOW_MENU_FN = re.compile(r'FFlowMenuText::(\w+)\(')
SCREEN_OF_MENU_FN = {"TitleHeading": "title", "StartGameLabel": "title", "DirectorsCutLabel": "title",
                     "PausedHeading": "pause", "ContinueLabel": "pause", "SettingsLabel": "pause", "QuitLabel": "pause",
                     "SettingsHeading": "settings", "SettingsStubBody": "settings", "BackLabel": "settings",
                     "LevelUpHeading": "level-up", "LevelUpBody": "level-up", "DoneLabel": "level-up", "SkipLabel": "level-up",
                     "DefeatHeading": "defeat", "RetryLabel": "defeat", "QuitToTitleLabel": "defeat"}
SCREEN_OF_FILE = {"SettingsMenuWidget": "settings", "SettingsModel": "settings-controller",
                  "DeveloperOptions": "settings-game-options", "ProgressionPurchaseWidget": "purchase",
                  "FlowTutorialText": "tutorial", "StoryWidgets": "journey-complete", "StoryRules": "journey-complete"}


def unescape(s):
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def is_text(s):
    return re.search(r"[A-Za-z]{3}", re.sub(r"\{\d+\}|%[-+0-9.]*[dfsi]", "", s)) is not None


def source_files():
    for base, _, names in os.walk(os.path.join(ROOT, "Source")):
        for n in sorted(names):
            rel = os.path.relpath(os.path.join(base, n), ROOT).replace(os.sep, "/")
            if n.endswith((".cpp", ".h")) and not any(p in "/" + rel for p in SKIP_PARTS):
                yield rel


def screen_for(rel, text_src, pos, kind):
    stem = os.path.splitext(os.path.basename(rel))[0]
    if stem == "FlowMenuText":
        line_start = text_src.rfind("\n", 0, pos) + 1
        m = FLOW_MENU_FN.search(text_src[line_start:pos + 1]) or FLOW_MENU_FN.search(text_src[line_start:text_src.find("\n", pos)])
        return SCREEN_OF_MENU_FN.get(m.group(1), "flow-menu") if m else "flow-menu"
    if stem == "FlowStoryText":
        return "ending" if "GetEndingPages" in text_src[max(0, pos - 400):pos].split("FFlowStoryText::")[-1] else "credits"
    if stem == "UmbrellaPlayerController":
        return "hud" if "Director's Cut" in text_src[pos:pos + 80] else "tutorial"
    return SCREEN_OF_FILE.get(stem, stem)


def shipped():
    """Every shipped player text: [{text, screen, kind, where}], in source order, duplicates kept."""
    out = []
    for rel in source_files():
        src = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
        for kind, rx in PATTERNS:
            for m in rx.finditer(src):
                for g in m.groups():
                    t = unescape(g)
                    if is_text(t):
                        out.append({"text": t, "screen": screen_for(rel, src, m.start(), kind), "kind": kind, "where": rel, "at": m.start()})
        if rel.endswith("SettingsModel.cpp"):
            for m in CREDIT.finditer(src):
                name, role = unescape(m.group(1)), unescape(m.group(2) or "")
                out.append({"text": f"{name} - {role}" if role else name, "screen": "credits", "kind": "credit", "where": rel, "at": m.start()})
        if rel.endswith("StoryRules.cpp"):
            for m in TSV_IN_CODE.finditer(src):
                out.append({"text": unescape(m.group(3)), "screen": tsv_screen(m.group(2)), "kind": "story-table", "where": rel, "at": m.start()})
    for line in open(os.path.join(ROOT, CUES), encoding="utf-8") if os.path.exists(os.path.join(ROOT, CUES)) else []:
        if line.startswith("#") or not line.strip():
            continue
        cols = line.rstrip("\n").split("\t")
        if len(cols) >= 5:
            out.append({"text": cols[4], "screen": tsv_screen(cols[1]), "kind": "story-table", "where": CUES, "at": 0})
    return out


def tsv_screen(trigger):
    return "ending" if trigger.startswith("Ending") else "opening" if trigger.startswith("ModeSelected") else "in-world"


def read_rows():
    path = os.path.join(ROOT, LINES)
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def distinct(items):
    seen, out = set(), []
    for it in items:
        if it["text"] not in seen:
            seen.add(it["text"])
            out.append(it)
    return out


def problems(items=None, rows=None):
    items = shipped() if items is None else items
    rows = read_rows() if rows is None else rows
    have = {r["text"] for r in rows}
    want = {i["text"] for i in items}
    out = []
    for it in distinct(items):
        if it["text"] not in have:
            out.append(f"FAIL [missing] {it['where']} ({it['screen']}): shipped text not in {LINES}: {it['text']!r}")
    for r in rows:
        if r["text"] not in want:
            out.append(f"FAIL [differs] {LINES} row {r['id']}: text is in no shipped source (source changed or removed): {r['text']!r}")
    return out


def slug(text, taken):
    words = re.findall(r"[a-z0-9]+", text.lower())[:5] or ["text"]
    base = "-".join(words)[:40].strip("-")
    out, n = base, 2
    while out in taken:
        out, n = f"{base}-{n}", n + 1
    return out


# First words that make a short UI text an action (a button); anything else short is a label (names a thing).
LABEL_ACTIONS = {"Start", "Play", "Resume", "Restart", "Quit", "Back", "Confirm", "Cancel", "Save", "Discard", "Keep", "Reset",
                 "Open", "Skip", "Done", "Next", "Begin", "Retry", "Continue", "Try", "Main", "Sound", "Controller", "Credits",
                 "Game", "Settings"}


# Short texts that head a screen or state a status; they are screen lines, not labels or buttons.
HEADING_TEXTS = {"Paused", "Defeated", "Journey Complete", "Unsaved changes."}


def surface_of(it):
    t, screen = it["text"], it["screen"]
    words = len(t.split())
    if screen == "title" and "\n" in t:
        return "title"
    if screen == "ending" and it["kind"] != "story-table":
        return "end_card"
    if it["kind"] == "story-table":
        return "end_card" if screen == "ending" else "clue"
    if t in HEADING_TEXTS:
        return "screen"
    if screen == "settings-controller":
        return "label"
    if words <= 3 and t.split()[0] in LABEL_ACTIONS:
        return "button"
    if words <= 4:
        return "label"
    return "screen"


def facts_of(it):
    if it["screen"] == "ending" and it["kind"] != "story-table":
        return "F3;P8"
    return ""


def new_rows(items, rows):
    have = {r["text"] for r in rows}
    taken = {r["id"] for r in rows}
    out, page = [], 0
    for it in distinct(items):
        if it["text"] in have:
            continue
        if it["screen"] == "ending" and it["kind"] != "story-table":
            page += 1
            rid = f"story-ending-page-{page}"
        else:
            prefix = "credit" if it["screen"] == "credits" else "ui-" + it["screen"]
            rid = f"{prefix}-{slug(it['text'], set())}"
            n = 2
            while rid in taken:
                rid, n = f"{prefix}-{slug(it['text'], set())}-{n}", n + 1
        taken.add(rid)
        note = f"screen={it['screen']}; where={os.path.basename(it['where'])}"
        out.append({"id": rid, "surface": surface_of(it), "text": it["text"], "facts": facts_of(it), "ship": "yes", "note": note})
    return out


def write():
    rows = read_rows()
    add = new_rows(shipped(), rows)
    with open(os.path.join(ROOT, LINES), "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        for r in add:
            w.writerow(r)
    print(f"story_inventory: added {len(add)} rows")


def screen_counts(rows, items):
    by_text = {i["text"]: i["screen"] for i in items}
    counts = {}
    for r in rows:
        m = re.search(r"screen=([\w-]+)", r["note"] or "")
        s = m.group(1) if m else by_text.get(r["text"], "story")
        counts[s] = counts.get(s, 0) + 1
    return counts


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "write":
        write()
        return 0
    if cmd == "list":
        for it in shipped():
            print(f"{it['screen']}\t{it['kind']}\t{it['text']!r}")
        return 0
    if cmd == "summary":
        rows = read_rows()
        counts = screen_counts(rows, shipped())
        print(f"TOTAL={len(rows)} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        return 0
    if cmd != "check":
        print(__doc__)
        return 2
    bad = problems()
    for b in bad:
        print(b)
    print(f"story_inventory: {'FAIL' if bad else 'PASS'} shipped={len(distinct(shipped()))} rows={len(read_rows())} problems={len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

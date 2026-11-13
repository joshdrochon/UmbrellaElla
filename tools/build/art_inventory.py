#!/usr/bin/env python3
"""Art inventory: every visual the game ships has an art-loop piece (Josh, Nov 12). Stdlib only.

  art_inventory.py [check]     FAIL lines for a shipped visual with no piece (exit 1); PASS otherwise
  art_inventory.py write       also rewrite docs/build/art-inventory.csv
  art_inventory.py summary     one line for the progress bar: TOTAL=<n> PASSED=<m> plus the count per owner lane
  art_inventory.py list        print the rows

Two sources feed the list of shipped visuals:
  1. the GDD: ANIM/ART/BG/VFX/UI rows of docs/gdd (STATIC below, each names its Rule ID; the Rule IDs must exist in
     docs/feature-manifest.json);
  2. what the code and the art folders actually carry: Source enums and tables (Ella and enemy presenters, screens,
     VFX catalogue, backdrop layers, widgets) and every file under Art/ and Content/*/Art.
A new enum value, sheet, layer, screen, widget or art file that no mapping below names is a FAIL, the same rule
tools/ui_check.py uses for screens. A visual whose piece is not an element of pipeline/art/references.json, or whose
piece has no owner lane, is a FAIL too. docs/build/art-inventory.csv must match the regenerated rows.

`passed` comes from the art loop's recorded verdicts (Saved/Logs/pipeline/art-loop.jsonl of this tree and of the
sibling area worktrees): the piece's newest round is ours or same, its checks passed, no pair is missing.
"""
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
CSV = os.path.join("docs", "build", "art-inventory.csv")
LOG = os.path.join("Saved", "Logs", "pipeline", "art-loop.jsonl")
LANES = ("artella", "artkeeper", "artscene", "artui", "artshots", "artfx", "artenemy")
HEADER = ["visual", "source", "piece", "owner", "passed"]

# Owner lane of the pieces that existed before the inventory (a new piece carries `owner` in references.json).
OWNERS = {
    "ella-up-open": "artella", "ella-closed": "artella", "ella-attack": "artella", "ella-shield": "artella",
    "umbrella": "artella", "umbrella-repair": "artella", "owl": "artkeeper",
    "owl-bolt": "artshots", "bolt-hit": "artshots", "wand-shot": "artshots", "wind-zone": "artshots",
    "wind-lines": "artshots", "scene": "artscene", "skyline": "artscene", "paper": "artscene",
    "menu-screen": "artscene",
}

# ---- 1. the GDD rows that name a visual no code scan sees: (visual, rule ids, piece) ----
STATIC = [
    ("ella:free-fall", "ANIM-03", "ella-closed"),
    ("ella:hop-cartwheel-dash", "ANIM-03", "ella-motion"),
    ("ella:mode-transition", "ANIM-03", "ella-transition"),
    ("ella:condition-100-to-0", "ANIM-04", "ella-condition"),
    ("ella:living-critical", "ANIM-04", "ella-condition"),
    ("umbrella:prop", "ART-06", "umbrella"),
    ("umbrella:repair", "ANIM-03", "umbrella-repair"),
    ("keeper:body-hover-flap", "ANIM-06", "owl"),
    ("keeper:clock-cover-glass-hands", "ANIM-06", "keeper-clock"),
    ("keeper:talon-empty-and-closed", "ANIM-06", "keeper-talon"),
    ("keeper:wings-gust-wear", "ANIM-06", "keeper-wing"),
    ("keeper:mechanism-front", "ANIM-06", "keeper-mech-front"),
    ("keeper:mechanism-middle", "ANIM-06", "keeper-mech-middle"),
    ("keeper:mechanism-rear", "ANIM-06", "keeper-mech-rear"),
    ("keeper:part-masks-7-6-4-0", "ANIM-06", "keeper-damage"),
    ("keeper:living-departure", "ANIM-06", "keeper-departure"),
    ("shot:red", "VFX-04", "owl-bolt"),
    ("shot:red-impact", "VFX-04", "bolt-hit"),
    ("shot:gold", "ANIM-05", "wand-shot"),
    ("shot:yellow", "VFX-04", "yellow-shot"),
    ("shot:stream-beam", "ANIM-05", "stream-beam"),
    ("wind:current-field", "ANIM-08", "wind-zone"),
    ("wind:decor-lines", "ART-06", "wind-lines"),
    ("bg:atmosphere", "BG-03", "bg-atmosphere"),
    ("bg:water", "BG-03", "bg-water"),
    ("bg:clocks", "BG-03", "bg-clock"),
    ("bg:land", "BG-04", "bg-land"),
    ("bg:start-end", "ART-04", "bg-start-end"),
    ("world:refuge-and-yellow-bay", "ANIM-08", "world-refuge"),
    ("world:solids", "ANIM-08", "world-solids"),
    ("world:mill-and-traps", "ANIM-08", "world-mill"),
    ("scene:gameplay-frame", "ART-07", "scene"),
    ("ui:xp-ring", "ART-08", "ui-xp-ring"),
    ("ui:spell-wheel", "ART-08", "ui-spell-wheel"),
    ("ui:device-and-remap-prompts", "ART-08", "ui-settings"),
]

# ---- 2. code-derived visuals: scan -> visual id, and the piece that judges it ----
ELLA_STATE = {"Idle": "ella-up-open", "Shoot": "ella-attack", "Absorb": "ella-shield", "Hurt": "ella-hurt",
              "Down": "ella-down"}
SCREEN = {"Title": "ui-title", "Playing": "ui-hud-clock", "Paused": "ui-pause", "Settings": "ui-settings",
          "Resuming": "ui-pause", "Defeat": "ui-defeated", "Story": "ui-story-text", "Credits": "ui-credits",
          "Tutorial": "ui-tutorial", "TutorialPaused": "ui-tutorial", "Purchase": "ui-purchase",
          "LevelUp": "ui-level-up", "Statistics": "ui-journey-complete"}
BACKDROP_LAYER = {"Sky": "paper", "FarLand": "skyline", "Base": "bg-base", "NearArchitecture": "bg-architecture",
                  "ClockWaterWind": "bg-clock-water-wind"}
FLOW_BACKDROP = {"Drift": "menu-screen", "Clocks": "ui-pause"}
ENEMY_FAMILY = {"SundialCaster": "enemy-sundial", "ArmillaryLauncher": "enemy-armillary",
                "EscapementRepeater": "enemy-repeater", "Floodstrider": "enemy-floodstrider",
                "SkyCourier": "enemy-courier"}
VFX_SHEET = {
    "VFX_GoldRelease": "wand-shot", "VFX_GoldTravel": "wand-shot", "VFX_TwinStarHead": "wand-shot",
    "VFX_GoldImpact": "vfx-gold-impact", "VFX_GoldFade": "vfx-gold-fade", "VFX_StreamStart": "vfx-stream-start",
    "VFX_StreamSustain": "vfx-stream-sustain", "VFX_NeedleChannel": "vfx-needle-channel",
    "VFX_NeedleSliver": "vfx-needle-sliver", "VFX_NeedlePierce": "vfx-needle-pierce", "VFX_Blocked": "vfx-blocked",
    "VFX_KeeperWarning": "vfx-keeper-warning", "VFX_KeeperStrike": "vfx-keeper-strike",
    "VFX_KeeperRecovery": "vfx-keeper-recovery", "VFX_ClockBeat": "vfx-clock-beat", "VFX_ClockOpen": "vfx-clock-open",
    "VFX_PartHit": "vfx-part-hit", "VFX_PartBreak": "vfx-part-break", "VFX_EyeExposed": "vfx-eye-exposed",
    "VFX_Stun": "vfx-stun", "VFX_Slow": "vfx-slow", "VFX_Gust": "vfx-gust", "VFX_GustPuff": "vfx-gust-puff",
    "VFX_Blackout": "vfx-blackout", "VFX_Restoration": "vfx-restoration", "VFX_Departure": "vfx-departure",
    "VFX_LightShaft": "vfx-light-shaft", "VFX_Umbra": "vfx-umbra",
}
MATERIAL = {"M_VFX_Sheet": "vfx-light-spill", "M_VFX_Spill": "vfx-light-spill"}
# A widget class (UUserWidget, SCompoundWidget, SLeafWidget, AHUD) is a visual; the piece judges its screen.
WIDGET = {"USettingsMenuWidget": "ui-settings", "UXpRingWidget": "ui-xp-ring",
          "UStoryCaptionWidget": "ui-story-text", "UJourneyCompleteWidget": "ui-journey-complete",
          "AUmbrellaHUD": "ui-hud-clock", "SFlowBackground": "menu-screen", "SFlowMenu": "ui-title",
          "SFlowTextScreen": "ui-credits", "UProgressionPurchaseWidget": "ui-purchase"}
# Files under Art/ and Content/*/Art: (regex on the repo-relative path, visual id; {1} = first group).
FILE_RULES = [
    (r"^Art/Source/VFX/Raw/(VFX_\w+?)(?:_PH)?\.png$", "vfx-sheet:{1}"),
    (r"^Content/[^/]+/Art/VFX/T_(VFX_\w+?)(?:_PH)?\.uasset$", "vfx-sheet:{1}"),
    (r"^Content/[^/]+/Art/VFX/(M_VFX_\w+?)(?:_PH)?\.uasset$", "vfx-material:{1}"),
    (r"^Art/Source/Keeper/", "keeper:body-hover-flap"),
]
NOT_ART = (".json", ".py", ".md", ".txt", ".csv", ".meta", ".sh", ".blend1", ".log")


def rd(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def enum_values(rel, name):
    m = re.search(r"enum class %s\b[^{]*\{(.*?)\};" % name, rd(rel), re.S)
    if not m:
        return []
    body = re.sub(r"/\*.*?\*/|//[^\n]*", "", m.group(1), flags=re.S)
    return [v.split("=")[0].strip() for v in body.split(",") if v.split("=")[0].strip()]


def art_files():
    out = []
    for top in ("Art", "Content"):
        for dp, dn, fn in os.walk(os.path.join(ROOT, top)):
            rel_dir = os.path.relpath(dp, ROOT).replace(os.sep, "/")
            if top == "Content" and "/Art" not in "/" + rel_dir + "/":
                continue
            for f in fn:
                if f.startswith(".") or f.lower().endswith(NOT_ART):
                    continue
                out.append(rel_dir + "/" + f)
    return sorted(out)


def discover():
    """{visual: [source, piece or None]} for every shipped visual; piece None = nothing maps it (a FAIL)."""
    rows = {}

    def put(visual, source, piece):
        if visual in rows:
            if source not in rows[visual][0].split("; "):
                rows[visual][0] += "; " + source
        else:
            rows[visual] = [source, piece]

    for visual, rule, piece in STATIC:
        put(visual, "GDD " + rule, piece)
    anim = "Source/UmbrellaElla/Public/Feedback/Anim/"
    for v in enum_values(anim + "EllaAnimPresenterComponent.h", "EEllaVisualState"):
        put("ella-state:" + v, "Source Feedback/Anim EEllaVisualState", ELLA_STATE.get(v))
    for v in enum_values("Source/UmbrellaElla/Public/Flow/FlowRules.h", "EFlowScreen"):
        put("screen:" + v, "Source Flow/FlowRules.h EFlowScreen", SCREEN.get(v))
    for v in enum_values("Source/UmbrellaElla/Public/UI/Menus/FlowMenuWidgets.h", "EFlowBackdrop"):
        put("menu-backdrop:" + v, "Source UI/Menus EFlowBackdrop", FLOW_BACKDROP.get(v))
    et = "Source/UmbrellaElla/Public/Enemy/EnemyTypes.h"
    genders = enum_values(et, "EEnemyGender")
    fams = []
    for t in enum_values(et, "EEnemyType"):
        fams += enum_values(et, "ERoadwardenEquipment") if t == "Roadwarden" else [t]
    for fam in fams:
        for g in genders:
            put("enemy:%s:%s" % (fam, g), "Source Enemy/EnemyTypes.h + GDD ANIM-08", ENEMY_FAMILY.get(fam))
    for m in re.finditer(r'Specs\.Add\(\{\s*TEXT\("(\w+)"\)',
                         rd("Source/UmbrellaElla/Private/Feedback/Background/UmbrellaBackdropSubsystem.cpp")):
        put("bg-layer:" + m.group(1), "Source Feedback/Background LayerSpecs", BACKDROP_LAYER.get(m.group(1)))
    sheets = []
    for m in re.finditer(r'TEXT\("(VFX_\w+)"\)', rd("Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h")):
        if m.group(1) not in sheets:
            sheets.append(m.group(1))
    for s in sheets:
        put("vfx-sheet:" + s, "Source Feedback/Vfx/VfxCatalog.h", VFX_SHEET.get(s))
    for dp, dn, fn in os.walk(os.path.join(ROOT, "Source")):
        for f in fn:
            if not f.endswith(".h") or "Tests" in dp:
                continue
            for m in re.finditer(r"^class\s+(?:\w+_API\s+)?(\w+)(?:\s+final)?\s*:\s*public\s+"
                                 r"(UUserWidget|SCompoundWidget|SLeafWidget|AHUD)\b", rd(os.path.relpath(
                                     os.path.join(dp, f), ROOT)), re.M):
                put("widget:" + m.group(1), "Source " + os.path.relpath(os.path.join(dp, f),
                    os.path.join(ROOT, "Source/UmbrellaElla/Public")).replace(os.sep, "/"), WIDGET.get(m.group(1)))
    for rel in art_files():
        for rx, vis in FILE_RULES:
            m = re.match(rx, rel)
            if m:
                visual = vis.format(*([None] + list(m.groups())))
                if visual.startswith("vfx-material:"):
                    piece = MATERIAL.get(m.group(1))
                    put(visual, rel, piece)
                elif visual.startswith("vfx-sheet:"):
                    put(visual, rel, VFX_SHEET.get(m.group(1)))
                else:
                    put(visual, rel, rows.get(visual, [None, None])[1])
                break
        else:
            put("file:" + rel, rel, None)
    return rows


def load_elements():
    with open(os.path.join(ROOT, "pipeline", "art", "references.json"), encoding="utf-8") as fh:
        refs = json.load(fh)
    els = dict(refs["elements"])
    els.setdefault("scene", {"owner": "artscene"})   # the full-frame piece lives under references.json "scene"
    return els


def manifest_ids():
    try:
        with open(os.path.join(ROOT, "docs", "feature-manifest.json"), encoding="utf-8") as fh:
            return {f["feature_id"] for f in json.load(fh)["features"]}
    except (OSError, ValueError, KeyError):
        return set()


def owner_of(piece, elements):
    el = elements.get(piece) or {}
    return el.get("owner") or OWNERS.get(piece)


def log_files():
    paths = [os.path.join(ROOT, LOG)]
    for p in sorted(glob.glob(os.path.join(ROOT, "..", "*", LOG))):
        if os.path.abspath(p) not in map(os.path.abspath, paths):
            paths.append(p)
    return paths


def passed_pieces(paths=None):
    """Pieces whose newest round in some log passed: verdict ours or same, checks passed, no pair missing."""
    import art_loop
    done = set()
    for path in (paths if paths is not None else log_files()):
        newest = {}
        try:
            with open(path, encoding="utf-8") as fh:
                for ln in fh:
                    try:
                        rec = json.loads(ln)
                    except ValueError:
                        continue
                    if isinstance(rec, dict) and rec.get("piece"):
                        newest[rec["piece"]] = rec
        except OSError:
            continue
        done |= {p for p, r in newest.items() if r.get("verdict") in ("ours", "same") and r.get("checks")
                 and not art_loop.missing_pairs(r)}
    return done


def build(log_paths=None):
    """(rows, problems): rows = [visual, source, piece, owner, passed]; problems = FAIL lines."""
    elements = load_elements()
    ids = manifest_ids()
    done = passed_pieces(log_paths)
    rows, problems = [], []
    for visual, (source, piece) in sorted(discover().items()):
        if not piece:
            problems.append("FAIL art_inventory: %s (%s) has no art-loop piece: add one to pipeline/art/references.json "
                            "and map it in tools/build/art_inventory.py" % (visual, source))
            continue
        if piece not in elements:
            problems.append("FAIL art_inventory: %s (%s) maps to piece %s, which is not an element of "
                            "pipeline/art/references.json" % (visual, source, piece))
            continue
        owner = owner_of(piece, elements)
        if owner not in LANES:
            problems.append("FAIL art_inventory: piece %s (%s) has owner %r, not one of %s"
                            % (piece, visual, owner, "/".join(LANES)))
            continue
        if not visual.startswith("widget:"):   # a widget class must have a piece but is not a row: its screen is
            rows.append([visual, source, piece, owner, "yes" if piece in done else "no"])
    for visual, rule, piece in STATIC:
        for r in rule.split("/"):
            if ids and r not in ids:
                problems.append("FAIL art_inventory: %s cites %s, which is not in docs/feature-manifest.json"
                                % (visual, r))
    return rows, problems


def read_csv():
    try:
        with open(os.path.join(ROOT, CSV), newline="", encoding="utf-8") as fh:
            return list(csv.reader(fh))
    except OSError:
        return []


def write_csv(rows):
    path = os.path.join(ROOT, CSV)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(rows)


def summary(rows):
    per = {l: sum(1 for r in rows if r[3] == l) for l in LANES}
    return "TOTAL=%d PASSED=%d %s" % (len(rows), sum(1 for r in rows if r[4] == "yes"),
                                      " ".join("%s=%d" % (l, n) for l, n in per.items()))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "check"
    rows, problems = build()
    if cmd == "summary":
        print(summary(rows))
        return 1 if problems else 0
    if cmd == "list":
        for r in rows:
            print(",".join(r))
        return 0
    if cmd == "write":
        write_csv(rows)
    else:
        have = read_csv()
        want_keys = [r[:4] for r in rows]
        have_keys = [r[:4] for r in have[1:]]
        if have_keys != want_keys:
            problems.append("FAIL art_inventory: %s is out of date: run python3 tools/build/art_inventory.py write" % CSV)
    for p in problems:
        print(p)
    print("art_inventory: %s (%s)" % ("FAIL" if problems else "PASS", summary(rows)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

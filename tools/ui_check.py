#!/usr/bin/env python3
"""UI, UX and accessibility gates for THE LAST HOUR. Stdlib only; runs locally and in CI.
Rules, owners and done-when for each check: pipeline/ui/accessibility.md. Role: pipeline/roles/ui-ux.md.

Subcommands (exit 0 = pass, 1 = fail, 2 = input missing or bad arguments):
  text-floor --res WxH            smallest allowed text height in px at that resolution (18 at 1080p, scaled by height)
  contrast CAPTURE --boxes F      WCAG contrast of each text/object box against the worst 5% of its background;
                                  the glyph colour is measured from the capture (the declared colour only picks
                                  the side); text under the size floor fails; HUD text needs a backing plate or an
                                  ink outline that rings the glyph edges
  layout CAPTURE --boxes F [--scale S]  text boxes are not cut by the screen edge, do not overlap, glyphs do not
                                  touch their box edge; with --scale, text is at least S x the size floor (text scale 2.0)
  grayscale CAPTURE --swatches F  colour-coded states (umbrella tiers, bolt vs arc) must differ in grayscale L*
  flashes FRAME_DIR --fps N       more than 3 general or 2 red flashes in any 1 s fails; a frame >= 20% saturated red fails
  strings [CSV]                   UI string table: no all-caps over 2 words, sentence-case hints, plain assist labels,
                                  prompts use a {key} placeholder (never a baked key name), plain reading level
  signals [JSON]                  every critical event has a sound AND a visual; every colour-coded state has a second signal;
                                  a sound_id is never blank (unless the sound is "none") and never shared without shared_ok;
                                  a row with "sound_status": "requested" whose id is not in the sound list yet is
                                  PENDING (a note), and fails with --release
  fonts [CSV]                     text styles: every body style uses one font, never a title (blackletter) font
  shake [JSON]                    pipeline/feel/feel.json: an off switch exists and no shake is over 2.5% of screen height
  flow-check LOG --commit SHA     UIFLOW line: title, pause (also during the end event), survived/fail card, restart, quits,
                                  keyboard-only, menu navigation, remap, release-activate, text scale 2.0
  quit                            a player can always quit (no Alt+F4): the string table has Title.Quit and Pause.QuitToTitle,
                                  and game code outside Smoke/ and Tests/ calls QuitGame or RequestExit (the Quit button)
  config [INI]                    DefaultEngine.ini uses the Shortest Side DPI rule
  widgets [SRC]                   no NativeTick in UUserWidget subclasses (HUD updates from events)
  tests [--tier P0,MVP8,P1,P2|all] print the required UI automation test names (for check_automation_report.py --require);
                                  default P0 only (card 0.21). A P1/P2 setting's own card asks for its tier
  screens [--src DIR] [--refs F]  every UI screen is an art-loop piece: each widget class (UUserWidget, Slate S-widget,
                                  AHUD) and each E...Screen value declared under a UI/ or Flow/ folder of the Source tree
                                  is named by a screen element of pipeline/art/references.json (its "ui" block:
                                  "widgets", "screens"), so a new screen cannot skip the visual bar. An element naming
                                  a widget or screen that no longer exists fails too. Tests/ folders are not scanned
  ci [--release]                  signals + strings + fonts + config + widgets + screens + shake + quit; inputs not created
                                  yet are skipped and listed (--release: a skipped input or a PENDING sound fails, for the G-gates)
"""
import argparse
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from png import read_png  # noqa: E402

# ---- thresholds (gate values; never loosen without a measurement, AGENTS.md section 7) ----
TEXT_PX_AT_1080 = 18.0          # smallest text height in physical px at 1920x1080; scales with height
CONTRAST_TEXT = 4.5             # WCAG 1.4.3 normal text
CONTRAST_LARGE = 3.0            # WCAG 1.4.3 large text (>= 24 px, or >= 18.66 px bold)
CONTRAST_OBJECT = 3.0           # WCAG 1.4.11 non-text: projectiles, icons, outlines
WORST_SHARE = 0.05              # contrast is taken at the worst 5% of background pixels in the box
LARGE_PX, LARGE_BOLD_PX = 24.0, 18.66
TEXT_MATCH, BG_MIN_DIST = 40.0, 60.0   # RGB distance: "is the text colour" / "is clearly background"
MIN_TEXT_SHARE, MIN_BG_SHARE = 0.01, 0.05
GLYPH_EXTREME_SHARE = 0.01      # measured glyph colour = median of the darkest (or lightest) 1% of the box
OUTLINE_REACH = 2               # px: an outline pixel must sit this close to a glyph edge pixel
MIN_OUTLINE_RING = 0.80         # share of glyph edge pixels with outline in reach. Calibrated on fixtures:
                                # drawn outline 1.00, no outline on half-dark sky ~0.5, no outline on paper 0.00
EDGE_MARGIN_AT_1080 = 4.0       # px a text box keeps from the screen edge at 1080p (scales with height)
GRAY_MIN_DELTA_L = 20.0         # L* gap between any two states of one colour-coded group
MAX_FLASHES_PER_S = 3           # WCAG 2.3.1
MAX_RED_FLASHES_PER_S = 2       # stricter for red (Xbox XAG 118: red needs a lower change); one under the general limit
FLASH_DELTA = 0.10              # relative-luminance change that counts as a transition
FLASH_DARK_MAX = 0.80           # ... when the darker side is below this
FLASH_AREA = 0.10               # share of the screen that must change for a transition to count
RED_AREA_MAX = 0.20             # no frame may be this much saturated red (desaturate full-screen red)
RED_SHARE = 0.80                # R / (R+G+B) at or above = saturated red
FLASH_MIN_SECONDS = 10.0
FLASH_GRID = 20000              # pixels sampled per frame
MAX_SENTENCE_WORDS = 15         # Hint./Instr./Settings. rows: words per sentence (cheap stand-in for lower-secondary level)
LONG_WORD_SYLLABLES = 3         # a word with more syllables than this is "long"
MAX_LONG_WORD_SHARE = 0.10      # ... and at most 10% of a row's words may be long
LONG_SHARE_MIN_WORDS = 5        # the share rule needs at least this many words (a 2-word label is not a sample)
MAX_SHAKE_AMP_PCT_H = 2.5       # largest allowed shake amplitude, % of screen height (feel.json amp_pct_h)

STRINGS_CSV = "Content/UmbrellaElla/UI/ST_UI.csv"
SIGNALS_JSON = "pipeline/ui/signals.json"
SOUND_LIST = "pipeline/audio/sound-list.csv"
ENGINE_INI = "Config/DefaultEngine.ini"
SOURCE_DIR = "Source"
FEEL_JSON = "pipeline/feel/feel.json"
TEXT_STYLES_CSV = "Content/UmbrellaElla/UI/text-styles.csv"
STYLE_USES = ("title", "body")
TITLE_FACE = re.compile(r"blackletter|fraktur|textura|gothic|old ?english", re.I)
READING_PREFIXES = ("Hint.", "Instr.", "Settings.")

BANNED_LABEL = re.compile(r"\b(easy|baby|cheat|noob|wimp|casual|coward)\b", re.I)
BAKED_KEY = re.compile(r"\b(space(bar)?|esc(ape)?|enter|shift|ctrl|tab|lmb|rmb|w/s|a/d|left mouse|right mouse)\b|\[[A-Z]\]", re.I)
PLACEHOLDER_RE = re.compile(r"\{[A-Za-z_][\w]*\}")
COLOUR_ONLY = {"amber", "red", "gold", "golden", "orange", "yellow", "white", "black", "sepia", "rust", "dark", "light",
               "darker", "lighter", "brighter", "dimmer", "flash", "glow", "tint", "colour", "color", "shade", "hue",
               "and", "a", "the", "of", "more", "less", "with", "in"}
UNSET = {"", "tbd", "todo", "?", "none yet", "n/a"}

# shield-catch, shield-heal, wind-enter: GDD 1.3 DEF-01, SURV-03 (CatchSucceeded, heal) and WIND-01 are APPROVED_P0.
REQUIRED_EVENTS = ["owl-windup", "gust-incoming", "bolt-launch", "arc-launch", "player-hit", "low-health",
                   "shield-catch", "shield-heal", "wind-enter",
                   "umbrella-tear", "umbrella-intact", "umbrella-damaged", "umbrella-critical", "end-trigger", "survived", "failed",
                   "progress-motif", "clock-hit", "wing-hit"]
# GDD section 8: progress is never told by colour or music alone, so this row needs a non-colour second signal
# even when its colour cell is blank.
NEEDS_SECOND = {"progress-motif"}

UIFLOW_FIELDS = ["title-play", "pause", "pause-end-event", "survived-card", "fail-card", "restart",
                 "quit-title", "quit-pause", "keyboard-only", "menu-nav-keyboard", "remap", "release-activate",
                 "text-scale-2", "prompts-consistent", "mouse-menus", "mouse-play", "remap-gamepad", "tutorial-skip"]
# A player can always leave the game (first test build had no Quit: Alt+F4). Keys in the string table, and a quit
# call in game code outside the smoke hook and the tests (the smoke hook's own -SmokeQuitAfter quit does not count).
QUIT_KEYS = ("Title.Quit", "Pause.QuitToTitle")
QUIT_CALL = re.compile(r"\b(?:UKismetSystemLibrary::QuitGame|QuitGame|RequestExit(?:WithStatus)?)\s*\(")
QUIT_SKIP_DIRS = ("Smoke", "Tests")
MAX_PLAY_PRESSES = 1

# (test name, tier). Card 0.21 requires P0. MVP8 = needs the end event (tier label kept; the outcome-trigger card, MVP 6, requires it).
# P1/P2 = that setting is P1/P2 (D-new-assist, D-new-audio-rules); its own card requires it. Remapping (keyboard/mouse
# and controller), the tutorial skip and the tutorial's control glyphs are P0 (team meeting, 11 Nov).
UI_TEST_TIERS = [
    ("UmbrellaElla.UI.World.HoldToggleSetting", "P0"),
    ("UmbrellaElla.UI.World.RemapUpdatesPrompt", "P0"),   # team meeting 11 Nov: remapping is required
    ("UmbrellaElla.UI.World.RemapGamepadUpdatesPrompt", "P0"),
    ("UmbrellaElla.UI.World.TutorialSkipReachesPlay", "P0"),
    ("UmbrellaElla.UI.World.TutorialShowsControlGlyphs", "P0"),
    ("UmbrellaElla.UI.World.VolumeSlidersSetSoundClass", "P1"),
    ("UmbrellaElla.UI.World.GameSpeedScalesTimer", "P1"),
    ("UmbrellaElla.UI.World.AssistSlidersScale", "P2"),
    ("UmbrellaElla.UI.World.SettingsPersist", "P0"),
    ("UmbrellaElla.UI.World.PauseDuringEndEvent", "MVP8"),
    ("UmbrellaElla.UI.World.SurvivedCardWaitsForInput", "P0"),
    ("UmbrellaElla.UI.World.ShakeOffZeroesShake", "P0"),
    ("UmbrellaElla.UI.World.TextSizeSettingScalesUI", "P0"),
    ("UmbrellaElla.UI.World.CursorShownInMenusHiddenInPlay", "P0"),
    ("UmbrellaElla.UI.World.QuitButtonsExit", "P0"),
]
UI_TESTS = [n for n, _ in UI_TEST_TIERS]
UI_TIERS = ("P0", "MVP8", "P1", "P2")


def ui_tests(tiers=("P0",)):
    return [n for n, t in UI_TEST_TIERS if t in tiers]

# ---- screens: every shipped screen is an art-loop piece (Josh, 12 Nov: the flat Defeated screen had no bar check) ----
REFERENCES_JSON = "pipeline/art/references.json"
SCREEN_DIRS = ("UI", "Flow")            # a Source path with one of these folders holds screens
SCREEN_SKIP_DIRS = ("Tests",)
CLASS_DECL = re.compile(r"^[ \t]*class\s+(?:\w+_API\s+)?(\w+)(?:\s+final)?\s*:\s*([^{;]+)\{", re.M)
BASE_NAME = re.compile(r"(?:public|protected|private)?\s*(?:virtual\s+)?(\w+)")
# A widget base: a UMG widget class, a Slate widget (S + capital, the engine's naming rule) or the HUD actor.
WIDGET_BASE_NAME = re.compile(r"^(U\w*Widget|S[A-Z]\w*|AHUD)$")
SCREEN_ENUM = re.compile(r"enum\s+class\s+(E\w*Screen)\b[^{]*\{([^}]*)\}", re.S)

WIDGET_BASES = re.compile(r"class\s+\w+(?:_API)?\s+(U\w+)\s*:\s*public\s+(UUserWidget|UCommonUserWidget|UCommonActivatableWidget)\b")
NATIVE_TICK = re.compile(r"\bNativeTick\s*\(")


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------- colour maths
def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"bad colour {h!r}; use #rrggbb")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(rgb):
    r, g, b = rgb[:3]
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def lstar(rgb):
    y = rel_lum(rgb)
    return 116 * y ** (1 / 3) - 16 if y > 216 / 24389 else y * 24389 / 27


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def text_floor(height):
    return round(TEXT_PX_AT_1080 * height / 1080.0, 2)


def parse_res(res):
    m = re.fullmatch(r"(\d+)x(\d+)", res.strip().lower())
    if not m:
        raise ValueError(f"bad --res {res!r}; use WxH like 1920x1080")
    return int(m.group(1)), int(m.group(2))


def region(rows, b):
    x, y, w, h = int(b["x"]), int(b["y"]), int(b["w"]), int(b["h"])
    H, W = len(rows), len(rows[0]) if rows else 0
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > W or y + h > H:
        raise ValueError(f"box {b.get('name', '?')} ({x},{y},{w},{h}) is outside the {W}x{H} capture")
    return [rows[j][i] for j in range(y, y + h) for i in range(x, x + w)]


def worst(values, share=WORST_SHARE):
    v = sorted(values)
    return v[min(len(v) - 1, int(len(v) * share))]


# ---------------------------------------------------------------- contrast
def contrast_problems(rows, boxes):
    """Each box: name, x, y, w, h, kind text|object, colour (#hex of glyph/object fill), px (text),
    bold, hud (bool), backing plate|outline, outline (#hex when backing=outline)."""
    out, report = [], []
    height = len(rows)
    for b in boxes:
        name = b.get("name", "?")
        kind = b.get("kind", "text")
        try:
            fg = hex_rgb(b["colour"])
            px = region(rows, b)
        except (KeyError, ValueError) as e:
            out.append(f"{name}: {e}")
            continue
        n = len(px)
        fg_l = rel_lum(fg)
        fg_share = sum(1 for p in px if dist(p, fg) <= TEXT_MATCH) / n
        if fg_share < MIN_TEXT_SHARE:
            out.append(f"{name}: colour {b['colour']} covers {fg_share:.1%} of the box (< {MIN_TEXT_SHARE:.0%}); wrong box or wrong colour")
            continue
        need = CONTRAST_OBJECT
        if kind == "text":
            size = b.get("px")
            if not isinstance(size, (int, float)):
                out.append(f"{name}: text box has no numeric px (glyph height in px)")
                continue
            floor = text_floor(height)
            if size < floor:
                out.append(f"{name}: text {size:g} px < floor {floor:g} px at height {height}")
            large = size >= LARGE_PX or (b.get("bold") and size >= LARGE_BOLD_PX)
            need = CONTRAST_LARGE if large else CONTRAST_TEXT
            if b.get("hud") and b.get("backing") not in ("plate", "outline"):
                out.append(f"{name}: HUD text needs backing plate or outline (got {b.get('backing')!r})")
        against, label = None, "background"
        if b.get("backing") == "outline":
            if "outline" not in b:
                out.append(f"{name}: backing=outline but no outline colour")
                continue
            ol = hex_rgb(b["outline"])
            ring = outline_ring(px, int(b["w"]), int(b["h"]), fg, ol)
            if ring is None:
                out.append(f"{name}: glyphs touch the box edge; pad the box by {OUTLINE_REACH + 1} px")
                continue
            if ring < MIN_OUTLINE_RING:
                out.append(f"{name}: outline {b['outline']} rings {ring:.0%} of the glyph edges (< {MIN_OUTLINE_RING:.0%}); not drawn")
                continue
            against, label = [rel_lum(ol)], "outline"
        else:
            bg = [p for p in px if dist(p, fg) >= BG_MIN_DIST]
            if len(bg) / n < MIN_BG_SHARE:
                out.append(f"{name}: background is {len(bg) / n:.1%} of the box; pad the box so it includes background")
                continue
            against = [rel_lum(p) for p in bg]
        # Measure the glyph: the declared colour only says which side (darker or lighter than the background).
        # The ratio uses whichever of declared and measured is closer to the background.
        lums = sorted(rel_lum(p) for p in px)
        k = max(1, int(n * GLYPH_EXTREME_SHARE))
        ref = sorted(against)[len(against) // 2]
        dark = fg_l < ref
        core = lums[:k] if dark else lums[-k:]
        measured = core[len(core) // 2]
        use = max(fg_l, measured) if dark else min(fg_l, measured)
        r = worst([ratio(use, l) for l in against])
        report.append({"name": name, "kind": kind, "ratio": round(r, 2), "need": need, "against": label,
                       "glyph_lum_declared": round(fg_l, 4), "glyph_lum_measured": round(measured, 4)})
        if r < need:
            out.append(f"{name}: contrast {r:.2f}:1 vs worst 5% of {label} < {need:g}:1")
    return out, report


def outline_ring(px, w, h, fg, ol, reach=OUTLINE_REACH):
    """Share of glyph edge pixels (glyph pixels with a non-glyph 4-neighbour) that have an outline-coloured
    pixel within `reach` px. None when glyphs touch the box border or no edge pixel can be judged."""
    glyph = [dist(p, fg) <= TEXT_MATCH for p in px]
    line = [dist(p, ol) <= TEXT_MATCH for p in px]
    rim = [i for i in range(w)] + [(h - 1) * w + i for i in range(w)] + [j * w for j in range(h)] + [j * w + w - 1 for j in range(h)]
    if any(glyph[i] for i in rim):
        return None    # glyphs on the box border: the outline outside the box cannot be judged
    edges = hits = 0
    for y in range(reach, h - reach):
        for x in range(reach, w - reach):
            i = y * w + x
            if not glyph[i] or all(glyph[j] for j in (i - 1, i + 1, i - w, i + w)):
                continue
            edges += 1
            if any(line[yy * w + xx] for yy in range(y - reach, y + reach + 1) for xx in range(x - reach, x + reach + 1)):
                hits += 1
    return hits / edges if edges else None


# ---------------------------------------------------------------- layout (text scale 2.0)
def layout_problems(rows, boxes, scale=None):
    """Text boxes from one screen capture: not cut by the screen edge, no two overlap, glyph pixels never on the
    box border (a clipped label runs into its box edge). With scale, every text px >= scale x floor."""
    out = []
    H, W = len(rows), len(rows[0]) if rows else 0
    margin = EDGE_MARGIN_AT_1080 * H / 1080.0
    texts = [b for b in boxes if b.get("kind", "text") == "text"]
    if not texts:
        return ["no text boxes; a screen capture needs its text boxes"]
    for b in texts:
        name = b.get("name", "?")
        x, y, w, h = int(b["x"]), int(b["y"]), int(b["w"]), int(b["h"])
        if x < margin or y < margin or x + w > W - margin or y + h > H - margin:
            out.append(f"{name}: box ({x},{y},{w},{h}) is within {margin:g} px of the {W}x{H} screen edge; cut off or about to be")
            continue
        try:
            fg = hex_rgb(b["colour"])
        except (KeyError, ValueError) as e:
            out.append(f"{name}: {e}")
            continue
        border = [rows[y][i] for i in range(x, x + w)] + [rows[y + h - 1][i] for i in range(x, x + w)]
        border += [rows[j][x] for j in range(y, y + h)] + [rows[j][x + w - 1] for j in range(y, y + h)]
        if any(dist(p, fg) <= TEXT_MATCH for p in border):
            out.append(f"{name}: glyph pixels touch the box edge; text is clipped (or pad the box)")
        if scale:
            px, need = b.get("px"), scale * text_floor(H)
            if not isinstance(px, (int, float)) or px < need:
                out.append(f"{name}: text {px} px < {need:g} px ({scale:g} x floor); is the capture at text scale {scale:g}?")
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, c = texts[i], texts[j]
            if (int(a["x"]) < int(c["x"]) + int(c["w"]) and int(c["x"]) < int(a["x"]) + int(a["w"]) and
                    int(a["y"]) < int(c["y"]) + int(c["h"]) and int(c["y"]) < int(a["y"]) + int(a["h"])):
                out.append(f"{a.get('name', '?')} overlaps {c.get('name', '?')}")
    return out


# ---------------------------------------------------------------- grayscale
def grayscale_problems(rows, groups, min_delta=GRAY_MIN_DELTA_L):
    out, report = [], []
    for g in groups:
        means = []
        for s in g.get("swatches", []):
            try:
                px = region(rows, s)
            except ValueError as e:
                out.append(f"{g.get('group', '?')}: {e}")
                continue
            means.append((s.get("name", "?"), sum(lstar(p) for p in px) / len(px)))
        if len(means) < 2:
            out.append(f"{g.get('group', '?')}: needs at least 2 swatches")
            continue
        for i in range(len(means)):
            for j in range(i + 1, len(means)):
                d = abs(means[i][1] - means[j][1])
                report.append({"group": g.get("group"), "pair": [means[i][0], means[j][0]], "delta_l": round(d, 1)})
                if d < min_delta:
                    out.append(f"{g.get('group')}: {means[i][0]} vs {means[j][0]} differ by L* {d:.1f} in grayscale (< {min_delta:g})")
    return out, report


# ---------------------------------------------------------------- flashes
def _sample(rows, limit=FLASH_GRID):
    H, W = len(rows), len(rows[0])
    step = max(1, int((W * H / limit) ** 0.5))
    return [rows[y][x] for y in range(0, H, step) for x in range(0, W, step)]


def _is_red(p):
    s = p[0] + p[1] + p[2]
    return s > 0 and p[0] / s >= RED_SHARE


def _count_window(signs, fps):
    """Collapse runs of the same direction into one transition, then the worst flash count in any 1 s window."""
    trans, last = [], 0
    for i, s in enumerate(signs):
        if s and s != last:
            trans.append(i)
            last = s
    best = 0
    for k, start in enumerate(trans):
        n = sum(1 for t in trans[k:] if t < start + fps)
        best = max(best, n // 2)
    return best


def flash_problems(frames, fps):
    """frames: list of sampled pixel lists (same length). Returns problems and numbers."""
    out = []
    secs = len(frames) / float(fps)
    if secs < FLASH_MIN_SECONDS:
        out.append(f"capture is {secs:.1f} s; need >= {FLASH_MIN_SECONDS:g} s of the busiest moment")
    lums = [[rel_lum(p) for p in f] for f in frames]
    reds = [[_is_red(p) for p in f] for f in frames]
    gen, red = [0], [0]
    worst_red = max((sum(r) / len(r) for r in reds), default=0)
    for i in range(1, len(frames)):
        a, b = lums[i - 1], lums[i]
        n = len(a)
        up = sum(1 for x, y in zip(a, b) if y - x >= FLASH_DELTA and min(x, y) < FLASH_DARK_MAX) / n
        dn = sum(1 for x, y in zip(a, b) if x - y >= FLASH_DELTA and min(x, y) < FLASH_DARK_MAX) / n
        gen.append(1 if up >= FLASH_AREA and up >= dn else -1 if dn >= FLASH_AREA else 0)
        ra, rb = reds[i - 1], reds[i]
        into = sum(1 for x, y in zip(ra, rb) if y and not x) / n
        outof = sum(1 for x, y in zip(ra, rb) if x and not y) / n
        red.append(1 if into >= FLASH_AREA and into >= outof else -1 if outof >= FLASH_AREA else 0)
    g, r = _count_window(gen, fps), _count_window(red, fps)
    if g > MAX_FLASHES_PER_S:
        out.append(f"{g} general flashes in one second (max {MAX_FLASHES_PER_S})")
    if r > MAX_RED_FLASHES_PER_S:
        out.append(f"{r} red flashes in one second (max {MAX_RED_FLASHES_PER_S})")
    if worst_red >= RED_AREA_MAX:
        out.append(f"a frame is {worst_red:.0%} saturated red (max {RED_AREA_MAX:.0%}); desaturate full-screen red")
    return out, {"seconds": round(secs, 2), "flashes_per_s": g, "red_flashes_per_s": r, "max_red_share": round(worst_red, 3)}


def load_frames(path):
    files = sorted(glob.glob(os.path.join(path, "*.png"))) if os.path.isdir(path) else [path]
    frames, size = [], None
    for f in files:
        w, h, rows = read_png(f)
        if size and (w, h) != size:
            raise ValueError(f"{f}: {w}x{h}, other frames are {size[0]}x{size[1]}")
        size = (w, h)
        frames.append(_sample(rows))
    return frames


# ---------------------------------------------------------------- strings
def syllables(word):
    """Rough English syllable count: vowel groups, minus a silent final e. Good enough to flag jargon."""
    w = word.lower().strip("'")
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    consonant_le = re.search(r"[^aeiouy]le$", w)   # "table" keeps its e syllable; "projectile" does not
    if n > 1 and w.endswith("e") and not consonant_le and not w.endswith(("ee", "ye")):
        n -= 1
    return max(1, n)


def reading_problems(text):
    out = []
    for sentence in [s for s in re.split(r"[.!?]+", text) if s.strip()]:
        n = len(re.findall(r"[A-Za-z][A-Za-z']*", sentence))
        if n > MAX_SENTENCE_WORDS:
            out.append(f"sentence has {n} words (max {MAX_SENTENCE_WORDS}); split it")
    words = re.findall(r"[A-Za-z][A-Za-z']*", text)
    if len(words) >= LONG_SHARE_MIN_WORDS:
        long_words = [w for w in words if syllables(w) > LONG_WORD_SYLLABLES]
        if len(long_words) / len(words) > MAX_LONG_WORD_SHARE:
            out.append(f"{len(long_words)} of {len(words)} words have more than {LONG_WORD_SYLLABLES} syllables "
                       f"({', '.join(long_words)}; max {MAX_LONG_WORD_SHARE:.0%}); use plainer words")
    return out


def string_problems(rows):
    """rows: list of (key, text) from a UE string table CSV (Key,SourceString)."""
    out, seen = [], set()
    for key, text in rows:
        where = f"{key}"
        if key in seen:
            out.append(f"{where}: duplicate key")
        seen.add(key)
        if not text.strip():
            out.append(f"{where}: empty text")
            continue
        plain = PLACEHOLDER_RE.sub("", text)
        words = re.findall(r"[A-Za-z][A-Za-z']*", plain)
        if len(words) > 2 and all(w.isupper() for w in words if len(w) > 1) and any(len(w) > 1 for w in words):
            out.append(f"{where}: all caps over 2 words; use sentence case")
        if key.startswith(("Hint.", "Instr.", "Prompt.", "Settings.")):
            later = [w for w in words[1:] if len(w) > 3]
            caps = [w for w in later if w[0].isupper()]
            if len(caps) >= 2 and len(caps) * 2 > len(later):
                out.append(f"{where}: Title Case; instructions and labels use sentence case")
        if key.startswith(("Settings.", "Assist.")) and BANNED_LABEL.search(plain):
            out.append(f"{where}: label judges the player ({BANNED_LABEL.search(plain).group(0)!r}); name what it changes")
        if key.startswith(READING_PREFIXES):
            out += [f"{where}: reading level: {p}" for p in reading_problems(plain)]
        if key.startswith("Prompt."):
            if not PLACEHOLDER_RE.search(text):
                out.append(f"{where}: prompt has no {{key}} placeholder; draw the key from the current binding")
            if BAKED_KEY.search(plain):
                out.append(f"{where}: prompt names a key ({BAKED_KEY.search(plain).group(0)!r}); use the binding placeholder")
    return out


def read_strings(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rdr = csv.reader(fh)
        header = next(rdr, None)
        if not header or [h.strip() for h in header[:2]] != ["Key", "SourceString"]:
            raise ValueError(f"{path}: first row must be Key,SourceString (Unreal string table CSV)")
        return [(r[0].strip(), r[1]) for r in rdr if r and r[0].strip()]


# ---------------------------------------------------------------- signals
def signal_problems(data, required=REQUIRED_EVENTS, sound_ids=None):
    """sound_ids: ids from pipeline/audio/sound-list.csv, or None to skip that cross-check."""
    out = []
    events = data.get("events", []) if isinstance(data, dict) else []
    names = [e.get("event", "") for e in events]
    for r in required:
        if r not in names:
            out.append(f"{r}: missing (every critical event needs a row)")
    for e in events:
        n = e.get("event", "?")
        for f in ("sound", "visual", "owner"):
            if str(e.get(f, "")).strip().lower() in UNSET:
                out.append(f"{n}: {f} is blank or TBD")
        sid = str(e.get("sound_id", "")).strip()
        silent = str(e.get("sound", "")).strip().lower().startswith("none")
        if not sid and not silent:
            out.append(f"{n}: sound_id is blank but the sound is {e.get('sound')!r}; name a row in {SOUND_LIST}")
        if sound_ids is not None and sid and sid not in sound_ids and not _requested(e):
            out.append(f"{n}: sound_id {sid} is not in {SOUND_LIST}")
        colour = str(e.get("colour", "")).strip().lower()
        if colour in UNSET and n in NEEDS_SECOND:
            colour = "progress"
        if colour and colour not in UNSET:
            second = str(e.get("second_signal", "")).strip().lower()
            if second in UNSET:
                out.append(f"{n}: {colour} state with no second signal (shape, icon, label or motion)")
            elif not [w for w in re.findall(r"[a-z]+", second) if w not in COLOUR_ONLY]:
                out.append(f"{n}: second signal {second!r} is still only a colour")
    first = {}
    for e in events:
        sid, n = str(e.get("sound_id", "")).strip(), e.get("event", "?")
        if not sid:
            continue
        if sid not in first:
            first[sid] = n
        elif str(e.get("shared_ok", "")).strip().lower() in UNSET:
            out.append(f"{n}: sound_id {sid} is already used by {first[sid]}; key events need distinct sounds "
                       f"(give it its own id, or a shared_ok reason)")
    return out


def _requested(e):
    return str(e.get("sound_status", "")).strip().lower() == "requested"


def pending_sounds(data, sound_ids):
    """Rows whose sound_id is requested from the audio lane and not in the sound list yet.
    None for sound_ids (no sound list) means every requested row is pending."""
    events = data.get("events", []) if isinstance(data, dict) else []
    return [f"{e.get('event', '?')}: sound_id {e.get('sound_id')} requested, not yet in {SOUND_LIST}"
            for e in events if _requested(e) and (sound_ids is None or str(e.get("sound_id", "")).strip() not in sound_ids)]


def read_sound_ids(root):
    path = os.path.join(root, SOUND_LIST)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r.get("id", "").strip() for r in csv.DictReader(fh)}


# ---------------------------------------------------------------- fonts
def font_problems(rows):
    """rows: dicts with Style, Font, Use (title|body) from the text style list. Body text uses exactly one font,
    which is never a title font and never a blackletter face (titles and the logo only)."""
    out, body, title = [], set(), set()
    if not rows:
        return ["no text styles listed"]
    for r in rows:
        style, font, use = (str(r.get(k, "") or "").strip() for k in ("Style", "Font", "Use"))
        use = use.lower()
        if not style or not font:
            out.append(f"{style or '?'}: Style and Font must be filled")
            continue
        if use not in STYLE_USES:
            out.append(f"{style}: Use is {use!r}; must be title or body")
            continue
        (title if use == "title" else body).add(font)
        if use == "body" and TITLE_FACE.search(font):
            out.append(f"{style}: body text in {font}; blackletter is for titles and the logo only")
    if len(body) > 1:
        out.append(f"body styles use {len(body)} fonts ({', '.join(sorted(body))}); use one plain sans-serif")
    for f in sorted(body & title):
        out.append(f"{f} is used for both title and body; body needs the plain sans-serif")
    if not body:
        out.append("no body style; hints, settings and HUD need a body style")
    return out


def read_styles(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rdr = csv.DictReader(fh)
        if not rdr.fieldnames or [h.strip() for h in rdr.fieldnames[:3]] != ["Style", "Font", "Use"]:
            raise ValueError(f"{path}: first row must be Style,Font,Use")
        return [r for r in rdr if any((v or "").strip() for v in r.values())]


# ---------------------------------------------------------------- flow
def _fields(line):
    got = {}
    for p in [p.strip() for p in line.split("|")][1:]:
        name, _, value = p.partition(" ")
        if "=" in name and not value:
            name, _, value = name.partition("=")
        got[name] = value.strip().lower()
    return got


def flow_problems(text, commit):
    lines = [l for l in text.splitlines() if l.strip().startswith("UIFLOW")]
    if not lines:
        return ["no UIFLOW line"]
    got = _fields(lines[-1])
    out = []
    c = got.get("commit", "")
    if not c or not (commit.lower().startswith(c) or c.startswith(commit.lower())):
        out.append(f"UIFLOW commit={c or '<none>'}, expected {commit}")
    for f in UIFLOW_FIELDS:
        v = got.get(f, "")
        if not v:
            out.append(f"{f}: blank (a blank field is not a pass)")
        elif not v.startswith("pass"):
            out.append(f"{f}: {v}")
    presses = got.get("play-presses", "")
    if not re.fullmatch(r"\d+", presses):
        out.append("play-presses: missing (key presses from title to control)")
    elif int(presses) > MAX_PLAY_PRESSES:
        out.append(f"play-presses: {presses} (max {MAX_PLAY_PRESSES})")
    return out


# ---------------------------------------------------------------- shake (reads the feel lane's file)
def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def shake_problems(data):
    out = []
    if not any(d.get("shake_off_option") is True for d in _walk(data)):
        out.append("shake_off_option is not true; the Screen shake On / Off setting is required (E8)")
    for d in _walk(data):
        if d.get("kind") != "shake":
            continue
        name = d.get("flag", "?")
        amp = d.get("amp_pct_h")
        if not isinstance(amp, (int, float)):
            out.append(f"{name}: shake has no numeric amp_pct_h")
        elif amp > MAX_SHAKE_AMP_PCT_H:
            out.append(f"{name}: shake amp {amp:g}% of height > {MAX_SHAKE_AMP_PCT_H:g}%")
    return out


# ---------------------------------------------------------------- config + widgets
def config_problems(text):
    section, rule = None, None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("["):
            section = line
        elif section == "[/Script/Engine.UserInterfaceSettings]" and line.split("=", 1)[0].strip() == "UIScaleRule":
            rule = line.split("=", 1)[1].strip()
    if rule is None:
        return ["[/Script/Engine.UserInterfaceSettings] has no UIScaleRule; set UIScaleRule=ShortestSide"]
    if rule != "ShortestSide":
        return [f"UIScaleRule={rule}; must be ShortestSide"]
    return []


def widget_problems(src):
    out = []
    for h in glob.glob(os.path.join(src, "**", "*.h"), recursive=True):
        text = _read(h)
        if not WIDGET_BASES.search(text):
            continue
        cpp = os.path.splitext(h)[0] + ".cpp"
        for f in [h] + glob.glob(os.path.join(src, "**", os.path.basename(cpp)), recursive=True):
            body = _read(f)
            for n, line in enumerate(body.splitlines(), 1):
                if NATIVE_TICK.search(line) and not line.strip().startswith("//"):
                    out.append(f"{os.path.relpath(f, src)}:{n}: NativeTick in a widget; update the HUD from events")
    return out


def _strip_comments(text):
    return re.sub(r"//[^\n]*", "", re.sub(r"/\*.*?\*/", "", text, flags=re.S))


def find_screens(src):
    """(widgets, screens) declared under a UI/ or Flow/ folder of src: {class name: file}, {"EEnum::Value": file}.
    A class counts when a base is a widget base, or a class found the same way (so a subclass of our own widget counts)."""
    decls, screens = [], {}
    for d, dirs, fs in os.walk(src):
        dirs[:] = sorted(x for x in dirs if x not in SCREEN_SKIP_DIRS)
        parts = os.path.relpath(d, src).split(os.sep)
        if not any(p in SCREEN_DIRS for p in parts):
            continue
        for f in sorted(fs):
            if not f.endswith((".h", ".cpp")):
                continue
            path = os.path.join(d, f)
            rel = os.path.relpath(path, src).replace(os.sep, "/")
            text = _strip_comments(_read(path))
            for m in CLASS_DECL.finditer(text):
                bases = [b.group(1) for b in (BASE_NAME.match(x.strip()) for x in m.group(2).split(",")) if b]
                decls.append((m.group(1), bases, rel))
            for m in SCREEN_ENUM.finditer(text):
                for v in m.group(2).split(","):
                    name = v.split("=")[0].strip()
                    if re.fullmatch(r"\w+", name or ""):
                        screens[f"{m.group(1)}::{name}"] = rel
    widgets, grew = {}, True
    while grew:
        grew = False
        for name, bases, rel in decls:
            if name not in widgets and any(WIDGET_BASE_NAME.match(b) or b in widgets for b in bases):
                widgets[name] = rel
                grew = True
    return widgets, screens


def screen_elements(refs):
    """{element id: its "ui" block} for the screen elements of references.json."""
    return {eid: el["ui"] for eid, el in (refs.get("elements") or {}).items() if isinstance(el.get("ui"), dict)}


def screen_problems(src, refs):
    out = []
    widgets, screens = find_screens(src)
    els = screen_elements(refs)
    ref_ids = {r.get("id") for r in refs.get("references") or []}
    qb = refs.get("quality_bar") or {}
    named_w, named_s = {}, {}
    for eid, ui in sorted(els.items()):
        el = refs["elements"][eid]
        if not (ui.get("widgets") or ui.get("screens")):
            out.append(f"screen element {eid} names no widget and no screen")
        for w in ui.get("widgets") or []:
            named_w.setdefault(w, eid)
        for sc in ui.get("screens") or []:
            if sc in named_s:
                out.append(f"screen {sc} is named by two elements ({named_s[sc]}, {eid}); one screen is one piece")
            named_s.setdefault(sc, eid)
        if not [r for r in el.get("refs") or [] if r in ref_ids]:
            out.append(f"screen element {eid} has no reference to be judged against")
        if (qb.get("by_piece") or {}).get(eid, qb.get("default")) not in set(qb.get("refs") or []):
            out.append(f"screen element {eid} has no quality-bar image")
    fix = f"add it to a screen element's \"ui\" block in {REFERENCES_JSON} (the screen is then judged by the art loop)"
    for w, rel in sorted(widgets.items()):
        if w not in named_w:
            out.append(f"{rel}: widget class {w} is no art-loop piece; {fix}")
    for sc, rel in sorted(screens.items()):
        if sc not in named_s:
            out.append(f"{rel}: screen {sc} is no art-loop piece; {fix}")
    for w, eid in sorted(named_w.items()):
        if w not in widgets:
            out.append(f"screen element {eid} names widget class {w}, which is not declared under a UI/ or Flow/ folder")
    for sc, eid in sorted(named_s.items()):
        if sc not in screens:
            out.append(f"screen element {eid} names screen {sc}, which is not declared under a UI/ or Flow/ folder")
    return out


# ---------------------------------------------------------------- cli
def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _finish(problems, report=None, as_json=False, name="ui_check"):
    if as_json:
        print(json.dumps({"check": name, "pass": not problems, "problems": problems, "numbers": report}, indent=1))
    else:
        for r in report or []:
            print(r if isinstance(r, str) else json.dumps(r))
        for p in problems:
            print(f"FAIL {p}")
        print(f"{name}: {'PASS' if not problems else 'FAIL'} ({len(problems)} problem(s))")
    return 1 if problems else 0


def quit_problems(strings=None, src=None):
    """strings: (key, text) rows or None (no table yet); src: the Source folder or None."""
    out = []
    if strings is not None:
        have = {k for k, v in strings if v.strip()}
        for k in QUIT_KEYS:
            if k not in have:
                out.append(f"string table has no {k} row: the title needs Quit and pause needs Quit to title "
                           "(docs/game-spec.md, pipeline/ui/menus.md)")
    if src is not None:
        found = False
        for d, dirs, fs in os.walk(src):
            dirs[:] = [x for x in dirs if x not in QUIT_SKIP_DIRS]
            for f in fs:
                if f.endswith((".cpp", ".h")) and QUIT_CALL.search(_read(os.path.join(d, f))):
                    found = True
        if not found:
            out.append("no Quit in game code: nothing outside Smoke/ and Tests/ calls QuitGame or RequestExit, so a "
                       "player can only leave with Alt+F4. Wire the title Quit button (pipeline/ui/menus.md)")
    return out


def run_ci(root, release=False):
    problems, skipped = [], []
    sig = os.path.join(root, SIGNALS_JSON)
    sound_ids = read_sound_ids(root)
    if sound_ids is None:
        skipped.append(SOUND_LIST)
    if os.path.exists(sig):
        data = _load_json(sig)
        problems += [f"signals: {p}" for p in signal_problems(data, sound_ids=sound_ids)]
        for p in pending_sounds(data, sound_ids):
            print(f"PENDING {p}")
            if release:
                problems.append(f"release: {p}")
    else:
        skipped.append(SIGNALS_JSON)
    sty = os.path.join(root, TEXT_STYLES_CSV)
    if os.path.exists(sty):
        try:
            problems += [f"fonts: {p}" for p in font_problems(read_styles(sty))]
        except ValueError as e:
            problems.append(f"fonts: {e}")
    else:
        skipped.append(TEXT_STYLES_CSV)
    st = os.path.join(root, STRINGS_CSV)
    if os.path.exists(st):
        try:
            problems += [f"strings: {p}" for p in string_problems(read_strings(st))]
        except ValueError as e:
            problems.append(f"strings: {e}")
    else:
        skipped.append(STRINGS_CSV)
    ini = os.path.join(root, ENGINE_INI)
    if os.path.exists(ini):
        problems += [f"config: {p}" for p in config_problems(_read(ini))]
    else:
        skipped.append(ENGINE_INI)
    src = os.path.join(root, SOURCE_DIR)
    if os.path.isdir(src):
        problems += [f"widgets: {p}" for p in widget_problems(src)]
        refs = os.path.join(root, REFERENCES_JSON)
        if os.path.exists(refs):
            problems += [f"screens: {p}" for p in screen_problems(src, _load_json(refs))]
        else:
            skipped.append(REFERENCES_JSON)
    else:
        skipped.append(SOURCE_DIR + "/")
    try:
        quit_strings = read_strings(st) if os.path.exists(st) else None
    except ValueError:
        quit_strings = None   # the strings check above already reported it
    problems += [f"quit: {p}" for p in quit_problems(quit_strings, src if os.path.isdir(src) else None)]
    feel = os.path.join(root, FEEL_JSON)
    if os.path.exists(feel):
        problems += [f"shake: {p}" for p in shake_problems(_load_json(feel))]
    else:
        skipped.append(FEEL_JSON)
    for s in skipped:
        print(f"skipped (not created yet): {s}")
        if release:
            problems.append(f"release: {s} does not exist; every UI input must exist for a G-gate")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("text-floor")
    t.add_argument("--res", required=True)
    lo = sub.add_parser("layout")
    lo.add_argument("capture")
    lo.add_argument("--boxes", required=True)
    lo.add_argument("--scale", type=float)
    c = sub.add_parser("contrast")
    c.add_argument("capture")
    c.add_argument("--boxes", required=True)
    g = sub.add_parser("grayscale")
    g.add_argument("capture")
    g.add_argument("--swatches", required=True)
    f = sub.add_parser("flashes")
    f.add_argument("frames", help="folder of PNG frames (or one PNG), e.g. ffmpeg -vf fps=30,scale=480:270")
    f.add_argument("--fps", type=float, required=True)
    s = sub.add_parser("strings")
    s.add_argument("csv", nargs="?")
    sg = sub.add_parser("signals")
    sg.add_argument("file", nargs="?")
    sg.add_argument("--release", action="store_true", help="a PENDING requested sound fails")
    fo = sub.add_parser("fonts")
    fo.add_argument("csv", nargs="?")
    fl = sub.add_parser("flow-check")
    fl.add_argument("log")
    fl.add_argument("--commit", required=True)
    cf = sub.add_parser("config")
    cf.add_argument("ini", nargs="?")
    w = sub.add_parser("widgets")
    w.add_argument("src", nargs="?")
    sk = sub.add_parser("shake")
    sk.add_argument("file", nargs="?")
    ts = sub.add_parser("tests")
    ts.add_argument("--tier", default="P0", help="comma list of P0, MVP8, P1, P2, or all (default P0)")
    sub.add_parser("quit")
    scr = sub.add_parser("screens")
    scr.add_argument("--src")
    scr.add_argument("--refs")
    ci = sub.add_parser("ci")
    ci.add_argument("--release", action="store_true", help="a skipped input fails (G-gates)")
    a = ap.parse_args(argv)
    root = a.root

    def need(path):
        if not os.path.exists(path):
            print(f"ui_check: {path} not found", file=sys.stderr)
            return False
        return True

    try:
        if a.cmd == "text-floor":
            _, h = parse_res(a.res)
            print(f"{text_floor(h):g}")
            return 0
        if a.cmd == "tests":
            tiers = UI_TIERS if a.tier == "all" else tuple(t.strip() for t in a.tier.split(","))
            bad = [t for t in tiers if t not in UI_TIERS]
            if bad:
                print(f"ui_check: unknown tier {', '.join(bad)} (use {', '.join(UI_TIERS)} or all)", file=sys.stderr)
                return 2
            print("\n".join(ui_tests(tiers)))
            return 0
        if a.cmd == "contrast":
            if not (need(a.capture) and need(a.boxes)):
                return 2
            _, _, rows = read_png(a.capture)
            p, r = contrast_problems(rows, _load_json(a.boxes))
            return _finish(p, r, a.json, "contrast")
        if a.cmd == "layout":
            if not (need(a.capture) and need(a.boxes)):
                return 2
            _, _, rows = read_png(a.capture)
            return _finish(layout_problems(rows, _load_json(a.boxes), a.scale), None, a.json, "layout")
        if a.cmd == "grayscale":
            if not (need(a.capture) and need(a.swatches)):
                return 2
            _, _, rows = read_png(a.capture)
            p, r = grayscale_problems(rows, _load_json(a.swatches))
            return _finish(p, r, a.json, "grayscale")
        if a.cmd == "flashes":
            if not need(a.frames):
                return 2
            frames = load_frames(a.frames)
            if len(frames) < 2:
                print("ui_check: need at least 2 frames", file=sys.stderr)
                return 2
            p, r = flash_problems(frames, a.fps)
            return _finish(p, [r], a.json, "flashes")
        if a.cmd == "strings":
            path = a.csv or os.path.join(root, STRINGS_CSV)
            if not need(path):
                return 2
            return _finish(string_problems(read_strings(path)), None, a.json, "strings")
        if a.cmd == "signals":
            path = a.file or os.path.join(root, SIGNALS_JSON)
            if not need(path):
                return 2
            data, ids = _load_json(path), read_sound_ids(root)
            pend = pending_sounds(data, ids)
            for p in pend:
                print(f"PENDING {p}")
            p = signal_problems(data, sound_ids=ids) + ([f"release: {x}" for x in pend] if a.release else [])
            return _finish(p, None, a.json, "signals")
        if a.cmd == "fonts":
            path = a.csv or os.path.join(root, TEXT_STYLES_CSV)
            if not need(path):
                return 2
            return _finish(font_problems(read_styles(path)), None, a.json, "fonts")
        if a.cmd == "flow-check":
            if not need(a.log):
                return 2
            text = _read(a.log)
            return _finish(flow_problems(text, a.commit), None, a.json, "flow-check")
        if a.cmd == "config":
            path = a.ini or os.path.join(root, ENGINE_INI)
            if not need(path):
                return 2
            return _finish(config_problems(_read(path)), None, a.json, "config")
        if a.cmd == "widgets":
            path = a.src or os.path.join(root, SOURCE_DIR)
            if not need(path):
                return 2
            return _finish(widget_problems(path), None, a.json, "widgets")
        if a.cmd == "shake":
            path = a.file or os.path.join(root, FEEL_JSON)
            if not need(path):
                return 2
            return _finish(shake_problems(_load_json(path)), None, a.json, "shake")
        if a.cmd == "quit":
            st, src = os.path.join(root, STRINGS_CSV), os.path.join(root, SOURCE_DIR)
            if not os.path.exists(st) and not os.path.isdir(src):
                print(f"ui_check: neither {STRINGS_CSV} nor {SOURCE_DIR}/ exists yet", file=sys.stderr)
                return 2
            return _finish(quit_problems(read_strings(st) if os.path.exists(st) else None,
                                         src if os.path.isdir(src) else None), None, a.json, "quit")
        if a.cmd == "screens":
            src, refs = a.src or os.path.join(root, SOURCE_DIR), a.refs or os.path.join(root, REFERENCES_JSON)
            if not (need(src) and need(refs)):
                return 2
            return _finish(screen_problems(src, _load_json(refs)), None, a.json, "screens")
        if a.cmd == "ci":
            # The two modes print different names, so a gate record cannot pass the plain run off as --release
            # (final-7 dry run B H6): `ui_check ci --release: PASS (0 problem(s))` vs `ui_check ci: PASS ...`
            return _finish(run_ci(root, a.release), None, a.json, "ui_check ci --release" if a.release else "ui_check ci")
    except (ValueError, json.JSONDecodeError) as e:
        print(f"ui_check: {e}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())

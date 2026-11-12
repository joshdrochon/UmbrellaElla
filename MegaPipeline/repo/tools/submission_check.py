#!/usr/bin/env python3
"""Submission gate (G4). Stdlib only, plus ffprobe/ffmpeg for the video and loudness checks.
Rules and their sources: docs/jam-rules.md. Checklist: pipeline/checklists/submission.md.

  zip PATH [--team T --game G] [--commit SHA] [--gate G<n>]
        The jam zip, and every gate zip (the fallback). Fails when: the name is not TeamName_GameName.zip (letters and digits only);
        it is over 1,000,000,000 bytes; it holds a .uproject, C++ source, a Saved/ folder, or a
        .uasset/.umap outside a Paks folder (not a cooked package); there is not exactly one game exe
        outside Engine/ and Binaries/; README.txt, LICENSE.txt or BUILD_INFO.txt is missing next to
        that exe; BUILD_INFO.txt says config is not Development, workbench is not 0 (D-new-workbench-debug)
        or dirty=yes, or its platform (if
        written) is not Win64; no <Project>/Binaries/Win64/*.exe; the commit differs from --commit.
        --gate G<n>: the zip sits in a folder named G<n>-<sha>, and BUILD_INFO commit starts with that sha.
        Prints the zip's SHA256 for the submission record.
  video PATH        30-60 s, a video stream at least 1920x1080, an audio stream (ffprobe).
  loudness PATH     integrated loudness within LUFS_TARGET +- LUFS_TOL (ffmpeg ebur128).
  page [DIR]        pipeline/submission/page/: cover.png at least 630x500 and 315:250; 3-5
                    shot-<beat>.png, each a known beat, at least 1920x1080, no two the same file;
                    no TBD left in the Page fields table of pipeline/submission/itch-page.md;
                    the Team table has a row per member, no TBD, Epic email collected = y;
                    Credits by role has a `- <role>: <names>` line for each CREDIT_ROLES role and
                    names every Team member; the controls rows (CONTROLS_ROW DEC-02 firing, KEYS_ROW DEC-01
                    keys) in docs/decisions.md are DECIDED or say "default accepted" with a link.
  credits           every provenance row that needs credit (CC-BY, OFL, Fab, third-party) is named
                    in pipeline/submission/credits.md; every font file in the repo, and every
                    .uasset under a Content/**/Fonts/ folder, has a provenance row.
  devlog --day N [--published]
                    pipeline/submission/devlog.md has the three Glass Box headings and, for days
                    1..N, at least 3 obstacle lines each with a link; --published also needs the
                    `Published:` line to hold an https link.
  prejam [--log-file F]
                    every commit that touched Source/, Content/, Config/ or a .uproject before the
                    jam start (JAM_START) is listed by short SHA in docs/pre-jam-declaration.md.
  declaration [--ref REF]
                    every file tracked at REF (default HEAD) matches a pattern in the declaration's
                    tables. Run it with --ref jam-start at G4.

In-jam inputs (G4 depends on them; run during the jam, not at G4):
  theme [--now ISO] [--brief F]
                    from THEME_DUE on, docs/jam-brief.md has `Theme: "<kickoff quote>"` and
                    `Theme in game: <one line>`, neither empty nor TBD. Before THEME_DUE: pass.
  capture LOG       a game log from a -CaptureMode run holds `CAPTURE_MODE hud=off debug=off cursor=off`.
  footage --day N [--final]   (--final alone: --day 4)
                    pipeline/submission/footage.md: from FOOTAGE_FROM_DAY to N, at least
                    FOOTAGE_MIN_PER_DAY clips per day named <day>-<beat>-<sha>.mp4 under that day;
                    --final also needs every beat in BEATS at least once; the P1 beats (gust, torn)
                    only once their Gust / Wear row in pipeline/qa/test-map.md is merged.
  daily --day N [--now ISO]
                    devlog --day N + footage --day N + theme. check_card.py --status runs it for
                    day just ended. The import for check_card.py is status_hook(brief_text, now):
                    it reads the gate times in the jam-brief Clock (Day N ends at G<N>).
  wiring            the submission duties are wired into the files that agents load: the cards,
                    role cards and check_card.py lines in WIRING are there. Fails until they are.
  (practice repo, tools/practice.py: zip without --gate G1-G3, page, signoff, files --final, devlog --published,
   footage --final, prejam and declaration exit 1; assets skips the date rule. video and loudness still measure)
  assets            Official Rules 7(h): a provenance row under Content/, Art/ or Audio/ dated before JAM_START
                    fails unless its path is in credits.md '## Sourced assets'; a file there that is a byte copy of
                    a pipeline/art/reference/ file (pre-jam key art) fails. LFS pointers compare by oid.
                    It also runs `art`.
  art               every shipped image (under Art/ outside Art/Source/) has its passing art-loop record for its exact
                    bytes (<stem>.artloop.json, tools/art_loop.py): a panel of 3 calibrated blind critics, unanimous
                    ours or SAME against every reference, the quality bar, the motion pair (a sheet) and the in-engine
                    context; art_check/screen_check/art_ref_check PASS; current references.json. A labelled
                    placeholder or stand-in fails; nothing waives it.
  english          Official Rules 7(i): README.txt, LICENSE.txt, itch-page.md, credits.md, devlog.md and string
                    tables (*.csv, *.json under Content/ and pipeline/ui/) hold no letters from a non-Latin script.
  butler LINE       the G1 gate-record line: BUTLER version=<v> login=ok user=<itch-user> by=<name>.
  rules             docs/jam-rules.md has no [VERIFY] left and each quoted row cites an Official Rules section;
                    docs/rules/official-rules.md still holds every RULES_FACTS phrase; the Clock deadline is §4's end.
  files [--final]   pipeline/submission/README.txt and LICENSE.txt (package.ps1 copies them next to the
                    exe): neither empty; README has a 'Title:' line and 'Controls', 'Team' and 'Credits'
                    sections, and no pipeline text (ROLE:, 'card <n>'); LICENSE names a copyright
                    holder line. --final (G4): no TBD left in either file.
  signoff LINE      the human CONTENT line (G4, Official Rules 8, 15(d), 7(d)(e), 7(f), 7(i)):
                    CONTENT teen=yes trademarks=ue-logo-only original=yes extra-software=none english=yes by=<name>; or
                    the human VIDEO line: first-frame=gameplay logo-first=no gameplay-by=<s, at most 5>
                    end=logo+CTA music=yes sfx-beats=yes by=<name>.

Exit 0 = pass, 1 = problems, 2 = not run (a tool is missing, or git failed).
Tests: python3 -m unittest tests.test_submission_check (all suites: python3 -m unittest discover tests).
"""
import argparse
import csv
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Jam rules (docs/jam-rules.md). Change only with the rule's source quoted in the commit message.
MAX_ZIP_BYTES = 1_000_000_000          # "keep it under 1 GB"; decimal GB is the strict reading
ZIP_NAME = re.compile(r"^([A-Za-z0-9]+)_([A-Za-z0-9]+)\.zip$")   # "TeamName_GameName"
REQUIRED_CONFIG = "Development"        # "Package your game for Windows (development build)"
REQUIRED_PLATFORM = "Win64"
VIDEO_MIN_S, VIDEO_MAX_S = 30.0, 60.0  # Official Rules 1(e): "between 30-60 seconds"
VIDEO_MIN_W, VIDEO_MIN_H = 1920, 1080  # Official Rules 7(c): "match 1920x1080 or higher"
LUFS_TARGET, LUFS_TOL = -14.0, 2.0     # web video norm; team default, not a jam rule
# GDD 1.3 section 12A: "Jam begins November 12 at 12:00 AM EST (November 11 at 9:00 PM PST)". One value everywhere.
JAM_START = dt.datetime(2026, 11, 11, 21, 0, tzinfo=dt.timezone(dt.timedelta(hours=-8)))  # = 2026-11-12T00:00-05:00
# Official Rules 4: ends 8:59 PM ET on November 15, 2026 (= 17:59 PST). The jam-brief Clock deadline must equal it.
JAM_END = dt.datetime(2026, 11, 15, 17, 59, tzinfo=dt.timezone(dt.timedelta(hours=-8)))  # = 2026-11-15T20:59-05:00
TEAM_MIN, TEAM_MAX = 1, 5              # Official Rules 1(a)
OFFICIAL_RULES = "docs/rules/official-rules.md"
# (section, words the Official Rules text must hold, whitespace-normalized). `rules` fails when the pinned text no
# longer says what the constants above encode, so a new rules version cannot slip past the checks.
RULES_FACTS = (
    ("4", "The Contest begins at 12:00 AM Eastern Time (\"ET\") on November 12, 2026, and ends at 8:59 PM ET on "
          "November 15, 2026"),
    ("1(a)", "must be created by a team of one (1) to five (5) Entrants"),
    ("1(b)", "must be packaged for Windows and playable on Windows 10 or 11"),
    ("1(c)", "include the full name and email address of all Entrants on a submitting team, identifying one of them "
             "as the team owner"),
    ("1(d)", "the sourced assets must be noted upon submission"),
    ("1(e)", "include a video short (between 30-60 seconds) demonstrating recorded gameplay"),
    ("7(c)", "Resolution of the Video must match 1920x1080 or higher"),
    ("7(h)", "All other game content, including gameplay, levels, and art assets (other than noted sourced assets), "
             "must be created during the Contest Period"),
    ("7(i)", "must be in English"),
    ("10", "the dev log must be submitted together with the Submission during the Contest Period"),
    ("17", "must be submitted by an Entrant (on behalf of the team) and not by an AI agent or other automated means"),
)

# In-jam inputs. THEME_DUE = the kickoff (Nov 11, 11 AM PST) plus 2 h.
THEME_DUE = dt.datetime(2026, 11, 11, 13, 0, tzinfo=dt.timezone(dt.timedelta(hours=-8)))
JAM_LAST_DAY = 4                       # D1-D4 (docs/jam-brief.md Team hours)
FOOTAGE_FROM_DAY = 2                   # "From G1 on"; G1 is the end of Day 1
FOOTAGE_MIN_PER_DAY = 2
CAPTURE_LINE = re.compile(r"\bCAPTURE_MODE\b(.*)$", re.M)
CAPTURE_NEED = {"hud": "off", "debug": "off", "cursor": "off"}
VIDEO_SIGNOFF = {"first-frame": "gameplay", "logo-first": "no", "end": "logo+CTA", "music": "yes", "sfx-beats": "yes"}
GAMEPLAY_BY_MAX_S = 5.0                # "Show gameplay in the first five seconds."

COVER_MIN_W, COVER_MIN_H = 630, 500    # itch cover: 315x250 minimum, 630x500 recommended
COVER_RATIO = 315 / 250
SHOTS_MIN, SHOTS_MAX = 3, 5
SHOT_MIN_W, SHOT_MIN_H = 1920, 1080
BEATS = ("volley", "rise", "fall", "gust", "torn", "end")
P1_BEATS = {"gust": "gust", "torn": "wear"}   # beat -> test-map row (P1) that must be merged before it is required
DEVLOG_HEADINGS = ("Went right", "Went wrong", "Change next time")
DEVLOG_MIN_PER_DAY = 3
CREDIT_NEEDED = re.compile(r"CC-BY|OFL|\bFab\b|third-party", re.I)
FONT_EXT = (".ttf", ".otf", ".woff", ".woff2")
CREDIT_ROLES = ("Game design", "Programming", "Art", "Audio", "Production", "QA")
CONTROLS_ROW = "DEC-02"                # docs/decisions.md row that fixes firing (GDD B §13: does closed aiming auto-fire)
KEYS_ROW = "DEC-01"                    # docs/decisions.md row that fixes the bindings (GDD B §13)
SETTLED = re.compile(r"^\s*DECIDED\b|default accepted", re.I)  # card 0.0: a linked "default accepted" counts
CONTROLS_QUESTION = re.compile(r"\bauto", re.I)  # the row must ask the current-GDD question (GDD B §13 automatic fire)
README_SECTIONS = ("Controls", "Team", "Credits")
PIPELINE_TEXT = re.compile(r"ROLE:|\bcard #?\d")
GATE_DIR = re.compile(r"^(G[1-4])-([0-9a-f]{7,40})$")
BUTLER_LINE = re.compile(r"^\s*BUTLER\s")
LINK = re.compile(r"https?://\S+|(?<![\w/])#\d+\b|\bgate-G[1-4]\b")

SUB = "pipeline/submission"
PAGE_DIR = f"{SUB}/page"
ITCH_PAGE = f"{SUB}/itch-page.md"
CREDITS = f"{SUB}/credits.md"
README_TXT = f"{SUB}/README.txt"
LICENSE_TXT = f"{SUB}/LICENSE.txt"
DEVLOG = f"{SUB}/devlog.md"
FOOTAGE = f"{SUB}/footage.md"
DECLARATION = "docs/pre-jam-declaration.md"
BRIEF = "docs/jam-brief.md"
JAM_RULES = "docs/jam-rules.md"
DECISIONS = "docs/decisions.md"
PROVENANCE = "pipeline/art/provenance.csv"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------- zip ----------------
def parse_build_info(text):
    out = {}
    for ln in text.splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def zip_problems(path, team=None, game=None, commit=None, max_bytes=MAX_ZIP_BYTES, gate=None):
    out = []
    name = os.path.basename(path)
    if gate:
        folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
        g = GATE_DIR.match(folder)
        if not g or g.group(1) != gate:
            out.append(f"gate zip folder is '{folder}', need {gate}-<sha> (rule 2, docs/jam-rules.md)")
        else:
            commit = commit or g.group(2)
            if not g.group(2).startswith(commit[:7]) and not commit.startswith(g.group(2)):
                out.append(f"gate zip folder sha {g.group(2)} is not --commit {commit}")
    m = ZIP_NAME.match(name)
    if not m:
        out.append(f"name '{name}' is not TeamName_GameName.zip (letters and digits, one underscore)")
    elif (team and m.group(1) != team) or (game and m.group(2) != game):
        out.append(f"name '{name}' is not {team or m.group(1)}_{game or m.group(2)}.zip")
    size = os.path.getsize(path)
    if size > max_bytes:
        out.append(f"zip is {size} bytes, over {max_bytes}; make it smaller (upload with butler only if the"
                   " jam rules allow, docs/jam-rules.md)")
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return out + ["not a zip file"]
    with zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        for n in names:
            parts = n.split("/")
            low = n.lower()
            if low.endswith(".uproject"):
                out.append(f"{n}: a .uproject; this is the project, not a packaged build")
            elif low.endswith((".cpp", ".h", ".cs")):
                out.append(f"{n}: source code in the zip")
            elif low.endswith((".uasset", ".umap")) and "Paks" not in parts:
                out.append(f"{n}: loose asset outside Paks/; not a cooked package")
            if "Saved" in parts[:-1]:
                out.append(f"{n}: Saved/ folder in the zip (local logs, config or crashes)")
        exes = [n for n in names if n.lower().endswith(".exe")
                and "Engine" not in n.split("/") and "Binaries" not in n.split("/")]
        if len(exes) != 1:
            out.append(f"expected 1 game exe outside Engine/ and Binaries/, found {len(exes)}: {exes[:5]}")
            return out
        folder = exes[0].rsplit("/", 1)[0] + "/" if "/" in exes[0] else ""
        for need in ("README.txt", "LICENSE.txt", "BUILD_INFO.txt"):
            if folder + need not in names:
                out.append(f"{need} missing next to {exes[0]}")
            elif need != "BUILD_INFO.txt" and not zf.read(folder + need).strip():
                out.append(f"{need} next to {exes[0]} is empty")
        if folder + "README.txt" in names:
            readme = zf.read(folder + "README.txt").decode("utf-8", "replace")
            if "controls" not in readme.lower():
                out.append("README.txt has no Controls section")
            if "ROLE:" in readme:
                out.append("README.txt holds pipeline text (ROLE:)")
        if not any(re.search(r"(^|/)[^/]+/Binaries/Win64/[^/]+\.exe$", n) and "Engine" not in n.split("/")
                   for n in names):
            out.append("no <Project>/Binaries/Win64/*.exe; not a Win64 package")
        if folder + "BUILD_INFO.txt" in names:
            info = parse_build_info(zf.read(folder + "BUILD_INFO.txt").decode("utf-8", "replace"))
            if info.get("config") != REQUIRED_CONFIG:
                out.append(f"BUILD_INFO config={info.get('config')}, the jam needs {REQUIRED_CONFIG}")
            if "platform" in info and info["platform"] != REQUIRED_PLATFORM:
                out.append(f"BUILD_INFO platform={info['platform']}, the jam needs {REQUIRED_PLATFORM}")
            if info.get("workbench") != "0":
                out.append(f"BUILD_INFO workbench={info.get('workbench', '<none>')}; the submission is built with the "
                           "workbench compiled out: package.ps1 without -Workbench (D-new-workbench-debug)")
            if info.get("dirty") != "no":
                out.append(f"BUILD_INFO dirty={info.get('dirty')}; package from a clean tag")
            if commit and not (info.get("commit") or "").startswith(commit):
                out.append(f"BUILD_INFO commit={info.get('commit')} is not {commit}")
    return out


def zip_commit(path):
    """BUILD_INFO commit= inside a package zip, or 'unknown'."""
    try:
        with zipfile.ZipFile(path) as zf:
            for n in zf.namelist():
                if n.endswith("BUILD_INFO.txt"):
                    return parse_build_info(zf.read(n).decode("utf-8", "replace")).get("commit") or "unknown"
    except (OSError, zipfile.BadZipFile):
        pass
    return "unknown"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------------- video and audio ----------------
def video_problems(probe):
    """probe = ffprobe JSON (-show_streams -show_format)."""
    out = []
    try:
        dur = float((probe.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        dur = None
    if dur is None:
        out.append("no duration in ffprobe output")
    elif not VIDEO_MIN_S <= dur <= VIDEO_MAX_S:
        out.append(f"duration {dur:.1f} s is outside {VIDEO_MIN_S:g}-{VIDEO_MAX_S:g} s")
    streams = probe.get("streams") or []
    vids = [s for s in streams if s.get("codec_type") == "video"]
    if not vids:
        out.append("no video stream")
    else:
        w, h = int(vids[0].get("width") or 0), int(vids[0].get("height") or 0)
        if w < VIDEO_MIN_W or h < VIDEO_MIN_H:
            out.append(f"video is {w}x{h}, below {VIDEO_MIN_W}x{VIDEO_MIN_H}")
    if not any(s.get("codec_type") == "audio" for s in streams):
        out.append("no audio stream (audio is a judged criterion)")
    return out


def probe_video(path):
    p = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise OSError(p.stderr.strip() or "ffprobe failed")
    return json.loads(p.stdout)


def integrated_lufs(ffmpeg_stderr):
    """The 'I: -14.2 LUFS' value from ffmpeg's ebur128 summary, or None."""
    m = re.findall(r"^\s*I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", ffmpeg_stderr, re.M)
    return float(m[-1]) if m else None


def loudness_problems(lufs):
    if lufs is None:
        return ["no integrated loudness in ffmpeg output (no audio?)"]
    if abs(lufs - LUFS_TARGET) > LUFS_TOL:
        return [f"integrated loudness {lufs:.1f} LUFS is outside {LUFS_TARGET:g} +- {LUFS_TOL:g}"]
    return []


def measure_lufs(path):
    p = subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-nostats", "-i", path, "-filter_complex", "ebur128",
                        "-f", "null", "-"], capture_output=True, text=True)
    return integrated_lufs(p.stderr)


# ---------------- itch page ----------------
def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    return struct.unpack(">II", head[16:24])


def page_fields(text):
    """{field: value} from the '## Page fields' table."""
    m = re.search(r"^## Page fields.*?$(.*?)(?=^## |\Z)", text, re.S | re.M)
    out = {}
    for ln in (m.group(1) if m else "").splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and len(cells) >= 2 and not set(cells[0]) <= set("-: "):
            out[cells[0]] = cells[1]
    out.pop("Field", None)
    return out


def md_section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}.*?$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else None


def team_table(text):
    """(header, rows) from the '## Team' table; each row is a list of cells."""
    sec = md_section(text, "Team") or ""
    header, rows = None, []
    for ln in sec.splitlines():
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
        elif len(cells) >= 3 and not set(cells[0]) <= set("-: "):
            rows.append(cells)
    return header or [], rows


def team_rows(text):
    """[[full name, role, ..., email y/n], ...] from the '## Team' table."""
    return team_table(text)[1]


def team_col(header, word):
    return next((i for i, h in enumerate(header) if word in h), None)


def team_problems(itch_text):
    """Official Rules 1(a), 1(c): a team of 1 to 5 Entrants, each with full name and email, one of them the Team
    Owner (the Team Owner submits for the team, 15(a))."""
    out = []
    header, rows = team_table(itch_text)
    if not rows:
        return ["itch-page.md has no '## Team' table rows (Official Rules 1(c): each Entrant's full name and email)"]
    if not TEAM_MIN <= len(rows) <= TEAM_MAX:
        out.append(f"itch-page.md Team table has {len(rows)} members; Official Rules 1(a): {TEAM_MIN} to {TEAM_MAX}")
    ei, oi = team_col(header, "email"), team_col(header, "owner")
    if oi is None:
        out.append("itch-page.md Team table has no 'Team Owner (y/n)' column (Official Rules 1(c))")
    for r in rows:
        if not _filled(r[0]) or not _filled(r[1]):
            out.append(f"itch-page.md Team row '{' | '.join(r)}' has a TBD or empty cell")
        elif len(r[0].split()) < 2:
            out.append(f"itch-page.md Team row '{r[0]}': Official Rules 1(c) asks for the full name (first and last)")
        mail = r[ei] if ei is not None and ei < len(r) else ""
        if mail.lower() != "y":
            out.append(f"itch-page.md Team row '{r[0]}': Epic email collected is '{mail}', need y")
    if oi is not None:
        owners = [r[0] for r in rows if oi < len(r) and r[oi].lower() == "y"]
        if len(owners) != 1:
            out.append(f"itch-page.md Team table names {len(owners)} Team Owner(s); Official Rules 1(c): exactly one")
    sec = md_section(itch_text, "Credits by role")
    if sec is None:
        return out + ["itch-page.md has no '## Credits by role' section"]
    lines = dict((m.group(1).strip().lower(), m.group(2).strip())
                 for m in re.finditer(r"^\s*[-*]\s+([^:\n]+):\s*(.*)$", sec, re.M))
    for role in CREDIT_ROLES:
        if not _filled(lines.get(role.lower(), "")):
            out.append(f"itch-page.md Credits by role has no filled '- {role}: <names>' line")
    names = " ".join(lines.values())
    for r in rows:
        if _filled(r[0]) and r[0] not in names:
            out.append(f"itch-page.md Credits by role does not name Team member '{r[0]}'")
    return out


def decision_status(decisions_text, row_id):
    for ln in decisions_text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and cells and cells[0] == row_id:
            return cells[-1]
    return None


def decision_question(decisions_text, row_id):
    for ln in decisions_text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and len(cells) > 1 and cells[0] == row_id:
            return cells[1]
    return None


def controls_problems(decisions_text):
    st = decision_status(decisions_text, CONTROLS_ROW)
    if st is None:
        return [f"{DECISIONS} has no row {CONTROLS_ROW} (controls: auto-fire vs aimed shot)"]
    out = []
    q = decision_question(decisions_text, CONTROLS_ROW) or ""
    if not CONTROLS_QUESTION.search(q):
        out.append(f"{DECISIONS} row {CONTROLS_ROW} asks '{q[:60]}', not the current GDD question"
                   " (automatic fire, GDD B §13 DEC-02); a DECIDED answer to it can't fix the controls")
    for row, st_ in ((CONTROLS_ROW, st), (KEYS_ROW, decision_status(decisions_text, KEYS_ROW))):
        if st_ is None and row == KEYS_ROW:
            continue  # unit-test tables without the keys row; the repo has it (test_doc_consistency)
        if not SETTLED.search(st_ or ""):
            out.append(f"{DECISIONS} row {row} (controls) is '{st_}'; the page Controls wait for DECIDED"
                       " or a linked 'default accepted'")
    return out


def page_problems(page_dir, itch_text, decisions_text=None):
    """decisions_text=None skips the controls-row check (unit tests of the image rules only)."""
    out = []
    cover = os.path.join(page_dir, "cover.png")
    if not os.path.isfile(cover):
        out.append("cover.png missing")
    else:
        try:
            w, h = png_size(cover)
            if w < COVER_MIN_W or h < COVER_MIN_H:
                out.append(f"cover.png is {w}x{h}, below {COVER_MIN_W}x{COVER_MIN_H}")
            if abs(w / h - COVER_RATIO) > 0.01 * COVER_RATIO:
                out.append(f"cover.png is {w}x{h}, not 315:250")
        except ValueError:
            out.append("cover.png is not a PNG")
    shots = sorted(f for f in (os.listdir(page_dir) if os.path.isdir(page_dir) else []) if f.startswith("shot-"))
    if not SHOTS_MIN <= len(shots) <= SHOTS_MAX:
        out.append(f"{len(shots)} screenshots, need {SHOTS_MIN}-{SHOTS_MAX}")
    hashes = {}
    for f in shots:
        m = re.fullmatch(r"shot-([a-z]+)\.png", f)
        if not m or m.group(1) not in BEATS:
            out.append(f"{f}: name is not shot-<beat>.png with a beat from {', '.join(BEATS)}")
            continue
        p = os.path.join(page_dir, f)
        try:
            w, h = png_size(p)
        except ValueError:
            out.append(f"{f}: not a PNG")
            continue
        if w < SHOT_MIN_W or h < SHOT_MIN_H:
            out.append(f"{f}: {w}x{h}, below {SHOT_MIN_W}x{SHOT_MIN_H}")
        d = sha256(p)
        if d in hashes:
            out.append(f"{f}: same file as {hashes[d]}")
        hashes[d] = f
    fields = page_fields(itch_text)
    if not fields:
        out.append("itch-page.md has no '## Page fields' table")
    for k, v in fields.items():
        if not v or re.search(r"\bTBD\b", v):
            out.append(f"itch-page.md field '{k}' is not filled")
    out += team_problems(itch_text)
    if decisions_text is not None:
        out += controls_problems(decisions_text)
    return out


# ---------------- pre-jam assets (Official Rules 7(h)) and English (7(i)) ----------------
GAME_ASSET_DIRS = ("Content/", "Art/", "Audio/")
REFERENCE_DIR = "pipeline/art/reference"
SOURCED_HEADING = "Sourced assets"
LFS_OID = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\s*\noid sha256:([0-9a-f]{64})")
NON_LATIN = ("CJK", "CYRILLIC", "ARABIC", "HEBREW", "GREEK", "HANGUL", "HIRAGANA", "KATAKANA", "THAI", "DEVANAGARI",
             "BENGALI", "TAMIL", "ARMENIAN", "GEORGIAN", "ETHIOPIC")
ENGLISH_FILES = (README_TXT, LICENSE_TXT, ITCH_PAGE, CREDITS, DEVLOG)


def sourced_paths(credits_text):
    """Paths in the credits.md '## Sourced assets' table (Official Rules 1(d), 15(c): noted upon submission)."""
    sec = md_section(credits_text or "", SOURCED_HEADING) or ""
    return {c.strip().strip("`") for ln in sec.splitlines() if ln.strip().startswith("|")
            for c in ln.strip().strip("|").split("|")[:1]}


def asset_date(value):
    """The provenance date as an aware datetime (a bare date is midnight ET), or None."""
    v = (value or "").strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return dt.datetime.fromisoformat(v + "T00:00-05:00")
        d = dt.datetime.fromisoformat(v)
        return d if d.tzinfo else None
    except ValueError:
        return None


def content_digest(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    m = LFS_OID.match(raw)
    return m.group(1).decode() if m and len(raw) < 1024 else hashlib.sha256(raw).hexdigest()


_START = object()


def assets_problems(csv_text, credits_text, root=ROOT, start=_START):
    """Official Rules 7(h): game content is made during the Contest Period, except noted sourced assets. A provenance
    row under Content/, Art/ or Audio/ needs a date; one before JAM_START fails unless the path is in credits.md
    'Sourced assets'. Pre-jam art is reference only: no game file is a byte copy of a pipeline/art/reference/ file or
    of any picture pipeline/art/references.json lists (under pipeline/art/reference/: Test_Assets/, Mockups/, the rehearsal sprites, the Discord posts;
    and the team art under Assets/ and Mockups/ that it joins: tools/art_check.py load_spec)."""
    start = JAM_START if start is _START else start   # None: a practice repo (tools/practice.py), D39 lifted
    out = []
    stand_ins = set()   # practice stand-ins placed by tools/assetgen.py --provider reference
    sourced = sourced_paths(credits_text)
    for r in provenance_rows(csv_text):
        path = (r.get("asset_path") or "").strip()
        if not path.startswith(GAME_ASSET_DIRS):
            continue
        if "source=reference (practice)" in (r.get("origin") or ""):
            stand_ins.add(path)
        if start is not None and "source=reference (practice)" in (r.get("origin") or ""):
            out.append(f"{path}: a practice stand-in copied from the team's reference art (source=reference (practice)); "
                       "only a practice repo may use one. Generate it in the jam (GDD 1.3 7C, Official Rules 7(h))")
            continue
        when = asset_date(r.get("date"))
        if when is None:
            out.append(f"{path}: provenance date {r.get('date')!r} is not YYYY-MM-DD or an ISO time with offset")
        elif start is not None and when < start and path not in sourced:
            out.append(f"{path}: provenance date {r.get('date')} is before the contest start ({start.isoformat()}) "
                       f"and it is not in {CREDITS} '{SOURCED_HEADING}' (Official Rules 7(h); pre-jam art is reference only)")
    refs = {}
    rdir = os.path.join(root, REFERENCE_DIR)
    for d, _, fs in os.walk(rdir):
        for f in fs:
            refs[content_digest(os.path.join(d, f))] = os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
    try:   # the team's art references (pipeline/art/references.json): style targets, never shipped (GDD 1.3 7C)
        sys.path.insert(0, os.path.join(root, "tools"))
        import art_check
        for rel in art_check.reference_files(root):
            if rel.lower().endswith(ART_EXT):
                refs.setdefault(content_digest(os.path.join(root, rel)), rel)
    except ImportError:
        pass
    for top in GAME_ASSET_DIRS:
        for d, _, fs in os.walk(os.path.join(root, top)):
            for f in fs:
                full = os.path.join(d, f)
                if start is None and os.path.relpath(full, root).replace(os.sep, "/") in stand_ins:
                    continue   # a practice repo: its labelled stand-in may be a byte copy (never on the team repo)
                ref = refs.get(content_digest(full))
                if ref:
                    out.append(f"{os.path.relpath(full, root)}: same bytes as {ref}; pre-jam reference art is never shipped")
    return out


def english_problems(texts):
    """Official Rules 7(i): all Submission content and entry information is in English. Heuristic: a letter from a
    non-Latin script in a submission text or string table fails. A human still signs off audio and the video."""
    import unicodedata
    out = []
    for name, text in texts:
        for n, ln in enumerate(text.splitlines(), 1):
            bad = [ch for ch in ln if ord(ch) > 0x24F and ch.isalpha()
                   and any(w in unicodedata.name(ch, "") for w in NON_LATIN)]
            if bad:
                out.append(f"{name}:{n}: non-English script {''.join(bad[:8])!r} (Official Rules 7(i): English only)")
    return out


def english_files(root=ROOT):
    """Submission texts plus string tables (*.csv, *.json) under Content/ and pipeline/ui/."""
    out = [p for p in ENGLISH_FILES if os.path.isfile(os.path.join(root, p))]
    for top in ("Content", "pipeline/ui"):
        for d, _, fs in os.walk(os.path.join(root, top)):
            out += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in fs
                    if f.lower().endswith((".csv", ".json"))]
    return sorted(out)


# ---------------- credits and fonts ----------------
def provenance_rows(csv_text):
    return list(csv.DictReader(io.StringIO(csv_text)))


def credits_problems(csv_text, credits_text, font_paths, art_paths=()):
    out = []
    rows = provenance_rows(csv_text)
    for r in rows:
        path = r.get("asset_path", "")
        if path.startswith("pipeline/art/reference/"):
            continue  # reference only, never shipped
        if CREDIT_NEEDED.search((r.get("licence") or "") + " " + (r.get("origin") or "")):
            if path not in credits_text:
                out.append(f"{path}: needs a credit ({r.get('licence')}) and is not in {CREDITS}")
    known = {r.get("asset_path") for r in rows}
    for p in font_paths:
        if p not in known:
            out.append(f"{p}: font with no provenance row in {PROVENANCE}")
    for p in art_paths:   # dry run B M1: AGENTS.md "never use art without a provenance row and a known licence"
        if p not in known:
            out.append(f"{p}: art file with no provenance row in {PROVENANCE}")
    return out


ART_EXT = (".png", ".jpg", ".jpeg", ".psd", ".ase", ".aseprite", ".tga", ".webp")
ART_DIRS = ("Art", "pipeline/art/fallback")


def art_files(root):
    """Image sources that can reach the game: everything under Art/ and the CC0 fallback set."""
    out = []
    for top in ART_DIRS:
        for d, dirs, fs in os.walk(os.path.join(root, top)):
            rel = os.path.relpath(d, root).replace(os.sep, "/")
            out += [f"{rel}/{f}" for f in fs if f.lower().endswith(ART_EXT)]
    return sorted(out)


def art_loop_problems(root=ROOT):
    """Every shipped art file (an image under Art/ outside Art/Source/) has its passing art-loop record for these
    exact bytes (tools/art_loop.py record_problems: ours or SAME against a reference and the quality bar, the motion
    pair for a sheet, art_check/screen_check/art_ref_check PASS, current references.json). A placeholder or stand-in
    never passes. No human sign-off waives it (Josh, 11 Nov: the reference bar is enforced, not advised)."""
    sys.path.insert(0, os.path.join(root, "tools"))
    import art_loop
    out = []
    rh = None
    for d, dirs, fs in os.walk(os.path.join(root, "Art")):
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
            if art_loop.shipped(rel):
                rh = rh or art_loop.refs_and_hash(root)[1]
                out += art_loop.record_problems(root, rel, rh)
    return out


def font_files(root):
    out = []
    for d, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if x not in (".git", "Saved", "Intermediate", "DerivedDataCache", "Binaries")]
        rel = os.path.relpath(d, root).replace(os.sep, "/")
        for f in fs:
            p = f if rel == "." else f"{rel}/{f}"
            if f.lower().endswith(FONT_EXT) or (p.startswith("Content/") and "/Fonts/" in p and f.endswith(".uasset")):
                out.append(p)
    return sorted(out)


# ---------------- devlog ----------------
def devlog_problems(text, day, published=False):
    out = []
    heads = re.findall(r"^##\s+(.+?)\s*$", text, re.M)
    for h in DEVLOG_HEADINGS:
        if h not in heads:
            out.append(f"devlog has no '## {h}' heading")
    for d in range(1, day + 1):
        m = re.search(rf"^### Day {d}\b.*?$(.*?)(?=^##|\Z)", text, re.S | re.M)
        lines = [ln for ln in (m.group(1) if m else "").splitlines()
                 if re.match(r"\s*[-*]\s+\S", ln) and LINK.search(ln)]
        if len(lines) < DEVLOG_MIN_PER_DAY:
            out.append(f"Day {d}: {len(lines)} obstacle line(s) with a link, need {DEVLOG_MIN_PER_DAY}")
    if published:
        m = re.search(r"^Published:\s*(https://\S+)", text, re.M)
        if not m:
            out.append("no 'Published: https://...' line; the devlog link goes on the jam submission")
    return out


# ---------------- in-jam inputs ----------------
def _filled(v):
    return bool(v) and not re.search(r"\bTBD\b", v)


def theme_problems(brief_text, now, due=THEME_DUE):
    if now < due:
        return []
    out = []
    m = re.search(r"^Theme:[ \t]*(.*)$", brief_text, re.M)
    v = m.group(1).strip() if m else ""
    if not _filled(v) or not re.search(r'["\u201c].+["\u201d]', v):
        out.append(f"{BRIEF} has no 'Theme: \"<kickoff quote>\"' line, due {due.isoformat()} (owner: game design owner, card 0.19)")
    m = re.search(r"^Theme in game:[ \t]*(.*)$", brief_text, re.M)
    if not _filled(m.group(1).strip() if m else ""):
        out.append(f"{BRIEF} has no 'Theme in game: <how THE LAST HOUR shows it>' line, due {due.isoformat()}")
    return out


def capture_problems(log_text):
    lines = CAPTURE_LINE.findall(log_text)
    if not lines:
        return ["no CAPTURE_MODE line in the log; run the package with -CaptureMode (video-plan.md)"]
    kv = dict(re.findall(r"(\w+)=(\S+)", lines[-1]))
    return [f"CAPTURE_MODE {k}={kv.get(k)}, need {k}={v}" for k, v in CAPTURE_NEED.items() if kv.get(k) != v]


def footage_clips(text):
    """{day: set of clip names} from '### Day N' sections of footage.md."""
    out = {}
    for m in re.finditer(r"^### Day (\d+)\b.*?$(.*?)(?=^##|\Z)", text, re.S | re.M):
        d = int(m.group(1))
        out[d] = set(re.findall(rf"^\s*[-*]\s+`?({d}-[a-z]+-[0-9a-f]{{7,40}}\.mp4)`?", m.group(2), re.M))
    return out


def merged_features(root=ROOT):
    """Lower-case labels of merged pipeline/qa/test-map.md rows (same reading as encounter_check)."""
    sys.path.insert(0, os.path.join(root, "tools"))
    import encounter_check
    return encounter_check.merged_features(os.path.join(root, "pipeline", "qa", "test-map.md"))


def footage_problems(text, day, final=False, merged=None):
    """merged: merged test-map labels (None = read the repo); a cut or unbuilt P1 feature needs no beat."""
    out = []
    clips = footage_clips(text)
    for d in range(FOOTAGE_FROM_DAY, day + 1):
        good = {c for c in clips.get(d, set()) if c.split("-")[1] in BEATS}
        bad = clips.get(d, set()) - good
        for c in sorted(bad):
            out.append(f"Day {d}: {c} has no beat from {', '.join(BEATS)}")
        if len(good) < FOOTAGE_MIN_PER_DAY:
            out.append(f"Day {d}: {len(good)} clip(s) in {FOOTAGE}, need {FOOTAGE_MIN_PER_DAY}"
                       " (owner Asset Specialist, video-plan.md)")
    if final:
        have = {c.split("-")[1] for cs in clips.values() for c in cs}
        merged = merged_features() if merged is None else merged
        miss = [b for b in BEATS if b not in have and (b not in P1_BEATS or P1_BEATS[b] in merged)]
        if miss:
            out.append(f"no clip yet for beat(s): {', '.join(miss)}; the shot list needs each one")
    return out


def daily_problems(day, now, root=ROOT):
    """What check_card.py --status runs for the day just ended."""
    def rd(rel):
        p = os.path.join(root, rel)
        return read(p) if os.path.isfile(p) else ""
    return (devlog_problems(rd(DEVLOG), day) + footage_problems(rd(FOOTAGE), day)
            + theme_problems(rd(BRIEF), now))


def gate_times(brief_text):
    """[(gate, datetime)] from the jam-brief Clock table, skipping TBD or bad times."""
    sec = re.search(r"^## Clock.*?$(.*?)(?=^## |\Z)", brief_text or "", re.S | re.M)
    out = []
    for m in re.finditer(r"^\|\s*(G[1-4])\s*\|\s*([^|]*?)\s*\|", sec.group(1) if sec else "", re.M):
        try:
            t = dt.datetime.fromisoformat(m.group(2).replace("Z", "+00:00"))
        except ValueError:
            continue
        if t.tzinfo:
            out.append((m.group(1), t))
    return out


def day_ended(brief_text, now):
    """The last jam day that has ended: Day N ends at gate G<N>. 0 before G1 or with no Clock times."""
    return max([int(g[1]) for g, t in gate_times(brief_text) if t <= now] or [0])


def status_hook(brief_text, now, root=ROOT):
    """check_card.py --status calls this: the daily checks for the day just ended."""
    day = day_ended(brief_text, now)
    return [f"submission (Day {day}): {p}" for p in daily_problems(day, now, root)] if day else theme_problems(brief_text or "", now)


# (file, text that must be there, or with a leading '!' must not be there, what it wires)
WIRING = (
    ("pipeline/day0-cards.md", "-CaptureMode", "a Day-0 card builds the capture switch (video-plan.md)"),
    ("pipeline/day0-cards.md", "submission_check.py capture", "that card's done-when runs the capture check"),
    ("pipeline/day0-cards.md", "submission_check.py rules", "card 0.2 clears the [VERIFY] tags in docs/jam-rules.md"),
    ("pipeline/day0-cards.md", "jam-rules.md row AI", "card 0.2 closes D14 by citing the quoted AI rule"),
    ("pipeline/day0-cards.md", "!uploaded hidden to the jam page", "card 0.4b uploads to the team's Draft itch project (rule 5)"),
    ("pipeline/day0-cards.md", "Video cut", "a G3-G4 card gives the video edit time"),
    ("pipeline/day0-cards.md", "!enemy defeat", "card 0.15 makes the GDD fallback set, not the old platformer set"),
    ("pipeline/roles/producer.md", "submission_check.py daily", "the Producer runs the daily devlog, footage and theme check"),
    ("pipeline/roles/producer.md", "devlog.md", "the Producer card names the devlog (Glass Box) duty"),
    ("pipeline/roles/producer.md", "video checks", "the G4 row lists the video checks"),
    ("pipeline/roles/asset-specialist.md", "submission_check.py footage", "the Asset Specialist card names the footage duty"),
    ("pipeline/roles/asset-specialist.md", "video-plan.md", "the Asset Specialist card names the video cut"),
    ("pipeline/roles/qa-build.md", "G<n>-<sha>/<TeamName>_<GameName>.zip", "gate zips use the jam zip name (rule 2)"),
    ("pipeline/roles/qa-build.md", "submission_check.py zip", "QA runs the zip check on every gate zip"),
    ("pipeline/roles/qa-build.md", "!UmbrellaElla-<gate", "no old gate zip name"),
    ("tools/check_card.py", "status_hook", "check_card.py --status runs the daily submission checks"),
    ("tools/check_card.py", "BUTLER", "check_card.py --gate-record G1 needs the BUTLER line"),
    ("tools/check_card.py", "!jam-page test upload", "test uploads go to the team's Draft itch project"),
    ("docs/jam-brief.md", "Submission deadline: 2026-11-15T17:59-08:00", "the Clock holds the real deadline"),
    ("pipeline/templates/gate-record.md", "!uploaded to the jam page", "test uploads go to the team's Draft itch project (rule 5)"),
    ("tools/ue/package.ps1", "README.txt", "package.ps1 copies pipeline/submission/README.txt next to the exe"),
    ("tools/ue/package.ps1", "LICENSE.txt", "package.ps1 copies pipeline/submission/LICENSE.txt next to the exe"),
)


def wiring_problems(root=ROOT, wiring=WIRING):
    out = []
    for rel, needle, why in wiring:
        p = os.path.join(root, rel)
        text = read(p) if os.path.isfile(p) else ""
        bad = needle[1:] in text if needle.startswith("!") else needle not in text
        if bad:
            verb = "still has" if needle.startswith("!") else "has no"
            out.append(f"{rel} {verb} '{needle.lstrip('!')}': {why}")
    return out


def butler_problems(line):
    if not BUTLER_LINE.match(line or ""):
        return ["not a 'BUTLER ...' line"]
    kv = dict(re.findall(r"([\w-]+)=(\S+)", line))
    out = []
    if not re.fullmatch(r"v?\d+\.\d+(\.\d+)?\S*", kv.get("version", "")):
        out.append(f"version={kv.get('version')}, need the output of 'butler -V'")
    if kv.get("login") != "ok":
        out.append(f"login={kv.get('login')}, need login=ok ('butler login' on the packaging machine)")
    for k in ("user", "by"):
        if not _filled(kv.get(k, "")) or kv.get(k, "").startswith("<"):
            out.append(f"{k}=<...> missing")
    return out


def files_problems(readme, licence, final=False):
    """readme/licence = text of pipeline/submission/README.txt and LICENSE.txt, or None if missing."""
    out = []
    for name, text in (("README.txt", readme), ("LICENSE.txt", licence)):
        if text is None:
            out.append(f"{SUB}/{name} missing; package.ps1 copies it next to the exe")
        elif not text.strip():
            out.append(f"{SUB}/{name} is empty")
        elif PIPELINE_TEXT.search(text):
            out.append(f"{SUB}/{name} holds pipeline text ('{PIPELINE_TEXT.search(text).group(0)}')")
        elif final and re.search(r"\bTBD\b", text):
            out.append(f"{SUB}/{name} still has TBD (G4 needs every line filled)")
    if readme and readme.strip():
        if not re.search(r"^Title:[ \t]*\S", readme, re.M):
            out.append("README.txt has no 'Title: <game title>' line")
        for sec in README_SECTIONS:
            if not re.search(rf"^{sec}\b", readme, re.M):
                out.append(f"README.txt has no '{sec}' section (a line starting '{sec}')")
    if licence and licence.strip() and not re.search(r"^Copyright\b", licence, re.M):
        out.append("LICENSE.txt has no 'Copyright <year> <holder>' line")
    return out


def _norm(text):
    return re.sub(r"\s+", " ", text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"'))


def rules_problems(text, official=None, brief=None):
    """docs/jam-rules.md has no [VERIFY] left and every quoted-rule row cites an Official Rules section (§n); the
    pinned Official Rules text still says each RULES_FACTS phrase; the Clock deadline is the rules' end (section 4)."""
    out = []
    n = len(re.findall(r"\[VERIFY", text))
    if n:
        out.append(f"{JAM_RULES} has {n} [VERIFY] tag(s); resolve each with a quote from {OFFICIAL_RULES}")
    sec = md_section(text, "Quoted rules") or ""
    for ln in sec.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and len(cells) >= 3 and cells[0] not in ("Rule",) and not set(cells[0]) <= set("-: "):
            if not re.search(r"§\s?\d|Official Rules: silent", ln):
                out.append(f"{JAM_RULES} row '{cells[0]}' cites no Official Rules section (§n, or 'Official Rules: silent')")
    if official is not None:
        body = _norm(official)
        for secno, phrase in RULES_FACTS:
            if _norm(phrase) not in body:
                out.append(f"{OFFICIAL_RULES} no longer says §{secno} \"{phrase[:50]}...\": a new rules version "
                           "changes the checks; a human updates submission_check.py and docs/jam-rules.md")
    if brief is not None:
        m = re.search(r"^Submission deadline:\s*(\S+)", brief, re.M)
        try:
            got = dt.datetime.fromisoformat(m.group(1)) if m else None
        except ValueError:
            got = None
        if got is None or got != JAM_END:
            out.append(f"{BRIEF} Clock 'Submission deadline' is {m.group(1) if m else 'missing'}; Official Rules §4 "
                       f"ends the contest at {JAM_END.isoformat()} (8:59 PM ET)")
    return out


CONTENT_SIGNOFF = {"teen": "yes", "trademarks": "ue-logo-only", "original": "yes", "extra-software": "none",
                   "english": "yes"}   # Official Rules 8, 15(d), 7(d)(e), 7(f), 7(i)


def signoff_problems(line):
    if re.match(r"\s*CONTENT\s", line or ""):
        kv = dict(re.findall(r"([\w-]+)=(\S+)", line))
        out = [f"{k}={kv.get(k)}, need {k}={v}" for k, v in CONTENT_SIGNOFF.items() if kv.get(k) != v]
        if not kv.get("by") or kv["by"].strip("<>").lower() in ("name", "tbd", "agent", "claude"):
            out.append("by=<the human who checked> missing")
        return out
    if not re.match(r"\s*VIDEO\s", line or ""):
        return ["not a 'VIDEO ...' or 'CONTENT ...' sign-off line"]
    kv = dict(re.findall(r"([\w-]+)=(\S+)", line))
    out = [f"{k}={kv.get(k)}, need {k}={v}" for k, v in VIDEO_SIGNOFF.items() if kv.get(k) != v]
    try:
        if float(kv.get("gameplay-by", "x").rstrip("s")) > GAMEPLAY_BY_MAX_S:
            out.append(f"gameplay-by={kv['gameplay-by']}, need {GAMEPLAY_BY_MAX_S:g} s or less")
    except ValueError:
        out.append("gameplay-by=<seconds> missing")
    if not kv.get("by"):
        out.append("by=<name> missing")
    return out


def parse_now(v):
    if not v:
        return dt.datetime.now(dt.timezone.utc)
    t = dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("--now needs a UTC offset")
    return t


# ---------------- pre-jam ----------------
def prejam_problems(log_lines, declaration_text, start=JAM_START):
    """log_lines: '<sha>\\t<committer ISO date>' for commits touching game paths."""
    out = []
    for ln in log_lines:
        parts = ln.strip().split("\t")
        if len(parts) < 2:
            continue
        sha, when = parts[0], dt.datetime.fromisoformat(parts[1].replace("Z", "+00:00"))
        if when < start and sha[:7] not in declaration_text:
            out.append(f"commit {sha[:7]} ({parts[1]}) touched game files before the jam start and is not"
                       f" listed in {DECLARATION}")
    return out


def declared_patterns(text):
    """Backticked patterns in the first column of every table row."""
    pats = []
    for ln in text.splitlines():
        if ln.strip().startswith("|"):
            first = ln.strip().strip("|").split("|")[0]
            pats += re.findall(r"`([^`]+)`", first)
    return pats


def declaration_problems(paths, text):
    pats = declared_patterns(text)
    if not pats:
        return [f"{DECLARATION} has no backticked patterns in its tables"]
    return [f"{p}: exists before the jam and matches no line in {DECLARATION}"
            for p in paths if not any(fnmatch.fnmatchcase(p, pat) for pat in pats)]


# ---------------- CLI ----------------
def report(problems, ok_msg):
    for p in problems:
        print("FAIL: " + p)
    if problems:
        print(f"submission_check: {len(problems)} problem(s)")
        return 1
    print("PASS: " + ok_msg)
    return 0


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)


PRACTICE_BLOCKED = ("page", "signoff", "prejam", "declaration")


def practice_blocked(a, root=None):
    """What practice mode (tools/practice.py) blocks for these arguments, or None: every check that certifies the
    entry (the final zip, page, video, credits, the human sign-off, the declaration). Gate zips G1-G3 still run."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import practice
    if not practice.is_practice(root or ROOT):
        return None
    if a.cmd in PRACTICE_BLOCKED:
        return f"submission_check {a.cmd}"
    if a.cmd == "zip" and getattr(a, "gate", None) in (None, "G4"):
        return "the submission zip check (zip without --gate G1-G3)"
    if (a.cmd == "files" and a.final) or (a.cmd == "devlog" and a.published) or (a.cmd == "footage" and a.final):
        return f"submission_check {a.cmd} (final)"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zip")
    z.add_argument("path")
    z.add_argument("--team")
    z.add_argument("--game")
    z.add_argument("--commit")
    z.add_argument("--gate", choices=("G1", "G2", "G3", "G4"))
    sub.add_parser("video").add_argument("path")
    sub.add_parser("loudness").add_argument("path")
    sub.add_parser("page").add_argument("dir", nargs="?", default=os.path.join(ROOT, PAGE_DIR))
    sub.add_parser("credits")
    d = sub.add_parser("devlog")
    d.add_argument("--day", type=int, required=True)
    d.add_argument("--published", action="store_true")
    pj = sub.add_parser("prejam")
    pj.add_argument("--log-file", help="'sha<TAB>ISO date' lines instead of running git")
    dc = sub.add_parser("declaration")
    dc.add_argument("--ref", default="HEAD")
    th = sub.add_parser("theme")
    th.add_argument("--now")
    th.add_argument("--brief", default=os.path.join(ROOT, BRIEF))
    sub.add_parser("capture").add_argument("log")
    ft = sub.add_parser("footage")
    ft.add_argument("--day", type=int, help="last day to check; --final alone means the whole jam (Day 4)")
    ft.add_argument("--final", action="store_true")
    dy = sub.add_parser("daily")
    dy.add_argument("--day", type=int, required=True)
    dy.add_argument("--now")
    sub.add_parser("rules")
    sub.add_parser("files").add_argument("--final", action="store_true")
    sub.add_parser("signoff").add_argument("line")
    sub.add_parser("wiring")
    sub.add_parser("assets")
    sub.add_parser("art")
    sub.add_parser("english")
    sub.add_parser("butler").add_argument("line")
    a = ap.parse_args(argv)

    what = practice_blocked(a)
    if what:
        import practice
        print("FAIL: " + practice.blocked(what, ROOT))
        print("submission_check: 1 problem(s)")
        return 1
    try:
        if a.cmd == "theme":
            text = read(a.brief) if os.path.isfile(a.brief) else ""
            return report(theme_problems(text, parse_now(a.now)), "theme lines (or not due yet)")
        if a.cmd == "daily":
            return report(daily_problems(a.day, parse_now(a.now)), f"day {a.day}: devlog, footage, theme")
    except ValueError as e:
        print(f"NOT RUN: {e}")
        return 2
    if a.cmd == "capture":
        if not os.path.isfile(a.log):
            print(f"NOT RUN: {a.log} not found")
            return 2
        return report(capture_problems(read(a.log)), "capture mode hides HUD, debug text and cursor")
    if a.cmd == "footage":
        if a.day is None and not a.final:   # final-9 A M10: card 0.24 runs `footage --final` as written
            print("NOT RUN: footage needs --day N, or --final for the whole jam")
            return 2
        a.day = JAM_LAST_DAY if a.day is None else a.day
        p = os.path.join(ROOT, FOOTAGE)
        return report(footage_problems(read(p) if os.path.isfile(p) else "", a.day, a.final), f"footage days {FOOTAGE_FROM_DAY}-{a.day}")
    if a.cmd == "rules":
        return report(rules_problems(read(os.path.join(ROOT, JAM_RULES)), read(os.path.join(ROOT, OFFICIAL_RULES)),
                                     read(os.path.join(ROOT, BRIEF))),
                      "jam rules cite the Official Rules, no [VERIFY] left, deadline = §4")
    if a.cmd == "files":
        def opt(rel):
            p = os.path.join(ROOT, rel)
            return read(p) if os.path.isfile(p) else None
        return report(files_problems(opt(README_TXT), opt(LICENSE_TXT), a.final), "README.txt and LICENSE.txt")
    if a.cmd == "signoff":
        return report(signoff_problems(a.line), "VIDEO sign-off line")
    if a.cmd == "assets":
        cp = os.path.join(ROOT, CREDITS)
        import practice
        start = None if practice.is_practice(ROOT) else JAM_START   # practice repo: D39 lifted (tools/practice.py)
        return report(assets_problems(read(os.path.join(ROOT, PROVENANCE)), read(cp) if os.path.isfile(cp) else "",
                                      start=start) + art_loop_problems(ROOT),
                      "no pre-jam game asset unless sourced; no reference art shipped (Official Rules 7(h)); every "
                      "shipped image passed the art loop")
    if a.cmd == "art":
        return report(art_loop_problems(ROOT), "every shipped image passed the art loop (reference and quality bar)")
    if a.cmd == "english":
        return report(english_problems([(p, read(os.path.join(ROOT, p))) for p in english_files()]),
                      "submission text and string tables are English (Official Rules 7(i))")
    if a.cmd == "wiring":
        return report(wiring_problems(), "submission duties are wired into cards, roles and check_card.py")
    if a.cmd == "butler":
        return report(butler_problems(a.line), "BUTLER line")

    if a.cmd == "zip":
        if not os.path.isfile(a.path):
            print(f"NOT RUN: {a.path} not found")
            return 2
        # The PASS line names the zip's commit and sha256 so a gate record ties it to its Build and its upload (B H7)
        rc = report(zip_problems(a.path, a.team, a.game, a.commit, gate=a.gate),
                    f"{a.path} config=Development platform=Win64 commit={zip_commit(a.path)} "   # the path: --gate-record re-hashes it (final-9 B H4)
                    f"sha256={sha256(a.path)}")
        print(f"zip={os.path.basename(a.path)} bytes={os.path.getsize(a.path)} sha256={sha256(a.path)}")
        return rc
    if a.cmd in ("video", "loudness"):
        tool = "ffprobe" if a.cmd == "video" else "ffmpeg"
        if not shutil.which(tool) or not os.path.isfile(a.path):
            print(f"NOT RUN: needs {tool} on PATH and an existing file")
            return 2
        if a.cmd == "video":
            try:
                probe = probe_video(a.path)
            except (OSError, ValueError) as e:
                print(f"FAIL: {e}")
                return 1
            return report(video_problems(probe), f"{a.path} length and size")
        lufs = measure_lufs(a.path)
        print(f"lufs={lufs}")
        return report(loudness_problems(lufs), f"{a.path} loudness")
    if a.cmd == "page":
        itch = read(os.path.join(ROOT, ITCH_PAGE)) if os.path.isfile(os.path.join(ROOT, ITCH_PAGE)) else ""
        dp = os.path.join(ROOT, DECISIONS)
        return report(page_problems(a.dir, itch, read(dp) if os.path.isfile(dp) else ""),
                      "itch page images, fields, team, credits and controls row")
    if a.cmd == "credits":
        csv_text = read(os.path.join(ROOT, PROVENANCE))
        credits_text = read(os.path.join(ROOT, CREDITS)) if os.path.isfile(os.path.join(ROOT, CREDITS)) else ""
        return report(credits_problems(csv_text, credits_text, font_files(ROOT), art_files(ROOT)),
                      "credits, font and art provenance")
    if a.cmd == "devlog":
        return report(devlog_problems(read(os.path.join(ROOT, DEVLOG)), a.day, a.published), f"devlog days 1-{a.day}")
    decl = read(os.path.join(ROOT, DECLARATION))
    if a.cmd == "prejam":
        if a.log_file:
            lines = read(a.log_file).splitlines()
        else:
            p = git("log", "--format=%H%x09%cI", "--", ":(top)Source", ":(top)Content", ":(top)Config",
                    ":(top,glob)*.uproject")
            if p.returncode != 0:
                print("NOT RUN: git log failed: " + p.stderr.strip())
                return 2
            lines = p.stdout.splitlines()
        return report(prejam_problems(lines, decl), f"no undeclared game commits before {JAM_START.isoformat()}")
    p = git("ls-tree", "-r", "--name-only", a.ref)
    if p.returncode != 0:
        print(f"NOT RUN: git ls-tree {a.ref} failed: " + p.stderr.strip())
        return 2
    return report(declaration_problems(p.stdout.splitlines(), decl), f"every file at {a.ref} is declared")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Producer's task-card linter. A card with an empty or vague field is not ready (AGENTS.md section 4).

Accepts both shapes a card comes in:
  template   "Field: value" lines as in pipeline/templates/task-card.md (fields are read from it)
  issue form "### <label>" sections as GitHub renders .github/ISSUE_TEMPLATE/task.yml
             (the card ID then comes from the issue title, "[UE-012] ...", passed with --title)

Checks:
  field     every field present, not empty, not a template placeholder (<...>, UE-000, TBD, _No response_)
  id        ID looks like UE-<number> (UE-000 is the template; Day-0 cards are UE-0.<n>, e.g. UE-0.4a)
  mvp       MVP item is a number in the docs/jam-brief.md MVP list, "Day 0", or "Stretch: <item from the brief>";
            a numbered item whose brief line names feature IDs needs one of them in Features
  owner     Owner role is in the AGENTS.md roles table: an agent role, never a person (agents own all the work; a
            person's part is a `HUMAN <kind>:` Done-when line, pipeline/human-checkpoints.md "Checkpoint kinds").
            Reviewer role is an agent role too (a fresh session reviews; no "Human only" reviewer); owner and
            reviewer differ
  lane      File lane names at least one path or glob; "none", "everything", "all" and the whole repo
            are rejected. "GitHub only" is allowed for cards that write no files (Day-0 0.1, 0.11).
            On issue-form cards the lane field holds three lines, each read on its own:
            `Lane: ...`, `Do not touch: ...`, `Locks: ...`
  done      Done when has at least one line with a measurable value: a number with a unit or comparison,
            an automation test name UmbrellaElla.<Area>.<Behavior>, SMOKE_OK, "marked DECIDED", or a
            command result ("exits 0", "prints PASS", "lists 8") on a line that names the command
            (`backticks`, tools/..., *.py/*.sh/*.ps1, gh/git/grep). A line that says "works" /
            "looks good" / "feels right" needs one of these; a hedge ("eventually", "should") always fails
  GDD ref   tooling cards write "none" ("n/a" is read as an unfilled placeholder)
  gdd       GDD revision names a snapshot in docs/gdd/ (GDD-<rev>.md). A card on an older revision than docs/gdd/CURRENT
            fails only if one of its Features changed between the two (tools/gdd_impact.py); other cards stay valid
  features  Features lists IDs from docs/feature-manifest.json, or "none" (tooling cards; a numeric MVP card needs IDs).
            Every ID must be implementation_authorized, unless the card says "Hook only" (interface + flag at its
            manifest default, no behavior) and the ID is OPEN or PROPOSED
  budget    Budget reads "<n> min agent + <n> min human"; agent time over 120 min or human time over
            60 min means split the card
  usedby    Used by is "none ..." or names the follow-up card (#<n> or UE-<n>)
  cap       a count of flipbook frames above the total cap in docs/jam-brief.md needs a decision row
            (D<n> / D-new-...) on the card
  story     a card whose Owner role is Story names, in Done when, `tools/story_check.py` with its PASS and the final
            `STORY_CRITIC: PASS` line of a separate critic session (pipeline/roles/story.md): no story card closes
            on the builder's word alone; tools/check_pr.py rule story asks for the same lines on its PR
  spike     a card titled 'Spike: ...' / 'Spike D<n>: ...', or with a 'Decision row:' line, needs
            'Decision row: D<n>', 'Decides it:' with an if/then, and 'Time box:' of at most SPIKE_MAX_MIN
            (pipeline/templates/spike-card.md)

Blocked card:
  --blocked-by C  prints only the cards that wait on card C, directly or transitively, one per line, and nothing
                  else: Day-0 rows whose After lists it, plus (with --issues FILE, gh issue list --json
                  number,title,body) filed cards with an 'After: <ids>' line naming it or named in its Used by.
                  Every other card keeps working. Exit 0; 2 = unknown card

Board and plan checks (each prints problems and exits 1 on any):
  --clock         docs/jam-brief.md Clock: deadline, gate times G1-G4, hard stop and card 0.9 cutoff are set;
                  gates in order; G4 at least MARGIN_H hours and G3 at least TUNE_DAY_H hours before the
                  deadline. With gate tags (gate-G<n>), a gate closed or still open more than CUT_AFTER_H
                  hours past its time prints CUT FIRES. --uploaded <ISO>: the jam-page time of the final
                  upload is at least MARGIN_H hours before the deadline. From the Card 0.9 cutoff on,
                  .github/workflows/clock.yml must exist and match pipeline/templates/clock-workflow.yml
                  (Day-0 card 0.16, D-new-clock-install)
  --people        People and Team hours tables: no TBD, no "(proposed)", Confirmed = yes or default (agent), hours as 8/8/8/6;
                  every teammate holds a People seat, nobody holds more than BLOCKER_SEATS_MAX BLOCKER seats;
                  away windows are 'none' or 'D<n> HH:MM-HH:MM', comma-separated; more than TEAM_MAX
                  Team hours rows, or fewer than CPP_MIN rows with UE C++ = y, prints a WARN line (exit code
                  unchanged; D-new-team-size, D-new-cpp-team)
  --hours --day N open cards (gh issue list JSON on stdin): human budget minutes per person vs RESERVE of
                  that person's Team hours for day N, minus their away windows on day N; an Asset
                  Specialist card's Used by card must be open
                  with a Budget, so the integration time is counted too
  --lanes         open cards (gh issue list JSON on stdin): no two share a lane glob, a .umap or a lock
                  (test-map.md, decisions.md and jam-brief.md are row-scoped and not counted);
                  no Stretch card while a numeric MVP card is open (no override; stretch waits for every MVP card)
  --status        Jam tracker (gh issue view --json body,comments on stdin): a status line with every
                  field of the producer.md format was posted in the last STATUS_MAX_H hours; 'Next gate' is
                  on track / at risk / will miss plus a reason; 'will miss' needs a 'Cut proposed: <item>'
                  comment since the last gate time; 'Absences next 12h' is 'none' or a name; once
                  the Clock G1 time has passed, a comment holds the itch test upload (link + sha256=<64 hex>);
                  within RETRO_LEAD_H of a gate, both retro questions are on the tracker; --tracker runs too;
                  and submission_check.status_hook (devlog, footage and theme for the day just ended)
  --tracker       tracker issue body: the MVP table (pipeline/templates/tracker-table.md) has one row per MVP
                  item, a status from TRACKER_STATUS, a sha for 'in build'/'passed', a playtest for 'passed'
  --gate-record   tracker comments: the newest 'Gate: G<n>' comment has every pipeline/templates/gate-record.md
                  line filled, and Risks has '<n> fired yes/no' per Top risks row (a yes names an owner);
                  a G1 record also needs a BUTLER line that passes submission_check.butler_problems;
                  a G4 record also needs 'Final upload: <ISO>' at least MARGIN_H hours before the deadline
                  and 'Baked preset: T-nn | bake_preset check: PASS preset=T-nn ...' (D-new-workbench-debug).
                  In a practice repo (tools/practice.py) a G4 record always fails.
                  Machine records (final-9 B H4, H5): the Repeat boots line is a line of the record file, the
                  PLAYTHROUGH line is re-checked from it (from G2 the UIFLOW line for the Build commit too: quits,
                  mouse in menus), the zip is on disk with that sha256, and 'launched: yes'
                  needs the record's LAUNCH line (Win64 smoke of that zip) whose SMOKE_EFFECTIVE passes on the
                  Build commit (complete at G4). Run it on the packaging machine, or pass --records FILE (repeat)
  --queue         cards in review (gh issue list --label review JSON on stdin): no Human has more than
                  QUEUE_MAX. Prints the count per human for the status line
  --overrun       cards in doing (gh issue list --label doing JSON on stdin): time with the doing label
                  (from each issue's timeline, fetched with gh api) vs agent + human Budget. Prints
                  OVER BUDGET past the budget and fails with OVERRUN #n +NN min past OVERRUN_MIN over it.
                  An issue with no Budget (a bug) is timed against 0 min
  --hardstop      commits on main (origin/main if present) in the last 24 h (or --since) whose time, in the
                  Clock's time zone (the deadline's UTC offset), falls inside the Hard stop window

Usage:
  python3 tools/check_card.py card.md [--title "[UE-012] ..."]
  python3 tools/check_card.py --event          # GitHub Actions issue event ($GITHUB_EVENT_PATH)
  gh issue view 12 --json title,body | python3 tools/check_card.py --json-stdin
  python3 tools/check_card.py --clock | --people
  gh issue list --label task --state open --json number,title,body --limit 200 | python3 tools/check_card.py --lanes
  gh issue list --label task --state open --json number,title,body --limit 200 | python3 tools/check_card.py --hours --day 2
  gh issue view <tracker #> --json body,comments | python3 tools/check_card.py --status | --tracker | --gate-record
  gh issue list --label review --state open --json number,title,body | python3 tools/check_card.py --queue
  gh issue list --label doing --state open --json number,title,body | python3 tools/check_card.py --overrun
  python3 tools/check_card.py --hardstop [--since 2026-11-14T08:00-05:00]
  python3 tools/check_card.py --clock --uploaded 2026-11-16T13:05-05:00
  python3 tools/check_card.py --blocked-by 0.3 [--issues open.json]   # one line per card that waits on 0.3
  gh issue list --label needs-human --state open --json number,title,labels,comments | python3 tools/check_card.py --needs-human
                  the human queue (pipeline/human-checkpoints.md): one line per labelled issue; exit 1 if one has no
                  `NEEDS HUMAN: <who/role> <what> <link> <YYYY-MM-DDTHH:MMZ>` comment. An ask no human answered in 2 h
                  ends `GRACE EXPIRED -> <role>` (the Producer's hourly sweep); a human-only kind ends `HUMAN ONLY`
Exit 0 = ready, 1 = problems, 2 = usage/input error.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORM_LABELS = [  # issue-form label prefix -> template fields it carries
    ("MVP item", ["MVP item"]),
    ("GDD ref", ["GDD ref"]),
    ("GDD revision", ["GDD revision"]),
    ("Features", ["Features"]),
    ("Player outcome", ["Player outcome"]),
    ("Owner role", ["Owner role"]),
    ("Reviewer role", ["Reviewer role"]),
    ("Human", ["Human"]),
    ("Inputs and outputs", ["Inputs", "Outputs"]),
    ("Context", ["Context"]),
    ("File lane", ["File lane", "Do not touch", "Binary locks"]),
    ("Out of scope", ["Out of scope"]),
    ("Used by", ["Used by"]),
    ("Needs", ["Needs"]),
    ("Done when", ["Done when"]),
    ("Budget and cut tier", ["Budget", "Cut tier"]),
    ("Unknowns", ["Unknowns"]),
]

# Optional form fields: read when present, never required (an empty one is "_No response_").
OPTIONAL_FORM_LABELS = [("After", ["After"])]

TEST_NAME = re.compile(r"\bUmbrellaElla\.[A-Z]\w*\.[A-Z]\w*")
NUMERIC = re.compile(
    r"(?:[<>=≤≥]=?|±|\bwithin|\bat (?:least|most)|\bunder|\bover|\bbelow|\babove)\s*-?\d"
    r"|-?\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?\s*)?(?:px|ms|s\b|sec|seconds?|min(?:utes?)?\b|fps|%|×|x\b|frames?|hp\b|uu\b|cm\b|hz\b|db\b)"
    r"|\bSMOKE_OK\b|\bΔE\b|\bdelta[_ ]?e\b|\bmarked DECIDED\b"
    r"|\bfailed=0\b|\b0 (?:errors?|warnings?|failures?|problems?)\b",
    re.IGNORECASE)
# A command result counts only on a line that names the command someone re-runs.
RESULT = re.compile(r"\bexits?\s+(?:with\s+)?(?:code\s+)?0\b|\bexit code 0\b"
                    r"|\b(?:prints?|shows?|lists?|reports?|returns?)\s+(?:\d+\b|PASS\b|FAIL\b|OK\b)|\bPASS\b|\bFAIL\b",
                    re.IGNORECASE)
COMMAND = re.compile(r"`[^`]+`|\btools/[\w./-]+|\b[\w-]+\.(?:py|sh|ps1)\b|\b(?:gh|git|grep|python3?)\s+[\w-]")
VAGUE = re.compile(
    r"\b(?:works?|working|functional|looks? (?:good|right|nice|fine|ok|okay|better|great)"
    r"|feels? (?:right|good|nice|better|fun|great)|is fine|properly|correctly|as expected|polished|is done)\b",
    re.IGNORECASE)
HEDGE = re.compile(r"\b(?:eventually|somehow|mostly|usually|sometimes|roughly|basically|ideally|hopefully"
                   r"|should|more or less|if possible)\b", re.IGNORECASE)
NO_LANE = re.compile(r"[`'\"\s]*(?:none|nothing|n/?a|everything|all|any|anything|whole repo|the (?:whole )?repo"
                     r"|all files|wherever needed|as needed)[`'\".\s]*", re.IGNORECASE)
NO_FILES_LANE = re.compile(r"\s*GitHub only\b(?:\s*\(.*\))?[.\s]*", re.IGNORECASE)
LANE_LINE = re.compile(r"^\s*[-*]?\s*(Lane|File lane|Do not touch|Locks|Binary locks)\s*:\s*(.*)$", re.IGNORECASE)
LANE_KEYS = {"lane": "File lane", "file lane": "File lane", "do not touch": "Do not touch",
             "locks": "Binary locks", "binary locks": "Binary locks"}


def measurable(line):
    return bool(TEST_NAME.search(line) or NUMERIC.search(line) or (RESULT.search(line) and COMMAND.search(line)))


def split_lane_field(value):
    """Issue-form lane field -> {File lane, Do not touch, Binary locks}, each from its own line."""
    out, cur = {}, None
    for line in value.splitlines():
        m = LANE_LINE.match(line)
        if m:
            cur = LANE_KEYS[m.group(1).lower()]
            out[cur] = m.group(2).strip()
        elif cur and line.strip():
            out[cur] = (out[cur] + "\n" + line.strip()).strip()
    return out
BUDGET = re.compile(r"(\d+)\s*min(?:utes?)?\s+agent\b[^+\n]*\+\s*(\d+)\s*min(?:utes?)?\s+human\b", re.I)
AGENT_MAX_MIN = 120
HUMAN_MAX_MIN = 60  # human minutes per card; over it, split the card (D-new-human-cap)
CARD_REF = re.compile(r"#\d+|\bUE-\d+(?:\.\d+[a-z]?)?\b")
DECISION_REF = re.compile(r"\bD(?:EC-\d{2}|-new-[\w-]+|\d+)\b")
CAP_COUNT = re.compile(r"\b(\d+)\s+((?:flipbook|animation|sprite) frames?)\b", re.I)
SPIKE_TITLE = re.compile(r"^\s*Spike\b(?:\s+D(?:-new-[\w-]+|\d+))?\s*:", re.I)
SPIKE_LINE = re.compile(r"^\s*[-*]?\s*(Decision row|Decides it|Time box)\s*:\s*(.*)$", re.I | re.M)
SPIKE_IF = re.compile(r"\bif\b.+\b(?:pick|choose|keep|use|go with|then)\b", re.I)
SPIKE_BOX = re.compile(r"^(\d+(?:\.\d+)?)\s*(min(?:utes?)?|h(?:ours?)?)\b", re.I)
SPIKE_MAX_MIN = 60  # a spike stops at its time box; at most one hour (spike-card.md, D1, D3)
PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>|\bUE-0+\b(?!\.\d)|\bUE-_+|_No response_|^\s*(?:tbd|todo|\?+|-|n/?a)\s*$",
                         re.IGNORECASE | re.M)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def template_fields(root):
    text = read(os.path.join(root, "pipeline", "templates", "task-card.md"))
    block = re.search(r"```\n(.*?)```", text, re.S).group(1)
    return re.findall(r"^([A-Z][A-Za-z ]+?):", block, re.M)


def roles(root):
    text = read(os.path.join(root, "AGENTS.md"))
    sec = text.split("## 3. Roles", 1)[1].split("\n## ", 1)[0]
    out = []
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] not in ("Role", "") and not set(cells[0]) <= set("-: "):
            out.append(cells[0])
    return out


def brief(root):
    text = read(os.path.join(root, "docs", "jam-brief.md"))
    mvp_sec = re.search(r"^## MVP.*?$(.*?)^## ", text, re.S | re.M).group(1)
    numbers = {int(n) for n in re.findall(r"^(\d+)\.\s", mvp_sec, re.M)}
    stretch = []
    m = re.search(r"^Stretch.*?:\s*\n(.+?)$", mvp_sec, re.M)
    if m:
        stretch = [s.strip(" .").lower() for s in re.split(r"→|->", m.group(1)) if s.strip(" .")]
    return numbers, stretch


ID_RANGE = re.compile(r"(?<![\w-])([A-Z]+)-(\d{2})\.\.\1-(\d{2})(?![\w-])")


def line_features(line):
    """Feature IDs a brief line names. GDD SH1.0 has 204 Rule IDs, so a line may name a range: OWL-06..OWL-35."""
    import gdd_impact
    ids = set(gdd_impact.FEATURE_ID.findall(line))
    for p, a, b in ID_RANGE.findall(line):
        ids |= {f"{p}-{n:02d}" for n in range(int(a), int(b) + 1)}
    return ids


def mvp_features(root):
    """{MVP number: feature IDs its docs/jam-brief.md line names}. Lines that name none map to an empty set."""
    text = read(os.path.join(root, "docs", "jam-brief.md"))
    mvp_sec = re.search(r"^## MVP.*?$(.*?)^## ", text, re.S | re.M).group(1)
    return {int(n): line_features(line) for n, line in re.findall(r"^(\d+)\.\s(.*)$", mvp_sec, re.M)}


GATE_TAG = re.compile(r"\[(G[1-4])\]\s*$")


def gate_mvp(root=None, text=None):
    """{gate: MVP numbers due at it} from the `[G<n>]` tag that ends each docs/jam-brief.md MVP line (D-new-sh10-g1).
    An item is due at its own gate and re-checked at every later gate; an untagged line is due at G4."""
    if text is None:
        try:
            text = read(os.path.join(root or ROOT, "docs", "jam-brief.md"))
        except OSError:
            return {}
    m = re.search(r"^## MVP.*?$(.*?)^## ", text, re.S | re.M)
    if not m:
        return {}
    due = {}
    for n, line in re.findall(r"^(\d+)\.\s(.*)$", m.group(1), re.M):
        t = GATE_TAG.search(line)
        due[int(n)] = int(t.group(1)[1]) if t else 4
    return {f"G{g}": sorted(n for n, d in due.items() if d <= g) for g in (1, 2, 3, 4)}


def cap_key(what):
    return "frames"


def content_caps(root):
    """'Content caps: flipbook frames 60 in total.' (the old platformer caps are gone with the old design)"""
    try:
        text = read(os.path.join(root, "docs", "jam-brief.md"))
    except OSError:
        return {}
    m = re.search(r"^Content caps\b.*$", text, re.M)
    if not m:
        return {}
    caps = {}
    for what, n in re.findall(r"(flipbook frames)\s+(\d+)", m.group(0), re.I):
        caps[cap_key(what)] = int(n)
    return caps


def parse(body, fields, title=None):
    """Return {field: value} from either card shape."""
    if re.search(r"^###\s+\S", body, re.M):
        out = {}
        parts = re.split(r"^###\s+(.+?)\s*$", body, flags=re.M)
        for label, value in zip(parts[1::2], parts[2::2]):
            for prefix, names in FORM_LABELS + OPTIONAL_FORM_LABELS:
                if label.startswith(prefix):
                    if prefix == "File lane":
                        # One textarea carries three fields; read each line on its own, so the
                        # always-present Do-not-touch path can't make an empty lane look filled.
                        out.update(split_lane_field(value.strip()))
                        break
                    for n in names:
                        out[n] = value.strip()
                    break
        if title is not None:
            m = re.match(r"\s*\[([^\]]*)\]\s*(.*)$", title)
            out["ID"] = m.group(1).strip() if m else ""
            out["Title"] = (m.group(2) if m else title).strip()
        required = ["ID", "Title"] if title is not None else []
        required += [n for _, names in FORM_LABELS for n in names]
        return out, required
    out, cur = {}, None
    names = "|".join(re.escape(f) for f in fields)
    for line in body.splitlines():
        m = re.match(r"^(" + names + r"):\s*(.*)$", line)
        if m:
            cur = m.group(1)
            out[cur] = m.group(2).strip()
        elif cur and (line.startswith((" ", "\t")) or not line.strip()):
            out[cur] = (out[cur] + "\n" + line.strip()).strip()
        else:
            cur = None
    return out, list(fields)


MANIFEST_PATH = None  # tests point this at a signed-off fixture manifest; None = <root>/docs/feature-manifest.json
HOOK_OK = {"OPEN", "PROPOSED"}


def feature_problems(card, mvp, root=ROOT, manifest=None):
    """GDD revision and Features fields against the snapshot folder and the feature manifest."""
    import gdd_impact
    rev = (card.get("GDD revision") or "").strip()
    feats = (card.get("Features") or "").strip()
    out = []
    path = manifest or MANIFEST_PATH or os.path.join(root, "docs", "feature-manifest.json")
    try:
        with open(path, encoding="utf-8") as fh:
            man = json.load(fh)
        with open(os.path.join(root, "docs", "gdd", "CURRENT"), encoding="utf-8") as fh:
            current = fh.read().strip()
    except (OSError, ValueError):
        return []
    recs = {f.get("feature_id"): f for f in man.get("features", [])}
    ids = sorted(set(gdd_impact.FEATURE_ID.findall(feats)))
    snap = None
    if rev and not PLACEHOLDER.search(rev):
        name = re.sub(r"(?i)^GDD-|\.md$", "", rev.split()[0])
        snap = os.path.join(root, "docs", "gdd", f"GDD-{name}.md")
        if not os.path.isfile(snap):
            out.append(("gdd", f"GDD revision '{rev}' has no snapshot docs/gdd/GDD-{name}.md (current: {current})"))
            snap = None
    if feats and not PLACEHOLDER.search(feats):
        if re.fullmatch(r"none\b.*", feats, re.S | re.I):
            if re.fullmatch(r"(?:MVP\s*)?#?\d+\b.*", mvp or "", re.S):
                out.append(("features", "an MVP card names its feature IDs from docs/feature-manifest.json, not 'none'"))
        elif not ids:
            out.append(("features", f"Features '{feats[:40]}' names no feature ID (e.g. UMB-03) and is not 'none'"))
        hook = re.search(r"\bhook only\b", feats, re.I)
        p0 = sorted(fid for fid in ids if (recs.get(fid) or {}).get("status") == "APPROVED_P0")
        # dry run B H5 / A M1: an APPROVED_P0 ID is always built in full on an MVP card, never Hook only or Stretch
        if p0 and hook:
            out.append(("features", f"{', '.join(p0)} is APPROVED_P0: build it in full; 'Hook only' is only for "
                                    "OPEN or PROPOSED IDs"))
        if p0 and re.match(r"\s*Stretch\b", mvp or "", re.I):
            out.append(("mvp", f"{', '.join(p0)} is APPROVED_P0, so this is an MVP card, never Stretch "
                               "(pipeline/day0-cards.md)"))
        if p0 and re.match(r"\s*Day\s*0\b", mvp or "", re.I):   # dry run A M8: Day 0 skips the MVP mapping and D39
            out.append(("mvp", f"{', '.join(p0)} is APPROVED_P0: a feature card names its MVP item, never 'Day 0'"))
        tier = cut_tier(card.get("Cut tier") or "")
        if p0 and tier != "MVP":   # dry run B H2: exact token, whichever card shape (form: "<budget>, <tier>")
            out.append(("mvp", f"Cut tier '{tier}' on an APPROVED_P0 card ({', '.join(p0)}): "
                               "P0 is never on the cut list; the tier is exactly 'MVP'"))
        for fid in ids:
            r = recs.get(fid)
            if r is None:
                out.append(("features", f"{fid} is not in docs/feature-manifest.json"))
            elif not r.get("implementation_authorized"):
                if hook and r.get("status") in HOOK_OK:
                    continue
                why = (" ('Hook only' is allowed only for OPEN or PROPOSED IDs)" if hook else
                       "; build it only after sign-off, or file a 'Hook only' card for an OPEN or PROPOSED ID")
                out.append(("features", f"{fid} is {r.get('status')} and not implementation_authorized{why}"))
    if snap and ids and os.path.basename(snap) != current:
        try:
            d = gdd_impact.diff(gdd_impact.load(snap), gdd_impact.load(os.path.join(root, "docs", "gdd", current)))
        except (OSError, ValueError):
            d = None
        stale = sorted(set(ids) & set(gdd_impact.touched(d))) if d else []
        if stale:
            out.append(("gdd", f"card is on {os.path.basename(snap)} but {', '.join(stale)} changed in {current};"
                               " re-check the card against the current GDD and update GDD revision"))
    return out


STORY_DONE_CHECK = re.compile(r"story_check\.py\b[^\n]*\bPASS\b")
STORY_DONE_CRITIC = re.compile(r"\bSTORY_CRITIC: PASS\b")


def story_card_problems(card):
    """A Story card closes only on the machine check and the blind critic, both pasted (pipeline/roles/story.md)."""
    if not re.match(r"\s*Story\b", card.get("Owner role") or "", re.I):
        return []
    done, out = card.get("Done when") or "", []
    if not STORY_DONE_CHECK.search(done):
        out.append(("story", "a Story card's Done when names `python3 tools/story_check.py` and its PASS (pasted)"))
    if not STORY_DONE_CRITIC.search(done):
        out.append(("story", "a Story card's Done when has the final `STORY_CRITIC: PASS ...` line of a separate critic "
                             "session (pipeline/roles/story.md, quality loop)"))
    return out


def problems(body, root=ROOT, title=None, manifest=None):
    fields = template_fields(root)
    card, required = parse(body, fields, title)
    role_list = roles(root)
    mvp_numbers, stretch = brief(root)
    out = []

    for f in required:
        v = card.get(f)
        if v is None:
            out.append(("field", f"missing field '{f}'"))
        elif not re.search(r"[\w*]", v) or PLACEHOLDER.search(v):
            shown = v.splitlines()[0][:60] if v else ""
            hint = "; tooling cards write 'none'" if f in ("GDD ref", "Player outcome") else ""
            out.append(("field", f"'{f}' is empty or still the template ({shown!r}){hint}"))

    cid = card.get("ID")
    if cid is not None and cid and not re.fullmatch(r"UE-(?!0+\b(?!\.\d))\d+(?:\.\d+[a-z]?)?", cid):
        out.append(("id", f"ID '{cid}' is not UE-<number>"))

    mvp = (card.get("MVP item") or "").strip()
    if mvp:
        m_num = re.fullmatch(r"(?:MVP\s*)?#?(\d+)\b.*", mvp, re.S)
        m_str = re.fullmatch(r"Stretch(?:-\d)?:\s*(.+)", mvp, re.S | re.I)
        if m_num:
            if int(m_num.group(1)) not in mvp_numbers:
                out.append(("mvp", f"MVP item {m_num.group(1)} is not in docs/jam-brief.md (valid: {min(mvp_numbers)}-{max(mvp_numbers)})"))
            else:
                import gdd_impact
                want = mvp_features(root).get(int(m_num.group(1))) or set()
                have = set(gdd_impact.FEATURE_ID.findall(card.get("Features") or ""))
                if want and have and not (want & have):
                    out.append(("mvp", f"MVP item {m_num.group(1)} is {', '.join(sorted(want))} in docs/jam-brief.md, "
                                       f"but Features names {', '.join(sorted(have))}"))
        elif re.fullmatch(r"Day\s*0\b.*", mvp, re.S | re.I):
            pass
        elif m_str:
            name = m_str.group(1).strip().lower()
            if stretch and not any(name in s or s in name for s in stretch):
                out.append(("mvp", f"stretch item '{m_str.group(1).strip()}' is not in the docs/jam-brief.md stretch list"))
        else:
            out.append(("mvp", f"MVP item '{mvp}' must be a number from docs/jam-brief.md, 'Day 0', or 'Stretch: <name>'"))

    def role_of(v, extra):
        v = (v or "").strip()
        for r in role_list + extra:
            if re.fullmatch(re.escape(r) + r"(?:\s*\(.*\))?", v, re.I):
                return r
        return None

    owner = role_of(card.get("Owner role"), [])
    reviewer = role_of(card.get("Reviewer role"), [])
    if card.get("Owner role") and not PLACEHOLDER.search(card["Owner role"]) and owner is None:
        person = role_of(card.get("Owner role"), ["Human", "Human only"])
        out.append(("owner", f"Owner role '{card['Owner role']}' is " + (
            "a person: an agent role owns every card, and the person's part is a `HUMAN <kind>:` Done-when line "
            "(pipeline/human-checkpoints.md)" if person else "not in the AGENTS.md roles table")))
    if card.get("Reviewer role") and not PLACEHOLDER.search(card["Reviewer role"]) and reviewer is None:
        person = re.match(r"\s*Human\b", card["Reviewer role"], re.I)
        out.append(("owner", f"Reviewer role '{card['Reviewer role']}' is " + (
            "a person: a fresh agent session of another role reviews every card (kickoff merges on its approve)"
            if person else "not in the AGENTS.md roles table")))
    if owner and reviewer and owner == reviewer:
        out.append(("owner", f"owner and reviewer are both '{owner}'; the reviewer must be a different role"))

    lane = card.get("File lane") or ""
    if lane and not PLACEHOLDER.search(lane) and NO_FILES_LANE.fullmatch(lane):
        pass  # a card that writes no files (tracker issue, spike filing)
    elif lane and NO_LANE.fullmatch(lane.splitlines()[0]):
        out.append(("lane", f"File lane '{lane.splitlines()[0][:60]}' is not a lane; name the folders this card may write"
                            " (or 'GitHub only' when it writes no files)"))
    elif lane and not PLACEHOLDER.search(lane):
        tokens = re.findall(r"[\w.*-]*(?:/|\*)[\w./*{},-]*|\b[\w-]+\.(?:h|cpp|cs|ini|uproject|umap|uasset|md|json|py|png)\b", lane)
        real = [t for t in tokens if t.strip("/*.") not in ("",) and not re.fullmatch(r"[/*.]+", t)]
        if any(re.fullmatch(r"\*\*(?:/\*)?|/\*\*|\./\*\*|\*", t) for t in tokens):
            out.append(("lane", "File lane covers the whole repo; name the folders this card may write"))
        elif not real:
            out.append(("lane", f"File lane '{lane.splitlines()[0][:60]}' names no path or glob"))

    budget = card.get("Budget") or ""
    if budget and not PLACEHOLDER.search(budget):
        m = BUDGET.search(budget)
        if not m:
            out.append(("budget", f"Budget '{budget.splitlines()[0][:60]}' is not '<n> min agent + <n> min human'"))
        elif int(m.group(1)) > AGENT_MAX_MIN:
            out.append(("budget", f"agent budget {m.group(1)} min is over {AGENT_MAX_MIN} min; split the card"))
        if m and int(m.group(2)) > HUMAN_MAX_MIN:
            out.append(("budget", f"human budget {m.group(2)} min is over {HUMAN_MAX_MIN} min; split the card"
                                  " (D-new-human-cap)"))

    used = (card.get("Used by") or "").strip()
    if used and not PLACEHOLDER.search(used) and not re.match(r"none\b", used, re.I) and not CARD_REF.search(used):
        out.append(("usedby", f"Used by '{used.splitlines()[0][:60]}' names no follow-up card (#<n> or UE-<n>);"
                              " write 'none' if nothing outside this lane reads it"))

    caps = content_caps(root)
    if caps:
        text = "\n".join(card.get(f) or "" for f in ("Title", "Player outcome", "Outputs", "Done when", "Out of scope"))
        if not DECISION_REF.search(text + "\n" + (card.get("Unknowns") or "")):
            for n, what in CAP_COUNT.findall(text):
                key = cap_key(what)
                if key in caps and int(n) > caps[key]:
                    out.append(("cap", f"{n} {what} is over the cap of {caps[key]} in docs/jam-brief.md;"
                                       " cite the decision row that allows it"))

    out += spike_problems(body, card.get("Title") or "")
    out += story_card_problems(card)
    out += mvp_card_problems(card, mvp)
    out += feature_problems(card, mvp, root, manifest)

    done = card.get("Done when") or ""
    if done and not PLACEHOLDER.search(done):
        lines = [re.sub(r"^\s*(?:[-*]\s*)?(?:\[[ xX]\]\s*)?", "", ln).strip() for ln in done.splitlines()]
        lines = [ln for ln in lines if ln]
        if not any(measurable(ln) for ln in lines):
            out.append(("done", "Done when names no measurable value, test (UmbrellaElla.<Area>.<Behavior>) "
                                "or command with its result"))
        elif re.match(r"\s*(?:MVP\s*)?#?\d+\b", mvp or "") and not re.search(r"\bUmbrellaElla(?:\.\w+){2,}", done):
            # dry run A M9 / docs/game-spec.md: a feature card is not ready without its test in Done-when
            out.append(("done", "an MVP feature card names its engine test (UmbrellaElla.<Area>.<Behavior>, "
                                "pipeline/qa/test-map.md) in Done when; a build line alone is not a feature test"))
        for ln in lines:
            if HEDGE.search(ln):
                out.append(("done", f"hedged Done-when line ('{HEDGE.search(ln).group(0)}'); say exactly what is checked: '{ln[:70]}'"))
            elif VAGUE.search(ln) and not measurable(ln):
                out.append(("done", f"vague Done-when line without a number or test: '{ln[:70]}'"))
    return out


def spike_problems(body, title=""):
    """A spike card (title 'Spike: ...' or a 'Decision row:' line) carries the spike-card.md fields."""
    vals = {}
    for k, v in SPIKE_LINE.findall(body):
        vals.setdefault(k.lower(), v.strip())
    if not (SPIKE_TITLE.match(title or "") or "decision row" in vals):
        return []
    out = []
    row = vals.get("decision row", "")
    if not DECISION_REF.fullmatch(row.split()[0].strip(".,") if row.split() else ""):
        out.append(("spike", f"spike card needs 'Decision row: D<n>' (got {row[:30]!r}); pipeline/templates/spike-card.md"))
    dec = vals.get("decides it", "")
    if PLACEHOLDER.search(dec) or not SPIKE_IF.search(dec):
        out.append(("spike", "spike card needs 'Decides it:' written before it runs, as 'if X, pick A; if Y, pick B'"
                             f" (got {dec[:40]!r})"))
    box = SPIKE_BOX.match(vals.get("time box", ""))
    if not box:
        out.append(("spike", f"spike card needs 'Time box: <n> min' (got {vals.get('time box', '')[:30]!r})"))
    else:
        mins = float(box.group(1)) * (60 if box.group(2).lower().startswith("h") else 1)
        if mins > SPIKE_MAX_MIN:
            out.append(("spike", f"spike time box {mins:g} min is over {SPIKE_MAX_MIN} min; split the question"))
    return out


# ---- Board and plan checks (Producer). Each returns a list of problem strings. ----
MARGIN_H = 3        # G4 at least this many hours before the submission deadline (D-new-clock)
TUNE_DAY_H = 20     # G3 at least this many hours before the deadline: the last day is for tuning (D-new-tune-day)
RESERVE = 0.7       # book at most this share of a person's day in human budget (D-new-reserve)
QUEUE_MAX = 3       # cards in review per human before that human's next card may not start (D-new-port-3)
OVERRUN_MIN = 60    # minutes over Budget that fire a cut, split or hide (D-new-overrun)
TEAM_MAX = 4        # more Team hours rows than this prints a warning (D-new-team-size)
CPP_MIN = 2         # fewer teammates than this who built UE C++ before prints a warning (D-new-cpp-team, D3)
BLOCKER_SEATS_MAX = 3  # BLOCKER People seats one person may hold (D-new-team-size)
CUT_AFTER_H = 2     # a gate this many hours late fires the next cut (jam-brief cut list)
STATUS_MAX_H = 12   # a status line at least this often (producer.md cadence)
GATES = ("G1", "G2", "G3", "G4")
CLOCK_KEYS = ("Submission deadline", "Hard stop", "Card 0.9 cutoff")
AWAY = re.compile(r"D([1-4])\s+([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)")
CLOCK_LIVE = ".github/workflows/clock.yml"
CLOCK_TEMPLATE = "pipeline/templates/clock-workflow.yml"
HOURS = re.compile(r"\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?){3}")
LANE_TOKEN = re.compile(r"[\w.*{},-]*(?:/|\*)[\w./*{},-]*|\b[\w-]+\.(?:h|cpp|cs|ini|uproject|umap|uasset|md|json|py|png|csv)\b")


def section(text, heading):
    m = re.search(r"^## " + re.escape(heading) + r".*?$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else None


def table_rows(sec):
    rows = []
    for line in (sec or "").splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                rows.append(cells)
    return rows[1:]  # drop the header row


def parse_time(v):
    """ISO 8601 with a UTC offset, e.g. 2026-11-16T17:00-05:00. None if not that."""
    try:
        t = dt.datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else None


def clock(text):
    """{key: raw value} from the jam-brief Clock section, gates included."""
    sec = section(text, "Clock")
    if sec is None:
        return None
    out = {}
    for key in CLOCK_KEYS:
        m = re.search(r"^" + re.escape(key) + r"[^:\n]*:\s*(.*?)\s*$", sec, re.M)
        if m:
            out[key] = m.group(1)
    for cells in table_rows(sec):
        if cells and cells[0] in GATES and len(cells) > 1:
            out[cells[0]] = cells[1]
    return out


def clock_problems(text, allow_tbd=False):
    c = clock(text)
    if c is None:
        return ["docs/jam-brief.md has no '## Clock' section"]
    out, times = [], {}
    for key in CLOCK_KEYS + GATES:
        v = c.get(key)
        if v is None:
            out.append(f"Clock: '{key}' is missing")
        elif re.match(r"TBD\b", v):
            if not allow_tbd:
                out.append(f"Clock: '{key}' is TBD (card 0.0 sets it)")
        elif key == "Hard stop":
            if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d", v):
                out.append(f"Clock: Hard stop '{v}' is not HH:MM-HH:MM")
        elif parse_time(v) is None:
            out.append(f"Clock: '{key}' = '{v}' is not ISO 8601 with a UTC offset (2026-11-16T17:00-05:00)")
        else:
            times[key] = parse_time(v)
    gates = [g for g in GATES if g in times]
    for a, b in zip(gates, gates[1:]):
        if times[a] >= times[b]:
            out.append(f"Clock: {a} is not before {b}")
    if "G4" in times and "Submission deadline" in times:
        if times["Submission deadline"] - times["G4"] < dt.timedelta(hours=MARGIN_H):
            out.append(f"Clock: G4 is less than {MARGIN_H} h before the submission deadline")
    if "G3" in times and "Submission deadline" in times:
        if times["Submission deadline"] - times["G3"] < dt.timedelta(hours=TUNE_DAY_H):
            out.append(f"Clock: G3 is less than {TUNE_DAY_H} h before the submission deadline;"
                       " the last day is for tuning (D-new-tune-day)")
    if "Card 0.9 cutoff" in times and "G1" in times and times["Card 0.9 cutoff"] >= times["G1"]:
        out.append("Clock: card 0.9 cutoff is not before G1")
    return out


def upload_problems(text, uploaded):
    """uploaded = jam-page time of the final upload. It must be MARGIN_H h before the deadline."""
    deadline = parse_time((clock(text) or {}).get("Submission deadline") or "")
    if deadline is None:
        return ["Clock: Submission deadline is not set; can't check the upload time"]
    left = (deadline - uploaded).total_seconds() / 3600
    if left < MARGIN_H:
        return [f"final upload was {left:.1f} h before the deadline, less than {MARGIN_H} h (D-new-clock)"]
    return []


def clock_install_problems(root, text, now):
    """From the Card 0.9 cutoff on, the scheduled run (reminders, cut trigger, overrun) is installed."""
    cutoff = parse_time((clock(text) or {}).get("Card 0.9 cutoff") or "")
    if cutoff is None or now < cutoff:
        return []
    live = os.path.join(root, CLOCK_LIVE)
    if not os.path.exists(live):
        return [f"{CLOCK_LIVE} is not installed and the card 0.9 cutoff has passed, so nothing runs the gate"
                " reminders or the cut trigger on its own; the human Producer copies"
                f" {CLOCK_TEMPLATE} and sets PIPELINE_CLOCK=on (Day-0 card 0.16, D-new-clock-install)"]
    try:
        same = read(live) == read(os.path.join(root, CLOCK_TEMPLATE))
    except OSError:
        same = False
    return [] if same else [f"{CLOCK_LIVE} differs from {CLOCK_TEMPLATE}; copy the template again (card 0.16)"]


def cut_report(text, closed, now):
    """closed = {gate: time the gate-G<n> tag was made}. Lines saying which gates fire a cut."""
    c = clock(text) or {}
    lines = []
    for g in GATES:
        due = parse_time(c.get(g, "") or "")
        if due is None:
            continue
        end = closed.get(g) or now
        late = (end - due).total_seconds() / 3600
        state = "closed" if g in closed else "open"
        if late > CUT_AFTER_H:
            lines.append(f"CUT FIRES: {g} {state}, {late:.1f} h past its time; cut the next cut-list item")
        else:
            lines.append(f"{g} {state}, due {due.isoformat()}, {(due - now).total_seconds() / 3600:+.1f} h from now")
    return lines


def gate_tags(root):
    try:
        out = subprocess.run(["git", "for-each-ref", "--format=%(refname:short) %(creatordate:iso-strict)",
                              "refs/tags/gate-G*"], cwd=root, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    tags = {}
    for line in out.splitlines():
        name, _, when = line.partition(" ")
        t = parse_time(when)
        if t and name[len("gate-"):] in GATES:
            tags[name[len("gate-"):]] = t
    return tags


def person_names(cell):
    """'Rick (proposed)' -> ['rick']; 'Ana, Bo' -> ['ana', 'bo']. TBD gives []."""
    cell = re.sub(r"\(.*?\)", "", cell)
    names = [n.strip().lstrip("@").lower() for n in re.split(r",|/|\band\b", cell)]
    return [n for n in names if n and not re.match(r"tbd\b", n)]


def seat_problems(text):
    """Every teammate holds a seat; nobody holds more than BLOCKER_SEATS_MAX BLOCKER seats."""
    seats, blockers, out = {}, {}, []
    for r in table_rows(section(text, "People")):
        if len(r) < 2:
            continue
        for n in person_names(r[1]):
            seats[n] = seats.get(n, 0) + 1
            if len(r) > 3 and "BLOCKER" in r[3]:
                blockers[n] = blockers.get(n, 0) + 1
    for n, k in sorted(blockers.items()):
        if k > BLOCKER_SEATS_MAX:
            out.append(f"People: {n} holds {k} BLOCKER seats, more than {BLOCKER_SEATS_MAX} (D-new-team-size)")
    for r in table_rows(section(text, "Team hours")):
        for n in person_names(r[0] if r else ""):
            if n not in seats:
                out.append(f"People: {n} has Team hours but no seat in the People table")
    return out


def people_warnings(text):
    rows = [r for r in table_rows(section(text, "Team hours")) if r and person_names(r[0])]
    out = []
    if len(rows) > TEAM_MAX:
        out.append(f"WARN: Team hours has {len(rows)} people, more than {TEAM_MAX} (D-new-team-size)")
    filled = [r for r in rows if len(r) > 3 and r[3].lower() in ("y", "n")]
    cpp = sum(1 for r in filled if r[3].lower() == "y")
    if filled and len(filled) == len(rows) and cpp < CPP_MIN:
        out.append(f"WARN: only {cpp} teammate(s) built UE C++ before, fewer than {CPP_MIN}; the TD human"
                   " decides D3 (Blueprint fallback) before card 0.3 (D-new-cpp-team)")
    return out


def away_problem(cell):
    """'none' or 'D2 12:00-14:00, D3 09:00-10:00'. None if fine, else a reason."""
    if re.fullmatch(r"\s*none\s*", cell, re.I):
        return None
    for part in cell.split(","):
        if not AWAY.fullmatch(part.strip()):
            return f"'{part.strip()}' is not 'D<n> HH:MM-HH:MM'"
    return None


def away_hours(cell):
    """{day: hours away} from an away-windows cell. A window past midnight wraps."""
    out = {}
    for d, h1, m1, h2, m2 in AWAY.findall(cell or ""):
        mins = (int(h2) * 60 + int(m2)) - (int(h1) * 60 + int(m1))
        out[int(d)] = out.get(int(d), 0) + (mins if mins > 0 else mins + 24 * 60) / 60
    return out


CONFIRMED = ("yes", "default (agent)")   # card 0.0: the Producer agent's rows (GitHub collaborators, the jam window)


def people_problems(text):
    out = seat_problems(text)
    people = table_rows(section(text, "People"))
    if not people:
        out.append("People table is missing")
    if not any(r[0].lower().startswith("producer") for r in people):
        out.append("People table has no 'Producer / time keeper (human)' row")
    for r in people:
        if len(r) < 3:
            continue
        if re.match(r"TBD\b", r[1]) or "(proposed" in r[1]:
            out.append(f"People: '{r[0][:40]}' has no confirmed person ('{r[1]}')")
        if r[2].lower() not in CONFIRMED:
            out.append(f"People: '{r[0][:40]}' Confirmed is '{r[2]}', not yes or default (agent)")
    team = table_rows(section(text, "Team hours"))
    if not team:
        out.append("Team hours table is missing")
    for r in team:
        if len(r) < 5:
            out.append(f"Team hours: row '{r[0]}' has {len(r)} cells, not 5")
            continue
        who = r[0]
        if re.match(r"TBD\b", who):
            out.append("Team hours: a row has no person (TBD)")
        if not HOURS.fullmatch(r[1]):
            out.append(f"Team hours: {who} hours '{r[1]}' is not D1/D2/D3/D4, e.g. 8/8/8/6")
        if not r[2] or re.match(r"TBD\b", r[2]):
            out.append(f"Team hours: {who} away windows not set (write 'none' if none)")
        elif away_problem(r[2]):
            out.append(f"Team hours: {who} away windows: {away_problem(r[2])}; --hours subtracts them (write 'none' if none)")
        if r[3].lower() not in ("y", "n"):
            out.append(f"Team hours: {who} 'Built UE C++ before' is '{r[3]}', not y or n")
        if r[4].lower() not in CONFIRMED:
            out.append(f"Team hours: {who} Confirmed is '{r[4]}', not yes or default (agent)")
    return out


def team_hours(text, away=False):
    """{person: [D1..D4 hours]}; with away=True, each day minus that person's away windows."""
    hours = {}
    for r in table_rows(section(text, "Team hours")):
        if len(r) >= 2 and HOURS.fullmatch(r[1]):
            h = [float(x) for x in r[1].split("/")]
            if away and len(r) >= 3:
                off = away_hours(r[2])
                h = [max(0.0, v - off.get(i + 1, 0)) for i, v in enumerate(h)]
            hours[r[0].lstrip("@").lower()] = h
    return hours


def issue_cards(issues, root):
    fields = template_fields(root)
    for issue in issues:
        card, _ = parse(issue.get("body") or "", fields, issue.get("title") or "")
        yield issue.get("number"), card


def hours_problems(issues, text, day, root=ROOT):
    hours = team_hours(text, away=True)
    full = team_hours(text)
    need = {}
    out = []
    cards = list(issue_cards(issues, root))
    budgeted = set()  # '#12' and 'UE-12' of every open card with a Budget
    for num, card in cards:
        if BUDGET.search(card.get("Budget") or ""):
            budgeted.add(f"#{num}")
            if card.get("ID"):
                budgeted.add(card["ID"].upper())
    for num, card in cards:
        who = (card.get("Human") or "").strip().lstrip("@").lower()
        m = BUDGET.search(card.get("Budget") or "")
        if not who or not m:
            out.append(f"#{num}: no Human or no '<n> min agent + <n> min human' budget; can't count it")
            continue
        need[who] = need.get(who, 0) + int(m.group(2))
        if (card.get("Owner role") or "").strip().lower().startswith("asset specialist"):
            refs = [r.upper() for r in CARD_REF.findall(card.get("Used by") or "")]
            if not any(r in budgeted for r in refs):
                out.append(f"#{num}: asset card's Used by names no open card with a Budget"
                           f" ({', '.join(refs) or 'none'}); file the Integrator card so its time is counted")
    for who, minutes in sorted(need.items()):
        if who not in hours:
            out.append(f"{who}: has open cards but no Team hours row")
        elif minutes > round(hours[who][day - 1] * 60 * RESERVE):
            cap = round(hours[who][day - 1] * 60 * RESERVE)
            gone = full[who][day - 1] - hours[who][day - 1]
            note = f" ({full[who][day - 1]:g} h minus {gone:g} h away)" if gone else ""
            out.append(f"{who}: {minutes} min of human budget on open cards, over {RESERVE:.0%} of"
                       f" {hours[who][day - 1]:g} h{note} ({cap} min) on day {day} (D-new-reserve);"
                       " move a card to someone who is in")
    return out


def queue_report(issues, root=ROOT):
    """Cards in review per Human -> (info lines, problems)."""
    per = {}
    for num, card in issue_cards(issues, root):
        who = (card.get("Human") or "").strip().lstrip("@").lower() or "(no human)"
        per.setdefault(who, []).append(num)
    info = ["Review queue: " + (", ".join(f"{w} {len(n)}" for w, n in sorted(per.items())) or "empty")]
    out = [f"QUEUE {w} has {len(n)} cards in review (limit {QUEUE_MAX}): {' '.join(f'#{x}' for x in n)};"
           f" none of {w}'s cards moves to doing (D-new-port-3)" for w, n in sorted(per.items()) if len(n) > QUEUE_MAX]
    return info, out


def doing_minutes(events, now):
    """Minutes the `doing` label was on, from issue timeline events. None if it was never added."""
    marks = []
    for e in events:
        name = ((e.get("label") or {}).get("name") or "").lower()
        t = parse_time(e.get("created_at") or e.get("createdAt") or "")
        if name == "doing" and t and e.get("event") in ("labeled", "unlabeled"):
            marks.append((t, e["event"]))
    if not any(ev == "labeled" for _, ev in marks):
        return None
    total, start = 0.0, None
    for t, ev in sorted(marks, key=lambda x: x[0]):
        if ev == "labeled" and start is None:
            start = t
        elif ev == "unlabeled" and start is not None:
            total += (t - start).total_seconds()
            start = None
    if start is not None:
        total += (now - start).total_seconds()
    return total / 60


def fetch_timeline(num):
    jq = '.[] | select(.event == "labeled" or .event == "unlabeled") | {event, created_at, label: {name: .label.name}}'
    out = subprocess.run(["gh", "api", f"repos/{{owner}}/{{repo}}/issues/{num}/timeline", "--paginate", "--jq", jq],
                         capture_output=True, text=True, check=True).stdout
    return [json.loads(ln) for ln in out.splitlines() if ln.strip()]


def overrun_report(issues, now, root=ROOT, fetch=fetch_timeline):
    """Cards labelled doing -> (info lines, problems). Each issue may carry its own 'timeline' list."""
    fields = template_fields(root)
    info, out = [], []
    for issue in issues:
        num = issue.get("number")
        card, _ = parse(issue.get("body") or "", fields, issue.get("title") or "")
        m = BUDGET.search(card.get("Budget") or "")
        budget = int(m.group(1)) + int(m.group(2)) if m else 0
        events = issue["timeline"] if "timeline" in issue else fetch(num)
        mins = doing_minutes(events, now)
        if mins is None:
            out.append(f"#{num}: no 'doing' label event in its timeline; can't time it")
            continue
        over = int(mins - budget)
        note = "" if m else " (no Budget: timed against 0 min)"
        if over > OVERRUN_MIN:
            out.append(f"OVERRUN #{num} +{over} min: doing {int(mins)} min, budget {budget} min{note};"
                       " cut or split it, or hide a non-P0 bug and refile it P2 (D-new-overrun)")
        elif over > 0:
            info.append(f"OVER BUDGET #{num} +{over} min: doing {int(mins)} min, budget {budget} min{note}; stop and report")
        else:
            info.append(f"#{num} doing {int(mins)} of {budget} min{note}")
    return info, out


def hard_stop_window(text):
    """(start minute, end minute, tzinfo) from the Clock, or a problem string."""
    c = clock(text) or {}
    m = re.fullmatch(r"(\d\d):(\d\d)-(\d\d):(\d\d)", c.get("Hard stop") or "")
    deadline = parse_time(c.get("Submission deadline") or "")
    if not m or deadline is None:
        return "Clock: Hard stop (HH:MM-HH:MM) and Submission deadline must be set to check the hard stop"
    h1, m1, h2, m2 = (int(x) for x in m.groups())
    return h1 * 60 + m1, h2 * 60 + m2, deadline.tzinfo


def hardstop_problems(log_lines, text, since):
    """log_lines: 'sha<TAB>committer ISO<TAB>author<TAB>committer'. Commits inside the hard stop window."""
    w = hard_stop_window(text)
    if isinstance(w, str):
        return [w]
    start, end, tz = w
    out = []
    for ln in log_lines:
        parts = ln.split("\t")
        t = parse_time(parts[1]) if len(parts) >= 3 else None
        if t is None or t < since:
            continue
        local = t.astimezone(tz)
        mm = local.hour * 60 + local.minute
        inside = start <= mm < end if start < end else (mm >= start or mm < end)
        if inside:
            who = parts[2] + (f" (committed by {parts[3]})" if len(parts) > 3 and parts[3] != parts[2] else "")
            out.append(f"HARD STOP {parts[0][:8]} at {local.strftime('%a %H:%M')} by {who} (D-new-hardstop)")
    return out


def git_log_lines(root):
    fmt = "--format=%H%x09%cI%x09%an%x09%cn"
    for ref in ("origin/main", "main"):
        try:
            return subprocess.run(["git", "log", ref, fmt, "--since=48 hours ago"], cwd=root,
                                  capture_output=True, text=True, check=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            continue
    raise ValueError("git log: no origin/main or main branch")


def expand_braces(p):
    m = re.search(r"\{([^{}]*)\}", p)
    if not m:
        return [p]
    return [x for alt in m.group(1).split(",") for x in expand_braces(p[:m.start()] + alt + p[m.end():])]


def mvp_card_problems(card, mvp):
    """Extra rules for a numeric MVP card (dry-run finding: a broken MVP card passed with 0 problems)."""
    if not re.fullmatch(r"(?:MVP\s*)?#?\d+\b.*", mvp or "", re.S):
        return []
    out = []
    for f in ("GDD ref", "Player outcome"):
        if re.fullmatch(r"\s*none\b.*", card.get(f) or "", re.S | re.I):
            out.append(("field", f"an MVP card needs a real '{f}', not 'none'"))
    lane = card.get("File lane") or ""
    done = card.get("Done when") or ""
    locks = card.get("Binary locks") or ""
    for umap in sorted(set(re.findall(r"[\w/.-]+\.umap", lane))):
        if umap not in locks:
            out.append(("lane", f"{umap} is in the lane but not in Locks; lock every map the card writes"))
    if (re.search(r"\bConfig/", lane) or ".umap" in lane) and "SMOKE_OK" not in done:
        out.append(("done", "the lane has Config/ or a .umap, so Done-when needs a packaged SMOKE_OK line"))
    if re.search(r"\bSource/", lane) and not re.match(r"\s*Dev Lead\b", card.get("Reviewer role") or "", re.I):
        out.append(("owner", "the lane has Source/, so the reviewer is Dev Lead"))
    return out


def lane_globs(value):
    globs = []
    for t in LANE_TOKEN.findall(re.sub(r"`", " ", value or "")):
        t = t.rstrip(".,").lstrip(",")   # a leading dot stays: .github/, .claude/**, .gitignore
        if t and not re.fullmatch(r"[/*.]+", t):
            globs.extend(expand_braces(t))
    return globs


def globs_overlap(a, b):
    wild = re.compile(r"[*?\[]")
    pa, pb = wild.split(a, 1)[0], wild.split(b, 1)[0]
    if not wild.search(a) and not wild.search(b):
        return a == b
    if not wild.search(a):
        return a.startswith(pb)
    if not wild.search(b):
        return b.startswith(pa)
    return pa.startswith(pb) or pb.startswith(pa)


# Each card edits only its own rows or lines in these; not a shared lane (day0-cards.md)
ROW_SCOPED = {"pipeline/qa/test-map.md", "docs/decisions.md", "docs/jam-brief.md", "pipeline/art/provenance.csv"}


def lanes_problems(issues, root=ROOT):
    cards = []
    for num, card in issue_cards(issues, root):
        lane = card.get("File lane") or ""
        if NO_FILES_LANE.fullmatch(lane):
            continue
        cards.append((num, [g for g in lane_globs(lane) if g not in ROW_SCOPED], lane_globs(card.get("Binary locks") or "")))
    out = []
    for i, (na, la, ka) in enumerate(cards):
        for nb, lb, kb in cards[i + 1:]:
            for a in la:
                for b in lb:
                    if globs_overlap(a, b):
                        what = ".umap" if a.endswith(".umap") or b.endswith(".umap") else "lane"
                        out.append(f"#{na} and #{nb} share a {what}: '{a}' / '{b}'")
            for k in set(ka) & set(kb):
                out.append(f"#{na} and #{nb} both lock '{k}'")
    return sorted(set(out))


# --blocked-by: a blocked card holds only the cards that wait on it (AGENTS.md section 6). Every other lane works on.
DAY0_ID = re.compile(r"0\.\d{1,2}[a-z]?")
AFTER_LINE = re.compile(r"^\s*[-*]?\s*\**After\**\s*:\s*(.+)$", re.I | re.M)
WAIT_REF = re.compile(r"#\d+|\bUE-\d+(?:\.\d+[a-z]?)?\b|(?<![\w.])0\.\d{1,2}[a-z]?\b", re.I)


def card_key(ref):
    """'UE-0.3' / '0.3' / 'ue-12' -> '0.3' / '12'; '#34' stays '#34'."""
    ref = ref.strip()
    return ref if ref.startswith("#") else re.sub(r"(?i)^ue-", "", ref).lower()


def natural(key):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", key)]


def day0_table(root):
    """[(id, name, after ids)] from the pipeline/day0-cards.md table."""
    out = []
    for line in read(os.path.join(root, "pipeline", "day0-cards.md")).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("| ") else []
        if len(cells) >= 6 and DAY0_ID.fullmatch(cells[0]):
            out.append((cells[0], cells[1], DAY0_ID.findall(cells[5])))
    return out


# Agents own every card; a person acts only at a true checkpoint (pipeline/human-checkpoints.md "Checkpoint kinds").
# Only two remain on Day-0 cards: the itch upload (Official Rules 17) and setting API keys. Gate patches are applied
# by kickoff through the tool checks (tools/git_gate.py apply --auto); machine work runs in kickoff on that machine.
CHECKPOINT_KINDS = ("submission", "secrets")
HUMAN_LINE = re.compile(r"^\s*HUMAN (?P<kind>[a-z]+):\s+\S")
SIGNOFF = re.compile(r"\(sign-off:\s*([^)]*)\)")
# A Done-when line that has a person act. Seats and names from the People table and the docs.
HUMAN_ACTOR = re.compile(r"\b(?:TD human|human Producer|Producer \(human\)|Rick|Richard|each teammate|every teammate|"
                         r"game design owner|scope decision-maker|packaging (?:machine|and submission) owner|"
                         r"launch machine owner|Art Director human|Creative director|audio owner|playtest lead|"
                         r"(?:the|a) human)\b")
PREJAM_LINE = re.compile(r"^\*\*Pre-jam cards:\*\*\s*(.+)$", re.M)


def prejam_cards(root=ROOT):
    """The cards kickoff files and runs before the jam start on the team repo (pipeline/day0-cards.md
    'Pre-jam cards:' line): tools, agent setup, rules and the synthetic workbench sample (Official Rules 7(h))."""
    m = PREJAM_LINE.search(read(os.path.join(root, "pipeline", "day0-cards.md")))
    return set(DAY0_ID.findall(m.group(1))) if m else set()


GATE_CARDS_LINE = re.compile(r"^\*\*(G[1-4]) cards:\*\*\s*(.+)$", re.M)


def gate_cards(root=ROOT, gate="G1"):
    """The Day-0 cards a gate needs (pipeline/day0-cards.md `**G1 cards:**` line; kickoff --until G1). Empty when the
    gate has no line: then only its MVP cards and their After cards count."""
    for g, ids in GATE_CARDS_LINE.findall(read(os.path.join(root, "pipeline", "day0-cards.md"))):
        if g == gate:
            return DAY0_ID.findall(ids)
    return []


def day0_owner_problems(text, roles_list):
    """Every Day-0 row is agent-owned, and a person appears only at a true checkpoint: column 3 starts with an agent
    role; `/ <seat> (sign-off: k, ...)` names known kinds; the reviewer is an agent role; a Done-when
    line that has a person act starts `HUMAN <kind>:` with a kind the row signs off."""
    out = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("| ") else []
        if len(cells) != 7 or not DAY0_ID.fullmatch(cells[0]):
            continue
        cid, _, owner_human, reviewer, _, _, done = cells
        owner, _, human = (p.strip() for p in owner_human.partition("/"))
        if owner not in roles_list:
            out.append(f"{cid}: owner '{owner}' is not an agent role: agents own every card (a person's part is a "
                       "`HUMAN <kind>:` line)")
        m = SIGNOFF.search(human)
        kinds = [k.strip() for k in m.group(1).split(",") if k.strip()] if m else []
        for k in kinds:
            if k not in CHECKPOINT_KINDS:
                out.append(f"{cid}: sign-off '{k}' is not a checkpoint kind ({', '.join(CHECKPOINT_KINDS)})")
        if reviewer not in roles_list:
            out.append(f"{cid}: reviewer '{reviewer}' is " + ("a person: give the review to an agent role (a fresh "
                       "session; kickoff merges on its approve)" if reviewer.startswith("Human")
                       else "not an agent role"))
        used = set()
        for seg in done.split("<br>"):
            hm = HUMAN_LINE.match(seg)
            if hm:
                k = hm.group("kind")
                used.add(k)
                if k not in CHECKPOINT_KINDS:
                    out.append(f"{cid}: 'HUMAN {k}:' is not a checkpoint kind ({', '.join(CHECKPOINT_KINDS)})")
                elif k not in kinds:
                    out.append(f"{cid}: a 'HUMAN {k}:' line but column 3 does not sign off '{k}'")
            elif HUMAN_ACTOR.search(re.sub(r"`[^`]*`", "", seg)):
                out.append(f"{cid}: a person acts in a line with no `HUMAN <kind>:` tag (an agent does the work, or "
                           f"it is a checkpoint): {seg.strip()[:90]}")
        for k in kinds:
            if k not in used:
                out.append(f"{cid}: signs off '{k}' but no Done-when line starts 'HUMAN {k}:'")
    return out


NEEDS_HUMAN_LABEL = "needs-human"
NEEDS_HUMAN = re.compile(r"^\s*(?:ROLE:[^\n]*\n\s*)?NEEDS HUMAN:\s+(?P<who>\S+)\s+(?P<what>.*?\S)\s+(?P<link>#\d+|https?://\S+)"
                         r"(?:\s+(?P<at>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z))?\s*$", re.M)
TD_SEAT = re.compile(r"^(?:TD\b|Technical)", re.I)


def grace_role(who):
    """The director session a grace default goes to (pipeline/human-checkpoints.md): technical calls to the
    Technical Director, design calls in Richard's area to the Producer acting for Richard, the rest (scope, schedule,
    cut list, approvals) to the Producer."""
    if TD_SEAT.match(who or ""):
        return "Technical Director"
    if (who or "").strip().lower().startswith("richard"):
        return "Producer for Richard"
    return "Producer"


def needs_human_queue(issues, now=None):
    """(lines, problems) for open issues labelled needs-human: each needs a `NEEDS HUMAN: <who/role> <what> <link>`
    comment (AGENTS.md section 4). The newest such comment is the ask the human answers.

    With now (a UTC-aware datetime; --needs-human passes it) each ask also needs its UTC timestamp, and the line ends
    with the grace state: `grace ends <t>`, `human replied` (a later comment that is not an agent's `ROLE:` comment),
    `GRACE EXPIRED -> <role>` after manifest_check.GRACE_HOURS, or `HUMAN ONLY (<kind>): no grace default` for the
    kinds that never get one (manifest_check.grace_kind)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import manifest_check  # noqa: E402  one human-only list for the queue and the decisions rows
    lines, probs = [], []
    for it in issues or []:
        labels = {(lb.get("name") if isinstance(lb, dict) else str(lb)) for lb in it.get("labels") or []}
        if NEEDS_HUMAN_LABEL not in labels:
            continue
        comments = it.get("comments") or []
        asks = [(i, m) for i, c in enumerate(comments) for m in NEEDS_HUMAN.finditer(c.get("body") or "")]
        if not asks:
            probs.append(f"#{it.get('number')}: labelled {NEEDS_HUMAN_LABEL} but no comment reads "
                         "`NEEDS HUMAN: <who/role> <what> <link>`")
            continue
        idx, m = asks[-1]
        line = f"#{it.get('number')} {m.group('who')}: {m.group('what')} {m.group('link')}"
        if now is None:
            lines.append(line)
            continue
        kind = manifest_check.grace_kind(m.group("what"))
        if kind:
            lines.append(f"{line} HUMAN ONLY ({kind}): no grace default")
            continue
        at = parse_time(m.group("at") or "")
        if at is None:
            probs.append(f"#{it.get('number')}: the NEEDS HUMAN line has no UTC timestamp (`... <link> "
                         "2026-11-12T18:00Z`), so its 2 h grace cannot start")
            continue
        replied = any(not re.match(r"\s*ROLE:", c.get("body") or "") for c in comments[idx + 1:])
        ends = at + dt.timedelta(hours=manifest_check.GRACE_HOURS)
        if replied:
            lines.append(f"{line} human replied")
        elif now >= ends:
            lines.append(f"{line} GRACE EXPIRED -> {grace_role(m.group('who'))}")
        else:
            lines.append(f"{line} grace ends {ends.astimezone(dt.timezone.utc):%Y-%m-%dT%H:%MZ}")
    return lines, probs


def blocked_by(card, root=ROOT, issues=()):
    """Cards that wait on `card`, directly or through other cards, in breadth-first order: [(key, label)].

    Edges: a Day-0 row lists the card in After; a filed card has an 'After: ...' line naming it; or the
    card's own Used by names the filed card. Raises KeyError for a card nobody knows."""
    alias, label, waits = {}, {}, {}
    for cid, name, after in day0_table(root):
        alias[cid] = cid
        label[cid] = f"{cid}  {name}"
        for a in after:
            waits.setdefault(card_key(a), set()).add(cid)
    fields = template_fields(root)
    filed = []
    for issue in issues or ():
        num, title, body = issue.get("number"), issue.get("title") or "", issue.get("body") or ""
        c, _ = parse(body, fields, title)
        cid = card_key(c["ID"]) if re.match(r"(?i)UE-\d", c.get("ID") or "") else ""
        key = cid or f"#{num}"
        alias.setdefault(key, key)
        alias[f"#{num}"] = key
        label[key] = f"#{num} {title}".strip()
        filed.append((key, body, c.get("Used by") or ""))
    for key, body, used_by in filed:
        for m in AFTER_LINE.finditer(body):
            for ref in WAIT_REF.findall(m.group(1)):
                waits.setdefault(card_key(ref), set()).add(key)
        if re.search(r"^###\s+After\b", body, re.M):   # the issue form's After field (its value is on the next lines)
            for ref in WAIT_REF.findall(parse(body, fields)[0].get("After") or ""):
                waits.setdefault(card_key(ref), set()).add(key)
        for ref in WAIT_REF.findall(used_by):
            waits.setdefault(key, set()).add(card_key(ref))
    start = alias.get(card_key(card))
    if start is None:
        raise KeyError(f"card '{card}' is not in pipeline/day0-cards.md or the filed cards given")
    graph = {}
    for src, dsts in waits.items():
        graph.setdefault(alias.get(src, src), set()).update(alias.get(d, d) for d in dsts)
    order, seen, queue = [], {start}, [start]
    while queue:
        cur = queue.pop(0)
        for nxt in sorted(graph.get(cur, ()), key=natural):
            if nxt not in seen:
                seen.add(nxt)
                order.append(nxt)
                queue.append(nxt)
    return [(k, label.get(k, k)) for k in order]


def status_fields(root):
    text = read(os.path.join(root, "pipeline", "roles", "producer.md"))
    m = re.search(r"`(Accepted since last status[^`]*)`", text)
    return [re.split(r"[(:]", f)[0].strip() for f in m.group(1).split(" | ")] if m else []


TEST_UPLOAD = re.compile(r"upload.*https?://\S+.*sha256=[0-9a-f]{64}", re.I)
# The verdict, any separator, then a reason holding a word (final-7 A M2: "on track, G1 21:00", "at risk: 2 cards
# blocked" and "at risk (G1 package not yet green)" are ordinary reasons)
NEXT_GATE = re.compile(r"(on track|at risk|will miss)\b[\s,;:.+()\[\]–—-]*(?=[^|\n]*[A-Za-z]{2,})\S", re.I)
RETRO_QS = ("What slowed us since the last gate?", "What do we change for the next one?")
CUT_PROPOSED = re.compile(r"Cut proposed:\s*(?!<)[^\s|][^|\n]{2,}", re.I)
RETRO_LEAD_H = 1    # the two retro questions are on the tracker this many hours before each gate


def field_value(body, name):
    """'Next gate: at risk, X | Absences next 12h: none' -> value of one field, or None."""
    m = re.search(re.escape(name) + r"[^:|\n]*:\s*([^|\n]*)", body, re.I)
    return m.group(1).strip() if m else None


def status_value_problems(body):
    out = []
    v = field_value(body, "Next gate")
    if v is not None and not NEXT_GATE.match(v):
        out.append(f"status line 'Next gate: {v[:40]}' needs 'on track', 'at risk' or 'will miss' first, then a reason "
                   "with at least one word (e.g. 'at risk: 2 cards blocked')")
    v = field_value(body, "Absences next 12h")
    if v is not None and (not re.search(r"[A-Za-z]{2,}", v) or PLACEHOLDER.search(v) or re.match(r"tbd\b", v, re.I)):
        out.append(f"status line 'Absences next 12h: {v[:40]}' is blank; write 'none' or name who is away and when")
    return out


def retro_problems(comments, now, brief_text):
    """Within RETRO_LEAD_H of a gate, both retro questions are on the tracker since the previous gate."""
    c = clock(brief_text) or {}
    due = [(g, parse_time(c.get(g) or "")) for g in GATES]
    due = [(g, t) for g, t in due if t]
    out = []
    for i, (g, t) in enumerate(due):
        if not t - dt.timedelta(hours=RETRO_LEAD_H) <= now <= t:
            continue
        since = due[i - 1][1] if i else None
        bodies = [x.get("body") or "" for x in comments
                  if since is None or ((parse_time(x.get("createdAt") or "") or since) >= since)]
        for q in RETRO_QS:
            if not any(q.lower() in b.lower() for b in bodies):
                out.append(f"{g} is due within {RETRO_LEAD_H} h and the tracker has no '{q}' comment since the"
                           " last gate (gate-record template)")
    return out


TRACKER_STATUS = ("todo", "doing", "review", "closed", "in build", "passed", "cut")
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
PLAYTEST_PASS = re.compile(r"\bP\d+ pass \d{4}-\d\d-\d\d\b|\bno P-test\b", re.I)


def tracker_problems(body, root=ROOT):
    """Tracker issue body: one row per MVP item, | MVP | Card | Status | Build sha | Playtest |
    (pipeline/templates/tracker-table.md). 'in build' and 'passed' need a sha; 'passed' needs a playtest pass."""
    mvp_numbers, _ = brief(root)
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import manifest_check
    overrides = manifest_check.decided_overrides(manifest_check.read_decisions(root))
    rows, header = [], None
    for line in (body or "").splitlines():
        if not line.strip().startswith("|"):
            if rows:
                break
            header = None
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if all(set(x) <= set("-: ") for x in cells):
            continue
        if header is None:
            if cells and cells[0].lower() == "mvp" and len(cells) >= 5:
                header = cells
            continue
        rows.append(cells)
    if header is None and not rows:
        return ["tracker has no MVP table ('| MVP | Card | Status | Build sha | Playtest |',"
                " pipeline/templates/tracker-table.md)"]
    out, seen = [], {}
    for r in rows:
        r = (r + [""] * 5)[:5]
        if not re.fullmatch(r"\d+", r[0]):
            out.append(f"tracker row '{r[0][:20]}' is not an MVP number")
            continue
        n = int(r[0])
        seen[n] = seen.get(n, 0) + 1
        st = r[2].lower()
        if st not in TRACKER_STATUS:
            out.append(f"tracker MVP {n}: status '{r[2]}' is not one of {', '.join(TRACKER_STATUS)}")
        if not CARD_REF.search(r[1]) and st != "cut":
            out.append(f"tracker MVP {n}: Card '{r[1]}' names no issue (#<n>)")
        if st in ("in build", "passed") and not SHA.search(r[3]):
            out.append(f"tracker MVP {n}: '{st}' needs the packaged build's commit sha")
        if st == "passed" and not PLAYTEST_PASS.search(r[4]):
            out.append(f"tracker MVP {n}: 'passed' needs 'P<n> pass YYYY-MM-DD' (or 'no P-test')")
        if st == "cut":
            feats = mvp_features(root).get(n) or set()
            left = sorted(feats - overrides) if feats else ["(no feature IDs on its jam-brief line)"]
            if left:
                out.append(f"tracker MVP {n}: 'cut', but every MVP item is APPROVED_P0 and never cut (docs/jam-brief.md); "
                           f"only a DECIDED row with 'Overrides: {', '.join(left)}' allows it")
    for n in sorted(mvp_numbers):
        if seen.get(n, 0) != 1:
            out.append(f"tracker has {seen.get(n, 0)} rows for MVP {n}, not 1")
    for n in sorted(set(seen) - mvp_numbers):
        out.append(f"tracker row MVP {n} is not in docs/jam-brief.md")
    return out


def cut_tier(value):
    """The tier token: the whole Cut tier field (template card), or the text after the last comma of the form's
    one "Budget and cut tier" field ("90 min agent + 20 min human, MVP")."""
    v = (value or "").strip()
    if re.search(r"\bmin\b", v) and "," in v:
        v = v.rsplit(",", 1)[1]
    return v.strip()


def gate_template(root):
    text = read(os.path.join(root, "pipeline", "templates", "gate-record.md"))
    block = re.search(r"```\n(.*?)```", text, re.S).group(1)
    return [tuple(x.strip() for x in ln.split(":", 1)) for ln in block.splitlines() if ":" in ln]


def submission_status(brief_text, now, root=ROOT):
    """The daily devlog, footage and theme checks (submission_check.status_hook) for --status."""
    sys.path.insert(0, os.path.join(root, "tools"))
    import submission_check
    return submission_check.status_hook(brief_text, now, root)


def butler_record_problems(record):
    """A G1 gate record carries the BUTLER line from the packaging machine (submission.md)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import submission_check
    line = next((ln for ln in record.splitlines() if re.match(r"\s*BUTLER\s", ln)), None)
    if line is None:
        return ["G1 record has no 'BUTLER version=<v> login=ok user=<itch-user> by=<name>' line (submission.md)"]
    return [f"G1 record BUTLER line: {p}" for p in submission_check.butler_problems(line)]


def baked_record_problems(lines, root=ROOT):
    """G4: the shipped defaults are the approved workbench preset (D-new-workbench-debug). The line names the
    preset and pastes the `bake_preset.py check --record` result for that same preset. The preset is T-01 (BASE,
    GDD 1.3 section 5A) unless a DECIDED row in docs/decisions.md says 'Overrides: <that preset>'."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bake_preset
    v = lines.get("baked preset")
    m = re.match(r"\s*(T-\d{2})\b", v or "")
    if not m:
        return ["G4 record has no 'Baked preset: T-nn | <bake_preset.py check --record output>' line (D-new-workbench-debug)"]
    if m.group(1) != bake_preset.SHIP_PRESET and not bake_preset.decided_names(bake_preset.read_decisions(root), m.group(1)):
        return [f"G4 record bakes {m.group(1)}, not {bake_preset.SHIP_PRESET} (BASE): only BASE ships unless a DECIDED "
                f"row in docs/decisions.md says 'Overrides: {m.group(1)}'"]
    if FAIL_WORDS.search(v):   # final-7 B H8: "FAIL 2 problem(s) | ... PASS" never passes
        return ["G4 record 'Baked preset:' shows a failure; paste only the passing `bake_preset check --record` line"]
    ok = re.search(r"bake_preset check: PASS preset=(T-\d{2})\b", v)
    if not ok:
        return [f"G4 record 'Baked preset:' has no `bake_preset check: PASS preset={m.group(1)}` result pasted"]
    if ok.group(1) != m.group(1):
        return [f"G4 record approves {m.group(1)}, but the pasted bake check is for {ok.group(1)}"]
    return build_bake_problems(lines, m.group(1), root)


def git_out(root, *args):
    import subprocess
    try:
        p = subprocess.run(["git", "-C", root, *args], capture_output=True)
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None


def extract_commit(root, full, tmp):
    """Write commit `full`'s tree into tmp (git archive). Returns an error string or None."""
    import io as _io
    import tarfile
    tar = git_out(root, "archive", "--format=tar", full)
    if tar is None:
        return "git archive failed"
    with tarfile.open(fileobj=_io.BytesIO(tar)) as tf:
        try:
            tf.extractall(tmp, filter="data")
        except TypeError:   # Python before 3.12
            tf.extractall(tmp)
    return None


RECORD_FILE = os.path.join("Saved", "Logs", "pipeline", "daily-records.txt")
LAUNCH_LINE = re.compile(r"^LAUNCH ([0-9a-f]{64}) \|(?P<meta>[^|]*)\| (?P<eff>SMOKE_EFFECTIVE\b.*)$")


# Final-10 A H5: the gate's DAILY line is the Win64 packaging machine's daily.ps1 run (pipeline/checklists/
# submission.md: `$env:SMOKE_REPEAT=5; tools\ue\daily.ps1` on the packaging machine). A Mac DAILY line counts only once a
# DECIDED Mac fallback rule exists: Josh's pending decision. Until then this stays None and only Windows counts.
DAILY_MAC_FALLBACK = None
DAILY_HOST = re.compile(r"^\s*DAILY \S+ \| (?P<node>[^/|]+)/(?P<system>[^\s|]+)")
LAUNCH_META = re.compile(r"\b([a-z_0-9]+)=(\S+)")


def packaging_machine(root=ROOT):
    """The machine name in the docs/jam-brief.md People row 'Windows packaging machine (owner, machine name, OS)'."""
    try:
        text = read(os.path.join(root, "docs", "jam-brief.md"))
    except OSError:
        return None
    for r in table_rows(section(text, "People")):
        if r and r[0].lower().startswith("windows packaging machine") and len(r) > 1:
            parts = [x.strip() for x in r[1].split(",")]
            if len(parts) >= 2 and parts[1] and not re.match(r"TBD\b", parts[1], re.I):
                return parts[1]
    return None


def host_name(node):
    return (node or "").strip().split(".")[0].lower()


def daily_host_problems(daily_line, root=ROOT):
    m = DAILY_HOST.match(daily_line or "")
    if not m:
        return []
    out = []
    if m.group("system") != "Windows" and not DAILY_MAC_FALLBACK:
        out.append(f"Repeat boots: the DAILY line ran on {m.group('node')}/{m.group('system')}; a gate's daily is "
                   "`SMOKE_REPEAT=5 tools\\ue\\daily.ps1` on the Win64 packaging machine (pipeline/checklists/"
                   "submission.md). No Mac fallback rule is decided yet (final-10 A H5)")
    want = packaging_machine(root)
    if want and m.group("system") == "Windows" and host_name(m.group("node")) != host_name(want):
        out.append(f"Repeat boots: the DAILY line ran on {m.group('node')}, not the packaging machine {want} "
                   "(docs/jam-brief.md People)")
    return out


def machine_record_problems(lines, gate, records, root=ROOT):
    """Final-9 B H4, H5, A H4: the gate's tool lines are the machine's own records, not typed text. The Repeat boots
    line is a line of the record file (Saved/Logs/pipeline/daily-records.txt, plus each --records file) from the Win64
    packaging machine (final-10 A H5); the PLAYTHROUGH result is re-run on the record's PLAYTHROUGH line; the zip
    check's zip is on disk with that sha256 and passes `submission_check.py zip --gate` again; every first-parent
    commit since the last gate has a passing DAILY line (merge-check, re-run; final-10 A M3); the UI line is re-run
    on the Build commit (final-10 A M5); and "re-downloaded and launched: yes" needs the record's LAUNCH line for that
    zip's sha256 (tools/ue_run.py launch-record: a passing smoke of the unzipped zip) from another machine (final-10 A
    M2), whose exe= member of the zip on disk has the recorded exe_sha256 (final-10 B H1, H2), from the Win64 build
    (SMOKE_EFFECTIVE platform=Windows, workbench=0), whose live values pass `bake_preset.py effective` on the Build
    commit's tree (complete at G4: the G4 bake tie)."""
    import contextlib
    import hashlib
    import io
    import tempfile
    import zipfile
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bake_preset
    import submission_check
    import ue_run
    out = []
    recs = [ln.strip() for ln in records if ln.strip()]
    if not recs:
        return ["no machine record lines: run --gate-record on the packaging machine (it reads "
                f"{RECORD_FILE}) or pass each machine's record file with --records (final-9 B H4)"]
    rb = lines.get("repeat boots", "").strip()
    if rb and rb not in recs:
        out.append("Repeat boots is not a line of the machine record: paste the DAILY line daily.sh / daily.ps1 "
                   "printed for the Build commit, unedited (the records read: this machine's "
                   f"{RECORD_FILE} plus each --records file)")
    elif rb:
        out += daily_host_problems(rb, root)
    b = re.match(r"\s*([0-9a-f]{7,40})\s*\|", lines.get("build", ""))
    sha = b.group(1) if b else ""
    full = git_out(root, "rev-parse", "--verify", "--quiet", sha + "^{commit}") if sha else None
    full = full.decode().strip() if full else None
    tmp_ctx = tempfile.TemporaryDirectory()
    tree = tmp_ctx.name
    tree_err = extract_commit(root, full, tree) if full else "no Build commit"
    try:
        pt = PLAYTHROUGH_OUT.match(lines.get("playthrough", ""))
        if pt:
            mine = [ln for ln in recs if ln.startswith("PLAYTHROUGH ") and len(ln.split()) > 1
                    and len(ln.split()[1]) >= 7 and same_sha(ln.split()[1], pt.group(1))]
            if not mine:
                out.append(f"PLAYTHROUGH: the machine record has no PLAYTHROUGH line for {pt.group(1)}")
            else:
                probs = ue_run.playthrough_problems(mine[-1], gate, root)
                if probs:
                    out.append(f"PLAYTHROUGH: the record's line for {pt.group(1)} fails at {gate}: " + "; ".join(probs))
        if full and gate in GATE_MVP:
            n = int(gate[1])
            since = next((t for t in [f"gate-G{n - 1}"] if n > 1 and git_out(root, "rev-parse", "--verify", "--quiet",
                                                                          t + "^{commit}")), "jam-start")
            if git_out(root, "rev-parse", "--verify", "--quiet", since + "^{commit}"):
                try:
                    _, missing = ue_run.merge_missing(root, since, recs, require_client=gate != "G1", until=full)
                except OSError as e:
                    missing, out = [], out + [f"merge-check: {e}"]
                if missing:
                    out.append(f"merge-check: {len(missing)} first-parent commit(s) in {since}..{sha} have no passing "
                               "DAILY line in the machine records (" + ", ".join(x[:12] for x in missing[:5]) + "): run "
                               "the daily on each (pipeline/roles/qa-build.md; final-10 A M3)")
        if sha and gate in ("G2", "G3", "G4"):
            # The player screens exist from G2: the UIFLOW line (quits, mouse in menus, the whole flow) is
            # re-checked from the machine record for the Build commit, never trusted from typed text.
            import ui_check
            flows = [ln for ln in recs if ln.startswith("UIFLOW")
                     and same_sha(ui_check._fields(ln).get("commit", ""), sha)]
            if not flows:
                out.append(f"UIFLOW: the machine record has no UIFLOW line for the Build commit {sha}: QA plays the "
                           "package (pipeline/ui/accessibility.md section 4) and appends the line to "
                           f"{RECORD_FILE}")
            else:
                probs = ui_check.flow_problems(flows[-1], sha)
                if probs:
                    out.append(f"UIFLOW: the record's line for {sha} fails: " + "; ".join(probs[:5]))
        if full and not tree_err:
            import ui_check
            with contextlib.redirect_stdout(io.StringIO()):
                ui = ui_check.run_ci(tree, release=gate != "G1")
            if ui:
                out.append(f"Gate checks: `ui_check ci{'' if gate == 'G1' else ' --release'}` on the Build commit {sha} "
                           f"fails ({len(ui)} problem(s): " + "; ".join(ui[:3]) + "): the pasted UI line is re-run "
                           "(final-10 A M5)")
        z = ZIP_OUT.search(lines.get("gate checks", ""))
        digest, zp = None, None
        if z:
            zp = z.group(1) if os.path.isabs(z.group(1)) else os.path.join(root, z.group(1))
            if not os.path.isfile(zp):
                out.append(f"the zip check's {z.group(1)} is not on this machine: run --gate-record where the zip is")
                zp = None
            else:
                with open(zp, "rb") as fh:
                    digest = hashlib.sha256(fh.read()).hexdigest()
                if digest != z.group(3):
                    out.append(f"{z.group(1)} on disk has sha256={digest}, not the pasted {z.group(3)}")
                zprobs = submission_check.zip_problems(zp, commit=sha or None, gate=gate)
                out += [f"{z.group(1)}: {p}" for p in zprobs]
        upload = next((v for k, v in lines.items() if k.endswith("test upload (g1 on)")), "")
        launched = re.search(r"re-downloaded and launched:\s*([^|]*)", upload)
        if launched and launched.group(1).strip() == "yes":
            up = UPLOAD_SHA.search(upload)
            want = digest or (z.group(3) if z else None) or (up.group(1) if up else None)
            hits = [LAUNCH_LINE.match(ln) for ln in recs if ln.startswith("LAUNCH ")]
            hits = [h for h in hits if h and h.group(1) == want]
            if not hits:
                out.append("'re-downloaded and launched: yes' has no LAUNCH record line for the zip's sha256: smoke the "
                           "re-downloaded zip with $env:SMOKE_ZIP=\"<zip>\"; tools\\ue\\smoke.ps1 on Windows (A H4, B H5)")
            else:
                out += launch_line_problems(hits[-1], zp, rb, sha, full, tree, tree_err, gate, bake_preset, ue_run)
    finally:
        tmp_ctx.cleanup()
    return out


def launch_line_problems(hit, zp, daily, sha, full, tree, tree_err, gate, bake_preset, ue_run):
    """One LAUNCH line against the files: the zip member it names has its exe_sha256 (final-10 B H1, H2), its fields
    agree with its SMOKE_EFFECTIVE line, workbench=0 (final-10 B H2), another machine than the daily's (A M2)."""
    import hashlib
    import zipfile
    out = []
    eff = ue_run.parse_effective(hit.group("eff"))
    meta = dict(LAUNCH_META.findall(hit.group("meta")))
    if not meta.get("exe") or not re.fullmatch(r"[0-9a-f]{64}", meta.get("exe_sha256", "")):
        out.append("the LAUNCH line has no exe= and exe_sha256=: it was not written by `ue_run.py launch-record` "
                   "(smoke.sh / smoke.ps1 with SMOKE_ZIP): smoke the unzipped zip again (final-10 B H1)")
    elif zp:
        try:
            with zipfile.ZipFile(zp) as zf, zf.open(meta["exe"]) as fh:
                got = hashlib.sha256(fh.read()).hexdigest()
        except (KeyError, OSError, zipfile.BadZipFile):
            got = None
        if got != meta["exe_sha256"]:
            out.append(f"the LAUNCH line's exe={meta['exe']} exe_sha256={meta['exe_sha256'][:12]}... is not that file "
                       f"of {os.path.basename(zp)} ({'missing' if got is None else got[:12] + '...'}): the launch "
                       "smoked another build than this zip (final-10 B H1, H2)")
    for k in ("commit", "platform", "workbench"):
        if k in meta and meta[k] != eff.get(k):
            out.append(f"the LAUNCH line says {k}={meta[k]}, but its SMOKE_EFFECTIVE says {k}={eff.get(k)}")
    if eff.get("platform") != "Windows":
        out.append(f"the LAUNCH record ran a platform={eff.get('platform')} build; the jam takes the Win64 "
                   "zip, so the launch is its Windows smoke")
    if eff.get("workbench") != "0":
        out.append(f"the LAUNCH record ran a workbench={eff.get('workbench')} build: the zip is the submission "
                   "package, never the -Workbench tester package (final-10 B H2; check_pr agrees)")
    dh = DAILY_HOST.match(daily or "")
    lh = re.match(r"([^/]+)/", meta.get("host", ""))
    if dh and lh and host_name(dh.group("node")) == host_name(lh.group(1)):
        out.append(f"the LAUNCH record ran on {lh.group(1)}, the packaging machine itself: download the zip and "
                   "launch it on another machine, which has no editor or SDK to hide a missing runtime prerequisite "
                   "(card 0.4b; final-10 A M2)")
    if sha and not same_sha(eff.get("commit", ""), sha):
        out.append(f"the launched game was compiled from {eff.get('commit')}, not the Build commit {sha}")
    if not full:
        out.append(f"Build commit {sha or '<none>'} is not a commit in this clone, so the launched game's "
                   "values cannot be checked: fetch main")
    else:
        probs = [tree_err] if tree_err else bake_preset.effective_problems(tree, eff, complete=gate == "G4")
        out += [f"the launched game's SMOKE_EFFECTIVE fails `bake_preset.py effective"
                f"{' --complete' if gate == 'G4' else ''}` on {sha}: {p}" for p in probs[:6]]
    return out


def build_bake_problems(lines, preset, root=ROOT):
    """Final-7 dry run B H8: the pasted bake line proves nothing about the zip. The Build commit must exist in this
    clone, be on the checked-out branch, and its own tree must pass `bake_preset check --record` (complete) for the
    record's preset, so a package built before the bake PR merged, or with a drifted default, fails the G4 record."""
    import tempfile
    b = re.match(r"\s*([0-9a-f]{7,40})\s*\|", lines.get("build", ""))
    if not b:
        return []   # gate_output_problems already reports the Build line
    sha = b.group(1)
    full = git_out(root, "rev-parse", "--verify", "--quiet", sha + "^{commit}")
    if not full:
        return [f"G4 Build commit {sha} is not a commit in this clone: fetch main and run --gate-record from it"]
    full = full.decode().strip()
    if git_out(root, "merge-base", "--is-ancestor", full, "HEAD") is None:
        return [f"G4 Build commit {sha} is not on the checked-out branch: check out main (the zip ships from main)"]
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bake_preset
    with tempfile.TemporaryDirectory() as tmp:
        err = extract_commit(root, full, tmp)
        if err:
            return [f"G4 Build commit {sha}: {err}"]
        try:
            probs, _ = bake_preset.check(tmp, preset, complete=True)
        except (OSError, ValueError) as e:
            probs = [str(e)]
    return [f"G4 Build commit {sha} fails `bake_preset check --record` for {preset}: {p}" for p in probs[:5]] + \
        ([f"... and {len(probs) - 5} more"] if len(probs) > 5 else [])


def risk_count(brief_text):
    sec = re.search(r"^## Top risks.*?$(.*?)(?=^## |\Z)", brief_text or "", re.S | re.M)
    return len(table_rows(sec.group(1))) if sec else 0


# Dry run B C2: failure in any case, a failing tool summary ("submission_check: 2 problem(s)", "errors=3"), exit != 0
FAIL_WORDS = re.compile(r"(?i)\bfail(?:ed|s|ure|ing)?\b(?!-)|\b[1-9]\d*\s+problem\(s\)|\berrors=[1-9]|\bexit(?:\s+code)?\s*[:=]?\s*[1-9]")
# MVP items due at each gate (pipeline/roles/producer.md Gates). From G2 on every item is re-checked: a G1 item that
# breaks later is still an MVP failure (docs/jam-brief.md: "done" when all are true; never cut).
# GDD SH1.0 (D-new-sh10-g1): read from the brief's [G<n>] tags, never a fixed list of numbers.
GATE_MVP = gate_mvp(ROOT)
PLAYTHROUGH_OUT = re.compile(r"^\s*PASS:\s*PLAYTHROUGH\s+([0-9a-f]{7,40}):\s*(G[1-4]):\s*\S.*\bpassed\s*$")
# The DAILY record line of the Build commit (tools/ue_run.py daily, SMOKE_REPEAT=5): ties repeat boots to the build (A M3)
REPEAT_OUT = re.compile(r"^\s*DAILY ([0-9a-f]{7,40}) \|.*\bsmoke=PASS\(\d+ map\(s\), repeat (\d+)/(\d+)\)")
REPEAT_MIN = 5   # pipeline/roles/qa-build.md: SMOKE_REPEAT=5 before each gate
# ui_check.py prints `ui_check ci --release: PASS ...` for the release run and `ui_check ci: PASS ...` for the plain one.
# G2-G4 need the release run (every UI input exists, no PENDING sound; final-7 B H6). G1 is the GDD 1.3 section 12A
# first playable, before the Nov 13 player screens, so its record may paste the plain run (final-7 A H1).
UI_CI_RELEASE = re.compile(r"\bui_check ci --release: PASS \(0 problem\(s\)\)")
UI_CI_PLAIN = re.compile(r"\bui_check ci: PASS \(0 problem\(s\)\)")
UI_VERDICT_RELEASE = re.compile(r"\bui_check ci --release: PASS\b")
UI_VERDICT_ANY = re.compile(r"\bui_check ci(?: --release)?: PASS\b")


def ui_gate_problem(text, gate, verdict=False):
    """The UI check line a gate needs, or None when it is there."""
    release, plain = (UI_VERDICT_RELEASE, UI_VERDICT_ANY) if verdict else (UI_CI_RELEASE, UI_CI_PLAIN)
    where = "Verdicts 'UI'" if verdict else "Gate checks"
    if release.search(text or ""):
        return None
    if gate == "G1" and plain.search(text or ""):
        return None
    if gate != "G1" and plain.search(text or ""):
        return (f"{where} has the plain `ui_check ci` line; {gate or 'this gate'} needs `ui_check ci --release: PASS"
                " (0 problem(s))` (every UI input exists, no PENDING sound)")
    return f"{where} has no `ui_check ci --release: PASS (0 problem(s))` line (G1: plain `ui_check ci` is enough)"
# submission_check.py zip's PASS line, with the zip's commit and sha256 (dry run B H7, A M3)
ZIP_OUT = re.compile(r"\bPASS: (\S+\.zip) config=Development platform=Win64 commit=([0-9a-f]{7,40}) sha256=([0-9a-f]{64})\b")
UPLOAD_SHA = re.compile(r"\bsha256=([0-9a-f]{64})\b")
OUTCOMES = ("Pass", "Pass with named exceptions", "Miss")   # pipeline/templates/gate-record.md, exactly (B C2)
# The whole outcome value: one exact word, then only the exceptions list (after ': ') or the cut (after ' → ')
OUTCOME_LINE = re.compile(r"(Pass)|(Pass with named exceptions)(?::\s+\S.*)?|(Miss)(?:\s+→\s+\S.*)?")


def gate_mvp_problems(text, gate):
    """Every MVP item due at the gate is listed as 'MVP <n> pass' (or '<n> pass'), with a build record or test link."""
    out = []
    got = {}
    for m in re.finditer(r"(?<![#\w-])(?:MVP\s*)?(\d{1,2})\s*[:=]?\s+([A-Za-z][\w/-]*)", text or ""):
        got.setdefault(int(m.group(1)), []).append(m.group(2).lower())
    bad = sorted(n for n, vs in got.items() if any(v != "pass" for v in vs))
    if bad:
        out.append("MVP item " + ", ".join(map(str, bad)) + " is not 'pass'")
    missing = [n for n in gate_mvp(ROOT).get(gate, []) if n not in got]
    if missing:
        out.append(f"MVP items for {gate} leave out " + ", ".join(map(str, missing))
                   + " (pipeline/roles/producer.md Gates; write 'MVP <n> pass' for each)")
    if got and not re.search(r"#\d+|https?://\S+", text or ""):
        out.append("MVP items link no build record or test (#n or a URL)")
    return out


def same_sha(a, b):
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


# Final-8 A C1 / B H1: the gate rule reads the DAILY line's step results and its `Not checked` entries by name
# (tools/ue_run.py NOT_CHECKED), keyed on what each gate requires, never on keywords in the entry text.
# Steps every gate needs as PASS: the gate's own build, tests, package and smokes ran on the Build commit.
GATE_DAILY_STEPS = ("clean-tree", "build", "test", "validate", "package", "smoke", "display", "settings")
# Switches with a gate in tools/ue/daily-checklist.md "Switches by gate": from that gate on, the entry is a P1 bug
# ("Past its gate, that entry is a P1 bug"), so a plain Pass fails; Pass with named exceptions lists it in Open
# P0/P1. Every other entry daily writes (Shipping smoke, REF_HOST, VERIFY tags, skipped display modes, ...) is a
# switch the docs leave off or an open decision, and never fails a gate.
GATE_SWITCHES = {"input": (1, "SMOKE_REQUIRE_INPUT=1 from Day 0"), "gamepad": (1, "SMOKE_REQUIRE_GAMEPAD=1 from G1"),
                 "client-test": (2, "CLIENT_TESTS=1 from G2"),
                 "restart-cycles": (3, "SMOKE_RESTART_CYCLES=5 from G3"),
                 "art-bootstrap": (2, "anchor art (card 0.10b) by G2, so the smoke's art checks block")}
# Entries that never belong to a gate build: the Day-1 bootstrap runs before cards 0.5 and 0.6 (tools/ue_run.py)
GATE_NEVER = {"bootstrap-tests", "bootstrap-smoke", "map-list"}


def daily_gate_problems(line, gate):
    """Hard problems with the Build commit's DAILY line for this gate (steps not PASS, entries daily never writes)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import ue_run
    out = []
    head, _, nc = line.partition(" | Not checked:")
    steps = dict(re.findall(r"\b([a-z-]+)=(PASS|FAIL|NOT RUN|not run)\b", head))
    bad = [f"{k}={steps.get(k, '<missing>')}" for k in GATE_DAILY_STEPS if steps.get(k) != "PASS"]
    if bad:
        out.append("Repeat boots DAILY line has " + ", ".join(bad) + ": every gate needs " + ", ".join(GATE_DAILY_STEPS)
                   + " = PASS on the Build commit")
    for e in ue_run.not_checked_entries(nc):
        kind = ue_run.not_checked_kind(e)
        if kind is None:
            out.append(f"Repeat boots 'Not checked' entry '{e[:60]}' is not one `ue_run.py daily` writes: paste the "
                       "DAILY line as printed")
        elif kind in GATE_NEVER:
            out.append(f"Repeat boots 'Not checked' has '{e[:60]}': a gate build never runs in the Day-1 bootstrap")
    return out


def daily_switch_due(line, gate):
    """Not checked entries whose switch is due by this gate (each is a P1 bug past its gate)."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import ue_run
    n = int(gate[1]) if gate and re.fullmatch(r"G[1-4]", gate) else 4
    out = []
    for e in ue_run.not_checked_entries(line.partition(" | Not checked:")[2]):
        kind = ue_run.not_checked_kind(e)
        if kind in GATE_SWITCHES and n >= GATE_SWITCHES[kind][0]:
            out.append(f"'{e}' ({GATE_SWITCHES[kind][1]})")
    return out


def gate_output_problems(lines, gate):
    """PLAYTHROUGH, Repeat boots and Gate checks hold the tools' own PASS lines, for this gate and this build. The
    zip line's commit is the Build commit, and its sha256 is the uploaded file's (dry run B H7, A M3)."""
    out = []
    build = re.match(r"\s*([0-9a-f]{7,40})\s*\|\s*([^|]*?)\s*\|", lines.get("build", ""))
    if not re.search(r"\|\s*Development\s*$", lines.get("build", "")):
        out.append("Build config is not Development (the jam takes the Development package, D25)")
    if not build:
        out.append("Build is not '<commit sha> | <packaged zip name> | Development'")
    pt = PLAYTHROUGH_OUT.match(lines.get("playthrough", ""))
    if not pt:
        out.append("PLAYTHROUGH is not the `ue_run.py playthrough-check --gate G<n>` output "
                   "('PASS: PLAYTHROUGH <sha>: G<n>: ... passed')")
    elif build and not same_sha(pt.group(1), build.group(1)):
        out.append(f"PLAYTHROUGH is for {pt.group(1)}, not the Build commit {build.group(1)}")
    rb = REPEAT_OUT.match(lines.get("repeat boots", ""))
    if not rb or rb.group(2) != rb.group(3) or int(rb.group(3)) < REPEAT_MIN:
        out.append(f"Repeat boots is not the Build commit's `DAILY <sha> | ... smoke=PASS(<n> map(s), repeat N/N)` "
                   f"record line with N >= {REPEAT_MIN} (SMOKE_REPEAT={REPEAT_MIN})")
    elif build and not same_sha(rb.group(1), build.group(1)):
        out.append(f"Repeat boots is the DAILY line of {rb.group(1)}, not the Build commit {build.group(1)}")
    if rb:
        out += daily_gate_problems(lines.get("repeat boots", ""), gate)
    gc = lines.get("gate checks", "")
    ui = ui_gate_problem(gc, gate)
    if ui:
        out.append(ui)
    z = ZIP_OUT.search(gc)
    if not z:
        out.append("Gate checks has no `submission_check.py zip` PASS line "
                   "('PASS: <zip> config=Development platform=Win64 commit=<sha> sha256=<64 hex>')")
    else:
        if build and not same_sha(z.group(2), build.group(1)):
            out.append(f"the zip check is for commit {z.group(2)}, not the Build commit {build.group(1)}")
        if build and os.path.basename(z.group(1)) != os.path.basename(build.group(2)):
            out.append(f"the zip check is for {z.group(1)}, not the Build zip {build.group(2)}")
        upload = next((v for k, v in lines.items() if k.endswith("test upload (g1 on)")), "")
        up = UPLOAD_SHA.search(upload)
        if not up:
            out.append("the jam-page upload line has no sha256=<64 hex> of the uploaded zip")
        elif up.group(1) != z.group(3):
            out.append("the uploaded file's sha256 is not the checked zip's sha256: upload the zip this gate checked")
    return out


def exception_owner_problems(open_p01, outcome):
    """Each open P0/P1 issue (#n) is named with an owner and the hour it is fixed or cut (gate-record.md)."""
    out = []
    if not open_p01 or re.fullmatch(r"\s*none\s*", open_p01, re.I) or PLACEHOLDER.search(open_p01):
        return out
    parts = re.split(r"[|;]", open_p01) + re.split(r"[|;]", outcome or "")
    for n in sorted(set(re.findall(r"#(\d+)", open_p01)), key=int):
        mine = [x for x in parts if re.search(rf"#{n}\b", x)]
        if not any(re.search(r"\bowner\s+\w", x, re.I) and re.search(r"\b(?:by|until)\s+\S*\d{1,2}:\d{2}", x, re.I)
                   for x in mine):
            out.append(f"open P0/P1 #{n} has no owner and fix-or-cut hour ('#{n} owner <name> by HH:MM')")
    return out


def named_exception_problems(lines, outcome_text=""):
    """Pass with named exceptions names at least one, and each has an owner and an hour (gate-record.md; A M2)."""
    out = []
    named = bool(re.search(r"#\d+[^|;]*\bowner\s+\w", outcome_text.partition(":")[2], re.I))
    p01 = lines.get("open p0/p1", "")
    if p01 and not re.fullmatch(r"\s*none\s*", p01, re.I) and not PLACEHOLDER.search(p01):
        named = True
    for part in re.split(r"[|;,]", lines.get("playtests for this gate", "")):
        if re.search(r"\bP\d+\b[^|;,]*?\bfail", part, re.I):
            named = True
            if not (re.search(r"\bowner\s+\w", part, re.I) and re.search(r"\b(?:by|until)\s+\S*\d{1,2}:\d{2}", part, re.I)):
                out.append(f"named exception '{part.strip()[:40]}' has no 'owner <name> by HH:MM'")
    for part in lines.get("verdicts", "").split("|"):
        if re.search(r"\bfail\b", part, re.I):
            named = True
            slot = (re.match(r"\s*(\w+)", part) or [None, "verdict"])[1]
            mine = [x for x in re.split(r"[|;]", outcome_text.partition(":")[2]) if re.search(rf"\b{slot}\b", x, re.I)]
            if not any(re.search(r"\bowner\s+\w", x, re.I) and re.search(r"\b(?:by|until)\s+\S*\d{1,2}:\d{2}", x, re.I)
                       for x in mine + [part]):
                out.append(f"named exception '{slot} verdict fail' has no 'owner <name> by HH:MM' in the outcome "
                           "(final-7 B M9)")
    if not named:
        out.append("'Pass with named exceptions' names no exception (an open P0/P1, a playtest fail or a verdict fail); "
                   "write 'Pass'")
    return out


def gate_record_problems(record, root=ROOT, brief_text=None, records=None):
    """A gate record has every template line, filled, and one 'fired yes/no' per Top risks row. records: the machine
    record lines (the CLI always passes them; None skips machine_record_problems, for unit tests of the rest)."""
    out = []
    lines = {}
    tkeys = {k.lower() for k, _ in gate_template(root)} | {"final upload", "baked preset"}
    for ln in record.splitlines():
        k, _, v = ln.partition(":")
        if _:
            key = k.strip().lower()
            if key in lines and key in tkeys:   # B M9: a second line per key is never ignored
                out.append(f"gate record has two '{k.strip()}:' lines; one line per key")
            lines.setdefault(key, v.strip())
    for key, tmpl in gate_template(root):
        v = lines.get(key.lower())
        if v is None:
            out.append(f"gate record has no '{key}:' line")
        elif not re.search(r"\w", v) or v == tmpl or PLACEHOLDER.search(v):
            out.append(f"gate record '{key}:' is empty or still the template")
    # The submission is the Development package (D25, D-new-ship-required): no SHIPPING line is required.
    outcome = lines.get("proposed outcome", "").strip()
    gate_id = (re.match(r"\s*(G[1-4])\b", lines.get("gate", "")) or [None, None])[1]
    if gate_id == "G4":   # a practice repo never closes G4 (tools/practice.py)
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import practice
        if practice.is_practice(root):
            out.append(practice.blocked("closing G4 (the gate record)", root))
    om = OUTCOME_LINE.fullmatch(outcome)
    if outcome and not om and not PLACEHOLDER.search(outcome):
        out.append(f"gate record 'Proposed outcome: {outcome[:40]}' is not exactly one of: " + ", ".join(OUTCOMES)
                   + " (dry run B C2: any other spelling fails)")
    late = re.search(r"\blate by\s+(\d+(?:\.\d+)?)\s*h\b", lines.get("gate", ""))
    hours = float(late.group(1)) if late else None
    # Final-7 B M5: the lateness is computed from the record's own due and closed times, and due is the Clock's time
    # for this gate; a typed 'late by' that disagrees fails, and the cut rule reads the computed hours.
    due_m = re.search(r"\bdue\s+(\S+)", lines.get("gate", ""))
    closed_m = re.search(r"\bclosed\s+(\S+)", lines.get("gate", ""))
    due_t = parse_time(due_m.group(1)) if due_m else None
    closed_t = parse_time(closed_m.group(1)) if closed_m else None
    if gate_id and brief_text and due_t:
        want = parse_time((clock(brief_text) or {}).get(gate_id) or "")
        if want and want != due_t:
            out.append(f"gate record says {gate_id} was due {due_m.group(1)}, but the Clock in docs/jam-brief.md has "
                       f"{(clock(brief_text) or {}).get(gate_id)}")
    if due_t and closed_t:
        real = max(0.0, (closed_t - due_t).total_seconds() / 3600)
        if hours is None or abs(hours - real) > 0.25:
            out.append(f"gate record 'late by' says {late.group(1) + ' h' if late else 'nothing'}, but due "
                       f"{due_m.group(1)} to closed {closed_m.group(1)} is {real:.2f} h: write 'late by {real:.1f} h'")
        hours = real
    elif not PLACEHOLDER.search(lines.get("gate", "")) and lines.get("gate"):
        out.append("gate record 'Gate:' needs 'due <ISO time> | closed <ISO time>' so the lateness can be computed")
    if hours is not None and hours > 2 and re.match(r"\s*no\b", lines.get("cut fired", ""), re.I):
        out.append(f"gate is late by {hours:g} h (over 2 h fires the next cut, gate-record.md), but "
                   "'Cut fired:' says no")
    outcome_text, outcome = outcome, (om.group(1) or om.group(2) or om.group(3) if om else "")
    if outcome in OUTCOMES[:2]:
        # A failing MVP item (an APPROVED_P0 feature) or a FAIL in the gate's own checks is never a named exception.
        # Dry run A H2 / B C2: the lines must be the real tool output, every MVP item due at the gate must say pass,
        # failure words are matched in any case, and a failing summary like "2 problem(s)" counts as a FAIL.
        hard = []
        hard += gate_mvp_problems(lines.get("mvp items for this gate", ""), gate_id)
        for k in ("mvp items for this gate", "playthrough", "repeat boots", "gate checks"):
            if FAIL_WORDS.search(lines.get(k, "")):
                hard.append(f"{k} shows a failure")
        hard += gate_output_problems(lines, gate_id)
        pt = lines.get("playtests for this gate", "")
        if re.search(r"\binsufficient\b", pt, re.I):
            hard.append("a playtest is insufficient (pipeline/qa/playtests.md: insufficient never passes a gate)")
        if re.search(r"\bP[124]\b[^|,;]*?\bfail", pt, re.I):
            hard.append("a P1, P2 or P4 playtest fails (pipeline/qa/playtests.md: it blocks the gate)")
        if not re.search(r"\bP\d+\b[^|,;]*?\bpass\b", pt, re.I):
            hard.append("Playtests names no 'P<n> pass' result")
        # final-7 B M7: "P1 not run", "P1 broken", "P3 crashed" are not results; each P<n> is pass, fail or insufficient
        for pm in re.finditer(r"\b(P\d+)\b\s*[:=-]?\s*([A-Za-z/]+(?:\s+run)?)", pt):
            if pm.group(2).lower() not in ("pass", "fail", "insufficient"):
                hard.append(f"playtest {pm.group(1)} reads '{pm.group(2)}'; each playtest is pass, fail or "
                            "insufficient (pipeline/qa/playtests.md)")
        if hard:
            out.append("gate record proposes Pass, but " + "; ".join(hard)
                       + ": a P0 gate FAIL cannot be a named exception; fix it or write 'Miss'")
        out += exception_owner_problems(lines.get("open p0/p1", ""), outcome_text)
    if outcome == "Pass with named exceptions":
        out += named_exception_problems(lines, outcome_text)
        due = daily_switch_due(lines.get("repeat boots", ""), gate_id)
        p01 = lines.get("open p0/p1", "")
        if due and (not p01 or re.fullmatch(r"\s*none\s*", p01, re.I)):
            out.append("the Build commit's DAILY line lists " + ", ".join(due) + " under Not checked: each is a P1 "
                       "bug past its gate; list its issue under Open P0/P1 with 'owner <name> by HH:MM'")
    if outcome == "Pass":
        why = []
        if re.search(r"\bfail", lines.get("playtests for this gate", ""), re.I):
            why.append("a playtest reads fail")
        p01 = lines.get("open p0/p1", "")
        if p01 and not re.fullmatch(r"\s*none\s*", p01, re.I) and not PLACEHOLDER.search(p01):
            why.append("Open P0/P1 is not none")
        due = daily_switch_due(lines.get("repeat boots", ""), gate_id)
        if due:
            why.append("the Build commit's DAILY line lists " + ", ".join(due) + " under Not checked; past its gate "
                       "that is a P1 bug (tools/ue/daily-checklist.md): list it under Open P0/P1")
        if re.search(r"\bfail\b", lines.get("verdicts", ""), re.I):
            why.append("a discipline verdict reads fail")
        upload = next((v for k, v in lines.items() if k.endswith("test upload (g1 on)")), "")
        launched = re.search(r"re-downloaded and launched:\s*([^|]*)", upload)
        if not launched or launched.group(1).strip() != "yes":   # A H7: exactly yes; "not yet", "pending" fail
            why.append("the test upload was not re-downloaded and launched ('re-downloaded and launched: yes')")
        if why:
            out.append("gate record proposes Pass, but " + "; ".join(why)
                       + ": write 'Pass with named exceptions' with owners, or 'Miss'")
    verdicts = lines.get("verdicts")
    if verdicts is not None and not PLACEHOLDER.search(verdicts):
        for slot in ("design", "art", "UI", "tech"):
            m = re.search(rf"(?:^|\|)\s*{slot}\s+([^|]*)", verdicts, re.I)
            if not m or not re.search(r"\w", m.group(1)):
                out.append(f"gate record Verdicts has no '{slot}' verdict (each discipline signs its own part)")
            elif slot != "UI" and not re.search(r"\b(pass|fail)\b", m.group(1), re.I):
                out.append(f"gate record Verdicts '{slot}' says neither pass nor fail")
            elif slot == "UI":
                ui = ui_gate_problem(m.group(1), gate_id, verdict=True)
                if ui:
                    out.append("gate record " + ui)
    inc = lines.get("incidents since last gate")
    if inc is not None and not PLACEHOLDER.search(inc) and not re.fullmatch(r"\s*none\.?\s*", inc, re.I):
        for part in inc.split("|"):
            if not (re.search(r"#\d+", part) and re.search(r"\bcause=\w", part) and re.search(r"\bfollow-up=\S", part)):
                out.append(f"gate record Incidents entry '{part.strip()[:50]}' needs #n, cause= and follow-up=")
    pc = lines.get("process change")
    if pc is not None and not PLACEHOLDER.search(pc) and not re.fullmatch(r"\s*none\.?\s*", pc, re.I) \
            and not (re.search(r"#\d+", pc) and re.search(r"\bowner\s+\w", pc, re.I)):
        out.append("gate record 'Process change:' needs a card '#n, owner <role>' or 'none'")
    pt, gate = re.search(r"\b(G[1-4]):", lines.get("playthrough", "")), re.match(r"\s*(G[1-4])\b", lines.get("gate", ""))
    if pt and gate and pt.group(1) != gate.group(1):
        out.append(f"PLAYTHROUGH was checked for {pt.group(1)}, not {gate.group(1)}: run playthrough-check --gate {gate.group(1)}")
    if re.match(r"\s*G1\b", lines.get("gate", "")):
        out += butler_record_problems(record)
    if re.match(r"\s*G4\b", lines.get("gate", "")):
        up = parse_time(lines.get("final upload") or "")
        if up is None:
            out.append("G4 record has no 'Final upload: <jam-page time, ISO with offset>' line (D-new-clock)")
        elif brief_text:
            out += upload_problems(brief_text, up)
        out += baked_record_problems(lines, root)
    if records is not None:
        out += machine_record_problems(lines, gate_id, records, root)
    risks = lines.get("risks")
    if risks is not None and brief_text:
        parts = re.split(r"\|", risks)
        for n in range(1, risk_count(brief_text) + 1):
            hit = [x for x in parts if re.match(rf"\s*{n}\s+fired\s+(yes|no)\b", x, re.I)]
            if not hit:
                out.append(f"gate record Risks has no '{n} fired yes/no' for Top risks row {n}")
            elif re.match(rf"\s*{n}\s+fired\s+yes\b", hit[0], re.I) and not re.search(r"owner\s+\w", hit[0], re.I):
                out.append(f"gate record Risks row {n} fired yes but names no owner")
    return out


def latest_gate_record(data):
    """gh issue view --json comments -> body of the newest comment that starts 'Gate: G'."""
    # final-9 A M2: the template pastes the `--clock` line first, so the Gate: line may follow it
    recs = [(c.get("createdAt") or "", c.get("body") or "") for c in data.get("comments") or []
            if re.search(r"^\s*Gate:\s*G\d", c.get("body") or "", re.M)]
    return max(recs)[1] if recs else None


def stretch_problems(issues, root=ROOT):
    """No open Stretch card while an open card has a numeric MVP item. No human override (Josh, 11 Nov; it replaced
    the 'Stretch approved: <link>' exception, D-new-stretch-approval): stretch starts once every MVP card is closed."""
    cards = [(n, c, i.get("body") or "") for i, (n, c) in zip(issues, issue_cards(issues, root))]
    mvp_open = [n for n, c, _ in cards if re.match(r"(?:MVP\s*)?#?\d+\b", (c.get("MVP item") or "").strip())]
    if not mvp_open:
        return []
    return [f"#{n} is a Stretch card while MVP cards are open ({' '.join(f'#{x}' for x in mvp_open[:5])});"
            " close it; stretch waits until every MVP card is closed (no override)"
            for n, c, _ in cards if re.match(r"Stretch\b", (c.get("MVP item") or "").strip(), re.I)]


def status_problems(comments, now, root=ROOT, brief_text=None):
    fields = status_fields(root)
    g1 = parse_time((clock(brief_text) or {}).get("G1") or "") if brief_text else None
    upload = []
    if g1 and now >= g1 and not any(TEST_UPLOAD.search(c.get("body") or "") for c in comments):
        upload = ["no itch test upload on the tracker after G1: a line with 'upload', the link and"
                  " sha256=<hash> (day0-cards.md 0.4b, D-new-upload-g1)"]
    recent = []
    for c in comments:
        t = parse_time(c.get("createdAt") or "")
        if t and re.search(r"^Accepted since last status", c.get("body") or "", re.M):
            recent.append((t, c["body"]))
    if not recent:
        return ["no status line ('Accepted since last status ...') on the tracker"] + upload
    t, body = max(recent)
    out = []
    age = (now - t).total_seconds() / 3600
    if age > STATUS_MAX_H:
        out.append(f"last status line is {age:.1f} h old (limit {STATUS_MAX_H} h)")
    for f in fields:
        if f.lower() not in body.lower():
            out.append(f"last status line has no '{f}' field")
    out += status_value_problems(body)
    out += will_miss_problems(body, comments, now, brief_text)
    if brief_text:
        out += retro_problems(comments, now, brief_text)
    return out + upload


def will_miss_problems(status_body, comments, now, brief_text=None):
    """'Next gate: will miss' needs a 'Cut proposed: <cut-list item>' comment since the last gate time."""
    v = field_value(status_body, "Next gate") or ""
    if not re.match(r"will miss\b", v, re.I):
        return []
    c = clock(brief_text) or {} if brief_text else {}
    past = [t for t in (parse_time(c.get(g) or "") for g in GATES) if t and t <= now]
    since = max(past) if past else None
    for x in comments:
        t = parse_time(x.get("createdAt") or "")
        if CUT_PROPOSED.search(x.get("body") or "") and (since is None or (t and t >= since)):
            return []
    return ["status line says 'will miss' but no tracker comment since the last gate has 'Cut proposed: <next"
            " cut-list item>' for the scope decision-maker (producer.md Cut rule)"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card", nargs="?", help="card file ('-' for stdin)")
    ap.add_argument("--title", help="issue title, for issue-form bodies")
    ap.add_argument("--event", action="store_true", help="read the issue from $GITHUB_EVENT_PATH")
    ap.add_argument("--json-stdin", action="store_true", help="read {title, body} JSON from stdin (gh issue view --json)")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--clock", action="store_true", help="check the jam-brief Clock and report gate lateness")
    ap.add_argument("--people", action="store_true", help="check the People and Team hours tables")
    ap.add_argument("--hours", action="store_true", help="open cards (JSON stdin) vs Team hours on --day")
    ap.add_argument("--day", type=int, choices=[1, 2, 3, 4], help="jam day for --hours")
    ap.add_argument("--lanes", action="store_true", help="open cards (JSON stdin) share no lane, .umap or lock")
    ap.add_argument("--status", action="store_true", help="tracker comments (JSON stdin) have a fresh status line")
    ap.add_argument("--queue", action="store_true", help="cards in review (JSON stdin): at most QUEUE_MAX per human")
    ap.add_argument("--overrun", action="store_true", help="cards in doing (JSON stdin): time in doing vs Budget")
    ap.add_argument("--hardstop", action="store_true", help="commits on main inside the Clock's hard stop window")
    ap.add_argument("--tracker", action="store_true", help="tracker issue (JSON stdin, body): one row per MVP item")
    ap.add_argument("--gate-record", action="store_true",
                    help="tracker comments (JSON stdin): newest 'Gate: G<n>' comment has every template line")
    ap.add_argument("--records", action="append", metavar="FILE",
                    help="with --gate-record: another machine's record file, read with this machine's "
                         "Saved/Logs/pipeline/daily-records.txt; repeat it per machine (the Windows launch machine)")
    ap.add_argument("--since", help="ISO time; --hardstop looks at commits after it (default 24 h before now)")
    ap.add_argument("--gitlog", help="file of git log lines for --hardstop (tests)")
    ap.add_argument("--uploaded", help="ISO jam-page time of the final upload, with --clock")
    ap.add_argument("--brief", help="jam brief to read (default docs/jam-brief.md)")
    ap.add_argument("--now", help="ISO time to use as now (tests)")
    ap.add_argument("--blocked-by", metavar="CARD",
                    help="print the cards that wait on CARD (Day-0 After, filed cards with --issues), one per line")
    ap.add_argument("--issues", metavar="FILE", help="with --blocked-by: gh issue list JSON of open cards ('-' = stdin)")
    ap.add_argument("--needs-human", action="store_true",
                    help="gh issue list JSON (stdin, with labels and comments): the needs-human queue")
    a = ap.parse_args(argv)
    if a.needs_human:
        try:
            now = parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
            if now is None:
                print(f"check_card: --now {a.now!r} is not an ISO time with a UTC offset", file=sys.stderr)
                return 2
            lines, probs = needs_human_queue(json.load(sys.stdin), now)
        except (ValueError, AttributeError) as e:
            print(f"check_card: {e}", file=sys.stderr)
            return 2
        for ln in lines:
            print(ln)
        for pr in probs:
            print(f"[needs-human] {pr}")
        print(f"check_card --needs-human: {len(lines)} waiting, {len(probs)} problem(s)")
        return 1 if probs else 0
    if a.blocked_by:
        try:
            issues = []
            if a.issues:
                issues = json.load(sys.stdin) if a.issues == "-" else json.loads(read(a.issues))
            waiting = blocked_by(a.blocked_by, a.root, issues)
        except (OSError, KeyError, ValueError, AttributeError) as e:
            print(f"check_card: {e}", file=sys.stderr)
            return 2
        for _, text in waiting:
            print(text)
        return 0
    title = a.title
    stdin_modes = (a.hours, a.lanes, a.status, a.queue, a.overrun, a.tracker, a.gate_record)
    modes = (a.clock, a.people, a.hardstop) + stdin_modes
    if sum(1 for x in stdin_modes if x) > 1:
        print("check_card: --hours, --lanes, --status, --queue, --overrun, --tracker and --gate-record each read"
              " their own stdin; run one at a time", file=sys.stderr)
        return 2
    if any(modes):
        return board_main(a)
    try:
        if a.event:
            with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
                issue = json.load(f).get("issue") or {}
            body, title = issue.get("body") or "", issue.get("title")
        elif a.json_stdin:
            issue = json.load(sys.stdin)
            body, title = issue.get("body") or "", issue.get("title")
        elif a.card == "-":
            body = sys.stdin.read()
        elif a.card:
            body = read(a.card)
        else:
            ap.print_usage(sys.stderr)
            return 2
        found = problems(body, a.root, title)
    except (OSError, KeyError, ValueError, AttributeError, IndexError) as e:
        print(f"check_card: {e}", file=sys.stderr)
        return 2
    for kind, msg in found:
        print(f"[{kind}] {msg}")
    print(f"check_card: {len(found)} problem(s)")
    return 1 if found else 0


def board_main(a):
    try:
        text = read(a.brief or os.path.join(a.root, "docs", "jam-brief.md"))
        now = parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
        if now is None:
            raise ValueError(f"--now '{a.now}' is not ISO 8601 with an offset")
        found, info = [], []
        if a.clock:
            found += clock_problems(text)
            found += clock_install_problems(a.root, text, now)
            info += cut_report(text, gate_tags(a.root), now)
            found += [ln for ln in info if ln.startswith("CUT FIRES")]
            if a.uploaded:
                up = parse_time(a.uploaded)
                if up is None:
                    raise ValueError(f"--uploaded '{a.uploaded}' is not ISO 8601 with an offset")
                found += upload_problems(text, up)
        if a.people:
            found += people_problems(text)
            info += people_warnings(text)
        if a.hardstop:
            since = parse_time(a.since) if a.since else now - dt.timedelta(hours=24)
            if since is None:
                raise ValueError(f"--since '{a.since}' is not ISO 8601 with an offset")
            lines = read(a.gitlog).splitlines() if a.gitlog else git_log_lines(a.root)
            found += hardstop_problems(lines, text, since)
        if a.hours or a.lanes or a.status or a.queue or a.overrun or a.tracker or a.gate_record:
            data = json.load(sys.stdin)
        if a.hours:
            if not a.day:
                raise ValueError("--hours needs --day 1-4")
            found += hours_problems(data, text, a.day, a.root)
        if a.lanes:
            found += lanes_problems(data, a.root)
            found += stretch_problems(data, a.root)
        if a.status:
            found += status_problems(data.get("comments") or [], now, a.root, text)
            found += submission_status(text, now, a.root)
        if a.status or a.tracker:
            if "body" not in data:
                found.append("tracker body not read; use gh issue view <tracker #> --json body,comments")
            else:
                found += tracker_problems(data["body"], a.root)
        if a.gate_record:
            rec = latest_gate_record(data)
            recs = []
            files = [os.path.join(a.root, RECORD_FILE)]   # final-10 A M1: --records adds a machine, never replaces this one
            for f in a.records or []:
                if os.path.abspath(f) not in map(os.path.abspath, files):
                    files.append(f)
            for f in files:
                try:
                    recs += read(f).splitlines()
                except OSError:
                    pass
            found += (gate_record_problems(rec, a.root, text, recs) if rec is not None
                      else ["no 'Gate: G<n>' comment on the tracker (pipeline/templates/gate-record.md)"])
        if a.queue:
            i, p = queue_report(data, a.root)
            info, found = info + i, found + p
        if a.overrun:
            i, p = overrun_report(data, now, a.root)
            info, found = info + i, found + p
    except (OSError, KeyError, ValueError, AttributeError, subprocess.CalledProcessError) as e:
        print(f"check_card: {e}", file=sys.stderr)
        return 2
    for ln in info:
        if not ln.startswith("CUT FIRES"):
            print(ln)
    for p in found:
        print(f"[plan] {p}")
    print(f"check_card: {len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

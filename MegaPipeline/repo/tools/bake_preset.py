#!/usr/bin/env python3
"""Bake the approved workbench preset into the shipped defaults (decision D-new-workbench-debug). Stdlib only.

The workbench (GDD B section 10: toggles, sliders, presets, scenarios, overlay) is compiled only into
editor and dev builds. The submitted Development package has no workbench, so the values the team picked in
it must become plain defaults. This tool writes them, so the change goes through a normal PR with the diff.

Where values go:
  params  each `F<Comp>Tuning` header default that carries a marker comment, e.g.
              float MoveSpeed = 600.f;   // bake: CORE-01.move_speed
          (pipeline/unreal/gameplay-code.md; key = manifest feature ID + one of its `parameters`)
  flags   `default_enabled` in docs/feature-manifest.json, and the C++ flag default marked
              { EFeatureId::UMB_02, false },   // bake: UMB-02.enabled
          A flag may differ from its manifest default only when the record is implementation_authorized.
  stamp   pipeline/qa/baked.json: preset ID, export hash, every baked value. The check reads it.

Workbench config export (card 0.26 writes it; Saved/Workbench/config-<preset>.json):
  {"kind": "workbench_config", "preset": "T-03", "commit": "<sha>", "manifest_version": "B1.0-m1",
   "flags": {"UMB-03": true}, "params": {"CORE-01.move_speed": 640.0, "UMB-03.catch_window": 0.25}}
  The export lists every marked key in Source/ (a value left out would ship unreviewed).

Commands:
  bake EXPORT [--dry-run]       validate, write the values and the stamp, print the diff (--dry-run: diff only)
  check [--record FILE | --preset T-nn] [--complete]
                                every stamped value equals its marked default in Source/ and its flag default,
                                the manifest version is the stamped one, and (with --record) the gate record's
                                `Baked preset: T-nn` line names the stamped preset. A marked key not in the stamp
                                yet (a feature coded after the bake) passes the `defaults` rules instead; it is
                                listed, not failed (final-7 dry run A H4). --record and --complete are the G4 mode:
                                every marked key is in the stamp and every required key has a marker
  marker   every flagged record's `<ID>.enabled` and every approved_parameters key of a built feature has a
           `// bake:` marker (dry run B H4). Required at G4 (check --record / --complete); before that the bake
           and CI list the missing ones, since the first bake (card 0.27, G2) runs before every P0 is coded
  shape    a `.enabled` marker sits on `true` or `false`, never a number; a parameter marker on a number; and the
           literal is the whole initializer (`= 350.f;`, `{ ID, false }`), never part of an expression such as
           `2 * 350.f` (final-7 dry run B H3, M2)
  ini      no `Config/**/*.ini` section names a config class that holds `// bake:` defaults (`UmbrellaTuning`, or any
           `UCLASS(Config...)` in a header with a marker): an ini line would override the shipped default at runtime,
           so the C++ default stays the one source of shipped values (defaults and check; final-7 dry run B H5)
  branch   a `// bake:` marker never sits inside a preprocessor conditional (`#if`, `#ifdef`, `#ifndef`, `#elif`,
           `#else`): the build that ships compiles one branch, and the checks read every line, so a marked
           value under `#if UMBRELLAELLA_WORKBENCH` with another value under `#else` shipped unchecked (final-8 B C1)
  one-src  the marked line is the only write of a baked member: no `.cpp`, `.h` or `.inl` under Source/ or Plugins/
           assigns it (`=`, `+=`, `*=`, ...) or sets it in a constructor initializer list (only the true branch of
           exactly `#if UMBRELLAELLA_WORKBENCH`, compiled out of the submission, may write a per-run copy), no
           other line sets a marked flag token to a literal, and no ini line names it
           or a Config UPROPERTY whose type is a struct holding a marker (final-8 B H2, H3). Final-10 B H3: no
           GetMutableDefault or const_cast of the tuning class, and no non-const copy of a marked struct (member,
           local, pointer) outside the UUmbrellaTuning class and Private/Tests/: gameplay reads the class default
           at the point of use, the object the hook reads at start and end of run
  defaults                      before the first bake: every `// bake:` default in Source/ passes the safety
                                rules below, each flag equals its manifest default_enabled, and each value the
                                sims read equals feel.json / encounter.json (CI runs it until baked.json exists;
                                dry run B M4, final-7 dry run B H3, H4)
  validate EXPORT [--shape-only]  the export's shape (and, without --shape-only, its IDs against the manifest)
  effective LOG... [--complete]   the packaged game's SMOKE_EFFECTIVE lines (tools/ue_run.py contract: one at=start,
                                at least one at=end, reflected `<Struct>.<Field>` mapped to keys by the marked line;
                                at the tree of the commit the game was built from, final-10): every live
                                value equals baked.json, else its `// bake:` default, else the manifest / GDD start;
                                every marked key is reported; --complete (G4) every required key. The runtime check
                                behind smoke.sh / smoke.ps1, check_pr and the G4 tie (final-9 B C1, H2, H3). The
                                static rules below stay: they fail before a package exists, and the startup read does
                                not see a write that happens after startup

Safety rules (validate, bake and check; GDD 1.3 sections 5, 5A, 12A):
  tuning  tools/tuning.py: a tunable param (approved min, max, step) sits in range and on the step; a fixed one
          equals its approved start, or (no approved entry, e.g. collider data) the value already in Source/
  off     an unapproved feature's flag is false, whatever the manifest default says (dry run B C1)
  start   a parameter other than its GDD start needs a counted DECIDED (<design owner>) row with `Overrides: <key>`:
          range and step are not an approval (GDD 1.3 line 226: no AI tunes a parameter; final-9 B H1)
  sim     each value the sims read (tuning.SIM_KEYS) equals feel.json / encounter.json: the export at bake time,
          the stamp after it, and the `// bake:` defaults before it (dry run B H4, final-7 dry run B H4)
  p0      an APPROVED_P0 flag may not be off: the shipped game is the full BASE baseline
  preset  the shipped preset is T-01 (BASE)
  A DECIDED row in docs/decisions.md whose text says `Overrides: <IDs>` lifts that rule for those IDs only. A
  DECIDED row that merely names an ID (D-new-p0-signoff, DEC-03) lifts nothing; manifest_check p0-on agrees.

Usage: python3 tools/bake_preset.py bake Saved/Workbench/config-T-01.json
       python3 tools/bake_preset.py check --record g4-record.md
Exit 0 = ok, 1 = problems, 2 = unreadable input.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = "docs/feature-manifest.json"
PRESETS = "pipeline/qa/presets.json"
STAMP = "pipeline/qa/baked.json"
SOURCE = "Source"
KEY = r"(?:[A-Z]+-\d{2}|QA-BASE)\.\w+"   # QA-BASE is a feature ID too (dry run B H2)
# The literal right before `// bake: KEY`, with only `;`, `}`, `,`, `)` and spaces between them.
MARKER = re.compile(r"(?P<lit>\btrue\b|\bfalse\b|(?<![\w.])[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?[fF]?)"
                    r"(?P<tail>[\s;},)]*//\s*bake:\s*(?P<key>" + KEY + r"))\b")
RECORD_LINE = re.compile(r"^\s*Baked preset:\s*(T-\d{2})\b", re.M)
PRESET_ID = re.compile(r"T-\d{2}")
DECISIONS = "docs/decisions.md"
SHIP_PRESET = "T-01"   # GDD 1.3 section 5A: "The full BASE preset loads all P0 values"; section 12A ships the baseline


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def parse_literal(lit):
    if lit in ("true", "false"):
        return lit == "true"
    return float(lit.rstrip("fF"))


def format_literal(old, value):
    """Write value in the old literal's style: bool, int, or float with the same f suffix."""
    if isinstance(value, bool) or old in ("true", "false"):
        return "true" if value else "false"
    suffix = old[-1] if old[-1] in "fF" else ""
    is_int = not suffix and not re.search(r"[.eE]", old)
    if is_int and float(value).is_integer():
        return str(int(value))
    text = repr(float(value))
    return text + suffix


def same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if a.is_integer() and b.is_integer():
        return a == b   # final-10 B M3: a whole number (the seed, a count) is exact; a relative margin let it drift by 20
    # a float32 printed by the game: its own precision (2^-23 relative), and never more than 1e-6 near zero
    return abs(a - b) <= max(1e-6, 1.2e-7 * max(abs(a), abs(b)))


def headers(root):
    base = os.path.join(root, SOURCE)
    out = []
    for d, _, files in os.walk(base):
        for f in files:
            if f.endswith((".h", ".hpp")):
                out.append(os.path.join(d, f))
    return sorted(out)


def marker_files(root):
    """Every C++ file under Source/ (headers and .cpp/.inl): a flag table in Harness/FeatureFlags.cpp holds markers
    as much as a header does, and defaults, bake and check all read the same files (final-9 A M4)."""
    base = os.path.join(root, SOURCE)
    out = []
    for d, _, files in os.walk(base):
        out += [os.path.join(d, f) for f in files if f.endswith((".h", ".hpp", ".cpp", ".inl"))]
    return sorted(out)


def markers(root):
    """{key: [(path, line index, match)]} for every `// bake:` marker under Source/."""
    found = {}
    for path in marker_files(root):
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        for i, ln in enumerate(lines):
            for m in MARKER.finditer(ln):
                found.setdefault(m.group("key"), []).append((path, i, m))
    return found


INIT_START = re.compile(r"(?:=|\{|,)\s*$")


def shape_problem(root, key, path, i, m):
    """Why one marker's literal is not a plain flag/number initializer, or None (final-7 dry run B H3, M2)."""
    lit, line = m.group("lit"), m.string
    where = f"{rel(root, path)}:{i + 1}"
    is_bool = lit in ("true", "false")
    if key.endswith(".enabled") and not is_bool:
        return (f"{key}: {where} sets the flag to {lit}; a flag default is `true` or `false` (a number would turn a "
                "P0 off or an experiment on unchecked)")
    if not key.endswith(".enabled") and is_bool:
        return f"{key}: {where} sets a parameter to {lit}; a parameter default is a number"
    before = line[:m.start("lit")]
    code = before.split("//", 1)[0]
    if not INIT_START.search(code):
        return (f"{key}: {where}: the marked literal {lit} is part of an expression; the default must be the "
                "literal alone (`= 350.f;` or `{ EFeatureId::X, false }`), or the shipped value differs from the "
                "checked one")
    if code.rstrip().endswith(","):
        brace = code.rfind("{")
        if brace < 0 or "(" in code[brace:]:
            return (f"{key}: {where}: the marked literal {lit} is an argument, not an initializer; write "
                    "`= <literal>;` or `{ EFeatureId::X, <literal> }`")
    return None


def shape_problems(root, found):
    return [p for k, hits in sorted(found.items()) for (path, i, m) in hits
            if (p := shape_problem(root, k, path, i, m))]


CONFIG_CLASS = re.compile(r"UCLASS\s*\(([^)]*)\)\s*class\s+(?:\w+_API\s+)?[UA](\w+)")
INI_SECTION = re.compile(r"^\s*\[\s*/Script/[\w.]*?\.?(\w+)\s*\]", re.M)
TUNING_CLASS = "UmbrellaTuning"


def config_classes(root):
    """Names (without the U prefix) of config classes that may carry shipped values: UmbrellaTuning, plus every
    UCLASS(Config...) declared in a header that holds a `// bake:` marker or a Config UPROPERTY of a marked struct."""
    names = {TUNING_CLASS}
    _, structs, _ = baked_members(markers(root))
    struct_rx = re.compile(r"UPROPERTY\s*\([^)]*\bConfig\b[^)]*\)\s*(?:\w+\s+)*?(" + "|".join(map(re.escape, sorted(structs)))
                           + r")\b") if structs else None
    for path in headers(root):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for spec, name in CONFIG_CLASS.findall(text):
            if re.search(r"\bConfig\b", spec) and ("// bake:" in text or "Tuning" in name
                                                    or (struct_rx and struct_rx.search(text))):
                names.add(name)   # final-8 B H2: any config class holding a marked struct, whatever its name
    return names


def ini_override_problems(root):
    """Final-7 dry run B H5: a `[/Script/UmbrellaElla.UmbrellaTuning]` section (one Project Settings edit writes it)
    overrides the baked C++ defaults at runtime, and no other check reads the ini."""
    cfg = os.path.join(root, "Config")
    if not os.path.isdir(cfg):
        return []
    names = {n.lower() for n in config_classes(root)}
    members = baked_members(markers(root))[0]
    member_rx = re.compile(r"\b(" + "|".join(map(re.escape, sorted(members))) + r")\s*=") if members else None
    out = []
    for d, _, files in os.walk(cfg):
        for f in sorted(files):
            if not f.lower().endswith(".ini"):
                continue
            path = os.path.join(d, f)
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            for m in INI_SECTION.finditer(text):
                if m.group(1).lower() in names:
                    line = text.count("\n", 0, m.start()) + 1
                    out.append(f"{rel(root, path)}:{line} has a [{m.group(0).strip()[1:-1]}] section: an ini value "
                               "overrides the baked C++ default at runtime. Remove it; shipped values come only from "
                               "the `// bake:` defaults (pipeline/unreal-rules.md)")
            # final-8 B H2: a baked member named on any ini line, in any section, is an override too
            if members:
                for n, ln in enumerate(text.splitlines(), 1):
                    if ln.strip().startswith(";"):
                        continue
                    hit = member_rx.search(ln)
                    if hit:
                        out.append(f"{rel(root, path)}:{n} sets {hit.group(1)} ({members[hit.group(1)]}): a config "
                                   "value overrides the baked C++ default at runtime. Remove it")
    return out


PP_OPEN = re.compile(r"^\s*#\s*(?:if|ifdef|ifndef)\b")
PP_ELSE = re.compile(r"^\s*#\s*(?:elif|else)\b")
PP_END = re.compile(r"^\s*#\s*endif\b")
INCLUDE_GUARD = re.compile(r"^\s*#\s*ifndef\s+(\w+)\s*$")


def branch_problems(root, found):
    """Final-8 B C1: a marker inside any preprocessor conditional is rejected. One branch ships; the checks read all
    of them. A classic include guard (`#ifndef X` then `#define X`) is not a conditional for this rule."""
    out = []
    files = sorted({path for hits in found.values() for path, _, _ in hits})
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        depth, guard, inside = 0, None, {}
        for i, ln in enumerate(lines):
            g = INCLUDE_GUARD.match(ln)
            if g and depth == 0 and guard is None and i + 1 < len(lines) and \
                    re.match(r"^\s*#\s*define\s+" + re.escape(g.group(1)) + r"\b", lines[i + 1]):
                guard = 1
                continue
            if PP_OPEN.match(ln):
                depth += 1
            elif PP_END.match(ln):
                if depth:
                    depth -= 1
                elif guard:
                    guard = 0
            inside[i] = depth > 0 or bool(PP_ELSE.match(ln))
        for key, hits in sorted(found.items()):
            for hp, i, _ in hits:
                if hp == path and inside.get(i):
                    out.append(f"{key}: {rel(root, path)}:{i + 1} is inside a preprocessor branch (#if/#else); a "
                               "shipped default is never conditional: move the marked line out of the block "
                               "(D-new-workbench-debug: IsFeatureEnabled and every default stay in every build)")
    return out


STRUCT_DECL = re.compile(r"\b(?:struct|class)\s+(?:\w+_API\s+)?(F\w+)\b")
MEMBER = re.compile(r"(\w+)\s*(?:=|\{)[^=]*$")


def baked_members(found):
    """({member name: key} for parameter markers (`float MoveSpeed = 350.f;   // bake: CORE-01.move_speed`),
    the struct names that hold a marker, {flag token: key} for flag markers (`{ EFeatureId::UMB_02, true }`))."""
    names, structs, flags = {}, set(), {}
    for key, hits in found.items():
        for path, i, m in hits:
            code = m.string[:m.start("lit")]
            if not key.endswith(".enabled"):
                mm = MEMBER.search(code.split("//", 1)[0])
                if mm:
                    names[mm.group(1)] = key
            else:
                fm = re.search(r"(\w+(?:::\w+)*)\s*,\s*$", code.split("//", 1)[0])
                if fm:
                    flags[fm.group(1)] = key
            with open(path, encoding="utf-8", errors="replace") as fh:
                head = "\n".join(fh.read().split("\n")[:i + 1])
            sd = list(STRUCT_DECL.finditer(head))
            if sd:
                structs.add(sd[-1].group(1))
    return names, structs, flags


def baked_fields(found):
    """Final-11 A H3: {field name: {struct name: key}} for parameter markers, so a write is matched on struct and
    field together (FAttackTuning::Cadence is COM-01.cadence, FOwlTuning::Cadence is OWL-01.cadence)."""
    out = {}
    for key, hits in found.items():
        if key.endswith(".enabled"):
            continue
        for path, i, m in hits:
            mm = MEMBER.search(m.string[:m.start("lit")].split("//", 1)[0])
            if not mm:
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                head = "\n".join(fh.read().split("\n")[:i + 1])
            sd = list(STRUCT_DECL.finditer(head))
            out.setdefault(mm.group(1), {})[sd[-1].group(1) if sd else None] = key
    return out


def tuning_members(root):
    """{member name: struct name} for the `F<S> <Member>;` UPROPERTYs of UUmbrellaTuning (Attack -> FAttackTuning)."""
    out = {}
    for path in headers(root):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        body = re.search(r"\bclass\s+(?:\w+_API\s+)?U" + TUNING_CLASS + r"\b[^{;]*\{(.*?)\n\};", text, re.S)
        if body:
            for s, n in re.findall(r"\b(F\w+)\s+(\w+)\s*;", body.group(1)):
                out[n] = s
    return out


DECL_BEFORE = re.compile(r"(?<![.>:])\b(?!(?:return|else|do|case|co_return|throw|delete|new)\b)[A-Za-z_][\w:]*"
                         r"(?:<[^<>;]*>)?\s*[&*]*\s*$")


def write_key(fields, name, pre, line, text_before, locals_, members):
    """The key a write of `name` changes, or None when it is not a baked field: a new local's declaration
    (`const float Cadence = ...`) is not a write; `<Member>.Field` / `<local of F<S>>.Field` / `F<S>::` code / the
    struct's own body name the struct. Unknown struct: the one marked struct with that field, else every candidate."""
    cands = fields.get(name) or {}
    q = re.search(r"(\w+)\s*(?:\.|->)\s*$", pre)
    struct = None
    if q:
        struct = members.get(q.group(1)) or locals_.get(q.group(1))
    elif DECL_BEFORE.search(pre):
        return None
    else:
        own = re.search(r"\b(F\w+)::", line) or max(list(STRUCT_DECL.finditer(text_before))
                                                       + list(re.finditer(r"\b(F\w+)::~?\w+\s*\(", text_before)),
                                                       key=lambda x: x.start(), default=None)
        struct = own.group(1) if own else None
    if struct:
        return cands.get(struct)
    if not cands:
        return None
    return " or ".join(sorted(set(cands.values())))


def source_files(root, exts=(".h", ".hpp", ".cpp", ".inl", ".cc")):
    out = []
    for top in (SOURCE, "Plugins"):
        for d, _, files in os.walk(os.path.join(root, top)):
            out += [os.path.join(d, f) for f in files if f.endswith(exts)]
    return sorted(out)


def one_source_problems(root, found):
    """Final-8 B H3: the marked header line is the only write of a baked member. Any other assignment in C++ (a .cpp
    constructor, an inline setter, an initializer list) changes the shipped value behind every check."""
    names, structs, flags = baked_members(found)
    if not names and not flags:
        return []
    fields, members = baked_fields(found), tuning_members(root)
    local_rx = re.compile(r"\b(" + "|".join(map(re.escape, sorted(structs))) + r")\b\s*[&*]?\s*(?:const\s+)?"
                          r"([A-Za-z_]\w*)\s*[;=,){\[]") if structs else None
    marked = {(path, i) for hits in found.values() for path, i, _ in hits}
    # Final-10 B H3: gameplay reads tuning at the point of use from GetDefault<UUmbrellaTuning>() (gameplay-code.md),
    # the object the hook reads at start and end of run. A non-const copy of a marked struct outside the settings
    # class (a component member, a local, a pointer) is a second source a whole-struct assign, a reference or a
    # memcpy can change unseen; GetMutableDefault and const_cast write the class default itself.
    copy_rx = re.compile(r"(?<![\w:])((?:const|constexpr)\s+)?\b(" + "|".join(map(re.escape, sorted(structs))) + r")\b\s*([&*]?)\s*"
                         r"(?:const\s+)?([A-Za-z_]\w*)\s*[;=,){\[]") if structs else None
    mutable_rx = re.compile(r"\bGetMutableDefault\s*<|\bconst_cast\s*<[^>]*\b(?:UUmbrellaTuning|"
                            + "|".join(map(re.escape, sorted(structs or {"\0never"}))) + r")\b")
    frx = re.compile(r"\b(" + "|".join(map(re.escape, sorted(flags))) + r")\s*,\s*(?:true|false)\b") if flags else None
    names = names or {"\0never": ""}
    rx = re.compile(r"\b(" + "|".join(map(re.escape, sorted(names))) + r")\b\s*(?:[-+*/%|&^]|<<|>>)?=(?!=)"
                    r"|(?:[:,]\s*)\b(" + "|".join(map(re.escape, sorted(names))) + r")\s*[({]")
    out = []
    for path in source_files(root):
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        settings = bool(re.search(r"\bclass\s+(?:\w+_API\s+)?U" + TUNING_CLASS + r"\b[^;]*?:", "\n".join(lines)))
        locals_ = {v: t for t, v in local_rx.findall("\n".join(lines))} if local_rx else {}
        tests = (os.sep + "Tests" + os.sep) in path   # a rule test builds its own tuning value for the plain rule
        stack = []   # one entry per open #if: True while in the true branch of exactly `#if UMBRELLAELLA_WORKBENCH`
        for i, ln in enumerate(lines):
            if PP_OPEN.match(ln):
                stack.append(bool(re.match(r"^\s*#\s*if\s+UMBRELLAELLA_WORKBENCH\s*(?://.*)?$", ln)))
                continue
            if PP_ELSE.match(ln):
                if stack:
                    stack[-1] = False
                continue
            if PP_END.match(ln):
                if stack:
                    stack.pop()
                continue
            # The workbench applies a preset to a per-run copy inside `#if UMBRELLAELLA_WORKBENCH`, which the
            # submission target compiles out (workbench-check); its #else branch and every other line ship.
            if (path, i) in marked or any(stack):
                continue
            code = ln.split("//", 1)[0]
            for m in rx.finditer(code):
                name = m.group(1) or m.group(2)
                key = write_key(fields, name, code[:m.start(1 if m.group(1) else 2)], code,
                                "\n".join(lines[:i + 1]), locals_, members) if name in fields else names.get(name)
                if key:
                    out.append(f"{key}: {rel(root, path)}:{i + 1} writes {name}; the `// bake:` default is the one "
                               "source of the shipped value (pipeline/unreal-rules.md): never assign it in code")
            for m in (frx.finditer(code) if frx else ()):
                out.append(f"{flags[m.group(1)]}: {rel(root, path)}:{i + 1} sets {m.group(1)} to a literal outside its "
                           "`// bake:` line; the marked flag default is the one source of the shipped value")
            if mutable_rx.search(code):
                out.append(f"{rel(root, path)}:{i + 1} writes the tuning class default (GetMutableDefault / const_cast): "
                           "gameplay reads GetDefault<UUmbrellaTuning>() and never writes it (pipeline/unreal/"
                           "gameplay-code.md); only `#if UMBRELLAELLA_WORKBENCH` code may")
            for m in (copy_rx.finditer(code) if copy_rx and not settings and not tests else ()):
                if m.group(1) or re.match(r"\s*(?:struct|class)\b", code[:m.start(2)][-7:]) or \
                        re.search(r"\b(?:struct|class|friend|USTRUCT)\s*$", code[:m.start(2)]):
                    continue
                out.append(f"{rel(root, path)}:{i + 1} holds a non-const {m.group(2)} ({m.group(4)}): read tuning at the "
                           "point of use with GetDefault<UUmbrellaTuning>() or a `const` reference to it, never a copy "
                           "that code can change after the hook's read (final-10 B H3); a flag table is `static constexpr` or "
                           "`static const` (final-11 A M3)")
    return out


def flag_default_problems(manifest, flags, decisions_text):
    """Before a key is baked, its flag default is the manifest default_enabled (card 0.27: each at its manifest
    default), unless a DECIDED row overrides that ID."""
    recs = flagged(manifest)
    out = []
    for fid, on in sorted(flags.items()):
        rec = recs.get(fid)
        if rec is None:
            out.append(f"{fid}.enabled: {fid} is not a flagged feature in {MANIFEST}")
        elif isinstance(on, bool) and on is not rec.get("default_enabled") and not decided_names(decisions_text, fid):
            out.append(f"{fid}.enabled: the C++ default is {str(on).lower()}, the manifest default_enabled is "
                       f"{str(rec.get('default_enabled')).lower()}: an unbaked flag ships at its manifest default")
    return out


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def flagged(manifest):
    return {f["feature_id"]: f for f in manifest.get("features", []) if f.get("flag")}


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest_check  # noqa: E402  one override rule for both tools (dry run B H3)
import tuning  # noqa: E402  one tunable/fixed rule for the bake and both sims (dry run B H3, H4)


def decided_rows(text):
    """Rows of the decisions tables whose last cell (Status) starts with DECIDED."""
    out = []
    for ln in (text or "").splitlines():
        if ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 2 and re.match(r"DECIDED\b", cells[-1]):
                out.append(ln)
    return out


def decided_names(text, token):
    """True when a DECIDED decision row explicitly overrides token with `Overrides: <IDs>` (a feature or preset
    ID). A row that only mentions the ID lifts nothing (manifest_check.decided_overrides)."""
    return token in manifest_check.decided_overrides(text)


def read_decisions(root):
    try:
        with open(os.path.join(root, DECISIONS), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def safety_problems(preset, flags, params, manifest, decisions_text, current=None):
    """The preset, p0, off and tuning rules for one set of values (export or stamp). The tunable/fixed rule is
    tools/tuning.py, the same one feel_check and encounter_check use (dry run B H3). current: {key: value already
    in Source/} so a fixed key with no approved start cannot be changed by a bake."""
    out = []
    if preset != SHIP_PRESET and not decided_names(decisions_text, preset or ""):
        out.append(f"preset {preset} is not {SHIP_PRESET} (BASE): only BASE ships unless a DECIDED row in "
                   f"{DECISIONS} says 'Overrides: {preset}'")
    feats = {f["feature_id"]: f for f in manifest.get("features", [])}
    for fid, on in sorted(flags.items()):
        rec = feats.get(fid)
        if rec and rec.get("status") == "APPROVED_P0" and on is False and not decided_names(decisions_text, fid):
            out.append(f"flag {fid}=off, but {fid} is APPROVED_P0 (never cut): it ships on unless a DECIDED row "
                       f"in {DECISIONS} says 'Overrides: {fid}'")
        why = tuning.flag_problem(manifest, fid, on)
        if why:
            out.append(why)
    approved = tuning.approved(manifest)
    for key, v in sorted(params.items()):
        why = tuning.value_problem(manifest, key, v, (current or {}).get(key))
        if why:
            out.append("param " + why)
            continue
        # final-9 B H1, GDD 1.3 line 226 ("No AI may invent a default, tune a parameter"): a shipped number other
        # than the GDD / manifest start is the design owner's call (manifest_check.DESIGN_OWNER). It needs a counted
        # DECIDED (<design owner>) row that names
        # the key itself in `Overrides: <key>` (docs/decisions.md); range and step alone are not an approval.
        start = (approved.get(key) or {}).get("start") if isinstance(approved.get(key), dict) else None
        if tuning.num(start) and tuning.num(v) and abs(v - start) > tuning.EPS and not decided_names(decisions_text, key):
            owner = manifest_check.DESIGN_OWNER
            out.append(f"param {key}={v:g} differs from the GDD start {start:g}: only {owner} (the design owner) tunes "
                       f"a parameter (no AI invents or tunes a value). Ship {start:g}, or add a row with Status 'DECIDED "
                       f"<date> ({owner})' and 'Overrides: {key}' to {DECISIONS}")
    return out


def export_problems(export, manifest=None, presets=None, shape_only=False, decisions_text=None, current=None):
    out = []
    if not isinstance(export, dict) or export.get("kind") != "workbench_config":
        return ["export is not a workbench config (needs \"kind\": \"workbench_config\")"]
    if not isinstance(export.get("preset"), str) or not PRESET_ID.fullmatch(export["preset"]):
        out.append(f"export preset {export.get('preset')!r} is not a T-nn ID")
    for k in ("commit", "manifest_version"):
        if not isinstance(export.get(k), str) or not export[k].strip():
            out.append(f"export has no {k}")
    flags, params = export.get("flags"), export.get("params")
    if not isinstance(flags, dict) or not all(isinstance(v, bool) for v in flags.values()):
        out.append("export flags must be an object of feature ID -> true/false")
        flags = {}
    if not isinstance(params, dict) or not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                               for v in params.values()):
        out.append("export params must be an object of '<feature ID>.<param>' -> number")
        params = {}
    if shape_only or manifest is None:
        return out
    if presets is not None and export.get("preset") not in {p.get("id") for p in presets.get("presets", [])}:
        out.append(f"export preset {export.get('preset')} is not in {PRESETS}")
    if export.get("manifest_version") != manifest.get("manifest_version"):
        out.append(f"export is for manifest {export.get('manifest_version')}, the repo has "
                   f"{manifest.get('manifest_version')}: export again from a build of this manifest")
    feats = {f["feature_id"]: f for f in manifest.get("features", [])}
    flag_recs = flagged(manifest)
    for fid, on in sorted(flags.items()):
        rec = flag_recs.get(fid)
        if rec is None:
            out.append(f"flag {fid} is not a flagged feature in {MANIFEST}")
        elif on is True and on is not rec.get("default_enabled") and not rec.get("implementation_authorized"):
            out.append(f"flag {fid}={'on' if on else 'off'} differs from its manifest default, but {fid} is "
                       f"{rec.get('status')} and not implementation_authorized: it may not ship changed")
    for key in sorted(params):
        fid, _, name = key.partition(".")
        if fid not in feats or name not in feats[fid].get("parameters", []):
            out.append(f"param {key} is not '<feature ID>.<param>' from {MANIFEST}")
    out += safety_problems(export.get("preset"), flags, params, manifest, decisions_text or "", current)
    return out


def wanted_values(export):
    vals = {f"{fid}.enabled": on for fid, on in export.get("flags", {}).items()}
    vals.update(export.get("params", {}))
    return vals


def required_keys(manifest):
    """Keys that must carry a `// bake:` marker once Source/ exists (dry run B H4): `<ID>.enabled` for every flagged
    record (card 0.27: one flag per flagged record), and every approved_parameters key whose feature is built
    (implementation_authorized or CONFIRMED). Without a marker the value ships unchecked."""
    feats = {f["feature_id"]: f for f in manifest.get("features", [])}
    keys = {f"{fid}.enabled" for fid in flagged(manifest)}
    for key in ((manifest.get("approved_parameters") or {}).get("values") or {}):
        rec = feats.get(key.partition(".")[0])
        if rec and (rec.get("implementation_authorized") or rec.get("status") == "CONFIRMED"):
            keys.add(key)
    return keys


def missing_markers(root, manifest, found):
    if not os.path.isdir(os.path.join(root, SOURCE)):
        return []
    return [f"{k}: no `// bake: {k}` marker in {SOURCE}/; every flag and every built approved parameter needs one, "
            "or it ships unchecked" for k in sorted(required_keys(manifest) - set(found))]


def bake(root, export_path, dry_run=False):
    """Returns (problems, diff text)."""
    try:
        with open(export_path, "rb") as fh:
            raw = fh.read()
        export = json.loads(raw.decode("utf-8"))
        manifest = read_json(os.path.join(root, MANIFEST))
        presets = read_json(os.path.join(root, PRESETS))
    except (OSError, ValueError) as e:
        raise OSError(f"cannot read input: {e}")
    found = markers(root)
    current = {k: parse_literal(v[0][2].group("lit")) for k, v in found.items() if len(v) == 1}
    probs = export_problems(export, manifest, presets, decisions_text=read_decisions(root), current=current)
    want = wanted_values(export)
    probs += [f"sim: {x}" for x in tuning.baked_vs_sim_problems(root, baked=want)]
    if probs:
        return probs, ""
    probs += shape_problems(root, found) + branch_problems(root, found) + one_source_problems(root, found)
    for key in sorted(want):
        n = len(found.get(key, []))
        if n == 0:
            probs.append(f"{key}: no `// bake: {key}` marker in {SOURCE}/; the value would not ship")
        elif n > 1:
            where = ", ".join(f"{rel(root, p)}:{i + 1}" for p, i, _ in found[key])
            probs.append(f"{key}: {n} markers ({where}); one default per key")
    for key in sorted(set(found) - set(want)):
        probs.append(f"{key}: marked in {rel(root, found[key][0][0])} but missing from the export; "
                     "the export must list every marked key")
    if probs:
        return probs, ""
    new_files = {}

    def text_of(path):
        if path not in new_files:
            with open(path, encoding="utf-8") as fh:
                new_files[path] = (fh.read(), None)
        return new_files[path]

    edits = {}
    for key, value in want.items():
        path, i, m = found[key][0]
        edits.setdefault(path, []).append((i, m, value))
    for path, items in edits.items():
        old, _ = text_of(path)
        lines = old.split("\n")
        for i, m, value in sorted(items, key=lambda x: (x[0], -x[1].start())):
            ln = lines[i]
            if same(parse_literal(m.group("lit")), value):
                continue   # final-10 A M7: an unchanged value keeps its spelling (300.f stays 300.f), so no Source/ diff
            lines[i] = ln[:m.start("lit")] + format_literal(m.group("lit"), value) + ln[m.end("lit"):]
        new_files[path] = (old, "\n".join(lines))
    mpath = os.path.join(root, MANIFEST)
    with open(mpath, encoding="utf-8") as fh:
        old_m = fh.read()
    for f in manifest["features"]:
        if f["feature_id"] in export["flags"]:
            f["default_enabled"] = export["flags"][f["feature_id"]]
    new_files[mpath] = (old_m, dump_json(manifest))
    spath = os.path.join(root, STAMP)
    old_s = ""
    if os.path.isfile(spath):
        with open(spath, encoding="utf-8") as fh:
            old_s = fh.read()
    stamp = {
        "note": "Written by tools/bake_preset.py from the approved workbench export (D-new-workbench-debug). "
                "Never edit by hand; bake again. The G4 gate record names this preset.",
        "preset": export["preset"],
        "export_sha256": hashlib.sha256(raw).hexdigest(),
        "export_commit": export["commit"],
        "manifest_version": export["manifest_version"],
        "values": {k: want[k] for k in sorted(want)},
    }
    new_files[spath] = (old_s, dump_json(stamp))
    diff = []
    for path in sorted(new_files):
        old, new = new_files[path]
        if new is None or new == old:
            continue
        r = rel(root, path)
        diff += difflib.unified_diff(old.splitlines(True), new.splitlines(True), "a/" + r, "b/" + r)
    if not dry_run:
        for path, (old, new) in new_files.items():
            if new is not None and new != old:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
    return [], "".join(diff)


def defaults(root):
    """Before the first bake (dry run B M4): every `// bake:` default in Source/ already follows the safety rules,
    so a G1-G3 package or the G2 Draft cannot ship an out-of-range, off-step or unapproved-on value. No Source/ = []."""
    manifest = read_json(os.path.join(root, MANIFEST))
    found = markers(root)
    vals = {k: parse_literal(v[0][2].group("lit")) for k, v in found.items()}
    flags = {k[:-len(".enabled")]: v for k, v in vals.items() if k.endswith(".enabled")}
    params = {k: v for k, v in vals.items() if not k.endswith(".enabled")}
    return unbaked_problems(root, manifest, found)


def unbaked_problems(root, manifest, found, skip=()):
    """The rules for `// bake:` defaults no stamp holds yet: shape, safety, the manifest flag default and the sims.
    skip: keys the stamp already holds (check compares those to the stamp)."""
    dec = read_decisions(root)
    found = {k: v for k, v in found.items() if k not in skip}
    vals = {k: parse_literal(v[0][2].group("lit")) for k, v in found.items()}
    flags = {k[:-len(".enabled")]: v for k, v in vals.items() if k.endswith(".enabled")}
    params = {k: v for k, v in vals.items() if not k.endswith(".enabled")}
    out = shape_problems(root, found)
    out += ini_override_problems(root)
    out += branch_problems(root, found) + one_source_problems(root, found)
    out += safety_problems(SHIP_PRESET, flags, params, manifest, dec, current=params)
    out += flag_default_problems(manifest, flags, dec)
    out += [f"sim: {x}" for x in tuning.baked_vs_sim_problems(root, baked={k: v for k, v in params.items()})]
    out += [f"{k}: {len(v)} markers; one default per key" for k, v in sorted(found.items()) if len(v) > 1]
    return out


def not_marked(root, manifest, found):
    """Required keys with no marker yet: listed before G4, failed at G4."""
    if not os.path.isdir(os.path.join(root, SOURCE)):
        return []
    return sorted(required_keys(manifest) - set(found))


def record_preset(text):
    m = RECORD_LINE.search(text)
    return m.group(1) if m else None


def check(root, preset=None, complete=False):
    """Returns (problems, stamp or None). complete=True is the G4 mode: every marked key is in the stamp and every
    required key has a marker. Otherwise a marked key the stamp does not hold yet passes the defaults rules."""
    spath = os.path.join(root, STAMP)
    if not os.path.isfile(spath):
        return [f"{STAMP} is missing: nothing is baked. Run bake on the approved export"], None
    try:
        stamp = read_json(spath)
        manifest = read_json(os.path.join(root, MANIFEST))
        presets = read_json(os.path.join(root, PRESETS))
    except (OSError, ValueError) as e:
        raise OSError(f"cannot read input: {e}")
    out = []
    sp = stamp.get("preset")
    if sp not in {p.get("id") for p in presets.get("presets", [])}:
        out.append(f"stamp preset {sp} is not in {PRESETS}")
    if preset is not None and preset != sp:
        out.append(f"the gate record approves preset {preset}, but {STAMP} has {sp}: bake {preset} or fix the record")
    if stamp.get("manifest_version") != manifest.get("manifest_version"):
        out.append(f"stamp is for manifest {stamp.get('manifest_version')}, the repo has "
                   f"{manifest.get('manifest_version')}: export and bake again")
    values = stamp.get("values") or {}
    flags = {k[:-len(".enabled")]: v for k, v in values.items() if k.endswith(".enabled")}
    params = {k: v for k, v in values.items() if not k.endswith(".enabled")}
    out += safety_problems(sp, flags, params, manifest, read_decisions(root))
    out += [f"sim: {x}" for x in tuning.baked_vs_sim_problems(root, baked=values)]
    found = markers(root)
    flag_recs = flagged(manifest)
    for key in sorted(values):
        want = values[key]
        fid, _, name = key.partition(".")
        if name == "enabled":
            rec = flag_recs.get(fid)
            if rec is None:
                out.append(f"{key}: {fid} is not a flagged feature in {MANIFEST}")
            elif not same(rec.get("default_enabled"), want):
                out.append(f"{key}: manifest default_enabled={rec.get('default_enabled')}, baked {want}")
        hits = found.get(key, [])
        if not hits:
            out.append(f"{key}: baked {want}, but no `// bake: {key}` marker in {SOURCE}/")
            continue
        for path, i, m in hits:
            got = parse_literal(m.group("lit"))
            if not same(got, want):
                out.append(f"{key}: {rel(root, path)}:{i + 1} has {m.group('lit')}, baked {want} (unbaked value)")
        if len(hits) > 1:
            out.append(f"{key}: {len(hits)} markers; one default per key")
    out += [x for x in shape_problems(root, {k: v for k, v in found.items() if k in values})]
    marked = {k: v for k, v in found.items() if k in values}
    out += branch_problems(root, marked) + one_source_problems(root, marked)
    if complete:
        out += ini_override_problems(root)
        for key in sorted(set(found) - set(values)):
            out.append(f"{key}: marked in {rel(root, found[key][0][0])} but not in the stamp: bake again (G4: "
                       "every shipped default is baked)")
        out += missing_markers(root, manifest, found)
    else:
        out += unbaked_problems(root, manifest, found, skip=set(values))
    return out, stamp


FIELD_PATH = re.compile(r"F?([A-Z]\w*)\.([A-Za-z_]\w*)")


def field_keys(root, found=None):
    """Final-10 A H1: {"<Struct>.<Field>": key} for every parameter marker under Source/: the hook reports each
    reflected field of the UUmbrellaTuning structs by its path (struct name without the F prefix), and the marked
    line names the key, so a card that marks a key never edits the hook."""
    found = markers(root) if found is None else found
    out = {}
    for key, hits in found.items():
        if key.endswith(".enabled"):
            continue
        for path, i, m in hits:
            mm = MEMBER.search(m.string[:m.start("lit")].split("//", 1)[0])
            with open(path, encoding="utf-8", errors="replace") as fh:
                head = "\n".join(fh.read().split("\n")[:i + 1])
            sd = list(STRUCT_DECL.finditer(head))
            if mm and sd:
                out[f"{sd[-1].group(1)[1:]}.{mm.group(1)}"] = key
    return out


def resolve_fields(root, eff, found=None):
    """The SMOKE_EFFECTIVE fields with each reflected `<Struct>.<Field>` that has a marker renamed to its key, and the
    problems: a key given twice (by key and by field, or twice by field) fails (final-10 B M2)."""
    paths = field_keys(root, found)
    out, probs = {}, []
    if eff.get("_dup"):
        probs.append(f"SMOKE_EFFECTIVE gives {eff['_dup']} more than once: one value per key (the last one would win)")
    for k, v in eff.items():
        if k == "_dup":
            continue
        name = k
        if not re.fullmatch(KEY, k) and FIELD_PATH.fullmatch(k):
            fm = FIELD_PATH.fullmatch(k)
            name = paths.get(f"{fm.group(1)}.{fm.group(2)}", k)
        if name in out and name != k:
            probs.append(f"SMOKE_EFFECTIVE gives {name} twice (as {k} too): one value per key")
        elif name in out:
            probs.append(f"SMOKE_EFFECTIVE gives {name} twice: one value per key")
        out[name] = v
    return out, probs


def effective_values(eff):
    """{key: bool or float} from a parsed SMOKE_EFFECTIVE line (ue_run.parse_effective), keys only."""
    out = {}
    for k, raw in eff.items():
        if not re.fullmatch(KEY, k):
            continue
        if k.endswith(".enabled"):
            out[k] = {"1": True, "true": True, "0": False, "false": False}.get(raw.lower(), raw)
        elif raw.lower() in ("true", "false"):
            out[k] = raw.lower() == "true"   # a reflected bool field prints True / False
        else:
            try:
                out[k] = float(raw)
            except ValueError:
                out[k] = raw
    return out


def effective_problems(root, eff, complete=False):
    """Final-9 B C1: the packaged game's own SMOKE_EFFECTIVE line (tools/ue_run.py contract) against the repo. Each
    live value equals pipeline/qa/baked.json once that key is baked, else its `// bake:` default in Source/, else
    the manifest default (flag) or the GDD 1.3 start (parameter). Every marked key is reported (the hook reads
    each one from the live objects). complete (G4): every required key and every baked key is reported."""
    out = []
    try:
        manifest = read_json(os.path.join(root, MANIFEST))
    except (OSError, ValueError) as e:
        return [f"cannot read {MANIFEST}: {e}"]
    try:
        stamp = read_json(os.path.join(root, STAMP)) if os.path.isfile(os.path.join(root, STAMP)) else {}
    except (OSError, ValueError) as e:
        return [f"cannot read {STAMP}: {e}"]
    baked = (stamp or {}).get("values") or {}
    found = markers(root)
    eff, out = resolve_fields(root, eff, found)
    for f in ("commit", "workbench", "platform"):
        if not eff.get(f):
            out.append(f"SMOKE_EFFECTIVE has no {f}= (the hook logs the compiled-in commit, workbench and platform)")
    if eff.get("commit") and not re.fullmatch(r"[0-9a-f]{7,40}", eff["commit"]):
        out.append(f"SMOKE_EFFECTIVE commit={eff['commit']}: the build did not compile a commit in "
                   "(package.sh / package.ps1 stamp UMBRELLAELLA_BUILD_COMMIT at build start)")
    vals = effective_values(eff)
    if (complete or any(k.endswith(".enabled") for k in vals)) and eff.get("manifest") != manifest.get("manifest_version"):
        out.append(f"SMOKE_EFFECTIVE manifest={eff.get('manifest', '<none>')}, the repo has "
                   f"{manifest.get('manifest_version')}: the harness flag table is from another manifest")
    flags = flagged(manifest)
    approved = tuning.approved(manifest)
    dec = read_decisions(root)
    feats = {f["feature_id"]: f for f in manifest.get("features", [])}
    for key, got in sorted(vals.items()):
        fid = key.partition(".")[0]
        if key in baked:
            want, src = baked[key], STAMP
        elif key in found:
            want, src = parse_literal(found[key][0][2].group("lit")), f"its `// bake:` default in {SOURCE}/"
        elif key.endswith(".enabled") and fid in flags:
            want, src = flags[fid].get("default_enabled"), f"the {MANIFEST} default"
        elif isinstance(approved.get(key), dict) and tuning.num(approved[key].get("start")):
            want, src = approved[key]["start"], "the GDD 1.3 start"
        else:
            out.append(f"{key}: the game reports it, but it is not a flag, an approved parameter or a marked default")
            continue
        if isinstance(got, str):
            out.append(f"{key}={got}: not a number or 0/1")
        elif not same(got, want):
            out.append(f"{key}: the running game has {got if not isinstance(got, bool) else int(got)}, but {src} "
                       f"says {want if not isinstance(want, bool) else int(want)}: the shipped binary does not run the "
                       "checked value (an #if/#else branch, a write in code, a DataAsset or an ini line)")
        if key.endswith(".enabled") and got is False and (feats.get(fid) or {}).get("status") == "APPROVED_P0" \
                and not decided_names(dec, fid):
            out.append(f"{key}: the running game has {fid} off, but it is APPROVED_P0 (GDD 1.3: never cut)")
        if key.endswith(".enabled") and got is True:
            why = tuning.flag_problem(manifest, fid, True)
            if why:
                out.append(f"{key}: the running game has {why}")
    for key in sorted(set(found) - set(vals)):
        out.append(f"{key}: marked in {rel(root, found[key][0][0])}, but the game's SMOKE_EFFECTIVE line does not report "
                   "it: the hook reports every reflected field of the UUmbrellaTuning structs and every harness flag; "
                   "is the field a UPROPERTY of a struct that is a UPROPERTY of UUmbrellaTuning?")
    if complete:
        for key in sorted((required_keys(manifest) | set(baked)) - set(vals) - set(found)):
            out.append(f"{key}: required at G4, but the game's SMOKE_EFFECTIVE line does not report it")
    return out


def commit_tree(root, commit):
    """Final-10 B M6, A M6: the tree the game was built from. (path, problem): root itself when the compiled-in commit
    is root's HEAD, root is no git clone, or the commit is not in it (a WARN line says so), else that commit's files
    in a temp dir (the caller removes it)."""
    import subprocess
    import tempfile

    def git(*args):
        return subprocess.run(["git", "-C", root, *args], capture_output=True)
    head = git("rev-parse", "HEAD")
    if head.returncode != 0 or not commit or not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        return root, None
    if head.stdout.decode().strip().startswith(commit.lower()):
        return root, None
    full = git("rev-parse", "--verify", "--quiet", commit + "^{commit}")
    if full.returncode != 0:
        # a clone behind the build: say so and use the checkout; check_pr and the G4 tie re-check on the right tree
        print(f"WARN: the game was built from {commit}, which is not a commit in this clone: checked against the "
              "checkout; fetch it for the built commit's values")
        return root, None
    tmp = tempfile.mkdtemp()
    tar = git("archive", "--format=tar", full.stdout.decode().strip())
    if tar.returncode != 0:
        return None, f"git archive {commit} failed"
    import io
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as tf:
        try:
            tf.extractall(tmp, filter="data")
        except TypeError:   # Python before 3.12
            tf.extractall(tmp)
    return tmp, None


def effective_main(root, logs, complete=False):
    """Every SMOKE_EFFECTIVE line the hook logged (exactly one at=start, at least one at=end; final-10 B H3, B M1)
    against the tree of the commit the game was built from (final-10 B M6)."""
    import shutil
    import ue_run
    texts = ue_run.read_logs(logs)
    hits = ue_run.effective_lines(list(reversed(texts)))   # the game log first: smoke.sh passes stdout, then it
    if not hits:
        print("FAIL: no SMOKE_EFFECTIVE line in the game log: the smoke hook logs the live tuning values and flags "
              "(tools/ue_run.py contract, card 0.6)")
        print("bake_preset effective: FAIL 1 problem(s)")
        return 1
    for raw, _ in hits:
        print(raw)   # the game's lines, as printed, for the PR
    probs = ue_run.effective_line_problems(hits)
    start = next((f for _, f in hits if f.get("at") == "start"), hits[0][1])
    tree, err = commit_tree(root, start.get("commit"))
    if err:
        probs.append(err)
    else:
        try:
            for raw, eff in hits:
                where = f"at={eff.get('at')}" + (f" outcome={eff['outcome']}" if eff.get("outcome") else "")
                probs += [p if eff is start else f"{where}: {p}" for p in effective_problems(tree, eff, complete)]
                if eff is not start:
                    for k in ("commit", "workbench", "platform", "manifest"):
                        if eff.get(k) != start.get(k):
                            probs.append(f"{where}: {k}={eff.get(k)}, but at=start says {k}={start.get(k)}")
        finally:
            if tree != root:
                shutil.rmtree(tree, ignore_errors=True)
    ok = ue_run.SMOKE_LINE.search("\n".join(texts))
    if ok:
        f = dict(ue_run.FIELDS.findall(ok.group("rest")))
        for k in ("commit", "workbench"):
            a, b = (f.get(k) or "").lower(), (start.get(k) or "").lower()
            if a and b and not (a.startswith(b) or b.startswith(a)):
                probs.append(f"SMOKE_EFFECTIVE {k}={b}, but SMOKE_OK says {k}={a}")
    seen = []
    for p in probs:
        if p not in seen:
            seen.append(p)
            print("FAIL: " + p)
    if seen:
        print(f"bake_preset effective: FAIL {len(seen)} problem(s)")
        return 1
    print(f"bake_preset effective: PASS keys={len(effective_values(resolve_fields(root, start)[0]))} "
          f"lines={len(hits)} commit={start.get('commit')} workbench={start.get('workbench')} "
          f"platform={start.get('platform')}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bake")
    b.add_argument("export")
    b.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("check")
    g = c.add_mutually_exclusive_group()
    g.add_argument("--record", help="gate record file with a 'Baked preset: T-nn' line")
    g.add_argument("--preset")
    c.add_argument("--complete", action="store_true", help="G4 mode: every marked key baked, every required key marked")
    sub.add_parser("defaults")
    ef = sub.add_parser("effective", help="the game's SMOKE_EFFECTIVE line against baked.json and the manifest")
    ef.add_argument("log", nargs="+")
    ef.add_argument("--complete", action="store_true", help="G4: every required key is reported")
    v = sub.add_parser("validate")
    v.add_argument("export")
    v.add_argument("--shape-only", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "bake":
            probs, diff = bake(a.root, a.export, a.dry_run)
            if probs:
                for p in probs:
                    print("FAIL: " + p)
                print(f"bake_preset bake: FAIL {len(probs)} problem(s); nothing written")
                return 1
            sys.stdout.write(diff)
            try:
                todo = not_marked(a.root, read_json(os.path.join(a.root, MANIFEST)), markers(a.root))
            except (OSError, ValueError):
                todo = []
            for k in todo:
                print(f"not marked yet (required at G4; bake again once it is coded): {k}")
            print(f"bake_preset bake: {'dry run, nothing written' if a.dry_run else 'written'}; "
                  "open a PR with this diff, then run check")
            return 0
        if a.cmd == "validate":
            export = read_json(a.export)
            manifest = None if a.shape_only else read_json(os.path.join(a.root, MANIFEST))
            presets = None if a.shape_only else read_json(os.path.join(a.root, PRESETS))
            probs = export_problems(export, manifest, presets, a.shape_only, read_decisions(a.root))
            for p in probs:
                print("FAIL: " + p)
            print(f"bake_preset validate: {'FAIL' if probs else 'PASS'} {len(probs)} problem(s)")
            return 1 if probs else 0
        if a.cmd == "effective":
            return effective_main(a.root, a.log, a.complete)
        if a.cmd == "defaults":
            probs = defaults(a.root)
            for p in probs:
                print("FAIL: " + p)
            print(f"bake_preset defaults: {'FAIL' if probs else 'PASS'} {len(probs)} problem(s)")
            return 1 if probs else 0
        preset = a.preset
        if a.record:
            with open(a.record, encoding="utf-8") as fh:
                preset = record_preset(fh.read())
            if preset is None:
                print(f"FAIL: {a.record} has no 'Baked preset: T-nn' line")
                print("bake_preset check: FAIL 1 problem(s)")
                return 1
        probs, stamp = check(a.root, preset, complete=a.complete or bool(a.record))
        for p in probs:
            print("FAIL: " + p)
        if not probs and not (a.complete or a.record):
            try:
                manifest = read_json(os.path.join(a.root, MANIFEST))
                found = markers(a.root)
                later = sorted(set(found) - set(stamp.get("values") or {}))
                todo = not_marked(a.root, manifest, found)
            except (OSError, ValueError):
                later, todo = [], []
            for k in later:
                print(f"not baked yet (checked as a default; bake before G4): {k}")
            for k in todo:
                print(f"not marked yet (required at G4): {k}")
        if probs:
            print(f"bake_preset check: FAIL {len(probs)} problem(s)")
            return 1
        print(f"bake_preset check: PASS preset={stamp['preset']} values={len(stamp.get('values') or {})}")
        return 0
    except (OSError, ValueError) as e:
        print(f"bake_preset: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

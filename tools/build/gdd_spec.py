#!/usr/bin/env python3
"""Generate docs/build/gdd-spec.json from the GDD snapshot named in docs/gdd/CURRENT (never hand-edited).

Every Rule ID row (`| ID | Behavior | Decision |`) is scanned for concrete numbers: counts, positions, radii, HP,
damage, timings, cadences, speeds, frame counts, XP. Each becomes one entry keyed `<RuleID>.<label>[.<n>]`:
  {"rule", "priority" (P0/P1/P2 from the row's APPROVED_P<n> status, "" when the row has none), "value", "unit", "tolerance" (only when the GDD gives one: +/-N%), "wording" (the GDD text around it)}
The label is the word(s) before the number (`damage 10` -> damage; `5 shots/s` -> shots_per_s), so keys stay put when
unrelated text elsewhere in the row changes. A key repeated in one row gets `.2`, `.3`.

  gdd_spec.py            write docs/build/gdd-spec.json
  gdd_spec.py --check    exit 1 if the file differs from a fresh generation
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "build", "gdd-spec.json")
ROW = re.compile(r"^\| ([A-Z][A-Z0-9]{1,6}-\d+[a-z]?) \| (.*) \| ([A-Z0-9_]+) \|\s*$")
IDTOK = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b|\bseed\d+|\bSH\d\.\d|\bGDD\s*\d[\d.]*|\b(?:section|rev|revision|row|page|step|D)\s*\d+",
                   re.I)
NUM = re.compile(r"(?<![\d.])([-+−]?)(\d+(?:\.\d+)?)(?![\w.]*\d)")
UNITS = [("units/s²", r"units/s²"), ("units/s", r"units\s*/\s*s\b"), ("shots/s", r"shots?\s*/\s*s\b"),
         ("volleys/s", r"volleys?\s*/\s*s\b"), ("ticks/s", r"(?:damage\s+)?ticks?\s*/\s*s\b"), ("s", r"\s?(?:s|sec|seconds?)\b"),
         ("%", r"\s?%"), ("deg", r"\s?°"), ("units", r"\s?(?:units?|px|pixels?)\b"), ("HP", r"\s?(?:HP|health)\b"),
         ("x", r"\s?[×x]\s*(?=\d)"), ("hits", r"\s?(?:ordinary\s+)?hits?\b"), ("frames", r"\s?frames?\b"),
         ("XP", r"\s?XP\b"), ("lives", r"\s?(?:current\s+)?lives\b"), ("shots", r"\s?shots?\b"), ("levels", r"\s?levels?\b")]
STOP = {"the", "a", "an", "of", "to", "and", "or", "at", "in", "on", "for", "by", "with", "is", "are", "be", "as", "from",
        "than", "per", "over", "x", "z", "about", "near", "then", "up", "gives", "equals", "plus", "minus", "max", "min",
        "maximum", "minimum", "about"}


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def snapshot():
    cur = _read(os.path.join(ROOT, "docs", "gdd", "CURRENT")).strip()
    return cur, _read(os.path.join(ROOT, "docs", "gdd", cur))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def label_for(text, start, end, unit=""):
    """Adjacent word before the number (`damage 10`, `Hop = 40`), else the word after number+unit (`0.7s cooldown`),
    else a unit label (`5 shots/s` -> shots_per_s), else `value`."""
    m = re.search(r"([A-Za-z][A-Za-z']*(?:[ _-][A-Za-z][A-Za-z']*)?)\s*(?:=|:|≤|≥|<|>|~|≈|\()?\s*[-+−]?$", text[max(0, start - 40):start])
    if m:
        words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z']*", m.group(1))]
        if words and words[-1] not in STOP:
            keep = [words[-1]] if len(words) == 1 or words[-2] in STOP else words[-2:]
            return slug("_".join(keep))
    after = re.match(r"[\s,]*([A-Za-z][A-Za-z']*)", text[end:])
    if after and after.group(1).lower() not in STOP and unit in ("", "s"):
        return slug(after.group(1))
    return {"shots/s": "shots_per_s", "volleys/s": "volleys_per_s", "ticks/s": "ticks_per_s", "units/s": "units_per_s",
            "%": "pct", "": "value"}.get(unit, slug(unit))


def unit_at(text, end):
    for name, rx in UNITS:
        m = re.match(rx, text[end:], re.I if name not in ("HP", "XP") else 0)
        if m:
            return name, end + m.end()
    return "", end


def priority_of(decision):
    m = re.search(r"_P(\d)\b", decision)
    return f"P{m.group(1)}" if m else ""


def extract(rule, behavior, priority=""):
    masked = IDTOK.sub(lambda m: " " * len(m.group(0)), behavior)
    out, seen = [], {}
    for m in NUM.finditer(masked):
        sign, digits = m.groups()
        val = float(digits) * (-1 if sign in ("-", "−") else 1)
        unit, uend = unit_at(masked, m.end())
        if unit == "s" and re.match(r"\s?(?:s|sec|seconds?)\b\w", masked[m.end():m.end() + 9]):
            unit = ""
        label = label_for(masked, m.start(), uend if unit else m.end(), unit)
        key = f"{rule}.{label}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            key += f".{seen[key]}"
        ent = {"rule": rule, "priority": priority, "value": int(val) if val == int(val) and "." not in digits else val, "unit": unit,
               "wording": re.sub(r"\s+", " ", behavior[max(0, m.start() - 30):uend + 25]).strip()}
        tail = masked[uend:uend + 12]
        tol = re.match(r"\s*[±]\s*(\d+(?:\.\d+)?)\s*(%?)", tail)
        if tol and re.match(r"\s*trim\b", masked[uend + tol.end():uend + tol.end() + 8]):
            tol = None   # "330 ±20% trim" is the trim's range, not the fall speed's
        if tol:
            ent["tolerance"] = {"value": float(tol.group(1)), "unit": "%" if tol.group(2) else unit or "abs"}
        out.append((key, ent))
    return out


def generate():
    cur, text = snapshot()
    spec = {}
    for line in text.split("\n"):
        m = ROW.match(line)
        if not m:
            continue
        rule, behavior, decision = m.groups()
        for key, ent in extract(rule, behavior, priority_of(decision)):
            spec[key] = ent
    return {"_note": "GENERATED by tools/build/gdd_spec.py from the GDD snapshot named below. Never hand-edit; rerun the tool.",
            "snapshot": cur, "count": len(spec), "values": spec}


def render():
    return json.dumps(generate(), indent=1, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv):
    new = render()
    if "--check" in argv:
        old = _read(OUT) if os.path.exists(OUT) else ""
        if old != new:
            print("FAIL gdd-spec.json differs from a fresh generation; run tools/build/gdd_spec.py")
            return 1
        print("gdd_spec: up to date"); return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"gdd_spec: wrote {os.path.relpath(OUT, ROOT)} ({json.loads(new)['count']} values)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

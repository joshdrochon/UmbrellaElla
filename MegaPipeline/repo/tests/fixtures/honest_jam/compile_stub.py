"""Stand-in for the compile + cook in tests/test_honest_jam.py's RunUAT stub (no engine here).

A real build compiles the values that ship into the binary. This stub does the same for the stand-in game
(game.sh): it reads what a compiler would read and writes a copy of game.sh with those values fixed in it.
  commit     UMBRELLAELLA_BUILD_COMMIT from the environment (the package script stamps it at build start)
  workbench  the UMBRELLAELLA_WORKBENCH value in Source/<target>.Target.cs
  platform   -platform=Win64 -> Windows, else Mac
  values     what the smoke hook's own mechanism reaches, never every marker (final-10 A H1). The hook in
             Source/**/Smoke/ reflects over UUmbrellaTuning (it names TFieldIterator and UUmbrellaTuning): for each
             `UPROPERTY(...) F<S> <Member>;` of the UUmbrellaTuning class, each `UPROPERTY(...) <type> <Field> = <lit>;`
             of struct F<S> is logged as `<S>.<Field>=<value>`. A field with no UPROPERTY, or a struct that is not a
             member of UUmbrellaTuning, is not reflected, so it is not logged. Flags: when the hook calls
             ForEachFlag (the card 0.3 harness seam), each `{ EFeatureId::<TOKEN>, true|false }` entry is logged as
             `<TOKEN with - for _>.enabled`; a hook that calls IsFeatureEnabled(EFeatureId::X) by name logs only X.
             The `// bake:` comments are read only to apply STUB_LIVE.
  manifest   the TEXT("...") of GManifestVersion in Source/ (card 0.3 seam: "none"; card 0.27 sets it), when the hook
             calls ManifestVersion()
  title      Source/UmbrellaElla/Private/UI/ exists (card 0.21); skip: the smoke hook source says SMOKE_TITLE
STUB_LIVE=<KEY>=<v>,...: the value the real compiler would ship differs from the marked one (an #else branch, a
write in code): only the broken-on-purpose cases set it. STUB_LIVE_END=<KEY>=<v>,...: the value changes after startup
(a write during play), so only the end-of-run line has it (final-10 B H3).
Usage: compile_stub.py <repo> <game.sh> <out exe> <target> <platform>
"""
import os
import re
import sys

repo, src, out, target, plat = sys.argv[1:6]
text = {}
for d, _, files in os.walk(os.path.join(repo, "Source")):
    for f in files:
        if f.endswith((".h", ".cpp", ".cs")):
            with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                text[os.path.join(d, f)] = fh.read()
tcs = text.get(os.path.join(repo, "Source", target + ".Target.cs"), "")
wb = (re.findall(r'"UMBRELLAELLA_WORKBENCH=(\d)"', tcs) or ["0"])[0]
hook = "\n".join(b for p, b in text.items() if os.sep + "Smoke" + os.sep in p)
UPROP = r"UPROPERTY\s*\((?:[^()]|\([^()]*\))*\)\s*"


def norm(lit):
    lit = lit.strip().rstrip("fF")
    if lit in ("true", "false"):
        return {"true": "1", "false": "0"}[lit]
    f = float(lit)
    return str(int(f)) if f.is_integer() else repr(f)


vals, by_key = {}, {}   # path -> value; bake key -> path (for STUB_LIVE only)
if "TFieldIterator" in hook and "UUmbrellaTuning" in hook:
    body = next((m.group(1) for b in text.values() for m in [re.search(
        r"class\s+(?:\w+_API\s+)?UUmbrellaTuning\b[^{;]*\{(.*?)\n\};", b, re.S)] if m), "")
    members = re.findall(UPROP + r"F(\w+)\s+\w+\s*;", body)
    structs = {}
    for b in text.values():
        for m in re.finditer(r"struct\s+(?:\w+_API\s+)?F(\w+)\s*\{(.*?)\n\};", b, re.S):
            structs[m.group(1)] = m.group(2)
    for s in members:
        for m in re.finditer(UPROP + r"(?:float|double|int32|uint8|bool)\s+(\w+)\s*=\s*([^;]+);([^\n]*)",
                             structs.get(s, "")):
            path = f"{s}.{m.group(1)}"
            vals[path] = norm(m.group(2))
            k = re.search(r"//\s*bake:\s*(\S+)", m.group(3))
            if k:
                by_key[k.group(1)] = path
# Final-11 A H1: ForEachFlag on the harness seam (card 0.3) enumerates the whole flag table, the way reflection
# enumerates tuning; a hook that names flags one by one (IsFeatureEnabled(EFeatureId::X)) logs only those.
named = set(re.findall(r"IsFeatureEnabled\s*\(\s*EFeatureId::(\w+)", hook))
if "ForEachFlag" in hook or named:
    for b in text.values():
        for m in re.finditer(r"\{\s*EFeatureId::(\w+)\s*,\s*(true|false)\s*\}[^\n]*", b):
            if "ForEachFlag" not in hook and m.group(1) not in named:
                continue
            key = m.group(1).replace("_", "-") + ".enabled"
            vals[key] = norm(m.group(2))
            by_key[key] = key


def live(env):
    v = dict(vals)
    for kv in filter(None, os.environ.get(env, "").split(",")):
        k, _, x = kv.partition("=")
        v[by_key.get(k, k)] = x
    return v


start = live("STUB_LIVE")
os.environ["STUB_LIVE"] = ",".join(filter(None, [os.environ.get("STUB_LIVE", ""), os.environ.get("STUB_LIVE_END", "")]))
end = live("STUB_LIVE")
man = next((m.group(1) for b in text.values() for m in [re.search(r'GManifestVersion\s*=\s*TEXT\("([^"]+)"\)', b)] if m),
           "") if "ManifestVersion()" in hook else ""
title = os.path.isdir(os.path.join(repo, "Source", "UmbrellaElla", "Private", "UI"))
skip = "SMOKE_TITLE" in hook
eff = " ".join(f"{k}={start[k]}" for k in sorted(start))
eff_end = " ".join(f"{k}={end[k]}" for k in sorted(end))
head = (f'COMMIT="{os.environ.get("UMBRELLAELLA_BUILD_COMMIT", "unknown")}"; WB="{wb}"; '
        f'PLATFORM="{"Windows" if plat == "Win64" else "Mac"}"; MANIFEST="{man}"; EFFECTIVE="{eff}"; '
        f'EFFECTIVE_END="{eff_end}"; TITLE="{int(title)}"; SKIP="{int(skip)}"; '
        f'FAKE_SHOT="{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fake_shot.py")}"\n')
with open(src, encoding="utf-8") as fh:
    game = fh.read().replace("# @COMPILED@\n", head)
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as fh:
    fh.write(game)
os.chmod(out, 0o755)
